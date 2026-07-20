"""Happy-path and gate semantics tests for the six-role novel workflow."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from novel_workflow.core import (
    DOMAIN_GATES,
    INTAKE_FIELD_KEYS,
    SIX_ROLES,
    analyze_intake,
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
    release_chapter,
    validate_chapter,
)


def _make_artifact(root: Path, name: str, text: str = "content") -> str:
    p = root / name
    p.write_text(text, encoding="utf-8")
    return name


def _prewrite_text() -> str:
    return """# Prewrite card
Chapter function: introduce the disputed signal.
POV and tense: repair lead, past tense.
Entry state: crew is tired and under pressure.
Three-event chain: false alarm / impossible delay / risky confirmation.
Central choice and cost: report truth, lose safety.
Voice anchors: cold metal, delayed light, dry air.
Forbidden drift: do not solve the signal yet.
Human-writing constraints: no explanatory monologue; subtext preserved.
"""


def _draft_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _editor_text(draft_text: str = "# Draft") -> str:
    return f"""# Editor Review
DEAI: no formulaic prose or explanation dump.
Audience respect: preserves inference and necessary complexity.
Structure: contract goal is delivered.
reviewed_fulltext: true
candidate_sha256: {_draft_sha(draft_text)}
CROSS_CHAPTER_CONSISTENCY: PASS
"""


def _reader_text(draft_text: str = "# Draft") -> str:
    return f"""# Reader Review
Real reading experience: clear and tense.
Immersion: stable.
Over-explanation: no blocking restatement.
End-state pull: yes.
reviewed_fulltext: true
candidate_sha256: {_draft_sha(draft_text)}
CROSS_CHAPTER_CONSISTENCY: PASS
"""


def _science_pass_text(draft_text: str = "# Draft") -> str:
    return f"""# Science Review
