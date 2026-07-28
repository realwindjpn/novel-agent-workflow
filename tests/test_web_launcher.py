from __future__ import annotations

import socket
import sys
import tempfile
import time
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


if __name__ == "__main__":
    unittest.main()
