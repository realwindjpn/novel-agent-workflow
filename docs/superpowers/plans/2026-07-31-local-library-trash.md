# Local Library Trash and Restore Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local-only, recoverable library recycle bin that safely moves, tags, lists, and restores books while leaving permanent deletion to the local file system.

**Architecture:** Pure trash naming and discovery live in `novel_workflow.library`; `LibrarySession` owns transactional moves and active MCP shutdown; the authenticated local HTTP bridge exposes list/recycle/restore routes. The browser uses three adapter calls plus a small deterministic state controller, while `app.js` remains responsible for rendering the existing library dialog and clearing active-book UI after a recycle operation.

**Tech Stack:** Python 3.11 standard library (`pathlib`, `datetime`, `json`, `os`, `unittest`), zero-build browser JavaScript, Node `node:test`, native `<dialog>`/`<details>`, existing local token/origin bridge.

---

## File map

- Modify `src/novel_workflow/library.py`: trash constants, metadata model, bounded discovery, collision-safe names, and `.trash` catalog exclusion.
- Modify `scripts/local_mcp_bridge.py`: active-book-safe recycle and restore transactions.
- Modify `scripts/launch_web.py`: authenticated local API routes and JSON serialization.
- Modify `web/local.js`: local transport methods.
- Create `web/library-trash.js`: deterministic recycle controller with no DOM or transport knowledge.
- Modify `web/app.js`: bind the controller to the library dialog and refresh/clear active state.
- Modify `web/index.html`: recycle controls, confirmation dialog, styles, and module script.
- Create `tests/js/test_library_trash.mjs`: controller state and async lifecycle tests.
- Modify `tests/test_library.py`, `tests/test_local_mcp_bridge.py`, `tests/test_web_launcher.py`, and `tests/js/test_local_adapter.mjs`: unit, API, asset, and adapter coverage.
- Regenerate `web/sources.js`: keep the browser snapshot synchronized with `library.py`.
- Modify `README.md`, `web/README.md`, and `CHANGELOG.md`: user-facing behavior and local deletion instructions.

## Invariants used by every task

- Never move or edit a real directory under `F:\bookworkflow\book` during tests or scripted acceptance.
- The web UI never exposes permanent deletion.
- `.trash` is an immediate child of the selected library; trash entries are immediate children of `.trash`.
- Symlinks/junctions, path separators, `.` / `..`, and resolved path escapes are rejected before mutation.
- The public static server remains unaware of every `/api/local/*` handler.
- A restore never overwrites an existing directory.

---

### Task 1: Pure trash paths, tags, and discovery

**Files:**
- Modify: `src/novel_workflow/library.py`
- Modify: `tests/test_library.py`
- Regenerate: `web/sources.js`

- [ ] **Step 1: Write the failing pure-library tests**

Extend the import list in `tests/test_library.py` and add these tests to `LibraryTests`:

```python
from datetime import date, datetime, timezone

from novel_workflow.library import (
    TRASH_DIRECTORY,
    TRASH_INFO_FILE,
    ProjectEntry,
    chapter_artifact_dir,
    discover_projects,
    discover_trash,
    next_book_directory,
    next_restore_directory,
    next_trash_directory,
    safe_component,
)


def test_discover_projects_excludes_trash_directory(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        book = root / "normal"
        book.mkdir()
        (book / "workflow.json").write_text(
            json.dumps({"title": "Normal", "chapters": {}}), encoding="utf-8"
        )
        trash = root / TRASH_DIRECTORY / "tagged"
        trash.mkdir(parents=True)
        (trash / "workflow.json").write_text(
            json.dumps({"title": "Hidden", "chapters": {}}), encoding="utf-8"
        )
        self.assertEqual([e.directory for e in discover_projects(root)], ["normal"])

def test_next_trash_and_restore_directories_are_collision_safe(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        now = datetime(2026, 7, 31, 8, 30, 15, 123456, tzinfo=timezone.utc)
        first = next_trash_directory(root, "雾城回声_20260731", now)
        self.assertEqual(
            first.name,
            "20260731T083015123456Z__雾城回声_20260731",
        )
        first.mkdir(parents=True)
        self.assertEqual(
            next_trash_directory(root, "雾城回声_20260731", now).name,
            first.name + "(1)",
        )
        occupied = root / "雾城回声_20260731"
        occupied.mkdir()
        self.assertEqual(
            next_restore_directory(root, "雾城回声_20260731").name,
            "雾城回声_20260731（恢复1）",
        )

def test_discover_trash_reads_valid_and_invalid_tags(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        valid = root / TRASH_DIRECTORY / "valid-id"
        valid.mkdir(parents=True)
        (valid / TRASH_INFO_FILE).write_text(json.dumps({
            "schema_version": 1,
            "original_directory": "雾城回声_20260731",
            "title": "雾城回声",
            "trashed_at": "2026-07-31T08:30:15.123456Z",
        }, ensure_ascii=False), encoding="utf-8")
        invalid = root / TRASH_DIRECTORY / "invalid-id"
        invalid.mkdir()
        entries = {entry.trash_id: entry for entry in discover_trash(root)}
        self.assertTrue(entries["valid-id"].valid)
        self.assertEqual(entries["valid-id"].original_directory, "雾城回声_20260731")
        self.assertFalse(entries["invalid-id"].valid)
        self.assertIn("missing", entries["invalid-id"].error)
```

- [ ] **Step 2: Run the tests and verify the new imports fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_library.LibraryTests -v
```

Expected: `ImportError` for the new trash constants/functions.

- [ ] **Step 3: Implement the pure library model and helpers**

Add these definitions to `src/novel_workflow/library.py`, importing
`datetime` and `timezone` alongside `date`:

```python
TRASH_DIRECTORY = ".trash"
TRASH_INFO_FILE = ".trash-info.json"


@dataclass(frozen=True)
class TrashEntry:
    trash_id: str
    original_directory: Optional[str]
    title: Optional[str]
    trashed_at: Optional[str]
    valid: bool
    error: Optional[str] = None


def next_trash_directory(
    library: Path,
    original_directory: str,
    now: Optional[datetime] = None,
) -> Path:
    library = Path(library)
    trash_root = library / TRASH_DIRECTORY
    if trash_root.is_symlink():
        raise ValueError("symlinked trash directory is not supported")
    trash_root.mkdir(parents=True, exist_ok=True)
    if _safe_resolve(trash_root, library) is None:
        raise ValueError("trash directory escapes the library")
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    instant = instant.astimezone(timezone.utc)
    stamp = instant.strftime("%Y%m%dT%H%M%S%fZ")
    base = f"{stamp}__{safe_component(original_directory)}"
    candidate = trash_root / base
    counter = 1
    while candidate.exists():
        candidate = trash_root / f"{base}({counter})"
        counter += 1
    return candidate


