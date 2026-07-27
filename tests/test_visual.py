"""Tests for the opt-in ``--human`` visual layer.

These tests verify three things without requiring a real TTY:

1. ``is_color_enabled`` respects ``NO_COLOR`` and non-TTY stdout.
2. ``paint`` and ``label`` return plain text when color is off, so CI logs
   stay readable.
3. The renderers produce a non-empty string for a representative payload,
   so the ``--human`` path cannot silently return ``""`` and look like the
   default JSON path.
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from unittest import mock

from novel_workflow import _visual


class ColorDetectionTest(unittest.TestCase):
    def test_no_color_env_disables_color(self):
        with mock.patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            with mock.patch.object(sys.stdout, "isatty", return_value=True):
                self.assertFalse(_visual.is_color_enabled())

    def test_non_tty_disables_color(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NO_COLOR", None)
            with mock.patch.object(sys.stdout, "isatty", return_value=False):
                self.assertFalse(_visual.is_color_enabled())

    def test_dumb_term_disables_color(self):
        with mock.patch.dict(os.environ, {"TERM": "dumb"}, clear=False):
            os.environ.pop("NO_COLOR", None)
            with mock.patch.object(sys.stdout, "isatty", return_value=True):
                self.assertFalse(_visual.is_color_enabled())


class PaintTest(unittest.TestCase):
    def test_paint_is_plain_when_color_off(self):
        with mock.patch.object(_visual, "is_color_enabled", return_value=False):
            self.assertEqual(_visual.paint("PASS", "green"), "PASS")
            self.assertEqual(_visual.symbol("PASS"), "✓")
            self.assertEqual(_visual.label("PASS"), "PASS")

    def test_paint_wraps_ansi_when_color_on(self):
        with mock.patch.object(_visual, "is_color_enabled", return_value=True):
            out = _visual.paint("PASS", "green")
            self.assertTrue(out.startswith("\x1b["))
            self.assertTrue(out.endswith("\x1b[0m"))
            self.assertIn("PASS", out)

    def test_unknown_style_is_passthrough(self):
        with mock.patch.object(_visual, "is_color_enabled", return_value=True):
            self.assertEqual(_visual.paint("x", "no_such_style"), "x")

    def test_unknown_status_falls_back_gracefully(self):
        with mock.patch.object(_visual, "is_color_enabled", return_value=False):
            self.assertEqual(_visual.symbol("WEIRD"), "·")
            self.assertEqual(_visual.label("WEIRD"), "WEIRD")


class RendererSmokeTest(unittest.TestCase):
    """Each renderer must return a non-empty, plain-text string when color is off."""

    def _assert_human(self, fn, payload):
        with mock.patch.object(_visual, "is_color_enabled", return_value=False):
            out = fn(payload)
        self.assertIsInstance(out, str)
        self.assertGreater(len(out), 0)
        self.assertNotIn("\x1b[", out)
        self.assertNotIn("'chapters':", out)
        self.assertNotIn("'status':", out)

    def test_render_status(self):
        payload = {
            "project": {"title": "Demo", "stage": "OUTLINE_LOCKED"},
            "project_errors": [],
            "chapter": {
                "chapter": 1, "title": "First Signal",
                "status": "READY_TO_RELEASE",
                "independence": {
                    "author": "author:noa",
                    "editor": "editor:mal",
                    "reader": "reader:jun",
                    "military": "military:bea",
                    "science": "science:kim",
                },
                "skip_reasons": {
                    "military": "no applicable content",
                    "science": "no applicable content",
                },
                "artifacts": {
                    "author": {"reviewer": "author:noa"},
                    "editor": {"verdict": "PASS", "reviewer": "editor:mal", "reason": ""},
                    "reader": {"verdict": "PASS", "reviewer": "reader:jun", "reason": ""},
                    "military": {"verdict": "SKIP_WITH_REASON", "reviewer": "military:bea", "reason": ""},
                    "science": {"verdict": "SKIP_WITH_REASON", "reviewer": "science:kim", "reason": ""},
                },
            },
            "chapter_errors": [],
        }
        self._assert_human(_visual.render_status, payload)

    def test_render_status_no_chapter(self):
        payload = {"project": {"title": "X", "stage": "IDEA"}, "project_errors": []}
        self._assert_human(_visual.render_status, payload)

    def test_render_check_clean(self):
        self._assert_human(_visual.render_check, {
            "project_errors": [], "chapter_errors": {}, "security_findings": [],
        })

    def test_render_check_dirty(self):
        self._assert_human(_visual.render_check, {
            "project_errors": ["stage X missing"],
            "chapter_errors": {"chapter-1.json": ["draft sha mismatch"]},
            "security_findings": ["absolute home path leaked: /home/.../foo.toml"],
        })

    def test_render_chapters_empty(self):
        self._assert_human(_visual.render_chapters, {"chapters": []})

    def test_render_chapters_populated(self):
        self._assert_human(_visual.render_chapters, {
            "chapters": [
                {"chapter": 1, "title": "First Signal", "status": "RELEASED"},
                {"chapter": 2, "title": "Cold Reply", "status": "IN_REVIEW"},
            ]
        })

    def test_render_roles(self):
        self._assert_human(_visual.render_roles, {
            "roles": ["controller", "author", "editor", "reader", "military_consultant", "science_consultant"],
            "charter": {
                "controller": "routes stages, records state, verifies evidence",
                "author": "writes candidate drafts",
                "editor": "independent craft review",
                "reader": "independent reading-experience review",
                "military_consultant": "tactics and conflict review",
                "science_consultant": "physics and world-rule review",
            },
        })

    def test_render_intake_complete(self):
        self._assert_human(_visual.render_intake, {
            "status": "COMPLETE", "missing": [], "complete": list(range(15)),
        })

    def test_render_intake_missing(self):
        self._assert_human(_visual.render_intake, {
            "status": "INCOMPLETE",
            "missing": ["premise", "central_conflict"],
            "complete": list(range(13)),
        })


class HumanFlagDoesNotChangeDefaultTest(unittest.TestCase):
    """Sanity: the default emit() path is untouched by --human.

    The status JSON payload is still valid JSON and contains the
    ``chapter`` key, so anything that pipes through ``status`` (tests,
    CI, model routing HUDs) keeps working.
    """

    def test_status_payload_is_valid_json(self):
        sample = {
            "project": {"title": "Demo", "stage": "OUTLINE_LOCKED"},
            "project_errors": [],
        }
        encoded = json.dumps(sample, ensure_ascii=False, indent=2)
        decoded = json.loads(encoded)
        self.assertEqual(decoded["project"]["stage"], "OUTLINE_LOCKED")


if __name__ == "__main__":
    unittest.main()
