# Local MCP Library and Persistent Web Workspace Design

## Context

The repository has three working surfaces: the Windows CLI, a stdio MCP
server, and a browser SPA that runs a source snapshot in Pyodide. The CLI and
MCP server operate on the host filesystem. The SPA currently runs entirely in
the browser and writes to its in-memory virtual filesystem, so its workflow
files disappear when the browser runtime is discarded.

The one-click launcher currently serves one static endpoint on
`127.0.0.1:8080` and sends that same endpoint through a Cloudflare Quick
Tunnel. Adding a disk-writing API to that endpoint would also make the API
reachable through the unauthenticated public URL. The local writable surface
and the public demonstration surface therefore need process-level and
port-level separation.

## Confirmed user decisions

- The local page must use the existing MCP/core implementation for workflow
  operations instead of adding a second state machine or file writer.
- The library path is configurable in the page by manual absolute-path input
  or a native Windows folder picker.
- The default is the repository's `book/` directory. In the current checkout
  this resolves to `F:\bookworkflow\book`.
- Existing projects can be discovered and opened so work resumes from their
  persisted `workflow.json` and chapter state.
- A new project folder is named `<safe-title>_YYYYMMDD`.
- When the same dated name already exists, new work uses `(1)`, `(2)`, and so
  on. Before creating a duplicate, the page offers to open the most recent
  same-title project, create a new project, or cancel.
- Issuing a chapter creates `chapters/第NNN章_YYYYMMDD/`. Later prewrite,
  draft, and review artifacts for that chapter stay in that directory.
- The Cloudflare page remains a Pyodide memory-only demonstration. It never
  receives the local library path and cannot invoke the local MCP bridge.
- The local and public pages display unambiguous mode labels:
  `本地 MCP · 可写磁盘` and `公网演示 · 浏览器内存`.

## Goals

- Make local browser work persist to a user-selected Windows library.
- Reuse the existing stdio MCP server and its project jail for every workflow
  state transition and artifact write.
- Discover existing projects and restore the web UI to their current stage.
- Provide deterministic, collision-safe book and chapter directory names.
- Preserve the existing CLI, standalone MCP, Pyodide, Replay, and one-click
  shutdown behavior.
- Keep all local filesystem capability unreachable from the public tunnel.
- Make every new boundary independently unit-testable without opening a real
  browser, folder dialog, or Cloudflare tunnel.

## Non-goals

- Remote editing of the host filesystem through the Quick Tunnel.
- User accounts, Cloudflare Access, or a fixed public hostname.
- Replacing the stdio MCP transport with an HTTP MCP server.
- Moving existing projects automatically into the new `book/` directory.
- Renaming old artifact files or chapter state files.
- Making the public Pyodide session persistent.
- Supporting network shares or non-Windows folder dialogs in the first
  release; manual path entry remains portable.

## Chosen architecture

The launcher owns two HTTP servers and one active MCP child process:

```text
default browser
  |
  +-- http://localhost:8080 -------------------------------+
  |      local SPA + same-origin /api/local/*              |
  |                         |                               |
  |                         +-- MCP stdio child             |
  |                              --root <active book>       |
  |                                      |                 |
  |                                      +-- core/filesystem
  |
  +-- https://<random>.trycloudflare.com
         Cloudflare -> 127.0.0.1:8081
                         pure static SPA -> Pyodide memory
```

Port `8080` is the local application. Port `8081` is a static-only mirror of
the same `web/` directory and is the sole Cloudflare origin. The public server
has no API handler, no token, and no reference to the library or active book.

The local bridge is a transport and library-management adapter. It does not
reimplement workflow rules. It starts `novel-workflow mcp --root <book>` and
forwards allowlisted JSON-RPC requests over the child's stdin/stdout. The MCP
server continues to call the shared core and remains the authority for state
transitions, limits, artifact jails, resources, and errors.

## Component boundaries

### `src/novel_workflow/library.py`

A host-filesystem utility module with no web or process dependencies. It owns:

- Windows-safe path-component normalization;
- `YYYYMMDD` local-date formatting;
- collision-safe book folder selection;
- immediate-child project discovery by `workflow.json`;
- exact-title matching and most-recent selection;
- chapter artifact-directory naming.

It never changes workflow state. Discovery reads only enough metadata to
render the project picker: title, stage, `updated_at`, directory name, and
chapter count. A malformed or unreadable project is returned as an invalid
catalog entry rather than preventing other books from loading.

The safe-name function replaces Windows-reserved characters and control
characters with `_`, collapses repeated whitespace, strips trailing spaces and
dots, and prefixes reserved device names such as `CON` and `NUL`. An empty
result becomes `未命名作品`.

### Chapter workspace in `core.py`

`issue_chapter()` creates the chapter artifact directory only after all
existing issue preconditions have passed and before state is committed. The
relative directory is stored in chapter state as `artifact_dir`, for example:

```json
{
  "chapter": 1,
  "artifact_dir": "chapters/第001章_20260728"
}
```

