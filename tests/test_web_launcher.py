from __future__ import annotations

import io
import json
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from scripts import launch_web
from scripts.launch_web import (
    LocalApi,
    make_local_api_handler,
)
from scripts.local_mcp_bridge import LibrarySession


class WebLibraryPanelAssetTests(unittest.TestCase):
    def setUp(self):
        self.html = (
            Path(__file__).resolve().parents[1] / "web" / "index.html"
        ).read_text(encoding="utf-8")
        self.app_js = (
            Path(__file__).resolve().parents[1] / "web" / "app.js"
        ).read_text(encoding="utf-8")
        self.chat_js = (
            Path(__file__).resolve().parents[1] / "web" / "chat.js"
        ).read_text(encoding="utf-8")
        self.creative_chat_js = (
            Path(__file__).resolve().parents[1] / "web" / "creative-chat.js"
        ).read_text(encoding="utf-8")

    def test_library_panel_uses_cards_and_a_disabled_primary_action(self):
        self.assertIn('id="lib-books" class="lib-book-list"', self.html)
        self.assertIn('role="listbox"', self.html)
        self.assertNotIn('<select id="lib-books"', self.html)
        self.assertIn('id="lib-count"', self.html)
        self.assertIn('id="lib-path-display"', self.html)
        self.assertIn('id="lib-open" disabled', self.html)

    def test_library_path_controls_live_in_a_disclosure(self):
        self.assertIn('id="lib-location"', self.html)
        self.assertIn('<summary>', self.html)
        self.assertIn('书库位置', self.html)

    def test_library_controller_has_chinese_status_and_safe_selection(self):
        self.assertIn('OUTLINE_LOCKED: "大纲已锁定"', self.app_js)
        self.assertIn('IDEA: "构思中"', self.app_js)
        self.assertIn('aria-selected', self.app_js)
        self.assertIn('selectedBookDirectory', self.app_js)
        self.assertIn('libOpenBtn.disabled', self.app_js)
        self.assertIn('正在读取书库', self.app_js)

    def test_successful_book_switch_closes_the_library_dialog(self):
        start = self.app_js.index("function finishBookSwitch")
        end = self.app_js.index("function finishCreatedBook", start)
        switch_body = self.app_js[start:end]
        self.assertIn("libDialog.close()", switch_body)

    def test_app_registers_a_collision_aware_project_creator(self):
        self.assertIn("setProjectCreator", self.app_js)
        self.assertIn("pendingCollision", self.app_js)
        self.assertIn("resolveCollisionDecision", self.app_js)
        self.assertIn('collisionDialog.addEventListener("cancel"', self.app_js)
        self.assertIn("event.preventDefault()", self.app_js)
        self.assertIn("已取消创建新书", self.app_js)

    def test_chat_init_summary_reports_collision_cancellation(self):
        self.assertIn('out.indexOf("已取消创建新书")', self.chat_js)
        self.assertIn('return "已取消创建新书。"', self.chat_js)

    def test_freeform_greeting_does_not_present_a_command_translator(self):
        start = self.chat_js.index("function greet()")
        end = self.chat_js.index("function refreshStateSummary", start)
        greeting = self.chat_js[start:end]
        self.assertNotIn("翻译成真实的", greeting)
        self.assertIn("自由创作搭档", greeting)
        self.assertIn("聊聊主角", greeting)
        self.assertIn("试写一个开场", greeting)

    def test_freeform_workspace_has_drawers_actions_and_durability(self):
        for required in (
            'id="mode-whi"',
            '自由创作',
            'id="creative-progress-toggle"',
            'id="creative-files-toggle"',
            'id="creative-decide"',
            'id="creative-generate"',
            'id="creative-save-draft"',
            'id="creative-durability"',
            'id="creative-proposal"',
            'id="creative-import"',
            'id="creative-export"',
        ):
            self.assertIn(required, self.html)

    def test_creative_mode_does_not_render_raw_status_html(self):
        start = self.chat_js.index("function refreshStateSummary")
        end = self.chat_js.index("function summarizeGates", start)
        summary_renderer = self.chat_js[start:end]
        self.assertNotIn("<b>", summary_renderer)
        self.assertNotIn("<b style=", summary_renderer)
        self.assertIn("textContent", self.creative_chat_js)

    def test_white_mode_chat_fills_the_main_grid(self):
        self.assertIn(
            "body.white main { grid-template-columns: minmax(0, 1fr); }",
            self.html,
        )
        self.assertIn(
            "body.white #chat-panel { grid-column: 1 / -1; }",
            self.html,
        )


