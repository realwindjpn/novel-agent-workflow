from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.creative_store import CreativeStore, CreativeStoreError, MAX_TEXT_BYTES


class CreativeStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.book = Path(self.tmp.name) / "book"
        self.book.mkdir()
        (self.book / "workflow.json").write_text(
            '{"title":"测试书","stage":"IDEA"}', encoding="utf-8"
        )

    def test_empty_session_does_not_create_files(self) -> None:
        store = CreativeStore(self.book)
        session = store.read_session()
        self.assertEqual(session["schema_version"], 1)
        self.assertEqual(session["turns"], [])
        self.assertEqual(session["summary"], "")
        self.assertFalse((self.book / "creative").exists())

    def test_requires_a_real_book_root(self) -> None:
        with self.assertRaisesRegex(CreativeStoreError, "workflow.json"):
            CreativeStore(Path(self.tmp.name) / "missing")

    def test_append_turn_is_resumable_and_idempotent(self) -> None:
        store = CreativeStore(self.book)
        turn = {
            "id": "turn-1",
            "role": "user",
            "text": "写一个雨夜追踪的开场",
            "created_at": "2026-07-30T00:00:00Z",
        }
        store.append_turn(turn)
        store.append_turn(turn)
        self.assertEqual(store.read_session()["turns"], [turn])

    def test_write_state_and_artifacts_round_trip(self) -> None:
        store = CreativeStore(self.book)
        facts = {
            "confirmed": ["主角是法医"],
            "boundaries": ["不使用超自然解释"],
            "rejected": [],
            "important_turn_ids": ["turn-1"],
        }
        store.write_state("雨夜命案的现实主义悬疑。", facts)
        store.write_proposal({
            "id": "proposal-1",
            "status": "pending",
            "preview": "主角追查被伪装的旧案。",
            "intake": {"genre": "悬疑"},
            "source_turn_ids": ["turn-1"],
        })
        store.write_draft({
            "id": "draft-1",
            "title": "雨夜试写",
            "content": "雨水沿着警戒线滴落。",
            "source_turn_ids": ["turn-1"],
        })
        session = store.read_session()
        self.assertEqual(session["summary"], "雨夜命案的现实主义悬疑。")
        self.assertEqual(session["facts"], facts)
        self.assertEqual(session["proposals"][0]["status"], "pending")
        self.assertEqual(session["drafts"][0]["content"], "雨水沿着警戒线滴落。")

    def test_rejects_invalid_ids_roles_and_oversized_text(self) -> None:
        store = CreativeStore(self.book)
        with self.assertRaises(CreativeStoreError):
            store.append_turn({"id": "../escape", "role": "user", "text": "x"})
        with self.assertRaises(CreativeStoreError):
            store.append_turn({"id": "turn-2", "role": "root", "text": "x"})
        with self.assertRaises(CreativeStoreError):
            store.append_turn({
                "id": "turn-3", "role": "user", "text": "x" * (MAX_TEXT_BYTES + 1)
            })


if __name__ == "__main__":
    unittest.main()
