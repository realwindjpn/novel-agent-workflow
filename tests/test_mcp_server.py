"""Tests for the stdio MCP server.

Strategy: drive the server by feeding newline-delimited JSON-RPC
frames into ``serve()`` via a pair of in-memory streams, then read
back the response frames. No subprocess, no socket. The test cases
cover protocol-version negotiation, the dual-channel error model,
state-machine tool plumbing, file-tool jail + limits, resources,
prompts, notification silence, EOF clean shutdown, and a full
end-to-end book run.
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from unittest import mock

from novel_workflow import core, mcp_server


@contextmanager
def _drive(root: Path) -> Iterator[list[dict]]:
    """Context manager: replace stdin/stdout with StringIOs, run serve().

    Yields a list that is filled with the response frames the server
    wrote, one JSON object per line. EOF is signalled by closing the
    fake stdin (readline returns ''), which is exactly what an
    exiting parent process would do.
    """
    frames: list[dict] = []
    fake_in = io.StringIO()
    fake_out = io.StringIO()
    real_stdin = sys.stdin
    real_stdout = sys.stdout

    def _capture_write():
        for line in fake_out.getvalue().splitlines():
            line = line.strip()
            if not line:
                continue
            frames.append(json.loads(line))

    with mock.patch.object(sys, "stdin", fake_in), mock.patch.object(sys, "stdout", fake_out):
        try:
            mcp_server.serve(root)
        finally:
            _capture_write()
    sys.stdin = real_stdin
    sys.stdout = real_stdout
    yield frames


def _send(root: Path, frames_in: list[dict]) -> list[dict]:
    """Feed ``frames_in`` to a fresh server run, return response frames."""
    payload = "\n".join(json.dumps(f, ensure_ascii=False) for f in frames_in) + "\n"
    fake_in = io.StringIO(payload)
    fake_out = io.StringIO()
    real_stdin, real_stdout = sys.stdin, sys.stdout
    captured: list[dict] = []
    with mock.patch.object(sys, "stdin", fake_in), mock.patch.object(sys, "stdout", fake_out):
        mcp_server.serve(root)
    sys.stdin, sys.stdout = real_stdin, real_stdout
    for line in fake_out.getvalue().splitlines():
        line = line.strip()
        if not line:
            continue
        captured.append(json.loads(line))
    return captured


def _tool_text(result: dict) -> str:
    """Return the first text content of a tool result."""
    content = result.get("content") or []
    if not content:
        return ""
    return content[0].get("text", "")


# --- shared fixtures ----------------------------------------------------
class _MCPTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _send(self, frames: list[dict]) -> list[dict]:
        return _send(self.root, frames)


# --- protocol ----------------------------------------------------------
class ProtocolTests(_MCPTestCase):
    def test_initialize_known_version_echoed(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}])
        self.assertEqual(out[0]["id"], 1)
        result = out[0]["result"]
        self.assertEqual(result["protocolVersion"], "2025-06-18")
        self.assertEqual(result["serverInfo"]["name"], "novel-workflow")
        self.assertIn("tools", result["capabilities"])
        self.assertIn("resources", result["capabilities"])
        self.assertIn("prompts", result["capabilities"])
        self.assertIn("six-role", result["instructions"])

    def test_initialize_unknown_version_falls_back(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2099-01-01"}}])
        self.assertEqual(out[0]["result"]["protocolVersion"], "2024-11-05")

    def test_ping(self):
        out = self._send([{"jsonrpc": "2.0", "id": 2, "method": "ping"}])
        self.assertEqual(out[0]["id"], 2)
        self.assertEqual(out[0]["result"], {})

    def test_notification_silenced(self):
        # A notification has no id; the server must not reply.
        out = self._send([{"jsonrpc": "2.0", "method": "notifications/initialized"}])
        self.assertEqual(out, [])

    def test_unknown_method_protocol_error(self):
        out = self._send([{"jsonrpc": "2.0", "id": 3, "method": "tools/unicorn"}])
        self.assertEqual(out[0]["error"]["code"], -32601)

    def test_malformed_json_yields_parse_error(self):
        out = self._send([])
        # Hand-craft a raw frame because _send json-encodes for us.
        payload = "{not-json\n"
        fake_in = io.StringIO(payload)
        fake_out = io.StringIO()
        with mock.patch.object(sys, "stdin", fake_in), mock.patch.object(sys, "stdout", fake_out):
            mcp_server.serve(self.root)
        line = fake_out.getvalue().strip()
        msg = json.loads(line)
        self.assertEqual(msg["error"]["code"], -32700)

    def test_eof_returns_zero(self):
        # Empty stdin -> serve returns 0 (clean shutdown).
        fake_in = io.StringIO("")
        fake_out = io.StringIO()
        with mock.patch.object(sys, "stdin", fake_in), mock.patch.object(sys, "stdout", fake_out):
            rc = mcp_server.serve(self.root)
        self.assertEqual(rc, 0)


# --- tools/list --------------------------------------------------------
class ToolsListTests(_MCPTestCase):
    def test_tools_list_has_21(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}])
        tools = out[0]["result"]["tools"]
        self.assertEqual(len(tools), 21)
        names = {t["name"] for t in tools}
        # Production chain (15)
        for n in (
            "init", "idea", "concept_review", "concept_repair", "bible",
            "outline_write", "outline_review", "outline_repair", "outline_lock",
            "issue", "draft", "review", "repair", "release",
        ):
            self.assertIn(n, names, f"missing state tool: {n}")
        # Read-only (5)
        for n in ("intake_check", "status", "check", "roles", "chapters"):
            self.assertIn(n, names, f"missing read tool: {n}")
        # File tools (2)
        for n in ("write_artifact", "read_artifact"):
            self.assertIn(n, names, f"missing file tool: {n}")

    def test_every_tool_has_input_schema(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}])
        for t in out[0]["result"]["tools"]:
            self.assertEqual(t["inputSchema"]["type"], "object", t["name"])
            self.assertIn("description", t, t["name"])


# --- init + status -----------------------------------------------------
class InitStatusTests(_MCPTestCase):
    def test_init_then_status(self):
        out = self._send([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "init", "arguments": {"path": ".", "title": "Demo"}}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "status", "arguments": {"path": "."}}},
        ])
        proj = json.loads(_tool_text(out[0]["result"]))
        self.assertEqual(proj["title"], "Demo")
        self.assertEqual(proj["stage"], "IDEA")
        self.assertIn("limits", proj)
        self.assertEqual(proj["limits"]["max_chapters"], 500)
        stat = json.loads(_tool_text(out[1]["result"]))
        self.assertEqual(stat["project"]["title"], "Demo")
        self.assertEqual(stat["project_errors"], [])

    def test_init_overwrites_existing_project(self):
        # init is a fresh-start command: re-initializing an existing project
        # resets title, stage, and idea. The previous workflow.json (which
        # doesn't even parse as a project) is overwritten. This documents
        # the design — there is no "refuse overwrite" guard.
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "workflow.json").write_text('{"schema_version": 99}', encoding="utf-8")
        out = self._send([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "init", "arguments": {"path": ".", "title": "NewTitle"}}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "status", "arguments": {"path": "."}}},
        ])
        self.assertNotEqual(out[0]["result"].get("isError"), True, msg=out[0]["result"])
        proj = json.loads(_tool_text(out[0]["result"]))
        self.assertEqual(proj["title"], "NewTitle")
        self.assertEqual(proj["stage"], "IDEA")
        stat = json.loads(_tool_text(out[1]["result"]))
        self.assertEqual(stat["project"]["title"], "NewTitle")
        # The schema_version from the prior file is gone.
        self.assertEqual(stat["project"]["schema_version"], core.SCHEMA_VERSION)

    def test_intake_check_pure_function(self):
        out = self._send([{
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "intake_check", "arguments": {"interview": {}}},
        }])
        report = json.loads(_tool_text(out[0]["result"]))
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertEqual(len(report["missing_fields"]), 15)


# --- write_artifact / read_artifact -----------------------------------
class FileToolTests(_MCPTestCase):
    def setUp(self) -> None:
        super().setUp()
        # init so workflow.json + standard subdirs exist
        self._send([{
            "jsonrpc": "2.0", "id": 0, "method": "tools/call",
            "params": {"name": "init", "arguments": {"path": ".", "title": "Demo"}},
        }])

    def test_write_then_read_artifact(self):
        out = self._send([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "write_artifact", "arguments": {"path": "chapters/notes.md", "content": "hello\n"}}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "read_artifact", "arguments": {"path": "chapters/notes.md"}}},
        ])
        self.assertFalse(out[0]["result"].get("isError"))
        body = json.loads(_tool_text(out[1]["result"]))
        self.assertEqual(body["text"], "hello\n")

    def test_write_artifact_jail_blocks_escape(self):
        out = self._send([{
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "write_artifact", "arguments": {"path": "../escape.md", "content": "no"}},
        }])
        self.assertTrue(out[0]["result"].get("isError"))
        self.assertIn("must stay inside project root", _tool_text(out[0]["result"]))

    def test_write_artifact_refuses_state_files(self):
        for forbidden in ("workflow.json", ".novel-workflow/foo.json", ".novel-workflow/events.jsonl"):
            with self.subTest(forbidden=forbidden):
                out = self._send([{
                    "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "write_artifact", "arguments": {"path": forbidden, "content": "x"}},
                }])
                self.assertTrue(out[0]["result"].get("isError"), forbidden)
                self.assertIn("not allowed via MCP", _tool_text(out[0]["result"]))

    def test_read_artifact_refuses_state_files(self):
        for forbidden in ("workflow.json", ".novel-workflow/chapter-1.json"):
            with self.subTest(forbidden=forbidden):
                out = self._send([{
                    "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "read_artifact", "arguments": {"path": forbidden}},
                }])
                self.assertTrue(out[0]["result"].get("isError"), forbidden)

    def test_write_artifact_enforces_max_artifact_bytes(self):
        # Override the project's limits to a tiny cap, then try to write 2 KiB.
        wf_path = self.root / "workflow.json"
        proj = json.loads(wf_path.read_text(encoding="utf-8"))
        proj["limits"]["max_artifact_bytes"] = 100
        wf_path.write_text(json.dumps(proj, ensure_ascii=False), encoding="utf-8")
        big = "a" * 2048
        out = self._send([{
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "write_artifact", "arguments": {"path": "chapters/big.md", "content": big}},
        }])
        self.assertTrue(out[0]["result"].get("isError"))
        self.assertIn("max_artifact_bytes", _tool_text(out[0]["result"]))


# --- dual-channel errors ----------------------------------------------
class DualChannelErrorTests(_MCPTestCase):
    def test_business_error_via_isError(self):
        # No init; trying to status should fail with isError, not a protocol error.
        out = self._send([{
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "status", "arguments": {"path": "."}},
        }])
        self.assertTrue(out[0]["result"].get("isError"))
        # No top-level JSON-RPC error envelope:
        self.assertNotIn("error", out[0])

    def test_protocol_error_unknown_tool(self):
        out = self._send([{
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "unicorn", "arguments": {}},
        }])
        # Unknown tool is still surfaced as a business error (isError),
        # not a -32601, because the tool name was syntactically valid;
        # only the dispatch layer raised. This matches the dual-channel
        # contract: protocol errors are for malformed frames / unknown
        # methods, business errors are for known tools that refused.
        self.assertTrue(out[0]["result"].get("isError"))
        self.assertIn("unknown tool", _tool_text(out[0]["result"]))

    def test_protocol_error_missing_method(self):
        out = self._send([{
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"arguments": {}},
        }])
        # Missing 'name' is an argument-shape problem, not a transport
        # problem: business error with isError true.
        self.assertTrue(out[0]["result"].get("isError"))


# --- resources ---------------------------------------------------------
class ResourcesTests(_MCPTestCase):
    def setUp(self) -> None:
        super().setUp()
        self._send([{
            "jsonrpc": "2.0", "id": 0, "method": "tools/call",
            "params": {"name": "init", "arguments": {"path": ".", "title": "Demo"}},
        }])

    def test_resources_list(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "resources/list"}])
        uris = [r["uri"] for r in out[0]["result"]["resources"]]
        self.assertIn("novel://state", uris)
        self.assertIn("novel://events", uris)
        self.assertIn("novel://chapter/{chapter}", uris)

    def test_read_state(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": "novel://state"}}])
        contents = out[0]["result"]["contents"]
        self.assertEqual(contents[0]["uri"], "novel://state")
        payload = json.loads(contents[0]["text"])
        self.assertEqual(payload["project"]["title"], "Demo")

    def test_read_events_has_init_event(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": "novel://events"}}])
        text = out[0]["result"]["contents"][0]["text"]
        self.assertIn("PROJECT_INITIALIZED", text)

    def test_read_chapter_missing(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": "novel://chapter/1"}}])
        self.assertEqual(out[0]["error"]["code"], -32602)

    def test_read_unknown_uri(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": "novel://banana"}}])
        self.assertEqual(out[0]["error"]["code"], -32602)


# --- prompts -----------------------------------------------------------
class PromptsTests(_MCPTestCase):
    def test_prompts_list_has_six(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "prompts/list"}])
        names = [p["name"] for p in out[0]["result"]["prompts"]]
        for role in ("controller", "author", "editor", "reader", "military_consultant", "science_consultant"):
            self.assertIn(role, names)

    def test_get_author_prompt(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "prompts/get", "params": {"name": "author"}}])
        result = out[0]["result"]
        text = result["messages"][0]["content"]["text"]
        self.assertIn("Author Role OS prewrite", text)
        self.assertIn("Chapter function", text)
        self.assertIn("Three-event chain", text)

    def test_get_editor_prompt_has_evidence_contract(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "prompts/get", "params": {"name": "editor"}}])
        text = out[0]["result"]["messages"][0]["content"]["text"]
        for needle in ("DEAI", "CROSS_CHAPTER_CONSISTENCY", "reviewed_fulltext", "candidate_sha256"):
            self.assertIn(needle, text)

    def test_get_unknown_prompt(self):
        out = self._send([{"jsonrpc": "2.0", "id": 1, "method": "prompts/get", "params": {"name": "unicorn"}}])
        self.assertEqual(out[0]["error"]["code"], -32602)


# --- end-to-end book run -----------------------------------------------
class EndToEndBookRun(_MCPTestCase):
    """Drive the full project lifecycle through MCP and verify state."""

    INTAKE = {
        "audience": "adult sci-fi readers seeking grounded tension",
        "genre": "science fiction mystery",
        "target_words": {"target": 90000, "range": "80000-100000"},
        "premise": "A relay repair lead must identify an impossible signal.",
        "world": "A remote orbital relay; light delay, scarce air, strict safety rules.",
        "protagonist": "A cautious repair lead fears reporting uncertain evidence.",
        "supporting_cast": "A cost-driven manager, a risk-seeking technician.",
        "central_conflict": "Each verification consumes safety margin and increases pressure.",
        "stakes": "Failure risks the crew, their livelihoods, and wider evidence.",
        "character_arc": "The lead moves from protective silence to accountable truth-telling.",
        "style": "close third person, past tense, restrained prose.",
        "structure": "anomaly, denial, costly verification, public choice and aftermath.",
        "ending": "the signal is verified, the crew survives at a cost.",
        "boundaries": "no copied franchise lore, no effortless technical solutions.",
        "craft_patterns": ["escalate clue certainty while shrinking physical safety margin."],
    }

    PREWRITE = (
        "# Chapter prewrite card\n\n"
        "## Chapter function\nShow the anomaly.\n\n"
        "## Three-event chain\n1. event one 2. event two 3. event three\n\n"
        "## Central choice\nThe lead chooses to log the anomaly.\n\n"
        "## Voice anchors\nrestrained, concrete sensory feedback, no monologues.\n\n"
        "## Forbidden drift\nexplanatory asides, jargon dumps.\n\n"
        "## Human-writing constraints\nno 'distinct', no 'vibrant'.\n"
    )

    DRAFT_TITLE = "First Signal"

    DRAFT_BODY = (
        "# First Signal\n\n"
        "The relay hummed a half-tone flat and Mara pretended not to notice. "
        "She logged the drift, signed her handle, and locked the screen before "
        "anyone could read the second digit. The reading did not need a second "
        "digit. The reading needed a quiet hour and a cup of something warm and "
        "the kind of patience the safety manual kept promising her. She did not "
        "have any of those things, so she did what the safety manual actually "
        "said, which was write the number down and walk away. She walked to the "
        "window. The window showed her own face and, behind it, the same orbit "
        "she had been watching for two hundred and twelve days. She did not "
        "pretend the number was a mistake. She also did not pretend it was a "
        "signal. She pretended, very carefully, that the next hour was hers.\n"
    )

    OUTLINE_MASTER = "# Master outline\n\nThe book is about a relay and a signal and a choice.\n"
    OUTLINE_VOLUME = "# Volume outline\n\nVolume one: the anomaly.\n"
    OUTLINE_CHAPTER = "# Chapter outline (working): First Signal\n\nThe lead notices and logs.\n"

    def _prewrite_artifact(self) -> str:
        return "chapters/prewrite-1.md"

    def _draft_artifact(self) -> str:
        return "chapters/draft-1.md"

    def _editor_review_artifact(self, draft_sha: str) -> str:
        return (
            "# Editor review\n\nDEAI: pass. Audience respect: pass.\n"
            "CROSS_CHAPTER_CONSISTENCY: PASS\n"
            "reviewed_fulltext: true\n"
            f"candidate_sha256: {draft_sha}\n"
        )

    def _reader_review_artifact(self, draft_sha: str) -> str:
        return (
            "# Reader review\n\nReal reading experience: pass.\n"
            "Immersion: pass. Over-explanation: none.\n"
            "CROSS_CHAPTER_CONSISTENCY: PASS\n"
            "reviewed_fulltext: true\n"
            f"candidate_sha256: {draft_sha}\n"
        )

    def _skip_review_artifact(self, gate: str, reason: str, draft_sha: str) -> str:
        return (
            f"# {gate} review\n\nreviewed_fulltext: true\n"
            f"candidate_sha256: {draft_sha}\n"
        )

    def _pass_review_artifact(self, gate: str, draft_sha: str) -> str:
        return (
            f"# {gate} review\n\nreviewed_fulltext: true\n"
            f"candidate_sha256: {draft_sha}\n"
            "NUMERICAL_CONSISTENCY: PASS\n"
        )

    def test_full_run_to_release(self):
        prewrite_path = self._prewrite_artifact()
        draft_path = self._draft_artifact()

        # 1. init
        self._send([{
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "init", "arguments": {"path": ".", "title": "The Silent Relay"}},
        }])

        # 2. idea
        self._send([{
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "idea", "arguments": {"path": ".", "summary": "A relay lead and an impossible signal.", "interview": self.INTAKE}},
        }])

        # 3. write concept-review artifact
        (self.root / "reviews").mkdir(exist_ok=True)
        concept_artifact = "reviews/concept.md"
        (self.root / concept_artifact).write_text("# Concept review\n\nConcept looks well-formed.\n", encoding="utf-8")

        # 4. concept-review PASS
        self._send([{
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "concept_review", "arguments": {"path": ".", "verdict": "PASS", "artifact": concept_artifact, "reviewer": "editor:mal"}},
        }])

        # 5. bible
        (self.root / "story-bible").mkdir(exist_ok=True)
        bible_artifact = "story-bible/world.md"
        (self.root / bible_artifact).write_text("# World\n\nRules: light delay, scarce air, strict safety.\n", encoding="utf-8")
        self._send([{
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "bible", "arguments": {"path": ".", "artifact": bible_artifact}},
        }])

        # 6. outline write x3 + review x3 PASS
        for level, body, idx in (
            ("master", self.OUTLINE_MASTER, 5),
            ("volume", self.OUTLINE_VOLUME, 6),
            ("chapter", self.OUTLINE_CHAPTER, 7),
        ):
            artifact = f"outlines/{level}.md"
            (self.root / artifact).write_text(body, encoding="utf-8")
            self._send([{
                "jsonrpc": "2.0", "id": idx, "method": "tools/call",
                "params": {"name": "outline_write", "arguments": {"path": ".", "level": level, "artifact": artifact}},
            }])
            review_artifact = f"reviews/outline-{level}.md"
            (self.root / review_artifact).write_text(f"# {level} review\n\nLooks good.\n", encoding="utf-8")
            self._send([{
                "jsonrpc": "2.0", "id": idx + 10, "method": "tools/call",
                "params": {"name": "outline_review", "arguments": {"path": ".", "level": level, "verdict": "PASS", "artifact": review_artifact, "reviewer": "editor:mal"}},
            }])

        # 7. outline lock
        self._send([{
            "jsonrpc": "2.0", "id": 8, "method": "tools/call",
            "params": {"name": "outline_lock", "arguments": {"path": "."}},
        }])

        # 8. issue chapter
        self._send([{
            "jsonrpc": "2.0", "id": 9, "method": "tools/call",
            "params": {"name": "issue", "arguments": {"path": ".", "chapter": 1, "title": "First Signal", "goal": "Establish the anomaly and the lead's choice to log it."}},
        }])

        # 9. write prewrite + draft via write_artifact (the bounded file tool)
        self._send([{
            "jsonrpc": "2.0", "id": 10, "method": "tools/call",
            "params": {"name": "write_artifact", "arguments": {"path": prewrite_path, "content": self.PREWRITE}},
        }])
        self._send([{
            "jsonrpc": "2.0", "id": 11, "method": "tools/call",
            "params": {"name": "write_artifact", "arguments": {"path": draft_path, "content": self.DRAFT_BODY}},
        }])

        # 10. record the draft
        self._send([{
            "jsonrpc": "2.0", "id": 12, "method": "tools/call",
            "params": {"name": "draft", "arguments": {"path": ".", "chapter": 1, "artifact": draft_path, "prewrite": prewrite_path, "author": "author:noa"}},
        }])

        # 11. five reviews
        draft_sha = core._sha256_full(self.DRAFT_BODY)
        reviews = [
            ("editor", "editor:mal", self._editor_review_artifact(draft_sha), "PASS", 13),
            ("reader", "reader:jun", self._reader_review_artifact(draft_sha), "PASS", 14),
            ("military", "military:bea", self._skip_review_artifact("military", "no applicable content", draft_sha), "SKIP_WITH_REASON", 15),
            ("science", "science:kim", self._skip_review_artifact("science", "no applicable content", draft_sha), "SKIP_WITH_REASON", 16),
            ("author", "author:noa", self._pass_review_artifact("author", draft_sha), "PASS", 17),
        ]
        for gate, reviewer, body, verdict, rid in reviews:
            artifact = f"reviews/{gate}.md"
            (self.root / artifact).write_text(body, encoding="utf-8")
            self._send([{
                "jsonrpc": "2.0", "id": rid, "method": "tools/call",
                "params": {
                    "name": "review",
                    "arguments": {
                        "path": ".", "chapter": 1, "gate": gate, "verdict": verdict,
                        "artifact": artifact, "reviewer": reviewer,
                        "reason": "no applicable content" if verdict == "SKIP_WITH_REASON" else "",
                    },
                },
            }])

        # 12. release
        out = self._send([{
            "jsonrpc": "2.0", "id": 18, "method": "tools/call",
            "params": {"name": "release", "arguments": {"path": ".", "chapter": 1}},
        }])
        state = json.loads(_tool_text(out[0]["result"]))
        self.assertEqual(state["status"], "RELEASED")
        self.assertTrue((self.root / "releases" / "chapter-1.json").exists())

        # 13. resources/read confirms the released state
        out = self._send([{
            "jsonrpc": "2.0", "id": 19, "method": "resources/read",
            "params": {"uri": "novel://chapter/1"},
        }])
        payload = json.loads(out[0]["result"]["contents"][0]["text"])
        self.assertEqual(payload["chapter"]["status"], "RELEASED")
        self.assertEqual(payload["chapter_errors"], [])

    def test_max_chapters_blocks_issue(self):
        # init + bible + outline + lock in a tight loop, then shrink
        # max_chapters to 1 in workflow.json, then try to issue two chapters.
        self._send([{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "init", "arguments": {"path": ".", "title": "Tiny"}}}])
        # record idea so concept-review is possible
        self._send([{
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "idea", "arguments": {"path": ".", "summary": "tiny", "interview": self.INTAKE}},
        }])
        # fake-pass the rest of the gates
        (self.root / "reviews").mkdir(exist_ok=True)
        (self.root / "reviews" / "concept.md").write_text("ok\n", encoding="utf-8")
        self._send([{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "concept_review", "arguments": {"path": ".", "verdict": "PASS", "artifact": "reviews/concept.md", "reviewer": "editor:mal"}}}])
        (self.root / "story-bible").mkdir(exist_ok=True)
        (self.root / "story-bible" / "world.md").write_text("ok\n", encoding="utf-8")
        self._send([{"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "bible", "arguments": {"path": ".", "artifact": "story-bible/world.md"}}}])
        for level, body in (("master", self.OUTLINE_MASTER), ("volume", self.OUTLINE_VOLUME), ("chapter", self.OUTLINE_CHAPTER)):
            (self.root / f"outlines/{level}.md").write_text(body, encoding="utf-8")
            self._send([{"jsonrpc": "2.0", "id": 90, "method": "tools/call", "params": {"name": "outline_write", "arguments": {"path": ".", "level": level, "artifact": f"outlines/{level}.md"}}}])
            (self.root / f"reviews/outline-{level}.md").write_text("ok\n", encoding="utf-8")
            self._send([{"jsonrpc": "2.0", "id": 91, "method": "tools/call", "params": {"name": "outline_review", "arguments": {"path": ".", "level": level, "verdict": "PASS", "artifact": f"reviews/outline-{level}.md", "reviewer": "editor:mal"}}}])
        self._send([{"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "outline_lock", "arguments": {"path": "."}}}])
        # Shrink the limit to 1
        wf = json.loads((self.root / "workflow.json").read_text(encoding="utf-8"))
        wf["limits"]["max_chapters"] = 1
        (self.root / "workflow.json").write_text(json.dumps(wf, ensure_ascii=False), encoding="utf-8")
        # First issue succeeds
        out = self._send([{"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "issue", "arguments": {"path": ".", "chapter": 1, "title": "t", "goal": "g"}}}])
        self.assertFalse(out[0]["result"].get("isError"), out[0])
        # Second is refused
        out = self._send([{"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "issue", "arguments": {"path": ".", "chapter": 2, "title": "t", "goal": "g"}}}])
        self.assertTrue(out[0]["result"].get("isError"))
        self.assertIn("max_chapters", _tool_text(out[0]["result"]))


if __name__ == "__main__":
    unittest.main()
