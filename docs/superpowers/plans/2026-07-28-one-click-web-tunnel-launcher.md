# One-click Web and Tunnel Launcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Windows double-click launcher that starts the browser SPA, creates a Cloudflare Quick Tunnel, opens the local page after both endpoints are ready, and cleans up every owned process on exit.

**Architecture:** `一键启动.cmd` selects Python and delegates to a standard-library orchestrator in `scripts/launch_web.py`. The orchestrator owns an in-process `ThreadingHTTPServer`, a monitored cloudflared subprocess, HTTP readiness checks, browser launch, and Windows Job Object cleanup; unit tests inject probes and process factories so they never open a browser or public tunnel.

**Tech Stack:** Python 3.11 standard library (`argparse`, `ctypes`, `http.server`, `queue`, `socket`, `subprocess`, `threading`, `urllib`, `webbrowser`), Windows CMD, `unittest`, cloudflared Quick Tunnels.

---

## File map

- Create `scripts/launch_web.py`: all launcher behavior, split into small testable functions and one `Launcher` coordinator.
- Create `tests/test_web_launcher.py`: unit and local integration coverage with no real browser or public network side effects.
- Create `一键启动.cmd`: Windows double-click entry point with Python selection and failure pause.
- Modify `README.md`: promote the one-click workflow in the Web live runner section.
- Modify `web/README.md`: document startup, exposure, shutdown, options, and manual fallback.

### Task 1: Configuration and prerequisite primitives

**Files:**
- Create: `scripts/launch_web.py`
- Create: `tests/test_web_launcher.py`

- [ ] **Step 1: Write failing tests for arguments, paths, tunnel URL parsing, executable lookup, and occupied ports**

Create `tests/test_web_launcher.py` with:

```python
from __future__ import annotations

import socket
import tempfile
import unittest
from pathlib import Path

from scripts import launch_web


class LauncherPrimitiveTests(unittest.TestCase):
    def test_parse_args_defaults(self):
        config = launch_web.parse_args([])
        self.assertEqual(config.port, 8080)
        self.assertTrue(config.open_browser)

    def test_parse_args_supports_port_and_no_browser(self):
        config = launch_web.parse_args(["--port", "9090", "--no-browser"])
        self.assertEqual(config.port, 9090)
        self.assertFalse(config.open_browser)

    def test_parse_quick_tunnel_url(self):
        line = 'INF Requesting new quick Tunnel url=https://quiet-brook.trycloudflare.com'
        self.assertEqual(
            launch_web.parse_quick_tunnel_url(line),
            "https://quiet-brook.trycloudflare.com",
        )

    def test_parse_quick_tunnel_url_rejects_unrelated_url(self):
        self.assertIsNone(launch_web.parse_quick_tunnel_url("https://example.com"))

    def test_validate_web_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web = root / "web"
            web.mkdir()
            (web / "index.html").write_text("novel-workflow", encoding="utf-8")
            self.assertEqual(launch_web.validate_web_root(root), web.resolve())

    def test_validate_web_root_rejects_missing_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(launch_web.LauncherError, "web/index.html"):
                launch_web.validate_web_root(Path(tmp))

    def test_find_cloudflared_uses_injected_lookup(self):
        found = launch_web.find_cloudflared(lambda name: "C:/tools/cloudflared.exe")
        self.assertEqual(found, Path("C:/tools/cloudflared.exe"))

    def test_find_cloudflared_rejects_missing_executable(self):
        with self.assertRaisesRegex(launch_web.LauncherError, "cloudflared"):
            launch_web.find_cloudflared(lambda name: None)

    def test_ensure_port_available_rejects_bound_port(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
            with self.assertRaisesRegex(launch_web.LauncherError, str(port)):
                launch_web.ensure_port_available("127.0.0.1", port)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the primitive tests and confirm the module is missing**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.LauncherPrimitiveTests -v
```

Expected: import failure because `scripts/launch_web.py` does not exist.

- [ ] **Step 3: Implement the primitive API**

Create `scripts/launch_web.py` with:

