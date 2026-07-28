"""Tests for the public release deny-list and scanner composition.

These tests cover the regex contracts in :mod:`novel_workflow._security` so
the scanner cannot drift back into flagging README badge links,
documentation references, and other well-known non-coupling URLs while
still catching real hardcoded API endpoints.
"""
from __future__ import annotations

import unittest

from novel_workflow._security import (
    SERVICE_COUPLING,
    SERVICE_COUPLING_URL,
    SERVICE_COUPLING_VAR,
    deny_list_findings,
)


class ServiceCouplingVarTest(unittest.TestCase):
    """Variable-style coupling is always flagged, regardless of context."""

    def test_flags_base_url(self):
        self.assertTrue(SERVICE_COUPLING_VAR.search('base_url = "https://x"'))

    def test_flags_endpoint_url(self):
        self.assertTrue(SERVICE_COUPLING_VAR.search("endpoint_url: 'x'"))

    def test_flags_api_endpoint(self):
        self.assertTrue(SERVICE_COUPLING_VAR.search("api_endpoint = 'x'"))

    def test_flags_model_id(self):
        self.assertTrue(SERVICE_COUPLING_VAR.search('model_id = "gpt-4"'))

    def test_flags_model_name(self):
        self.assertTrue(SERVICE_COUPLING_VAR.search('model_name: "claude"'))

    def test_flags_bearer(self):
        self.assertTrue(SERVICE_COUPLING_VAR.search("bearer abc12345678"))

    def test_does_not_flag_bare_prose(self):
        self.assertIsNone(SERVICE_COUPLING_VAR.search("plain prose mentions nothing"))


class ServiceCouplingUrlTest(unittest.TestCase):
    """URL-style coupling is only flagged when the path looks like an API endpoint."""

    def test_flags_openai_chat_completions(self):
        self.assertTrue(
            SERVICE_COUPLING_URL.search("https://api.openai.com/v1/chat/completions")
        )

    def test_flags_openai_v1_with_trailing_path(self):
        self.assertTrue(
            SERVICE_COUPLING_URL.search("https://api.openai.com/v1/embeddings")
        )

    def test_flags_anthropic_messages(self):
        self.assertTrue(
            SERVICE_COUPLING_URL.search("https://api.anthropic.com/v1/messages")
        )

    def test_flags_url_with_api_segment_at_end(self):
        # /v1/chat without trailing slash should still be flagged.
        self.assertTrue(
            SERVICE_COUPLING_URL.search("https://api.deepseek.com/v1/chat")
        )

    def test_flags_provider_api_chat(self):
        # /api/chat with two segments.
        self.assertTrue(
            SERVICE_COUPLING_URL.search("https://provider.example.com/api/chat")
        )

    def test_does_not_flag_github_repo_link(self):
        self.assertIsNone(
            SERVICE_COUPLING_URL.search(
                "https://github.com/realwindjpn/novel-agent-workflow"
            )
        )

    def test_does_not_flag_github_blob_link(self):
        self.assertIsNone(
            SERVICE_COUPLING_URL.search(
                "https://github.com/realwindjpn/novel-agent-workflow/blob/main/README.md"
            )
        )

    def test_does_not_flag_github_actions_badge(self):
        self.assertIsNone(
            SERVICE_COUPLING_URL.search(
                "https://github.com/realwindjpn/novel-agent-workflow"
                "/actions/workflows/ci.yml/badge.svg"
            )
        )

    def test_does_not_flag_shields_badge(self):
        self.assertIsNone(
            SERVICE_COUPLING_URL.search(
                "https://img.shields.io/badge/license-Apache_2.0-blue.svg"
            )
        )

    def test_does_not_flag_no_color(self):
        self.assertIsNone(SERVICE_COUPLING_URL.search("https://no-color.org"))

    def test_does_not_flag_python_org(self):
        self.assertIsNone(SERVICE_COUPLING_URL.search("https://python.org/downloads"))

    def test_does_not_flag_apache_license(self):
        self.assertIsNone(
            SERVICE_COUPLING_URL.search("https://www.apache.org/licenses/LICENSE-2.0")
        )

    def test_does_not_flag_creative_commons(self):
        self.assertIsNone(
            SERVICE_COUPLING_URL.search("https://creativecommons.org/licenses/by/4.0/")
        )

    def test_does_not_flag_bare_docs_link(self):
        self.assertIsNone(
            SERVICE_COUPLING_URL.search("See https://docs.example.com for more info.")
        )


class ComposedServiceCouplingTest(unittest.TestCase):
    """The composed ``SERVICE_COUPLING`` matches both variable and URL styles."""

    def test_url_match(self):
        self.assertTrue(
            SERVICE_COUPLING.search("https://api.openai.com/v1/chat/completions")
        )

    def test_variable_match(self):
        self.assertTrue(SERVICE_COUPLING.search("base_url = 'x'"))

    def test_badge_does_not_match(self):
        self.assertIsNone(
            SERVICE_COUPLING.search("https://img.shields.io/badge/license-Apache_2.0-blue.svg")
        )

    def test_no_color_does_not_match(self):
        self.assertIsNone(SERVICE_COUPLING.search("https://no-color.org"))


class DenyListFindingsTest(unittest.TestCase):
    """End-to-end checks via :func:`deny_list_findings`."""

    def test_readme_with_badges_is_clean(self):
        # A realistic README with badge links must not produce any findings.
        readme = (
            "# Project\n\n"
            "[![CI](https://github.com/owner/repo/actions/workflows/ci.yml/badge.svg)]"
            "(https://github.com/owner/repo/actions/workflows/ci.yml)\n"
            "[![License](https://img.shields.io/badge/license-Apache_2.0-blue.svg)](LICENSE)\n"
            "[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)\n"
            "[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](pyproject.toml)\n"
            "[![Runtime deps](https://img.shields.io/badge/runtime_deps-0-green.svg)](pyproject.toml)\n\n"
            "See https://no-color.org and https://python.org for standards.\n"
        )
        self.assertEqual(deny_list_findings("README.md", readme), [])

    def test_visual_module_no_color_reference_is_clean(self):
        text = (
            "Stdlib-only ANSI helpers.\n"
            "- Respect NO_COLOR (https://no-color.org) and non-TTY stdout.\n"
            "- NO_COLOR is set to any non-empty value (https://no-color.org).\n"
        )
        self.assertEqual(deny_list_findings("src/novel_workflow/_visual.py", text), [])

    def test_real_api_endpoint_in_docs_is_flagged(self):
        text = (
            "Configure your endpoint:\n"
            "  base_url = 'https://api.openai.com/v1'\n"
            "  curl https://api.openai.com/v1/chat/completions\n"
        )
        findings = deny_list_findings("docs/private.md", text)
        self.assertTrue(any("external service coupling" in f for f in findings))


if __name__ == "__main__":
    unittest.main()
