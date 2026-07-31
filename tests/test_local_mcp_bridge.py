"""Tests for the local MCP stdio bridge and library session.

The bridge spawns a Python child running the existing stdio MCP server
and translates one JSON-RPC request/response at a time. The tests use a
fake child process so the test stays fast, deterministic, and offline:
the only thing they assert against the real CLI command is the *exact*
argv that ``McpStdioClient`` builds, since that is the long-lived
contract the launcher and the SPA both rely on.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.local_mcp_bridge import (
    BookCollision,
    LibrarySession,
    McpBridgeError,
    McpStdioClient,
)
from novel_workflow.library import ProjectEntry, TRASH_DIRECTORY, TRASH_INFO_FILE


class _FakeProc:
    """Minimal stand-in for ``subprocess.Popen`` for the bridge.

    The fake reads one JSON object per line from a queue of canned inputs
    and emits matching responses. Tests configure ``responses`` (a dict
    of ``id`` -> response dict); unconfigured ids cause the pump to block
    so the bridge's request timeout can fire.
    """

    def __init__(self, cmd, **kwargs):
        self.cmd = list(cmd)
        self.stdin = _FakeStdin()
        self.stdout = _FakeStdout()
        self.stderr = _FakeStdout()
        self._returncode: int | None = None
        self._reader_thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.responses: dict[int, dict] = {}
        self.request_log: list[dict] = []
        self.respond_delay: float = 0.0
        self._cv_resp = threading.Condition()
        self._started = False

    def start_reader(self) -> None:
        if self._started:
            return
        self._started = True
        self._reader_thread = threading.Thread(
            target=self._pump, name="fake-mcp-reader", daemon=True
        )
        self._reader_thread.start()

    def _pump(self) -> None:
        for raw in self.stdin.feed():
            try:
                line = raw.decode("utf-8").strip()
            except Exception:
                continue
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            self.request_log.append(msg)
            request_id = msg.get("id")
            if request_id is None:
                continue
            response = self._await_response(int(request_id))
            if response is None:
                return  # parent asked us to stop
            self.stdout.push(json.dumps(response).encode("utf-8") + b"\n")
        self._returncode = 0

    def _await_response(self, request_id: int) -> dict | None:
        """Block until a response for ``request_id`` is registered.

        Returning ``None`` signals the dispatcher that the test wants the
        pump to give up (e.g. the child has been marked exited).
        """
        deadline = None
        if self.respond_delay:
            deadline = time.monotonic() + 10.0
        while True:
            with self._cv_resp:
                if self._stop.is_set():
                    return None
                if self._returncode is not None:
                    return None
                if request_id in self.responses:
                    return self.responses.pop(request_id)
            # If the test never programmed a response, sleep briefly
            # then re-check; this lets the bridge's timeout fire.
            if deadline is not None and time.monotonic() > deadline:
                return None
            time.sleep(0.005)

    def poll(self) -> int | None:
        return self._returncode

    def terminate(self) -> None:
        self._returncode = 0
        self.stdout.close()
        self.stdin.close()

    def kill(self) -> None:
        self.terminate()

    def wait(self, timeout=None) -> int:
        return self._returncode or 0


class _FakeStdin:
    def __init__(self):
        self._buf: list[bytes] = []
        self._cv = threading.Condition()
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def write(self, data: bytes) -> None:
        if self._closed:
            raise ValueError("I/O on closed pipe")
        with self._cv:
            self._buf.append(data)
            self._cv.notify_all()

    def flush(self) -> None:
        return None

    def close(self) -> None:
        with self._cv:
            self._closed = True
            self._cv.notify_all()

    def feed(self):
        i = 0
        while True:
            with self._cv:
                while i >= len(self._buf) and not self._closed:
                    self._cv.wait(timeout=0.05)
                if i >= len(self._buf):
                    if self._closed:
                        return
                    continue
                chunk = self._buf[i]
                i += 1
            yield chunk


class _FakeStdout:
    def __init__(self):
        self._buf: list[bytes] = []
        self._cv = threading.Condition()
        self._closed = False

    def push(self, data: bytes) -> None:
        with self._cv:
            self._buf.append(data)
            self._cv.notify_all()

    def __iter__(self):
        return self

    def __next__(self) -> bytes:
        with self._cv:
            while not self._buf and not self._closed:
                self._cv.wait(timeout=0.05)
            if not self._buf:
                if self._closed:
                    raise StopIteration
                return b""
            return self._buf.pop(0)

    def close(self) -> None:
        with self._cv:
            self._closed = True
            self._cv.notify_all()


def _spawn(**kwargs):
    """Pre-create a fake and return a popen that hands it out.

    Tests want to configure ``fake.responses`` *before* the bridge ever
    spawns, so the responses table is in place when the bridge writes the
    first ``initialize`` frame. This helper allocates the fake eagerly
    and hands it back to every ``popen()`` call.
    """
    fake = _FakeProc(["python", "-u", "-m", "novel_workflow.cli", "mcp"])
    fake.start_reader()
    holder = {"fake": fake}

    def _popen(cmd, **popen_kwargs):
        return holder["fake"]

    return _popen, holder


def _write_project(root: Path, name: str, title: str = "Demo") -> None:
    p = root / name
    p.mkdir(parents=True, exist_ok=True)
    (p / "workflow.json").write_text(json.dumps({
        "title": title, "stage": "IDEA", "chapters": {}
    }), encoding="utf-8")


class McpStdioClientTests(unittest.TestCase):
    def test_build_command_uses_real_invocation(self):
        with tempfile.TemporaryDirectory() as d:
            book = Path(d) / "book"
            book.mkdir()
            client = McpStdioClient(book)
            self.assertEqual(
                client._build_command(),
                [
                    sys.executable,
                    "-u",
                    "-m",
                    "novel_workflow.cli",
                    "mcp",
                    "--root",
                    str(book.resolve()),
                ],
            )

    def test_initialize_round_trip_and_id_matching(self):
        with tempfile.TemporaryDirectory() as d:
            book = Path(d) / "book"
            book.mkdir()
            popen, holder = _spawn()
            client = McpStdioClient(book, popen=popen)
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {
                    "serverInfo": {"name": "novel-workflow", "version": "0.3.0"}
                },
            }
            client.start()
            self.assertEqual(client.server_info, {
                "name": "novel-workflow", "version": "0.3.0"
            })
            holder["fake"].responses[2] = {
                "jsonrpc": "2.0", "id": 2, "result": {"ok": True}
            }
            out = client.request("tools/list")
            self.assertEqual(out, {"ok": True})
            self.assertEqual(
                [m["method"] for m in holder["fake"].request_log],
                ["initialize", "tools/list"],
            )
            client.close()
            client.close()  # idempotent

    def test_serialised_concurrent_calls(self):
        with tempfile.TemporaryDirectory() as d:
            book = Path(d) / "book"
            book.mkdir()
            popen, holder = _spawn()
            client = McpStdioClient(book, popen=popen)
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"serverInfo": {"name": "novel-workflow"}},
            }
            client.start()
            holder["fake"].respond_delay = 0.05
            for expected_id in range(2, 12):
                holder["fake"].responses[expected_id] = {
                    "jsonrpc": "2.0", "id": expected_id,
                    "result": {"echo": expected_id},
                }
            results: list[dict] = []
            errors: list[BaseException] = []
            def _go(i: int) -> None:
                try:
                    results.append(client.request("tools/call", {"i": i}))
                except BaseException as exc:
                    errors.append(exc)
            threads = [threading.Thread(target=_go, args=(i,)) for i in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=5.0)
            self.assertFalse(errors, errors)
            self.assertEqual(
                sorted(r["echo"] for r in results),
                list(range(2, 12)),
            )
            client.close()

    def test_malformed_response_is_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            book = Path(d) / "book"
            book.mkdir()
            popen, holder = _spawn()
            client = McpStdioClient(book, popen=popen)
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"serverInfo": {"name": "novel-workflow"}},
            }
            client.start()
            holder["fake"].stdout.push(b"not json at all\n")
            holder["fake"].responses[2] = {
                "jsonrpc": "2.0", "id": 2, "result": {"ok": True}
            }
            out = client.request("tools/list")
            self.assertEqual(out, {"ok": True})
            client.close()

    def test_request_times_out(self):
        with tempfile.TemporaryDirectory() as d:
            book = Path(d) / "book"
            book.mkdir()
            popen, holder = _spawn()
            client = McpStdioClient(book, popen=popen, timeout=0.1)
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"serverInfo": {"name": "novel-workflow"}},
            }
            client.start()
            with self.assertRaises(McpBridgeError):
                client.request("tools/list")
            client.close()

    def test_early_exit_surfaces_error(self):
        with tempfile.TemporaryDirectory() as d:
            book = Path(d) / "book"
            book.mkdir()
            popen, holder = _spawn()
            client = McpStdioClient(book, popen=popen)
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"serverInfo": {"name": "novel-workflow"}},
            }
            client.start()
            holder["fake"]._returncode = 1
            with self.assertRaises(McpBridgeError):
                client.request("tools/list")
            client.close()


class LibrarySessionTests(unittest.TestCase):
    def _plain_book(self, library: Path, name: str, title: str = "Demo") -> Path:
        book = library / name
        book.mkdir()
        (book / "workflow.json").write_text(
            json.dumps({"title": title, "chapters": {}}), encoding="utf-8"
        )
        return book

    def test_trash_book_moves_and_tags_a_closed_book(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp)
            source = self._plain_book(library, "demo_20260731")
            session = LibrarySession(library)
            result = session.trash_book("demo_20260731")
            recycled = library / TRASH_DIRECTORY / result["trash_id"]
            self.assertFalse(source.exists())
            self.assertTrue((recycled / "workflow.json").is_file())
            tag = json.loads((recycled / TRASH_INFO_FILE).read_text(encoding="utf-8"))
            self.assertEqual(tag["original_directory"], "demo_20260731")
            self.assertEqual(tag["title"], "Demo")

    def test_trash_active_book_closes_client_before_move(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp)
            source = self._plain_book(library, "demo_20260731")
            events = []

            class ActiveClient:
                root = source
                open = True

                def close(inner_self):
                    self.assertTrue(source.exists())
                    events.append("closed")
                    inner_self.open = False

            session = LibrarySession(library)
            session._client = ActiveClient()
            result = session.trash_book("demo_20260731")
            self.assertEqual(events, ["closed"])
            self.assertIsNone(session.client)
            self.assertTrue(result["was_active"])

    def test_restore_book_renames_on_collision_and_removes_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp)
            self._plain_book(library, "demo_20260731")
            session = LibrarySession(library)
            trashed = session.trash_book("demo_20260731")
            self._plain_book(library, "demo_20260731", "Replacement")
            restored = session.restore_book(trashed["trash_id"])
            self.assertEqual(restored["directory"], "demo_20260731（恢复1）")
            self.assertTrue(restored["renamed"])
            target = library / restored["directory"]
            self.assertTrue((target / "workflow.json").is_file())
            self.assertFalse((target / TRASH_INFO_FILE).exists())
            self.assertFalse(session.open)

    def test_trash_book_rejects_traversal_and_reserved_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = LibrarySession(Path(tmp))
            for value in ("", ".", "..", ".trash", "../book", "a/b", "a\\b"):
                with self.subTest(value=value):
                    with self.assertRaises(ValueError):
                        session.trash_book(value)

    def test_tag_write_failure_rolls_book_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp)
            source = self._plain_book(library, "demo_20260731")
            session = LibrarySession(library)
            with patch("scripts.local_mcp_bridge.os.replace", side_effect=OSError("tag failed")):
                with self.assertRaises(OSError):
                    session.trash_book("demo_20260731")
            self.assertTrue(source.is_dir())
            self.assertFalse((source / TRASH_INFO_FILE).exists())

    def test_failed_active_close_aborts_before_move(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp)
            source = self._plain_book(library, "demo_20260731")

            class FailingClient:
                root = source
                open = True

                def close(inner_self):
                    raise RuntimeError("close failed")

            session = LibrarySession(library)
            session._client = FailingClient()
            with self.assertRaisesRegex(RuntimeError, "close failed"):
                session.trash_book("demo_20260731")
            self.assertTrue(source.is_dir())
            trash_root = library / TRASH_DIRECTORY
            self.assertFalse(trash_root.exists() and any(trash_root.iterdir()))

    def test_trash_book_rejects_symlinked_book(self):
        if not _symlink_supported():
            self.skipTest("symlinks not supported on this platform")
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp) / "library"
            library.mkdir()
            outside = Path(tmp) / "outside"
            outside.mkdir()
            (outside / "workflow.json").write_text("{}", encoding="utf-8")
            (library / "linked").symlink_to(outside, target_is_directory=True)
            session = LibrarySession(library)
            with self.assertRaisesRegex(ValueError, "symlink"):
                session.trash_book("linked")
            self.assertTrue(outside.is_dir())

    @unittest.skipUnless(sys.platform == "win32", "Windows junction test")
    def test_trash_book_rejects_junctioned_book(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp) / "library"
            library.mkdir()
            outside = Path(tmp) / "outside"
            outside.mkdir()
            self._plain_book(outside, "book")
            junction = library / "linked"
            created = subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(outside / "book")],
                capture_output=True,
                text=True,
            )
            if created.returncode != 0:
                self.skipTest("cannot create a Windows junction in this environment")
            self.assertFalse(junction.is_symlink())
            with self.assertRaisesRegex(ValueError, "junction"):
                LibrarySession(library).trash_book("linked")

    @unittest.skipUnless(sys.platform == "win32", "Windows junction test")
    def test_trash_book_rejects_junctioned_trash_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp) / "library"
            library.mkdir()
            self._plain_book(library, "demo_20260731")
            outside = Path(tmp) / "outside"
            outside.mkdir()
            junction = library / TRASH_DIRECTORY
            created = subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(outside)],
                capture_output=True,
                text=True,
            )
            if created.returncode != 0:
                self.skipTest("cannot create a Windows junction in this environment")
            self.assertFalse(junction.is_symlink())
            with self.assertRaisesRegex(ValueError, "junction"):
                LibrarySession(library).trash_book("demo_20260731")

    def test_restore_rejects_traversal_and_symlinked_trash_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp) / "library"
            library.mkdir()
            session = LibrarySession(library)
            for value in ("", ".", "..", ".trash", "../book", "a/b", "a\\b"):
                with self.subTest(value=value):
                    with self.assertRaises(ValueError):
                        session.restore_book(value)
            if _symlink_supported():
                outside = Path(tmp) / "outside"
                outside.mkdir()
                trash_root = library / TRASH_DIRECTORY
                trash_root.mkdir()
                (trash_root / "linked").symlink_to(outside, target_is_directory=True)
                with self.assertRaisesRegex(ValueError, "symlink"):
                    session.restore_book("linked")

    @unittest.skipUnless(sys.platform == "win32", "Windows junction test")
    def test_restore_rejects_junctioned_trash_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp) / "library"
            library.mkdir()
            trash_root = library / TRASH_DIRECTORY
            trash_root.mkdir()
            outside = Path(tmp) / "outside"
            outside.mkdir()
            junction = trash_root / "linked"
            created = subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(outside)],
                capture_output=True,
                text=True,
            )
            if created.returncode != 0:
                self.skipTest("cannot create a Windows junction in this environment")
            self.assertFalse(junction.is_symlink())
            with self.assertRaisesRegex(ValueError, "junction"):
                LibrarySession(library).restore_book("linked")

    def test_trash_move_failure_preserves_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp)
            source = self._plain_book(library, "demo_20260731")
            session = LibrarySession(library)
            original_rename = os.rename

            def fail_first_move(path, target):
                if path == source:
                    raise OSError("trash move failed")
                return original_rename(path, target)

            with patch("scripts.local_mcp_bridge.os.rename", fail_first_move):
                with self.assertRaisesRegex(OSError, "trash move failed"):
                    session.trash_book("demo_20260731")
            self.assertTrue(source.is_dir())
            self.assertFalse((source / TRASH_INFO_FILE).exists())

    def test_restore_failure_recreates_original_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp)
            self._plain_book(library, "demo_20260731")
            session = LibrarySession(library)
            moved = session.trash_book("demo_20260731")
            recycled = library / TRASH_DIRECTORY / moved["trash_id"]
            expected = (recycled / TRASH_INFO_FILE).read_bytes()
            original_rename = os.rename

            def fail_restore(path, target):
                if path == recycled:
                    raise OSError("restore move failed")
                return original_rename(path, target)

            with patch("scripts.local_mcp_bridge.os.rename", fail_restore):
                with self.assertRaisesRegex(OSError, "restore move failed"):
                    session.restore_book(moved["trash_id"])
            self.assertEqual((recycled / TRASH_INFO_FILE).read_bytes(), expected)
            self.assertFalse((library / "demo_20260731").exists())

    def test_restore_retries_collision_created_after_destination_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp)
            self._plain_book(library, "demo_20260731")
            session = LibrarySession(library)
            moved = session.trash_book("demo_20260731")
            recycled = library / TRASH_DIRECTORY / moved["trash_id"]
            original_rename = os.rename
            raced = False

            def collide_once(path, target):
                nonlocal raced
                if path == recycled and not raced:
                    raced = True
                    Path(target).mkdir()
                    raise FileExistsError("destination appeared during restore")
                return original_rename(path, target)

            with patch("scripts.local_mcp_bridge.os.rename", collide_once):
                restored = session.restore_book(moved["trash_id"])
            self.assertTrue(raced)
            self.assertEqual(restored["directory"], "demo_20260731（恢复1）")
            self.assertTrue((library / "demo_20260731").is_dir())
            self.assertTrue((library / restored["directory"] / "workflow.json").is_file())

    def test_restore_rollback_preserves_concurrently_recreated_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp)
            self._plain_book(library, "demo_20260731")
            session = LibrarySession(library)
            moved = session.trash_book("demo_20260731")
            recycled = library / TRASH_DIRECTORY / moved["trash_id"]
            tag = recycled / TRASH_INFO_FILE
            recreated = b'{"concurrent": true}\n'
            original_rename = os.rename

            def recreate_tag_then_fail(path, target):
                if path == recycled:
                    tag.write_bytes(recreated)
                    raise OSError("restore move failed")
                return original_rename(path, target)

            with patch("scripts.local_mcp_bridge.os.rename", recreate_tag_then_fail):
                with self.assertRaisesRegex(OSError, "restore move failed"):
                    session.restore_book(moved["trash_id"])
            self.assertEqual(tag.read_bytes(), recreated)

    def test_open_book_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            session = LibrarySession(Path(d))
            with self.assertRaises(ValueError):
                session.open_book("../escape")
            with self.assertRaises(ValueError):
                session.open_book("a/b")
            with self.assertRaises(ValueError):
                session.open_book(".")

    def test_open_book_rejects_non_immediate_child(self):
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            nested = lib / "outer" / "inner"
            nested.mkdir(parents=True)
            session = LibrarySession(lib)
            with self.assertRaises(ValueError):
                session.open_book("outer")

    def test_open_book_rejects_missing_or_malformed_workflow(self):
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            empty = lib / "empty"
            empty.mkdir()
            (empty / "workflow.json").write_text("{not json", encoding="utf-8")
            session = LibrarySession(lib)
            with self.assertRaises(ValueError):
                session.open_book("empty")

    def test_open_book_rejects_symlink_escape(self):
        if not _symlink_supported():
            self.skipTest("symlinks not supported here")
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d) / "lib"
            lib.mkdir()
            outside = Path(d) / "outside"
            outside.mkdir()
            (outside / "workflow.json").write_text("{}", encoding="utf-8")
            (lib / "sneak").symlink_to(outside)
            session = LibrarySession(lib)
            with self.assertRaises(ValueError):
                session.open_book("sneak")

    def test_create_book_publishes_client_only_after_initialize(self):
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            popen, holder = _spawn()
            session = LibrarySession(lib, client_factory=lambda root, **kw: _make_client(root, popen, holder))
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"serverInfo": {"name": "novel-workflow"}},
            }
            holder["fake"].responses[2] = {
                "jsonrpc": "2.0", "id": 2, "result": {"ok": True}
            }
            holder["fake"].responses[3] = {
                "jsonrpc": "2.0", "id": 3, "result": {"ok": True}
            }
            result = session.create_book("\u63a5\u53e3")
            self.assertEqual(result["status"], "created")
            self.assertTrue(session.open)
            # The child must have run initialize + tools/call init + state read
            methods = [m["method"] for m in holder["fake"].request_log]
            self.assertEqual(methods, ["initialize", "tools/call", "resources/read"])
            session.close()

    def test_create_book_reports_collision_when_title_matches(self):
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            _write_project(lib, "\u63a5\u53e3_20260728", title="\u63a5\u53e3")
            session = LibrarySession(lib)
            result = session.create_book("\u63a5\u53e3")
            self.assertEqual(result["status"], "collision")
            self.assertEqual(len(result["matches"]), 1)
            self.assertIsInstance(result["matches"][0], ProjectEntry)

    def test_tree_snapshot_returns_empty_when_no_active_book(self):
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            session = LibrarySession(lib)
            snap = session.tree_snapshot()
            self.assertIsNone(snap["root"])
            self.assertEqual(snap["entries"], [])
            self.assertFalse(snap["truncated"])

    def test_tree_snapshot_walks_active_book_files_and_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            book = lib / "demo_20260728"
            book.mkdir()
            (book / "workflow.json").write_text("{\"meta\": {\"title\": \"demo\"}}", encoding="utf-8")
            (book / "chapters").mkdir()
            (book / "chapters" / "ch-001.md").write_text("hello", encoding="utf-8")
            (book / "chapters" / "ch-002.md").write_text("world!" * 4, encoding="utf-8")

            popen, holder = _spawn()
            session = LibrarySession(lib, client_factory=lambda root, **kw: _make_client(root, popen, holder))
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"serverInfo": {"name": "novel-workflow"}},
            }
            holder["fake"].responses[2] = {
                "jsonrpc": "2.0", "id": 2, "result": {"ok": True}
            }
            result = session.open_book("demo_20260728")
            self.assertEqual(result["status"], "opened")
            snap = session.tree_snapshot()
            self.assertEqual(snap["root"], str(book.resolve()))
            names = [e["path"] for e in snap["entries"]]
            # Directories first, then files alphabetically within each.
            self.assertEqual(names[:2], ["chapters", "workflow.json"])
            self.assertIn("chapters/ch-001.md", names)
            self.assertIn("chapters/ch-002.md", names)
            sizes = {e["path"]: e["size"] for e in snap["entries"]}
            self.assertIsNone(sizes["chapters"])
            self.assertEqual(sizes["chapters/ch-001.md"], 5)
            self.assertEqual(sizes["chapters/ch-002.md"], 24)
            self.assertFalse(snap["truncated"])
            session.close()

    def test_tree_snapshot_respects_max_entries(self):
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            book = lib / "many_20260728"
            book.mkdir()
            for i in range(10):
                (book / f"file-{i:02d}.txt").write_text("x", encoding="utf-8")
            (book / "workflow.json").write_text(
                "{\"meta\": {\"title\": \"many\"}}", encoding="utf-8"
            )

            popen, holder = _spawn()
            session = LibrarySession(lib, client_factory=lambda root, **kw: _make_client(root, popen, holder))
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"serverInfo": {"name": "novel-workflow"}},
            }
            holder["fake"].responses[2] = {
                "jsonrpc": "2.0", "id": 2, "result": {"ok": True}
            }
            session.open_book("many_20260728")
            snap = session.tree_snapshot(max_entries=3)
            self.assertEqual(len(snap["entries"]), 3)
            self.assertTrue(snap["truncated"])
            session.close()

    def test_tree_snapshot_skips_unreadable_children(self):
        if not _symlink_supported():
            self.skipTest("symlinks not supported on this platform")
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            book = lib / "broken_20260728"
            book.mkdir()
            (book / "visible.txt").write_text("ok", encoding="utf-8")
            (book / "workflow.json").write_text(
                "{\"meta\": {\"title\": \"broken\"}}", encoding="utf-8"
            )
            # A symlink whose target was deleted should be skipped, not raise.
            ghost = book / "ghost.txt"
            ghost.symlink_to(book / "missing.txt")

            popen, holder = _spawn()
            session = LibrarySession(lib, client_factory=lambda root, **kw: _make_client(root, popen, holder))
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"serverInfo": {"name": "novel-workflow"}},
            }
            holder["fake"].responses[2] = {
                "jsonrpc": "2.0", "id": 2, "result": {"ok": True}
            }
            session.open_book("broken_20260728")
            snap = session.tree_snapshot()
            names = [e["path"] for e in snap["entries"]]
            self.assertIn("visible.txt", names)
            self.assertNotIn("ghost.txt", names)
            session.close()

    def test_tree_snapshot_skips_git_and_cache_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            book = lib / "book_20260728"
            book.mkdir()
            (book / "workflow.json").write_text("{}", encoding="utf-8")
            (book / ".git").mkdir()
            (book / ".git" / "HEAD").write_text("ref: master", encoding="utf-8")
            (book / "__pycache__").mkdir()
            (book / "__pycache__" / "x.pyc").write_bytes(b"\x00")
            (book / "chapters").mkdir()
            (book / "chapters" / "c1.md").write_text("# C1", encoding="utf-8")
            popen, holder = _spawn()
            session = LibrarySession(lib, client_factory=lambda root, **kw: _make_client(root, popen, holder))
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"serverInfo": {"name": "novel-workflow"}},
            }
            holder["fake"].responses[2] = {
                "jsonrpc": "2.0", "id": 2, "result": {"ok": True}
            }
            session.open_book("book_20260728")
            snap = session.tree_snapshot()
            names = [e["path"] for e in snap["entries"]]
            self.assertIn("workflow.json", names)
            self.assertIn("chapters", names)
            self.assertIn("chapters/c1.md", names)
            self.assertNotIn(".git", names)
            self.assertNotIn(".git/HEAD", names)
            self.assertNotIn("__pycache__", names)
            self.assertNotIn("__pycache__/x.pyc", names)
            # "{}" (2) + "# C1" (4) = 6 bytes of text content
            self.assertEqual(snap["total_bytes"], 6)
            session.close()

    def test_tree_snapshot_respects_total_byte_cap(self):
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            book = lib / "book_20260728"
            book.mkdir()
            (book / "workflow.json").write_text("{}", encoding="utf-8")
            (book / "a.bin").write_bytes(b"x" * 1000)
            (book / "b.bin").write_bytes(b"y" * 1000)
            (book / "c.bin").write_bytes(b"z" * 1000)
            popen, holder = _spawn()
            session = LibrarySession(lib, client_factory=lambda root, **kw: _make_client(root, popen, holder))
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"serverInfo": {"name": "novel-workflow"}},
            }
            holder["fake"].responses[2] = {
                "jsonrpc": "2.0", "id": 2, "result": {"ok": True}
            }
            session.open_book("book_20260728")
            snap = session.tree_snapshot(max_bytes=1500)
            # Only one of the three 1KB files fit before the cap is hit.
            self.assertTrue(snap["truncated"])
            self.assertLessEqual(snap["total_bytes"], 1500)
            session.close()

    def test_tree_snapshot_does_not_follow_symlinks(self):
        if not _symlink_supported():
            self.skipTest("symlinks not supported on this platform")
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            book = lib / "book_20260728"
            book.mkdir()
            (book / "workflow.json").write_text("{}", encoding="utf-8")
            outside = Path(d) / "outside"
            outside.mkdir()
            (outside / "secret.txt").write_text("hush", encoding="utf-8")
            (book / "link").symlink_to(outside)
            popen, holder = _spawn()
            session = LibrarySession(lib, client_factory=lambda root, **kw: _make_client(root, popen, holder))
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"serverInfo": {"name": "novel-workflow"}},
            }
            holder["fake"].responses[2] = {
                "jsonrpc": "2.0", "id": 2, "result": {"ok": True}
            }
            session.open_book("book_20260728")
            snap = session.tree_snapshot()
            names = [e["path"] for e in snap["entries"]]
            self.assertNotIn("link", names)
            self.assertNotIn("link/secret.txt", names)
            session.close()

    def test_active_root_is_none_until_a_book_is_open(self):
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            book = lib / "demo_20260728"
            book.mkdir()
            (book / "workflow.json").write_text(
                "{\"meta\": {\"title\": \"demo\"}}", encoding="utf-8"
            )
            popen, holder = _spawn()
            session = LibrarySession(
                lib, client_factory=lambda root, **kw: _make_client(root, popen, holder)
            )
            self.assertIsNone(session.active_root)
            holder["fake"].responses[1] = {
                "jsonrpc": "2.0", "id": 1,
                "result": {"serverInfo": {"name": "novel-workflow"}},
            }
            holder["fake"].responses[2] = {
                "jsonrpc": "2.0", "id": 2, "result": {"ok": True}
            }
            session.open_book("demo_20260728")
            self.assertEqual(session.active_root.name, "demo_20260728")
            session.close()


def _make_client(root, popen, holder):
    client = McpStdioClient(root, popen=popen)
    # Stash the holder so tests can configure responses by reference.
    client._test_holder = holder
    return client


def _symlink_supported() -> bool:
    try:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a").symlink_to(Path(d) / "b")
        return True
    except (OSError, NotImplementedError):
        return False


class PickerRunnerTests(unittest.TestCase):
    """Validate the Windows folder-picker behaviour without spawning PowerShell.

    The real PowerShell script is exercised manually on Windows; the
    automated tests cover the two paths that matter: a chosen path is
    surfaced, and a cancellation surfaces as ``None``. The
    ``picker_runner`` injection means we never shell out, so the test
    runs on every host (including this Linux sandbox).
    """

    def test_picker_runner_returns_chosen_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            chosen = Path(tmp) / "books"
            chosen.mkdir()
            session = LibrarySession(
                Path(tmp) / "library",
                picker_runner=lambda: chosen,
            )
            self.assertEqual(session.pick_library(), chosen)

    def test_picker_runner_cancel_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = LibrarySession(
                Path(tmp) / "library",
                picker_runner=lambda: None,
            )
            self.assertIsNone(session.pick_library())

    def test_picker_runner_takes_precedence_over_subprocess(self):
        # The runner injection must short-circuit any real subprocess
        # attempt; if PowerShell actually ran, the runner would be
        # bypassed. Asserting precedence prevents accidental fall-through.
        with tempfile.TemporaryDirectory() as tmp:
            chosen = Path(tmp) / "picked"
            chosen.mkdir()
            session = LibrarySession(
                Path(tmp) / "library",
                picker_runner=lambda: chosen,
            )
            # The default path (no runner) would return None on non-Windows.
            # With the runner it must return the chosen path regardless.
            self.assertEqual(session.pick_library(), chosen)

    def test_picker_subprocess_command_is_fixed_and_lacks_user_input(self):
        # The default Windows path shells out to a hard-coded
        # ``powershell.exe -NoProfile -STA -Command <script>`` tuple.
        # Lock the exact shape so a future change cannot accidentally
        # interpolate caller-controlled text. The runner is intentionally
        # not used here so we exercise the real subprocess path; the
        # platform check is patched to ``win32`` so the Linux sandbox
        # still reaches the subprocess branch.
        captured: dict = {}

        class _FakeRun:
            def __call__(self, cmd, **kwargs):
                captured["cmd"] = list(cmd)
                captured["kwargs"] = dict(kwargs)
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            session = LibrarySession(Path(tmp) / "library")
            from scripts import local_mcp_bridge as bridge_mod
            original_run = bridge_mod.subprocess.run
            original_platform = bridge_mod.sys.platform
            bridge_mod.subprocess.run = _FakeRun()  # type: ignore[assignment]
            bridge_mod.sys.platform = "win32"  # type: ignore[attr-defined]
            try:
                self.assertIsNone(session.pick_library())
            finally:
                bridge_mod.subprocess.run = original_run
                bridge_mod.sys.platform = original_platform
        cmd = captured["cmd"]
        self.assertEqual(cmd[:3], ["powershell.exe", "-NoProfile", "-STA"])
        self.assertEqual(cmd[3], "-Command")
        # The script body must be a single string and must NOT contain
        # any of the runtime library path.
        script = cmd[4]
        self.assertIsInstance(script, str)
        self.assertNotIn(str(tmp), script)
        self.assertNotIn(str(Path(tmp) / "library"), script)
        self.assertIn("FolderBrowserDialog", script)
        # Subprocess flags lock down IO so a hung dialog never blocks.
        self.assertEqual(captured["kwargs"].get("check"), True)
        self.assertEqual(captured["kwargs"].get("timeout"), 60)


if __name__ == "__main__":
    unittest.main()
