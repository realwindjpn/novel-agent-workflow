# One-click Web and Tunnel Launcher Design

## Context

The repository currently exposes the browser SPA under `web/`, but local use
requires several manual steps: start `python -m http.server`, start a separate
tunnel process, find its public URL, open the local page, and later stop both
processes. On Windows this is easy to get wrong and commonly leaves port 8080
or a tunnel process running in the background.

The requested experience is a single double-click that starts the local web
runner and a Cloudflare Quick Tunnel, opens the local page automatically, and
stops everything when the launcher window closes.

## Goals

- Provide a Windows double-click entry point named `一键启动.cmd`.
- Serve `web/` on `127.0.0.1:8080` by default.
- Start a zero-login Cloudflare Quick Tunnel automatically.
- Wait until both the local page and public tunnel are usable.
- Open `http://localhost:8080` in the default browser after startup succeeds.
- Print the temporary `https://*.trycloudflare.com` URL prominently.
- Stop the local server and tunnel on Ctrl+C, normal exit, or launcher-window
  closure.
- Use only the Python standard library and the already-installed
  `cloudflared` executable.
- Keep the launcher testable without creating a real public tunnel during
  automated tests.

## Non-goals

- A fixed public hostname, Cloudflare account login, or named tunnel.
- Authentication or access control for the temporary public URL.
- Installing `cloudflared` automatically.
- Replacing the existing manual `python -m http.server` workflow.
- Changing the SPA, Pyodide boot logic, CLI, MCP server, or workflow core.
- Fixing the pre-existing Windows CRLF failure in
  `test_write_then_read_artifact`.

## Chosen approach

Use a Python orchestration script plus a small Windows CMD wrapper.

This matches the existing Python project, avoids an extra Node dependency,
allows deterministic unit tests, and gives one process ownership over the
HTTP server, browser launch, tunnel output, and cleanup. A PowerShell-only
implementation was rejected because output parsing and child-process cleanup
are harder to test reliably. A Node implementation was rejected because the
repository is not otherwise a Node runtime application.

## Components

### `一键启动.cmd`

The double-click entry point:

1. Changes to the repository root using `%~dp0` so invocation does not depend
   on the user's current directory.
2. Uses `.venv\Scripts\python.exe` when present.
3. Otherwise uses `py -3.11`, then `python`, in that order.
4. Runs `scripts\launch_web.py` with its original arguments.
5. Preserves the launcher result code and pauses on startup failure so the
   error remains visible to a double-click user.

### `scripts/launch_web.py`

The standard-library orchestration layer. It owns these responsibilities:

- validate the repository layout and runtime prerequisites;
- bind and serve the `web/` directory;
- launch and monitor `cloudflared`;
- parse the Quick Tunnel URL from process output;
- run local and public readiness checks;
- open the local page;
- render concise status and security messages;
- coordinate shutdown and child-process cleanup.

The module exposes small functions for dependency lookup, URL parsing,
readiness polling, HTTP-server construction, tunnel launch, and cleanup so
each behavior can be tested independently.

### `tests/test_web_launcher.py`

Standard-library `unittest` coverage. Tests use temporary directories,
ephemeral ports, a fake browser callback, and a fake `cloudflared` executable.
No automated test opens a real tunnel or browser.

## Startup data flow

1. Parse arguments. Supported options are `--port` (default `8080`) and
   `--no-browser` (used by automation and headless environments).
2. Resolve the repository root relative to `launch_web.py`, not the current
   working directory.
3. Validate that `web/index.html` exists.
4. Locate `cloudflared` with `shutil.which`. If it is absent, fail before
   starting any service and print an installation-oriented message.
5. Pre-bind `127.0.0.1:<port>`. An occupied port is a startup error; the
   launcher never kills an unknown process or silently selects another port.
6. Start a `ThreadingHTTPServer` serving only the resolved `web/` directory.
   The server runs in a daemon thread owned by the launcher process.
7. Poll `http://127.0.0.1:<port>/` until it returns HTTP 200 and the response
   identifies the novel-workflow page.
8. Spawn:

   ```text
   cloudflared tunnel --url http://127.0.0.1:<port> --no-autoupdate
   ```

   Capture both stdout and stderr because cloudflared may write the Quick
   Tunnel URL to either stream. Reader threads forward useful lines to the
   launcher console and search for
   `https://<generated-name>.trycloudflare.com`.
9. After the URL appears, poll the public URL until it returns a usable HTTP
   response. A printed URL alone is not treated as tunnel readiness.
10. Print a success block with local URL, public URL, the unauthenticated
    exposure warning, and shutdown instructions.
11. Unless `--no-browser` is set, call `webbrowser.open` for
    `http://localhost:<port>`.
12. Remain in a supervision loop. If cloudflared exits unexpectedly, report
    its exit code and shut down the local server instead of leaving a partial
    startup running.

## Process lifetime and Windows cleanup

