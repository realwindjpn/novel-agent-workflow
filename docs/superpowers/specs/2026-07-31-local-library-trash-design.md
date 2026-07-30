# Local Library Trash and Restore Design

## Context

The local library can create and open books, but it cannot remove mistaken or
obsolete entries. The approved behavior is recoverable removal: a book is moved
inside the selected library's `.trash` directory, visibly tagged as recycled,
and can be restored from the web UI. If the user later wants permanent removal,
they delete that tagged directory directly from the local file system. The web
application does not expose an irreversible delete endpoint.

This feature is local-mode only. The public static port and Quick Tunnel must
continue to return `404` for every `/api/local/*` route and must never receive a
library token or local path.

## Goals

- Let the user move a selected book out of the normal catalog without losing it.
- Close an active book safely before its directory is moved.
- Show recycled books in a separate collapsible recycle section and restore
  them without overwriting an existing directory.
- Give every recycled directory a durable, human-readable local tag so it can
  be identified and permanently deleted in Explorer if desired.
- Preserve the existing token, same-origin, path-jail, symlink, and public-port
  isolation guarantees.

## Non-goals

- No permanent-delete button or permanent-delete HTTP endpoint.
- No integration with the Windows Recycle Bin.
- No recursive catalog or trash scan.
- No automatic retention period, cleanup job, or storage quota.
- No moving books between different libraries or disk volumes.

## Storage Model

The selected library owns one hidden recycle directory:

```text
<library>/.trash/
  20260731T083015123456Z__雾城回声_20260731/
    .trash-info.json
    workflow.json
    chapters/
    ...
```

The timestamp uses UTC with microseconds. If a destination still collides, a
numeric suffix is appended. The original book directory is moved as a whole on
the same volume; files are never copied individually.

`.trash-info.json` is the recycle tag and contains only local metadata:

```json
{
  "schema_version": 1,
  "original_directory": "雾城回声_20260731",
  "title": "雾城回声",
  "trashed_at": "2026-07-31T08:30:15.123456Z"
}
```

The timestamped directory name is also a visible fallback tag. Metadata is
written only after the move succeeds. If writing the tag fails, the operation
rolls the directory back to its original location and reports an error. On a
successful restore, `.trash-info.json` is removed before the book returns to the
normal catalog.

Because the tag lives inside the recycled directory, manually deleting that
one directory from `.trash` leaves no orphan index entry. A missing or malformed
tag is not trusted for restoration and is shown as an invalid recycle item.

## Library Primitives

`src/novel_workflow/library.py` will define the pure path and metadata layer:

- `TRASH_DIRECTORY = ".trash"` and `TRASH_INFO_FILE = ".trash-info.json"`.
- `TrashEntry`, containing the trash directory ID, original directory, title,
  recycled timestamp, validity, and an optional error.
- `next_trash_directory(library, original_directory, now=None)` for a unique
  immediate-child destination.
- `discover_trash(library)` for a bounded, non-recursive listing.
- `next_restore_directory(library, original_directory)` for collision-safe
  recovery using `原目录名（恢复1）`, `原目录名（恢复2）`, and so on.

`discover_projects()` must explicitly skip `.trash`. This prevents the recycle
directory from appearing as a broken book and removes recycled titles from
same-title collision checks. Both catalog and trash discovery reject symlinks
and resolved paths outside the selected library.

## Session Operations

`LibrarySession` remains the authority for stateful operations and gains:

```python
def trash(self) -> list[TrashEntry]: ...
def trash_book(self, directory: str) -> dict: ...
def restore_book(self, trash_id: str) -> dict: ...
```

Both mutation methods accept only one immediate-child name. They reject empty
strings, `.` / `..`, path separators, `.trash`, missing directories, symlinks,
path escapes, and unreadable project metadata.

### Moving a normal book to trash

1. Validate the selected book and reserve a unique destination under `.trash`.
2. Acquire the existing switch lock.
3. If the selected directory is the active book, close its MCP child before any
   move. The session then has no active book.
4. Move the directory into `.trash` with a same-volume rename.
5. Write `.trash-info.json` atomically as UTF-8 JSON.
6. Return the recycled entry and refreshed catalog/trash data.

If the active child cannot be closed, the move does not start. If the move or
tag write fails, the operation reports an I/O error; a tag-write failure first
attempts to move the directory back. The implementation never deletes files as
part of rollback.

### Restoring a recycled book