def next_restore_directory(library: Path, original_directory: str) -> Path:
    library = Path(library)
    base = safe_component(original_directory)
    candidate = library / base
    counter = 1
    while candidate.exists():
        candidate = library / f"{base}（恢复{counter}）"
        counter += 1
    return candidate


def _read_trash_entry(child: Path) -> TrashEntry:
    tag = child / TRASH_INFO_FILE
    if not tag.is_file():
        return TrashEntry(child.name, None, None, None, False, "trash tag missing")
    try:
        data = json.loads(tag.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return TrashEntry(child.name, None, None, None, False, f"trash tag unreadable: {exc}")
    original = data.get("original_directory")
    title = data.get("title")
    trashed_at = data.get("trashed_at")
    if (
        data.get("schema_version") != 1
        or not isinstance(original, str) or not original
        or original in {".", "..", TRASH_DIRECTORY}
        or "/" in original or "\\" in original
        or not isinstance(title, str) or not title
        or not isinstance(trashed_at, str) or not trashed_at
    ):
        return TrashEntry(child.name, None, None, None, False, "trash tag invalid")
    return TrashEntry(child.name, original, title, trashed_at, True, None)


def discover_trash(library: Path) -> list[TrashEntry]:
    library = Path(library)
    trash_root = library / TRASH_DIRECTORY
    if not trash_root.is_dir() or trash_root.is_symlink():
        return []
    entries: list[TrashEntry] = []
    for child in sorted(trash_root.iterdir(), key=lambda p: p.name):
        if not child.is_dir() or child.is_symlink():
            continue
        if _safe_resolve(child, trash_root) is None:
            continue
        entries.append(_read_trash_entry(child))
    entries.sort(key=lambda e: (e.trashed_at or "", e.trash_id), reverse=True)
    return entries
```

In `discover_projects()`, skip the recycle root before resolving it:

```python
for child in sorted(library.iterdir(), key=lambda p: p.name):
    if child.name == TRASH_DIRECTORY:
        continue
    if not child.is_dir() or child.is_symlink():
        continue
```

- [ ] **Step 4: Run the focused tests and regenerate the canonical snapshot**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_library.LibraryTests -v
.\.venv\Scripts\python.exe scripts\gen_web_sources.py
git diff --check
```

Expected: all `LibraryTests` pass; `web/sources.js` changes only because the
canonical `library.py` source changed; `git diff --check` is silent.

- [ ] **Step 5: Commit the pure layer**

```powershell
git add src/novel_workflow/library.py tests/test_library.py web/sources.js
git commit -m "feat: add library trash primitives"
```

---

### Task 2: Transactional LibrarySession recycle and restore

**Files:**
- Modify: `scripts/local_mcp_bridge.py`
- Modify: `tests/test_local_mcp_bridge.py`

- [ ] **Step 1: Add failing session transaction tests**

Import `TRASH_DIRECTORY`, `TRASH_INFO_FILE`, and `datetime/timezone`, then add
these methods to `LibrarySessionTests`:

```python
def _plain_book(self, library: Path, name: str, title: str = "Demo") -> Path:
    book = library / name
    book.mkdir()
    (book / "workflow.json").write_text(
        json.dumps({"title": title, "chapters": {}}), encoding="utf-8"
    )
    return book

def test_trash_book_moves_and_tags_a_closed_book(self):
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp)
        source = self._plain_book(library, "demo_20260731")
        session = LibrarySession(library)
        result = session.trash_book("demo_20260731")
        recycled = library / TRASH_DIRECTORY / result["trash_id"]
        self.assertFalse(source.exists())
        self.assertTrue((recycled / "workflow.json").is_file())
        tag = json.loads((recycled / TRASH_INFO_FILE).read_text(encoding="utf-8"))
        self.assertEqual(tag["original_directory"], "demo_20260731")
        self.assertEqual(tag["title"], "Demo")

def test_trash_active_book_closes_client_before_move(self):
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp)
        source = self._plain_book(library, "demo_20260731")
        events = []

        class ActiveClient:
            root = source
            open = True
            def close(inner_self):
                self.assertTrue(source.exists())
                events.append("closed")
                inner_self.open = False

        session = LibrarySession(library)
        session._client = ActiveClient()
        result = session.trash_book("demo_20260731")
        self.assertEqual(events, ["closed"])
        self.assertIsNone(session.client)
        self.assertTrue(result["was_active"])

def test_restore_book_renames_on_collision_and_removes_tag(self):
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp)
        self._plain_book(library, "demo_20260731")
        session = LibrarySession(library)
        trashed = session.trash_book("demo_20260731")
        self._plain_book(library, "demo_20260731", "Replacement")
        restored = session.restore_book(trashed["trash_id"])
        self.assertEqual(restored["directory"], "demo_20260731（恢复1）")
        self.assertTrue(restored["renamed"])
        target = library / restored["directory"]
        self.assertTrue((target / "workflow.json").is_file())
        self.assertFalse((target / TRASH_INFO_FILE).exists())
        self.assertFalse(session.open)

def test_trash_book_rejects_traversal_and_reserved_root(self):
    with tempfile.TemporaryDirectory() as tmp:
        session = LibrarySession(Path(tmp))
        for value in ("", ".", "..", ".trash", "../book", "a/b", "a\\b"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    session.trash_book(value)

def test_tag_write_failure_rolls_book_back(self):
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp)
        source = self._plain_book(library, "demo_20260731")
        session = LibrarySession(library)
        with patch("scripts.local_mcp_bridge.os.replace", side_effect=OSError("tag failed")):
            with self.assertRaises(OSError):
                session.trash_book("demo_20260731")
        self.assertTrue(source.is_dir())
        self.assertFalse((source / TRASH_INFO_FILE).exists())
```

- [ ] **Step 2: Run the session tests and verify missing methods fail**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_local_mcp_bridge.LibrarySessionTests -v
```

Expected: failures reporting that `trash_book` and `restore_book` do not exist.

- [ ] **Step 3: Implement strict validation and transactional moves**

Expand the `novel_workflow.library` import in `scripts/local_mcp_bridge.py`:

```python
from datetime import datetime, timezone

from novel_workflow.library import (
    TRASH_DIRECTORY,
    TRASH_INFO_FILE,
    ProjectEntry,
    TrashEntry,
    discover_projects,
    discover_trash,
    next_book_directory,
    next_restore_directory,
    next_trash_directory,
)
```

Add these methods to `LibrarySession` before `mcp()`:

```python
def trash(self) -> list[TrashEntry]:
    return discover_trash(self._library)

def _validate_immediate_name(self, value: str, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} is required")
    if value in {".", "..", TRASH_DIRECTORY} or "/" in value or "\\" in value:
        raise ValueError(f"{label} must be an immediate child name")
    return value

def _write_trash_tag(self, recycled: Path, payload: dict) -> None:
    tag = recycled / TRASH_INFO_FILE
    temporary = recycled / f"{TRASH_INFO_FILE}.tmp"
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, tag)
    finally:
        if temporary.exists():
            temporary.unlink()