The HTTP server lives inside the launcher process, so it cannot outlive that
process.

The cloudflared child process is assigned to a Windows Job Object configured
with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, implemented with `ctypes` from the
standard library. When the launcher exits for any reason, Windows closes the
job handle and terminates the child process. This covers direct console-window
closure in addition to normal Python cleanup.

The launcher also installs normal shutdown paths using `try/finally`,
`atexit`, and supported termination signals. These paths call
`HTTPServer.shutdown()`, request graceful cloudflared termination, wait for a
short bounded interval, and force termination only when graceful exit fails.
On non-Windows systems, the Job Object layer is skipped and the normal
termination path remains active.

Cleanup is idempotent so simultaneous exit paths cannot attempt to shut down
the same resource twice.

## Error handling

Startup is transactional: either the local server and tunnel both become
ready, or every resource started by the launcher is cleaned up.

- Missing `web/index.html`: fail with the resolved path.
- Missing `cloudflared`: fail before binding the port.
- Port already occupied: fail without killing or reusing the owner.
- Local server readiness timeout: stop the HTTP server and exit non-zero.
- Tunnel URL timeout: stop cloudflared and the HTTP server, then exit non-zero.
- Cloudflared exits before readiness: include its exit code and recent output
  in the error, then clean up.
- Public URL readiness timeout: clean up both services and exit non-zero.
- Browser open returns false or raises: keep both services running, print the
  local URL again, and report that it must be opened manually.
- Cloudflared exits after successful startup: shut down the local server and
  return non-zero so the console does not falsely display a healthy state.

Timeouts are bounded and have stable defaults. Poll loops use short intervals
and monotonic time rather than fixed long sleeps.

## Security model

The local HTTP listener binds only to `127.0.0.1`. External access is possible
only through the temporary Cloudflare URL.

Quick Tunnel URLs are unauthenticated. The success block states in Chinese
that anyone with the URL can access the SPA while the launcher is running.
The URL changes on every run and becomes unusable after the launcher stops.
The launcher does not read or store Cloudflare credentials, cookies, browser
profiles, API keys, or SPA localStorage.

## User-facing console states

The console uses plain UTF-8-compatible text and these stable phases:

- `[检查]` prerequisites and port;
- `[本地]` HTTP server address and readiness;
- `[穿透]` cloudflared startup and public readiness;
- `[就绪]` local and public URLs;
- `[警告]` unauthenticated public exposure;
- `[退出]` cleanup progress.

Failures end with a concise cause and a non-zero exit code. The CMD wrapper
pauses only on failure; normal Ctrl+C shutdown does not require an extra key.

## Testing strategy

`tests/test_web_launcher.py` covers:

- Quick Tunnel URL extraction from stdout and stderr variants;
- rejecting unrelated URLs;
- repository-root and `web/index.html` validation;
- missing cloudflared detection;
- occupied-port rejection;
- local readiness success and timeout;
- public readiness success and timeout;
- `--no-browser` suppressing browser launch;
- browser-open failure remaining non-fatal after service readiness;
- cloudflared early-exit handling;
- successful end-to-end orchestration with a fake tunnel process;
- idempotent cleanup and child-process termination;
- argument parsing for the default port and an explicit alternate port.

The fake tunnel executable prints a deterministic
`https://launcher-test.trycloudflare.com` URL and remains alive until the test
terminates it. HTTP readiness is exercised against a real ephemeral local
server; public readiness is injected as a test callback rather than using the
network.

Manual Windows acceptance:

1. Run launcher-specific unit tests.
2. Double-click `一键启动.cmd`.
3. Confirm the window reports both URLs.
4. Confirm Chrome opens `http://localhost:8080` and reaches
   `LIVE WASM · CPython 3.12`.
5. Open the printed `trycloudflare.com` URL and confirm the same SPA renders.
6. Execute the first workflow step and confirm `workflow.json` appears.
7. Close the launcher window.
8. Confirm port 8080 is free and no child cloudflared process remains.

The repository-wide release check is still run and reported. Its existing
Windows CRLF failure is not changed or hidden by this feature.

## Documentation changes

Update the root `README.md` and `web/README.md` with:

- the Windows one-click command and double-click instructions;
- the exact startup behavior;
- the local and temporary public URL distinction;
- the public-link security warning;
- Ctrl+C/window-close shutdown behavior;
- `--port` and `--no-browser` examples;
- the existing manual `python -m http.server` command as a fallback.

## Acceptance criteria

- A clean Windows checkout with Python 3.11+ and cloudflared installed starts
  the web runner by double-clicking `一键启动.cmd`.
- The browser opens the local page automatically only after both endpoints are
  ready.
- The console shows a working random Cloudflare public URL.
- A startup failure leaves neither port 8080 nor a cloudflared process behind.
- Closing the launcher window releases both resources.
- Launcher unit tests pass without opening a browser or public tunnel.
- The Git working tree contains no generated runtime logs, tunnel state, or
  credentials.
