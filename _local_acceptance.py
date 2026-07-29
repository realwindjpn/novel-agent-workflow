"""Local acceptance smoke for the dual-server launcher (Linux/headless).

Runs the Launcher with the cloudflared tunnel replaced by a no-op factory,
so the local API on 18090 and the public static handler on 18091 are real.
Validates the runtime claims that do not require a Windows host or a browser
(MCP end-to-end is covered by tests.test_local_mcp_bridge, 83 cases):

  1. /api/local/capabilities on the local port returns 200 with a token
  2. The same path on the public port returns 404
  3. The public port serves the SPA index
  4. POST /api/local/library with the right token + origin creates a book
     (MCP child round-trip is real — see session.create_book)
  5. Graceful stop frees both ports and closes the MCP child
"""

from __future__ import annotations

import json
import socket
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from launch_web import HOST, Launcher, LauncherConfig

LOCAL_PORT = 18090
PUBLIC_PORT = 18091


def http_get(url, *, headers=None, timeout=5.0):
    req = urllib.request.Request(url, method="GET", headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()


def http_post(url, body, *, headers=None, timeout=10.0):
    req = urllib.request.Request(
        url, method="POST", data=body, headers=headers or {}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # SO_REUSEADDR mirrors the launcher's pre-check; without it, recent
        # connections in TIME_WAIT make the port look busy even after a
        # clean server_close().
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((HOST, port))
            return True
        except OSError:
            return False


def wait_port_free(port: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if port_free(port):
            return True
        time.sleep(0.1)
    return False


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp) / "lib"
        library.mkdir()
        config = LauncherConfig(
            port=LOCAL_PORT, public_port=PUBLIC_PORT, library_root=library
        )
        launcher = Launcher(config)
        launcher.cloudflared = Path("/bin/true")  # skip find_cloudflared()
        launcher.tunnel_factory = lambda exe, url: None  # no real tunnel

        run_thread = threading.Thread(target=launcher.run, daemon=True)
        run_thread.start()

        try:
            # Wait for both ports to bind
            deadline = time.time() + 15
            while time.time() < deadline:
                if not port_free(LOCAL_PORT) and not port_free(PUBLIC_PORT):
                    break
                time.sleep(0.2)
            else:
                print("FAIL: ports did not bind in time")
                return 1

            local_url = f"http://{HOST}:{LOCAL_PORT}"
            public_url = f"http://{HOST}:{PUBLIC_PORT}"

            # 1. local capabilities = 200 (Origin required even for GET)
            status, _, body = http_get(
                local_url + "/api/local/capabilities",
                headers={"Origin": "http://localhost:18090"},
            )
            assert status == 200, f"local capabilities status={status} body={body[:120]!r}"
            caps = json.loads(body)
            assert caps.get("token"), f"no token in capabilities: {caps!r}"
            token = caps["token"]
            print(f"OK 1. local /api/local/capabilities=200 token={token[:8]}…")

            # 2. public capabilities = 404
            status, _, _ = http_get(public_url + "/api/local/capabilities")
            assert status == 404, f"public capabilities status={status}, expected 404"
            print("OK 2. public /api/local/capabilities=404")

            # 3. public port serves the SPA
            status, _, body = http_get(public_url + "/")
            assert status == 200 and b"novel-workflow" in body, (
                f"public root status={status} body[:80]={body[:80]!r}"
            )
            print("OK 3. public / serves the SPA")

            # 4. mutation without token = 403
            status, _, _ = http_post(
                local_url + "/api/local/library",
                json.dumps({"title": "x"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            assert status == 403, f"mutation without token status={status}, expected 403"
            print("OK 4. local mutation without token=403")

            # 5. mutation with wrong origin = 403
            status, _, _ = http_post(
                local_url + "/api/local/library",
                json.dumps({"title": "x"}).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-Library-Token": token,
                    "Origin": "https://evil.example",
                    "Referer": "https://evil.example/",
                },
            )
            assert status == 403, f"mutation with bad origin status={status}, expected 403"
            print("OK 5. local mutation with bad origin=403")

            # 6. create a book via the local API → real MCP child round-trip
            create_body = json.dumps({"title": "验收书"}).encode("utf-8")
            status, _, body = http_post(
                local_url + "/api/local/create",
                create_body,
                headers={
                    "Content-Type": "application/json",
                    "X-Library-Token": token,
                    "Origin": "http://localhost:18090",
                    "Referer": "http://localhost:18090/",
                },
            )
            assert status == 200, f"create status={status} body={body[:200]!r}"
            create_resp = json.loads(body)
            assert create_resp.get("status") == "created", create_resp
            directory = create_resp["directory"]
            book_dir = library / directory
            assert book_dir.is_dir() and (book_dir / "workflow.json").is_file()
            assert "验收书_" in directory, directory
            print(f"OK 6. book created via MCP child → {directory}")

            # 7. the same title again yields a collision
            status, _, body = http_post(
                local_url + "/api/local/create",
                json.dumps({"title": "验收书"}).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-Library-Token": token,
                    "Origin": "http://localhost:18090",
                    "Referer": "http://localhost:18090/",
                },
            )
            assert status == 200
            collision = json.loads(body)
            assert collision.get("status") == "collision", collision
            assert any(
                "验收书_" in m["directory"] for m in collision.get("matches", [])
            ), collision
            print("OK 7. duplicate title triggers collision prompt")

            # 8. graceful shutdown frees both ports and closes the MCP child
            session = launcher.resources.library_session
            assert session is not None and session._client is not None
            child = session._client
            launcher.stop_event.set()
            launcher.resources.close()
            assert wait_port_free(LOCAL_PORT), "local port still bound"
            assert wait_port_free(PUBLIC_PORT), "public port still bound"
            assert not child.open, "MCP child still open after close()"
            print("OK 8. shutdown clean: both ports free, MCP child closed")
            return 0
        finally:
            try:
                launcher.stop_event.set()
                launcher.resources.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
