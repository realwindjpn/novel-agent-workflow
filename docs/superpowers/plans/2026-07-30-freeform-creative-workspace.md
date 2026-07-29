# Freeform Creative Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the rigid white-language command translator with a resumable freeform creative workspace that compiles user-confirmed ideas into the existing formal workflow.

**Architecture:** Add a dedicated creative-storage layer scoped to each active book, a browser storage/ZIP adapter, and separate freeform and compiler model calls. A new creative controller owns conversation, autonomy, proposals, drafts, and durability state; the existing `NWB`/`NWLocal` execution boundary remains the only route to formal core mutations.

**Tech Stack:** Python 3.11 standard library, zero-build browser JavaScript, OpenAI-compatible chat calls, Node `node:test`, Python `unittest`, native ZIP, local HTTP bridge, stdio MCP/core workflow.

---

## File map

- Create `scripts/creative_store.py`: active-book creative persistence, validation, ZIP export/import, deterministic merge.
- Create `tests/test_creative_store.py`: filesystem, bounds, ZIP safety, merge, and copy-import tests.
- Modify `scripts/launch_web.py`: authenticated creative routes and binary response helper.
- Modify `scripts/local_mcp_bridge.py`: expose the active book root through a read-only property.
- Modify `tests/test_web_launcher.py`: API isolation, authentication, binary export, and static asset contracts.
- Create `web/zip.js`: zero-dependency stored-entry ZIP encoder/decoder with CRC32 and traversal checks.
- Create `web/creative.js`: local/browser/memory storage adapter, durability state, backup download, and import.
- Create `tests/js/test_creative_adapter.mjs`: browser adapter and ZIP behavior without a real browser.
- Modify `web/local.js`: creative HTTP methods with JSON and binary response paths.
- Modify `tests/js/test_local_adapter.mjs`: local creative request contracts.
- Modify `web/llm.js`: separate plain creative reply, readiness assessment, and validated compiler calls.
- Create `tests/js/test_llm_adapter.mjs`: freeform response, typed failure, compiler validation, and repair tests.
- Create `web/creative-chat.js`: conversation lifecycle, autonomy, proposal/draft actions, persistence, and formal-plan handoff.
- Create `tests/js/test_creative_chat.mjs`: controller behavior with fake UI/storage/model/executor ports.
- Modify `web/chat.js`: expose formal-plan preview/confirmation and retain rule engine only for explicit commands.
- Modify `web/app.js`: book-switch lifecycle, creative workspace boot/resume, and drawer state.
- Modify `web/index.html`: freeform layout, progress/file drawers, actions, proposal card, save states, import/export controls.
- Modify `web/README.md`, `README.md`, and `CHANGELOG.md`: user behavior, persistence, fallback, and migration.

### Task 1: Add a bounded active-book creative store

**Files:**
- Create: `scripts/creative_store.py`
- Create: `tests/test_creative_store.py`

- [ ] **Step 1: Write failing construction and empty-session tests**

Create `tests/test_creative_store.py` with:

```python
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.creative_store import CreativeStore, CreativeStoreError


class CreativeStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.book = Path(self.tmp.name) / "book"
        self.book.mkdir()
        (self.book / "workflow.json").write_text(
            '{"title":"测试书","stage":"IDEA"}', encoding="utf-8"
        )

    def test_empty_session_does_not_create_files(self) -> None:
        store = CreativeStore(self.book)
        session = store.read_session()
        self.assertEqual(session["schema_version"], 1)
        self.assertEqual(session["turns"], [])
        self.assertEqual(session["summary"], "")
        self.assertFalse((self.book / "creative").exists())

    def test_requires_a_real_book_root(self) -> None:
        with self.assertRaisesRegex(CreativeStoreError, "workflow.json"):
            CreativeStore(Path(self.tmp.name) / "missing")
```

- [ ] **Step 2: Run the tests and verify the module is missing**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_creative_store.CreativeStoreTests
```

Expected: import failure for `scripts.creative_store`.

- [ ] **Step 3: Implement the store schema and safe path boundary**

Create `scripts/creative_store.py` with these public constants and methods:

```python
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = 1
MAX_TURNS = 10_000
MAX_TEXT_BYTES = 256 * 1024
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class CreativeStoreError(ValueError):
    pass


def _empty_facts() -> dict[str, list[str]]:
    return {
        "confirmed": [],
        "boundaries": [],
        "rejected": [],
        "important_turn_ids": [],
    }


class CreativeStore:
    def __init__(self, book_root: Path) -> None:
        self.book_root = book_root.resolve()
        if not (self.book_root / "workflow.json").is_file():
            raise CreativeStoreError("active book root must contain workflow.json")
        self.root = self.book_root / "creative"

    def read_session(self) -> dict[str, Any]:
        if not self.root.exists():
            return {
                "schema_version": SCHEMA_VERSION,
                "turns": [],
                "summary": "",
                "facts": _empty_facts(),
                "proposals": [],
                "drafts": [],
            }
        return self._read_existing_session()

    def _read_existing_session(self) -> dict[str, Any]:
        manifest = self._read_json(self.root / "manifest.json", {})
        turns = []
        turns_path = self.root / "conversation.jsonl"
        if turns_path.is_file():
            for line in turns_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    turns.append(json.loads(line))
        return {
            "schema_version": int(manifest.get("schema_version", SCHEMA_VERSION)),
            "turns": turns,
            "summary": self._read_text(self.root / "context-summary.md"),
            "facts": self._read_json(self.root / "facts.json", _empty_facts()),
            "proposals": self._read_collection("proposals"),
            "drafts": self._read_collection("drafts"),
        }

    def _read_collection(self, name: str) -> list[dict[str, Any]]:
        directory = self.root / name
        if not directory.is_dir():
            return []
        return [
            self._read_json(path, {})
            for path in sorted(directory.glob("*.json"))
            if path.is_file()
        ]

    @staticmethod
    def _read_json(path: Path, fallback: Any) -> Any:
        if not path.is_file():
            return fallback
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _read_text(path: Path) -> str:
        return path.read_text(encoding="utf-8") if path.is_file() else ""
