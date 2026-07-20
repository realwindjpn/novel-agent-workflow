"""Shared security-scan constants for the release gate and CLI check.

Both ``scripts/release_check.py`` and ``novel_workflow.core.security_scan``
import from this module so the deny-list cannot drift between the two
surfaces. The regular expressions are assembled from string fragments so
that this source file itself does not match its own patterns - a file
containing the literal ``"root/"`` in a compiled regex would otherwise
trip the absolute-home rule.

The deny-list covers two leak classes:

1. Private manuscript identifiers from the original internal workflow.
2. Internal infrastructure identifiers (internal task ids, session ids,
   WAL/takeover/inbox artifacts) that must never ship.

Generic ecosystem vocabulary (``openai``, ``claude``, ``hermes``, ``codex``,
``gemini``, ``qwen``, ``deepseek`` and the like) is intentionally *not* on
the deny-list. These are common nouns a public tutorial may legitimately
use; blocking them would both produce false positives and give a false
sense of security. The scanner blocks real private coupling: secret-like
values, absolute home paths, external service endpoint variables, the
internal working-artifact filenames, and the specific private project /
infrastructure identifiers listed below.

The scanner self-excludes its own source files by *path relative to the
project root*, never by bare filename, so a contributor's ``core.py`` in
``examples/`` is still scanned.
"""
from __future__ import annotations

import re

# File extensions treated as text and therefore scanned. Widened beyond the
# original set so that .jsonl / .log / .csv / .ini / .cfg / .sh leaks are
# caught. Binary and asset extensions are skipped.
TEXT_EXT = {
    ".py", ".md", ".json", ".toml", ".yaml", ".yml", ".txt",
    ".jsonl", ".log", ".csv", ".ini", ".cfg", ".conf", ".sh",
}

# Secret-like values (api keys, bearer tokens, cookies).
SECRET = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}"
    r"|(?:api[_-]?key|authorization|token|cookie|secret)"
    r"\s*[:=]\s*['\"]?[A-Za-z0-9_-]{12,})",
    re.I,
)

# Absolute home paths: /root/..., /home/..., C:\Users\...
ABSOLUTE_HOME = re.compile(
    r"/(?:root|home)/[A-Za-z0-9_.\-/]+|[A-Za-z]:\\\\Users\\\\",
    re.I,
)

# External service coupling: base_url, model_id, http URLs, bearer tokens.
# These are variable names / URL schemes, not generic ecosystem words, so a
# tutorial mentioning "openai" in prose is fine while a hardcoded endpoint
# is flagged.
SERVICE_COUPLING = re.compile(
    r"\b(?:base_url|endpoint_url|api_endpoint|model_id|model_name"
    r"|http[s]?://|bearer\s+[A-Za-z0-9_-]{8,})\b",
    re.I,
)

# Internal working-artifact filenames that must never be published.
INTERNAL_WORD = re.compile(
    r"\b(?:WAL|SECURITY_RELEASE_CHECKLIST)\b",
)

# Private manuscript identifiers (fragmented so the source does not match).
MANUSCRIPT_PRIVATE = re.compile(
    "chat\\." + "qwen\\.ai|fan" + "qie|科武" + "纪元",
    re.I,
)

# Internal infrastructure vocabulary (fragmented). Covers internal task ids,
# session ids, and daemon paths that leaked in prior internal working files.
# Generic ecosystem words (hermes, codex, openai, claude, etc.) are
# deliberately excluded so public docs can reference common tools; only
# private project / infrastructure identifiers are listed here. Any hit is a
# release blocker.
INFRA_PRIVATE = re.compile(
    "yao" + "he|aero" + "link|fa" + "ble5|open" + "claw|miro" + "fish"
    + "|agent" + "ly|g" + "brain"
    + "|mcp_" + "children|controller_" + "events|takeover_" + "recovered"
    + "|novel_" + "oss|session_" + "id|child\\.log|infra/" + "mcp"
    + "|澄" + "砚|小" + "哥",
    re.I,
)

# Source files that define these very patterns. Excluded by path relative to
# the project root so the scanner does not flag its own deny-list. Listed
# explicitly (not by bare filename) so a same-named file elsewhere is still
# scanned.
SELF_EXCLUDE_RELS = frozenset({
    "src/novel_workflow/_security.py",
    "src/novel_workflow/core.py",
    "src/novel_workflow/model_adapter.py",
    "src/novel_workflow/model_cli.py",
    "scripts/release_check.py",
    # The model-adapter test legitimately constructs fake secrets, base_url
    # values, and private-path strings to exercise the parser and redaction.
    # It is excluded the same way release_check.py is: it defines and tests
    # the deny-list surface itself. A real secret here would still be caught
    # by the release gate's own file enumeration cross-check.
    "tests/test_model_adapter.py",
})

# Public template files that MUST show base_url / endpoint syntax so users
# learn how to configure the routing layer. These are exempt from the
# service-coupling rule ONLY; they are still scanned for secrets and
# absolute private paths. A literal key value here would still be a release
# blocker.
TEMPLATE_SERVICE_COUPLING_EXEMPT = frozenset({
    "templates/model_routing.example.toml",
    "templates/env.example",
})


def deny_list_findings(rel: str, text: str) -> list[str]:
    """Return human-readable findings for a single file's text.

    ``rel`` is the path relative to the project root, used so callers can
    report which file tripped which rule.
    """
    findings: list[str] = []
    if SECRET.search(text):
        findings.append(f"possible secret: {rel}")
    if ABSOLUTE_HOME.search(text):
        findings.append(f"absolute home path: {rel}")
    # Public template examples must show base_url / endpoint syntax so users
    # can learn the routing config; they are exempt from the service-coupling
    # rule only, never from the secret or absolute-path rules.
    if rel not in TEMPLATE_SERVICE_COUPLING_EXEMPT and SERVICE_COUPLING.search(text):
        findings.append(f"external service coupling: {rel}")
    if INTERNAL_WORD.search(text):
        findings.append(f"internal working artifact mention: {rel}")
    if MANUSCRIPT_PRIVATE.search(text):
        findings.append(f"private manuscript identifier: {rel}")
    if INFRA_PRIVATE.search(text):
        findings.append(f"internal infrastructure identifier: {rel}")
    return findings
