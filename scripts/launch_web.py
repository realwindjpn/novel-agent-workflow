#!/usr/bin/env python3
"""Start the browser SPA and a disposable Cloudflare Quick Tunnel."""
from __future__ import annotations

import argparse
import atexit
import base64
import ctypes
import functools
import json
import os
import queue
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from collections import deque
from ctypes import wintypes
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Optional, Protocol, Sequence

# ``一键启动.cmd`` executes this file by path.  In that mode Python puts the
# scripts directory (not the repository root) on ``sys.path``, so the later
# ``scripts.local_mcp_bridge`` package import would otherwise fail before the
# launcher can show a useful status message.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


HOST = "127.0.0.1"
DEFAULT_PORT = 8080
DEFAULT_PUBLIC_PORT = 8081
LOCAL_API_PREFIX = "/api/local/"
QUICK_TUNNEL_RE = re.compile(
    r"https://[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.trycloudflare\.com(?=$|[\s/?#:])",
    re.IGNORECASE,
)
MCP_METHOD_WHITELIST = frozenset({
    "ping",
    "tools/list",
    "tools/call",
    "resources/list",
    "resources/read",
    "prompts/list",
    "prompts/get",
})


class LauncherError(RuntimeError):
    """A user-actionable launcher failure."""


class LauncherStopped(Exception):
    """The user requested a clean stop while startup was still in progress."""


@dataclass(frozen=True)
class LauncherConfig:
    port: int = DEFAULT_PORT
    public_port: int = DEFAULT_PUBLIC_PORT
    open_browser: bool = True
    enable_tunnel: bool = True
    library_root: Optional[Path] = None