```

- [ ] **Step 4: Run the focused tests**

Run the command from Step 2.

Expected: 2 tests pass.

- [ ] **Step 5: Commit the empty store boundary**

```powershell
git add -- scripts/creative_store.py tests/test_creative_store.py
git commit -m "feat: add bounded creative store"
```

### Task 2: Persist turns, facts, proposals, and trial drafts

**Files:**
- Modify: `scripts/creative_store.py`
- Modify: `tests/test_creative_store.py`

- [ ] **Step 1: Add failing persistence and validation tests**

Append these methods to `CreativeStoreTests`:

```python
    def test_append_turn_is_resumable_and_idempotent(self) -> None:
        store = CreativeStore(self.book)
        turn = {
            "id": "turn-1",
            "role": "user",
            "text": "写一个雨夜追踪的开场",
            "created_at": "2026-07-30T00:00:00Z",
        }
        store.append_turn(turn)
        store.append_turn(turn)
        self.assertEqual(store.read_session()["turns"], [turn])

    def test_write_state_and_artifacts_round_trip(self) -> None:
        store = CreativeStore(self.book)
        facts = {
            "confirmed": ["主角是法医"],
            "boundaries": ["不使用超自然解释"],
            "rejected": [],
            "important_turn_ids": ["turn-1"],
        }
        store.write_state("雨夜命案的现实主义悬疑。", facts)
        store.write_proposal({
            "id": "proposal-1",
            "status": "pending",
            "preview": "主角追查被伪装的旧案。",
            "intake": {"genre": "悬疑"},
            "source_turn_ids": ["turn-1"],
        })
        store.write_draft({
            "id": "draft-1",
            "title": "雨夜试写",
            "content": "雨水沿着警戒线滴落。",
            "source_turn_ids": ["turn-1"],
        })
        session = store.read_session()
        self.assertEqual(session["summary"], "雨夜命案的现实主义悬疑。")
        self.assertEqual(session["facts"], facts)
        self.assertEqual(session["proposals"][0]["status"], "pending")
        self.assertEqual(session["drafts"][0]["content"], "雨水沿着警戒线滴落。")

    def test_rejects_invalid_ids_roles_and_oversized_text(self) -> None:
        store = CreativeStore(self.book)
        with self.assertRaises(CreativeStoreError):
            store.append_turn({"id": "../escape", "role": "user", "text": "x"})
        with self.assertRaises(CreativeStoreError):
            store.append_turn({"id": "turn-2", "role": "root", "text": "x"})
        with self.assertRaises(CreativeStoreError):
            store.append_turn({
                "id": "turn-3", "role": "user", "text": "x" * (MAX_TEXT_BYTES + 1)
            })
```

Import `MAX_TEXT_BYTES` from `scripts.creative_store` at the top of the test.

- [ ] **Step 2: Run the new tests and verify missing methods fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_creative_store.CreativeStoreTests
```

Expected: failures for `append_turn`, `write_state`, `write_proposal`, and `write_draft`.

- [ ] **Step 3: Implement atomic writes and bounded append**

Add these methods to `CreativeStore`:

```python
    def append_turn(self, turn: Mapping[str, Any]) -> dict[str, Any]:
        item = dict(turn)
        self._validate_record(item, roles={"user", "assistant", "system"})
        existing = self.read_session()["turns"]
        if any(old.get("id") == item["id"] for old in existing):
            return item
        if len(existing) >= MAX_TURNS:
            raise CreativeStoreError("creative turn limit reached")
        self._ensure_root()
        with (self.root / "conversation.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
        self._write_manifest()
        return item

    def write_state(self, summary: str, facts: Mapping[str, Any]) -> None:
        self._validate_text(summary)
        clean = {key: list(facts.get(key, [])) for key in _empty_facts()}
        for values in clean.values():
            if not all(isinstance(value, str) for value in values):
                raise CreativeStoreError("fact lists must contain strings")
        self._ensure_root()
        self._atomic_text(self.root / "context-summary.md", summary)
        self._atomic_json(self.root / "facts.json", clean)
        self._write_manifest()

    def write_proposal(self, proposal: Mapping[str, Any]) -> dict[str, Any]:
        return self._write_record("proposals", proposal)

    def write_draft(self, draft: Mapping[str, Any]) -> dict[str, Any]:
        return self._write_record("drafts", draft)

    def _write_record(self, collection: str, record: Mapping[str, Any]) -> dict[str, Any]:
        item = dict(record)
        self._validate_record(item)
        self._ensure_root()
        self._atomic_json(self.root / collection / f"{item['id']}.json", item)
        self._write_manifest()
        return item

    def _validate_record(self, item: dict[str, Any], roles: set[str] | None = None) -> None:
        record_id = item.get("id")
        if not isinstance(record_id, str) or not ID_RE.fullmatch(record_id):
            raise CreativeStoreError("record id is invalid")
        if roles is not None and item.get("role") not in roles:
            raise CreativeStoreError("turn role is invalid")
        for key in ("text", "preview", "content", "title"):
            value = item.get(key)
            if value is not None:
                if not isinstance(value, str):
                    raise CreativeStoreError(f"{key} must be a string")
                self._validate_text(value)

    @staticmethod
    def _validate_text(value: str) -> None:
        if len(value.encode("utf-8")) > MAX_TEXT_BYTES:
            raise CreativeStoreError("creative text is too large")

    def _ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "proposals").mkdir(exist_ok=True)
        (self.root / "drafts").mkdir(exist_ok=True)

    def _write_manifest(self) -> None:
        current = self.read_session()
        self._atomic_json(self.root / "manifest.json", {
            "schema_version": SCHEMA_VERSION,
            "turn_count": len(current["turns"]),
            "proposal_count": len(current["proposals"]),
            "draft_count": len(current["drafts"]),
        })

    @staticmethod
    def _atomic_json(path: Path, payload: Any) -> None:
        CreativeStore._atomic_text(
            path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        )

    @staticmethod
    def _atomic_text(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
```

- [ ] **Step 4: Run the store tests**

Expected: 5 tests pass.

- [ ] **Step 5: Commit persistence**

```powershell
git add -- scripts/creative_store.py tests/test_creative_store.py
git commit -m "feat: persist creative sessions"
```

### Task 3: Add safe single-ZIP export and import

