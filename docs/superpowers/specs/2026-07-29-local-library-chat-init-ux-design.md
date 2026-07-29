# Local library panel and chat-init UX design

Date: 2026-07-29
Status: approved for planning

## Goal

This change has two equal product goals:

1. Replace the raw local-library list box with a clearer card-based layout.
2. Make a local-mode chat request to start a new book create and activate the
   book before any MCP workflow command is sent.

The screenshots motivating the change show both failures at once: the library
dialog exposes raw machine state in a dense native list, while the chat creates
an `init` plan and sends it to the MCP transport even though the header still
says that no book is selected. The result is `transport: no active book`.

## User-facing behavior

### Library panel

The modal remains a focused library chooser rather than becoming a separate
management page. Its visual hierarchy is:

1. Header: `本地书库`, book count, and close action.
2. Collapsible `书库位置` row: current absolute path plus `更改路径` and
   `重新读取`. The path is visible but visually secondary.
3. `已有创作` card list.
4. A primary `继续创作` button, disabled until a card is selected.
5. A separate `新建创作` area with a book-title input and `创建新书` button.
6. One stable status line for loading, success, empty, and error states.

Each book is a real button-like card, not a native `<select>` option. A card
shows:

- book title as the primary label;
- a Chinese workflow-status chip;
- chapter count;
- the actual directory name as secondary monospace metadata.

One click selects a card and applies a visible selected state. Selection alone
does not open the project. The user must click `继续创作`, preventing accidental
book switches. Keyboard focus, `aria-pressed`, and disabled states must mirror
the visual state.

Known workflow states are translated through one `statusLabel()` function.
Examples include `IDEA` -> `构思中`, `OUTLINE_LOCKED` -> `大纲已锁定`, and a
released chapter summary -> `已有章节发布`. Unknown states display `处理中`;
the original machine value remains available in the element title for support
and debugging, but is not primary UI text.

On narrow screens the same hierarchy stays single-column. The card list may
scroll inside the modal, while the selected-book action remains easy to reach.

### Chat-driven new-book creation

In local mode, an `init` plan means "create a new library project". It must not
be passed directly to the active MCP child.

The required flow is:

1. Chat produces an `init` argv plan containing the requested title.
2. `NWLocal.runSmart()` recognises the mapped `init` tool.
3. It calls a project-creation coordinator registered by `app.js`.
4. The coordinator calls the local `/api/local/create` route.
5. The backend reserves `<title>_YYYYMMDD[(n)]`, starts the MCP child, and
   initializes that project exactly once.
6. The browser refreshes capabilities, state, files, the header, and the
   library cards.
7. `runSmart()` returns a normal successful result to chat without sending a
   second MCP `init` call.

This routing applies even when another book is active. Starting a new book must
never reset or overwrite the active book's `workflow.json`.

If the title collides, the coordinator pauses the original chat promise and
shows the existing collision dialog with three outcomes:

- `打开上次同名创作`;
- `建立新创作`;
- `取消`.

The promise resolves only after that decision. Cancellation returns a neutral,
human-readable cancellation result rather than a transport failure. Opening an
existing project or creating a copy refreshes the same UI state as normal
creation.

Public Pyodide/replay mode keeps its current in-memory `init` behavior and does
not load or expose the local library coordinator.

## Component boundaries

### `web/local.js`

- Continue to translate argv into MCP tool calls.
- Add a small registration point for an async project-creation coordinator.
- Intercept mapped `init` plans before `prepareSetup()` or `runMcp()`.
- Return the established `{code, out, err}` result shape.
- Contain no dialog or visual DOM logic.

### `web/app.js`

- Own card rendering, current selection, status labels, and button states.
- Own the creation coordinator and collision-decision promise.
- Refresh header, capabilities, files, chat state, and cards after a switch.
- Render user-controlled titles and directory names with `textContent` only.

### `web/index.html`

- Replace the native book `<select>` with a card-list container.
- Group location controls, existing books, primary continuation, and creation
  controls into explicit visual sections.
- Keep the existing dark industrial/terminal visual language; improve spacing,
  hierarchy, focus rings, chips, hover, selected, loading, and empty states
  without redesigning the rest of the application.

### Python launcher and bridge

No state-machine change is required. `/api/local/create`, collision decisions,
book reservation, and MCP-child activation remain the source of truth. Browser
code coordinates these existing operations rather than duplicating them.

## Error handling and safety

- No active book is no longer an error for a local `init` plan.
- Non-`init` MCP operations without an active book still fail explicitly.
- Creation failures keep the modal or chat plan visible and show a concise
  message; they do not silently select another project.
- Collision handling never chooses on the user's behalf.
- Existing books are never overwritten or reinitialized.
- Multiple creation clicks are serialized by the existing local queue and
  disabled while one decision is pending.
- Library paths and book metadata are treated as text, never injected HTML.

## Acceptance criteria

1. With no active book, the local chat flow `开始一本新书` -> `血迹` creates and
   activates `F:\bookworkflow\book\血迹_20260729` (or the approved collision
   suffix) without `transport: no active book`.
2. The project is initialized once, the header shows the active directory, and
   later workflow steps use its real MCP child.
3. Repeating the same title presents the three-way collision decision before
   any new directory is created or existing project is opened.
4. The library modal renders one selectable card per catalog entry, Chinese
   statuses, chapter counts, and directory metadata.
5. Card selection is visible and does not open a book until `继续创作` is used.
6. Loading, empty, selected, success, cancellation, and API-error states are
   legible on desktop and a narrow viewport.
7. The public 8081 page has no local library UI or API access and keeps its
   current in-memory workflow behavior.
8. Browser console errors are empty for the local flow.
9. JavaScript adapter tests, Python launcher/library tests, release checks, and
   the local headless acceptance smoke all pass.

## Verification plan

- Add JavaScript unit coverage for init interception, coordinator success,
  cancellation, collision resolution, and proof that `runMcp(init)` is skipped.
- Extend launcher/UI fixtures where DOM or runtime injection contracts change.
- Use the in-app browser at `http://localhost:8080/` to reproduce the screenshot
  path, create `血迹`, verify the active header and card state, and inspect
  console warnings/errors.
- Reopen the library panel, select an existing card, and continue it.
- Repeat `血迹` to exercise the collision dialog without automatic overwrite.
- Check one narrow viewport for card wrapping, scrolling, focus visibility, and
  reachable primary actions.
- Run the complete Python, JavaScript, release, and local-acceptance suites.

## Non-goals

- A standalone library-management page.
- Deleting or renaming books from the browser.
- Cloudflare/ngrok changes, installer packaging, or automatic updates.
- Redesigning the full chat surface or workflow guide.
- Removing old acceptance projects from the user's library.
