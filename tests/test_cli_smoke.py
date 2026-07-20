"""CLI-level illegal-transition smoke tests.

These exercise the argparse entrypoint, not just the core API, to ensure the
state machine blocks false completion through the public CLI surface.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from novel_workflow.core import complete_intake_example

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


def _run(args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "novel_workflow.cli", *args],
        cwd=cwd,
        env=ENV,
        capture_output=True,
        text=True,
    )


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


DRAFT_TEXT = "# Draft\n"
DRAFT_SHA = hashlib.sha256(DRAFT_TEXT.encode("utf-8")).hexdigest()

PREWRITE = """# Prewrite
Chapter function: introduce the disputed signal.
Three-event chain: false alarm / impossible delay / risky confirmation.
Central choice and cost: report truth, lose safety.
Voice anchors: cold metal, delayed light, dry air.
Forbidden drift: do not solve the signal yet.
Human-writing constraints: no explanatory monologue; subtext preserved.
"""

EDITOR = f"""# Editor Review
DEAI: no formulaic prose.
Audience respect: preserves inference.
reviewed_fulltext: true
candidate_sha256: {DRAFT_SHA}
CROSS_CHAPTER_CONSISTENCY: PASS
"""

READER = f"""# Reader Review
Real reading experience: clear and tense.
Immersion: stable.
Over-explanation: no blocking restatement.
reviewed_fulltext: true
candidate_sha256: {DRAFT_SHA}
CROSS_CHAPTER_CONSISTENCY: PASS
"""


class CLISmokeTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _write(self.root / "bible.md", "# Story Bible\n")
        _write(self.root / "master.md", "# Master\n")
        _write(self.root / "master-review.md", "PASS\n")
        _write(self.root / "volume.md", "# Volume\n")
        _write(self.root / "volume-review.md", "PASS\n")
        _write(self.root / "chapter-outline.md", "# Chapter Outline\n")
        _write(self.root / "chapter-outline-review.md", "PASS\n")
        _write(self.root / "concept-review.md", "PASS\n")
        _write(self.root / "prewrite.md", PREWRITE)
        _write(self.root / "draft.md", "# Draft\n")
        _write(self.root / "editor.md", EDITOR)
        _write(self.root / "reader.md", READER)
        _write(self.root / "military.md", "No military content checked.\n")
        _write(self.root / "science.md", "No science content checked.\n")

    def tearDown(self):
        self._tmp.cleanup()

    def _init_and_idea(self):
        _run(["init", str(self.root), "--title", "Smoke"], cwd=ROOT)
        _run([
            "idea", str(self.root),
            "--summary", "A relay crew hears an impossible signal.",
            "--interview", json.dumps(complete_intake_example()),
        ], cwd=ROOT)

    def test_cannot_issue_chapter_before_outline_lock(self):
        self._init_and_idea()
        _run(["concept-review", str(self.root), "PASS", "--artifact", "concept-review.md", "--reviewer", "controller:c"], cwd=ROOT)
        _run(["bible", str(self.root), "--artifact", "bible.md"], cwd=ROOT)
        res = _run(["issue", str(self.root), "1", "--title", "T", "--goal", "G"], cwd=ROOT)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("must be LOCKED", res.stdout + res.stderr)

    def test_cannot_release_before_all_gates(self):
        self._init_and_idea()
        _run(["concept-review", str(self.root), "PASS", "--artifact", "concept-review.md", "--reviewer", "controller:c"], cwd=ROOT)
        _run(["bible", str(self.root), "--artifact", "bible.md"], cwd=ROOT)
        _run(["outline-write", str(self.root), "master", "--artifact", "master.md"], cwd=ROOT)
        _run(["outline-review", str(self.root), "master", "PASS", "--artifact", "master-review.md", "--reviewer", "controller:m"], cwd=ROOT)
        _run(["outline-write", str(self.root), "volume", "--artifact", "volume.md"], cwd=ROOT)
        _run(["outline-review", str(self.root), "volume", "PASS", "--artifact", "volume-review.md", "--reviewer", "controller:v"], cwd=ROOT)
        _run(["outline-write", str(self.root), "chapter", "--artifact", "chapter-outline.md"], cwd=ROOT)
        _run(["outline-review", str(self.root), "chapter", "PASS", "--artifact", "chapter-outline-review.md", "--reviewer", "controller:ch"], cwd=ROOT)
        _run(["outline-lock", str(self.root)], cwd=ROOT)
        _run(["issue", str(self.root), "1", "--title", "T", "--goal", "G"], cwd=ROOT)
        res = _run(["release", str(self.root), "1"], cwd=ROOT)
        self.assertNotEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertIn("no draft to release", payload["error"])

    def test_release_requires_explicit_command_after_ready(self):
        self._init_and_idea()
        _run(["concept-review", str(self.root), "PASS", "--artifact", "concept-review.md", "--reviewer", "controller:c"], cwd=ROOT)
        _run(["bible", str(self.root), "--artifact", "bible.md"], cwd=ROOT)
        _run(["outline-write", str(self.root), "master", "--artifact", "master.md"], cwd=ROOT)
        _run(["outline-review", str(self.root), "master", "PASS", "--artifact", "master-review.md", "--reviewer", "controller:m"], cwd=ROOT)
        _run(["outline-write", str(self.root), "volume", "--artifact", "volume.md"], cwd=ROOT)
        _run(["outline-review", str(self.root), "volume", "PASS", "--artifact", "volume-review.md", "--reviewer", "controller:v"], cwd=ROOT)
        _run(["outline-write", str(self.root), "chapter", "--artifact", "chapter-outline.md"], cwd=ROOT)
        _run(["outline-review", str(self.root), "chapter", "PASS", "--artifact", "chapter-outline-review.md", "--reviewer", "controller:ch"], cwd=ROOT)
        _run(["outline-lock", str(self.root)], cwd=ROOT)
        _run(["issue", str(self.root), "1", "--title", "T", "--goal", "G"], cwd=ROOT)
        _run(["draft", str(self.root), "1", "--artifact", "draft.md", "--prewrite", "prewrite.md", "--author", "author:a"], cwd=ROOT)
        _run(["review", str(self.root), "1", "editor", "PASS", "--artifact", "editor.md", "--reviewer", "editor:b"], cwd=ROOT)
        _run(["review", str(self.root), "1", "reader", "PASS", "--artifact", "reader.md", "--reviewer", "reader:c"], cwd=ROOT)
        _run(["review", str(self.root), "1", "military", "SKIP_WITH_REASON", "--artifact", "military.md", "--reviewer", "military:d", "--reason", "No military content."], cwd=ROOT)
        _run(["review", str(self.root), "1", "science", "SKIP_WITH_REASON", "--artifact", "science.md", "--reviewer", "science:e", "--reason", "No science content."], cwd=ROOT)
        status = _run(["status", str(self.root), "--chapter", "1"], cwd=ROOT)
        payload = json.loads(status.stdout)
        self.assertEqual(payload["chapter"]["status"], "READY_TO_RELEASE")
        self.assertFalse((self.root / "releases" / "chapter-1.json").exists())
        rel = _run(["release", str(self.root), "1"], cwd=ROOT)
        self.assertEqual(rel.returncode, 0)
        self.assertTrue((self.root / "releases" / "chapter-1.json").exists())


if __name__ == "__main__":
    unittest.main()