**Files:**
- Modify: `scripts/creative_store.py`
- Modify: `tests/test_creative_store.py`

- [ ] **Step 1: Add failing round-trip, traversal, merge, and copy tests**

Add imports `io`, `json`, and `zipfile`, then append:

```python
    def test_zip_round_trip_restores_session(self) -> None:
        store = CreativeStore(self.book)
        store.append_turn({"id": "turn-1", "role": "user", "text": "雨夜追凶"})
        archive = store.export_zip()
        restored_book = Path(self.tmp.name) / "restored"
        restored_book.mkdir()
        (restored_book / "workflow.json").write_text(
            '{"title":"恢复书","stage":"IDEA"}', encoding="utf-8"
        )
        restored = CreativeStore(restored_book)
        result = restored.import_zip(archive, "merge")
        self.assertEqual(result["turn_count"], 1)
        self.assertEqual(restored.read_session()["turns"][0]["text"], "雨夜追凶")

    def test_zip_rejects_traversal_and_oversized_archives(self) -> None:
        store = CreativeStore(self.book)
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_STORED) as zf:
            zf.writestr("../workflow.json", "bad")
        with self.assertRaisesRegex(CreativeStoreError, "unsafe ZIP path"):
            store.import_zip(raw.getvalue(), "merge")

    def test_import_merge_deduplicates_turn_ids(self) -> None:
        store = CreativeStore(self.book)
        turn = {"id": "turn-1", "role": "user", "text": "保留一次"}
        store.append_turn(turn)
        archive = store.export_zip()
        store.import_zip(archive, "merge")
        self.assertEqual(len(store.read_session()["turns"]), 1)

    def test_import_copy_preserves_current_and_records_inactive_copy(self) -> None:
        store = CreativeStore(self.book)
        store.append_turn({"id": "current", "role": "user", "text": "当前"})
        source_book = Path(self.tmp.name) / "source"
        source_book.mkdir()
        (source_book / "workflow.json").write_text('{}', encoding="utf-8")
        source = CreativeStore(source_book)
        source.append_turn({"id": "incoming", "role": "user", "text": "导入"})
        result = store.import_zip(source.export_zip(), "copy")
        self.assertEqual(store.read_session()["turns"][0]["id"], "current")
        self.assertTrue((self.book / "creative" / "imports" / result["copy_id"] / "manifest.json").is_file())
```

- [ ] **Step 2: Run and verify the ZIP methods are missing**

Run the full creative-store test class.

Expected: 4 new failures for `export_zip`/`import_zip`.

- [ ] **Step 3: Implement bounded ZIP serialization and import decisions**

Add these constants and methods:

```python
import io
import shutil
import zipfile

MAX_ARCHIVE_BYTES = 8 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 256
MAX_UNPACKED_BYTES = 16 * 1024 * 1024

    def export_zip(self) -> bytes:
        session = self.read_session()
        entries = {
            "creative-backup/manifest.json": json.dumps({
                "schema_version": SCHEMA_VERSION,
                "turn_count": len(session["turns"]),
                "proposal_count": len(session["proposals"]),
                "draft_count": len(session["drafts"]),
            }, ensure_ascii=False, indent=2) + "\n",
            "creative-backup/conversation.jsonl": "".join(
                json.dumps(turn, ensure_ascii=False, separators=(",", ":")) + "\n"
                for turn in session["turns"]
            ),
            "creative-backup/context-summary.md": session["summary"],
            "creative-backup/facts.json": json.dumps(
                session["facts"], ensure_ascii=False, indent=2
            ) + "\n",
        }
        for proposal in session["proposals"]:
            entries[f"creative-backup/proposals/{proposal['id']}.json"] = json.dumps(
                proposal, ensure_ascii=False, indent=2
            ) + "\n"
        for draft in session["drafts"]:
            entries[f"creative-backup/drafts/{draft['id']}.json"] = json.dumps(
                draft, ensure_ascii=False, indent=2
            ) + "\n"
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_STORED) as zf:
            for name, text in entries.items():
                zf.writestr(name, text.encode("utf-8"))
        payload = raw.getvalue()
        if len(payload) > MAX_ARCHIVE_BYTES:
            raise CreativeStoreError("creative ZIP is too large")
        return payload

    def import_zip(self, payload: bytes, decision: str) -> dict[str, Any]:
        if decision not in {"merge", "copy", "cancel"}:
            raise CreativeStoreError("import decision is invalid")
        if decision == "cancel":
            return {"cancelled": True}
        entries = self._read_zip_entries(payload)
        session = self._session_from_entries(entries)
        if decision == "copy":
            copy_id = self._next_copy_id()
            target = self.root / "imports" / copy_id
            self._write_session_tree(target, session)
            return {"copy_id": copy_id, "turn_count": len(session["turns"])}
        self._merge_session(session)
        return {"merged": True, "turn_count": len(self.read_session()["turns"])}

    def _read_zip_entries(self, payload: bytes) -> dict[str, bytes]:
        if len(payload) > MAX_ARCHIVE_BYTES:
            raise CreativeStoreError("creative ZIP is too large")
        out: dict[str, bytes] = {}
        total = 0
        with zipfile.ZipFile(io.BytesIO(payload), "r") as zf:
            infos = zf.infolist()
            if len(infos) > MAX_ARCHIVE_ENTRIES:
                raise CreativeStoreError("creative ZIP has too many entries")
            for info in infos:
                path = Path(info.filename)
                if path.is_absolute() or ".." in path.parts or info.is_dir():
                    if info.is_dir():
                        continue
                    raise CreativeStoreError("unsafe ZIP path")
                if info.external_attr >> 16 & 0o170000 == 0o120000:
                    raise CreativeStoreError("ZIP links are not allowed")
                total += info.file_size
                if total > MAX_UNPACKED_BYTES:
                    raise CreativeStoreError("creative ZIP expands too large")
                out[info.filename] = zf.read(info)
        return out
```

Implement `_session_from_entries`, `_write_session_tree`, `_merge_session`, and
`_next_copy_id` with these exact rules:

- only names below `creative-backup/` are accepted;
- manifest schema must equal `SCHEMA_VERSION`;
- JSON/text uses strict UTF-8;
- merge de-duplicates turns/proposals/drafts by `id`, keeping the current record
  when ids collide;