def trash_book(self, directory: str) -> dict:
    directory = self._validate_immediate_name(directory, label="directory")
    candidate = self._library / directory
    if candidate.is_symlink():
        raise ValueError("symlinked books are not supported")
    source = candidate.resolve()
    try:
        source.relative_to(self._library.resolve())
    except ValueError as exc:
        raise ValueError(f"directory escapes the library: {directory}") from exc
    entries = {entry.directory: entry for entry in self.catalog()}
    entry = entries.get(directory)
    if entry is None:
        raise ValueError(f"book directory missing: {directory}")
    if not entry.valid:
        raise ValueError(entry.error or f"invalid book: {directory}")
    if (source / TRASH_INFO_FILE).exists():
        raise ValueError(f"reserved trash tag already exists in {directory}")

    now = datetime.now(timezone.utc)
    destination = next_trash_directory(self._library, directory, now)
    tag = {
        "schema_version": 1,
        "original_directory": directory,
        "title": entry.title,
        "trashed_at": now.isoformat().replace("+00:00", "Z"),
    }
    with self._switch_lock:
        was_active = bool(
            self._client is not None
            and self._client.root.resolve() == source
        )
        if was_active:
            client = self._client
            client.close()
            self._client = None
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
        try:
            self._write_trash_tag(destination, tag)
        except Exception:
            destination.rename(source)
            raise
    return {
        "status": "trashed",
        "trash_id": destination.name,
        "original_directory": directory,
        "title": entry.title,
        "trashed_at": tag["trashed_at"],
        "was_active": was_active,
    }

def restore_book(self, trash_id: str) -> dict:
    trash_id = self._validate_immediate_name(trash_id, label="trash_id")
    trash_root = self._library / TRASH_DIRECTORY
    if trash_root.is_symlink():
        raise ValueError("symlinked trash directory is not supported")
    candidate = trash_root / trash_id
    if candidate.is_symlink():
        raise ValueError("symlinked trash entries are not supported")
    source = candidate.resolve()
    try:
        source.relative_to(trash_root.resolve())
    except ValueError as exc:
        raise ValueError(f"trash entry escapes the library: {trash_id}") from exc
    entries = {entry.trash_id: entry for entry in self.trash()}
    entry = entries.get(trash_id)
    if entry is None:
        raise ValueError(f"trash entry missing: {trash_id}")
    if not entry.valid or entry.original_directory is None:
        raise ValueError(entry.error or f"invalid trash entry: {trash_id}")
    if not (source / "workflow.json").is_file():
        raise ValueError(f"workflow.json missing in trash entry: {trash_id}")

    destination = next_restore_directory(self._library, entry.original_directory)
    original_tag = (source / TRASH_INFO_FILE).read_bytes()
    with self._switch_lock:
        (source / TRASH_INFO_FILE).unlink()
        try:
            source.rename(destination)
        except Exception:
            (source / TRASH_INFO_FILE).write_bytes(original_tag)
            raise
    return {
        "status": "restored",
        "trash_id": trash_id,
        "directory": destination.name,
        "renamed": destination.name != entry.original_directory,
    }
```

- [ ] **Step 4: Add concrete close, symlink, and restore-rollback tests**

Add these methods to `LibrarySessionTests`:

```python
def test_failed_active_close_aborts_before_move(self):
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp)
        source = self._plain_book(library, "demo_20260731")

        class FailingClient:
            root = source
            open = True
            def close(inner_self):
                raise RuntimeError("close failed")

        session = LibrarySession(library)
        session._client = FailingClient()
        with self.assertRaisesRegex(RuntimeError, "close failed"):
            session.trash_book("demo_20260731")
        self.assertTrue(source.is_dir())
        trash_root = library / TRASH_DIRECTORY
        self.assertFalse(trash_root.exists() and any(trash_root.iterdir()))

def test_trash_book_rejects_symlinked_book(self):
    if not _symlink_supported():
        self.skipTest("symlinks not supported on this platform")
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp) / "library"
        library.mkdir()
        outside = Path(tmp) / "outside"
        outside.mkdir()
        (outside / "workflow.json").write_text("{}", encoding="utf-8")
        (library / "linked").symlink_to(outside, target_is_directory=True)
        session = LibrarySession(library)
        with self.assertRaisesRegex(ValueError, "symlink"):
            session.trash_book("linked")
        self.assertTrue(outside.is_dir())

def test_restore_rejects_traversal_and_symlinked_trash_entry(self):
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp) / "library"
        library.mkdir()
        session = LibrarySession(library)
        for value in ("", ".", "..", ".trash", "../book", "a/b", "a\\b"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    session.restore_book(value)
        if _symlink_supported():
            outside = Path(tmp) / "outside"
            outside.mkdir()
            trash_root = library / TRASH_DIRECTORY
            trash_root.mkdir()
            (trash_root / "linked").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                session.restore_book("linked")

def test_trash_move_failure_preserves_source(self):
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp)
        source = self._plain_book(library, "demo_20260731")
        session = LibrarySession(library)
        original_rename = Path.rename

        def fail_first_move(path, target):
            if path == source:
                raise OSError("trash move failed")
            return original_rename(path, target)

        with patch.object(Path, "rename", fail_first_move):
            with self.assertRaisesRegex(OSError, "trash move failed"):
                session.trash_book("demo_20260731")
        self.assertTrue(source.is_dir())
        self.assertFalse((source / TRASH_INFO_FILE).exists())

def test_restore_failure_recreates_original_tag(self):
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp)
        self._plain_book(library, "demo_20260731")
        session = LibrarySession(library)
        moved = session.trash_book("demo_20260731")
        recycled = library / TRASH_DIRECTORY / moved["trash_id"]
        expected = (recycled / TRASH_INFO_FILE).read_bytes()
        original_rename = Path.rename

        def fail_restore(path, target):
            if path == recycled:
                raise OSError("restore move failed")
            return original_rename(path, target)

        with patch.object(Path, "rename", fail_restore):
            with self.assertRaisesRegex(OSError, "restore move failed"):
                session.restore_book(moved["trash_id"])
        self.assertEqual((recycled / TRASH_INFO_FILE).read_bytes(), expected)
        self.assertFalse((library / "demo_20260731").exists())
