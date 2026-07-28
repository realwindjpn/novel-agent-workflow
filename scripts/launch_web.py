#!/usr/bin/env python3
"""Start the browser SPA and a disposable Cloudflare Quick Tunnel."""
from __future__ import annotations

import argparse
import ctypes
import functools
import os
import queue
import re
import shutil
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from ctypes import wintypes
from dataclasses import dataclass, field
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
) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
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