```python
#!/usr/bin/env python3
"""Start the browser SPA and a disposable Cloudflare Quick Tunnel."""
from __future__ import annotations

import argparse
import re
import shutil
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


HOST = "127.0.0.1"
DEFAULT_PORT = 8080
QUICK_TUNNEL_RE = re.compile(
    r"https://[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.trycloudflare\.com",
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
        raise LauncherError(f"找不到网页入口: {index} (需要 web/index.html)")
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
            "找不到 cloudflared。请先安装 Cloudflare Tunnel 客户端并加入 PATH。"
        )
    return Path(found)


def ensure_port_available(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError as exc:
            raise LauncherError(
                f"端口 {port} 已被占用；请关闭占用程序或使用 --port。"
            ) from exc
```

- [ ] **Step 4: Run the primitive tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.LauncherPrimitiveTests -v
```

Expected: 9 tests pass.

- [ ] **Step 5: Commit the primitives**

```powershell
git add scripts/launch_web.py tests/test_web_launcher.py
git commit -m "feat: add web launcher primitives"
```

### Task 2: Local HTTP server and readiness checks

**Files:**
- Modify: `scripts/launch_web.py`
- Modify: `tests/test_web_launcher.py`

- [ ] **Step 1: Add failing HTTP server and polling tests**

Add these imports to `tests/test_web_launcher.py`:

```python
import time
import urllib.error
```

Add this test class before the `if __name__ == "__main__"` block:

```python
class HttpServerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.web_root = Path(self._tmp.name)
        (self.web_root / "index.html").write_text(
            "<title>novel-workflow Live Runner</title>", encoding="utf-8"
        )
        self.server, self.thread = launch_web.start_http_server(
            self.web_root, "127.0.0.1", 0
        )
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self._tmp.cleanup()

    def test_probe_http_accepts_expected_marker(self):
        url = f"http://127.0.0.1:{self.port}/"
        self.assertTrue(launch_web.probe_http(url, marker="novel-workflow"))

    def test_probe_http_rejects_missing_marker(self):
        url = f"http://127.0.0.1:{self.port}/"
        self.assertFalse(launch_web.probe_http(url, marker="not-present"))

    def test_wait_until_ready_retries_until_success(self):
        attempts = iter([False, False, True])
        launch_web.wait_until_ready(
            "http://local.test",
            timeout=1,
            probe=lambda url, marker=None: next(attempts),
            interval=0,
        )

    def test_wait_until_ready_times_out(self):
        started = time.monotonic()
        with self.assertRaisesRegex(launch_web.LauncherError, "超时"):
            launch_web.wait_until_ready(
                "http://local.test",
                timeout=0.02,
                probe=lambda url, marker=None: False,
                interval=0.005,
            )
        self.assertLess(time.monotonic() - started, 0.5)
```

- [ ] **Step 2: Run HTTP tests and confirm the new functions are missing**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.HttpServerTests -v
```

Expected: failures for missing `start_http_server`, `probe_http`, and
`wait_until_ready`.

- [ ] **Step 3: Implement the local server and bounded readiness polling**

Add these imports to `scripts/launch_web.py`:

```python
import functools
import threading
import time
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Protocol
```

Append:

```python
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
    raise LauncherError(f"等待地址就绪超时: {url}")
```

- [ ] **Step 4: Run primitive and HTTP tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher -v
```

Expected: 13 tests pass.

- [ ] **Step 5: Commit HTTP serving**

```powershell
git add scripts/launch_web.py tests/test_web_launcher.py
git commit -m "feat: serve web runner with readiness checks"
```

### Task 3: Cloudflared monitoring and Windows process-tree cleanup

**Files:**
- Modify: `scripts/launch_web.py`
- Modify: `tests/test_web_launcher.py`

- [ ] **Step 1: Add failing tunnel output, early-exit, and cleanup tests**

Add these imports to `tests/test_web_launcher.py`:

```python
import subprocess
import sys
```

Add:

```python
class TunnelProcessTests(unittest.TestCase):
    def _python_process(self, code: str):
        return launch_web.start_output_process(
            [sys.executable, "-u", "-c", code], assign_windows_job=False
        )

    def test_wait_for_tunnel_url_reads_process_output(self):
        tunnel = self._python_process(
            "import time; "
            "print('https://unit-test.trycloudflare.com', flush=True); "
            "time.sleep(60)"
        )
        try:
            self.assertEqual(
                launch_web.wait_for_tunnel_url(tunnel, timeout=2),
                "https://unit-test.trycloudflare.com",
            )
        finally:
            tunnel.close()

    def test_wait_for_tunnel_url_reports_early_exit(self):
        tunnel = self._python_process("print('cloudflared failed', flush=True)")
        try:
            with self.assertRaisesRegex(launch_web.LauncherError, "提前退出"):
                launch_web.wait_for_tunnel_url(tunnel, timeout=2)
        finally:
            tunnel.close()

    def test_close_is_idempotent_and_terminates_process(self):
        tunnel = self._python_process("import time; time.sleep(60)")
        tunnel.close()
        tunnel.close()
        self.assertIsNotNone(tunnel.process.poll())