```

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_library tests.test_local_mcp_bridge -v
git diff --check
```

Expected: both modules pass and the diff check is silent.

- [ ] **Step 5: Commit the stateful session layer**

```powershell
git add scripts/local_mcp_bridge.py tests/test_local_mcp_bridge.py
git commit -m "feat: recycle and restore library books"
```

---

### Task 3: Authenticated local API routes

**Files:**
- Modify: `scripts/launch_web.py`
- Modify: `tests/test_web_launcher.py`

- [ ] **Step 1: Add failing end-to-end local API tests**

Add a helper to `LocalApiTests`:

```python
def _auth_headers(self, *, origin=True):
    headers = {"Authorization": f"Bearer {self.token}"}
    if origin:
        headers["Origin"] = f"http://localhost:{self.port}"
    return headers
```

Then add:

```python
def test_trash_routes_list_recycle_and_restore(self):
    status, moved = self._request(
        "POST", "/api/local/trash",
        headers=self._auth_headers(),
        body={"directory": "demo_20260728"},
    )
    self.assertEqual(status, 200)
    self.assertEqual(moved["status"], "trashed")
    self.assertFalse((self.library / "demo_20260728").exists())

    status, listed = self._request(
        "GET", "/api/local/trash", headers=self._auth_headers()
    )
    self.assertEqual(status, 200)
    self.assertEqual(listed["trash"][0]["trash_id"], moved["trash_id"])
    self.assertTrue(listed["trash"][0]["valid"])

    status, restored = self._request(
        "POST", "/api/local/restore",
        headers=self._auth_headers(),
        body={"trash_id": moved["trash_id"]},
    )
    self.assertEqual(status, 200)
    self.assertEqual(restored["status"], "restored")
    self.assertTrue((self.library / restored["directory"]).is_dir())

def test_trash_active_book_clears_capabilities(self):
    self._request(
        "POST", "/api/local/open",
        headers=self._auth_headers(),
        body={"directory": "demo_20260728"},
    )
    status, moved = self._request(
        "POST", "/api/local/trash",
        headers=self._auth_headers(),
        body={"directory": "demo_20260728"},
    )
    self.assertEqual(status, 200)
    self.assertTrue(moved["was_active"])
    status, capabilities = self._request(
        "GET", "/api/local/capabilities",
        headers={"Authorization": f"Bearer {self.token}"},
    )
    self.assertEqual(status, 200)
    self.assertIsNone(capabilities["active_directory"])

def test_trash_routes_require_authentication(self):
    for method, path, body in (
        ("GET", "/api/local/trash", None),
        ("POST", "/api/local/trash", {"directory": "demo_20260728"}),
        ("POST", "/api/local/restore", {"trash_id": "x"}),
    ):
        with self.subTest(method=method, path=path):
            status, response = self._request(method, path, body=body)
            self.assertEqual(status, 401)
            self.assertEqual(response["error"]["code"], "unauthorized")

def test_public_server_has_no_trash_routes(self):
    for method, path, body in (
        ("GET", "/api/local/trash", None),
        ("POST", "/api/local/trash", {"directory": "demo_20260728"}),
        ("POST", "/api/local/restore", {"trash_id": "x"}),
    ):
        status, _ = self._request(
            method, path, port=self.public_port,
            headers={"Authorization": f"Bearer {self.token}"}, body=body,
        )
        self.assertEqual(status, 404)
```

- [ ] **Step 2: Run the API tests and verify `404` on the new local routes**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.LocalApiTests -v
```

Expected: the new authenticated route test fails with `404` while existing tests
remain green.

- [ ] **Step 3: Add route dispatch and serialization**

Add these branches in `LocalApi.handle()` after the existing library routes:

```python
elif route == ("GET", "trash"):
    self._serve_trash(handler)
elif route == ("POST", "trash"):
    self._serve_trash_book(handler)
elif route == ("POST", "restore"):
    self._serve_restore_book(handler)
```

Add these methods next to `_serve_library()`:

```python
@staticmethod
def _trash_json(entry) -> dict:
    return {
        "trash_id": entry.trash_id,
        "original_directory": entry.original_directory,
        "title": entry.title,
        "trashed_at": entry.trashed_at,
        "valid": entry.valid,
        "error": entry.error,
    }

def _serve_trash(self, handler: BaseHTTPRequestHandler) -> None:
    self._send_json(handler, 200, {
        "library": str(self._session.library),
        "trash": [self._trash_json(entry) for entry in self._session.trash()],
    })

def _serve_trash_book(self, handler: BaseHTTPRequestHandler) -> None:
    body = self._read_json(handler)
    directory = body.get("directory")
    if not isinstance(directory, str) or not directory:
        self._send_error(handler, 400, "bad_request", "directory is required.")
        return
    self._send_json(handler, 200, self._session.trash_book(directory))

def _serve_restore_book(self, handler: BaseHTTPRequestHandler) -> None:
    body = self._read_json(handler)
    trash_id = body.get("trash_id")
    if not isinstance(trash_id, str) or not trash_id:
        self._send_error(handler, 400, "bad_request", "trash_id is required.")
        return
    self._send_json(handler, 200, self._session.restore_book(trash_id))
```

- [ ] **Step 4: Add origin, malformed body, collision restore, and invalid-tag tests**

Add these methods to `LocalApiTests`:

```python
def test_trash_rejects_foreign_origin_and_empty_body(self):
    status, body = self._request(
        "POST", "/api/local/trash",
        headers={
            "Origin": "http://evil.example",
            "Authorization": f"Bearer {self.token}",
        },
        body={"directory": "demo_20260728"},
    )
    self.assertEqual(status, 403)
    self.assertEqual(body["error"]["code"], "origin_rejected")
    status, body = self._request(
        "POST", "/api/local/trash",
        headers=self._auth_headers(), body={},
    )
    self.assertEqual(status, 400)
    self.assertEqual(body["error"]["code"], "bad_request")

def test_restore_collision_uses_recovery_suffix(self):
    status, moved = self._request(
        "POST", "/api/local/trash",
        headers=self._auth_headers(), body={"directory": "demo_20260728"},
    )
    self.assertEqual(status, 200)
    replacement = self.library / "demo_20260728"
    replacement.mkdir()
    (replacement / "workflow.json").write_text(
        json.dumps({"title": "replacement", "chapters": {}}), encoding="utf-8"
    )
    status, restored = self._request(
        "POST", "/api/local/restore",
        headers=self._auth_headers(), body={"trash_id": moved["trash_id"]},
    )
    self.assertEqual(status, 200)
    self.assertEqual(restored["directory"], "demo_20260728（恢复1）")
    self.assertTrue(restored["renamed"])

