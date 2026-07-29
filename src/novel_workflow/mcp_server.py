"""Zero-dependency stdio MCP server for novel-agent-workflow.

Wraps the ``core`` state machine as Model Context Protocol tools,
exposes the project's state files as MCP resources, and renders the
six role charters as MCP prompts. The transport is newline-delimited
JSON-RPC 2.0 over ``stdin``/``stdout`` (one JSON object per line,
no embedded raw newlines). See ``docs/MCP.md`` for the design.

Hard rules enforced here (all lifted from ``core``'s invariants, not
added by this module):

- the server is single-process, single-threaded, and serial: one JSON
  request in, one JSON response out, in order. There is no internal
  queue, no ``asyncio``, and no signal-based timeout (the client owns
  end-to-end liveness).
- the server never writes to ``workflow.json`` or to
  ``.novel-workflow/**`` directly. Those files are only ever mutated
  by the state-machine tools, which call into ``core``.
- the server never imports ``model_adapter`` and never opens a socket.
  Any tool that does networking is a misuse; this server has none.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

from . import core
from .core import (
    DOMAIN_GATES,
    OUTLINE_LEVELS,
    REVIEW_GATES,
    ROLE_CHARTER,
    SIX_ROLES,
    DEFAULT_LIMITS,
    load_limits,
    analyze_intake,
    init_project,
    record_idea,
    review_concept,
    repair_concept,
    write_bible,
    write_outline,
    review_outline,
    repair_outline,
    lock_outline,
    issue_chapter,
    record_draft,
    review_chapter,
    repair_chapter,
    release_chapter,
    list_chapters,
    validate_chapter,
    validate_project,
    security_scan,
    load_json,
    save_json,
)

# --- protocol constants --------------------------------------------------
PROTOCOL_VERSIONS: tuple[str, ...] = (
    "2025-06-18",
    "2025-03-26",
    "2024-11-05",
)
DEFAULT_PROTOCOL_VERSION = PROTOCOL_VERSIONS[-1]

SERVER_NAME = "novel-workflow"
SERVER_VERSION = "0.3.0"

# The instructions string is the single place where the workflow's
# invariants are stated to the agent at handshake time. Keep it short
# (agents paraphrase long instructions away) and concrete (every claim
# is something the state machine will refuse to violate anyway).
INSTRUCTIONS = (
    "You are driving a six-role, gate-driven long-form fiction workflow. "
    "Every state transition is recorded in workflow.json + per-chapter state "
    "files, and every transition is checked by the core state machine.\n\n"
    "The six roles are controller, author, editor, reader, "
    "military_consultant, science_consultant. A reviewer is named as "
    "'role:identifier' (e.g. 'editor:mal'); the identifier is what the "
    "engine uses for independence checks. Editor and reader must not share "
    "an identifier with the author, and the reader must differ from the "
    "editor.\n\n"
    "A PASS review on a chapter must attest it read the full current draft: "
    "the review artifact must contain 'reviewed_fulltext: true' and a "
    "'candidate_sha256' line matching the sha256 of the draft under review. "
    "Editor and reader PASS reviews additionally need "
    "'CROSS_CHAPTER_CONSISTENCY: PASS'; science additionally needs "
    "'NUMERICAL_CONSISTENCY: PASS'. Military and science may "
    "'SKIP_WITH_REASON' but the reason is required; a missing PENDING is "
    "treated as a fail.\n\n"
    "A chapter is only 'RELEASED' when an explicit 'release' call succeeds. "
    "'The last review passed' never implies release. 'repair' resets the "
    "named gates to PENDING, removes the matching reviewer provenance, and "
    "deletes the release receipt if any; never treat a repair as silent.\n\n"
    "Always read the project root's README and docs/BEGINNER_GUIDE.md, and "
    "the role's own skills/<role>/SKILL.md, before producing an artifact. "
    "Use 'write_artifact' to lay down artifact text; never write to "
    "workflow.json or .novel-workflow/ directly. Use 'resources/read' to "
    "load state; 'novel://state', 'novel://events', 'novel://chapter/{n}'."
)


# --- I/O helpers ---------------------------------------------------------
def _log(message: str) -> None:
    """Write a diagnostic line to stderr; never to stdout."""
    sys.stderr.write(f"[mcp] {message}\n")
    sys.stderr.flush()


def _read_message() -> dict | None:
    """Read one JSON-RPC frame from stdin.

    Returns ``None`` for blank lines (silently skipped) and raises
    ``EOFError`` when stdin closes. Raises ``ValueError`` for malformed
    JSON so the caller can produce a ``-32700`` parse-error response.
    """
    line = sys.stdin.readline()
    if not line:
        raise EOFError
    line = line.strip()
    if not line:
        return None
    return json.loads(line)


def _write_message(message: dict) -> None:
    """Serialize and write one JSON-RPC frame to stdout, flushed."""
    sys.stdout.write(json.dumps(message, ensure_ascii=False))
    sys.stdout.write("\n")
    sys.stdout.flush()


# --- error helpers -------------------------------------------------------
def _tool_error(text: str) -> dict:
    """Return a tool result with ``isError: true`` (business error)."""
    return {"content": [{"type": "text", "text": text}], "isError": True}


def _protocol_error(code: int, message: str, request_id: Any) -> dict:
    """Return a JSON-RPC error envelope."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