```

- [ ] **Step 2: Run tunnel tests and confirm the process API is missing**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.TunnelProcessTests -v
```

Expected: failures for missing `start_output_process` and
`wait_for_tunnel_url`.

- [ ] **Step 3: Implement Windows Job Object ownership**

Add imports to `scripts/launch_web.py`:

```python
import ctypes
import os
import subprocess
from ctypes import wintypes
```

Append:

```python
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
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        handle = kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise LauncherError("无法创建 Windows 进程清理 Job Object。")
        info = _ExtendedLimitInformation()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            handle,
            JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
            ctypes.byref(info),
            ctypes.sizeof(info),
        ):
            kernel32.CloseHandle(handle)
            raise LauncherError("无法配置 Windows 进程清理 Job Object。")
        if not kernel32.AssignProcessToJobObject(handle, wintypes.HANDLE(process._handle)):
            kernel32.CloseHandle(handle)
            raise LauncherError("无法把 cloudflared 加入 Windows 清理任务。")
        self._handle = int(handle)

    def close(self) -> None:
        if self._handle is None or os.name != "nt":
            return
        ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle(
            wintypes.HANDLE(self._handle)
        )
        self._handle = None
```

- [ ] **Step 4: Implement output pumping, URL waiting, and idempotent cleanup**

Add imports:

```python
import queue
from collections import deque
from dataclasses import field
```

Append:

```python
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
            line = tunnel.lines.get(timeout=min(0.2, max(0.01, deadline - time.monotonic())))
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
            detail = " | ".join(tunnel.recent) or "无输出"
            raise LauncherError(
                f"cloudflared 在生成公网地址前提前退出 "
                f"(code={tunnel.process.returncode}): {detail}"
            )
    raise LauncherError("等待 Cloudflare 临时公网地址超时。")
```