1. Validate the trash ID as one immediate child of `<library>/.trash`.
2. Read and validate `.trash-info.json` without following symlinks.
3. Choose the original directory name if free; otherwise choose the first
   `（恢复N）` name that does not exist.
4. Remove the tag and move the directory into the library root.
5. If the move fails after tag removal, restore the same tag in place.
6. Return the restored directory and refreshed catalog/trash data.

Restoration does not automatically open the book. This keeps recovery and MCP
startup separate; the user can select the restored card and click
`继续创作`.

## Local HTTP API

The authenticated local API adds three routes:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/local/trash` | List tagged recycle entries. |
| `POST` | `/api/local/trash` | Move `{ "directory": "..." }` to trash. |
| `POST` | `/api/local/restore` | Restore `{ "trash_id": "..." }`. |

All three routes use the existing random bearer/X-library token and same-origin
checks. Validation failures return the existing structured error envelope. An
attempt to recycle the active book returns success only after the MCP child has
closed and capabilities report `active_directory: null`.

The static public server is not given these handlers. Public acceptance must
verify all three routes return `404`, including requests that copy a local
token.

## Browser Adapter and UI

`web/local.js` adds `listTrash()`, `trashBook(directory)`, and
`restoreBook(trashId)`. They call only the authenticated local bridge and refresh
capabilities after mutations.

The existing library modal changes as follows:

- Selecting a normal book enables `继续创作` and `移入回收区`.
- `移入回收区` opens a confirmation dialog showing the book title, exact
  directory, and the statement that it can be restored.
- Confirmation is explicit; closing or cancelling performs no request.
- After success, the normal list and recycle list refresh together.
- If the recycled book was active, the header returns to `(选一本书)`, the file
  and creative views clear their active-book state, and the library modal stays
  open so the result is visible.
- A collapsible `回收区` section lists tagged entries with a `已回收` chip,
  original directory, recycle time, and `恢复` action.
- The section states the exact `.trash` path and explains that permanent removal
  is done locally by deleting the tagged directory. There is no web permanent
  delete control.
- Restore success refreshes both lists and reports the actual recovered name;
  collision-renamed entries are called out explicitly.

The normal empty state depends only on the normal catalog. Recycled books do not
count toward `N 本创作` and do not block creating a new book with the same title.

## Error Handling

- A failed recycle/restore request leaves the dialog open and displays the
  server message without changing the current selection.
- Double submission is prevented while a mutation is in flight.
- Missing manual-deleted trash directories disappear on the next refresh.
- Invalid tagged entries remain visible as unavailable items with their error;
  the UI does not offer restore for them.
- A failed active-book close aborts recycling before any filesystem mutation.
- No failure path performs recursive deletion.

## Test Strategy

All filesystem tests use temporary libraries; existing user books under
`F:\bookworkflow\book` are never moved or modified.

### Python unit tests

- `.trash` is excluded from `discover_projects()` and same-title matching.
- Trash destinations are unique and restore collisions use `（恢复N）`.
- Trash discovery accepts valid tags and reports missing/malformed tags.
- Recycle moves a normal book and writes the expected tag.
- Recycling the active book closes the exact MCP child first.
- Restore removes the tag, never overwrites, and leaves the book closed.
- Traversal, separators, `.trash`, symlinks, missing books, unreadable projects,
  and paths outside the library are rejected.
- Move/tag failures preserve or roll back the source without deleting data.

### Local API tests

- Token and origin checks cover all new routes.
- List, recycle, active-book recycle, restore, collision restore, and structured
  error responses are verified through the real test HTTP server.
- The public static sibling returns `404` for all new routes.

### Browser tests

- Static asset tests assert confirmation and recycle controls exist only in the
  local library UI.
- Adapter tests verify request method/body, capability refresh, and error
  propagation.
- Controller tests cover selection enablement, cancel-without-request, busy
  state, active-book clearing, refresh after recycle, valid/invalid trash cards,
  restore, and collision-renamed success copy.
- Real browser acceptance covers a temporary book from create through recycle
  and restore, then verifies the public port remains isolated.

## Documentation and Release Checks

`web/README.md`, the main `README.md`, and `CHANGELOG.md` will describe the
recoverable behavior, the `.trash` layout, the manual permanent-delete path, and
the absence of a web permanent-delete endpoint. Final acceptance runs focused
Python and JavaScript suites, the complete test suites, `release_check.py`, and
`git diff --check` before any implementation is considered complete.