# --- jail + limits helpers ----------------------------------------------
def _resolve_artifact_path(root: Path, rel: str) -> Path:
    """Resolve ``rel`` against ``root`` and enforce the project jail.

    Returns the resolved path. Raises ``ValueError`` if the resolved
    path escapes the project root or is empty.
    """
    if not rel or not isinstance(rel, str):
        raise ValueError("artifact path is required")
    target = (root / rel).resolve()
    root_resolved = root.resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise ValueError("artifact path must stay inside project root")
    return target


def _is_state_path(rel: Path) -> bool:
    """True for paths that must be mutated only through state-machine tools."""
    if rel.name == "workflow.json":
        return True
    if rel.parts and rel.parts[0] == ".novel-workflow":
        return True
    return False


# --- file tools ---------------------------------------------------------
def _do_write_artifact(root: Path, args: dict, limits: dict) -> dict:
    rel = args.get("path")
    content = args.get("content")
    if not isinstance(rel, str) or not rel:
        raise ValueError("path (string) is required")
    if not isinstance(content, str):
        raise ValueError("content (string) is required")
    target = _resolve_artifact_path(root, rel)
    rel_posix = target.relative_to(root.resolve()).as_posix()
    if _is_state_path(target.relative_to(root.resolve())):
        raise ValueError(
            f"writing to '{rel_posix}' is not allowed via MCP; "
            "mutate state through the state-machine tools"
        )
    encoded = content.encode("utf-8")
    if len(encoded) > limits["max_artifact_bytes"]:
        raise ValueError(
            f"content exceeds max_artifact_bytes "
            f"({limits['max_artifact_bytes']}); write refused"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    # Preserve the caller's UTF-8 bytes exactly on every platform.  Path.write_text
    # applies Windows newline translation by default, which made a requested LF
    # round-trip as CRLF through write_artifact/read_artifact.
    target.write_bytes(encoded)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {"path": rel_posix, "bytes": len(encoded)},
                    ensure_ascii=False,
                ),
            }
        ]
    }


def _do_read_artifact(root: Path, args: dict, limits: dict) -> dict:
    rel = args.get("path")
    if not isinstance(rel, str) or not rel:
        raise ValueError("path (string) is required")
    target = _resolve_artifact_path(root, rel)
    rel_posix = target.relative_to(root.resolve()).as_posix()
    if _is_state_path(target.relative_to(root.resolve())):
        raise ValueError(
            f"reading '{rel_posix}' via read_artifact is not allowed; "
            "use resources/read (novel://state, novel://chapter/{n})"
        )
    if not target.exists():
        raise ValueError(f"artifact not found: {rel_posix}")
    raw = target.read_bytes()
    if len(raw) > limits["max_read_bytes"]:
        raise ValueError(
            f"artifact exceeds max_read_bytes ({limits['max_read_bytes']}); "
            "read refused"
        )
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {"path": rel_posix, "bytes": len(raw), "text": raw.decode("utf-8", errors="replace")},
                    ensure_ascii=False,
                ),
            }
        ]
    }