The project-level chapter ledger mirrors `artifact_dir`. Existing projects
without the field remain valid. Existing caller-supplied artifact paths remain
accepted so CLI and MCP compatibility is preserved. The local web adapter uses
the stored directory when constructing prewrite, draft, repair, and review
paths.

### `scripts/local_mcp_bridge.py`

This module owns four focused units:

1. `McpStdioClient`: start, initialize, serialize requests, match responses,
   detect child exit, and stop the MCP process.
2. `LibrarySession`: validate the library path, catalog projects, resolve
   duplicate decisions, create/open a book, and atomically switch the active
   MCP child.
3. `LocalApi`: validate same-origin requests, session tokens, JSON bodies, and
   dispatch API routes.
4. `pick_windows_directory()`: invoke a fixed PowerShell STA script using
   `System.Windows.Forms.FolderBrowserDialog` and return only its selected
   path. No user-controlled text is interpolated into the script.

Only one active book and one MCP request are allowed at a time. Switching books
stops the old child before the new child is published to request handlers.
Failed switches leave no half-active child.

### Local API contract

All responses are JSON and use `{ "ok": true, ... }` or
`{ "ok": false, "error": { "code": "...", "message": "..." } }`.

Read routes:

- `GET /api/local/capabilities`: mode, session token, default/current library,
  active book metadata, MCP version.
- `GET /api/local/books`: catalog of immediate child projects.
- `GET /api/local/project`: current MCP `novel://state`, chapter ledger, and
  event tail.
- `GET /api/local/tree`: bounded UTF-8 snapshot for the existing explorer.
  The bridge may read this display snapshot directly, but it is read-only and
  jailed to the active book. Workflow state reads still come from MCP
  resources/tools.

Mutation routes require `Content-Type: application/json`, an exact local
`Origin`, and `X-Novel-Session`:

- `POST /api/local/library`: validate/create and select an absolute library
  path, clear the active book, and return the refreshed catalog.
- `POST /api/local/select-directory`: show the Windows folder dialog and then
  apply the selected path.
- `POST /api/local/books/open`: select an existing immediate child directory,
  start MCP with that directory as `--root`, and restore state.
- `POST /api/local/books/create`: detect title collisions. Without an explicit
  choice it returns HTTP 409 and the matching projects. With `open_latest` it
  opens the most recent match; with `create_new` it selects the next dated
  directory, starts MCP there, and calls MCP `init` with `path="."`.
- `POST /api/local/mcp`: forward only `tools/list`, `tools/call`,
  `resources/list`, `resources/read`, `prompts/list`, `prompts/get`, and
  `ping`. The server assigns request IDs and rejects client attempts to change
  the active root.

The request-body limit is 2 MiB. Concurrent MCP calls are serialized. API
errors redact child command lines and absolute paths outside the selected
library.

### `web/local.js`

The browser-side adapter detects the local bridge before Pyodide boot. If the
capability request succeeds, it exposes an `NWL` interface for library
settings, project selection, MCP calls, state refresh, tree refresh, and
workflow command translation. If detection fails or the origin is not
localhost, the existing Pyodide/Replay path starts unchanged.

The adapter translates the SPA's existing structured `argv` arrays to MCP tool
names and arguments. Setup artifacts are written first through
`write_artifact`. For chapter steps it rewrites setup/artifact paths into the
chapter state's `artifact_dir`; command arguments passed to the MCP state
machine remain relative to the active book.

Pseudo commands remain local adapter operations:

- `__reset__` is unavailable for persisted projects unless the user confirms
  permanent deletion; the first release returns a clear refusal and directs
  users to create a new project.
- `__ls__`, `__tree__`, and `__cat__` use the bounded local tree endpoint.

### Page controls

`web/index.html` gains a compact local-library panel near the engine status:

- mode badge;
- library path input;
- `选择文件夹` and `应用路径` buttons;
- `读取已有创作` project selector;
- active book name/path suffix/stage;
- a new-book action integrated with the existing init flow.

The public page shows only the public-memory badge and hides all path and
project-picker controls. The local page never displays a full path until the
capability handshake confirms the local bridge.

## Data flows

### Startup

1. Validate ports `8080` and `8081` and locate cloudflared.
2. Create the default library at `<repository>/book` if missing.
3. Generate a cryptographically random local session token.
4. Start the local API/static server on `8080`.
5. Start the public static-only server on `8081`.
6. Start cloudflared against `127.0.0.1:8081` and verify its public URL.
7. Open `http://localhost:8080`.
8. The page detects local capabilities and lists projects. MCP is started only
   after a project is opened or created.

### Create a book

1. Sanitize the title and scan exact `workflow.json.title` matches.
2. If matches exist and no decision was supplied, return 409 with candidates.
3. `open_latest` binds MCP to the most recently updated matching directory.
4. `create_new` reserves the next `<title>_YYYYMMDD[(n)]` directory.
5. Start MCP with the new directory as root and call `init` at `.`.
6. If MCP initialization fails, stop MCP and remove the new directory only
   when it is still empty except for files created by the failed initialization.
