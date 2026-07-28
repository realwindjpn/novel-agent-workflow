# Local MCP Library and Persistent Web Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the local browser a persistent, user-selectable book library through the existing stdio MCP/core while keeping the Cloudflare page strictly static and memory-only.

**Architecture:** The launcher serves a local API-enabled SPA on port 8080 and a separate static-only SPA on port 8081, with cloudflared tunneling only port 8081. A local bridge discovers books, starts one MCP child rooted at the active book, forwards allowlisted JSON-RPC, and lets the SPA restore state; shared core creates dated chapter artifact directories.

**Tech Stack:** Python 3.11 standard library, newline-delimited MCP JSON-RPC over stdio, `ThreadingHTTPServer`, Windows PowerShell STA folder picker, vanilla JavaScript, Pyodide fallback, `unittest`, cloudflared.

---

## Required reading and invariants

Before editing, read:

- `docs/superpowers/specs/2026-07-28-local-mcp-library-design.md`
- `scripts/launch_web.py`
- `src/novel_workflow/mcp_server.py`
- `src/novel_workflow/core.py`
- `web/app.js`, `web/chat.js`, `web/index.html`, and `web/explorer.js`
- `tests/test_web_launcher.py` and `tests/test_mcp_server.py`

Keep these invariants throughout implementation:

1. `127.0.0.1:8080` may serve `/api/local/*`; the Cloudflare origin on
   `127.0.0.1:8081` must never serve those routes.
2. Every workflow mutation and artifact write from the local page goes through
   the active MCP child. The bridge may directly read only catalog metadata and
   the bounded explorer snapshot.
3. MCP `--root` is the active book directory, never the drive, repository, or
   whole library.
4. Existing CLI syntax, MCP schemas, and old projects remain valid.
5. Do not modify `web/sources.js` by hand; run `scripts/gen_web_sources.py`.
6. Do not stop or inspect unrelated ngrok processes during acceptance.

## File map

- Create `src/novel_workflow/library.py`: safe names, dated directories,
  collision resolution, catalog discovery, chapter directory naming.
- Create `scripts/local_mcp_bridge.py`: MCP subprocess client, library session,
  local API handler support, and Windows directory picker.
- Create `tests/test_library.py`: library and chapter naming tests.
- Create `tests/test_local_mcp_bridge.py`: MCP lifecycle, session, API, and
  isolation tests.
- Create `web/local.js`: capability detection, settings/catalog UI logic, MCP
  request client, CLI-argv-to-MCP mapping, and persisted-state adapter.
- Create `tests/js/test_local_adapter.mjs`: deterministic JavaScript mapping
  tests using Node when available.
- Modify `src/novel_workflow/core.py`: create and persist chapter
  `artifact_dir` during `issue`.
- Modify `src/novel_workflow/mcp_server.py`: expose active chapter directory in
  existing responses without changing transport.
- Modify `scripts/launch_web.py`: dual servers, local bridge ownership,
  public-port option, readiness, and cleanup.
- Modify `tests/test_web_launcher.py`: dual-port orchestration and public API
  isolation.
- Modify `web/index.html`: local-library panel and mode badge; load `local.js`.
- Modify `web/app.js`: choose MCP local engine before Pyodide and delegate local
  operations through `NWL`.
- Modify `web/chat.js`: use the active book title/state and duplicate dialog.
- Modify the stylesheet embedded in `web/index.html`: compact settings panel,
  dialogs, project list, and mode states.
- Regenerate `web/sources.js` from shared Python sources.
- Modify `README.md` and `web/README.md`: local/public distinction, library
  naming, reopening, and security.

### Task 1: Library naming and discovery primitives

**Files:**
- Create: `src/novel_workflow/library.py`
- Create: `tests/test_library.py`

- [ ] **Step 1: Write failing tests for safe names, dated collisions, and discovery**

Create `tests/test_library.py` with these cases:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from novel_workflow.library import (
    ProjectEntry,
    chapter_artifact_dir,
    discover_projects,
    next_book_directory,
    safe_component,
)