def test_invalid_trash_tag_is_listed_but_cannot_restore(self):
    invalid = self.library / ".trash" / "invalid-id"
    invalid.mkdir(parents=True)
    (invalid / "workflow.json").write_text("{}", encoding="utf-8")
    status, listed = self._request(
        "GET", "/api/local/trash", headers=self._auth_headers()
    )
    self.assertEqual(status, 200)
    item = next(entry for entry in listed["trash"] if entry["trash_id"] == "invalid-id")
    self.assertFalse(item["valid"])
    status, body = self._request(
        "POST", "/api/local/restore",
        headers=self._auth_headers(), body={"trash_id": "invalid-id"},
    )
    self.assertEqual(status, 400)
    self.assertEqual(body["error"]["code"], "bad_request")
```

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.LocalApiTests -v
```

Expected: all `LocalApiTests` pass, including the public `404` assertions.

- [ ] **Step 5: Commit the local API**

```powershell
git add scripts/launch_web.py tests/test_web_launcher.py
git commit -m "feat: expose local recycle bin API"
```

---

### Task 4: Browser local transport adapter

**Files:**
- Modify: `web/local.js`
- Modify: `tests/js/test_local_adapter.mjs`

- [ ] **Step 1: Add failing adapter request tests**

Add these tests after the existing local-library adapter tests:

```javascript
test("listTrash calls authenticated GET trash", async () => {
  const calls = [];
  const NWL = loadLocalWithFetch(
    { apiBase: "/api/local", token: "tk-test" },
    (url, opts) => {
      calls.push({ url, opts });
      return Promise.resolve({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ library: "C:\\Books", trash: [] }))
      });
    }
  );
  const result = await NWL.listTrash();
  assert.equal(calls[0].url, "/api/local/trash");
  assert.equal(calls[0].opts.method, "GET");
  assert.equal(calls[0].opts.headers.Authorization, "Bearer tk-test");
  assert.equal(result.trash.length, 0);
});

test("trashBook posts directory then refreshes capabilities", async () => {
  const calls = [];
  const NWL = loadLocalWithFetch(
    { apiBase: "/api/local", token: "tk-test" },
    (url, opts) => {
      calls.push({ url, opts });
      const body = url.endsWith("/trash")
        ? { status: "trashed", trash_id: "t1", was_active: true }
        : { library: "C:\\Books", active_directory: null };
      return Promise.resolve({ ok: true, text: () => Promise.resolve(JSON.stringify(body)) });
    }
  );
  const result = await NWL.trashBook("demo_20260731");
  assert.equal(calls[0].url, "/api/local/trash");
  assert.equal(calls[0].opts.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].opts.body), { directory: "demo_20260731" });
  assert.equal(calls[1].url, "/api/local/capabilities");
  assert.equal(result.trash_id, "t1");
  assert.equal(NWL.capabilities.active_directory, null);
});

test("restoreBook posts trash_id and propagates structured errors", async () => {
  const NWL = loadLocalWithFetch(
    { apiBase: "/api/local", token: "tk-test" },
    () => Promise.resolve({
      ok: false,
      status: 400,
      text: () => Promise.resolve(JSON.stringify({
        error: { code: "bad_request", message: "invalid trash entry" }
      }))
    })
  );
  await assert.rejects(
    NWL.restoreBook("bad"),
    (error) => error.code === "bad_request" && error.status === 400
  );
});
```

- [ ] **Step 2: Run the adapter tests and verify methods are missing**

```powershell
node --test tests\js\test_local_adapter.mjs
```

Expected: failures saying `listTrash`, `trashBook`, and `restoreBook` are not
functions.

- [ ] **Step 3: Implement and export the adapter methods**

Add beside `listBooks()` in `web/local.js`:

```javascript
function listTrash() {
  if (!active) return Promise.resolve({ library: "", trash: [] });
  return callApi("trash");
}

function trashBook(directory) {
  if (!active) return Promise.reject(new Error("local library not active"));
  return callApi("trash", { method: "POST", body: { directory: directory } })
    .then(function (result) {
      return refreshCapabilities().then(function () { return result; });
    });
}

function restoreBook(trashId) {
  if (!active) return Promise.reject(new Error("local library not active"));
  return callApi("restore", { method: "POST", body: { trash_id: trashId } })
    .then(function (result) {
      return refreshCapabilities().then(function () { return result; });
    });
}
```

Add `listTrash`, `trashBook`, and `restoreBook` to the exported `api` object.

- [ ] **Step 4: Run adapter and existing routing tests**

```powershell
node --test tests\js\test_local_adapter.mjs tests\js\test_chat_routing.mjs
```

Expected: both files pass.

- [ ] **Step 5: Commit the adapter**

```powershell
git add web/local.js tests/js/test_local_adapter.mjs
git commit -m "feat: add browser recycle transport"
```

---

### Task 5: Deterministic recycle state controller

**Files:**
- Create: `web/library-trash.js`
- Create: `tests/js/test_library_trash.mjs`

- [ ] **Step 1: Create failing controller lifecycle tests**

