#!/usr/bin/env python3
"""Start the browser SPA and a disposable Cloudflare Quick Tunnel."""
from __future__ import annotations

import argparse
import functools
import re
import shutil
import socket
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Protocol, Sequence


HOST = "127.0.0.1"
DEFAULT_PORT = 8080
QUICK_TUNNEL_RE = re.compile(
    r"https://[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.trycloudflare\.com(?=$|[\s/?#:])",
    re.IGNORECASE,
)


class LauncherError(RuntimeError):
    """A user-actionable launcher failure."""


@dataclass(frozen=True)
class LauncherConfig:
    port: int = DEFAULT_PORT
    open_browser: bool = True


def parse_args(argv: Sequence[str] | None = None) -> LauncherConfig:
    parser = argparse.ArgumentParser(
        description="Start novel-workflow web and a Cloudflare Quick Tunnel."
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    ns = parser.parse_args(argv)
    if not 1 <= ns.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    return LauncherConfig(port=ns.port, open_browser=not ns.no_browser)


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


def start_http_server(
    web_root: Path,
    host: str,
    port: int,
) -> tuple[ThreadingHTTPServer, threading.Thread]:
    handler = functools.partial(QuietStaticHandler, directory=str(web_root))
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    thread = threading.Thread(
        target=server.serve_forever,
        name="novel-workflow-http",
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
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if probe(url, marker):
            return
        time.sleep(interval)
    raise LauncherError(f"Timed out waiting for endpoint: {url}")