# --- state-machine tools ------------------------------------------------
def _do_init(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    title = args.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title (non-empty string) is required")
    proj = init_project(path, title.strip())
    return {"content": [{"type": "text", "text": json.dumps(proj, ensure_ascii=False)}]}


def _do_idea(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    summary = args.get("summary")
    interview = args.get("interview")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("summary (non-empty string) is required")
    if not isinstance(interview, dict):
        raise ValueError("interview (object) is required; pass {} for empty intake")
    proj = record_idea(path, summary.strip(), interview)
    return {"content": [{"type": "text", "text": json.dumps(proj, ensure_ascii=False)}]}


def _do_intake_check(_root: Path, args: dict, _limits: dict) -> dict:
    interview = args.get("interview")
    if not isinstance(interview, dict):
        raise ValueError("interview (object) is required")
    report = analyze_intake(interview)
    return {"content": [{"type": "text", "text": json.dumps(report, ensure_ascii=False)}]}


def _do_concept_review(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    proj = review_concept(path, _as_str(args, "verdict"), _as_str(args, "artifact"), _as_str(args, "reviewer"))
    return {"content": [{"type": "text", "text": json.dumps(proj, ensure_ascii=False)}]}


def _do_concept_repair(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    summary = args.get("summary") if isinstance(args.get("summary"), str) else None
    raw_interview = args.get("interview")
    interview = raw_interview if isinstance(raw_interview, dict) else None
    proj = repair_concept(
        path,
        summary,
        interview,
        _as_str(args, "verdict"),
        _as_str(args, "artifact"),
        _as_str(args, "reviewer"),
    )
    return {"content": [{"type": "text", "text": json.dumps(proj, ensure_ascii=False)}]}


def _do_bible(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    proj = write_bible(path, _as_str(args, "artifact"))
    return {"content": [{"type": "text", "text": json.dumps(proj, ensure_ascii=False)}]}


def _do_outline_write(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    level = _as_str(args, "level")
    if level not in OUTLINE_LEVELS:
        raise ValueError(f"level must be one of {list(OUTLINE_LEVELS)}")
    proj = write_outline(path, level, _as_str(args, "artifact"))
    return {"content": [{"type": "text", "text": json.dumps(proj, ensure_ascii=False)}]}


def _do_outline_review(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    level = _as_str(args, "level")
    if level not in OUTLINE_LEVELS:
        raise ValueError(f"level must be one of {list(OUTLINE_LEVELS)}")
    proj = review_outline(path, level, _as_str(args, "verdict"), _as_str(args, "artifact"), _as_str(args, "reviewer"))
    return {"content": [{"type": "text", "text": json.dumps(proj, ensure_ascii=False)}]}


def _do_outline_repair(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    level = _as_str(args, "level")
    if level not in OUTLINE_LEVELS:
        raise ValueError(f"level must be one of {list(OUTLINE_LEVELS)}")
    proj = repair_outline(
        path,
        level,
        _as_str(args, "artifact"),
        _as_str(args, "verdict"),
        _as_str(args, "review_artifact"),
        _as_str(args, "reviewer"),
    )
    return {"content": [{"type": "text", "text": json.dumps(proj, ensure_ascii=False)}]}


def _do_outline_lock(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    proj = lock_outline(path)
    return {"content": [{"type": "text", "text": json.dumps(proj, ensure_ascii=False)}]}


def _do_issue(root: Path, args: dict, limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    chapter = _as_int(args, "chapter")
    title = _as_str(args, "title")
    goal = _as_str(args, "goal")
    proj_for_count = load_json(path / "workflow.json") if (path / "workflow.json").exists() else {"chapters": {}}
    if len(proj_for_count.get("chapters", {})) >= limits["max_chapters"]:
        raise ValueError(f"max_chapters ({limits['max_chapters']}) reached; issue refused")
    state = issue_chapter(path, chapter, title, goal)
    return {"content": [{"type": "text", "text": json.dumps(state, ensure_ascii=False)}]}


def _do_draft(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    chapter = _as_int(args, "chapter")
    state = record_draft(
        path,
        chapter,
        _as_str(args, "artifact"),
        _as_str(args, "prewrite"),
        _as_str(args, "author"),
    )
    return {"content": [{"type": "text", "text": json.dumps(state, ensure_ascii=False)}]}


def _do_review(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    chapter = _as_int(args, "chapter")
    gate = _as_str(args, "gate")
    reason = args.get("reason")
    if not isinstance(reason, str):
        reason = ""
    state = review_chapter(
        path,
        chapter,
        gate,
        _as_str(args, "verdict"),
        _as_str(args, "artifact"),
        _as_str(args, "reviewer"),
        reason,
    )
    return {"content": [{"type": "text", "text": json.dumps(state, ensure_ascii=False)}]}


def _do_repair(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    chapter = _as_int(args, "chapter")
    affected = args.get("affected")
    if not isinstance(affected, list) or not affected:
        raise ValueError("affected (non-empty array of gate names) is required")
    state = repair_chapter(path, chapter, _as_str(args, "artifact"), affected)
    return {"content": [{"type": "text", "text": json.dumps(state, ensure_ascii=False)}]}


def _do_release(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    chapter = _as_int(args, "chapter")
    state = release_chapter(path, chapter)
    return {"content": [{"type": "text", "text": json.dumps(state, ensure_ascii=False)}]}


# --- read-only tools ----------------------------------------------------
def _do_status(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    proj = load_json(path / "workflow.json")
    result: dict = {"project": proj, "project_errors": validate_project(proj)}
    chapter = args.get("chapter")
    if chapter is not None:
        if not isinstance(chapter, int):
            raise ValueError("chapter (integer) is required when provided")
        sp = path / ".novel-workflow" / f"chapter-{chapter}.json"
        if sp.exists():
            st = load_json(sp)
            result["chapter"] = st
            result["chapter_errors"] = validate_chapter(st)
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}


def _do_check(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    states: dict[str, list[str]] = {}
    nw = path / ".novel-workflow"
    if nw.exists():
        for cp in nw.glob("chapter-*.json"):
            states[cp.name] = validate_chapter(load_json(cp))
    proj = load_json(path / "workflow.json")
    proj_errors = validate_project(proj)
    findings = security_scan(path) if args.get("security") else []
    result = {"project_errors": proj_errors, "chapter_errors": states, "security_findings": findings}
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}


def _do_roles(_root: Path, _args: dict, _limits: dict) -> dict:
    result = {"roles": list(SIX_ROLES), "charter": dict(ROLE_CHARTER)}
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}


def _do_chapters(root: Path, args: dict, _limits: dict) -> dict:
    path = _as_path(root, args.get("path"), "path")
    result = {"chapters": list_chapters(path)}
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}


# --- tool dispatch ------------------------------------------------------
def _as_path(root: Path, value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} (non-empty string) is required")
    # The path is always resolved against the server's project root, so
    # the client cannot reach the host filesystem. A literal "."
    # collapses to the project root.
    if value in (".", ""):
        return root
    target = (root / value).resolve()
    root_resolved = root.resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise ValueError(f"{field} must stay inside project root")
    return target


def _as_str(args: dict, field: str) -> str:
    value = args.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} (non-empty string) is required")
    return value


def _as_int(args: dict, field: str) -> int:
    value = args.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} (integer) is required")
    return value


# Tool registry: name -> (handler, json_schema). Adding a tool means
# adding one entry here, one schema in TOOLS, and (if needed) one line
# in the CLI. The handler receives (root, args, limits).
TOOL_HANDLERS: dict[str, Callable[[Path, dict, dict], dict]] = {
    "init": _do_init,
    "idea": _do_idea,
    "intake_check": _do_intake_check,
    "concept_review": _do_concept_review,
    "concept_repair": _do_concept_repair,
    "bible": _do_bible,
    "outline_write": _do_outline_write,
    "outline_review": _do_outline_review,
    "outline_repair": _do_outline_repair,
    "outline_lock": _do_outline_lock,
    "issue": _do_issue,
    "draft": _do_draft,
    "review": _do_review,
    "repair": _do_repair,
    "release": _do_release,
    "status": _do_status,
    "check": _do_check,
    "roles": _do_roles,
    "chapters": _do_chapters,
    "write_artifact": _do_write_artifact,
    "read_artifact": _do_read_artifact,
}


# --- tool schemas (inputSchema for tools/list) ---------------------------
_COMMON_PATH = {
    "type": "string",
    "description": (
        "Project path, relative to the MCP server's --root. '.' refers to the "
        "root itself. Resolved and jailed against the server root."
    ),
}

# A reusable bag: gate choice covers the union of review gates (author/
# editor/reader) and domain gates (military/science). The engine's
# review handler validates prefix conventions; the schema just tells
# the agent which names exist.
_GATE_CHOICE = list(REVIEW_GATES) + list(DOMAIN_GATES)

TOOLS: list[dict] = [
    {
        "name": "init",
        "description": (
            "Create a new novel project at <path>. Writes workflow.json with "
            "stage=IDEA, creates the standard sub-directories (story-bible, "
            "outlines, chapters, reviews, releases, idea, assets), and seeds "
            "the default limits block. Must be the first call for a new "
            "project. Refuses to overwrite an existing workflow.json."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "title": {"type": "string", "description": "Project title."},
            },
            "required": ["path", "title"],
            "additionalProperties": False,
        },
    },
    {
        "name": "idea",
        "description": (
            "Record the project idea. <summary> is a one-sentence logline; "
            "<interview> is the structured intake object (15 fields: audience, "
            "genre, target_words, premise, world, protagonist, supporting_cast, "
            "central_conflict, stakes, character_arc, style, structure, ending, "
            "boundaries, craft_patterns). Use 'intake_check' first to see which "
            "fields are still missing before 'concept_review'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "summary": {"type": "string"},
                "interview": {
                    "type": "object",
                    "description": "Structured intake object; pass {} if not yet filled.",
                    "additionalProperties": True,
                },
            },
            "required": ["path", "summary", "interview"],
            "additionalProperties": False,
        },
    },
    {
        "name": "intake_check",
        "description": (
            "Deterministic, model-free completeness report for a structured "
            "intake object. Returns status (COMPLETE/INCOMPLETE), the list of "
            "missing fields, the next question, and the copyright boundary "
            "reminder. Run this before 'concept_review'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "interview": {"type": "object", "additionalProperties": True},
            },
            "required": ["interview"],
            "additionalProperties": False,
        },
    },
    {
        "name": "concept_review",
        "description": (
            "Review the recorded idea. verdict must be PASS or FAIL. The "
            "engine hard-requires COMPLETE intake before this can PASS; an "
            "INCOMPLETE intake is refused with the missing field list."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
                "artifact": {"type": "string", "description": "Path (relative to project root) of the review artifact."},
                "reviewer": {"type": "string", "description": "Provenance string, e.g. 'editor:mal'."},
            },
            "required": ["path", "verdict", "artifact", "reviewer"],
            "additionalProperties": False,
        },
    },
    {
        "name": "concept_repair",
        "description": (
            "Repair a FAILED concept. Pass new summary / interview only if you "
            "want to update the idea in the same call; otherwise the existing "
            "idea is kept and only the verdict changes."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "summary": {"type": "string"},
                "interview": {"type": "object", "additionalProperties": True},
                "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
                "artifact": {"type": "string"},
                "reviewer": {"type": "string"},
            },
            "required": ["path", "verdict", "artifact", "reviewer"],
            "additionalProperties": False,
        },
    },
    {
        "name": "bible",
        "description": (
            "Record the story bible artifact. Requires concept.status == PASS. "
            "Advances stage to STORY_BIBLE."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "artifact": {"type": "string"},
            },
            "required": ["path", "artifact"],
            "additionalProperties": False,
        },
    },
    {
        "name": "outline_write",
        "description": (
            "Write an outline artifact at the given level (master / volume / "
            "chapter). Each level requires the previous level to be PASS."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "level": {"type": "string", "enum": list(OUTLINE_LEVELS)},
                "artifact": {"type": "string"},
            },
            "required": ["path", "level", "artifact"],
            "additionalProperties": False,
        },
    },
    {
        "name": "outline_review",
        "description": (
            "Review an outline at the given level. verdict must be PASS or FAIL. "
            "On PASS the engine allows progression; on FAIL the outline must be "
            "repaired via 'outline_repair' before lock."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "level": {"type": "string", "enum": list(OUTLINE_LEVELS)},
                "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
                "artifact": {"type": "string"},
                "reviewer": {"type": "string"},
            },
            "required": ["path", "level", "verdict", "artifact", "reviewer"],
            "additionalProperties": False,
        },
    },
    {
        "name": "outline_repair",
        "description": (
            "Repair a FAILED outline at the given level by writing a new "
            "artifact and re-reviewing. Only valid after a FAIL review."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "level": {"type": "string", "enum": list(OUTLINE_LEVELS)},
                "artifact": {"type": "string", "description": "New outline artifact."},
                "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
                "review_artifact": {"type": "string", "description": "Path to the review artifact for the new outline."},
                "reviewer": {"type": "string"},
            },
            "required": ["path", "level", "artifact", "verdict", "review_artifact", "reviewer"],
            "additionalProperties": False,
        },
    },
    {
        "name": "outline_lock",
        "description": (
            "Lock the outline. Requires all three levels (master, volume, "
            "chapter) to be PASS. This is the most important gate: chapters "
            "cannot be issued before this succeeds."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"path": _COMMON_PATH},
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "issue",
        "description": (
            "Issue a new chapter. Requires the project to be in OUTLINE_LOCKED. "
            "The chapter number must not already exist. Refused when the "
            "configured max_chapters limit would be exceeded."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "chapter": {"type": "integer", "minimum": 1},
                "title": {"type": "string"},
                "goal": {"type": "string", "description": "The chapter's narrative goal."},
            },
            "required": ["path", "chapter", "title", "goal"],
            "additionalProperties": False,
        },
    },
    {
        "name": "draft",
        "description": (
            "Record a candidate draft for <chapter>. <author> must be prefixed "
            "'author:' (e.g. 'author:noa'). <artifact> is the draft text path; "
            "<prewrite> is the Author Role OS prewrite card path. The prewrite "
            "card is validated for six required sections (Chapter function, "
            "Three-event chain, Central choice, Voice anchors, Forbidden drift, "
            "Human-writing constraints) and the draft title is checked against "
            "the locked chapter outline (SOURCE_MISMATCH guard)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "chapter": {"type": "integer", "minimum": 1},
                "artifact": {"type": "string", "description": "Path to the draft text."},
                "prewrite": {"type": "string", "description": "Path to the Author Role OS prewrite card."},
                "author": {"type": "string", "description": "'author:<identifier>' provenance."},
            },
            "required": ["path", "chapter", "artifact", "prewrite", "author"],
            "additionalProperties": False,
        },
    },
    {
        "name": "review",
        "description": (
            "Sign a chapter gate. <gate> is one of author / editor / reader / "
            "military / science. Reviewer provenance must match the gate (e.g. "
            "'editor:mal' for gate=editor, 'military:bea' or "
            "'military_consultant:bea' for gate=military). Verdict for review "
            "gates is PASS or FAIL; for domain gates it is PASS, FAIL, or "
            "SKIP_WITH_REASON (a reason is required for SKIP). A PASS review "
            "must include 'reviewed_fulltext: true' and a 'candidate_sha256' "
            "matching the current draft; editor/reader additionally need "
            "'CROSS_CHAPTER_CONSISTENCY: PASS'; science needs "
            "'NUMERICAL_CONSISTENCY: PASS'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "chapter": {"type": "integer", "minimum": 1},
                "gate": {"type": "string", "enum": _GATE_CHOICE},
                "verdict": {"type": "string", "enum": ["PASS", "FAIL", "SKIP_WITH_REASON"]},
                "artifact": {"type": "string"},
                "reviewer": {"type": "string", "description": "Provenance: 'role:identifier'."},
                "reason": {"type": "string", "description": "Required only for SKIP_WITH_REASON on domain gates."},
            },
            "required": ["path", "chapter", "gate", "verdict", "artifact", "reviewer"],
            "additionalProperties": False,
        },
    },
    {
        "name": "repair",
        "description": (
            "Replace a chapter's draft and reset the named affected gates to "
            "PENDING. The matching reviewer provenance and old release receipt "
            "are removed. Use this when a FAIL review makes the current draft "
            "unpublishable; do not use it to silently overwrite a passing draft."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "chapter": {"type": "integer", "minimum": 1},
                "artifact": {"type": "string", "description": "New draft text path."},
                "affected": {
                    "type": "array",
                    "items": {"type": "string", "enum": _GATE_CHOICE},
                    "minItems": 1,
                },
            },
            "required": ["path", "chapter", "artifact", "affected"],
            "additionalProperties": False,
        },
    },
    {
        "name": "release",
        "description": (
            "Explicitly release a chapter. Only valid when every chapter gate "
            "is satisfied (PASS, or SKIP_WITH_REASON for military/science with "
            "reason set). 'RELEASED' is never written by any other path; this "
            "is the only call that flips status to RELEASED and writes the "
            "release receipt."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "chapter": {"type": "integer", "minimum": 1},
            },
            "required": ["path", "chapter"],
            "additionalProperties": False,
        },
    },
    {
        "name": "status",
        "description": (
            "Read-only project + chapter status. Pass chapter to include the "
            "per-chapter state document and its validation errors."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "chapter": {"type": "integer", "minimum": 1},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "check",
        "description": (
            "Validation summary. Returns project_errors, chapter_errors (per "
            "chapter state file), and security_findings (only when security "
            "is true). Does not modify state."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": _COMMON_PATH,
                "security": {"type": "boolean", "default": False},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "roles",
        "description": (
            "List the six workflow roles with their charter text. No arguments."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "chapters",
        "description": (
            "Whole-book chapter ledger. Merges workflow.json.chapters with the "
            "on-disk per-chapter state files. No chapter argument."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"path": _COMMON_PATH},
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "write_artifact",
        "description": (
            "Write a text artifact inside the project root. Refuses to write to "
            "workflow.json or to .novel-workflow/** (state files must be "
            "mutated through the state-machine tools). Refuses paths that "
            "escape the project root. Enforces limits.max_artifact_bytes."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relative to the project root."},
                "content": {"type": "string", "description": "UTF-8 text content."},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "read_artifact",
        "description": (
            "Read a text artifact inside the project root. Refuses to read "
            "workflow.json or .novel-workflow/** (use resources/read for those). "
            "Refuses paths that escape the project root. Enforces "
            "limits.max_read_bytes."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relative to the project root."},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
]


# --- resources ----------------------------------------------------------
RESOURCES: list[dict] = [
    {
        "uri": "novel://state",
        "name": "Project state",
        "description": (
            "The full project document at <root>/workflow.json, plus the "
            "current project_errors from validate_project."
        ),
        "mimeType": "application/json",
    },
    {
        "uri": "novel://events",
        "name": "Event log",
        "description": (
            "The append-only event log at <root>/.novel-workflow/events.jsonl. "
            "Tails the file to limits.max_events_jsonl_bytes when the live file "
            "is larger."
        ),
        "mimeType": "application/jsonl",
    },
    {
        "uri": "novel://chapter/{chapter}",
        "name": "Chapter state",
        "description": (
            "Per-chapter state at <root>/.novel-workflow/chapter-{n}.json. "
            "Returns 404-shaped protocol error when the chapter does not exist."
        ),
        "mimeType": "application/json",
    },
]


def _read_resource(root: Path, uri: str, limits: dict) -> dict:
    """Resolve a ``novel://`` URI and return its content as an MCP ``contents`` item."""
    if not isinstance(uri, str) or not uri:
        raise ValueError("uri (string) is required")
    if uri == "novel://state":
        wf = root / "workflow.json"
        if not wf.exists():
            raise FileNotFoundError("workflow.json not found; run init first")
        proj = load_json(wf)
        payload = {"project": proj, "project_errors": validate_project(proj)}
        return {
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps(payload, ensure_ascii=False, indent=2),
        }
    if uri == "novel://events":
        ev = root / ".novel-workflow" / "events.jsonl"
        if not ev.exists():
            return {"uri": uri, "mimeType": "application/jsonl", "text": ""}
        raw = ev.read_bytes()
        cap = limits["max_events_jsonl_bytes"]
        if len(raw) > cap:
            # Keep the most recent ``cap`` bytes; the engine's append-only log
            # is line-oriented, so walk backwards until the next newline.
            tail = raw[-cap:]
            nl = tail.find(b"\n")
            if nl >= 0 and nl + 1 < len(tail):
                tail = tail[nl + 1 :]
            raw = tail
        return {"uri": uri, "mimeType": "application/jsonl", "text": raw.decode("utf-8", errors="replace")}
    if uri.startswith("novel://chapter/"):
        suffix = uri[len("novel://chapter/") :]
        if not suffix.isdigit():
            raise ValueError("chapter segment must be a positive integer")
        n = int(suffix)
        sp = root / ".novel-workflow" / f"chapter-{n}.json"
        if not sp.exists():
            raise FileNotFoundError(f"chapter {n} not issued yet")
        state = load_json(sp)
        payload = {"chapter": state, "chapter_errors": validate_chapter(state)}
        return {
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps(payload, ensure_ascii=False, indent=2),
        }
    raise ValueError(f"unknown resource URI: {uri}")


# --- prompts ------------------------------------------------------------
PROMPTS: list[dict] = [
    {"name": "controller", "description": "Controller role: route stages, verify evidence, block false completion."},
    {"name": "author", "description": "Author role: produce candidate drafts with Author Role OS prewrite."},
    {"name": "editor", "description": "Editor role: independent structural, prose, DEAI, and audience-respect review."},
    {"name": "reader", "description": "Reader role: independent reading-experience review."},
    {"name": "military_consultant", "description": "Military consultant: domain review for tactics and force structure."},
    {"name": "science_consultant", "description": "Science consultant: domain review for physical, biological, technical plausibility."},
]


def _get_prompt(name: str, args: dict | None) -> dict:
    if name not in SIX_ROLES:
        raise ValueError(f"unknown prompt: {name}")
    charter = ROLE_CHARTER[name]
    # Per-role evidence contracts. The author prompt references the prewrite
    # card keywords the engine validates; the editor / reader / science
    # prompts restate the exact evidence strings the engine grep-checks.
    role_specific: dict[str, str] = {
        "controller": (
            "Your job is decomposition, routing, and verification. You never "
            "author or review prose. Before any state transition, confirm the "
            "preconditions listed in core.py for that transition (e.g. "
            "concept.status == PASS before 'bible'; outline_locked before "
            "'issue'; every chapter gate satisfied before 'release'). Reject "
            "any proposal that would write to workflow.json or to "
            ".novel-workflow/** directly; route through the state-machine tools."
        ),
        "author": (
            "Before recording a draft, write an Author Role OS prewrite card "
            "and persist it with 'write_artifact'. The prewrite card MUST "
            "contain these six section headings (the engine grep-checks them, "
            "case-insensitive):\n"
            "  Chapter function\n"
            "  Three-event chain\n"
            "  Central choice\n"
            "  Voice anchors\n"
            "  Forbidden drift\n"
            "  Human-writing constraints\n"
            "Then 'draft' the candidate. Provenance is 'author:<identifier>' "
            "(e.g. 'author:noa'). Do not write the draft title in a way that "
            "disagrees with the locked chapter outline title -- the engine "
            "raises SOURCE_MISMATCH if they differ."
        ),
        "editor": (
            "An editor review is independent: your identifier must not equal "
            "the author's. The review artifact must contain (the engine "
            "validates these strings, case-insensitive):\n"
            "  DEAI\n"
            "  Audience respect\n"
            "  CROSS_CHAPTER_CONSISTENCY: PASS\n"
            "  reviewed_fulltext: true\n"
            "  candidate_sha256: <64-hex sha256 of the current draft>\n"
            "The candidate_sha256 must match the sha256 of the draft the "
            "engine currently has on file; the engine raises a 'review cites "
            "<prefix>... but current draft is <prefix>...' error otherwise."
        ),
        "reader": (
            "A reader review is independent: your identifier must differ from "
            "the author's AND from the editor's. The review artifact must "
            "contain:\n"
            "  Real reading experience\n"
            "  Immersion\n"
            "  Over-explanation\n"
            "  CROSS_CHAPTER_CONSISTENCY: PASS\n"
            "  reviewed_fulltext: true\n"
            "  candidate_sha256: <64-hex sha256 of the current draft>"
        ),
        "military_consultant": (
            "A military review is opt-out: if the chapter has no applicable "
            "content, sign SKIP_WITH_REASON with a real reason. Verdict is "
            "PASS, FAIL, or SKIP_WITH_REASON. On PASS the artifact must "
            "include 'reviewed_fulltext: true' and a candidate_sha256 matching "
            "the current draft. Provenance prefix can be 'military:' or "
            "'military_consultant:'."
        ),
        "science_consultant": (
            "A science review is opt-out: if the chapter has no applicable "
            "content, sign SKIP_WITH_REASON with a real reason. On PASS the "
            "artifact must additionally include 'NUMERICAL_CONSISTENCY: PASS' "
            "plus the standard 'reviewed_fulltext: true' and candidate_sha256. "
            "Provenance prefix can be 'science:' or 'science_consultant:'."
        ),
    }
    text = (
        f"Role: {name}\n\nCharter: {charter}\n\n"
        f"Evidence contract:\n{role_specific[name]}"
    )
    return {
        "description": f"{name} role prompt with evidence contract",
        "messages": [
            {
                "role": "user",
                "content": {"type": "text", "text": text},
            }
        ],
    }


# --- initialize / method routing ---------------------------------------
def _respond_initialize(params: dict, request_id: Any) -> dict:
    requested = params.get("protocolVersion") if isinstance(params, dict) else None
    version = requested if isinstance(requested, str) and requested in PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": version,
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False},
            },
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "instructions": INSTRUCTIONS,
        },
    }


def _call_tool(name: Any, arguments: Any, root: Path, limits: dict) -> dict:
    if not isinstance(name, str) or not name:
        raise ValueError("tools/call: name (non-empty string) is required")
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"unknown tool: {name}")
    if not isinstance(arguments, dict):
        raise ValueError("tools/call: arguments (object) is required")
    return handler(root, arguments, limits)


