"""Stdlib-only ANSI helpers for opt-in human-friendly CLI output.

The core workflow always returns machine-readable JSON by default. This
module powers an opt-in ``--human`` flag for inspection commands
(``status``, ``check``, ``chapters``, ``roles``, ``intake-check``).

Design rules (keep this module boring on purpose):

- Pure stdlib. Never import ``rich`` / ``colorama`` / ``click``.
- Respect ``NO_COLOR`` (https://no-color.org) and non-TTY stdout.
- When color is disabled, return plain text with the same shape so
  ``--help`` examples and CI logs stay readable.
- Never embed provider names, model names, or file paths in style codes.
  Style is generic role / status semantics only.

The module is intentionally small: a palette, a few helpers, and one
renderer per supported command. Keep it that way.
"""
from __future__ import annotations

import os
import shutil
import sys
from typing import Any, Iterable, Mapping, Sequence

# --- color detection ----------------------------------------------------

def is_color_enabled() -> bool:
    """Return True only when ANSI color is safe and desired.

    Disabled when:
    - stdout is not a TTY (piped, redirected, CI log capture)
    - ``NO_COLOR`` is set to any non-empty value (https://no-color.org)
    - ``TERM`` is ``dumb`` or empty
    """
    if not sys.stdout.isatty():
        return False
    if os.environ.get("NO_COLOR"):
        return False
    term = os.environ.get("TERM", "").strip().lower()
    if term in ("", "dumb"):
        return False
    return True


# --- low-level ANSI -----------------------------------------------------

_RESET = "\x1b[0m"
_STYLES = {
    "reset":       _RESET,
    "bold":        "\x1b[1m",
    "dim":         "\x1b[2m",
    "red":         "\x1b[31m",
    "green":       "\x1b[32m",
    "yellow":      "\x1b[33m",
    "blue":        "\x1b[34m",
    "magenta":     "\x1b[35m",
    "cyan":        "\x1b[36m",
    "bold_red":    "\x1b[1;31m",
    "bold_green":  "\x1b[1;32m",
    "bold_yellow": "\x1b[1;33m",
    "bold_cyan":   "\x1b[1;36m",
}


def paint(text: str, style: str) -> str:
    """Wrap ``text`` in the named ANSI style. No-op when color is off."""
    if not is_color_enabled():
        return text
    open_code = _STYLES.get(style, "")
    if not open_code:
        return text
    return f"{open_code}{text}{_RESET}"


# --- semantic palette ---------------------------------------------------

# Status -> (symbol, style, plain_label)
_STATUS: dict[str, tuple[str, str, str]] = {
    "PASS":              ("✓", "green",      "PASS"),
    "FAIL":              ("✗", "red",        "FAIL"),
    "PENDING":           ("◌", "yellow",     "PENDING"),
    "WRITTEN":           ("•", "dim",        "WRITTEN"),
    "SKIP_WITH_REASON":  ("–", "dim",        "SKIP"),
    "READY_TO_RELEASE":  ("●", "bold_cyan",  "READY"),
    "RELEASED":          ("★", "bold_green", "RELEASED"),
    "BLOCKED":           ("■", "bold_red",   "BLOCKED"),
    "ISSUED":            ("▸", "cyan",       "ISSUED"),
    "IN_REVIEW":         ("▸", "cyan",       "IN_REVIEW"),
    "INIT":              ("◌", "dim",        "INIT"),
    "OUTLINE_LOCKED":    ("●", "bold_cyan",  "OUTLINE_LOCKED"),
}


def symbol(status: str) -> str:
    """Return the visual marker for a status (color-aware)."""
    info = _STATUS.get(status)
    if info is None:
        return "·"
    sym, sty, _label = info
    return paint(sym, sty)


def label(status: str) -> str:
    """Return the right-aligned status label (color-aware)."""
    info = _STATUS.get(status)
    if info is None:
        return status
    _sym, sty, plain = info
    return paint(plain, sty)


# --- layout helpers -----------------------------------------------------

def _term_width(default: int = 88) -> int:
    try:
        return max(40, shutil.get_terminal_size((default, 24)).columns)
    except (OSError, ValueError):
        return default


def _row(key: str, value: str, key_width: int = 14) -> str:
    return f"  {key.ljust(key_width)}{value}"


def _box(title: str, body: Iterable[str]) -> str:
    width = _term_width()
    bar = "─" * max(8, min(width - 4, 72))
    out = [paint(f"── {title} ", "bold") + bar[: max(0, width - len(title) - 6)], ""]
    out.extend(body)
    return "\n".join(out)


# --- payload renderers --------------------------------------------------

