# Task 6 Report: Library dialog recycle and restore UI

## Scope

Implemented the local library recycle/restore UI in the requested files:

- `web/index.html`
- `web/app.js`
- `tests/test_web_launcher.py`

The task report is the only additional file, as requested. No files under `book/` and no plan files were changed.

## Delivered behavior

- The existing-book action area now offers **继续创作** and **移入回收区**.
- A recoverable, local-only 回收区 displays its count, `.trash` location, explanatory permanent-deletion guidance, and restore controls.
- There is no permanent-delete control in the application UI.
- Recycle requires confirmation; cancelling with either the button or Escape clears the pending request.
- Recycle and restore both refresh the visible library and recycle state while leaving the library dialog open.
- Invalid recycle entries remain visible with their error information and never receive a restore button.
- Selection is connected to `NWLibraryTrash` through `visibleBooksByDirectory`.
- Recycling the active book refreshes the library header and files, then clears/reboots the creative workspace through `bootCreativeForActiveBook()`.
- All recycle-list DOM content is constructed with DOM APIs and `textContent`.

## TDD evidence

### RED

Added two static UI/controller contract tests to `WebLibraryPanelAssetTests`, then ran:

    .\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests -v

Result: 21 tests ran; the two new tests failed as expected because the recycle markup, `library-trash.js` load, and controller integration were absent.

- `test_library_panel_has_recoverable_trash_controls`: failed on missing `id="lib-trash-book"`.
- `test_library_controller_integrates_recycle_state`: failed on missing `window.NWLibraryTrash.createController`.

### GREEN

After implementation, ran the requested focused regression commands:

    .\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests tests.test_web_launcher.LocalApiTests -v
    node --test tests\js\test_library_trash.mjs tests\js\test_local_adapter.mjs
    git diff --check

Results:

- Python: 68 tests passed.
- Node: 51 tests passed.
- `git diff --check`: no whitespace errors.

## Self-review and concerns

- Confirmed no permanent-delete button is present; the copy directs users to their local file manager only.
- Confirmed the adapter/controller regression suite covers active-book recycle, refresh, busy state, error visibility, and invalid entries.
- The focused Python run emitted existing `ResourceWarning` messages about unclosed subprocess file handles in `scripts/local_mcp_bridge.py` during one create-book test. The test suite still passed; this task did not modify that code and its requested scope excludes it.