def _handle_request(msg: dict, state: dict) -> dict | None:
    method = msg.get("method")
    params = msg.get("params")
    request_id = msg.get("id")
    if not isinstance(params, dict):
        params = {}
    if method == "initialize":
        return _respond_initialize(params, request_id)
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        try:
            limits = load_limits(state["root"])
            result = _call_tool(params.get("name"), params.get("arguments"), state["root"], limits)
        except (ValueError, OSError, KeyError) as exc:
            result = _tool_error(str(exc))
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    if method == "resources/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"resources": RESOURCES}}
    if method == "resources/read":
        try:
            limits = load_limits(state["root"])
            content = _read_resource(state["root"], params.get("uri"), limits)
        except FileNotFoundError as exc:
            return _protocol_error(-32602, str(exc), request_id)
        except ValueError as exc:
            return _protocol_error(-32602, str(exc), request_id)
        return {"jsonrpc": "2.0", "id": request_id, "result": {"contents": [content]}}
    if method == "prompts/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"prompts": PROMPTS}}
    if method == "prompts/get":
        try:
            prompt = _get_prompt(params.get("name"), params.get("arguments"))
        except ValueError as exc:
            return _protocol_error(-32602, str(exc), request_id)
        return {"jsonrpc": "2.0", "id": request_id, "result": prompt}
    return _protocol_error(-32601, f"method not found: {method}", request_id)