7. Return MCP state and make it active in the SPA.

### Resume a book

1. Validate that the requested directory is an immediate child of the active
   library and contains a regular `workflow.json`.
2. Stop the previous MCP child.
3. Start and initialize MCP on the selected book root.
4. Read `novel://state`, `chapters`, `novel://events`, and the bounded tree.
5. Restore the engine badge, project header, guide availability, chapter
   ledger, terminal context, and explorer.

### Issue and write a chapter

1. The SPA calls MCP `issue` at project path `.`.
2. Core creates and records `chapters/第NNN章_YYYYMMDD`.
3. The SPA reads chapter state to obtain `artifact_dir`.
4. Setup text is written through MCP `write_artifact` underneath that
   directory.
5. MCP `draft`, `review`, and `repair` receive those relative artifact paths.
6. Reloading or reopening the project reads `artifact_dir` from chapter state,
   so later work continues in the same directory even on another date.

## Security model

- Both listeners bind to `127.0.0.1`; only the static listener is tunneled.
- The public handler class has no API routing code.
- The local API validates Host, Origin, JSON content type, body size, and a
  per-launch session token for every mutation.
- No permissive CORS headers are sent. OPTIONS does not grant cross-origin
  access.
- MCP is rooted at one active book, not the whole drive or whole library.
- Manual library selection changes where future book directories may be
  selected; it never changes the active MCP root without an explicit open or
  create action.
- Catalog and tree traversal do not follow directory symlinks or junctions
  outside their resolved roots.
- The bridge never accepts executable names, command fragments, shell text, or
  a raw MCP root from the browser.
- Closing the launcher terminates both HTTP servers, MCP, and cloudflared via
  normal cleanup and the existing Windows Job Object ownership.

## Error handling

- Invalid/non-absolute path: HTTP 400; keep the previous library and MCP.
- Unwritable library: HTTP 422 with a user-actionable message.
- Folder picker canceled: HTTP 200 with `selected=false`; no state change.
- Malformed `workflow.json`: catalog entry marked invalid; opening is refused.
- Same-title collision: HTTP 409 until the user chooses open/create/cancel.
- MCP startup/initialize failure: HTTP 503; child is terminated and no active
  project is reported.
- MCP tool business error: preserve `isError: true` and show it in the existing
  terminal; do not convert it into an HTTP transport failure.
- MCP unexpected exit: clear active state, display reconnect guidance, and
  allow the same project to be reopened.
- Public server or tunnel failure: transactional launcher cleanup remains in
  effect.

## Compatibility and migration

- CLI argument syntax and standalone `novel-workflow mcp --root` behavior do
  not change.
- Existing projects can be opened from any selected library and need no schema
  migration. Missing `artifact_dir` is derived lazily for display; newly issued
  chapters persist it.
- The Pyodide snapshot is regenerated after core/library changes. Public mode
  can create the same chapter directory structure in memory.
- Replay tapes remain valid because existing recorded artifact paths are still
  accepted. New live local projects use chapter directories.
- The one-click CMD entry point remains unchanged except for any new optional
  `--public-port` argument passed through to Python.

## Testing strategy

- Pure unit tests for safe names, duplicate numbering, discovery ordering,
  malformed projects, and chapter directory names.
- Core tests for issue-time directory creation, state persistence, duplicate
  issue refusal, and backward-compatible validation.
- MCP client tests using a fake newline-delimited JSON-RPC child.
- Local API tests on ephemeral ports with a fake MCP client and fake picker.
- Security tests proving the public server returns 404 for every API route,
  bad origins/tokens fail, traversal is rejected, and symlink escape is not
  followed.
- JavaScript tests for argv-to-MCP mapping and local/public mode detection.
- Existing 210-test suite, launcher tests, source snapshot generation,
  `py_compile`, deny-list scan, and release check.
- Manual Windows acceptance with a temporary library, a duplicate-title
  choice, a chapter issue/write, launcher restart, project reopen, and proof
  that the public URL cannot reach `/api/local/capabilities`.

## Acceptance criteria

- One-click startup opens a local page labeled `本地 MCP · 可写磁盘`.
- The displayed default library is `F:\bookworkflow\book` in this checkout.
- Manual input and the Windows picker both switch the library safely.
- Existing projects appear and reopen with their persisted stage and chapters.
- Duplicate titles trigger the three-choice confirmation and new duplicates
  receive deterministic `(n)` suffixes.
- Issuing chapter 1 creates and records
  `chapters/第001章_YYYYMMDD` and later writes remain under it.
- Reloading and reopening continues the same book instead of creating a new
  in-memory `demo` project.
- The Cloudflare page is labeled `公网演示 · 浏览器内存`, receives no local
  path, and gets 404 for `/api/local/*`.
- Closing the launcher releases ports `8080` and `8081` and leaves no owned MCP
  or cloudflared process.
- No regression is introduced in CLI, MCP, Pyodide, Replay, or project-jail
  tests.