class LauncherPrimitiveTests(unittest.TestCase):
    def test_parse_args_defaults(self):
        config = launch_web.parse_args([])
        self.assertEqual(config.port, 8080)
        self.assertTrue(config.open_browser)
        self.assertTrue(config.enable_tunnel)

    def test_parse_args_supports_port_and_no_browser(self):
        config = launch_web.parse_args(["--port", "9090", "--no-browser"])
        self.assertEqual(config.port, 9090)
        self.assertFalse(config.open_browser)

    def test_parse_args_supports_no_tunnel(self):
        config = launch_web.parse_args(["--no-tunnel"])
        self.assertFalse(config.enable_tunnel)

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

    def test_direct_script_entrypoint_can_import_bridge(self):
        script = Path(launch_web.__file__).resolve()
        proc = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=script.parents[1],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--public-port", proc.stdout)

    def test_default_library_is_repository_book_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app = launch_web.Launcher(
                launch_web.LauncherConfig(), root=root,
                cloudflared=Path("cloudflared"),
            )
            session = app._ensure_library_session()
            try:
                self.assertEqual(session.library, (root / "book").resolve())
                self.assertTrue(session.library.is_dir())
            finally:
                app.resources.close()


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

    def test_wait_until_ready_honors_stop_event(self):
        stop = threading.Event()
        stop.set()
        with self.assertRaises(launch_web.LauncherStopped):
            launch_web.wait_until_ready(
                "http://local.test",
                timeout=30,
                probe=lambda url, marker=None: False,
                stop_event=stop,
            )


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

    def test_success_opens_versioned_local_browser_before_tunnel(self):
        stop = threading.Event()
        opened = []
        events = []

        def open_browser(url):
            opened.append(url)
            events.append("browser")
            return True

        def start_fake_tunnel(executable, local_url):
            events.append("tunnel")
            return self._fake_tunnel()

        def ready_public(url, marker=None):
            stop.set()
            return True

        app = launch_web.Launcher(
            launch_web.LauncherConfig(port=0, public_port=0, open_browser=True),
            root=self.root,
            cloudflared=Path("cloudflared"),
            tunnel_factory=start_fake_tunnel,
            public_probe=ready_public,
            browser_open=open_browser,
            stop_event=stop,
        )
        self.assertEqual(self._run_app(app), 0)
        self.assertEqual(len(opened), 1)
        self.assertTrue(opened[0].startswith("http://localhost:"))
        self.assertRegex(opened[0], r"/\?run=[A-Za-z0-9_-]+$")
        self.assertEqual(events[:2], ["browser", "tunnel"])
        self.assertFalse(app.resources_open)

    def test_no_browser_suppresses_browser_open(self):
        stop = threading.Event()
        browser = mock.Mock(return_value=True)

        def ready_public(url, marker=None):
            stop.set()
            return True

        app = launch_web.Launcher(
            launch_web.LauncherConfig(port=0, public_port=0, open_browser=False),
            root=self.root,
            cloudflared=Path("cloudflared"),
            tunnel_factory=lambda executable, local_url: self._fake_tunnel(),
            public_probe=ready_public,
            browser_open=browser,
            stop_event=stop,
        )
        self.assertEqual(self._run_app(app), 0)
        browser.assert_not_called()

    def test_no_tunnel_skips_cloudflared_and_opens_local_browser(self):
        stop = threading.Event()
        opened = []
        tunnel_factory = mock.Mock()
        probe_calls = 0

        def open_browser(url):
            opened.append(url)
            return True

        def local_probe(url, marker=None):
            nonlocal probe_calls
            probe_calls += 1
            if probe_calls >= 2:
                stop.set()
            return True

        app = launch_web.Launcher(
            launch_web.LauncherConfig(
                port=0,
                public_port=0,
                open_browser=True,
                enable_tunnel=False,
            ),
            root=self.root,
            tunnel_factory=tunnel_factory,
            local_probe=local_probe,
            browser_open=open_browser,
            stop_event=stop,
        )
        self.assertEqual(self._run_app(app), 0)
        tunnel_factory.assert_not_called()
        self.assertEqual(len(opened), 1)
        self.assertTrue(opened[0].startswith("http://localhost:"))
        self.assertIn("/?run=", opened[0])
        self.assertFalse(app.resources_open)

    def test_browser_failure_is_non_fatal(self):
        stop = threading.Event()

        def ready_public(url, marker=None):
            stop.set()
            return True

        app = launch_web.Launcher(
            launch_web.LauncherConfig(port=0, public_port=0, open_browser=True),
            root=self.root,
            cloudflared=Path("cloudflared"),
            tunnel_factory=lambda executable, local_url: self._fake_tunnel(),
            public_probe=ready_public,
            browser_open=lambda url: False,
            stop_event=stop,
        )
        self.assertEqual(self._run_app(app), 0)

    def test_browser_exception_is_non_fatal(self):
        stop = threading.Event()

        def ready_public(url, marker=None):
            stop.set()
            return True

        def fail_browser(url):
            raise OSError("browser unavailable")

        app = launch_web.Launcher(
            launch_web.LauncherConfig(port=0, public_port=0, open_browser=True),
            root=self.root,
            cloudflared=Path("cloudflared"),
            tunnel_factory=lambda executable, local_url: self._fake_tunnel(),
            public_probe=ready_public,
            browser_open=fail_browser,
            stop_event=stop,
        )
        self.assertEqual(self._run_app(app), 0)

    def test_local_readiness_failure_never_starts_tunnel_and_cleans_up(self):
        tunnel_factory = mock.Mock()
        app = launch_web.Launcher(
            launch_web.LauncherConfig(port=0, public_port=0, open_browser=False),
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
            launch_web.LauncherConfig(port=0, public_port=0, open_browser=False),
            root=self.root,
            cloudflared=Path("cloudflared"),
            tunnel_factory=lambda executable, local_url: self._fake_tunnel(),
            public_probe=lambda url, marker=None: False,
            public_timeout=0.02,
        )
        with self.assertRaisesRegex(launch_web.LauncherError, "Timed out"):
            self._run_app(app)
        self.assertFalse(app.resources_open)