def parse_args(argv: Sequence[str] | None = None) -> LauncherConfig:
    parser = argparse.ArgumentParser(
        description="Start novel-workflow web and a Cloudflare Quick Tunnel."
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--public-port", type=int, default=DEFAULT_PUBLIC_PORT)
    parser.add_argument("--library-root", type=Path, default=None)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument(
        "--no-tunnel",
        action="store_true",
        help="start the local/public listeners without cloudflared",
    )
    ns = parser.parse_args(argv)
    if not 1 <= ns.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if not 1 <= ns.public_port <= 65535:
        parser.error("--public-port must be between 1 and 65535")
    if ns.port == ns.public_port:
        parser.error("--port and --public-port must be different")
    return LauncherConfig(
        port=ns.port,
        public_port=ns.public_port,
        open_browser=not ns.no_browser,
        enable_tunnel=not ns.no_tunnel,
        library_root=ns.library_root,
    )


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def validate_web_root(root: Path) -> Path:
    web_root = (root / "web").resolve()
    index = web_root / "index.html"
    if not index.is_file():
        raise LauncherError(f"Cannot find web entry point: {index} (requires web/index.html)")
    return web_root


def parse_quick_tunnel_url(line: str) -> str | None:
    match = QUICK_TUNNEL_RE.search(line)
    return match.group(0) if match else None


def find_cloudflared(
    lookup: Callable[[str], str | None] = shutil.which,
) -> Path:
    found = lookup("cloudflared")
    if not found:
        raise LauncherError(
            "Cannot find cloudflared. Install the Cloudflare Tunnel client and add it to PATH."
        )
    return Path(found)


def ensure_port_available(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Mirror ThreadingHTTPServer's SO_REUSEADDR so the pre-check is not
        # fooled by a freshly closed server still in TIME_WAIT.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError as exc:
            raise LauncherError(
                f"Port {port} is already in use; close the occupying process or use --port."
            ) from exc


class HttpProbe(Protocol):
    def __call__(self, url: str, marker: str | None = None) -> bool: ...


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:  # type: ignore[override]
        """Keep the public static server from exposing local API routes."""
        if self.path.startswith(LOCAL_API_PREFIX):
            self.send_error(404, "Not Found")
            return
        super().do_GET()

    def do_HEAD(self) -> None:  # type: ignore[override]
        """Keep the public static server from exposing local API routes."""
        if self.path.startswith(LOCAL_API_PREFIX):
            self.send_error(404, "Not Found")
            return
        super().do_HEAD()

    def do_POST(self) -> None:  # type: ignore[override]
        """Keep the public static server from exposing local API routes."""
        if self.path.startswith(LOCAL_API_PREFIX):
            self.send_error(404, "Not Found")
            return
        self.send_error(405, "Method Not Allowed")


def start_http_server(
    web_root: Path,
    host: str,
    port: int,
    *,
    handler_factory: Optional[Callable[..., BaseHTTPRequestHandler]] = None,
    server_name: str = "novel-workflow-http",
) -> tuple[ThreadingHTTPServer, threading.Thread]:
    """Start a static-file (or custom) HTTP server on ``(host, port)``.

    ``handler_factory`` defaults to :class:`QuietStaticHandler` rooted at
    ``web_root``. Callers wanting a custom handler (e.g. the local API
    router) can pass a ``functools.partial`` that closes over any extra
    state. ``server_name`` is only used to label the daemon thread.
    """
    if handler_factory is None:
        handler_factory = functools.partial(
            QuietStaticHandler, directory=str(web_root)
        )
    server = ThreadingHTTPServer((host, port), handler_factory)
    server.daemon_threads = True
    thread = threading.Thread(
        target=server.serve_forever,
        name=server_name,
        daemon=True,
    )
    thread.start()
    return server, thread


def probe_http(url: str, marker: str | None = None) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            if response.status < 200 or response.status >= 400:
                return False
            body = response.read(256 * 1024).decode("utf-8", errors="replace")
            return marker is None or marker in body
    except (OSError, urllib.error.URLError, ValueError):
        return False


def wait_until_ready(
    url: str,
    *,
    timeout: float,
    probe: HttpProbe = probe_http,
    marker: str | None = None,
    interval: float = 0.2,
    stop_event: threading.Event | None = None,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if stop_event is not None and stop_event.is_set():
            raise LauncherStopped
        if probe(url, marker):
            return
        time.sleep(interval)
    raise LauncherError(f"Timed out waiting for endpoint: {url}")


# --- Local API ----------------------------------------------------------
#
# The local API lives on the private port (default 8080) only. It exposes
# a small JSON surface so the SPA can list, create, open, and probe the
# local book library without the user pasting a long path in the URL bar.
# Every endpoint except ``/api/local/capabilities`` requires a token
# generated at launcher startup. Every endpoint (including capabilities)
# requires the ``Origin`` header to match the private host, so a script
# running on the same machine cannot impersonate the browser.


def _origin_allowed(origin: str, host: str, port: int) -> bool:
    """Return ``True`` when ``origin`` points back at the local server."""
    if not origin:
        return False
    expected_hosts = {f"http://localhost:{port}", f"http://127.0.0.1:{port}"}
    return origin.rstrip("/") in expected_hosts


def _bearer_or_x_token(handler: BaseHTTPRequestHandler) -> Optional[str]:
    """Extract a token from ``Authorization: Bearer`` or ``X-Library-Token``."""
    auth = handler.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return handler.headers.get("X-Library-Token", "").strip() or None


class NoActiveBookError(Exception):
    """Raised when a creative route is called without an active book."""


class LocalApi:
    """Routes JSON requests against a :class:`LibrarySession`.

    The API is intentionally narrow: it is the *only* surface that talks
    to the MCP child, and it is reachable only from the local browser.
    Any 4xx/5xx response goes through :meth:`_send_error` so the SPA can
    rely on a stable ``{"error": {"code": str, "message": str}}`` shape.
    """

    def __init__(
        self,
        session: "LibrarySession",
        *,
        host: str = HOST,
        port: int = DEFAULT_PORT,
        token: Optional[str] = None,
        mcp_whitelist: frozenset[str] = MCP_METHOD_WHITELIST,
        creative_store_factory: Optional[Callable[..., "CreativeStore"]] = None,
    ) -> None:
        self._session = session
        self._host = host
        self._port = int(port)
        self._token = token or secrets.token_urlsafe(32)
        self._mcp_whitelist = mcp_whitelist
        self._creative_store_factory = creative_store_factory or _default_creative_store

    @property
    def token(self) -> str:
        return self._token

    @property
    def public_origin(self) -> str:
        return f"http://localhost:{self._port}"

    @property
    def port(self) -> int:
        return self._port

    @port.setter
    def port(self, value: int) -> None:
        """Update the bound port after the HTTP server actually listens.

        ``port=0`` asks the OS for any free port; the real port is only
        known after ``ThreadingHTTPServer`` is bound. Tests rely on this
        to keep the local API in sync with whichever port the server
        ended up using.
        """
        self._port = int(value)

    # -- dispatch --------------------------------------------------------

    def handle(self, handler: BaseHTTPRequestHandler, method: str) -> None:
        path = handler.path
        if not path.startswith(LOCAL_API_PREFIX):
            self._send_error(handler, 404, "not_found", "Unknown endpoint.")
            return
        sub = path[len(LOCAL_API_PREFIX):].rstrip("/")
        # ``capabilities`` is the only unauthenticated endpoint; it's how
        # the SPA learns the token and what it can call.
        if sub == "capabilities" and method == "GET":
            self._serve_capabilities(handler)
            return
        origin = handler.headers.get("Origin", "")
        if origin and not _origin_allowed(origin, self._host, self._port):
            self._send_error(
                handler, 403, "origin_rejected",
                "Origin is not allowed for the local API.",
            )
            return
        if _bearer_or_x_token(handler) != self._token:
            self._send_error(
                handler, 401, "unauthorized",
                "Missing or invalid library token.",
            )
            return
        route = (method, sub)
        try:
            if route == ("GET", "library"):
                self._serve_library(handler)
            elif route == ("POST", "library"):
                self._serve_set_library(handler)
            elif route == ("GET", "trash"):
                self._serve_trash(handler)
            elif route == ("POST", "trash"):
                self._serve_trash_book(handler)
            elif route == ("POST", "restore"):
                self._serve_restore_book(handler)
            elif route == ("POST", "select-directory"):
                self._serve_select_directory(handler)
            elif route == ("GET", "tree"):
                self._serve_tree(handler)
            elif route == ("POST", "open"):
                self._serve_open(handler)
            elif route == ("POST", "create"):
                self._serve_create(handler)
            elif route == ("POST", "mcp"):
                self._serve_mcp(handler)
            elif route == ("GET", "active"):
                self._serve_active(handler)
            elif route == ("GET", "creative/session"):
                self._serve_creative_session(handler)
            elif route == ("POST", "creative/turn"):
                self._serve_creative_turn(handler)
            elif route == ("POST", "creative/state"):
                self._serve_creative_state(handler)
            elif route == ("POST", "creative/conversation-state"):
                self._serve_creative_conversation_state(handler)
            elif route == ("POST", "creative/proposal"):
                self._serve_creative_proposal(handler)
            elif route == ("POST", "creative/draft"):
                self._serve_creative_draft(handler)
            elif route == ("GET", "creative/export"):
                self._serve_creative_export(handler)
            elif route == ("POST", "creative/import"):
                self._serve_creative_import(handler)
            else:
                self._send_error(handler, 404, "not_found", "Unknown route.")
        except ValueError as exc:
            self._send_error(handler, 400, "bad_request", str(exc))
        except NoActiveBookError as exc:
            self._send_error(handler, 409, "no_active_book", str(exc))
        except CreativeStoreError as exc:
            self._send_error(handler, 400, "creative_error", str(exc))
        except McpBridgeError as exc:
            self._send_error(handler, 502, "mcp_error", str(exc))
        except OSError as exc:
            self._send_error(handler, 500, "io_error", str(exc))

    # -- handlers --------------------------------------------------------

    def _serve_capabilities(self, handler: BaseHTTPRequestHandler) -> None:
        # Same-origin browser GET requests commonly omit ``Origin``.  The
        # local index already receives this launch's random token through the
        # private handler, so accept either proof: a matching Origin (used by
        # diagnostics/first contact) or the injected token (used by the SPA).
        origin_ok = _origin_allowed(
            handler.headers.get("Origin", ""), self._host, self._port
        )
        token_ok = _bearer_or_x_token(handler) == self._token
        if not (origin_ok or token_ok):
            self._send_error(
                handler, 403, "origin_rejected",
                "Origin or local runtime token is required for capabilities.",
            )
            return
        catalog = self._session.catalog()
        payload = {
            "version": "0.1.0",
            "library": str(self._session.library),
            "has_active_book": self._session.open,
            "active_directory": (
                self._session.client.root.name
                if self._session.open and self._session.client is not None
                else None
            ),
            "public_origin": self.public_origin,
            "token": self._token,
            "mcp_methods": sorted(self._mcp_whitelist),
            "catalog": [
                {
                    "title": entry.title,
                    "directory": entry.directory,
                    "stage": entry.stage,
                    "updated_at": entry.updated_at,
                    "chapter_count": entry.chapter_count,
                }
                for entry in catalog
            ],
        }
        self._send_json(handler, 200, payload)

    def _serve_library(self, handler: BaseHTTPRequestHandler) -> None:
        catalog = self._session.catalog()
        self._send_json(handler, 200, {
            "library": str(self._session.library),
            "books": [
                {
                    "title": entry.title,
                    "directory": entry.directory,
                    "stage": entry.stage,
                    "updated_at": entry.updated_at,
                    "chapter_count": entry.chapter_count,
                }
                for entry in catalog
            ],
        })

    @staticmethod
    def _trash_json(entry) -> dict:
        return {
            "trash_id": entry.trash_id,
            "original_directory": entry.original_directory,
            "title": entry.title,
            "trashed_at": entry.trashed_at,
            "valid": entry.valid,
            "error": entry.error,
        }

    def _serve_trash(self, handler: BaseHTTPRequestHandler) -> None:
        self._send_json(handler, 200, {
            "library": str(self._session.library),
            "trash": [self._trash_json(entry) for entry in self._session.trash()],
        })

    def _serve_trash_book(self, handler: BaseHTTPRequestHandler) -> None:
        body = self._read_json(handler)
        directory = body.get("directory")
        if not isinstance(directory, str) or not directory:
            self._send_error(handler, 400, "bad_request", "directory is required.")
            return
        self._send_json(handler, 200, self._session.trash_book(directory))

    def _serve_restore_book(self, handler: BaseHTTPRequestHandler) -> None:
        body = self._read_json(handler)
        trash_id = body.get("trash_id")
        if not isinstance(trash_id, str) or not trash_id:
            self._send_error(handler, 400, "bad_request", "trash_id is required.")
            return
        self._send_json(handler, 200, self._session.restore_book(trash_id))

    def _serve_set_library(self, handler: BaseHTTPRequestHandler) -> None:
        """Switch the active library to an absolute path provided by the SPA.

        Rejects non-absolute, empty, or non-directory paths. The active
        MCP child (if any) is left untouched — the caller must follow up
        with an ``open`` or ``create`` request to rebind MCP.
        """
        body = self._read_json(handler)
        path = body.get("path")
        if not isinstance(path, str) or not path.strip():
            self._send_error(
                handler, 400, "bad_request",
                "path is required and must be a non-empty string.",
            )
            return
        target = Path(path)
        if not target.is_absolute():
            self._send_error(
                handler, 400, "bad_request",
                "path must be an absolute directory.",
            )
            return
        if not target.is_dir():
            self._send_error(
                handler, 422, "unwritable_library",
                f"library directory does not exist: {target}",
            )
            return
        catalog = self._session.set_library(target)
        self._send_json(handler, 200, {
            "library": str(self._session.library),
            "books": [
                {
                    "title": entry.title,
                    "directory": entry.directory,
                    "stage": entry.stage,
                    "updated_at": entry.updated_at,
                    "chapter_count": entry.chapter_count,
                }
                for entry in catalog
            ],
        })

    def _serve_select_directory(self, handler: BaseHTTPRequestHandler) -> None:
        """Open the native Windows folder picker and switch library if chosen.

        Returns ``{"selected": true, ...}`` on success, ``{"selected": false}``
        when the user cancels, and HTTP 501 on non-Windows callers. The
        picker subprocess is injected for testability; the default
        implementation never receives user-controlled text.
        """
        try:
            picked = self._session.pick_library()
        except Exception as exc:
            self._send_error(
                handler, 500, "picker_failed", str(exc),
            )
            return
        if picked is None:
            # Either the platform doesn't support it, or the user
            # cancelled; the SPA renders this as a no-op state.
            self._send_json(handler, 200, {"selected": False})
            return
        try:
            catalog = self._session.set_library(picked)
        except ValueError as exc:
            self._send_error(handler, 422, "unwritable_library", str(exc))
            return
        self._send_json(handler, 200, {
            "selected": True,
            "library": str(self._session.library),
            "books": [
                {
                    "title": entry.title,
                    "directory": entry.directory,
                    "stage": entry.stage,
                    "updated_at": entry.updated_at,
                    "chapter_count": entry.chapter_count,
                }
                for entry in catalog
            ],
        })

    def _serve_tree(self, handler: BaseHTTPRequestHandler) -> None:
        self._send_json(handler, 200, self._session.tree_snapshot())

    def _serve_active(self, handler: BaseHTTPRequestHandler) -> None:
        if not self._session.open or self._session.client is None:
            self._send_json(handler, 200, {
                "active": None,
                "tree": self._session.tree_snapshot(),
            })
            return
        self._send_json(handler, 200, {
            "active": {
                "directory": self._session.client.root.name,
                "path": str(self._session.client.root),
            },
            "tree": self._session.tree_snapshot(),
        })

    def _serve_open(self, handler: BaseHTTPRequestHandler) -> None:
        body = self._read_json(handler)
        directory = body.get("directory")
        if not isinstance(directory, str) or not directory:
            self._send_error(
                handler, 400, "bad_request", "directory is required."
            )
            return
        result = self._session.open_book(directory)
        self._send_json(handler, 200, result)

    def _serve_create(self, handler: BaseHTTPRequestHandler) -> None:
        body = self._read_json(handler)
        title = body.get("title")
        decision = body.get("decision")
        if not isinstance(title, str) or not title.strip():
            self._send_error(
                handler, 400, "bad_request", "title is required."
            )
            return
        if decision is not None and not isinstance(decision, str):
            self._send_error(
                handler, 400, "bad_request", "decision must be a string."
            )
            return
        result = self._session.create_book(title, decision)
        # ProjectEntry objects aren't JSON-serializable; convert the
        # collision matches into a plain dict shape before sending.
        if result.get("status") == "collision":
            result["matches"] = [
                {
                    "title": m.title,
                    "directory": m.directory,
                    "stage": m.stage,
                    "updated_at": m.updated_at,
                    "chapter_count": m.chapter_count,
                }
                for m in result.get("matches", [])
            ]
        # A 200 + collision payload lets the UI prompt without an error.
        self._send_json(handler, 200, result)

    def _serve_mcp(self, handler: BaseHTTPRequestHandler) -> None:
        body = self._read_json(handler)
        method = body.get("method")
        params = body.get("params")
        if not isinstance(method, str) or not method:
            self._send_error(
                handler, 400, "bad_request", "method is required."
            )
            return
        if method not in self._mcp_whitelist:
            self._send_error(
                handler, 403, "method_forbidden",
                f"MCP method not allowed: {method}",
            )
            return
        if params is not None and not isinstance(params, dict):
            self._send_error(
                handler, 400, "bad_request", "params must be an object."
            )
            return
        result = self._session.mcp(method, params)
        self._send_json(handler, 200, result)

    # -- creative storage -----------------------------------------------

    def _creative_store(self) -> CreativeStore:
        root = self._session.active_root
        if root is None:
            raise NoActiveBookError("A book must be open for creative storage.")
        return self._creative_store_factory(root)

    def _serve_creative_session(self, handler: BaseHTTPRequestHandler) -> None:
        store = self._creative_store()
        self._send_json(handler, 200, store.read_session())

    def _serve_creative_turn(self, handler: BaseHTTPRequestHandler) -> None:
        body = self._read_json(handler)
        turn = body.get("turn")
        if not isinstance(turn, dict):
            self._send_error(handler, 400, "bad_request", "turn is required.")
            return
        store = self._creative_store()
        result = store.append_turn(turn)
        self._send_json(handler, 200, result)

    def _serve_creative_state(self, handler: BaseHTTPRequestHandler) -> None:
        body = self._read_json(handler)
        summary = body.get("summary", "")
        facts = body.get("facts", {})
        if not isinstance(summary, str):
            self._send_error(handler, 400, "bad_request", "summary must be a string.")
            return
        if not isinstance(facts, dict):
            self._send_error(handler, 400, "bad_request", "facts must be an object.")
            return
        store = self._creative_store()
        store.write_state(summary, facts)
        self._send_json(handler, 200, {"ok": True})

    def _serve_creative_conversation_state(self, handler: BaseHTTPRequestHandler) -> None:
        body = self._read_json(handler)
        state = body.get("conversation_state")
        if not isinstance(state, dict):
            self._send_error(handler, 400, "bad_request", "conversation_state is required.")
            return
        store = self._creative_store()
        store.write_conversation_state(state)
        self._send_json(handler, 200, {"ok": True})

    def _serve_creative_proposal(self, handler: BaseHTTPRequestHandler) -> None:
        body = self._read_json(handler)
        proposal = body.get("proposal")
        if not isinstance(proposal, dict):
            self._send_error(handler, 400, "bad_request", "proposal is required.")
            return
        store = self._creative_store()
        result = store.write_proposal(proposal)
        self._send_json(handler, 200, result)

    def _serve_creative_draft(self, handler: BaseHTTPRequestHandler) -> None:
        body = self._read_json(handler)
        draft = body.get("draft")
        if not isinstance(draft, dict):
            self._send_error(handler, 400, "bad_request", "draft is required.")
            return
        store = self._creative_store()
        result = store.write_draft(draft)
        self._send_json(handler, 200, result)

    def _serve_creative_export(self, handler: BaseHTTPRequestHandler) -> None:
        store = self._creative_store()
        payload = store.export_zip()
        self._send_bytes(
            handler, 200, payload,
            content_type="application/zip",
            filename="creative-backup.zip",
        )

    def _serve_creative_import(self, handler: BaseHTTPRequestHandler) -> None:
        body = self._read_json(handler)
        archive_b64 = body.get("archive_base64")
        decision = body.get("decision")
        if not isinstance(archive_b64, str) or not archive_b64:
            self._send_error(handler, 400, "bad_request", "archive_base64 is required.")
            return
        if not isinstance(decision, str):
            self._send_error(handler, 400, "bad_request", "decision is required.")
            return
        # Cap at 12 MiB before base64 decode.
        if len(archive_b64) > 16 * 1024 * 1024:
            self._send_error(handler, 413, "payload_too_large", "Archive is too large.")
            return
        payload = base64.b64decode(archive_b64)
        store = self._creative_store()
        result = store.import_zip(payload, decision)
        self._send_json(handler, 200, result)

    # -- helpers ---------------------------------------------------------

    def _read_json(self, handler: BaseHTTPRequestHandler) -> dict:
        length = int(handler.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        if length > 256 * 1024:
            raise ValueError(f"request body too large: {length}")
        raw = handler.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid JSON body: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object.")
        return payload

    def _send_json(
        self, handler: BaseHTTPRequestHandler, status: int, payload: dict
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        handler.wfile.write(body)

    def _send_error(
        self,
        handler: BaseHTTPRequestHandler,
        status: int,
        code: str,
        message: str,
    ) -> None:
        self._send_json(handler, status, {
            "error": {"code": code, "message": message},
        })

    def _send_bytes(
        self,
        handler: BaseHTTPRequestHandler,
        status: int,
        payload: bytes,
        content_type: str,
        filename: str,
    ) -> None:
        handler.send_response(status)
        handler.send_header("Content-Type", content_type)
        handler.send_header("Content-Length", str(len(payload)))
        handler.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        handler.wfile.write(payload)


def make_local_api_handler(
    api: LocalApi, web_root: Path
) -> Callable[..., BaseHTTPRequestHandler]:
    """Build a :class:`BaseHTTPRequestHandler` subclass bound to ``api``.

    Requests under ``/api/local/*`` are routed to ``api.handle``;
    everything else falls through to the standard static-file serving
    rooted at ``web_root``. This is the factory the launcher uses to
    build the private port's HTTP server.
    """

    cache_nonce = secrets.token_urlsafe(8)

    def local_index_body() -> bytes:
        index = (web_root / "index.html").read_text(encoding="utf-8")
        for asset in (
            "sources.js", "tape.js", "ansi.js", "explorer.js", "guide.js",
            "local.js", "conversation-router.js", "zip.js", "creative.js",
            "creative-coverage.js", "creative-chat.js", "floating-chat.js",
            "app.js", "llm.js", "chat.js",
        ):
            index = index.replace(
                f'src="{asset}"', f'src="{asset}?runtime={cache_nonce}"'
            )
        marker = '<script src="local.js"></script>'
        versioned_marker = f'<script src="local.js?runtime={cache_nonce}"></script>'
        runtime = json.dumps(
            {"apiBase": "/api/local", "token": api.token},
            ensure_ascii=True,
            separators=(",", ":"),
        )
        injected = (
            f"<script>window.NWL_RUNTIME={runtime};</script>\n{versioned_marker}"
        )
        if versioned_marker in index:
            index = index.replace(versioned_marker, injected, 1)
        elif marker in index:
            index = index.replace(marker, injected, 1)
        else:
            index = f"<script>window.NWL_RUNTIME={runtime};</script>\n{index}"
        return index.encode("utf-8")

    class _LocalApiHandler(QuietStaticHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def end_headers(self) -> None:  # type: ignore[override]
            if not self.path.startswith(LOCAL_API_PREFIX):
                self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def _serve_local_index(self, *, include_body: bool) -> None:
            body = local_index_body()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
            self.end_headers()
            if include_body:
                self.wfile.write(body)

        def do_GET(self) -> None:  # type: ignore[override]
            if self.path.startswith(LOCAL_API_PREFIX):
                try:
                    api.handle(self, "GET")
                except Exception as exc:  # pragma: no cover - safety net
                    api._send_error(self, 500, "internal_error", str(exc))
                return
            if self.path.split("?", 1)[0] in ("/", "/index.html"):
                self._serve_local_index(include_body=True)
                return
            super().do_GET()

        def do_POST(self) -> None:  # type: ignore[override]
            if self.path.startswith(LOCAL_API_PREFIX):
                try:
                    api.handle(self, "POST")
                except Exception as exc:  # pragma: no cover - safety net
                    api._send_error(self, 500, "internal_error", str(exc))
                return
            self.send_error(405, "Method Not Allowed")

        def do_HEAD(self) -> None:  # type: ignore[override]
            if self.path.startswith(LOCAL_API_PREFIX):
                self.send_error(405, "Method Not Allowed")
                return
            if self.path.split("?", 1)[0] in ("/", "/index.html"):
                self._serve_local_index(include_body=False)
                return
            super().do_HEAD()

    return functools.partial(_LocalApiHandler, directory=str(web_root))


# Late import to avoid a hard dependency for callers that only want the
# launcher / tunnel half of this module.
from scripts.local_mcp_bridge import (  # noqa: E402  (intentional late import)
    LibrarySession,
    McpBridgeError,
)
from scripts.creative_store import (  # noqa: E402
    CreativeStore,
    CreativeStoreError,
)


def _default_creative_store(book_root):
    return CreativeStore(book_root)


JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class WindowsJob:
    def __init__(self, process: subprocess.Popen[str]):
        self._handle: int | None = None
        if os.name != "nt":
            return
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel32.AssignProcessToJobObject.argtypes = [
            wintypes.HANDLE,
            wintypes.HANDLE,
        ]
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise LauncherError("Cannot create the Windows cleanup job object.")
        info = _ExtendedLimitInformation()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            handle,
            JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
            ctypes.byref(info),
            ctypes.sizeof(info),
        ):
            kernel32.CloseHandle(handle)
            raise LauncherError("Cannot configure the Windows cleanup job object.")
        if not kernel32.AssignProcessToJobObject(
            handle,
            wintypes.HANDLE(process._handle),
        ):
            kernel32.CloseHandle(handle)
            raise LauncherError("Cannot add cloudflared to the Windows cleanup job.")
        self._handle = int(handle)

    def close(self) -> None:
        if self._handle is None or os.name != "nt":
            return
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle(wintypes.HANDLE(self._handle))
        self._handle = None


@dataclass
class ManagedProcess:
    process: subprocess.Popen[str]
    lines: queue.Queue[str]
    recent: deque[str] = field(default_factory=lambda: deque(maxlen=20))
    job: WindowsJob | None = None
    _closed: bool = False

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        if self.process.stdout is not None:
            self.process.stdout.close()
        if self.job is not None:
            self.job.close()


def _pump_output(stream: object, lines: queue.Queue[str]) -> None:
    if stream is None:
        return
    for raw in stream:
        lines.put(str(raw).rstrip("\r\n"))


def start_output_process(
    command: Sequence[str],
    *,
    assign_windows_job: bool = True,
) -> ManagedProcess:
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=creationflags,
    )
    lines: queue.Queue[str] = queue.Queue()
    threading.Thread(
        target=_pump_output,
        args=(process.stdout, lines),
        name="cloudflared-output",
        daemon=True,
    ).start()
    managed = ManagedProcess(process=process, lines=lines)
    try:
        if assign_windows_job:
            managed.job = WindowsJob(process)
    except Exception:
        managed.close()
        raise
    return managed


def start_tunnel(executable: Path, local_url: str) -> ManagedProcess:
    return start_output_process(
        [
            str(executable),
            "tunnel",
            "--url",
            local_url,
            "--no-autoupdate",
        ]
    )


def wait_for_tunnel_url(
    tunnel: ManagedProcess,
    *,
    timeout: float,
    on_line: Callable[[str], None] | None = None,
    stop_event: threading.Event | None = None,
) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if stop_event is not None and stop_event.is_set():
            raise LauncherStopped
        try:
            remaining = max(0.01, deadline - time.monotonic())
            line = tunnel.lines.get(timeout=min(0.2, remaining))
        except queue.Empty:
            line = ""
        if line:
            tunnel.recent.append(line)
            if on_line is not None:
                on_line(line)
            found = parse_quick_tunnel_url(line)
            if found:
                return found
        if tunnel.process.poll() is not None and tunnel.lines.empty():
            detail = " | ".join(tunnel.recent) or "no output"
            raise LauncherError(
                "cloudflared exited early before creating a public URL "
                f"(code={tunnel.process.returncode}): {detail}"
            )
    raise LauncherError("Timed out waiting for a Cloudflare public URL.")


@dataclass
class LauncherResources:
    """All long-lived resources owned by a single :class:`Launcher` run.

    The launcher starts up to three things in parallel:

    * a private static+API server on the configured local port,
    * a public static-only server on the configured public port (the
      one the cloudflared tunnel actually proxies to), and
    * the cloudflared tunnel itself.

    On :meth:`close` every resource is shut down in reverse order. The
    :class:`LibrarySession` is closed last so any in-flight MCP request
    on the way out gets a clean error instead of a half-torn pipe.
    """

    server: ThreadingHTTPServer | None = None
    server_thread: threading.Thread | None = None
    public_server: ThreadingHTTPServer | None = None
    public_server_thread: threading.Thread | None = None
    tunnel: ManagedProcess | None = None
    library_session: Optional["LibrarySession"] = None
    local_api: Optional["LocalApi"] = None
    _closed: bool = False

    @property
    def open(self) -> bool:
        return (
            not self._closed
            and (
                self.server is not None
                or self.public_server is not None
                or self.tunnel is not None
            )
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self.tunnel is not None:
            self.tunnel.close()
        for srv, thr in (
            (self.public_server, self.public_server_thread),
            (self.server, self.server_thread),
        ):
            if srv is not None:
                try:
                    srv.shutdown()
                except Exception:
                    pass
                try:
                    srv.server_close()
                except Exception:
                    pass
            if thr is not None:
                thr.join(timeout=2)
        if self.library_session is not None:
            try:
                self.library_session.close()
            except Exception:
                pass
            self.library_session = None


class Launcher:
    def __init__(
        self,
        config: LauncherConfig,
        *,
        root: Path | None = None,
        cloudflared: Path | None = None,
        tunnel_factory: Callable[[Path, str], ManagedProcess] = start_tunnel,
        local_probe: HttpProbe = probe_http,
        public_probe: HttpProbe = probe_http,
        browser_open: Callable[[str], bool] = webbrowser.open,
        stop_event: threading.Event | None = None,
        local_timeout: float = 10,
        tunnel_timeout: float = 30,
        public_timeout: float = 60,
        library_session: Optional["LibrarySession"] = None,
        library_session_factory: Optional[Callable[[Path], "LibrarySession"]] = None,
    ):
        self.config = config
        self.root = root or repository_root()
        self.cloudflared = cloudflared
        self.tunnel_factory = tunnel_factory
        self.local_probe = local_probe
        self.public_probe = public_probe
        self.browser_open = browser_open
        self.stop_event = stop_event or threading.Event()
        self.local_timeout = local_timeout
        self.tunnel_timeout = tunnel_timeout
        self.public_timeout = public_timeout
        self._library_session_factory = library_session_factory
        # Accept an explicit session (used by tests) or build one on the
        # first ``run()`` from the configured ``library_root``. Building
        # lazily keeps the import order: tests can inject a session
        # without a real library directory on disk.
        self._library_session = library_session
        self.resources = LauncherResources()

    @property
    def resources_open(self) -> bool:
        return self.resources.open

    def _print_ready(
        self,
        local_url: str,
        public_url: str,
        *,
        tunnel_enabled: bool = True,
    ) -> None:
        if tunnel_enabled:
            print("\n[就绪] 网页端与临时穿透均已启动")
            print(f"[本地] {local_url}")
            print(f"[穿透] {public_url}")
            print("[警告] 任何获得公网链接的人都可以访问此页面。")
        else:
            print("\n[就绪] 本地网页端已启动")
            print(f"[本地] {local_url}")
            print(f"[公开本机] {public_url}")
            print("[说明] 未启动内置穿透；现有 ngrok 等进程不受影响。")
        print("[退出] 按 Ctrl+C 或关闭此窗口即可停止全部服务。\n")

    def _open_local_browser(self, local_url: str) -> None:
        if not self.config.open_browser:
            return
        try:
            if not self.browser_open(local_url):
                print(f"[警告] 浏览器未自动打开，请手动访问 {local_url}")
        except Exception as exc:
            print(f"[警告] 浏览器打开失败: {exc}; 请手动访问 {local_url}")

    def _ensure_library_session(self) -> "LibrarySession":
        if self.resources.library_session is not None:
            return self.resources.library_session
        if self._library_session is not None:
            self.resources.library_session = self._library_session
            return self._library_session
        root = self.config.library_root
        if root is None:
            root = self.root / "book"
        if self._library_session_factory is None:
            session = LibrarySession(root)
        else:
            session = self._library_session_factory(root)
        self.resources.library_session = session
        return session

    def run(self) -> int:
        web_root = validate_web_root(self.root)
        executable = None
        if self.config.enable_tunnel:
            executable = self.cloudflared or find_cloudflared()
        if self.config.port:
            ensure_port_available(HOST, self.config.port)
        if self.config.public_port:
            ensure_port_available(HOST, self.config.public_port)
        try:
            print("[检查] 启动本地网页与 Cloudflare 临时穿透…")
            session = self._ensure_library_session()
            api = LocalApi(session, host=HOST, port=self.config.port)
            self.resources.local_api = api
            local_factory = make_local_api_handler(api, web_root)
            local_server, local_thread = start_http_server(
                web_root,
                HOST,
                self.config.port,
                handler_factory=local_factory,
                server_name="novel-workflow-local",
            )
            self.resources.server = local_server
            self.resources.server_thread = local_thread
            actual_port = int(local_server.server_address[1])
            api.port = actual_port  # reconcile with OS-assigned port
            local_health_url = f"http://{HOST}:{actual_port}/"
            run_id = secrets.token_urlsafe(6)
            local_browser_url = f"http://localhost:{actual_port}/?run={run_id}"
            wait_until_ready(
                local_health_url,
                timeout=self.local_timeout,
                probe=self.local_probe,
                marker="novel-workflow",
                stop_event=self.stop_event,
            )
            print(f"[本地] 已就绪: {local_browser_url}")
            self._open_local_browser(local_browser_url)

            public_server, public_thread = start_http_server(
                web_root,
                HOST,
                self.config.public_port,
                server_name="novel-workflow-public",
            )
            self.resources.public_server = public_server
            self.resources.public_server_thread = public_thread
            actual_public_port = int(public_server.server_address[1])
            public_health_url = (
                f"http://{HOST}:{actual_public_port}/"
            )
            wait_until_ready(
                public_health_url,
                timeout=self.local_timeout,
                probe=self.local_probe,
                marker="novel-workflow",
                stop_event=self.stop_event,
            )
            print(f"[公开] 已就绪: {public_health_url}")

            if not self.config.enable_tunnel:
                print(
                    f"[本地] 已按 --no-tunnel 跳过 cloudflared; "
                    f"不会影响其他穿透进程。"
                )
                self._print_ready(
                    local_browser_url,
                    public_health_url,
                    tunnel_enabled=False,
                )
                self.stop_event.wait()
                return 0

            assert executable is not None
            self.resources.tunnel = self.tunnel_factory(
                executable,
                public_health_url,
            )
            if self.resources.tunnel is None:
                # Headless / acceptance mode: run local servers only, no
                # public URL. The two ports are still real and routable.
                print(
                    f"[本地] 公共穿透未启用 (tunnel_factory=None); "
                    f"对外仅暴露本地端 {local_browser_url}"
                )
                self._print_ready(local_browser_url, public_health_url)
                self.stop_event.wait()
                return 0
            public_url = wait_for_tunnel_url(
                self.resources.tunnel,
                timeout=self.tunnel_timeout,
                on_line=lambda line: print(f"[穿透] {line}"),
                stop_event=self.stop_event,
            )
            try:
                wait_until_ready(
                    public_url,
                    timeout=self.public_timeout,
                    probe=self.public_probe,
                    stop_event=self.stop_event,
                )
            except LauncherError:
                # A local machine can be unable to resolve or reach its own
                # trycloudflare URL even though cloudflared has registered the
                # tunnel and remote clients can use it. Keep the local app and
                # the live tunnel available; an actual cloudflared exit is
                # still detected by the ownership loop below.
                if self.resources.tunnel.process.poll() is not None:
                    raise
                print(
                    "[警告] 已创建公网地址，但本机无法完成回环验证；"
                    "本地网页与 cloudflared 将继续运行。"
                )
            self._print_ready(local_browser_url, public_url)

            while not self.stop_event.wait(0.25):
                if self.resources.tunnel.process.poll() is not None:
                    raise LauncherError(
                        "cloudflared 已意外退出 "
                        f"(code={self.resources.tunnel.process.returncode})。"
                    )
            return 0
        finally:
            print("[退出] 正在停止本地服务与穿透…")
            self.resources.close()


def main(argv: Sequence[str] | None = None) -> int:
    config = parse_args(argv)
    app = Launcher(config)
    atexit.register(app.resources.close)

    def request_stop(signum: int, frame: object) -> None:
        app.stop_event.set()

    for sig_name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        sig = getattr(signal, sig_name, None)
        if sig is not None:
            signal.signal(sig, request_stop)
    try:
        return app.run()
    except KeyboardInterrupt:
        app.stop_event.set()
        return 0
    except LauncherStopped:
        return 0
    except LauncherError as exc:
        print(f"[失败] {exc}", file=sys.stderr)
        return 1
    finally:
        app.resources.close()


if __name__ == "__main__":
    exit_code = main()
    if exit_code and os.environ.get("BOOKWORKFLOW_PAUSE_ON_ERROR"):
        try:
            input("按回车键关闭此窗口…")
        except (EOFError, KeyboardInterrupt):
            pass
    raise SystemExit(exit_code)
