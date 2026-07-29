from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.creative_store import CreativeStore, CreativeStoreError


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


if __name__ == "__main__":
    unittest.main()