- confirmed/boundary/rejected/important lists are stable-order unions;
- incoming non-empty summary replaces an empty current summary only;
- copies are written under `creative/imports/import-YYYYMMDD-HHMMSS-N/` and do
  not change the active session.

- [ ] **Step 4: Run the full creative-store suite**

Expected: 9 tests pass.

- [ ] **Step 5: Commit ZIP support**

```powershell
git add -- scripts/creative_store.py tests/test_creative_store.py
git commit -m "feat: export and import creative backups"
```

### Task 4: Expose creative storage through the authenticated local bridge

**Files:**
- Modify: `scripts/local_mcp_bridge.py`
- Modify: `scripts/launch_web.py`
- Modify: `tests/test_web_launcher.py`
- Modify: `web/local.js`
- Modify: `tests/js/test_local_adapter.mjs`

- [ ] **Step 1: Add failing API isolation and active-root tests**

Add to the library-session tests:

```python
    def test_active_root_is_none_until_a_book_is_open(self):
        self.assertIsNone(self.session.active_root)
        self.session.open_book("验收书_20260730")
        self.assertEqual(self.session.active_root.name, "验收书_20260730")
```

Add LocalApi tests that call the handler fixture:

```python
    def test_creative_session_requires_active_book(self):
        response = self.call_api("GET", "creative/session", token="tk-test")
        self.assertEqual(response.status, 409)
        self.assertEqual(response.json["error"]["code"], "no_active_book")

    def test_creative_routes_require_token_and_stay_off_public_handler(self):
        denied = self.call_api("GET", "creative/session", token="")
        self.assertEqual(denied.status, 401)
        public = self.call_public("GET", "/api/local/creative/session")
        self.assertEqual(public.status, 404)
```

- [ ] **Step 2: Run the focused tests and verify failures**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_library tests.test_web_launcher.LocalApiTests
```

Expected: failures for missing `active_root` and creative routes.

- [ ] **Step 3: Add the active-root property and creative route handlers**

Add to `LibrarySession`:

```python
    @property
    def active_root(self) -> Path | None:
        if not self.open or self.client is None:
            return None
        return self.client.root
```

Add `creative_store_factory` injection to `LocalApi.__init__`, defaulting to
`CreativeStore`. Route the following exact operations after authentication:

```python
elif route == ("GET", "creative/session"):
    self._serve_creative_session(handler)
elif route == ("POST", "creative/turn"):
    self._serve_creative_turn(handler)
elif route == ("POST", "creative/state"):
    self._serve_creative_state(handler)
elif route == ("POST", "creative/proposal"):
    self._serve_creative_proposal(handler)
elif route == ("POST", "creative/draft"):
    self._serve_creative_draft(handler)
elif route == ("GET", "creative/export"):
    self._serve_creative_export(handler)
elif route == ("POST", "creative/import"):
    self._serve_creative_import(handler)
```

Use a `_creative_store()` helper that raises a typed `NoActiveBookError` when
`session.active_root` is absent. Map it to HTTP 409 code `no_active_book`.
Import bodies carry `{archive_base64, decision}` and are capped at 12 MiB before
base64 decode. Export uses this helper:

```python
    def _send_bytes(
        self,
        handler: BaseHTTPRequestHandler,
        status: int,
        payload: bytes,
        content_type: str,
        filename: str,
    ) -> None:
        handler.send_response(status)
        handler.send_header("Content-Type", content_type)
        handler.send_header("Content-Length", str(len(payload)))
        handler.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        handler.wfile.write(payload)
```

- [ ] **Step 4: Add local browser adapter methods and tests**

In `web/local.js`, split the request helper into `callApiResponse` and JSON
`callApi`, then expose:

```javascript
function creativeSession() { return callApi("creative/session"); }
function appendCreativeTurn(turn) {
  return callApi("creative/turn", { method: "POST", body: { turn: turn } });
}
function writeCreativeState(summary, facts) {
  return callApi("creative/state", { method: "POST", body: { summary: summary, facts: facts } });
}
function writeCreativeProposal(proposal) {
  return callApi("creative/proposal", { method: "POST", body: { proposal: proposal } });
}
function writeCreativeDraft(draft) {
  return callApi("creative/draft", { method: "POST", body: { draft: draft } });
}
function exportCreativeBackup() {
  return callApiResponse("creative/export").then(function (response) { return response.arrayBuffer(); });
}
function importCreativeBackup(bytes, decision) {
  return callApi("creative/import", {
    method: "POST",
    body: { archive_base64: bytesToBase64(bytes), decision: decision }
  });
}
```

Add Node tests proving the exact paths, methods, token header, and error shape.

- [ ] **Step 5: Run Python and JavaScript focused suites**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_library tests.test_web_launcher.LocalApiTests
node --test tests\js\test_local_adapter.mjs
```

Expected: all focused tests pass.

- [ ] **Step 6: Commit the local creative bridge**

```powershell
git add -- scripts/local_mcp_bridge.py scripts/launch_web.py tests/test_web_launcher.py web/local.js tests/js/test_local_adapter.mjs
git commit -m "feat: expose active-book creative storage"
```

### Task 5: Add browser storage and zero-dependency ZIP fallback

**Files:**
- Create: `web/zip.js`
- Create: `web/creative.js`
- Create: `tests/js/test_creative_adapter.mjs`
- Modify: `web/index.html`
- Modify: `scripts/launch_web.py`

- [ ] **Step 1: Write failing ZIP and durability adapter tests**

Create `tests/js/test_creative_adapter.mjs` using `node:test`, `assert/strict`,
and `vm`. Test these contracts:

```javascript
test("stored ZIP round-trips UTF-8 creative entries", async () => {
  const archive = NWZip.encode({
    "creative-backup/manifest.json": '{"schema_version":1}',
    "creative-backup/context-summary.md": "雨夜追凶"
  });
  const entries = NWZip.decode(archive);
  assert.equal(entries["creative-backup/context-summary.md"], "雨夜追凶");
});

test("ZIP decoder rejects traversal", () => {
  assert.throws(
    () => NWZip.validateName("../workflow.json"),
    /unsafe ZIP path/
  );
});

test("local backend reports written-local after append", async () => {
  const local = fakeLocal();
  const creative = loadCreative({ local, storage: fakeStorage() });
  await creative.boot("book-a");
  await creative.appendTurn({ id: "turn-1", role: "user", text: "开始" });
  assert.equal(creative.durability(), "local");
  assert.equal(local.calls[0].name, "appendCreativeTurn");
});

test("write failure keeps the turn and requires backup", async () => {
  const local = fakeLocal({ appendError: new Error("disk denied") });
  const creative = loadCreative({ local, storage: fakeStorage() });
  await creative.boot("book-a");
  await creative.appendTurn({ id: "turn-1", role: "user", text: "不要丢" });
  assert.equal(creative.durability(), "backup-required");
  assert.equal(creative.session().turns[0].text, "不要丢");
});
```

- [ ] **Step 2: Run and verify missing globals fail**

```powershell
node --test tests\js\test_creative_adapter.mjs
```

Expected: failures for `NWZip` and `NWCreative`.

- [ ] **Step 3: Implement `web/zip.js`**

Implement `window.NWZip` with this public surface:

```javascript
window.NWZip = {
  encode: encode,
  decode: decode,
  validateName: validateName,
  crc32: crc32
};
```

The encoder must use ZIP method 0, UTF-8 names, local headers, central
directory, CRC32, and an end record. The decoder accepts only method 0,
rejects encrypted entries, validates CRC32, limits 256 entries and 16 MiB
expanded size, and calls:

```javascript
function validateName(name) {
  if (!name || name[0] === "/" || /^[A-Za-z]:/.test(name)) {
    throw new Error("unsafe ZIP path");
  }
  var parts = name.replace(/\\/g, "/").split("/");
  if (parts.some(function (part) { return part === ".." || part === ""; })) {
    throw new Error("unsafe ZIP path");
  }
  if (parts[0] !== "creative-backup") throw new Error("unexpected ZIP root");
  return parts.join("/");
}
```

- [ ] **Step 4: Implement `web/creative.js`**

Expose `window.NWCreative` with:

```javascript
window.NWCreative = {
  boot: boot,
  session: function () { return clone(currentSession); },
  durability: function () { return durabilityState; },
  appendTurn: appendTurn,
  writeState: writeState,
  writeProposal: writeProposal,
  writeDraft: writeDraft,
  exportBackup: exportBackup,
  previewImport: previewImport,
  importBackup: importBackup,
  subscribe: subscribe
};
```

Use local backend when `NWLocal.active` and an active book exist. Otherwise use
`localStorage` key `nwa.creative.<book-directory>`; if storage throws, keep the
session in memory and set `backup-required`. Every mutation updates memory
first, then attempts durable storage. A failed durable write never rolls memory
back.

- [ ] **Step 5: Load the new assets with the launcher nonce**

Add scripts in this order before `app.js`:

```html
<script src="zip.js"></script>
<script src="creative.js"></script>
```

Add both names to the asset nonce list in `make_local_api_handler`.

- [ ] **Step 6: Run adapter and launcher asset tests**

```powershell
node --test tests\js\test_creative_adapter.mjs
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests
```

- [ ] **Step 7: Commit the browser fallback layer**

```powershell
git add -- web/zip.js web/creative.js web/index.html scripts/launch_web.py tests/js/test_creative_adapter.mjs tests/test_web_launcher.py
git commit -m "feat: add browser creative backup adapter"
```

### Task 6: Split freeform and compiler model calls

**Files:**
- Modify: `web/llm.js`
- Create: `tests/js/test_llm_adapter.mjs`

- [ ] **Step 1: Add failing freeform, readiness, compiler, and failure tests**

Create a VM harness with fake DOM, storage, and fetch. Add:

```javascript
test("creativeReply returns plain prose without JSON parsing", async () => {
  const NWL = loadLLM({ content: "我会把方向定为现实主义悬疑，从雨夜旧案切入。" });
  const result = await NWL.creativeReply({ text: "你来决定", autonomy: true, context: {} });
  assert.equal(result.reply, "我会把方向定为现实主义悬疑，从雨夜旧案切入。");
});

test("creativeReply exposes typed provider failure", async () => {
  const NWL = loadLLM({ status: 429, body: "busy" });
  await assert.rejects(
    NWL.creativeReply({ text: "继续", autonomy: false, context: {} }),
    error => error.code === "provider_http" && error.status === 429
  );
});

test("assessReadiness failure does not alter a creative reply", async () => {
  const NWL = loadLLMSequence([
    { content: "先确定主角为什么害怕真相。" },
    { content: "not-json" }
  ]);
  const reply = await NWL.creativeReply({ text: "继续", autonomy: false, context: {} });
  const ready = await NWL.assessReadiness({ context: {} });
  assert.equal(reply.reply, "先确定主角为什么害怕真相。");
  assert.equal(ready.ready, false);
});

test("compileProposal validates all intake keys and repairs once", async () => {
  const NWL = loadLLMSequence([
    { content: '{"preview":"方案","intake":{"genre":"悬疑"}}' },
    { content: completeCompilerJson() }
  ]);
  const proposal = await NWL.compileProposal({ context: {}, autonomy: true });
  assert.equal(proposal.preview, "完整方案");
  assert.equal(Object.keys(proposal.intake).length, 15);
  assert.equal(NWL.__calls.length, 2);
});
```

- [ ] **Step 2: Run and verify the new public methods are absent**

```powershell
node --test tests\js\test_llm_adapter.mjs
```

- [ ] **Step 3: Refactor model request and typed errors**

Keep provider settings but replace the single JSON-only path with:

```javascript
function ModelError(code, message, detail) {
  this.name = "ModelError";
  this.code = code;
  this.message = message;
  this.detail = detail || "";
}
ModelError.prototype = Object.create(Error.prototype);

function requestText(messages, options) {
  options = options || {};
  return requestProvider(messages, {
    temperature: options.temperature,
    maxTokens: options.maxTokens,
    json: !!options.json
  }).then(function (payload) {
    var text = extractProviderText(payload);
    if (!text.trim()) throw new ModelError("empty_response", "模型返回为空");
    return text;
  });
}
```

Map configuration, network/CORS, timeout, HTTP, empty, JSON parse, and schema
errors to distinct codes. Do not return `{kind:"fallback"}` from the new
methods.