class LibraryTests(unittest.TestCase):
    def test_safe_component_handles_windows_rules(self):
        self.assertEqual(safe_component('  A<B>: C.  '), 'A_B_ C')
        self.assertEqual(safe_component('CON'), '_CON')
        self.assertEqual(safe_component('...'), '未命名作品')

    def test_next_book_directory_uses_date_and_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                next_book_directory(root, '同名', date(2026, 7, 28)).name,
                '同名_20260728',
            )
            (root / '同名_20260728').mkdir()
            (root / '同名_20260728(1)').mkdir()
            self.assertEqual(
                next_book_directory(root, '同名', date(2026, 7, 28)).name,
                '同名_20260728(2)',
            )

    def test_discover_projects_sorts_recent_first_and_marks_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, title, updated in (
                ('old', '书甲', '2026-07-27T01:00:00+00:00'),
                ('new', '书乙', '2026-07-28T01:00:00+00:00'),
            ):
                p = root / name
                p.mkdir()
                (p / 'workflow.json').write_text(json.dumps({
                    'title': title, 'stage': 'IDEA', 'updated_at': updated,
                    'chapters': {},
                }), encoding='utf-8')
            bad = root / 'bad'
            bad.mkdir()
            (bad / 'workflow.json').write_text('{', encoding='utf-8')
            entries = discover_projects(root)
            self.assertEqual([e.directory for e in entries], ['new', 'old', 'bad'])
            self.assertFalse(entries[-1].valid)

    def test_chapter_artifact_dir_is_relative_and_zero_padded(self):
        self.assertEqual(
            chapter_artifact_dir(7, date(2026, 7, 28)).as_posix(),
            'chapters/第007章_20260728',
        )


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run the new tests and verify the module is missing**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_library -v
```

Expected: import error for `novel_workflow.library`.

- [ ] **Step 3: Implement the pure library module**

Implement these public interfaces in `src/novel_workflow/library.py`:

```python
@dataclass(frozen=True)
class ProjectEntry:
    directory: str
    title: str
    stage: str | None
    updated_at: str | None
    chapter_count: int
    valid: bool
    error: str | None = None

def safe_component(value: str) -> str: ...
def next_book_directory(library: Path, title: str, on_date: date | None = None) -> Path: ...
def discover_projects(library: Path) -> list[ProjectEntry]: ...
def same_title(entries: list[ProjectEntry], title: str) -> list[ProjectEntry]: ...
def chapter_artifact_dir(chapter: int, on_date: date | None = None) -> Path: ...
```

Implementation rules:

- Reject `chapter < 1` with `ValueError`.
- Never recurse below immediate book directories during catalog discovery.
- Ignore immediate children without `workflow.json`.
- Use `updated_at` descending, then directory descending; invalid entries sort
  last.
- Compare same titles with Unicode `casefold()` after surrounding whitespace
  is removed.
- Do not follow a symlink/junction whose resolved path leaves the library.

- [ ] **Step 4: Run library tests**

Run the command from Step 2.

Expected: all `LibraryTests` pass.

- [ ] **Step 5: Commit the library primitives**

```powershell
git add src/novel_workflow/library.py tests/test_library.py
git commit -m "feat: add persistent book library primitives"
```

### Task 2: Persist chapter artifact directories in shared core

**Files:**
- Modify: `src/novel_workflow/core.py`
- Modify: `tests/test_library.py`
- Modify: `tests/test_illegal_transitions.py`

- [ ] **Step 1: Add failing issue-time directory tests**

Add a test that prepares a project through `OUTLINE_LOCKED`, patches
`novel_workflow.core.local_today` to `date(2026, 7, 28)`, calls
`issue_chapter(root, 1, '开端', '建立冲突')`, and asserts:

```python
self.assertEqual(state['artifact_dir'], 'chapters/第001章_20260728')
self.assertTrue((root / state['artifact_dir']).is_dir())
self.assertEqual(
    load_json(root / 'workflow.json')['chapters']['1']['artifact_dir'],
    'chapters/第001章_20260728',
)
```

Add a backward-compatibility test that removes `artifact_dir` from an old
chapter fixture and confirms `validate_chapter(state) == []`.

- [ ] **Step 2: Run the focused tests and confirm failure**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_library tests.test_illegal_transitions -v
```

Expected: `artifact_dir` is absent before implementation.

