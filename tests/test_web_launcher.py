from __future__ import annotations

import io
import socket
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

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

    def test_parse_quick_tunnel_url_rejects_host_suffix(self):
        self.assertIsNone(
            launch_web.parse_quick_tunnel_url(
                "https://valid.trycloudflare.com.evil.example"
            )
        )

    def test_parse_quick_tunnel_url_rejects_user_info_suffix(self):
        self.assertIsNone(
            launch_web.parse_quick_tunnel_url(
                "https://valid.trycloudflare.com@evil.example"
            )
        )

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
        with self.assertRaisesRegex(launch_web.LauncherError, "Timed out"):
            launch_web.wait_until_ready(
                "http://local.test",
                timeout=0.02,
                probe=lambda url, marker=None: False,
                interval=0.005,
            )
        self.assertLess(time.monotonic() - started, 0.5)


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
            with self.assertRaisesRegex(launch_web.LauncherError, "exited early"):
                launch_web.wait_for_tunnel_url(tunnel, timeout=2)
        finally:
            tunnel.close()

    def test_close_is_idempotent_and_terminates_process(self):
        tunnel = self._python_process("import time; time.sleep(60)")
        tunnel.close()
        tunnel.close()
        self.assertIsNotNone(tunnel.process.poll())


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

    def _run_app(self, app):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return app.run()

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
        self.assertEqual(self._run_app(app), 0)
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
        self.assertEqual(self._run_app(app), 0)
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
        self.assertEqual(self._run_app(app), 0)

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
        self.assertEqual(self._run_app(app), 0)

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
        with self.assertRaisesRegex(launch_web.LauncherError, "Timed out"):
            self._run_app(app)
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
        with self.assertRaisesRegex(launch_web.LauncherError, "Timed out"):
            self._run_app(app)
        self.assertFalse(app.resources_open)


if __name__ == "__main__":
    unittest.main()