- [ ] **Step 4: Implement three separated model calls**

Expose:

```javascript
function creativeReply(input) {
  return requestText(buildCreativeMessages(input), {
    temperature: getCreativeTemperature(), maxTokens: 3000, json: false
  }).then(function (reply) { return { reply: reply }; });
}

function assessReadiness(input) {
  return requestText(buildReadinessMessages(input), {
    temperature: 0.1, maxTokens: 300, json: true
  }).then(extractJson).then(validateReadiness)
    .catch(function () { return { ready: false, reason: "" }; });
}

function compileProposal(input) {
  return compileOnce(input).catch(function (firstError) {
    return repairCompile(input, firstError).then(validateProposal);
  });
}
```

The creative prompt explicitly defines autonomy, confirmed facts, boundaries,
rejected directions, summary, recent turns, and instructs plain natural
language. The compiler schema uses the 15 keys from `core.INTAKE_FIELD_KEYS` as
a fixed JS constant with a test that matches the Python keys.

- [ ] **Step 5: Keep legacy `tryLLM` for explicit command mode only**

Do not remove `tryLLM` yet. Mark it legacy and ensure new creative controller
never calls it. This preserves code-mode compatibility while the freeform path
ships independently.

- [ ] **Step 6: Run LLM and existing adapter tests**

```powershell
node --test tests\js\test_llm_adapter.mjs tests\js\test_local_adapter.mjs
```

- [ ] **Step 7: Commit model separation**

```powershell
git add -- web/llm.js tests/js/test_llm_adapter.mjs
git commit -m "feat: separate creative and compiler model calls"
```

### Task 7: Add the freeform creative controller

**Files:**
- Create: `web/creative-chat.js`
- Create: `tests/js/test_creative_chat.mjs`
- Modify: `web/chat.js`
- Modify: `web/index.html`
- Modify: `scripts/launch_web.py`

- [ ] **Step 1: Write failing controller tests with injected ports**

Define a factory `NWCreativeChat.createController(ports)` and test:

```javascript
test("autonomy phrase reaches creative model and persists both turns", async () => {
  const ports = fakePorts({ reply: "我决定采用双线悬疑。" });
  const controller = NWCreativeChat.createController(ports);
  await controller.submit("你来决定这个方向");
  assert.equal(ports.model.inputs[0].autonomy, true);
  assert.deepEqual(ports.storage.turns.map(t => t.role), ["user", "assistant"]);
  assert.match(ports.view.messages[1].text, /双线悬疑/);
});

test("model failure is visible and never invokes rule engine", async () => {
  const ports = fakePorts({ error: Object.assign(new Error("请求超时"), { code: "timeout" }) });
  const controller = NWCreativeChat.createController(ports);
  await controller.submit("你来决定");
  assert.equal(ports.ruleCalls, 0);
  assert.equal(ports.view.errors[0].code, "timeout");
});

test("restart restores session and pending proposal", async () => {
  const ports = fakePorts({ storedSession: savedSession() });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  assert.equal(ports.view.messages.length, savedSession().turns.length);
  assert.equal(ports.view.proposal.id, "proposal-1");
});
```

- [ ] **Step 2: Run and verify the controller is missing**

```powershell
node --test tests\js\test_creative_chat.mjs
```

- [ ] **Step 3: Implement the controller state machine**

Create `web/creative-chat.js` with states `idle`, `responding`, `compiling`,
`proposal`, `committing`, and `error`. Inject these ports:

```javascript
function createController(ports) {
  var state = "idle";
  var bookId = "";
  var session = emptySession();

  return {
    boot: boot,
    clear: clear,
    submit: submit,
    letModelDecide: letModelDecide,
    generateProposal: generateProposal,
    saveTrialDraft: saveTrialDraft,
    acceptProposal: acceptProposal,
    reviseProposal: reviseProposal,
    discardProposal: discardProposal,
    exportBackup: ports.storage.exportBackup,
    previewImport: ports.storage.previewImport,
    importBackup: ports.storage.importBackup,
    state: function () { return state; }
  };
}
```

`clear` resets the in-memory book id/session, sets state to `idle`, and asks the
view port to render an empty workspace without deleting durable records.

At browser startup, bind one controller to `makeBrowserPorts()` and expose both
the factory used by tests and the singleton methods used by `app.js`:

```javascript
var browserController = createController(makeBrowserPorts());
window.NWCreativeChat = {
  createController: createController,
  boot: browserController.boot,
  clear: browserController.clear,
  submit: browserController.submit,
  letModelDecide: browserController.letModelDecide,
  generateProposal: browserController.generateProposal,
  saveTrialDraft: browserController.saveTrialDraft,
  acceptProposal: browserController.acceptProposal,
  reviseProposal: browserController.reviseProposal,
  discardProposal: browserController.discardProposal,
  importBackup: browserController.importBackup,
  exportBackup: browserController.exportBackup
};
```

`submit` persists the user turn, calls `ports.model.creativeReply`, persists the
assistant turn, renders it, and triggers non-blocking readiness assessment.
Autonomy is true for the explicit action or text matching
`/(你|由你|模型).*(决定|做主)|你来定/`.

On model failure, render `ports.view.showError({code,message,retry})`; retain the
user turn and unsent recovery buffer; never call the legacy rule engine.

- [ ] **Step 4: Expose formal-plan preview from legacy chat**

In `web/chat.js`, add:

```javascript
function offerExternalPlan(plan) {
  assistantMsg("下面是确认后的正式写入计划：");
  var card = planCard(plan);
  pending = { kind: "plan", plan: plan, div: card };
}

window.NWC = {
  setMode: setMode,
  refresh: refreshStateSummary,
  offerExternalPlan: offerExternalPlan
};
```

The creative controller calls this only after `确认采用并写入`; the existing
plan card supplies the second execute confirmation.

- [ ] **Step 5: Load the controller after `chat.js`**

```html
<script src="llm.js"></script>
<script src="chat.js"></script>
<script src="creative-chat.js"></script>
```

This guarantees `window.NWC.offerExternalPlan` exists before the creative
controller binds its browser ports. Add the new asset to the launcher nonce
list.