Plausible: numbers are self-consistent.
Quantities cited: distance 3.0e8 m, time 1.0 s.
NUMERICAL_CONSISTENCY: PASS
reviewed_fulltext: true
candidate_sha256: {_draft_sha(draft_text)}
"""


def _skip_text() -> str:
    return "No applicable content checked."


class ProjectFlowTest(unittest.TestCase):
    def test_structured_intake_reports_next_missing_decision(self):
        report = analyze_intake({"audience": "adult readers"})
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertIn("genre", report["missing_fields"])
        self.assertEqual(report["next_question"]["field"], "genre")
        self.assertIn("copy", report["copyright_boundary"].lower())

    def test_complete_intake_covers_all_required_sections(self):
        interview = complete_intake_example()
        self.assertEqual(set(interview), set(INTAKE_FIELD_KEYS))
        report = analyze_intake(interview)
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["completion_percent"], 100.0)
        self.assertIsNone(report["next_question"])

    def test_concept_review_blocked_until_structured_intake_complete(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            init_project(root, "Incomplete")
            record_idea(root, "An idea", {"audience": "adult readers"})
            artifact = _make_artifact(root, "concept.md", "PASS")
            with self.assertRaises(ValueError) as cm:
                review_concept(root, "PASS", artifact, "controller:reviewer")
            self.assertIn("structured intake", str(cm.exception))
            self.assertIn("target_words", str(cm.exception))

    def test_full_happy_path_to_release(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            init_project(root, "Demo Novel")
            record_idea(root, "A relay crew hears an impossible signal.", complete_intake_example())
            ca = _make_artifact(root, "concept-review.md", "# Concept\nPASS")
            review_concept(root, "PASS", ca, "controller:concept-reviewer-a")
            ba = _make_artifact(root, "bible.md", "# Story Bible")
            write_bible(root, ba)
            for level in ("master", "volume", "chapter"):
                oa = _make_artifact(root, f"outline-{level}.md", f"# {level}")
                write_outline(root, level, oa)
                ra = _make_artifact(root, f"outline-{level}-review.md", f"# {level} review\nPASS")
                review_outline(root, level, "PASS", ra, f"controller:outline-{level}-reviewer")
            lock_outline(root)
            issue_chapter(root, 1, "First Signal", "Introduce the disputed signal")
            pre = _make_artifact(root, "ch1-prewrite.md", _prewrite_text())
            draft = _make_artifact(root, "ch1-draft.md", "# Draft")
            record_draft(root, 1, draft, pre, "author:writer-a")
            editor = _make_artifact(root, "ch1-editor.md", _editor_text())
            review_chapter(root, 1, "editor", "PASS", editor, "editor:reviewer-b")
            reader = _make_artifact(root, "ch1-reader.md", _reader_text())
            review_chapter(root, 1, "reader", "PASS", reader, "reader:reviewer-c")
            for gate in DOMAIN_GATES:
                aa = _make_artifact(root, f"ch1-{gate}.md", f"# {gate} skip\nNo applicable content checked.")
                review_chapter(root, 1, gate, "SKIP_WITH_REASON", aa, f"{gate}:consultant", reason="No applicable content in this chapter.")
            receipt = release_chapter(root, 1)
            self.assertEqual(receipt["status"], "RELEASED")
            self.assertEqual(validate_chapter(receipt), [])

    def test_six_roles_present(self):
        self.assertEqual(len(SIX_ROLES), 6)
        for role in ("controller", "author", "editor", "reader", "military_consultant", "science_consultant"):
            self.assertIn(role, SIX_ROLES)

    def test_domain_skip_requires_reason(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep_locked_outline(root)
            issue_chapter(root, 1, "T", "G")
            pre = _make_artifact(root, "pre.md", _prewrite_text())
            draft = _make_artifact(root, "draft.md", "# Draft")
            record_draft(root, 1, draft, pre, "author:a")
            art = _make_artifact(root, "mil.md")
            with self.assertRaises(ValueError):
                review_chapter(root, 1, "military", "SKIP_WITH_REASON", art, "military:x", reason="")

    def test_domain_pending_blocks_release(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep_locked_outline(root)
            issue_chapter(root, 1, "T", "G")
            pre = _make_artifact(root, "pre.md", _prewrite_text())
            draft = _make_artifact(root, "draft.md", "# Draft")
            record_draft(root, 1, draft, pre, "author:a")
            editor = _make_artifact(root, "editor.md", _editor_text())
            review_chapter(root, 1, "editor", "PASS", editor, "editor:b")
            reader = _make_artifact(root, "reader.md", _reader_text())
            review_chapter(root, 1, "reader", "PASS", reader, "reader:c")
            with self.assertRaises(ValueError):
                release_chapter(root, 1)

    def test_independence_enforced(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep_locked_outline(root)
            issue_chapter(root, 1, "T", "G")
            pre = _make_artifact(root, "pre.md", _prewrite_text())
            draft = _make_artifact(root, "draft.md", "# Draft")
            record_draft(root, 1, draft, pre, "author:same-entity")
            art = _make_artifact(root, "ed.md", _editor_text())
            with self.assertRaises(ValueError):
                review_chapter(root, 1, "editor", "PASS", art, "editor:same-entity")

    def _prep_locked_outline(self, root: Path):
        init_project(root, "Demo")
        record_idea(root, "idea", complete_intake_example())
        ca = _make_artifact(root, "concept.md", "PASS")
        review_concept(root, "PASS", ca, "controller:r")
        ba = _make_artifact(root, "bible.md")
        write_bible(root, ba)
        for level in ("master", "volume", "chapter"):
            oa = _make_artifact(root, f"o-{level}.md", "x")
            write_outline(root, level, oa)
            ra = _make_artifact(root, f"o-{level}-r.md", "PASS")
            review_outline(root, level, "PASS", ra, f"controller:{level}-r")
        lock_outline(root)


if __name__ == "__main__":
    unittest.main()
