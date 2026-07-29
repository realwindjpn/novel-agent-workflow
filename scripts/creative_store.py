"""Active-book creative persistence.

Each local book may carry a ``creative/`` workspace beside its formal
``workflow.json``. The workspace stores the freeform conversation,
facts, proposals, and trial drafts that live *outside* the formal
state machine. Formal project state is never touched here: the core's
review/lock/release gates remain the only route to ``workflow.json``
mutations.

The store is deliberately bounded: every record id, text length, and
collection is validated before it touches disk, and all writes are
atomic (write-temp then ``os.replace``) so a crashed append can never
leave a half-written ``conversation.jsonl`` or manifest.
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = 1
MAX_TURNS = 10_000
MAX_TEXT_BYTES = 256 * 1024
MAX_ARCHIVE_BYTES = 8 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 256
MAX_UNPACKED_BYTES = 16 * 1024 * 1024
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class CreativeStoreError(ValueError):
    """Raised when a creative record violates the store's bounds."""


def _empty_facts() -> dict[str, list[str]]:
    return {
        "confirmed": [],
        "boundaries": [],
        "rejected": [],
        "important_turn_ids": [],
    }


class CreativeStore:
    def __init__(self, book_root: Path) -> None:
        self.book_root = book_root.resolve()
        if not (self.book_root / "workflow.json").is_file():
            raise CreativeStoreError("active book root must contain workflow.json")
        self.root = self.book_root / "creative"

    def read_session(self) -> dict[str, Any]:
        if not self.root.exists():
            return {
                "schema_version": SCHEMA_VERSION,
                "turns": [],
                "summary": "",
                "facts": _empty_facts(),
                "proposals": [],
                "drafts": [],
            }
        return self._read_existing_session()

    def _read_existing_session(self) -> dict[str, Any]:
        manifest = self._read_json(self.root / "manifest.json", {})
        turns = []
        turns_path = self.root / "conversation.jsonl"
        if turns_path.is_file():
            for line in turns_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    turns.append(json.loads(line))
        return {
            "schema_version": int(manifest.get("schema_version", SCHEMA_VERSION)),
            "turns": turns,
            "summary": self._read_text(self.root / "context-summary.md"),
            "facts": self._read_json(self.root / "facts.json", _empty_facts()),
            "proposals": self._read_collection("proposals"),
            "drafts": self._read_collection("drafts"),
        }

    def _read_collection(self, name: str) -> list[dict[str, Any]]:
        directory = self.root / name
        if not directory.is_dir():
            return []
        return [
            self._read_json(path, {})
            for path in sorted(directory.glob("*.json"))
            if path.is_file()
        ]

    @staticmethod
    def _read_json(path: Path, fallback: Any) -> Any:
        if not path.is_file():
            return fallback
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _read_text(path: Path) -> str:
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    # -- mutation surface ------------------------------------------------

    def append_turn(self, turn: Mapping[str, Any]) -> dict[str, Any]:
        item = dict(turn)
        self._validate_record(item, roles={"user", "assistant", "system"})
        existing = self.read_session()["turns"]
        if any(old.get("id") == item["id"] for old in existing):
            return item
        if len(existing) >= MAX_TURNS:
            raise CreativeStoreError("creative turn limit reached")
        self._ensure_root()
        with (self.root / "conversation.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
        self._write_manifest()
        return item

    def write_state(self, summary: str, facts: Mapping[str, Any]) -> None:
        self._validate_text(summary)
        clean = {key: list(facts.get(key, [])) for key in _empty_facts()}
        for values in clean.values():
            if not all(isinstance(value, str) for value in values):
                raise CreativeStoreError("fact lists must contain strings")
        self._ensure_root()
        self._atomic_text(self.root / "context-summary.md", summary)
        self._atomic_json(self.root / "facts.json", clean)
        self._write_manifest()

    def write_proposal(self, proposal: Mapping[str, Any]) -> dict[str, Any]:
        return self._write_record("proposals", proposal)

    def write_draft(self, draft: Mapping[str, Any]) -> dict[str, Any]:
        return self._write_record("drafts", draft)

    def _write_record(self, collection: str, record: Mapping[str, Any]) -> dict[str, Any]:
        item = dict(record)
        self._validate_record(item)
        self._ensure_root()
        self._atomic_json(self.root / collection / f"{item['id']}.json", item)
        self._write_manifest()
        return item

    def _validate_record(self, item: dict[str, Any], roles: set[str] | None = None) -> None:
        record_id = item.get("id")
        if not isinstance(record_id, str) or not ID_RE.fullmatch(record_id):
            raise CreativeStoreError("record id is invalid")
        if roles is not None and item.get("role") not in roles:
            raise CreativeStoreError("turn role is invalid")
        for key in ("text", "preview", "content", "title"):
            value = item.get(key)
            if value is not None:
                if not isinstance(value, str):
                    raise CreativeStoreError(f"{key} must be a string")
                self._validate_text(value)

    @staticmethod
    def _validate_text(value: str) -> None:
        if len(value.encode("utf-8")) > MAX_TEXT_BYTES:
            raise CreativeStoreError("creative text is too large")

    def _ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "proposals").mkdir(exist_ok=True)
        (self.root / "drafts").mkdir(exist_ok=True)

    def _write_manifest(self) -> None:
        current = self.read_session()
        self._atomic_json(self.root / "manifest.json", {
            "schema_version": SCHEMA_VERSION,
            "turn_count": len(current["turns"]),
            "proposal_count": len(current["proposals"]),
            "draft_count": len(current["drafts"]),
        })

    @staticmethod
    def _atomic_json(path: Path, payload: Any) -> None:
        CreativeStore._atomic_text(
            path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        )

    @staticmethod
    def _atomic_text(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    # -- ZIP export / import --------------------------------------------

    def export_zip(self) -> bytes:
        session = self.read_session()
        entries = {
            "creative-backup/manifest.json": json.dumps({
                "schema_version": SCHEMA_VERSION,
                "turn_count": len(session["turns"]),
                "proposal_count": len(session["proposals"]),
                "draft_count": len(session["drafts"]),
            }, ensure_ascii=False, indent=2) + "\n",
            "creative-backup/conversation.jsonl": "".join(
                json.dumps(turn, ensure_ascii=False, separators=(",", ":")) + "\n"
                for turn in session["turns"]
            ),
            "creative-backup/context-summary.md": session["summary"],
            "creative-backup/facts.json": json.dumps(
                session["facts"], ensure_ascii=False, indent=2
            ) + "\n",
        }
        for proposal in session["proposals"]:
            entries[f"creative-backup/proposals/{proposal['id']}.json"] = json.dumps(
                proposal, ensure_ascii=False, indent=2
            ) + "\n"
        for draft in session["drafts"]:
            entries[f"creative-backup/drafts/{draft['id']}.json"] = json.dumps(
                draft, ensure_ascii=False, indent=2
            ) + "\n"
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_STORED) as zf:
            for name, text in entries.items():
                zf.writestr(name, text.encode("utf-8"))
        payload = raw.getvalue()
        if len(payload) > MAX_ARCHIVE_BYTES:
            raise CreativeStoreError("creative ZIP is too large")
        return payload

    def import_zip(self, payload: bytes, decision: str) -> dict[str, Any]:
        if decision not in {"merge", "copy", "cancel"}:
            raise CreativeStoreError("import decision is invalid")
        if decision == "cancel":
            return {"cancelled": True}
        entries = self._read_zip_entries(payload)
        session = self._session_from_entries(entries)
        if decision == "copy":
            copy_id = self._next_copy_id()
            target = self.root / "imports" / copy_id
            self._write_session_tree(target, session)
            return {"copy_id": copy_id, "turn_count": len(session["turns"])}
        self._merge_session(session)
        return {"merged": True, "turn_count": len(self.read_session()["turns"])}

    def _read_zip_entries(self, payload: bytes) -> dict[str, bytes]:
        if len(payload) > MAX_ARCHIVE_BYTES:
            raise CreativeStoreError("creative ZIP is too large")
        out: dict[str, bytes] = {}
        total = 0
        with zipfile.ZipFile(io.BytesIO(payload), "r") as zf:
            infos = zf.infolist()
            if len(infos) > MAX_ARCHIVE_ENTRIES:
                raise CreativeStoreError("creative ZIP has too many entries")
            for info in infos:
                path = Path(info.filename)
                if path.is_absolute() or ".." in path.parts or info.is_dir():
                    if info.is_dir():
                        continue
                    raise CreativeStoreError("unsafe ZIP path")
                if info.external_attr >> 16 & 0o170000 == 0o120000:
                    raise CreativeStoreError("ZIP links are not allowed")
                total += info.file_size
                if total > MAX_UNPACKED_BYTES:
                    raise CreativeStoreError("creative ZIP expands too large")
                out[info.filename] = zf.read(info)
        return out

    def _session_from_entries(self, entries: dict[str, bytes]) -> dict[str, Any]:
        manifest_raw = entries.get("creative-backup/manifest.json")
        if manifest_raw is None:
            raise CreativeStoreError("creative ZIP manifest is missing")
        try:
            manifest = json.loads(manifest_raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CreativeStoreError("creative ZIP manifest is unreadable") from exc
        if int(manifest.get("schema_version", -1)) != SCHEMA_VERSION:
            raise CreativeStoreError("creative ZIP schema version is unsupported")

        def _decode(name: str) -> str:
            raw = entries.get(name)
            if raw is None:
                return ""
            return raw.decode("utf-8")

        turns: list[dict[str, Any]] = []
        convo = _decode("creative-backup/conversation.jsonl")
        for line in convo.splitlines():
            if line.strip():
                turns.append(json.loads(line))
        try:
            facts = json.loads(_decode("creative-backup/facts.json")) or _empty_facts()
        except json.JSONDecodeError:
            facts = _empty_facts()
        if not isinstance(facts, dict):
            facts = _empty_facts()
        facts = {key: list(facts.get(key, [])) for key in _empty_facts()}

        proposals: list[dict[str, Any]] = []
        drafts: list[dict[str, Any]] = []
        for name, raw in entries.items():
            if not name.startswith("creative-backup/proposals/"):
                continue
            try:
                proposals.append(json.loads(raw.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        for name, raw in entries.items():
            if not name.startswith("creative-backup/drafts/"):
                continue
            try:
                drafts.append(json.loads(raw.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        return {
            "schema_version": SCHEMA_VERSION,
            "turns": turns,
            "summary": _decode("creative-backup/context-summary.md"),
            "facts": facts,
            "proposals": proposals,
            "drafts": drafts,
        }

    def _write_session_tree(self, target: Path, session: dict[str, Any]) -> None:
        target.mkdir(parents=True, exist_ok=True)
        (target / "proposals").mkdir(exist_ok=True)
        (target / "drafts").mkdir(exist_ok=True)
        self._atomic_json(target / "manifest.json", {
            "schema_version": SCHEMA_VERSION,
            "turn_count": len(session["turns"]),
            "proposal_count": len(session["proposals"]),
            "draft_count": len(session["drafts"]),
        })
        self._atomic_text(
            target / "conversation.jsonl",
            "".join(json.dumps(t, ensure_ascii=False, separators=(",", ":")) + "\n"
                    for t in session["turns"]),
        )
        self._atomic_text(target / "context-summary.md", session["summary"])
        self._atomic_json(target / "facts.json", session["facts"])
        for proposal in session["proposals"]:
            self._atomic_json(target / "proposals" / f"{proposal['id']}.json", proposal)
        for draft in session["drafts"]:
            self._atomic_json(target / "drafts" / f"{draft['id']}.json", draft)

    def _merge_session(self, incoming: dict[str, Any]) -> None:
        current = self.read_session()
        merged_turns = list(current["turns"])
        existing_ids = {t.get("id") for t in merged_turns}
        for turn in incoming["turns"]:
            if turn.get("id") not in existing_ids:
                merged_turns.append(turn)
                existing_ids.add(turn.get("id"))

        def _merge_collection(name: str) -> list[dict[str, Any]]:
            kept = list(current[name])
            kept_ids = {r.get("id") for r in kept}
            for record in incoming[name]:
                if record.get("id") not in kept_ids:
                    kept.append(record)
                    kept_ids.add(record.get("id"))
            return kept

        merged_proposals = _merge_collection("proposals")
        merged_drafts = _merge_collection("drafts")

        merged_facts = {key: list(current["facts"].get(key, [])) for key in _empty_facts()}
        for key in merged_facts:
            seen = list(merged_facts[key])
            for value in incoming["facts"].get(key, []):
                if value not in seen:
                    seen.append(value)
            merged_facts[key] = seen

        merged_summary = current["summary"]
        if not merged_summary and incoming["summary"]:
            merged_summary = incoming["summary"]

        self._ensure_root()
        self._atomic_text(
            self.root / "conversation.jsonl",
            "".join(json.dumps(t, ensure_ascii=False, separators=(",", ":")) + "\n"
                    for t in merged_turns),
        )
        self._atomic_text(self.root / "context-summary.md", merged_summary)
        self._atomic_json(self.root / "facts.json", merged_facts)
        (self.root / "proposals").mkdir(exist_ok=True)
        (self.root / "drafts").mkdir(exist_ok=True)
        for proposal in merged_proposals:
            self._atomic_json(self.root / "proposals" / f"{proposal['id']}.json", proposal)
        for draft in merged_drafts:
            self._atomic_json(self.root / "drafts" / f"{draft['id']}.json", draft)
        self._write_manifest()

    def _next_copy_id(self) -> str:
        self._ensure_root()
        imports_dir = self.root / "imports"
        imports_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        candidate = f"import-{stamp}"
        n = 1
        while (imports_dir / candidate).exists():
            n += 1
            candidate = f"import-{stamp}-{n}"
        return candidate
