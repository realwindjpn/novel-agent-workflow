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

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = 1
MAX_TURNS = 10_000
MAX_TEXT_BYTES = 256 * 1024
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
