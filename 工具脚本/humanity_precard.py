#!/usr/bin/env python3
"""Generate and validate path-only humanity pre-cards for chapter candidates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "kewu-humanity-precard-v1"
REQUIRED_CONSTRAINT_FIELDS = (
    "character_current_goals",
    "obstacles",
    "costs",
    "relationship_tensions",
    "sensory_physical_feedback",
    "action_chain",
    "character_voice_constraints",
)


class HumanityCardBlockedError(ValueError):
    """Raised when a humanity pre-card cannot enter the review chain."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def default_card_path(candidate_path: str | Path) -> Path:
    candidate = Path(candidate_path)
    return candidate.with_name(f"{candidate.stem}.humanity.json")


def _is_filled(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value) and all(_is_filled(item) for item in value)
    if isinstance(value, dict):
        return bool(value) and all(str(key).strip() and _is_filled(item) for key, item in value.items())
    return value is not None


def build_card_template(candidate_path: str | Path) -> dict[str, Any]:
    candidate = Path(candidate_path).resolve()
    if not candidate.is_file():
        raise FileNotFoundError(f"candidate missing: {candidate}")
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate": {
            "path": str(candidate),
            "sha256": sha256_file(candidate),
        },
        "anchors": [],
        "constraints": {field: [] for field in REQUIRED_CONSTRAINT_FIELDS},
        "status": "BLOCKED",
    }


def write_card_template(candidate_path: str | Path, card_path: str | Path | None = None) -> Path:
    candidate = Path(candidate_path)
    destination = Path(card_path) if card_path else default_card_path(candidate)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(build_card_template(candidate), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


def validate_card(card_path: str | Path, candidate_path: str | Path | None = None) -> dict[str, Any]:
    card_file = Path(card_path)
    errors: list[str] = []
    if not card_file.is_file():
        return {"status": "BLOCKED", "errors": ["HUMANITY_CARD_MISSING"], "card_path": str(card_file)}
    try:
        card = json.loads(card_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "BLOCKED",
            "errors": [f"HUMANITY_CARD_INVALID_JSON:{exc}"],
            "card_path": str(card_file),
        }
    if not isinstance(card, dict):
        return {"status": "BLOCKED", "errors": ["HUMANITY_CARD_NOT_OBJECT"], "card_path": str(card_file)}

    if card.get("schema_version") != SCHEMA_VERSION:
        errors.append("HUMANITY_CARD_SCHEMA_MISMATCH")
    candidate_meta = card.get("candidate") if isinstance(card.get("candidate"), dict) else {}
    recorded_path = candidate_meta.get("path")
    recorded_sha = candidate_meta.get("sha256")
    candidate = Path(candidate_path or recorded_path or "")
    if not recorded_path:
        errors.append("HUMANITY_CARD_CANDIDATE_PATH_MISSING")
    if not recorded_sha:
        errors.append("HUMANITY_CARD_CANDIDATE_SHA_MISSING")
    if not candidate.is_file():
        errors.append("HUMANITY_CARD_CANDIDATE_MISSING")
        candidate_lines: list[str] = []
    else:
        candidate_lines = candidate.read_text(encoding="utf-8", errors="strict").splitlines()
        resolved = str(candidate.resolve())
        if recorded_path and str(Path(recorded_path).resolve()) != resolved:
            errors.append("HUMANITY_CARD_CANDIDATE_PATH_MISMATCH")
        if recorded_sha and sha256_file(candidate) != recorded_sha:
            errors.append("HUMANITY_CARD_CANDIDATE_SHA_MISMATCH")

    constraints = card.get("constraints") if isinstance(card.get("constraints"), dict) else {}
    for field in REQUIRED_CONSTRAINT_FIELDS:
        if not _is_filled(constraints.get(field)):
            errors.append(f"HUMANITY_CARD_FIELD_MISSING:{field}")

    anchors = card.get("anchors")
    if not isinstance(anchors, list) or not anchors:
        errors.append("HUMANITY_CARD_ANCHORS_MISSING")
    else:
        for index, anchor in enumerate(anchors):
            if not isinstance(anchor, dict):
                errors.append(f"HUMANITY_CARD_ANCHOR_INVALID:{index}")
                continue
            allowed = {"id", "line_start", "line_end", "sha256", "constraint_refs"}
            unexpected = sorted(set(anchor) - allowed)
            if unexpected:
                errors.append(f"HUMANITY_CARD_ANCHOR_INLINE_TEXT_FORBIDDEN:{index}:{','.join(unexpected)}")
            required = ("id", "line_start", "line_end", "sha256", "constraint_refs")
            if any(not _is_filled(anchor.get(key)) for key in required):
                errors.append(f"HUMANITY_CARD_ANCHOR_FIELD_MISSING:{index}")
                continue
            line_start = anchor["line_start"]
            line_end = anchor["line_end"]
            if not isinstance(line_start, int) or not isinstance(line_end, int) or line_start < 1 or line_end < line_start:
                errors.append(f"HUMANITY_CARD_ANCHOR_RANGE_INVALID:{index}")
                continue
            if candidate_lines and line_end > len(candidate_lines):
                errors.append(f"HUMANITY_CARD_ANCHOR_RANGE_OUT_OF_BOUNDS:{index}")
                continue
            if candidate_lines:
                anchored_text = "\n".join(candidate_lines[line_start - 1:line_end])
                if sha256_text(anchored_text) != anchor["sha256"]:
                    errors.append(f"HUMANITY_CARD_ANCHOR_SHA_MISMATCH:{index}")
            refs = anchor["constraint_refs"]
            if not isinstance(refs, list) or not refs or any(ref not in REQUIRED_CONSTRAINT_FIELDS for ref in refs):
                errors.append(f"HUMANITY_CARD_ANCHOR_CONSTRAINT_REF_INVALID:{index}")

    status = "PASS" if not errors else "BLOCKED"
    return {
        "status": status,
        "errors": errors,
        "card_path": str(card_file.resolve()),
        "card_sha256": sha256_file(card_file),
        "candidate_path": str(candidate.resolve()) if candidate.is_file() else str(candidate),
        "candidate_sha256": recorded_sha or "",
        "anchor_count": len(anchors) if isinstance(anchors, list) else 0,
    }


def require_valid_card(card_path: str | Path, candidate_path: str | Path | None = None) -> dict[str, Any]:
    result = validate_card(card_path, candidate_path)
    if result["status"] != "PASS":
        raise HumanityCardBlockedError("; ".join(result["errors"]))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="科武纪元人味前置卡生成/校验")
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init", help="生成不含正文的结构化模板")
    init_parser.add_argument("candidate")
    init_parser.add_argument("--out")
    validate_parser = subparsers.add_parser("validate", help="校验前置卡")
    validate_parser.add_argument("card")
    validate_parser.add_argument("--candidate")
    args = parser.parse_args()
    if args.command == "init":
        print(write_card_template(args.candidate, args.out))
        return 0
    result = validate_card(args.card, args.candidate)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