- [ ] **Step 6: Run controller and legacy tests**

```powershell
node --test tests\js\test_creative_chat.mjs tests\js\test_llm_adapter.mjs tests\js\test_local_adapter.mjs
```

- [ ] **Step 7: Commit the controller**

```powershell
git add -- web/creative-chat.js web/chat.js web/index.html scripts/launch_web.py tests/js/test_creative_chat.mjs
git commit -m "feat: add freeform creative controller"
```

### Task 8: Compile natural-language proposals and preserve formal gates

**Files:**
- Modify: `web/creative-chat.js`
- Modify: `tests/js/test_creative_chat.mjs`
- Modify: `web/chat.js`

- [ ] **Step 1: Add failing proposal and trial-draft tests**

```javascript
test("proposal preview hides raw intake and requires two confirmations", async () => {
  const ports = fakePorts({ proposal: completeProposal() });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.generateProposal();
  assert.equal(ports.view.proposal.preview, "完整方案");
  assert.equal(ports.view.rawJsonShown, false);
  await controller.acceptProposal();
  assert.equal(ports.executor.offered.length, 1);
  assert.equal(ports.executor.executed.length, 0);
});

test("formal idea argv contains the validated 15-field intake", async () => {
  const ports = fakePorts({ proposal: completeProposal() });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.generateProposal();
  await controller.acceptProposal();
  const argv = ports.executor.offered[0].argv;
  const intake = JSON.parse(argv[argv.indexOf("--interview") + 1]);
  assert.equal(Object.keys(intake).length, 15);
});

test("trial draft persists without formal execution", async () => {
  const ports = fakePorts();
  const controller = NWCreativeChat.createController(ports);
  await controller.saveTrialDraft("雨夜开场", "雨水沿着警戒线滴落。", ["turn-1"]);
  assert.equal(ports.storage.drafts.length, 1);
  assert.equal(ports.executor.offered.length, 0);
});
```

- [ ] **Step 2: Implement proposal generation and plan construction**

`generateProposal` calls the compiler with the saved summary/facts/turns,
creates a stable `proposal-<timestamp>` id, writes it with `pending` status, and
renders only `preview`, `assumptions`, `uncertainties`, and draft references.

`acceptProposal` writes status `accepted` and offers this exact plan:

```javascript
function formalIdeaPlan(proposal) {
  var summary = proposal.summary || proposal.preview;
  var argv = [
    "idea", ".", "--summary", summary,
    "--interview", JSON.stringify(proposal.intake)
  ];
  return {
    kind: "custom",
    intent: "采用创意方案",
    explain: "把已确认的自然语言方案写入正式工作流。",
    cmdDisplay: "novel-workflow idea . --summary <已确认方案> --interview <内部结构化创意>",
    argv: argv,
    setup: {},
    source: "creative-compiler",
    proposalId: proposal.id,
    resultSummary: function (ok, result) {
      return ok ? "创意方案已写入正式工作流。" : "写入失败：" + ((result && result.err) || "未知错误");
    }
  };
}
```

The plan card must not display the serialized intake. The actual argv remains
available only to the executor.

- [ ] **Step 3: Implement trial draft records**

Store:

```javascript
{
  id: "draft-<timestamp>",
  title: title,
  content: content,
  source_turn_ids: sourceTurnIds,
  status: "trial",
  created_at: new Date().toISOString()
}
```

No method in this task calls chapter issue, draft, review, or release tools.

- [ ] **Step 4: Run proposal/controller tests**

```powershell
node --test tests\js\test_creative_chat.mjs
```

- [ ] **Step 5: Commit compiler handoff**

```powershell
git add -- web/creative-chat.js web/chat.js tests/js/test_creative_chat.mjs
git commit -m "feat: compile confirmed creative proposals"
```

### Task 9: Redesign the white-language surface as the creative workspace

**Files:**
- Modify: `web/index.html`
- Modify: `web/app.js`
- Modify: `tests/test_web_launcher.py`

- [ ] **Step 1: Add a failing asset contract**

Extend `WebLibraryPanelAssetTests` to load `creative-chat.js` and add:

```python
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
        self.assertNotIn("状态已更新 —— <b>", self.chat_js)
        self.assertIn("textContent", self.creative_chat_js)
```

- [ ] **Step 2: Run and verify the asset contract fails**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests
```

- [ ] **Step 3: Replace the creative-mode markup**

Rename the tab to `自由创作`. Add a creative header containing durability and
drawer toggles, an expanded conversation region, a proposal region, and the
three composer actions. Keep the existing chat input and plan-card container so
formal confirmation remains compatible.

Use real buttons with `aria-expanded`, `aria-controls`, and visible focus. The
proposal section starts hidden and uses text nodes for all model fields.

- [ ] **Step 4: Add drawer and responsive CSS**

Desktop creative mode uses one primary column. `#guide` and `#files` become
fixed-width overlay drawers with backdrops, not permanent grid columns. At
widths below 620px they become full-width sheets; the action row wraps and the
composer remains sticky above mobile navigation.

Add state styles:

```css
.creative-durability[data-state="local"] { color: #64f0de; }
.creative-durability[data-state="browser"] { color: #f1c75b; }
.creative-durability[data-state="backup-required"] { color: var(--red); }
.creative-proposal[hidden] { display: none; }
body.white:not(.creative-progress-open) #guide { display: none; }
body.white:not(.creative-files-open) #files { display: none; }
```

- [ ] **Step 5: Wire book boot, drawers, and durability in `app.js`**

After capabilities refresh or book switch, call:

```javascript
function bootCreativeForActiveBook() {
  if (!window.NWCreativeChat || !window.NWLocal || !window.NWLocal.capabilities) return Promise.resolve();
  var directory = window.NWLocal.capabilities.active_directory || "";
  if (!directory) return window.NWCreativeChat.clear();
  return window.NWCreativeChat.boot(directory);
}
```

Drawer buttons only toggle `creative-progress-open` and `creative-files-open`.
Persist drawer state for the current browser session, not per book.