- [ ] **Step 5: Run all launcher tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher -v
```

Expected: 16 tests pass and no Python child process remains.

- [ ] **Step 6: Commit tunnel lifecycle support**

```powershell
git add scripts/launch_web.py tests/test_web_launcher.py
git commit -m "feat: manage cloudflare tunnel lifecycle"
```

### Task 4: Transactional orchestration, browser launch, and supervision

**Files:**
- Modify: `scripts/launch_web.py`
- Modify: `tests/test_web_launcher.py`

- [ ] **Step 1: Add failing orchestration tests with injected dependencies**

Add these imports to `tests/test_web_launcher.py`:

```python
import threading
from unittest import mock
```

Add:

```python
class LauncherOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        web = self.root / "web"
        web.mkdir()
        (web / "index.html").write_text(
            "<title>novel-workflow Live Runner</title>", encoding="utf-8"
        )

    def tearDown(self):
        self._tmp.cleanup()

    def _fake_tunnel(self):
        return launch_web.start_output_process(
            [
                sys.executable,
                "-u",
                "-c",
                "import time; "
                "print('https://orchestration-test.trycloudflare.com', flush=True); "
                "time.sleep(60)",
            ],
            assign_windows_job=False,
        )

    def test_success_waits_for_tunnel_then_opens_local_browser(self):
        stop = threading.Event()
        opened = []

        def open_browser(url):
            opened.append(url)
            stop.set()
            return True

        app = launch_web.Launcher(
            launch_web.LauncherConfig(port=0, open_browser=True),
            root=self.root,
            cloudflared=Path("cloudflared"),
            tunnel_factory=lambda executable, local_url: self._fake_tunnel(),
            public_probe=lambda url, marker=None: True,
            browser_open=open_browser,
            stop_event=stop,
        )
        self.assertEqual(app.run(), 0)
        self.assertEqual(len(opened), 1)
        self.assertTrue(opened[0].startswith("http://localhost:"))
        self.assertFalse(app.resources_open)

    def test_no_browser_suppresses_browser_open(self):
        stop = threading.Event()
        stop.set()
        browser = mock.Mock(return_value=True)
        app = launch_web.Launcher(
            launch_web.LauncherConfig(port=0, open_browser=False),
            root=self.root,
            cloudflared=Path("cloudflared"),
            tunnel_factory=lambda executable, local_url: self._fake_tunnel(),
            public_probe=lambda url, marker=None: True,
            browser_open=browser,
            stop_event=stop,
        )
        self.assertEqual(app.run(), 0)
        browser.assert_not_called()

    def test_browser_failure_is_non_fatal(self):
        stop = threading.Event()
        stop.set()
        app = launch_web.Launcher(
            launch_web.LauncherConfig(port=0, open_browser=True),
            root=self.root,
            cloudflared=Path("cloudflared"),
            tunnel_factory=lambda executable, local_url: self._fake_tunnel(),
            public_probe=lambda url, marker=None: True,
            browser_open=lambda url: False,
            stop_event=stop,
        )
        self.assertEqual(app.run(), 0)

    def test_browser_exception_is_non_fatal(self):
        stop = threading.Event()
        stop.set()

        def fail_browser(url):
            raise OSError("browser unavailable")

        app = launch_web.Launcher(
            launch_web.LauncherConfig(port=0, open_browser=True),
            root=self.root,
            cloudflared=Path("cloudflared"),
            tunnel_factory=lambda executable, local_url: self._fake_tunnel(),
            public_probe=lambda url, marker=None: True,
            browser_open=fail_browser,
            stop_event=stop,
        )
        self.assertEqual(app.run(), 0)

    def test_local_readiness_failure_never_starts_tunnel_and_cleans_up(self):
        tunnel_factory = mock.Mock()
        app = launch_web.Launcher(
            launch_web.LauncherConfig(port=0, open_browser=False),
            root=self.root,
            cloudflared=Path("cloudflared"),
            tunnel_factory=tunnel_factory,
            local_probe=lambda url, marker=None: False,
            local_timeout=0.02,
        )
        with self.assertRaisesRegex(launch_web.LauncherError, "超时"):
            app.run()
        tunnel_factory.assert_not_called()
        self.assertFalse(app.resources_open)

    def test_public_readiness_failure_cleans_up_everything(self):
        app = launch_web.Launcher(
            launch_web.LauncherConfig(port=0, open_browser=False),
            root=self.root,
            cloudflared=Path("cloudflared"),
            tunnel_factory=lambda executable, local_url: self._fake_tunnel(),
            public_probe=lambda url, marker=None: False,
            public_timeout=0.02,
        )
        with self.assertRaisesRegex(launch_web.LauncherError, "超时"):
            app.run()
        self.assertFalse(app.resources_open)
```

- [ ] **Step 2: Run orchestration tests and confirm `Launcher` is missing**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.LauncherOrchestrationTests -v
```

Expected: failures because `Launcher` does not exist.

- [ ] **Step 3: Implement idempotent launcher resource ownership**

Add imports to `scripts/launch_web.py`:

```python
import atexit
import signal
import sys
import webbrowser
```

Append before `Launcher`:

```python
@dataclass
class LauncherResources:
    server: ThreadingHTTPServer | None = None
    server_thread: threading.Thread | None = None
    tunnel: ManagedProcess | None = None
    _closed: bool = False

    @property
    def open(self) -> bool:
        return not self._closed and (self.server is not None or self.tunnel is not None)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self.tunnel is not None:
            self.tunnel.close()
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.server_thread is not None:
            self.server_thread.join(timeout=2)
```

- [ ] **Step 4: Implement transactional startup and supervision**

Append:

```python
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
        public_timeout: float = 30,
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
        self.resources = LauncherResources()

    @property
    def resources_open(self) -> bool:
        return self.resources.open

    def _print_ready(self, local_url: str, public_url: str) -> None:
        print("\n[就绪] 网页端与临时穿透均已启动")
        print(f"[本地] {local_url}")
        print(f"[穿透] {public_url}")
        print("[警告] 任何获得公网链接的人都可以访问此页面。")
        print("[退出] 按 Ctrl+C 或关闭此窗口即可停止全部服务。\n")

    def run(self) -> int:
        web_root = validate_web_root(self.root)
        executable = self.cloudflared or find_cloudflared()
        if self.config.port:
            ensure_port_available(HOST, self.config.port)
        try:
            print("[检查] 启动本地网页与 Cloudflare 临时穿透…")
            server, server_thread = start_http_server(web_root, HOST, self.config.port)
            self.resources.server = server
            self.resources.server_thread = server_thread
            actual_port = int(server.server_address[1])
            local_health_url = f"http://{HOST}:{actual_port}/"
            local_browser_url = f"http://localhost:{actual_port}/"
            wait_until_ready(
                local_health_url,
                timeout=self.local_timeout,
                probe=self.local_probe,
                marker="novel-workflow",
            )
            print(f"[本地] 已就绪: {local_browser_url}")

            self.resources.tunnel = self.tunnel_factory(executable, local_health_url)
            public_url = wait_for_tunnel_url(
                self.resources.tunnel,
                timeout=self.tunnel_timeout,
                on_line=lambda line: print(f"[穿透] {line}"),
            )
            wait_until_ready(
                public_url,
                timeout=self.public_timeout,
                probe=self.public_probe,
            )
            self._print_ready(local_browser_url, public_url)

            if self.config.open_browser:
                try:
                    if not self.browser_open(local_browser_url):
                        print(f"[警告] 浏览器未自动打开，请手动访问 {local_browser_url}")
                except Exception as exc:
                    print(f"[警告] 浏览器打开失败: {exc}; 请手动访问 {local_browser_url}")

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
```

- [ ] **Step 5: Implement the CLI main function and signal path**

Append:

```python
def main(argv: Sequence[str] | None = None) -> int:
    config = parse_args(argv)
    app = Launcher(config)
    atexit.register(app.resources.close)

    def request_stop(signum: int, frame: object) -> None:
        app.stop_event.set()

    for sig_name in ("SIGTERM", "SIGBREAK"):
        sig = getattr(signal, sig_name, None)
        if sig is not None:
            signal.signal(sig, request_stop)
    try:
        return app.run()
    except KeyboardInterrupt:
        app.stop_event.set()
        return 0
    except LauncherError as exc:
        print(f"[失败] {exc}", file=sys.stderr)
        return 1
    finally:
        app.resources.close()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Run all launcher tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher -v
```

Expected: 22 tests pass, no browser opens, no public tunnel is created, and
no child Python process remains.

- [ ] **Step 7: Commit orchestration**

```powershell
git add scripts/launch_web.py tests/test_web_launcher.py
git commit -m "feat: orchestrate web and tunnel startup"
```

### Task 5: Windows double-click entry point

**Files:**
- Create: `一键启动.cmd`

- [ ] **Step 1: Create the CMD wrapper**

Create `一键启动.cmd` with exactly:

```bat
@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto run_venv
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 goto run_py
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 goto run_python

echo [失败] 找不到 Python 3.11。请先安装 Python，或在项目中创建 .venv。
set "EXIT_CODE=1"
goto finish

:run_venv
".venv\Scripts\python.exe" "scripts\launch_web.py" %*
set "EXIT_CODE=%ERRORLEVEL%"
goto finish

:run_py
py -3.11 "scripts\launch_web.py" %*
set "EXIT_CODE=%ERRORLEVEL%"
goto finish

:run_python
python "scripts\launch_web.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

:finish
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%
```

- [ ] **Step 2: Verify argument forwarding without starting a tunnel**

Run:

```powershell
cmd /c "一键启动.cmd --help"
```

Expected: launcher help lists `--port` and `--no-browser`, then exits 0 without
pausing.

- [ ] **Step 3: Commit the Windows entry point**

```powershell
git add -- "一键启动.cmd"
git commit -m "feat: add one-click Windows launcher"
```

### Task 6: User documentation

**Files:**
- Modify: `README.md` in `## Web live runner (browser SPA)`
- Modify: `web/README.md` in `## Local preview`

- [ ] **Step 1: Replace the root README local preview paragraph with one-click instructions**

In `README.md`, replace the existing `Local preview (any static server works)`
block with:

```markdown
### Windows one-click start (local + temporary public URL)

With Python 3.11+ and [`cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) installed, double-click:

```text
一键启动.cmd
```

The launcher starts the SPA on `http://localhost:8080`, creates a random
`https://….trycloudflare.com` Quick Tunnel, waits for both endpoints, and then
opens the local page automatically. The public URL is temporary and has no
login protection: anyone with the link can access the page while the launcher
is running. Press Ctrl+C or close the launcher window to stop both services.

Optional command-line use:

```powershell
.\一键启动.cmd --port 9090
.\一键启动.cmd --no-browser
```