- [ ] **Step 3: Implement issue-time workspace creation**

In `core.py`, import `date` and `chapter_artifact_dir`, expose a patchable
clock, and update `issue_chapter`:

```python
def local_today() -> date:
    return date.today()

# after all issue preconditions succeed
artifact_dir = chapter_artifact_dir(chapter, local_today())
(root / artifact_dir).mkdir(parents=True, exist_ok=False)
c['artifact_dir'] = artifact_dir.as_posix()
```

Update `_chapter_ledger_entry` to copy `artifact_dir` only when present. If a
filesystem error occurs after directory creation but before state persistence,
remove the newly created empty directory and re-raise. Do not remove a
non-empty directory.

- [ ] **Step 4: Run core, CLI, and MCP regression tests**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_library tests.test_illegal_transitions tests.test_cli_smoke tests.test_mcp_server -v
```

Expected: all tests pass except the already documented Windows CRLF assertion
if it still reproduces unchanged.

- [ ] **Step 5: Commit shared-core chapter workspaces**

```powershell
git add src/novel_workflow/core.py tests/test_library.py tests/test_illegal_transitions.py
git commit -m "feat: create dated chapter workspaces"
```

### Task 3: MCP stdio client and active-book session

**Files:**
- Create: `scripts/local_mcp_bridge.py`
- Create: `tests/test_local_mcp_bridge.py`

- [ ] **Step 1: Write failing MCP client lifecycle tests**

Use a fake Python child that reads one JSON object per line and returns the
same ID. Cover initialize, serialized concurrent calls, early exit, malformed
response, timeout, idempotent close, and root command construction. Assert the
real command is exactly:

```python
[
    sys.executable, '-u', '-m', 'novel_workflow.cli',
    'mcp', '--root', str(book.resolve()),
]
```

Also test `LibrarySession.open_book()` rejects traversal, non-immediate child
directories, missing/malformed `workflow.json`, and symlink escapes.

- [ ] **Step 2: Run tests and verify the bridge module is missing**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_local_mcp_bridge -v
```

Expected: import error for `scripts.local_mcp_bridge`.

- [ ] **Step 3: Implement `McpStdioClient`**

Provide this stable interface:

```python
class McpBridgeError(RuntimeError):
    pass

class McpStdioClient:
    def __init__(self, root: Path, *, python: Path = Path(sys.executable),
                 popen=subprocess.Popen, timeout: float = 10.0): ...
    def start(self) -> None: ...
    def request(self, method: str, params: dict | None = None) -> dict: ...
    def close(self) -> None: ...
    @property
    def open(self) -> bool: ...
```

Use one lock around ID allocation, stdin write, stdout read, and ID matching.
Capture stderr in a bounded deque on a reader thread. Assign the child to the
existing Windows Job Object helper. `start()` must send MCP `initialize` and
verify `serverInfo.name == 'novel-workflow'` before marking the client open.

- [ ] **Step 4: Implement `LibrarySession`**

Provide:

```python
class LibrarySession:
    def __init__(self, library: Path, *, client_factory=McpStdioClient): ...
    def set_library(self, path: Path) -> list[ProjectEntry]: ...
    def catalog(self) -> list[ProjectEntry]: ...
    def create_book(self, title: str, decision: str | None) -> dict: ...
    def open_book(self, directory: str) -> dict: ...
    def mcp(self, method: str, params: dict | None = None) -> dict: ...
    def close(self) -> None: ...
```

`create_book` returns a collision result until decision is `open_latest` or
`create_new`. For `create_new`, start MCP on the reserved directory and invoke:

```python
client.request('tools/call', {
    'name': 'init',
    'arguments': {'path': '.', 'title': title.strip()},
})
```

Publish the new client as active only after initialize and init/open-state
read succeed. Keep all project switches under one session lock.