def serve(root: Path) -> int:
    """Run the MCP server loop on stdin/stdout until EOF.

    Returns 0 on clean shutdown. ``root`` is the project root the server
    is bound to; it is the base for every ``path`` argument in the
    tools, the base for every ``novel://`` resource, and the source of
    truth for ``load_limits``.
    """
    state = {"root": root.resolve()}
    while True:
        try:
            msg = _read_message()
        except EOFError:
            return 0
        except ValueError as exc:
            # Malformed JSON: respond with parse error and keep going.
            # We don't know the request id (the frame wasn't even valid
            # JSON), so use null per the JSON-RPC 2.0 spec.
            _write_message(_protocol_error(-32700, f"parse error: {exc}", None))
            continue
        if msg is None:
            continue
        if not isinstance(msg, dict):
            _write_message(_protocol_error(-32600, "invalid request (not an object)", None))
            continue
        if "id" not in msg:
            # Notification; the spec says do not reply.
            continue
        try:
            response = _handle_request(msg, state)
        except Exception as exc:  # pragma: no cover - defensive
            _log(f"unhandled exception in {msg.get('method')!r}: {exc!r}")
            response = _protocol_error(-32603, f"internal error: {exc}", msg.get("id"))
        if response is not None:
            _write_message(response)


def cmd_serve(ns: Any) -> int:
    """CLI handler for ``novel-workflow mcp --root PATH``."""
    root = Path(ns.root).resolve()
    if not root.exists():
        # Allow the server to start in an empty directory; the first
        # tool call from the agent will be 'init', which creates the
        # standard sub-directories.
        root.mkdir(parents=True, exist_ok=True)
    return serve(root)


def register(subparsers: Any) -> None:
    """Register the ``mcp`` subcommand on an existing subparsers action.

    Mirrors the ``model_cli.register`` pattern: keep the protocol code
    out of the top-level CLI module so the existing CLI surface stays
    one entry point.
    """
    p = subparsers.add_parser(
        "mcp",
        help="start a stdio MCP server bound to --root (for Claude Code, Codex, ...)",
    )
    p.add_argument(
        "--root",
        default=".",
        help="project root directory (default: current directory)",
    )
    p.set_defaults(_mcp_handler=cmd_serve)


__all__ = [
    "PROTOCOL_VERSIONS",
    "DEFAULT_PROTOCOL_VERSION",
    "SERVER_NAME",
    "SERVER_VERSION",
    "INSTRUCTIONS",
    "TOOLS",
    "RESOURCES",
    "PROMPTS",
    "serve",
    "cmd_serve",
    "register",
]
