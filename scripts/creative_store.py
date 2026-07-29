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