- [ ] **Step 5: Run bridge tests and commit**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_local_mcp_bridge -v
git add scripts/local_mcp_bridge.py tests/test_local_mcp_bridge.py
git commit -m "feat: bridge local sessions to stdio MCP"
```

Expected: all bridge tests pass and no child process remains.

### Task 4: Local API and dual HTTP-server isolation

**Files:**
- Modify: `scripts/local_mcp_bridge.py`
- Modify: `scripts/launch_web.py`
- Modify: `tests/test_local_mcp_bridge.py`
- Modify: `tests/test_web_launcher.py`

- [ ] **Step 1: Add failing API security and public-isolation tests**

Start both servers on ephemeral ports. Assert:

```python
self.assertEqual(get(local, '/api/local/capabilities').status, 200)
self.assertEqual(get(public, '/api/local/capabilities').status, 404)
self.assertEqual(post(local, '/api/local/library', json_body, token=None).status, 403)
self.assertEqual(post(local, '/api/local/library', json_body,
                      token='wrong').status, 403)
self.assertEqual(post(local, '/api/local/library', json_body,
                      token=token, origin='https://evil.example').status, 403)
```

Cover the 2 MiB limit, invalid JSON, non-absolute paths, collision HTTP 409,
open/create success, picker cancel, unknown routes, and MCP tool business
errors remaining HTTP 200 with `isError` intact.

- [ ] **Step 2: Add the local API handler**

Implement the routes and envelopes defined by the design document. Generate
the token with `secrets.token_urlsafe(32)`. Require exact origins
`http://localhost:<local-port>` and `http://127.0.0.1:<local-port>` for
mutations. Send no `Access-Control-Allow-Origin` header.

The `/api/local/mcp` route must allow only:

```python
ALLOWED_MCP_METHODS = frozenset({
    'ping', 'tools/list', 'tools/call', 'resources/list', 'resources/read',
    'prompts/list', 'prompts/get',
})
```

Reject `initialize` from the browser because the bridge owns the MCP session.

- [ ] **Step 3: Split the launcher servers**

Extend `LauncherConfig` and CLI parsing with:

```python
public_port: int = 8081
```

and `--public-port`. Start:

- a local combined static/API handler on `config.port`;
- an unchanged `QuietStaticHandler` on `config.public_port`;
- cloudflared with the public static URL only.

Extend `LauncherResources.close()` to close the library session, local server,
public server, their threads, and tunnel idempotently. Include the MCP child in
the same Windows Job Object ownership model.