- [ ] **Step 6: Run asset and controller tests**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests
node --test tests\js\test_creative_chat.mjs
```

- [ ] **Step 7: Commit the workspace UI**

```powershell
git add -- web/index.html web/app.js tests/test_web_launcher.py
git commit -m "feat: make freeform creation the primary workspace"
```

### Task 10: Complete ZIP download, import preview, and recovery UI

**Files:**
- Modify: `web/creative.js`
- Modify: `web/creative-chat.js`
- Modify: `web/index.html`
- Modify: `tests/js/test_creative_adapter.mjs`
- Modify: `tests/js/test_creative_chat.mjs`

- [ ] **Step 1: Add failing export/import UI tests**

```javascript
test("exportBackup returns one named ZIP without credentials", async () => {
  const creative = loadCreative({ local: null, storage: fakeStorageWithSession() });
  await creative.boot("book-a");
  const backup = await creative.exportBackup();
  assert.match(backup.filename, /^book-a-creative-\d{8}\.zip$/);
  const text = JSON.stringify(NWZip.decode(backup.bytes));
  assert.doesNotMatch(text, /api[_-]?key|authorization/i);
});

test("previewImport reports counts before mutation", async () => {
  const creative = loadCreative({ local: null, storage: fakeStorage() });
  const preview = await creative.previewImport(validArchive());
  assert.deepEqual(preview, {
    schemaVersion: 1, turnCount: 2, proposalCount: 1, draftCount: 1
  });
  assert.equal(creative.session().turns.length, 0);
});

test("controller requires merge copy or cancel on collision", async () => {
  const ports = fakePorts({ importCollision: true });
  const controller = NWCreativeChat.createController(ports);
  await controller.importBackup(validArchive());
  assert.deepEqual(ports.view.importChoices, ["merge", "copy", "cancel"]);
});
```

- [ ] **Step 2: Implement download and file-picker actions**

`exportBackup` returns `{bytes, filename, mimeType:"application/zip"}`. The UI
creates one object URL, clicks a temporary download anchor, then revokes the URL.

The import input uses `accept=".zip,application/zip"`. Read bytes with
`file.arrayBuffer()`, preview before mutation, and show the three explicit
collision decisions. After successful merge, re-render the restored session;
after copy, show the returned copy id and leave the active session unchanged.

- [ ] **Step 3: Implement persistent recovery state**

When a local write fails, keep the message/draft/proposal in memory, set
`backup-required`, display the error reason, and keep `下载创作备份` visible until
a later local save succeeds or the session is exported. Export does not claim
the session is locally durable; it changes the label to `已下载备份，尚未写入本地`.

- [ ] **Step 4: Run adapter/controller tests**

```powershell
node --test tests\js\test_creative_adapter.mjs tests\js\test_creative_chat.mjs
```

- [ ] **Step 5: Commit recovery UX**

```powershell
git add -- web/creative.js web/creative-chat.js web/index.html tests/js/test_creative_adapter.mjs tests/js/test_creative_chat.mjs
git commit -m "feat: add creative backup recovery flow"
```

### Task 11: Document, regress, and perform real browser acceptance

**Files:**
- Modify: `web/README.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Verify: all implementation files from Tasks 1-10

- [ ] **Step 1: Document the user-facing workflow**

Document:

- free conversation versus formal commit;
- `让模型决定` autonomy;
- proposal and second execute confirmation;
- per-book persistence and resume;
- trial drafts versus formal chapters;
- durability labels;
- single-ZIP download and manual import;
- local/public isolation;
- explicit model failure behavior.

Add one Unreleased changelog item summarizing the new workspace without naming a
specific provider or embedding a service endpoint.

- [ ] **Step 2: Run all JavaScript tests**

```powershell
node --test tests\js\test_local_adapter.mjs tests\js\test_creative_adapter.mjs tests\js\test_llm_adapter.mjs tests\js\test_creative_chat.mjs
```

Expected: all tests pass with zero failures.

- [ ] **Step 3: Run all Python tests**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Expected: all tests pass; platform capability tests may skip with named reasons.

- [ ] **Step 4: Run release and local acceptance**

```powershell
.\.venv\Scripts\python.exe scripts\release_check.py
.\.venv\Scripts\python.exe _local_acceptance.py
```

Expected: `RELEASE_CHECK_PASS` and all local acceptance steps report `OK`.

- [ ] **Step 5: Restart the one-click local-only launcher**

Close only the launcher process that owns ports 8080/8081 after verifying its
command line contains `scripts\launch_web.py`. Do not stop a separately running
tunnel process. Start:

```powershell
.\一键启动.cmd --no-tunnel
```

Expected: local and public listeners become ready and the local page opens.

- [ ] **Step 6: Perform desktop browser acceptance**

With a disposable QA book:

1. Enter `自由创作` and verify progress/files are collapsed.
2. Send `你来决定这个创意方向` and verify substantive prose, no raw JSON, no
   CLI, and no `没听懂`.
3. Reload and reopen the same book; verify the conversation resumes.
4. Generate a proposal, continue discussion, rewrite, and generate again.
5. Accept the proposal; verify a separate formal plan card appears and core is
   unchanged until `执行` is clicked.
6. Save a trial scene before outline lock; verify no formal chapter exists.
7. Verify console errors/warnings are empty.

- [ ] **Step 7: Perform failure, ZIP, narrow-screen, and public acceptance**

1. Simulate creative-write failure with the test-only failure switch.
2. Verify `需要下载备份`, download one ZIP, and inspect its manifest/counts.
3. Clear browser creative state, import the ZIP, preview counts, merge, and
   recover the session.
4. Repeat import as copy and verify the active session is unchanged.
5. At a 390x844 viewport, verify composer/actions/proposal/backup are reachable
   and both drawers work.
6. Verify the public page cannot access creative local routes and the public
   local-API path returns 404.
7. Reset the viewport and keep the local page open for handoff.

- [ ] **Step 8: Commit documentation and any QA-only correction**

```powershell
git add -- README.md web/README.md CHANGELOG.md
git commit -m "docs: explain freeform creative workspace"
```

- [ ] **Step 9: Review, push, and verify CI**

```powershell
git diff --check
git status -sb
git log --oneline origin/codex/local-mcp-library-plan..HEAD
git push -u origin codex/local-mcp-library-plan
gh pr checks 1 --watch --interval 10
```

Expected: clean worktree, remote updated, PR remains Draft, all checks pass.