Create `tests/js/test_library_trash.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import vm from "node:vm";

const __dirname = dirname(fileURLToPath(import.meta.url));

function loadApi() {
  const source = readFileSync(resolve(__dirname, "..", "..", "web", "library-trash.js"), "utf8");
  const moduleObj = { exports: {} };
  const sandbox = { module: moduleObj, exports: moduleObj.exports, window: {}, console };
  vm.createContext(sandbox);
  vm.runInContext(source, sandbox, { filename: "web/library-trash.js" });
  return moduleObj.exports;
}

test("selection and cancel never call the transport", async () => {
  const calls = [];
  const states = [];
  const controller = loadApi().createController({
    listTrash: async () => ({ library: "C:\\Books", trash: [] }),
    trashBook: async (directory) => calls.push(directory),
    restoreBook: async () => {},
    onChange: (state) => states.push(state),
    onMutation: async () => {},
  });
  controller.select({ directory: "demo", title: "Demo" });
  controller.requestTrash();
  assert.equal(controller.snapshot().pending.directory, "demo");
  controller.cancelTrash();
  assert.equal(controller.snapshot().pending, null);
  assert.deepEqual(calls, []);
  assert.equal(states.at(-1).busy, false);
});

test("confirmed recycle is busy, forwards result, refreshes, and clears selection", async () => {
  let release;
  const mutations = [];
  const controller = loadApi().createController({
    listTrash: async () => ({ library: "C:\\Books", trash: [{ trash_id: "t1", valid: true }] }),
    trashBook: () => new Promise((resolve) => { release = resolve; }),
    restoreBook: async () => {},
    onChange: () => {},
    onMutation: async (result, kind) => mutations.push({ result, kind }),
  });
  controller.select({ directory: "demo", title: "Demo" });
  controller.requestTrash();
  const pending = controller.confirmTrash();
  assert.equal(controller.snapshot().busy, true);
  release({ status: "trashed", trash_id: "t1", was_active: true });
  const result = await pending;
  assert.equal(result.trash_id, "t1");
  assert.equal(controller.snapshot().busy, false);
  assert.equal(controller.snapshot().selected, null);
  assert.equal(controller.snapshot().trash.length, 1);
  assert.equal(mutations[0].kind, "trash");
  assert.equal(mutations[0].result.was_active, true);
});

test("restore errors remain visible and always clear busy", async () => {
  const controller = loadApi().createController({
    listTrash: async () => ({ library: "C:\\Books", trash: [] }),
    trashBook: async () => {},
    restoreBook: async () => { throw new Error("restore failed"); },
    onChange: () => {},
    onMutation: async () => {},
  });
  await assert.rejects(controller.restore("t1"), /restore failed/);
  assert.equal(controller.snapshot().busy, false);
  assert.equal(controller.snapshot().error, "restore failed");
});
```

- [ ] **Step 2: Run the test and verify the module is absent**

```powershell
node --test tests\js\test_library_trash.mjs
```

Expected: `ENOENT` for `web/library-trash.js`.

- [ ] **Step 3: Implement the transport-agnostic controller**

Create `web/library-trash.js`:

```javascript
(function () {
  "use strict";

  function cloneState(state) {
    return {
      library: state.library,
      trash: state.trash.slice(),
      selected: state.selected,
      pending: state.pending,
      busy: state.busy,
      error: state.error,
    };
  }

  function createController(options) {
    var state = {
      library: "", trash: [], selected: null,
      pending: null, busy: false, error: ""
    };

    function emit() {
      if (options.onChange) options.onChange(cloneState(state));
    }

    function snapshot() { return cloneState(state); }

    function select(book) {
      if (state.busy) return snapshot();
      state.selected = book || null;
      emit();
      return snapshot();
    }

    function requestTrash() {
      if (state.busy || !state.selected) return snapshot();
      state.pending = state.selected;
      state.error = "";
      emit();
      return snapshot();
    }

    function cancelTrash() {
      if (!state.busy) state.pending = null;
      emit();
      return snapshot();
    }

    function refresh() {
      return Promise.resolve(options.listTrash()).then(function (payload) {
        state.library = payload && payload.library ? payload.library : "";
        state.trash = payload && Array.isArray(payload.trash) ? payload.trash.slice() : [];
        state.error = "";
        emit();
        return snapshot();
      }).catch(function (error) {
        state.error = (error && error.message) || String(error);
        emit();
        throw error;
      });
    }

    function runMutation(kind, operation) {
      if (state.busy) return Promise.reject(new Error("recycle operation already running"));
      state.busy = true;
      state.error = "";
      emit();
      return Promise.resolve(operation()).then(function (result) {
        return Promise.resolve(options.onMutation ? options.onMutation(result, kind) : null)
          .then(function () { return refresh(); })
          .then(function () { return result; });
      }).catch(function (error) {
        state.error = (error && error.message) || String(error);
        emit();
        throw error;
      }).finally(function () {
        state.busy = false;
        emit();
      });
    }

    function confirmTrash() {
      if (!state.pending) return Promise.reject(new Error("no book selected for recycle"));
      var directory = state.pending.directory;
      state.pending = null;
      return runMutation("trash", function () {
        return options.trashBook(directory);
      }).then(function (result) {
        state.selected = null;
        emit();
        return result;
      });
    }

    function restore(trashId) {
      return runMutation("restore", function () {
        return options.restoreBook(trashId);
      });
    }

    emit();
    return {
      snapshot: snapshot,
      select: select,
      requestTrash: requestTrash,
      cancelTrash: cancelTrash,
      confirmTrash: confirmTrash,
      restore: restore,
      refresh: refresh,
    };
  }

  var api = { createController: createController };
  if (typeof window !== "undefined") window.NWLibraryTrash = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
```

- [ ] **Step 4: Add duplicate-submit and invalid-item tests, then run the suite**

Append these tests to `tests/js/test_library_trash.mjs`:

```javascript
test("a second mutation is rejected while recycle is running", async () => {
  let release;
  const controller = loadApi().createController({
    listTrash: async () => ({ library: "C:\\Books", trash: [] }),
    trashBook: () => new Promise((resolve) => { release = resolve; }),
    restoreBook: async () => ({ status: "restored" }),
    onChange: () => {},
    onMutation: async () => {},
  });
  controller.select({ directory: "demo", title: "Demo" });
  controller.requestTrash();
  const first = controller.confirmTrash();
  await assert.rejects(controller.restore("t1"), /already running/);
  release({ status: "trashed", trash_id: "t1" });
  await first;
});

test("refresh preserves invalid items for unavailable UI rendering", async () => {
  let restoreCalls = 0;
  const controller = loadApi().createController({
    listTrash: async () => ({
      library: "C:\\Books",
      trash: [{ trash_id: "bad", valid: false, error: "trash tag missing" }],
    }),
    trashBook: async () => {},
    restoreBook: async () => { restoreCalls += 1; },
    onChange: () => {},
    onMutation: async () => {},
  });
  await controller.refresh();
  assert.equal(controller.snapshot().trash[0].valid, false);
  assert.equal(controller.snapshot().trash[0].error, "trash tag missing");
  assert.equal(restoreCalls, 0);
});
```

Run:

```powershell
node --test tests\js\test_library_trash.mjs
```

Expected: all controller tests pass.

- [ ] **Step 5: Commit the controller**

```powershell
git add web/library-trash.js tests/js/test_library_trash.mjs
git commit -m "feat: add recycle bin state controller"
```

---

### Task 6: Library dialog recycle and restore UI

**Files:**
- Modify: `web/index.html`
- Modify: `web/app.js`
- Modify: `tests/test_web_launcher.py`

- [ ] **Step 1: Add failing static UI contract tests**

Add to `WebLibraryPanelAssetTests`:

```python
def test_library_panel_has_recoverable_trash_controls(self):
    self.assertIn('id="lib-trash-book"', self.html)
    self.assertIn('id="lib-trash-list"', self.html)
    self.assertIn('id="lib-trash-path"', self.html)
    self.assertIn('id="lib-trash-confirm"', self.html)
    self.assertIn('id="lib-trash-apply"', self.html)
    self.assertIn('id="lib-trash-cancel"', self.html)
    self.assertIn('回收区', self.html)
    self.assertIn('本地永久删除', self.html)
    self.assertNotIn('永久删除</button>', self.html)
    self.assertIn('<script src="library-trash.js"></script>', self.html)

def test_library_controller_integrates_recycle_state(self):
    self.assertIn('window.NWLibraryTrash.createController', self.app_js)
    self.assertIn('window.NWLocal.listTrash', self.app_js)
    self.assertIn('window.NWLocal.trashBook', self.app_js)
    self.assertIn('window.NWLocal.restoreBook', self.app_js)
    self.assertIn('was_active', self.app_js)
```

- [ ] **Step 2: Run the asset tests and verify missing controls fail**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests -v
```

Expected: both new tests fail because the markup and integration are absent.

- [ ] **Step 3: Add accessible markup and local-only explanatory copy**

In the existing-book section of `web/index.html`, replace the single primary
button with:

```html
<div class="lib-book-actions">
  <button type="button" class="primary lib-primary-action"
          id="lib-open" disabled>继续创作</button>
  <button type="button" class="danger lib-primary-action"
          id="lib-trash-book" disabled>移入回收区</button>
</div>
```

Insert after that section:

```html
<details id="lib-trash-section" class="lib-location lib-trash-section">
  <summary>
    <span>回收区</span>
    <span id="lib-trash-count" class="lib-count">0 本已回收</span>
  </summary>
  <div class="lib-location-body">
    <p class="lib-trash-help">
      可在这里恢复。需要本地永久删除时，请在资源管理器删除
      <code id="lib-trash-path">.trash</code> 中对应的已标记目录。
    </p>
    <div id="lib-trash-list" class="lib-book-list" aria-label="回收区列表"></div>
  </div>
</details>
```

Insert a sibling confirmation dialog after `lib-collision`:

```html
<dialog id="lib-trash-confirm" class="lib-dialog" aria-labelledby="lib-trash-confirm-title">
  <div class="lib-dialog-inner">
    <div class="lib-dialog-head"><h2 id="lib-trash-confirm-title">移入回收区</h2></div>
    <p id="lib-trash-confirm-text" class="lib-dialog-status"></p>
    <div class="lib-dialog-actions">
      <button type="button" class="danger" id="lib-trash-apply">确认移入</button>
      <button type="button" id="lib-trash-cancel">取消</button>
    </div>
  </div>