def render_status(payload: Mapping[str, Any]) -> str:
    """Render a ``status`` payload (project + optional chapter) for humans."""
    lines: list[str] = []
    project = payload.get("project") or {}
    proj_name = project.get("title") or project.get("name") or "(project)"
    lines.append(_box(f"project · {proj_name}", [
        _row("stage:", label(str(project.get("stage", "INIT")))),
        _row("errors:", _summarize_errors(payload.get("project_errors"))),
    ]))

    chapter = payload.get("chapter")
    if chapter is not None:
        ch_lines: list[str] = []
        ch_lines.append(_row("chapter:", f"#{chapter.get('chapter', '?')} — {chapter.get('title', '')}"))
        ch_lines.append(_row("status:", f"{symbol(chapter.get('status', ''))} {label(str(chapter.get('status', '')))}"))
        # author provenance: independence dict preferred, fall back to artifacts.
        indep = chapter.get("independence") or {}
        author = indep.get("author") or (chapter.get("artifacts") or {}).get("author", {}).get("reviewer") or "—"
        ch_lines.append(_row("author:", str(author)))
        # skip_reasons at top level (e.g. {"military": "...", "science": "..."})
        skip_reasons = chapter.get("skip_reasons") or {}
        artifacts = chapter.get("artifacts") or {}
        for gate in ("editor", "reader", "military", "science"):
            art = artifacts.get(gate) or {}
            verdict = art.get("verdict") or "PENDING"
            who = art.get("reviewer") or "—"
            reason = art.get("reason") or skip_reasons.get(gate) or ""
            suffix = f"  — {reason}" if reason else ""
            ch_lines.append(_row(f"{gate}:", f"{symbol(verdict)} {label(str(verdict))}  {paint(who, 'dim')}{suffix}"))
        err_count = len(payload.get("chapter_errors") or [])
        ch_lines.append(_row("errors:", "none" if err_count == 0 else f"{err_count} issue(s)"))
        nxt = _next_action_for_chapter(chapter)
        if nxt:
            ch_lines.append(_row("next:", paint(nxt, "bold_cyan")))
        lines.append("")
        lines.append(_box(f"chapter · #{chapter.get('chapter', '?')}", ch_lines))
    return "\n".join(lines)


def render_check(payload: Mapping[str, Any]) -> str:
    """Render a ``check`` payload (project/chapter errors + security findings)."""
    lines: list[str] = []
    proj_errs = payload.get("project_errors") or []
    ch_errs = payload.get("chapter_errors") or {}
    findings = payload.get("security_findings") or []

    lines.append(_box("check · summary", [
        _row("project:", _verdict_line(proj_errs)),
        _row("chapters:", _chapters_summary(ch_errs)),
        _row("security:", _verdict_line(findings)),
    ]))
    if proj_errs:
        lines.append("")
        lines.append(_box("project issues", [f"  {paint('✗', 'red')} {e}" for e in proj_errs]))
    if findings:
        lines.append("")
        lines.append(_box("security findings", [f"  {paint('✗', 'red')} {f}" for f in findings]))
    return "\n".join(lines)


def render_chapters(payload: Mapping[str, Any]) -> str:
    """Render a ``chapters`` payload as a fixed-width table."""
    rows = payload.get("chapters") or []
    if not rows:
        return _box("chapters", ["  (no chapters issued yet)"])
    header = "  " + "ch · title".ljust(34) + "status"
    body = ["  " + f"#{c.get('chapter', '?')} {c.get('title','')}".ljust(34) + f"{symbol(c.get('status',''))} {label(str(c.get('status','')))}" for c in rows]
    return _box("chapters", [header, ""] + body)


def render_roles(payload: Mapping[str, Any]) -> str:
    """Render a ``roles`` payload as a role / responsibility table."""
    roles = payload.get("roles") or []
    charter = payload.get("charter") or {}
    rows = [f"  {paint(r, 'bold_cyan').ljust(28)}  {charter.get(r, '')}" for r in roles]
    return _box("six roles", rows)


def render_intake(report: Mapping[str, Any]) -> str:
    """Render an ``intake-check`` report for humans."""
    status = str(report.get("status", "INCOMPLETE"))
    missing = list(report.get("missing") or [])
    complete = list(report.get("complete") or [])
    verdict = "PASS" if status == "COMPLETE" else "PENDING"
    lines = [
        _row("status:", f"{symbol(verdict)} {label(verdict)}  ({status})"),
        _row("complete:", str(len(complete))),
        _row("missing:", str(len(missing))),
    ]
    if missing:
        lines.append("")
        lines.append(_box("missing fields", [f"  {paint('◌', 'yellow')} {m}" for m in missing]))
    return _box("intake", lines)


# --- internals ----------------------------------------------------------

def _summarize_errors(errs: Any) -> str:
    if not errs:
        return paint("none", "green")
    return paint(f"{len(errs)} issue(s)", "yellow")


def _verdict_line(items: Sequence[Any]) -> str:
    if not items:
        return paint("clean", "green")
    return paint(f"{len(items)} issue(s)", "yellow")


def _chapters_summary(ch_errs: Mapping[str, Sequence[Any]]) -> str:
    if not ch_errs:
        return paint("none issued", "dim")
    bad = sum(1 for v in ch_errs.values() if v)
    if bad == 0:
        return paint(f"{len(ch_errs)} checked, all clean", "green")
    return paint(f"{len(ch_errs)} checked, {bad} with issues", "yellow")


def _next_action_for_chapter(chapter: Mapping[str, Any]) -> str:
    status = str(chapter.get("status", ""))
    n = chapter.get("chapter", "?")
    if status == "READY_TO_RELEASE":
        return f"novel-workflow release <project> {n}"
    if status == "ISSUED":
        return f"novel-workflow draft <project> {n} --artifact ... --prewrite ... --author ..."
    if status == "IN_REVIEW":
        return "wait for independent reviews, or run `novel-workflow repair` if a draft must change"
    if status == "BLOCKED":
        return "address chapter_errors, then re-run `novel-workflow review`"
    if status == "RELEASED":
        return f"novel-workflow issue <project> {int(n) + 1} --title ... --goal ..."
    return ""


__all__ = [
    "is_color_enabled",
    "paint",
    "symbol",
    "label",
    "render_status",
    "render_check",
    "render_chapters",
    "render_roles",
    "render_intake",
]
