#!/usr/bin/env python3
"""Material-bus DISPOSITION_MANIFEST adapter for the real MiroFish bridge.

The adapter is deliberately not a SenseNova run-dir.  It reads source records,
checks their evidence in place, and emits references plus hashes only.  It never
writes a material card, a run directory, an index, Wiki, outline, or chapter.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

BRIDGE_PATH = Path(__file__).with_name("mirofish_feed_to_card_bridge_20260606.py")
REQUIRED_FIELDS = ("card_md", "body_path", "url", "body_status", "verification_status")
SELECTED_DISPOSITION = "MIROFISH_CANDIDATE"


def _load_bridge() -> Any:
    spec = importlib.util.spec_from_file_location("real_mirofish_bridge", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load real bridge: {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REAL_BRIDGE = _load_bridge()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def source_title(value: Any) -> str:
    """Return an embedded source title without altering the raw evidence record."""
    text = _text(value)
    if not text.startswith("{"):
        return text
    candidates = (
        text,
        text.replace(r'\"', '"'),
        re.sub(r'\\+(?=")', '', text),
    )
    for candidate in candidates:
        try:
            embedded = json.loads(candidate)
        except json.JSONDecodeError:
            # Some historical material records preserve a truncated JSON envelope.
            # Recover only the explicit title field; keep the raw record/SHA untouched.
            match = re.search(r'"title"\s*:\s*"((?:\\.|[^"\\])*)"', candidate)
            if match:
                try:
                    return json.loads(f'"{match.group(1)}"').strip() or text
                except json.JSONDecodeError:
                    return match.group(1).strip() or text
            continue
        if isinstance(embedded, dict) and isinstance(embedded.get("title"), str):
            return embedded["title"].strip() or text
    return text


def normalized_signature(record: dict[str, Any]) -> str:
    url = REAL_BRIDGE.normalize_url(_text(record.get("url")))
    title = re.sub(r"\s+", " ", source_title(record.get("title"))).lower()
    return hashlib.sha256(f"{url}\n{title}".encode("utf-8")).hexdigest()


def manifest_material_id(entry: dict[str, Any]) -> str:
    return _text(entry.get("material_id") or entry.get("id"))


def select_manifest_entries(manifest: dict[str, Any], limit: int = 0) -> list[dict[str, Any]]:
    entries = manifest.get("entries") if isinstance(manifest, dict) else None
    if not isinstance(entries, list):
        raise ValueError("manifest.entries must be a list")
    selected = [
        entry for entry in entries
        if isinstance(entry, dict) and entry.get("disposition") == SELECTED_DISPOSITION
    ]
    return selected[:limit] if limit > 0 else selected


def load_cards_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at line {line_no}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"material card at line {line_no} is not an object")
        records.append(value)
    return records


def _path_error(field: str, value: Any, require_nonempty: bool = True) -> str | None:
    text = _text(value)
    if require_nonempty and not text:
        return f"{field}_missing"
    if not text:
        return None
    path = Path(text)
    if not path.is_file() or path.stat().st_size <= 0:
        return f"{field}_missing_or_empty"
    return None


def validate_record(entry: dict[str, Any], record: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if _text(record.get("id")) != manifest_material_id(entry):
        reasons.append("identity_mismatch")
    for field in REQUIRED_FIELDS:
        if not _text(record.get(field)):
            reasons.append(f"{field}_missing")
    if _text(record.get("body_status")).lower() not in {"fetched", "body_fetched"}:
        reasons.append("body_status_not_fetched")
    if not _text(record.get("verification_status")):
        reasons.append("verification_status_missing")
    for field in ("card_md", "body_path"):
        reason = _path_error(field, record.get(field))
        if reason:
            reasons.append(reason)
    if not _text(record.get("source_run")):
        reasons.append("source_run_missing")
    if not _text(record.get("url")):
        reasons.append("url_missing")
    return sorted(set(reasons))


def _rejection(material_id: str, entry: dict[str, Any], reasons: list[str], record: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "material_id": material_id,
        "candidate_id": _text((record or {}).get("candidate_id")) or None,
        "reasons": sorted(set(reasons)),
        "manifest_reason": entry.get("reason", ""),
        "source_run": _text((record or {}).get("source_run")) or None,
    }


def build_package(manifest: dict[str, Any], records: list[dict[str, Any]], limit: int = 0) -> dict[str, Any]:
    entries = select_manifest_entries(manifest, limit)
    records_by_id: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        records_by_id.setdefault(_text(record.get("id")), []).append(record)

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    conversion_tasks: list[dict[str, Any]] = []
    seen_manifest_ids: set[str] = set()
    seen_signatures: set[str] = set()

    for entry in entries:
        material_id = manifest_material_id(entry)
        if not material_id:
            rejected.append(_rejection(material_id, entry, ["manifest_id_missing"]))
            continue
        if material_id in seen_manifest_ids:
            rejected.append(_rejection(material_id, entry, ["duplicate_manifest_id"]))
            continue
        seen_manifest_ids.add(material_id)
        matches = records_by_id.get(material_id, [])
        if not matches:
            rejected.append(_rejection(material_id, entry, ["missing_card"]))
            continue
        if len(matches) != 1:
            rejected.append(_rejection(material_id, entry, ["duplicate_card_id"], matches[0]))
            continue
        record = matches[0]
        reasons = validate_record(entry, record)
        signature = normalized_signature(record)
        if signature in seen_signatures:
            reasons.append("duplicate_signature")
        if reasons:
            rejected.append(_rejection(material_id, entry, reasons, record))
            continue
        seen_signatures.add(signature)

        card_path = Path(_text(record["card_md"]))
        body_path = Path(_text(record["body_path"]))
        source_sha = sha256_bytes(canonical_json(record).encode("utf-8"))
        mapping = {
            "material_id": material_id,
            "candidate_id": _text(record.get("candidate_id")) or None,
            "source_run": _text(record.get("source_run")),
            "body_path": str(body_path),
            "card_md": str(card_path),
            "source_sha256": source_sha,
            "card_sha256": sha256_file(card_path),
            "body_sha256": sha256_file(body_path),
            "url": _text(record.get("url")),
            "body_status": _text(record.get("body_status")),
            "verification_status": _text(record.get("verification_status")),
            "mapping_reason": "manifest material_id exact-match; source evidence fields validated; no SenseNova run-dir substitution",
            "signature_sha256": signature,
        }
        accepted.append(mapping)

        card_text = card_path.read_text(encoding="utf-8", errors="ignore")
        body_text = body_path.read_text(encoding="utf-8", errors="ignore")
        item = {
            "title": source_title(record.get("title")),
            "url": _text(record.get("url")),
            "source_group": _text(record.get("source")),
            "source_type": _text(record.get("platform")),
            "verification_status": _text(record.get("verification_status")),
            "material_id": material_id,
        }
        disposition, chapter, reason, axis = REAL_BRIDGE.classify_material(
            item["title"], "", f"{card_text}\n{body_text}", item["source_group"]
        )
        decision = {
            "$schema": "decision_card_v1_bus_manifest_adapter",
            "material_id": material_id,
            "candidate_id": mapping["candidate_id"],
            "source_url": item["url"],
            "title": REAL_BRIDGE.normalize_title(item["title"]),
            "source_run": mapping["source_run"],
            "source_card_path": mapping["card_md"],
            "body_path": mapping["body_path"],
            "source_sha256": source_sha,
            "body_sha256": mapping["body_sha256"],
            "card_sha256": mapping["card_sha256"],
            "verification_status": mapping["verification_status"],
            "evidence_complete": True,
            "disposition": disposition,
            "disposition_reason": reason,
            "disposition_by": "bus_manifest_adapter_dry_run",
            "mirofish_projection": REAL_BRIDGE.make_projection(item, card_text, disposition, chapter, reason, axis),
            "bridge_policy": "dry_run_no_formal_card_no_index_no_wiki_write",
        }
        decisions.append(decision)
        if disposition == "CHAPTER_PREP_ONLY":
            conversion_tasks.append({
                "task": "FORMAL_CARD_CANDIDATE_AFTER_HUMAN_OR_CONTROLLER_REVIEW",
                "material_id": material_id,
                "candidate_id": mapping["candidate_id"],
                "title": decision["title"],
                "source_url": decision["source_url"],
                "source_card_path": mapping["card_md"],
                "target_chapter_hint": chapter,
                "not_done_in_dry_run": True,
            })

    if not accepted:
        status = "FAIL"
    elif rejected:
        status = "PARTIAL"
    else:
        status = "PASS"
    return {
        "schema": "bus_manifest_adapter_package_v1",
        "status": status,
        "dry_run": True,
        "bridge_input_mode": "material_bus_manifest",
        "source_manifest_schema": manifest.get("schema"),
        "selected_disposition": SELECTED_DISPOSITION,
        "requested_count": len(entries),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "accepted": accepted,
        "rejected": rejected,
        "decision_cards": decisions,
        "card_conversion_tasks": conversion_tasks,
        "formal_cards_written": False,
        "production_files_modified": False,
        "source_run_policy": "source_run is provenance only; never used as --run-dir or copied",
    }


def write_outputs(package: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "adapter_package.json").write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "decision_cards.json").write_text(json.dumps(package["decision_cards"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "card_conversion_tasks.json").write_text(json.dumps(package["card_conversion_tasks"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Bus manifest adapter dry-run",
        "",
        f"- verdict: {package['status']}",
        f"- requested_count: {package['requested_count']}",
        f"- accepted_count: {package['accepted_count']}",
        f"- rejected_count: {package['rejected_count']}",
        "- dry_run: true",
        "- formal_cards_written: false",
        "- production_files_modified: false",
        "",
        "## Rejections",
        "",
    ]
    for item in package["rejected"]:
        lines.append(f"- {item['material_id']}: {', '.join(item['reasons'])}")
    (out_dir / "dry_run_report.generated.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bus-manifest", required=True, type=Path)
    parser.add_argument("--cards-jsonl", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true", required=True)
    args = parser.parse_args(argv)
    manifest = json.loads(args.bus_manifest.read_text(encoding="utf-8"))
    records = load_cards_jsonl(args.cards_jsonl)
    package = build_package(manifest, records, args.limit)
    write_outputs(package, args.out_dir)
    print(json.dumps({
        "status": package["status"],
        "requested_count": package["requested_count"],
        "accepted_count": package["accepted_count"],
        "rejected_count": package["rejected_count"],
        "out_dir": str(args.out_dir),
    }, ensure_ascii=False, indent=2))
    return 0 if package["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
