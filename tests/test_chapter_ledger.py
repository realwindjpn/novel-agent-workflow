"""Tests for the whole-book chapter ledger and source-alignment guard.

Covers the integration-layer features added on top of the per-chapter state
machine:

- ``list_chapters`` reflects every chapter state file on disk.
- the ledger in ``workflow.json.chapters`` is kept in sync after issue,
  draft, review, repair, and release.
- ``record_draft`` rejects a draft whose title disagrees with the locked
  chapter outline (SOURCE_MISMATCH).
- the CLI ``chapters`` command returns the ledger as JSON.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from novel_workflow.core import (
    complete_intake_example,
    init_project,
    record_idea,
    review_concept,
    write_bible,
    write_outline,
    review_outline,
    lock_outline,
    issue_chapter,
    record_draft,
    review_chapter,
    repair_chapter,
    release_chapter,
    list_chapters,
)


def _write(root: Path, name: str, text: str = "x") -> str:
    (root / name).write_text(text, encoding="utf-8")
    return name


def _prewrite() -> str:
    return (
        "# Prewrite\n"
        "Chapter function: introduce the signal.\n"
        "Three-event chain: wake / hear / disagree.\n"
        "Central choice: trust or not.\n"
        "Voice anchors: terse, cold.\n"
        "Forbidden drift: no exposition.\n"
        "Human-writing constraints: show through action.\n"
    )


_DRAFT_BODY = "# Chapter One\ndraft"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _editor(draft_text: str = _DRAFT_BODY) -> str:
    return (
        "# Editor\n"
        "DEAI: clean.\n"
        "Audience respect: kept.\n"
        "reviewed_fulltext: true\n"
        f"candidate_sha256: {_sha(draft_text)}\n"
        "CROSS_CHAPTER_CONSISTENCY: PASS\n"
    )


def _reader(draft_text: str = _DRAFT_BODY) -> str:
    return (
        "# Reader\n"
        "Real reading experience: immersive.\n"
        "Immersion: high.\n"
        "Over-explanation: none.\n"
        "reviewed_fulltext: true\n"
        f"candidate_sha256: {_sha(draft_text)}\n"
        "CROSS_CHAPTER_CONSISTENCY: PASS\n"
    )


def _prep_locked(root: Path, chapter_title: str = "Chapter One") -> None:
    init_project(root, "Ledger Book")
    record_idea(root, "idea", complete_intake_example())
    review_concept(root, "PASS", _write(root, "concept.md", "PASS"), "controller:c")
    write_bible(root, _write(root, "bible.md", "bible"))
    for level in ("master", "volume", "chapter"):
        _write(root, f"o-{level}.md", f"Title (working): {chapter_title}\n{level}")
        write_outline(root, level, f"o-{level}.md")
        review_outline(root, level, "PASS", _write(root, f"o-{level}-r.md", "PASS"), f"controller:{level}-r")
    lock_outline(root)


class LedgerTest(unittest.TestCase):
    def test_list_chapters_reflects_issued_chapters(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _prep_locked(root)
            issue_chapter(root, 1, "Chapter One", "goal one")
            issue_chapter(root, 2, "Chapter Two", "goal two")
            ledger = list_chapters(root)
            self.assertEqual(set(ledger), {"1", "2"})
            self.assertEqual(ledger["1"]["status"], "ISSUED")
            self.assertEqual(ledger["2"]["title"], "Chapter Two")

    def test_ledger_updates_after_release(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _prep_locked(root)
            issue_chapter(root, 1, "Chapter One", "goal")
            record_draft(root, 1, _write(root, "d.md", "# Chapter One\ndraft"),
                         _write(root, "pre.md", _prewrite()), "author:a")
            review_chapter(root, 1, "editor", "PASS", _write(root, "ed.md", _editor()), "editor:b")
            review_chapter(root, 1, "reader", "PASS", _write(root, "rd.md", _reader()), "reader:c")
            review_chapter(root, 1, "military", "SKIP_WITH_REASON",
                           _write(root, "m.md"), "military_consultant:d", reason="none")
            review_chapter(root, 1, "science", "SKIP_WITH_REASON",
                           _write(root, "s.md"), "science_consultant:e", reason="none")
            release_chapter(root, 1)
            ledger = list_chapters(root)
            self.assertEqual(ledger["1"]["status"], "RELEASED")
            self.assertIsNotNone(ledger["1"]["released_at"])

    def test_ledger_reflects_repair_reset(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _prep_locked(root)
            issue_chapter(root, 1, "Chapter One", "goal")
            record_draft(root, 1, _write(root, "d.md", "# Chapter One\ndraft"),
                         _write(root, "pre.md", _prewrite()), "author:a")
            review_chapter(root, 1, "editor", "PASS", _write(root, "ed.md", _editor()), "editor:b")
            review_chapter(root, 1, "reader", "FAIL", _write(root, "rd.md", _reader()), "reader:c")
            # chapter is BLOCKED; repair resets editor+reader
            repair_chapter(root, 1, _write(root, "d2.md", "# Chapter One\ndraft v2", ), ["editor", "reader"])
            ledger = list_chapters(root)
            self.assertEqual(ledger["1"]["status"], "IN_REVIEW")
            self.assertEqual(ledger["1"]["gates"]["editor"], "PENDING")
            self.assertEqual(ledger["1"]["gates"]["reader"], "PENDING")


class SourceAlignmentTest(unittest.TestCase):
    def test_draft_title_mismatch_with_outline_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            # outline declares title "Chapter One"
            _prep_locked(root, chapter_title="Chapter One")
            issue_chapter(root, 1, "Chapter One", "goal")
            # draft carries a different title
            draft = _write(root, "d.md", "# Wrong Title\nbody")
            pre = _write(root, "pre.md", _prewrite())
            with self.assertRaises(ValueError) as ctx:
                record_draft(root, 1, draft, pre, "author:a")
            self.assertIn("SOURCE_MISMATCH", str(ctx.exception))

    def test_draft_title_match_is_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _prep_locked(root, chapter_title="Chapter One")
            issue_chapter(root, 1, "Chapter One", "goal")
            draft = _write(root, "d.md", "# Chapter One\nbody")
            pre = _write(root, "pre.md", _prewrite())
            state = record_draft(root, 1, draft, pre, "author:a")
            self.assertEqual(state["status"], "IN_REVIEW")


class ChaptersCLITest(unittest.TestCase):
    def test_chapters_command_emits_ledger_json(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _prep_locked(root)
            issue_chapter(root, 1, "Chapter One", "goal one")
            env = {"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
            proc = subprocess.run(
                [sys.executable, "-m", "novel_workflow.cli", "chapters", str(root)],
                capture_output=True, text=True, env={**__import__("os").environ, **env},
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertIn("chapters", payload)
            self.assertIn("1", payload["chapters"])
            self.assertEqual(payload["chapters"]["1"]["title"], "Chapter One")


if __name__ == "__main__":
    unittest.main()
