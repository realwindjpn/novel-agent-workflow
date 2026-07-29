"""Persistent local book library + active-book MCP session.

Two layers sit on top of the existing stdio MCP server:

``McpStdioClient`` owns a single child process running
``python -u -m novel_workflow.cli mcp --root <book>`` and turns it into a
small request/response coroutine: allocate an ID, write a JSON-RPC message
on stdin, read frames on stdout until the matching ID arrives, return the
result. A reader thread drains stderr into a bounded deque so a child
stack trace never blocks stdout parsing.

``LibrarySession`` is the long-lived wrapper used by both the launcher and
the local SPA. It enumerates books in a library directory, decides whether
to ``create_new`` or ``open_latest`` on a title collision, and (only after
``initialize`` plus an initial ``tools/call`` succeed) publishes the
client as the session's active MCP child. Switching books is serialised
under a single lock so a partial switch can never leave a request
pointed at the wrong project root.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Deque, Optional

from novel_workflow.library import ProjectEntry, discover_projects, next_book_directory


# --- Low-level stdio client -----------------------------------------------

class McpBridgeError(RuntimeError):
    """Raised when the MCP stdio child cannot be talked to."""


class McpStdioClient:
    """Minimal stdio JSON-RPC client for the local MCP server.

    The client owns the child process and the reader thread. All public
    methods are safe to call from one thread at a time; the internal
    lock serialises ID allocation, stdin writes, and stdout reads so a
    caller never sees interleaved messages.
    """

    def __init__(
        self,
        root: Path,
        *,
        python: Optional[Path] = None,
        popen: Callable[..., subprocess.Popen] = subprocess.Popen,
        timeout: float = 10.0,
    ) -> None:
        self._root = Path(root)
        if not self._root.is_dir():
            raise ValueError(f"root is not a directory: {self._root}")
        self._python = Path(python) if python is not None else Path(sys.executable)
        self._popen = popen
        self._timeout = float(timeout)
        self._proc: Optional[subprocess.Popen] = None
        self._stderr: Deque[str] = deque(maxlen=4096)
        self._reader: Optional[threading.Thread] = None
        self._next_id = 0
        self._lock = threading.Lock()
        self._open_lock = threading.Lock()
        # ``_inflight`` is keyed by request id; readers block on the
        # matching Event until the dispatcher threads a response to them.
        self._inflight: dict[int, tuple[threading.Event, dict]] = {}
        self._wake_event = threading.Event()
        self._wake_payload: Optional[dict] = None
        self._wake_lock = threading.Lock()
        self._closed = False
        self._server_info: Optional[dict] = None

    # -- public surface --------------------------------------------------

    @property
    def open(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    @property
    def root(self) -> Path:
        return self._root

    @property
    def stderr_tail(self) -> list[str]:
        return list(self._stderr)

    @property
    def server_info(self) -> Optional[dict]:
        return self._server_info

    def start(self) -> None:
        """Spawn the child and complete the MCP ``initialize`` handshake."""
        if self._proc is not None:
            raise McpBridgeError("client already started")
        cmd = self._build_command()
        # ``-u`` disables stdout buffering; we want raw JSON lines.
        self._proc = self._popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        self._reader = threading.Thread(
            target=self._drain_stdout, name="mcp-bridge-stdout", daemon=True
        )
        self._reader.start()
        err_reader = threading.Thread(
            target=self._drain_stderr, name="mcp-bridge-stderr", daemon=True
        )
        err_reader.start()
        info = self.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "local-library-bridge", "version": "0.1.0"},
        })
        server_info = info.get("serverInfo") or {}
        if server_info.get("name") != "novel-workflow":
            raise McpBridgeError(
                f"unexpected server identity: {server_info!r}"
            )
        self._server_info = server_info

    def request(self, method: str, params: Optional[dict] = None) -> dict:
        """Send one JSON-RPC request and block until the matching response."""
        if self._proc is None or self._proc.stdin is None:
            raise McpBridgeError("client not started")
        if not self.open:
            raise McpBridgeError("child process is not running")
        with self._lock:
            self._next_id += 1
            request_id = self._next_id
            event = threading.Event()
            self._inflight[request_id] = (event, {})
            message = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
            }
            if params is not None:
                message["params"] = params
            try:
                self._write_message(message)
            except Exception:
                self._inflight.pop(request_id, None)
                raise
        if not event.wait(timeout=self._timeout):
            self._inflight.pop(request_id, None)
            raise McpBridgeError(f"timeout waiting for {method} (id={request_id})")
        slot = self._inflight.pop(request_id, None)
        if slot is None:
            raise McpBridgeError(f"response slot missing for id={request_id}")
        _, response = slot
        if "error" in response:
            err = response["error"]
            raise McpBridgeError(
                f"{method} failed: {err.get('code')}: {err.get('message')}"
            )
        return response.get("result") or {}

    def close(self) -> None:
        """Idempotent shutdown of child + reader threads."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            proc = self._proc
            self._proc = None
        if proc is not None:
            try:
                if proc.stdin and not proc.stdin.closed:
                    proc.stdin.close()
            except OSError:
                pass
            try:
                proc.terminate()
            except OSError:
                pass
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except OSError:
                    pass
        # Wake anyone blocked on a request so they surface a clean error
        # instead of hanging forever.
        with self._wake_lock:
            self._wake_payload = {"jsonrpc": "2.0", "id": None, "error": {
                "code": -32000, "message": "client closed"
            }}
            self._wake_event.set()
        for event, _ in list(self._inflight.values()):
            event.set()

    # -- internals -------------------------------------------------------

    def _build_command(self) -> list[str]:
        return [
            str(self._python),
            "-u",
            "-m",
            "novel_workflow.cli",
            "mcp",
            "--root",
            str(self._root.resolve()),
        ]

    def _write_message(self, message: dict) -> None:
        assert self._proc is not None and self._proc.stdin is not None
        line = json.dumps(message, ensure_ascii=False)
        self._proc.stdin.write((line + "\n").encode("utf-8"))
        self._proc.stdin.flush()

    def _drain_stdout(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        for raw in self._proc.stdout:
            try:
                line = raw.decode("utf-8", errors="replace").strip()
            except Exception:
                continue
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                # Malformed frames are surfaced via stderr tail and ignored
                # for ID-matching; the next well-formed frame continues.
                continue
            if not isinstance(payload, dict):
                continue
            request_id = payload.get("id")
            if request_id is None:
                # Notification from the server; no caller waiting.
                continue
            with self._lock:
                slot = self._inflight.get(int(request_id))
            if slot is None:
                continue
            event, holder = slot
            holder.update(payload)
            event.set()

    def _drain_stderr(self) -> None:
        assert self._proc is not None and self._proc.stderr is not None
        for raw in self._proc.stderr:
            try:
                line = raw.decode("utf-8", errors="replace")
            except Exception:
                continue
            self._stderr.append(line.rstrip("\n"))


# --- Library session ------------------------------------------------------

@dataclass(frozen=True)
class BookCollision:
    """Returned by ``LibrarySession.create_book`` to prompt the UI."""
    title: str
    matches: list[ProjectEntry]


class LibrarySession:
    """Long-lived wrapper around one active book.

    The session owns a single ``McpStdioClient`` and exposes a higher-level
    vocabulary (``set_library``, ``create_book``, ``open_book``) that
    matches the SPA's needs. The active book is published only after
    ``initialize`` plus an initial MCP read succeed, so callers never
    see a half-open client.
    """

    def __init__(
        self,
        library: Path,
        *,
        client_factory: Callable[..., McpStdioClient] = McpStdioClient,
        picker_runner: Optional[Callable[[], Optional[Path]]] = None,
    ) -> None:
        self._library = Path(library)
        self._library.mkdir(parents=True, exist_ok=True)
        self._client: Optional[McpStdioClient] = None
        self._client_factory = client_factory
        self._switch_lock = threading.Lock()
        self._picker_runner = picker_runner

    # -- properties ------------------------------------------------------

    @property
    def library(self) -> Path:
        return self._library

    @property
    def client(self) -> Optional[McpStdioClient]:
        return self._client

    @property
    def open(self) -> bool:
        return self._client is not None and self._client.open

    @property
    def active_root(self) -> Optional[Path]:
        """The active book's root directory, or ``None`` when no book is open.

        Creative storage and other active-book-scoped bridges key off this
        so they can refuse work before any MCP child is published. It is
        intentionally read-only: the only way to change it is
        ``open_book`` / ``create_book``.
        """
        if not self.open or self._client is None:
            return None
        return self._client.root

    # -- library queries -------------------------------------------------

    def catalog(self) -> list[ProjectEntry]:
        return discover_projects(self._library)

    def set_library(self, path: Path) -> list[ProjectEntry]:
        """Re-target the library to ``path``; returns the new catalog."""
        path = Path(path)
        if not path.is_dir():
            raise ValueError(f"library is not a directory: {path}")
        self._library = path
        return self.catalog()

    def pick_library(self) -> Optional[Path]:
        """Interactive Windows folder picker; returns ``None`` if cancelled.

        The launcher bridges to a small PowerShell STA script that shows
        ``System.Windows.Forms.FolderBrowserDialog``; non-Windows callers
        should skip this and feed ``set_library`` directly. The
        ``picker_runner`` constructor argument lets tests inject a stub
        that returns a chosen path or ``None`` without spawning a real
        PowerShell subprocess.
        """
        if self._picker_runner is not None:
            return self._picker_runner()
        if sys.platform != "win32":
            return None
        script = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog;"
            "$dialog.Description = 'novel-workflow \u5e93\u76ee\u5f55';"
            "$dialog.ShowNewFolderButton = $true;"
            "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) "
            "{ [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            "Write-Output $dialog.SelectedPath }"
        )
        try:
            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-STA",
                    "-Command",
                    script,
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=60,
            )
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None
        picked = result.stdout.strip()
        if not picked:
            return None
        return Path(picked)

    # -- lifecycle -------------------------------------------------------

    def create_book(
        self,
        title: str,
        decision: Optional[str] = None,
    ) -> dict:
        """Create a new book, or report collisions if ``decision`` is unset.

        The MCP child is started on the reserved directory and ``init`` is
        invoked only after the handshake completes. The newly-spawned
        client is published as the session's active client only after the
        initial state read succeeds, so callers never see a half-open
        session.
        """
        title = (title or "").strip()
        if not title:
            raise ValueError("title is required")
        catalog = self.catalog()
        from novel_workflow.library import same_title  # avoid cycle
        matches = same_title(catalog, title)
        if matches and decision not in {"open_latest", "create_new"}:
            return {
                "status": "collision",
                "title": title,
                "matches": matches,
            }
        if decision == "open_latest":
            return self.open_book(matches[0].directory)
        target = next_book_directory(self._library, title)
        target.mkdir(parents=True, exist_ok=False)
        with self._switch_lock:
            self._close_quietly()
            client = self._client_factory(target)
            client.start()
            try:
                client.request("tools/call", {
                    "name": "init",
                    "arguments": {"path": ".", "title": title},
                })
                # Probe a cheap, read-only resource so a half-initialized
                # state never becomes visible to the rest of the system.
                client.request("resources/read", {"uri": "novel://state"})
            except Exception:
                client.close()
                if target.is_dir() and not any(target.iterdir()):
                    try:
                        target.rmdir()
                    except OSError:
                        pass
                raise
            self._client = client
        return {
            "status": "created",
            "directory": target.name,
            "path": str(target),
        }

    def open_book(self, directory: str) -> dict:
        """Switch the active book to ``directory`` (an immediate child).

        Rejects traversal segments, non-immediate children, missing or
        malformed ``workflow.json``, and symlinks whose target escapes the
        library. The active client is published only after initialize and
        a state read both succeed.
        """
        if not isinstance(directory, str) or not directory:
            raise ValueError("directory is required")
        if directory in {".", ".."} or "/" in directory or "\\" in directory:
            raise ValueError("directory must be an immediate child name")
        target = (self._library / directory).resolve()
        try:
            target.relative_to(self._library.resolve())
        except ValueError as exc:
            raise ValueError(
                f"directory escapes the library: {directory}"
            ) from exc
        if target.is_symlink():
            raise ValueError("symlinked books are not supported")
        if not target.is_dir():
            raise ValueError(f"book directory missing: {directory}")
        wf = target / "workflow.json"
        if not wf.is_file():
            raise ValueError(f"workflow.json missing in {directory}")
        try:
            json.loads(wf.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"workflow.json unreadable in {directory}: {exc}"
            ) from exc
        with self._switch_lock:
            self._close_quietly()
            client = self._client_factory(target)
            client.start()
            try:
                client.request("resources/read", {"uri": "novel://state"})
            except Exception:
                client.close()
                raise
            self._client = client
        return {
            "status": "opened",
            "directory": directory,
            "path": str(target),
        }

    def mcp(self, method: str, params: Optional[dict] = None) -> dict:
        """Pass-through to the active MCP client."""
        if self._client is None:
            raise McpBridgeError("no active book")
        return self._client.request(method, params)

    def tree_snapshot(
        self,
        *,
        max_entries: int = 5000,
        max_bytes: int = 2 * 1024 * 1024,
        skip_dirs: Optional[set[str]] = None,
    ) -> dict:
        """Bounded filesystem walk of the active book.

        Returns ``{"root": str|None, "entries": [...], "truncated": bool,
        "total_bytes": int}``. Entries are relative to the active book
        root. Top-level entries come first, alphabetically with
        directories sorted before files; each directory's children are
        listed directly after it. The walk stops after ``max_entries``
        items or when the cumulative file size would exceed
        ``max_bytes``, and reports ``truncated=True`` so the UI can offer
        a deeper view later. The directories named in ``skip_dirs`` are
        never recursed into; ``.git``, ``__pycache__``, and
        ``.pytest_cache`` are skipped by default. When no book is
        active, returns ``{"root": None, "entries": [], "truncated":
        False, "total_bytes": 0}``.

        Filesystem errors (broken symlinks, permission denied) are
        skipped, never raised. Symlinks and symlinked directories are
        not followed.
        """
        if self._client is None:
            return {
                "root": None, "entries": [], "truncated": False,
                "total_bytes": 0,
            }
        root = self._client.root
        if not root.is_dir():
            return {
                "root": str(root), "entries": [], "truncated": False,
                "total_bytes": 0,
            }
        skip = skip_dirs if skip_dirs is not None else {
            ".git", "__pycache__", ".pytest_cache", "node_modules",
        }
        entries: list[dict] = []
        total_bytes = 0
        truncated = False

        def visit(directory: Path, prefix: str) -> None:
            nonlocal truncated, total_bytes
            if truncated:
                return
            try:
                children = sorted(
                    directory.iterdir(),
                    key=lambda p: (not p.is_dir(), p.name.lower()),
                )
            except OSError:
                return
            for child in children:
                if len(entries) >= max_entries:
                    truncated = True
                    return
                rel = f"{prefix}{child.name}" if prefix else child.name
                try:
                    is_link = child.is_symlink()
                except OSError:
                    continue
                # Top-level skipped directories are also omitted from
                # the entry list, not just hidden from recursion, so
                # ``.git``/cache dirs never leak into the SPA view.
                if child.is_dir() and not is_link and child.name in skip:
                    continue
                try:
                    if child.is_dir() and not is_link:
                        entries.append(
                            {"path": rel, "type": "directory", "size": None}
                        )
                    elif child.is_file() and not is_link:
                        stat = child.stat()
                        size = int(stat.st_size)
                        if total_bytes + size > max_bytes:
                            truncated = True
                            return
                        entries.append(
                            {"path": rel, "type": "file", "size": size}
                        )
                        total_bytes += size
                except OSError:
                    continue
            # Recurse AFTER emitting this level so all root-level
            # entries surface before any subdirectory contents.
            for child in children:
                if truncated or len(entries) >= max_entries:
                    truncated = True
                    return
                if child.is_symlink() or not child.is_dir():
                    continue
                if child.name in skip:
                    continue
                rel = f"{prefix}{child.name}" if prefix else child.name
                visit(child, rel + "/")

        visit(root, "")
        return {
            "root": str(root),
            "entries": entries,
            "truncated": truncated,
            "total_bytes": total_bytes,
        }

    def close(self) -> None:
        with self._switch_lock:
            self._close_quietly()

    # -- helpers ---------------------------------------------------------

    def _close_quietly(self) -> None:
        if self._client is None:
            return
        try:
            self._client.close()
        except Exception:
            pass
        self._client = None