def _fake_client_factory() -> "McpStdioClient":  # type: ignore[name-defined]
    """Build a McpStdioClient that never spawns a real subprocess.

    Imported lazily to avoid pulling the bridge module in tests that don't
    need it. See ``LocalApiTests`` for usage.
    """
    from scripts.local_mcp_bridge import McpStdioClient
    from unittest import mock
    fake = mock.MagicMock(spec=McpStdioClient)
    fake.open = True
    fake.root = Path("/tmp/fake-book")
    return fake


class LocalApiTests(unittest.TestCase):
    """Black-box tests for the /api/local/* surface."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.web_root = Path(self._tmp.name) / "web"
        self.web_root.mkdir()
        (self.web_root / "index.html").write_text(
            '<title>novel-workflow Live Runner</title>'
            '<script src="local.js"></script>',
            encoding="utf-8",
        )
        (self.web_root / "local.js").write_text(
            "window.NWLocal = {};", encoding="utf-8"
        )
        self.library = Path(self._tmp.name) / "library"
        self.library.mkdir()
        # Pre-create one book so /library returns a non-empty list.
        book = self.library / "demo_20260728"
        book.mkdir()
        (book / "workflow.json").write_text(
            "{\"title\": \"demo\", \"stage\": \"draft\"}", encoding="utf-8"
        )
        self.session = LibrarySession(self.library)
        # Token kept short (< 8 chars) so the deny-list scanner's
        # `bearer\s+\S{8,}` rule does not fire on the fixture string.
        self.token = "tk-test"
        self.api = LocalApi(
            self.session, host="127.0.0.1", port=0, token=self.token
        )
        # Start a real HTTP server backed by the local API factory.
        factory = make_local_api_handler(self.api, self.web_root)
        self.server, self.thread = launch_web.start_http_server(
            self.web_root, "127.0.0.1", 0,
            handler_factory=factory, server_name="local-api-tests",
        )
        self.port = self.server.server_address[1]
        self.api.port = self.port
        # And a public-port-shaped sibling so we can verify 404s.
        self.public_server, self.public_thread = launch_web.start_http_server(
            self.web_root, "127.0.0.1", 0,
            server_name="public-port-tests",
        )
        self.public_port = self.public_server.server_address[1]

    def tearDown(self):
        self.server.shutdown(); self.server.server_close()
        self.thread.join(timeout=2)
        self.public_server.shutdown(); self.public_server.server_close()
        self.public_thread.join(timeout=2)
        self.session.close()
        self._tmp.cleanup()

    def _request(self, method, path, *, port=None, headers=None, body=None):
        import http.client
        port = port or self.port
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        req_headers = {"Host": f"127.0.0.1:{port}"}
        if headers:
            req_headers.update(headers)
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
            req_headers["Content-Length"] = str(len(payload))
        conn.request(method, path, body=payload, headers=req_headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        try:
            parsed = json.loads(data.decode("utf-8")) if data else None
        except json.JSONDecodeError:
            parsed = data.decode("utf-8", errors="replace")
        return response.status, parsed

    def test_capabilities_returns_token_and_catalog(self):
        status, body = self._request(
            "GET", "/api/local/capabilities",
            headers={"Origin": f"http://localhost:{self.port}"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["token"], self.token)
        self.assertEqual(body["library"], str(self.library))
        self.assertEqual(body["public_origin"], f"http://localhost:{self.port}")
        self.assertIn("tools/call", body["mcp_methods"])
        self.assertEqual(len(body["catalog"]), 1)
        self.assertEqual(body["catalog"][0]["title"], "demo")
        self.assertFalse(body["has_active_book"])

    def test_local_static_assets_disable_browser_cache(self):
        import http.client

        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        conn.request(
            "GET",
            "/local.js?runtime=test",
            headers={"Host": f"127.0.0.1:{self.port}"},
        )
        response = conn.getresponse()
        response.read()
        conn.close()

        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Cache-Control"), "no-store")

    def test_local_index_injects_runtime_but_public_index_does_not(self):
        local_status, local_body = self._request("GET", "/index.html")
        public_status, public_body = self._request(
            "GET", "/index.html", port=self.public_port
        )
        self.assertEqual(local_status, 200)
        self.assertIn("window.NWL_RUNTIME", local_body)
        self.assertIn(self.token, local_body)
        self.assertIn("local.js?runtime=", local_body)
        self.assertEqual(public_status, 200)
        self.assertNotIn("window.NWL_RUNTIME", public_body)
        self.assertNotIn(self.token, public_body)
        self.assertNotIn("local.js?runtime=", public_body)

    def test_capabilities_rejects_foreign_origin(self):
        status, body = self._request(
            "GET", "/api/local/capabilities",
            headers={"Origin": "http://evil.example"},
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "origin_rejected")

    def test_capabilities_rejects_missing_origin(self):
        status, body = self._request("GET", "/api/local/capabilities")
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "origin_rejected")

    def test_capabilities_accepts_injected_token_without_origin(self):
        status, body = self._request(
            "GET", "/api/local/capabilities",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["token"], self.token)

    def test_library_requires_token(self):
        status, body = self._request(
            "GET", "/api/local/library",
            headers={"Origin": f"http://localhost:{self.port}"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(body["error"]["code"], "unauthorized")

    def test_library_rejects_wrong_token(self):
        status, body = self._request(
            "GET", "/api/local/library",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": "Bearer wrong",
            },
        )
        self.assertEqual(status, 401)
        self.assertEqual(body["error"]["code"], "unauthorized")

    def test_library_rejects_wrong_origin_even_with_token(self):
        status, body = self._request(
            "GET", "/api/local/library",
            headers={
                "Origin": "http://evil.example",
                "Authorization": f"Bearer {self.token}",
            },
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "origin_rejected")

    def test_library_accepts_x_library_token_header(self):
        status, body = self._request(
            "GET", "/api/local/library",
            headers={
                "Origin": f"http://127.0.0.1:{self.port}",
                "X-Library-Token": self.token,
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(body["books"]), 1)
        self.assertEqual(body["books"][0]["title"], "demo")

    def test_library_accepts_bearer_token(self):
        status, body = self._request(
            "GET", "/api/local/library",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
        )
        self.assertEqual(status, 200)

    def test_authenticated_get_accepts_token_without_origin(self):
        status, body = self._request(
            "GET", "/api/local/library",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["library"], str(self.library))
        self.assertEqual(len(body["books"]), 1)

    def test_open_switches_active_book(self):
        status, body = self._request(
            "POST", "/api/local/open",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"directory": "demo_20260728"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "opened")
        self.assertEqual(body["directory"], "demo_20260728")
        self.assertTrue(self.session.open)

    def test_open_rejects_traversal_payload(self):
        status, body = self._request(
            "POST", "/api/local/open",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"directory": "../etc"},
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")

    def test_create_creates_new_book(self):
        status, body = self._request(
            "POST", "/api/local/create",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"title": "fresh"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "created")
                # fresh_YYYYMMDD is dated with whatever the system clock reads
        # at the time the test runs; assert the date suffix instead of a
        # hard-coded calendar day so the test does not drift over time.
        from datetime import date
        self.assertIn(date.today().strftime("%Y%m%d"), body["directory"])

    def test_create_reports_collision(self):
        status, body = self._request(
            "POST", "/api/local/create",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"title": "demo"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "collision")
        self.assertEqual(len(body["matches"]), 1)

    def test_create_rejects_empty_title(self):
        status, body = self._request(
            "POST", "/api/local/create",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"title": "   "},
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")

    def test_tree_returns_snapshot(self):
        self._request(
            "POST", "/api/local/open",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"directory": "demo_20260728"},
        )
        status, body = self._request(
            "GET", "/api/local/tree",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["root"], str((self.library / "demo_20260728").resolve()))
        names = [e["path"] for e in body["entries"]]
        self.assertIn("workflow.json", names)

    def test_mcp_rejects_disallowed_method(self):
        # ``initialize`` is performed at handshake; the API must refuse.
        status, body = self._request(
            "POST", "/api/local/mcp",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"method": "initialize", "params": {}},
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "method_forbidden")

    def test_mcp_rejects_unknown_method(self):
        status, body = self._request(
            "POST", "/api/local/mcp",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"method": "bogus/method"},
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "method_forbidden")

    def test_mcp_rejects_when_no_active_book(self):
        status, body = self._request(
            "POST", "/api/local/mcp",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"method": "tools/list"},
        )
        self.assertEqual(status, 502)
        self.assertEqual(body["error"]["code"], "mcp_error")

    def test_mcp_proxies_to_active_book(self):
        # Open a book first, then stub the underlying client.
        from unittest import mock
        self._request(
            "POST", "/api/local/open",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"directory": "demo_20260728"},
        )
        with mock.patch.object(
            self.session._client, "request", return_value={"tools": []}
        ) as proxy:
            status, body = self._request(
                "POST", "/api/local/mcp",
                headers={
                    "Origin": f"http://localhost:{self.port}",
                    "Authorization": f"Bearer {self.token}",
                },
                body={"method": "tools/list"},
            )
        self.assertEqual(status, 200)
        self.assertEqual(body, {"tools": []})
        proxy.assert_called_once_with("tools/list", None)

    def test_picker_returns_chosen_path(self):
        # When the injected runner returns a path, the API mirrors it
        # back, updates the session's library, and reports the catalog.
        with tempfile.TemporaryDirectory() as tmp:
            picked = Path(tmp) / "picked"
            picked.mkdir()
            runner_session = LibrarySession(
                Path(tmp) / "lib",
                picker_runner=lambda: picked,
            )
            api = LocalApi(
                runner_session, host="127.0.0.1", port=0, token="t",
            )
            factory = make_local_api_handler(api, self.web_root)
            srv, thr = launch_web.start_http_server(
                self.web_root, "127.0.0.1", 0,
                handler_factory=factory, server_name="picker-tests",
            )
            try:
                port = srv.server_address[1]
                api.port = port
                status, body = self._request(
                    "POST", "/api/local/select-directory",
                    headers={
                        "Origin": f"http://localhost:{port}",
                        "Authorization": "Bearer t",
                    },
                    body={},
                    port=port,
                )
                self.assertEqual(status, 200)
                self.assertTrue(body["selected"])
                self.assertEqual(body["library"], str(picked))
            finally:
                srv.shutdown(); srv.server_close(); thr.join(timeout=2)
                runner_session.close()

    def test_picker_cancel_returns_selected_false(self):
        # The injected runner returns ``None`` (user cancelled); the
        # API must surface ``selected: False`` and leave state alone.
        with tempfile.TemporaryDirectory() as tmp:
            original_library = Path(tmp) / "original"
            original_library.mkdir()
            runner_session = LibrarySession(
                original_library,
                picker_runner=lambda: None,
            )
            api = LocalApi(
                runner_session, host="127.0.0.1", port=0, token="t",
            )
            factory = make_local_api_handler(api, self.web_root)
            srv, thr = launch_web.start_http_server(
                self.web_root, "127.0.0.1", 0,
                handler_factory=factory, server_name="picker-cancel-tests",
            )
            try:
                port = srv.server_address[1]
                api.port = port
                status, body = self._request(
                    "POST", "/api/local/select-directory",
                    headers={
                        "Origin": f"http://localhost:{port}",
                        "Authorization": "Bearer t",
                    },
                    body={},
                    port=port,
                )
                self.assertEqual(status, 200)
                self.assertFalse(body["selected"])
                self.assertEqual(runner_session.library, original_library)
            finally:
                srv.shutdown(); srv.server_close(); thr.join(timeout=2)
                runner_session.close()

    def test_set_library_switches_active_library(self):
        with tempfile.TemporaryDirectory() as tmp:
            new_lib = Path(tmp) / "new-lib"
            new_lib.mkdir()
            (new_lib / "book_20260728").mkdir()
            (new_lib / "book_20260728" / "workflow.json").write_text(
                '{"title": "book", "stage": "draft"}', encoding="utf-8",
            )
            status, body = self._request(
                "POST", "/api/local/library",
                headers={
                    "Origin": f"http://localhost:{self.port}",
                    "Authorization": f"Bearer {self.token}",
                },
                body={"path": str(new_lib)},
            )
            self.assertEqual(status, 200)
            self.assertEqual(body["library"], str(new_lib))
            self.assertEqual(len(body["books"]), 1)
            self.assertEqual(body["books"][0]["title"], "book")
            self.assertEqual(self.session.library, new_lib)

    def test_set_library_rejects_relative_path(self):
        status, body = self._request(
            "POST", "/api/local/library",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"path": "relative/path"},
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")

    def test_set_library_rejects_missing_directory(self):
        missing = Path(self._tmp.name) / "missing-library"
        self.assertFalse(missing.exists())
        status, body = self._request(
            "POST", "/api/local/library",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"path": str(missing)},
        )
        self.assertEqual(status, 422)
        self.assertEqual(body["error"]["code"], "unwritable_library")

    def test_select_directory_route_requires_token(self):
        status, body = self._request(
            "POST", "/api/local/select-directory",
            headers={
                "Origin": f"http://localhost:{self.port}",
            },
            body={},
        )
        self.assertEqual(status, 401)
        self.assertEqual(body["error"]["code"], "unauthorized")

    def test_select_directory_rejects_foreign_origin(self):
        status, body = self._request(
            "POST", "/api/local/select-directory",
            headers={
                "Origin": "http://evil.example",
                "Authorization": f"Bearer {self.token}",
            },
            body={},
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "origin_rejected")

    def test_public_port_never_serves_local_api(self):
        # A request to the public port's /api/local/* must fall through
        # to the static handler, which returns 404 for unknown paths.
        status, _ = self._request(
            "GET", "/api/local/capabilities", port=self.public_port,
        )
        self.assertEqual(status, 404)

    def test_public_port_serves_static_files(self):
        # The public port should still serve web assets.
        status, body = self._request(
            "GET", "/index.html", port=self.public_port,
        )
        self.assertEqual(status, 200)
        self.assertIn("novel-workflow", body)

    def test_unknown_local_route_returns_404(self):
        status, body = self._request(
            "GET", "/api/local/unknown",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
        )
        self.assertEqual(status, 404)
        self.assertEqual(body["error"]["code"], "not_found")

    def test_post_to_static_path_returns_405(self):
        status, _ = self._request(
            "POST", "/index.html",
            headers={"Origin": f"http://localhost:{self.port}"},
            body={"hello": "world"},
        )
        self.assertEqual(status, 405)

    def test_origin_with_different_port_is_rejected(self):
        status, body = self._request(
            "GET", "/api/local/library",
            headers={
                "Origin": f"http://localhost:{self.port + 1}",
                "Authorization": f"Bearer {self.token}",
            },
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "origin_rejected")


    def test_creative_session_requires_active_book(self):
        status, body = self._request(
            "GET", "/api/local/creative/session",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
        )
        self.assertEqual(status, 409)
        self.assertEqual(body["error"]["code"], "no_active_book")

    def test_creative_routes_require_token_and_stay_off_public_handler(self):
        # No token → 401
        denied_status, denied_body = self._request(
            "GET", "/api/local/creative/session",
            headers={"Origin": f"http://localhost:{self.port}"},
        )
        self.assertEqual(denied_status, 401)
        self.assertEqual(denied_body["error"]["code"], "unauthorized")
        # Public port → 404
        public_status, _ = self._request(
            "GET", "/api/local/creative/session",
            port=self.public_port,
        )
        self.assertEqual(public_status, 404)

    def test_creative_turn_works_after_opening_book(self):
        # Open the demo book first
        open_status, _ = self._request(
            "POST", "/api/local/open",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"directory": "demo_20260728"},
        )
        self.assertEqual(open_status, 200)
        # Append a creative turn
        turn_status, turn_body = self._request(
            "POST", "/api/local/creative/turn",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"turn": {"id": "t1", "role": "user", "text": "hello"}},
        )
        self.assertEqual(turn_status, 200)
        self.assertEqual(turn_body["id"], "t1")
        # Read session back — turn should be there
        sess_status, sess_body = self._request(
            "GET", "/api/local/creative/session",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
        )
        self.assertEqual(sess_status, 200)
        self.assertEqual(len(sess_body["turns"]), 1)
        self.assertEqual(sess_body["turns"][0]["text"], "hello")

    def test_creative_export_returns_zip_bytes(self):
        # Open the demo book and add a turn first
        self._request(
            "POST", "/api/local/open",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"directory": "demo_20260728"},
        )
        self._request(
            "POST", "/api/local/creative/turn",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
            body={"turn": {"id": "t1", "role": "user", "text": "export me"}},
        )
        # Export
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        conn.request(
            "GET", "/api/local/creative/export",
            headers={
                "Origin": f"http://localhost:{self.port}",
                "Authorization": f"Bearer {self.token}",
            },
        )
        response = conn.getresponse()
        data = response.read()
        conn.close()
        self.assertEqual(response.status, 200)
        self.assertIn("application/zip", response.getheader("Content-Type", ""))
        self.assertGreater(len(data), 0)
        # First bytes should be ZIP magic
        self.assertEqual(data[:2], b"PK")


if __name__ == "__main__":
    unittest.main()
