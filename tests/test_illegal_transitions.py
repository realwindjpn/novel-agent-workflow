"""Illegal-transition and false-completion guard tests.

These encode the PLAN requirements:
- #3 outline must be all-PASS before chapter issuance
- #4 independence + DEAI + reader double-PASS
- #5 domain gates may SKIP_WITH_REASON but may not be absent
- #6 repair resets affected gates and requires re-review
- #7 CLI/state machine blocks false completion
- #9 increased coverage of illegal transitions
"""
import hashlib
import tempfile
import unittest
from pathlib import Path

from novel_workflow.core import (
    CHAPTER_GATES,
    DOMAIN_GATES,
    PASS,
    SKIP,
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
    validate_chapter,
)


def _mk(root: Path, name: str, text: str = "x") -> str:
    p = root / name
    p.write_text(text, encoding="utf-8")
    return name


_DRAFT_TEXT = "draft body"


def _draft_sha(text: str = _DRAFT_TEXT) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _prewrite_text() -> str:
    return """# Prewrite
Chapter function: setup
POV and tense: limited past
Entry state: uncertain
Three-event chain: one / two / three
Central choice and cost: choose truth, lose safety
Voice anchors: metal, delay, cold
Forbidden drift: no exposition dump
Human-writing constraints: no explanatory monologue; subtext preserved
"""


def _editor_text(draft_text: str = _DRAFT_TEXT) -> str:
    return f"""# Editor Review
DEAI: no formulaic prose, no explanatory monologue.
Audience respect: subtext is preserved and the reader is trusted.
Structure: chapter contract delivered.
reviewed_fulltext: true
candidate_sha256: {_draft_sha(draft_text)}
CROSS_CHAPTER_CONSISTENCY: PASS
"""


def _reader_text(draft_text: str = _DRAFT_TEXT) -> str:
    return f"""# Reader Review
Real reading experience: clear and immersive.
Immersion: steady; no fatigue spike.
Over-explanation: none blocking.
End-state pull: wants next chapter.
reviewed_fulltext: true
candidate_sha256: {_draft_sha(draft_text)}
CROSS_CHAPTER_CONSISTENCY: PASS
"""


def _science_pass_text(draft_text: str = _DRAFT_TEXT) -> str:
    return f"""# Science Review
Plausible: consistent.
NUMERICAL_CONSISTENCY: PASS
reviewed_fulltext: true
candidate_sha256: {_draft_sha(draft_text)}
"""


def _locked_outline(root: Path):
    init_project(root, "Demo")
    record_idea(root, "idea", complete_intake_example())
    ca = _mk(root, "concept.md", "PASS")
    review_concept(root, "PASS", ca, "controller:r")
    ba = _mk(root, "bible.md")
    write_bible(root, ba)
    for level in ("master", "volume", "chapter"):
        oa = _mk(root, f"o-{level}.md", "x")
        write_outline(root, level, oa)
        ra = _mk(root, f"o-{level}-r.md", "PASS")
        review_outline(root, level, "PASS", ra, f"controller:{level}-r")
    lock_outline(root)


def _chapter_ready_for_review(root: Path):
    issue_chapter(root, 1, "T", "G")
    pre = _mk(root, "pre.md", _prewrite_text())
    draft = _mk(root, "draft.md", _DRAFT_TEXT)
    record_draft(root, 1, draft, pre, "author:a")


def _pass_editor_reader_domain(root: Path):
    editor = _mk(root, "editor.md", _editor_text())
    state = review_chapter(root, 1, "editor", "PASS", editor, "editor:b")
    reader = _mk(root, "reader.md", _reader_text())
    state = review_chapter(root, 1, "reader", "PASS", reader, "reader:c")
    for gate in DOMAIN_GATES:
        aa = _mk(root, f"{gate}.md", "No applicable content checked.")
        state = review_chapter(root, 1, gate, "SKIP_WITH_REASON", aa, f"{gate}:x", reason="No applicable content in this chapter.")
    return state