- [ ] **Step 4: Run launcher and bridge suites**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_local_mcp_bridge tests.test_web_launcher -v
```

Expected: all tests pass; tests use fake tunnel and fake MCP factories and do
not open a real browser, picker, or network tunnel.

- [ ] **Step 5: Commit API isolation**

```powershell
git add scripts/local_mcp_bridge.py scripts/launch_web.py tests/test_local_mcp_bridge.py tests/test_web_launcher.py
git commit -m "feat: isolate local MCP API from public web"
```

### Task 5: Windows folder picker and bounded explorer snapshot

**Files:**
- Modify: `scripts/local_mcp_bridge.py`
- Modify: `tests/test_local_mcp_bridge.py`

- [ ] **Step 1: Add failing picker and tree-jail tests**

Inject the subprocess runner and assert the picker uses a fixed
`powershell.exe -NoProfile -Sta -Command` script, returns `None` on cancel, and
does not interpolate the current library into PowerShell source. For the tree
endpoint, cover UTF-8 text, binary placeholders, per-file and total byte caps,
ignored symlinks, and stable POSIX relative paths.

- [ ] **Step 2: Implement the Windows picker**

Use this fixed script body as a single subprocess argument:

```powershell
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = '选择 novel-workflow 本地书库'
$dialog.ShowNewFolderButton = $true
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  Write-Output $dialog.SelectedPath
}
```

Return HTTP 501 for the picker route on non-Windows systems while manual path
entry continues to work.

- [ ] **Step 3: Implement a read-only project snapshot**

Walk only the active book. Do not follow symlinks. Skip `.git`, cache folders,
and files above `limits.max_read_bytes`; cap the aggregate response at 2 MiB.
Include `workflow.json`, `.novel-workflow/*.json*`, Markdown/text artifacts,
and release receipts. Return binary/unreadable entries as `'<binary>'` without
raising for the whole tree.

- [ ] **Step 4: Test and commit**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_local_mcp_bridge -v
git add scripts/local_mcp_bridge.py tests/test_local_mcp_bridge.py
git commit -m "feat: add local library picker and snapshot"
```

### Task 6: Browser local-mode adapter and library UI

**Files:**
- Create: `web/local.js`
- Create: `tests/js/test_local_adapter.mjs`
- Modify: `web/index.html`
- Modify: `web/app.js`
- Modify: `web/chat.js`

- [ ] **Step 1: Add JavaScript tests for command mapping**

Export the pure mapping helpers through CommonJS/ES-module detection without
changing browser globals. Test every unique command in `NW_TAPE.steps`, plus
`__ls__`, `__cat__`, `__tree__`, and refusal of `__reset__`. Required examples:

```javascript
assert.deepEqual(mapArgv(['init', 'demo', '--title', '书名']), {
  name: 'init', arguments: { path: '.', title: '书名' }
});
assert.deepEqual(mapArgv(['issue', 'demo', '1', '--title', '开端', '--goal', '建立冲突']), {
  name: 'issue', arguments: { path: '.', chapter: 1, title: '开端', goal: '建立冲突' }
});
```

For draft/review/repair mappings, assert numeric chapters, arrays for
`affected`, exact verdict/reason values, and artifact paths supplied by the
chapter-path rewriter.

- [ ] **Step 2: Implement `web/local.js`**

Expose:

```javascript
window.NWL = {
  detect: function () {},
  capabilities: function () {},
  setLibrary: function (path) {},
  pickLibrary: function () {},
  listBooks: function () {},
  createBook: function (title, decision) {},
  openBook: function (directory) {},
  callMcp: function (method, params) {},
  runSmart: function (setup, argv, intake) {},
  readState: function () {},
  refreshTree: function () {},
  mapArgv: mapArgv
};
```

Store only the preferred library string in `localStorage`; never store the
session token or full project contents. Read the token fresh from capabilities
on each page load. Escape all catalog text through existing HTML helpers.

- [ ] **Step 3: Add the local-library controls**

Add semantic controls with stable IDs:

```html
<section id="local-library" hidden>
  <div id="runtime-mode-badge"></div>
  <label for="library-path">本地书库路径</label>
  <input id="library-path" autocomplete="off" spellcheck="false">
  <button id="pick-library" type="button">选择文件夹</button>
  <button id="apply-library" type="button">应用路径</button>
  <button id="load-projects" type="button">读取已有创作</button>
  <select id="project-list" aria-label="已有创作"></select>
  <button id="open-project" type="button">继续创作</button>
  <div id="active-project"></div>
</section>
```

Use a native `<dialog>` for duplicate titles with buttons carrying
`open_latest`, `create_new`, and `cancel`. Keep keyboard focus and Escape
behavior accessible.

- [ ] **Step 4: Integrate engine selection and restore**

Load `local.js` before `app.js`. At boot:

1. Await `NWL.detect()` for at most 800 ms.
2. On success, select local MCP mode and do not boot Pyodide.
3. On failure, execute the existing Pyodide/Replay boot unchanged.
4. When a book opens, call MCP `resources/read novel://state`, `tools/call
   chapters`, `resources/read novel://events`, and `/api/local/tree`.
5. Populate the existing state cache and explorer, then enable only guide
   actions allowed by the persisted state.

Route existing `NWB.runSmart`, `NWB.readState`, and tree refresh calls to NWL
when local mode is active. Keep Replay and LIVE WASM branches byte-compatible
outside the new dispatch condition.

- [ ] **Step 5: Rewrite chapter artifact paths**

After a successful `issue`, read `novel://chapter/<n>` and cache
`artifact_dir`. Before `write_artifact`, prefix each chapter setup filename
with that directory. Pass the resulting project-relative paths into `draft`,
`review`, and `repair`. Reopened projects rebuild this cache from their chapter
resources.

- [ ] **Step 6: Run JavaScript and Python web tests, then commit**

```powershell
node tests/js/test_local_adapter.mjs
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher tests.test_local_mcp_bridge -v
git add web/local.js web/index.html web/app.js web/chat.js tests/js/test_local_adapter.mjs
git commit -m "feat: add persistent local MCP web mode"
```

Expected: JavaScript mapping tests and Python bridge/launcher tests pass.

### Task 7: Refresh source contract and documentation

**Files:**
- Modify (generated): `web/sources.js`
- Modify: `README.md`
- Modify: `web/README.md`

- [ ] **Step 1: Add `library.py` to the canonical web snapshot list**

Update `FILES` in `scripts/gen_web_sources.py` to include `library.py`, then
run:

```powershell
.\.venv\Scripts\python.exe scripts\gen_web_sources.py
```

Expected: `web/sources.js` is regenerated and public Pyodide can import the
same chapter naming helper.

- [ ] **Step 2: Document the two runtime surfaces**

Document:

- local `8080` as MCP-backed and disk-writable;
- public `8081`/Quick Tunnel as Pyodide memory-only;
- default `<repo>\book` path and the current checkout example;
- manual input and Windows picker;
- `<title>_YYYYMMDD[(n)]` duplicate behavior;
- reopening existing work;
- `chapters\第NNN章_YYYYMMDD` artifact layout;
- shutdown ownership for MCP, both HTTP servers, and cloudflared;
- `--port`, `--public-port`, and `--no-browser` examples.

- [ ] **Step 3: Run snapshot and deny-list checks**

```powershell
.\.venv\Scripts\python.exe -m py_compile src\novel_workflow\library.py scripts\local_mcp_bridge.py scripts\launch_web.py
.\.venv\Scripts\python.exe scripts\gen_web_sources.py
git diff --exit-code -- web\sources.js
```

Run the repository's existing deny-list/release scanner. Any new absolute-path
example that triggers the release scanner must be expressed as a runtime
derived path or a clearly permitted documentation example; do not weaken the
scanner.

- [ ] **Step 4: Commit generated contract and docs**

```powershell
git add scripts/gen_web_sources.py web/sources.js README.md web/README.md
git commit -m "docs: explain local MCP book library"
```

### Task 8: Full automated and Windows acceptance

**Files:**
- Modify only files required by failures attributable to this feature.

- [ ] **Step 1: Run focused suites**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_library tests.test_local_mcp_bridge tests.test_web_launcher tests.test_mcp_server tests.test_cli_smoke tests.test_illegal_transitions -v
node tests/js/test_local_adapter.mjs
```

Expected: all new and launcher tests pass. Record the known Windows CRLF result
separately if the legacy assertion remains.

- [ ] **Step 2: Run the full release check**

```powershell
.\.venv\Scripts\python.exe scripts\release_check.py
```

Expected: `RELEASE_CHECK_PASS`, or only the already documented
`test_write_then_read_artifact` CRLF mismatch with no additional failure.

- [ ] **Step 3: Perform real local acceptance in a temporary library**

Start `一键启动.cmd`, set the library to a temporary directory, and verify:

1. Local badge reads `本地 MCP · 可写磁盘`.
2. Public badge reads `公网演示 · 浏览器内存`.
3. Create `验收书_20260728`, reload, and reopen it.
4. Create the same title; verify the dialog and `验收书_20260728(1)`.
5. Advance the workflow to issue chapter 1.
6. Confirm `chapters\第001章_20260728` exists and receives prewrite/draft.
7. Restart the launcher and continue the same chapter directory.
8. Request `/api/local/capabilities` through the Cloudflare URL and confirm
   HTTP 404.
9. Close the launcher and confirm ports 8080/8081 are free and its MCP and
   cloudflared children are gone.
10. Confirm the user's unrelated ngrok process remains unchanged.

- [ ] **Step 4: Commit acceptance fixes, if any**

Stage only feature-related fixes, rerun the affected focused test, and commit:

```powershell
git commit -m "fix: complete local MCP library acceptance"
```

If no fixes were needed, do not create an empty commit.

## Definition of done

- All acceptance criteria in the design document have direct automated or
  manual evidence.
- Public HTTP code has no route capable of reaching the MCP client or local
  session.
- All persisted mutations visible in the local SPA can be traced to an MCP
  `tools/call` response.
- Existing books reopen without migration; newly issued chapters record
  `artifact_dir`.
- The generated web snapshot matches the source list.
- The worktree is clean, the implementation branch is pushed, and the handoff
  reports exact test results and any unchanged legacy failure.
