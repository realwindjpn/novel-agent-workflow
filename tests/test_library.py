from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

from novel_workflow import core as nw_core
from novel_workflow.library import (
    TRASH_DIRECTORY,
    TRASH_INFO_FILE,
    ProjectEntry,
    chapter_artifact_dir,
    discover_projects,
    discover_trash,
    next_book_directory,
    next_restore_directory,
    next_trash_directory,
    safe_component,
)
from novel_workflow.core import (
    complete_intake_example,
    init_project,
    issue_chapter,
    lock_outline,
    record_idea,
    review_concept,
    review_outline,
    write_bible,
    write_outline,
)


class LibraryTests(unittest.TestCase):
    def test_safe_component_handles_windows_rules(self):
        self.assertEqual(safe_component("  A<B>: C.  "), "A_B_ C")
        self.assertEqual(safe_component("CON"), "_CON")
        self.assertEqual(safe_component("..."), "\u3002")

    def test_next_book_directory_uses_date_and_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                next_book_directory(root, "\u62fe\u9057", date(2026, 7, 28)).name,
                "\u62fe\u9057_20260728",
            )
            (root / "\u62fe\u9057_20260728").mkdir()
            (root / "\u62fe\u9057_20260728(1)").mkdir()
            self.assertEqual(
                next_book_directory(root, "\u62fe\u9057", date(2026, 7, 28)).name,
                "\u62fe\u9057_20260728(2)",
            )

    def test_discover_projects_sorts_recent_first_and_marks_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, title, updated in (
                ("old", "\u4e0a\u4e0a\u4e0b", "2026-07-27T01:00:00+00:00"),
                ("new", "\u4e0a\u4e0a\u53c8", "2026-07-28T01:00:00+00:00"),
            ):
                p = root / name
                p.mkdir()
                (p / "workflow.json").write_text(json.dumps({
                    "title": title, "stage": "IDEA", "updated_at": updated,
                    "chapters": {},
                }), encoding="utf-8")
            bad = root / "bad"
            bad.mkdir()
            (bad / "workflow.json").write_text("{", encoding="utf-8")
            entries = discover_projects(root)
            self.assertEqual([e.directory for e in entries], ["new", "old", "bad"])
            self.assertFalse(entries[-1].valid)

    def test_discover_projects_excludes_trash_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            book = root / "normal"
            book.mkdir()
            (book / "workflow.json").write_text(
                json.dumps({"title": "Normal", "chapters": {}}), encoding="utf-8"
            )
            trash = root / TRASH_DIRECTORY / "tagged"
            trash.mkdir(parents=True)
            (trash / "workflow.json").write_text(
                json.dumps({"title": "Hidden", "chapters": {}}), encoding="utf-8"
            )
            self.assertEqual([e.directory for e in discover_projects(root)], ["normal"])

    def test_next_trash_and_restore_directories_are_collision_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = datetime(2026, 7, 31, 8, 30, 15, 123456, tzinfo=timezone.utc)
            first = next_trash_directory(root, "雾城回声_20260731", now)
            self.assertEqual(
                first.name,
                "20260731T083015123456Z__雾城回声_20260731",
            )
            first.mkdir(parents=True)
            self.assertEqual(
                next_trash_directory(root, "雾城回声_20260731", now).name,
                first.name + "(1)",
            )
            occupied = root / "雾城回声_20260731"
            occupied.mkdir()
            self.assertEqual(
                next_restore_directory(root, "雾城回声_20260731").name,
                "雾城回声_20260731（恢复1）",
            )

    def test_discover_trash_reads_valid_and_invalid_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid = root / TRASH_DIRECTORY / "valid-id"
            valid.mkdir(parents=True)
            (valid / TRASH_INFO_FILE).write_text(json.dumps({
                "schema_version": 1,
                "original_directory": "雾城回声_20260731",
                "title": "雾城回声",
                "trashed_at": "2026-07-31T08:30:15.123456Z",
            }, ensure_ascii=False), encoding="utf-8")
            invalid = root / TRASH_DIRECTORY / "invalid-id"
            invalid.mkdir()
            entries = {entry.trash_id: entry for entry in discover_trash(root)}
            self.assertTrue(entries["valid-id"].valid)
            self.assertEqual(entries["valid-id"].original_directory, "雾城回声_20260731")
            self.assertFalse(entries["invalid-id"].valid)
            self.assertIn("missing", entries["invalid-id"].error)

    def test_chapter_artifact_dir_is_relative_and_zero_padded(self):
        self.assertEqual(
            chapter_artifact_dir(7, date(2026, 7, 28)).as_posix(),
            "chapters/\u7b2c007\u7ae0_20260728",
        )

    def test_issue_chapter_persists_artifact_dir_and_workspace(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            init_project(root, "Ledger Book")
            record_idea(root, "idea", complete_intake_example())
            (root / "concept.md").write_text("PASS", encoding="utf-8")
            review_concept(root, "PASS", "concept.md", "controller:c")
            (root / "bible.md").write_text("bible", encoding="utf-8")
            write_bible(root, "bible.md")
            for level in ("master", "volume", "chapter"):
                (root / f"o-{level}.md").write_text(
                    f"Title (working): Chapter One\n{level}", encoding="utf-8"
                )
                write_outline(root, level, f"o-{level}.md")
                (root / f"o-{level}-r.md").write_text("PASS", encoding="utf-8")
                review_outline(
                    root, level, "PASS", f"o-{level}-r.md", f"controller:{level}-r"
                )
            lock_outline(root)
            with patch.object(nw_core, "local_today", lambda: date(2026, 7, 28)):
                state = issue_chapter(root, 7, "\u63a5\u53e3", "\u63a5\u53e3\u4f7f\u547d")
            self.assertEqual(
                state["artifact_dir"], "chapters/\u7b2c007\u7ae0_20260728"
            )
            self.assertTrue((root / state["artifact_dir"]).is_dir())
            proj = json.loads((root / "workflow.json").read_text(encoding="utf-8"))
            self.assertEqual(
                proj["chapters"]["7"]["artifact_dir"],
                "chapters/\u7b2c007\u7ae0_20260728",
            )


if __name__ == "__main__":
    unittest.main()