Manual local-only fallback (any static server works):

```bash
cd web
python3 -m http.server 8080
# open http://localhost:8080
```
```

- [ ] **Step 2: Replace `web/README.md` local preview section with the detailed workflow**

Replace the content under `## Local preview` through the Replay-mode paragraph
with:

```markdown
## One-click local + Quick Tunnel start (Windows)

From the repository root, double-click `一键启动.cmd`. The launcher:

1. serves this directory on `127.0.0.1:8080`;
2. starts `cloudflared` with a zero-login Quick Tunnel;
3. verifies both the local and temporary public endpoints;
4. opens `http://localhost:8080` in the default browser;
5. prints the random `https://….trycloudflare.com` URL;
6. stops the HTTP server and tunnel when Ctrl+C is pressed or the window closes.

Prerequisites are Python 3.11+ and `cloudflared` on PATH. The temporary public
URL is unauthenticated: anyone with the URL can access the runner until the
launcher stops. The URL changes on every run.

```powershell
.\一键启动.cmd --port 9090
.\一键启动.cmd --no-browser
```

For a local-only manual preview, any static HTTP server still works:

```bash
cd web
python3 -m http.server 8080
# open http://localhost:8080
```

Pyodide fetches Python and packages from jsDelivr on first load (~10s).
Subsequent loads are cached. If the WASM engine takes more than ~150s to
respond, the page falls back to Replay mode automatically so you can still
explore the 22-step flow.
```

- [ ] **Step 3: Run the deny-list scanner and launcher tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher -v
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); from novel_workflow._security import deny_list_findings; from pathlib import Path; files=['README.md','web/README.md','scripts/launch_web.py']; findings=[x for f in files for x in deny_list_findings(f, Path(f).read_text(encoding='utf-8'))]; print(findings); raise SystemExit(bool(findings))"
```

Expected: launcher tests pass and the scanner prints `[]`.

- [ ] **Step 4: Commit documentation**

```powershell
git add README.md web/README.md
git commit -m "docs: explain one-click web tunnel startup"
```

### Task 7: Full validation and real Windows smoke test

**Files:**
- Verify: `scripts/launch_web.py`
- Verify: `tests/test_web_launcher.py`
- Verify: `一键启动.cmd`
- Verify: `README.md`
- Verify: `web/README.md`

- [ ] **Step 1: Run syntax and launcher tests**

```powershell
.\.venv\Scripts\python.exe -m py_compile scripts\launch_web.py tests\test_web_launcher.py
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher -v
```

Expected: compilation succeeds and all launcher tests pass.

- [ ] **Step 2: Run the repository test suite and release check**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\release_check.py
```

Expected on this Windows checkout: every new launcher test passes; the full
gate may still report only the previously documented CRLF mismatch in
`test_write_then_read_artifact`. Do not suppress or relabel that existing
failure.

- [ ] **Step 3: Start the real launcher and capture both ready URLs**

Run from an interactive PowerShell window:

```powershell
.\一键启动.cmd
```

Expected console state:

```text
[本地] 已就绪: http://localhost:8080/
[就绪] 网页端与临时穿透均已启动
[本地] http://localhost:8080/
[穿透] https://<random>.trycloudflare.com
[警告] 任何获得公网链接的人都可以访问此页面。
```

- [ ] **Step 4: Validate the rendered local flow in Chrome**

Open the automatically created Chrome tab and verify:

```text
page title: novel-workflow Live Runner · 网页实跑器
engine badge: LIVE WASM · CPython 3.12
interaction: click 初始化项目
result: step becomes 已完成 and workflow.json appears
relevant page console errors: none
```

- [ ] **Step 5: Validate the public URL**

Open the exact printed `trycloudflare.com` URL and verify the page title and
22-step runner render. Do not enter API keys or other sensitive data during
the public smoke test.

- [ ] **Step 6: Validate close-window cleanup**

Close the launcher window, then run:

```powershell
Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
Get-Process cloudflared -ErrorAction SilentlyContinue
```

Expected: no listener owned by this launcher and no cloudflared process owned
by this run remains.

- [ ] **Step 7: Check Git scope and commit any validation-only correction**

```powershell
git status -sb
git diff --check
```

Expected: no generated runtime files, tunnel state, credentials, or unrelated
changes. If validation required a launcher-only correction, stage only the
five feature files and commit with a terse message describing that correction.