class IllegalTransitionTest(unittest.TestCase):
    def test_public_chapter_gates_are_six_role_only(self):
        # Continuity is a responsibility inside review evidence, not a seventh role/gate.
        self.assertEqual(CHAPTER_GATES, ("author", "editor", "reader", "military", "science"))

    def test_cannot_issue_chapter_without_locked_outline(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            init_project(root, "Demo")
            with self.assertRaises(ValueError):
                issue_chapter(root, 1, "T", "G")

    def test_cannot_lock_outline_with_unreviewed_level(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            init_project(root, "Demo")
            record_idea(root, "idea", complete_intake_example())
            ca = _mk(root, "concept.md", "PASS")
            review_concept(root, "PASS", ca, "controller:r")
            ba = _mk(root, "bible.md")
            write_bible(root, ba)
            oa = _mk(root, "o-master.md", "x")
            write_outline(root, "master", oa)
            ra = _mk(root, "o-master-r.md", "PASS")
            review_outline(root, "master", "PASS", ra, "controller:m-r")
            ov = _mk(root, "o-volume.md", "x")
            write_outline(root, "volume", ov)
            rv = _mk(root, "o-volume-r.md", "PASS")
            review_outline(root, "volume", "PASS", rv, "controller:v-r")
            oc = _mk(root, "o-chapter.md", "x")
            write_outline(root, "chapter", oc)
            with self.assertRaises(ValueError):
                lock_outline(root)

    def test_cannot_write_bible_before_concept_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            init_project(root, "Demo")
            record_idea(root, "idea", complete_intake_example())
            ba = _mk(root, "bible.md")
            with self.assertRaises(ValueError):
                write_bible(root, ba)

    def test_cannot_write_outline_before_bible(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            init_project(root, "Demo")
            record_idea(root, "idea", complete_intake_example())
            ca = _mk(root, "concept.md", "PASS")
            review_concept(root, "PASS", ca, "controller:r")
            oa = _mk(root, "o-master.md", "x")
            with self.assertRaises(ValueError):
                write_outline(root, "master", oa)

    def test_cannot_record_draft_without_issued_chapter(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            pre = _mk(root, "pre.md", _prewrite_text())
            draft = _mk(root, "draft.md")
            with self.assertRaises(ValueError):
                record_draft(root, 1, draft, pre, "author:a")

    def test_cannot_review_chapter_before_draft(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            issue_chapter(root, 1, "T", "G")
            art = _mk(root, "ed.md", _editor_text())
            with self.assertRaises(ValueError):
                review_chapter(root, 1, "editor", "PASS", art, "editor:b")

    def test_prewrite_card_must_include_author_role_os_constraints(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            issue_chapter(root, 1, "T", "G")
            draft = _mk(root, "draft.md", "draft")
            bare_prewrite = _mk(root, "bare-prewrite.md", "notes only")
            with self.assertRaises(ValueError):
                record_draft(root, 1, draft, bare_prewrite, "author:a")

    def test_reviewer_provenance_must_match_gate_role(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            _chapter_ready_for_review(root)
            editor_art = _mk(root, "editor.md", _editor_text())
            with self.assertRaises(ValueError):
                review_chapter(root, 1, "editor", "PASS", editor_art, "reader:b")
            military_art = _mk(root, "military.md", "No military content.")
            with self.assertRaises(ValueError):
                review_chapter(root, 1, "military", "SKIP_WITH_REASON", military_art, "science:c", reason="No military content.")

    def test_editor_and_reader_pass_require_evidence_sections(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            _chapter_ready_for_review(root)
            thin_editor = _mk(root, "thin-editor.md", "PASS")
            with self.assertRaises(ValueError):
                review_chapter(root, 1, "editor", "PASS", thin_editor, "editor:b")
            good_editor = _mk(root, "good-editor.md", _editor_text())
            review_chapter(root, 1, "editor", "PASS", good_editor, "editor:b")
            thin_reader = _mk(root, "thin-reader.md", "PASS")
            with self.assertRaises(ValueError):
                review_chapter(root, 1, "reader", "PASS", thin_reader, "reader:c")

    def test_release_blocked_when_editor_failed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            _chapter_ready_for_review(root)
            art_fail = _mk(root, "ed-fail.md", "FAIL\nover-explanation: yes")
            review_chapter(root, 1, "editor", "FAIL", art_fail, "editor:b")
            reader = _mk(root, "rd.md", _reader_text())
            review_chapter(root, 1, "reader", "PASS", reader, "reader:c")
            with self.assertRaises(ValueError):
                release_chapter(root, 1)

    def test_release_blocked_without_reader_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            _chapter_ready_for_review(root)
            editor = _mk(root, "editor.md", _editor_text())
            review_chapter(root, 1, "editor", "PASS", editor, "editor:b")
            for gate in DOMAIN_GATES:
                aa = _mk(root, f"{gate}.md", "skip")
                review_chapter(root, 1, gate, "SKIP_WITH_REASON", aa, f"{gate}:x", reason="n/a")
            with self.assertRaises(ValueError):
                release_chapter(root, 1)

    def test_repair_resets_affected_gates(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            _chapter_ready_for_review(root)
            _pass_editor_reader_domain(root)
            state = release_chapter(root, 1)
            self.assertEqual(state["status"], "RELEASED")
            new_draft = _mk(root, "draft2.md", "revised")
            state = repair_chapter(root, 1, new_draft, affected_gates=["editor", "reader"])
            self.assertEqual(state["status"], "IN_REVIEW")
            self.assertEqual(state["gates"]["editor"], "PENDING")
            self.assertEqual(state["gates"]["reader"], "PENDING")
            self.assertEqual(state["gates"]["military"], "SKIP_WITH_REASON")
            with self.assertRaises(ValueError):
                release_chapter(root, 1)

    def test_repair_revokes_stale_release_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            _chapter_ready_for_review(root)
            _pass_editor_reader_domain(root)
            release_chapter(root, 1)
            receipt = root / "releases" / "chapter-1.json"
            self.assertTrue(receipt.exists())
            new_draft = _mk(root, "draft2.md", "revised")
            repair_chapter(root, 1, new_draft, affected_gates=["editor"])
            self.assertFalse(receipt.exists())

    def test_repair_then_re_review_can_release(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            _chapter_ready_for_review(root)
            _pass_editor_reader_domain(root)
            release_chapter(root, 1)
            new_draft = _mk(root, "draft2.md", "revised")
            repair_chapter(root, 1, new_draft, affected_gates=["editor", "reader"])
            editor = _mk(root, "editor2.md", _editor_text("revised"))
            review_chapter(root, 1, "editor", "PASS", editor, "editor:b2")
            reader = _mk(root, "reader2.md", _reader_text("revised"))
            review_chapter(root, 1, "reader", "PASS", reader, "reader:c2")
            state = release_chapter(root, 1)
            self.assertEqual(state["status"], "RELEASED")

    def test_all_gates_pass_is_not_released_until_release_command(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            _chapter_ready_for_review(root)
            state = _pass_editor_reader_domain(root)
            self.assertEqual(state["status"], "READY_TO_RELEASE")
            self.assertFalse((root / "releases" / "chapter-1.json").exists())

    def test_concept_fail_blocks_bible(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            init_project(root, "Demo")
            record_idea(root, "idea", complete_intake_example())
            ca = _mk(root, "concept.md", "FAIL")
            review_concept(root, "FAIL", ca, "controller:r")
            ba = _mk(root, "bible.md")
            with self.assertRaises(ValueError):
                write_bible(root, ba)

    def test_outline_review_fail_blocks_lock(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            init_project(root, "Demo")
            record_idea(root, "idea", complete_intake_example())
            ca = _mk(root, "concept.md", "PASS")
            review_concept(root, "PASS", ca, "controller:r")
            ba = _mk(root, "bible.md")
            write_bible(root, ba)
            oa = _mk(root, "o-master.md", "x")
            write_outline(root, "master", oa)
            ra = _mk(root, "o-master-r.md", "FAIL")
            review_outline(root, "master", "FAIL", ra, "controller:m-r")
            with self.assertRaises(ValueError):
                lock_outline(root)

    def test_independence_editor_reader(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            _chapter_ready_for_review(root)
            aa = _mk(root, "ed.md", _editor_text())
            review_chapter(root, 1, "editor", "PASS", aa, "editor:ent")
            ra = _mk(root, "rd.md", _reader_text())
            with self.assertRaises(ValueError):
                review_chapter(root, 1, "reader", "PASS", ra, "editor:ent")

    def test_chapter_gate_validation_catches_tampered_state(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            _chapter_ready_for_review(root)
            import json
            sp = root / ".novel-workflow" / "chapter-1.json"
            data = json.loads(sp.read_text(encoding="utf-8"))
            data["status"] = "RELEASED"
            data["gates"]["editor"] = "PASS"
            sp.write_text(json.dumps(data), encoding="utf-8")
            errors = validate_chapter(data)
            self.assertTrue(any("RELEASED" in e for e in errors))

    def test_chapter_without_artifact_dir_is_backward_compatible(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _locked_outline(root)
            _chapter_ready_for_review(root)
            sp = root / ".novel-workflow" / "chapter-1.json"
            data = json.loads(sp.read_text(encoding="utf-8"))
            # Older projects persisted chapters before artifact_dir existed;
            # validation must remain silent in that case so they keep loading.
            data.pop("artifact_dir", None)
            sp.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(validate_chapter(data), [])


class ReviewHardGateTest(unittest.TestCase):
    """Hard-gate tests for the PASS review attestation contract.

    These were previously documented conventions (reviewed_fulltext,
    candidate_sha256, CROSS_CHAPTER_CONSISTENCY, NUMERICAL_CONSISTENCY). They
    are now code gates: a PASS that skips them must be refused.
    """

    def _prep(self, root: Path):
        _locked_outline(root)
        _chapter_ready_for_review(root)

    def test_editor_pass_rejected_without_reviewed_fulltext(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep(root)
            art = _mk(root, "ed.md", _editor_text().replace("reviewed_fulltext: true", "reviewed_fulltext: false"))
            with self.assertRaises(ValueError) as cm:
                review_chapter(root, 1, "editor", "PASS", art, "editor:b")
            self.assertIn("reviewed_fulltext", str(cm.exception))

    def test_editor_pass_rejected_without_candidate_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep(root)
            art = _mk(root, "ed.md", _editor_text().replace("candidate_sha256:", "candidate_sha256_omitted:"))
            with self.assertRaises(ValueError) as cm:
                review_chapter(root, 1, "editor", "PASS", art, "editor:b")
            self.assertIn("candidate_sha256", str(cm.exception))

    def test_editor_pass_rejected_with_mismatched_candidate_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep(root)
            wrong = "0" * 64
            art = _mk(root, "ed.md", _editor_text().replace(_draft_sha(), wrong))
            with self.assertRaises(ValueError) as cm:
                review_chapter(root, 1, "editor", "PASS", art, "editor:b")
            self.assertIn("mismatch", str(cm.exception).lower())

    def test_editor_pass_rejected_without_cross_chapter_consistency(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep(root)
            art = _mk(root, "ed.md", _editor_text().replace("CROSS_CHAPTER_CONSISTENCY: PASS", "CROSS_CHAPTER_CONSISTENCY: FAIL"))
            with self.assertRaises(ValueError) as cm:
                review_chapter(root, 1, "editor", "PASS", art, "editor:b")
            self.assertIn("CROSS_CHAPTER_CONSISTENCY", str(cm.exception))

    def test_reader_pass_rejected_without_cross_chapter_consistency(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep(root)
            art = _mk(root, "rd.md", _reader_text().replace("CROSS_CHAPTER_CONSISTENCY: PASS", "CROSS_CHAPTER_CONSISTENCY: FAIL"))
            with self.assertRaises(ValueError) as cm:
                review_chapter(root, 1, "reader", "PASS", art, "reader:c")
            self.assertIn("CROSS_CHAPTER_CONSISTENCY", str(cm.exception))

    def test_reader_pass_rejected_without_reviewed_fulltext(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep(root)
            art = _mk(root, "rd.md", _reader_text().replace("reviewed_fulltext: true", "reviewed_fulltext: false"))
            with self.assertRaises(ValueError):
                review_chapter(root, 1, "reader", "PASS", art, "reader:c")

    def test_science_pass_rejected_without_numerical_consistency(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep(root)
            art = _mk(root, "sci.md", _science_pass_text().replace("NUMERICAL_CONSISTENCY: PASS", "NUMERICAL_CONSISTENCY: FAIL"))
            with self.assertRaises(ValueError) as cm:
                review_chapter(root, 1, "science", "PASS", art, "science:s")
            self.assertIn("NUMERICAL_CONSISTENCY", str(cm.exception))

    def test_science_pass_rejected_without_reviewed_fulltext(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep(root)
            art = _mk(root, "sci.md", _science_pass_text().replace("reviewed_fulltext: true", "reviewed_fulltext: false"))
            with self.assertRaises(ValueError):
                review_chapter(root, 1, "science", "PASS", art, "science:s")

    def test_science_skip_does_not_require_numerical_consistency(self):
        # SKIP_WITH_REASON is not PASS; the numerical gate does not apply.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep(root)
            art = _mk(root, "sci.md", "No applicable content checked.")
            state = review_chapter(root, 1, "science", "SKIP_WITH_REASON", art, "science:s", reason="No quantitative content.")
            self.assertEqual(state["gates"]["science"], "SKIP_WITH_REASON")

    def test_military_pass_rejected_without_reviewed_fulltext(self):
        # Domain PASS also requires full-text attestation; only SKIP is exempt.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep(root)
            art = _mk(root, "mil.md", "Plausible.\nNUMERICAL_CONSISTENCY: PASS\n")
            with self.assertRaises(ValueError):
                review_chapter(root, 1, "military", "PASS", art, "military:m")

    def test_stale_draft_sha_blocks_review_after_repair(self):
        # A review citing the old draft sha must be rejected after repair.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._prep(root)
            _pass_editor_reader_domain(root)
            release_chapter(root, 1)
            new_draft = _mk(root, "draft2.md", "revised body")
            repair_chapter(root, 1, new_draft, affected_gates=["editor"])
            # editor2 cites the OLD draft sha (_DRAFT_TEXT), not "revised body"
            stale = _mk(root, "editor2.md", _editor_text(_DRAFT_TEXT))
            with self.assertRaises(ValueError) as cm:
                review_chapter(root, 1, "editor", "PASS", stale, "editor:b2")
            self.assertIn("mismatch", str(cm.exception).lower())


if __name__ == "__main__":
    unittest.main()