</dialog>
```

Add styles:

```css
.lib-book-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.lib-dialog button.danger { border-color: #8a3946; background: #2a1118; color: #ff9eaa; }
.lib-trash-section .lib-location-body { gap: 12px; }
.lib-trash-help { margin: 0; color: var(--dim); font-size: 10px; line-height: 1.6; }
.lib-trash-help code { color: var(--ink); overflow-wrap: anywhere; }
.lib-trash-card { cursor: default !important; }
.lib-trash-card .lib-dialog-actions { grid-column: 1 / -1; }
```

Load `library-trash.js` after `local.js` and before `app.js`.

- [ ] **Step 4: Bind selection, confirmation, rendering, and mutation refresh**

In `web/app.js`, cache the new elements and maintain `visibleBooksByDirectory`.
When `renderBookList()` receives books, populate that map. Extend
`selectBookCard()` so it calls `trashController.select(book)` and disables the
move button when there is no selection.

Create the controller after the element declarations:

```javascript
var trashController = window.NWLibraryTrash.createController({
  listTrash: function () { return window.NWLocal.listTrash(); },
  trashBook: function (directory) { return window.NWLocal.trashBook(directory); },
  restoreBook: function (trashId) { return window.NWLocal.restoreBook(trashId); },
  onChange: renderTrashState,
  onMutation: function (result, kind) {
    return window.NWLocal.listBooks().then(function (payload) {
      renderBookList(payload);
      refreshLibPanel();
      if (kind === "trash" && result && result.was_active) {
        return refreshFiles().then(function () {
          return bootCreativeForActiveBook();
        });
      }
      return null;
    });
  }
});
```

Implement `renderTrashState(state)` with DOM creation only through
`textContent`:

```javascript
function renderTrashState(state) {
  libTrashBookBtn.disabled = state.busy || !state.selected;
  libTrashApplyBtn.disabled = state.busy || !state.pending;
  libTrashCancelBtn.disabled = state.busy;
  libTrashCount.textContent = state.trash.length + " 本已回收";
  libTrashPath.textContent = state.library ? state.library + "\\.trash" : ".trash";
  libTrashList.replaceChildren();
  state.trash.forEach(function (entry) {
    var card = document.createElement("div");
    card.className = "lib-book-card lib-trash-card";
    var title = document.createElement("span");
    title.className = "lib-book-title";
    title.textContent = entry.title || entry.original_directory || entry.trash_id;
    var chip = document.createElement("span");
    chip.className = "lib-status-chip";
    chip.textContent = entry.valid ? "已回收" : "标签无效";
    var meta = document.createElement("span");
    meta.className = "lib-book-meta";
    meta.textContent = entry.valid
      ? (entry.original_directory + " · " + entry.trashed_at)
      : (entry.error || "无法读取回收标签");
    card.append(title, chip, meta);
    if (entry.valid) {
      var actions = document.createElement("div");
      actions.className = "lib-dialog-actions";
      var restore = document.createElement("button");
      restore.type = "button";
      restore.dataset.trashId = entry.trash_id;
      restore.textContent = "恢复";
      restore.disabled = state.busy;
      actions.appendChild(restore);
      card.appendChild(actions);
    }
    libTrashList.appendChild(card);
  });
  if (state.pending && !libTrashConfirm.open) {
    libTrashConfirmText.textContent =
      "将《" + (state.pending.title || state.pending.directory) + "》(" +
      state.pending.directory + ") 移入可恢复回收区？";
    libTrashConfirm.showModal();
  }
  if (!state.pending && libTrashConfirm.open && !state.busy) libTrashConfirm.close();
  if (state.error) setLibStatus(state.error, true);
}
```

Bind events:

```javascript
libTrashBookBtn.addEventListener("click", function () { trashController.requestTrash(); });
libTrashCancelBtn.addEventListener("click", function () { trashController.cancelTrash(); });
libTrashApplyBtn.addEventListener("click", function () {
  trashController.confirmTrash().then(function (result) {
    setLibStatus("已移入回收区：" + result.original_directory, false);
  }).catch(function (error) { setLibStatus(error.message || error, true); });
});
libTrashList.addEventListener("click", function (event) {
  var button = event.target.closest("button[data-trash-id]");
  if (!button) return;
  trashController.restore(button.dataset.trashId).then(function (result) {
    setLibStatus(
      result.renamed ? "已恢复并改名：" + result.directory : "已恢复：" + result.directory,
      false
    );
  }).catch(function (error) { setLibStatus(error.message || error, true); });
});
```

Call `trashController.refresh()` in `loadLibraryDialog()`, after library path
changes, and after manual refresh. Keep the modal open after recycle/restore.

- [ ] **Step 5: Run UI, adapter, and API regression tests**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests tests.test_web_launcher.LocalApiTests -v
node --test tests\js\test_library_trash.mjs tests\js\test_local_adapter.mjs
git diff --check
```

Expected: all focused Python/JavaScript tests pass and the diff check is silent.

- [ ] **Step 6: Commit the UI integration**

```powershell
git add web/index.html web/app.js tests/test_web_launcher.py
git commit -m "feat: add library recycle bin UI"
```

---

### Task 7: Documentation, generated-source audit, and focused acceptance

**Files:**
- Modify: `README.md`
- Modify: `web/README.md`
- Modify: `CHANGELOG.md`
- Verify: `web/sources.js`

- [ ] **Step 1: Document the exact recoverable behavior**

Add a `Local recycle bin` subsection to the local-library sections of both
READMEs with this content:

```markdown
### Local recycle bin

In the local library dialog, select a book and choose **移入回收区**. The local
launcher closes that book's MCP child if it is active, then moves the complete
directory to `<library>/.trash/<timestamp>__<original-directory>` and writes a
UTF-8 `.trash-info.json` tag. Recycled books are excluded from the normal
catalog and same-title checks.

Expand **回收区** to restore a book. Restore never overwrites an existing
directory; a collision becomes `原目录名（恢复1）`, then `（恢复2）`, and so on.
The web UI has no permanent-delete action. To remove a recycled book forever,
delete its tagged directory directly from `<library>/.trash` in the local file
system. The public Quick Tunnel cannot list, recycle, restore, or delete books.
```

Add under `## Unreleased` in `CHANGELOG.md`:

```markdown
- Added a local-only recoverable library recycle bin. Books are moved into a
  tagged `.trash` directory, active MCP children close before the move, restores
  never overwrite an existing directory, and permanent deletion remains an
  explicit local-file-system action. Public static/tunnel routes stay isolated.
```

- [ ] **Step 2: Verify snapshot and focused suites**

Run:

```powershell
.\.venv\Scripts\python.exe scripts\gen_web_sources.py
git diff --exit-code -- web/sources.js
.\.venv\Scripts\python.exe -m unittest tests.test_library tests.test_local_mcp_bridge tests.test_web_launcher -v
node --test tests\js\test_library_trash.mjs tests\js\test_local_adapter.mjs
git diff --check
```

Expected: the generator produces no new diff, all focused suites pass, and
`git diff --check` is silent.

- [ ] **Step 3: Commit documentation**

```powershell
git add README.md web/README.md CHANGELOG.md
git commit -m "docs: explain local library recycle bin"
```

---

### Task 8: Full regression, real temporary-library acceptance, and plan completion

**Files:**
- Modify if a defect is found: only files already named in Tasks 1-7
- Modify after all checks pass: `docs/superpowers/plans/2026-07-31-local-library-trash.md`

- [ ] **Step 1: Run all JavaScript tests**

```powershell
$failed = $false
Get-ChildItem tests\js\test_*.mjs | ForEach-Object {
  node --test $_.FullName
  if ($LASTEXITCODE -ne 0) { $failed = $true }
}
if ($failed) { exit 1 }
```

Expected: every JavaScript test file passes.

- [ ] **Step 2: Run all Python and release checks**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\release_check.py
```

Expected: the Python suite passes (environment-specific skips are reported, not
failures) and the release script prints `RELEASE_CHECK_PASS`.

- [ ] **Step 3: Perform real browser acceptance in a disposable library**

Create a temporary library outside `F:\bookworkflow\book`:

```powershell
$acceptanceRoot = Join-Path $env:TEMP ("bookworkflow-trash-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $acceptanceRoot | Out-Null
$acceptanceRoot
```

Start the local launcher with this exact directory and without reusing the
production library:

```powershell
.\.venv\Scripts\python.exe scripts\launch_web.py --library-root $acceptanceRoot
```

In the local page:

1. Create `回收验收书` and confirm it becomes active.
2. Open the library list, select it, click `移入回收区`, inspect the title and
   directory in the confirmation, then cancel. Confirm the normal card remains.
3. Confirm the operation. Verify the header becomes `(选一本书)`, active files
   clear, the normal card disappears, and one `已回收` card appears.
4. Create another book with the same title; confirm recycled data does not block
   creation.
5. Restore the recycled entry; confirm it returns as a `（恢复1）` directory and
   is not automatically opened.
6. Inspect `$acceptanceRoot\.trash` in Explorer or PowerShell and confirm no
   permanent-delete control exists in the web page.
7. Request the public static port's `/api/local/trash` and
   `/api/local/restore`; confirm both are `404`.

Do not delete the disposable directory until the launcher is stopped. After
acceptance, stop only that launcher process and remove only the printed
`$acceptanceRoot` path.

- [ ] **Step 4: Audit repository and security boundaries**

```powershell
git status --short
git diff --check
git diff --name-only HEAD~7..HEAD
rg -n "Bearer |X-Library-Token|api[_-]?key|secret" README.md web scripts src tests
```

Expected: only planned files changed; no real local token, key, acceptance
directory, trash payload, or user-book content is present in the repository.

- [ ] **Step 5: Stop on acceptance defects rather than recording false completion**

If any acceptance defect remains, leave the affected checkbox unchecked, record
the exact failing command or browser step beneath it, and revise this plan with
a concrete failing test plus exact patch before making another implementation
commit. Do not mark the plan complete and do not broaden scope into Windows
Recycle Bin integration or web permanent deletion.

- [ ] **Step 6: Mark this plan complete and commit the acceptance record**

Change every checkbox in this plan from `[ ]` to `[x]` only after its command or
manual check has actually passed, then run:

```powershell
git add docs/superpowers/plans/2026-07-31-local-library-trash.md
git commit -m "docs: complete local recycle bin acceptance"
git status --short --branch
```

Expected: the plan completion commit succeeds and the worktree is clean.
