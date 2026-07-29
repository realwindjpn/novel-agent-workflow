# Local Library Cards and Chat Init Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the raw local-library selector with accessible Chinese-status book cards and route local chat `init` plans through safe library creation instead of an inactive MCP transport.

**Architecture:** `web/local.js` remains the command-routing boundary and gains an injected async project creator for local `init` plans. `web/app.js` remains the DOM/controller boundary: it renders card selection, coordinates creation and collision decisions, refreshes browser state, and returns the standard `{code, out, err}` result to chat. The Python launcher and library bridge stay authoritative and unchanged except for existing tests being rerun.

**Tech Stack:** Zero-build HTML/CSS/JavaScript SPA, Node `node:test`, Python 3.11 `unittest`, local HTTP API, stdio MCP child, in-app Browser QA.

---

## File map

- Modify `web/local.js`: injectable project-creation boundary and `init` interception.
- Modify `web/app.js`: card rendering/selection, Chinese status labels, creation coordinator, collision promise, UI refresh.
- Modify `web/index.html`: card-list markup, library-location disclosure, responsive card/modal CSS.
- Modify `tests/js/test_local_adapter.mjs`: TDD coverage proving local `init` skips MCP and delegates once.
- Modify `tests/test_web_launcher.py`: static asset contract for the new card DOM and public/local isolation regression.
- Modify `web/README.md`: describe chat-driven creation and card selection.
- Modify `CHANGELOG.md`: record the user-visible fix under Unreleased.

### Task 1: Intercept local `init` plans at the adapter boundary

**Files:**
- Modify: `tests/js/test_local_adapter.mjs`
- Modify: `web/local.js:606-701`

- [ ] **Step 1: Write the failing adapter tests**

Append these tests after the existing active-flag tests in
`tests/js/test_local_adapter.mjs`:

```javascript
test("local init delegates to the registered project creator and skips MCP", async () => {
  const NWL = loadLocal({ apiBase: "/api/local", token: "abc" });
  const calls = [];
  NWL.setProjectCreator(async (title) => {
    calls.push(title);
    return { code: 0, out: "已创建并打开：血迹_20260729", err: "" };
  });

  const result = await NWL.runSmart(
    {}, ["init", "demo", "--title", "血迹"], false
  );

  assert.deepEqual(calls, ["血迹"]);
  assert.equal(result.code, 0);
  assert.match(result.out, /血迹_20260729/);
  assert.equal(result.err, "");
});

test("local init reports a setup error when no project creator is registered", async () => {
  const NWL = loadLocal({ apiBase: "/api/local", token: "abc" });
  const result = await NWL.runSmart(
    {}, ["init", "demo", "--title", "血迹"], false
  );
  assert.equal(result.code, 1);
  assert.match(result.err, /新书创建器/);
});

test("local init converts project-creator rejection to a transport result", async () => {
  const NWL = loadLocal({ apiBase: "/api/local", token: "abc" });
  NWL.setProjectCreator(async () => {
    throw new Error("create failed");
  });
  const result = await NWL.runSmart(
    {}, ["init", "demo", "--title", "血迹"], false
  );
  assert.equal(result.code, 1);
  assert.match(result.err, /create failed/);
});
```

The existing `loadLocal()` fetch stub already rejects every network request;
therefore the first test also proves that `runMcp("tools/call", init)` was not
attempted.

- [ ] **Step 2: Run the tests and verify the new cases fail**

Run:

```powershell
node --test tests\js\test_local_adapter.mjs
```

Expected: the three new tests fail because `setProjectCreator` does not exist.

- [ ] **Step 3: Add the injectable creator and `init` branch**

Add this state and API immediately before `runSmart()` in `web/local.js`:

```javascript
  var projectCreator = null;

  function setProjectCreator(fn) {
    projectCreator = typeof fn === "function" ? fn : null;
  }

  function runProjectCreator(title) {
    if (!projectCreator) {
      return Promise.resolve({
        code: 1,
        out: "",
        err: "本地新书创建器尚未就绪，请打开书库面板后重试。"
      });
    }
    return Promise.resolve()
      .then(function () { return projectCreator(title); })
      .then(function (result) {
        if (result && typeof result.code === "number") return result;
        return { code: 1, out: "", err: "本地新书创建器返回了无效结果。" };
      })
      .catch(function (error) {
        return {
          code: 1,
          out: "",
          err: "新书创建失败：" + ((error && error.message) || error)
        };
      });
  }
```

In `runSmartInner()`, insert the branch after the `empty`/`unknown` guards and
before `prepareSetup()`:

```javascript
    if (plan.tool === "init") {
      return runProjectCreator(plan.arguments.title);
    }
```

Expose the registration function on the public API object:

```javascript
    setProjectCreator: setProjectCreator,
```

- [ ] **Step 4: Run the adapter tests and verify they pass**

Run:

```powershell
node --test tests\js\test_local_adapter.mjs
```

Expected: 33 tests pass, 0 fail.

- [ ] **Step 5: Commit the adapter boundary**

```powershell
git add -- web/local.js tests/js/test_local_adapter.mjs
git commit -m "fix: route local init through book creation"
```

### Task 2: Replace the native selector with the card-layout DOM contract

**Files:**
- Modify: `tests/test_web_launcher.py`
- Modify: `web/index.html:109-134`
- Modify: `web/index.html:727-757`

- [ ] **Step 1: Add a failing static asset contract test**

Add this class near the top of `tests/test_web_launcher.py`, after imports and
before server fixture classes:

```python
class WebLibraryPanelAssetTests(unittest.TestCase):
    def setUp(self):
        self.html = (
            Path(__file__).resolve().parents[1] / "web" / "index.html"
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
```

- [ ] **Step 2: Run the asset test and verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests
```

Expected: both tests fail because `lib-books` is still a `<select>` and the
new count/path elements do not exist.

- [ ] **Step 3: Replace the library dialog markup**

Replace the current `lib-dialog` contents (not the separate collision dialog)
with:

```html
  <dialog id="lib-dialog" class="lib-dialog" aria-labelledby="lib-dialog-title">
    <div class="lib-dialog-inner">
      <div class="lib-dialog-head">
        <div>
          <span class="lib-eyebrow">LOCAL LIBRARY</span>
          <h2 id="lib-dialog-title">本地书库</h2>
        </div>
        <span id="lib-count" class="lib-count">0 本创作</span>
        <span class="spacer"></span>
        <button type="button" id="lib-close" aria-label="关闭书库设置">关闭</button>
      </div>

      <details id="lib-location" class="lib-location">
        <summary>
          <span>书库位置</span>
          <code id="lib-path-display">F:\bookworkflow\book</code>
        </summary>
        <div class="lib-location-body">
          <label>本地绝对路径
            <input id="lib-path" type="text" autocomplete="off" spellcheck="false"
                   placeholder="F:\bookworkflow\book">
          </label>
          <div class="lib-dialog-actions">
            <button type="button" id="lib-apply">应用路径</button>
            <button type="button" id="lib-browse">选择文件夹</button>
            <button type="button" id="lib-refresh">重新读取</button>
          </div>
        </div>
      </details>

      <section class="lib-section" aria-labelledby="lib-existing-title">
        <div class="lib-section-head">
          <h3 id="lib-existing-title">已有创作</h3>
          <span>选择后再继续，避免误打开</span>
        </div>
        <div id="lib-books" class="lib-book-list" role="listbox"
             aria-label="已有创作列表"></div>
        <button type="button" class="primary lib-primary-action"
                id="lib-open" disabled>继续创作</button>
      </section>

      <section class="lib-section lib-create-section" aria-labelledby="lib-create-title">
        <div class="lib-section-head">
          <h3 id="lib-create-title">新建创作</h3>
          <span>将按书名和日期建立独立目录</span>
        </div>
        <div class="lib-create-row">
          <input id="lib-new-title" type="text" autocomplete="off" maxlength="120"
                 aria-label="新书书名" placeholder="输入书名，例如：血迹">
          <button type="button" class="primary" id="lib-create">创建新书</button>
        </div>
      </section>

      <p id="lib-status" class="lib-dialog-status" role="status"></p>
    </div>
  </dialog>
```

- [ ] **Step 4: Replace the old modal CSS with the card-system CSS**

Keep the existing `#lib-panel` rules. Replace the `.lib-dialog` through
`.lib-dialog-status.err` block with:

```css
  .lib-dialog {
    width: min(680px, calc(100vw - 28px)); max-height: min(780px, calc(100vh - 28px));
    color: var(--ink); background: #0b1424; border: 1px solid #263756;
    border-radius: 14px; padding: 0; box-shadow: 0 28px 90px #000d;
    font-family: var(--mono); overflow: hidden;
  }
  .lib-dialog::backdrop { background: #02070ddd; backdrop-filter: blur(4px); }
  .lib-dialog-inner { padding: 22px; display: grid; gap: 16px; overflow: auto; }
  .lib-dialog-head { display: flex; align-items: center; gap: 12px; }
  .lib-dialog-head h2 { margin: 2px 0 0; font-size: 18px; letter-spacing: .04em; }
  .lib-dialog-head .spacer { flex: 1; }
  .lib-eyebrow { color: var(--signal); font-size: 9px; letter-spacing: .16em; }
  .lib-count { color: var(--dim); border: 1px solid var(--edge2); border-radius: 999px; padding: 4px 9px; font-size: 10px; }
  .lib-dialog label { display: grid; gap: 6px; color: var(--dim); font-size: 11px; }
  .lib-dialog input {
    width: 100%; box-sizing: border-box; background: #07101d; color: var(--ink);
    border: 1px solid #263756; border-radius: 8px; padding: 10px 12px;
    font: 12px/1.4 var(--mono); outline: none;
  }
  .lib-dialog input:focus { border-color: var(--signal); box-shadow: 0 0 0 2px #16d9c21f; }
  .lib-dialog-actions { display: flex; flex-wrap: wrap; gap: 8px; }
  .lib-dialog button {
    border: 1px solid #2b3c5a; border-radius: 8px; padding: 8px 12px;
    background: #0d1829; color: var(--ink); font: 11px var(--mono); cursor: pointer;
  }
  .lib-dialog button:hover:not(:disabled) { border-color: var(--signal); color: var(--signal); }
  .lib-dialog button:focus-visible { outline: 2px solid var(--signal); outline-offset: 2px; }
  .lib-dialog button.primary { border-color: #137f78; background: #0b292b; color: #64f0de; }
  .lib-dialog button:disabled { cursor: not-allowed; opacity: .42; }
  .lib-location, .lib-section { border: 1px solid #21314d; border-radius: 10px; background: #091321; }
  .lib-location summary { display: flex; gap: 12px; align-items: center; padding: 12px 14px; cursor: pointer; color: var(--dim); }
  .lib-location summary code { margin-left: auto; max-width: 66%; overflow: hidden; text-overflow: ellipsis; color: var(--ink); white-space: nowrap; }
  .lib-location-body { border-top: 1px solid #21314d; padding: 14px; display: grid; gap: 10px; }
  .lib-section { padding: 14px; display: grid; gap: 12px; }
  .lib-section-head { display: flex; align-items: baseline; gap: 10px; }
  .lib-section-head h3 { margin: 0; font-size: 13px; color: var(--ink); }
  .lib-section-head span { color: var(--dim); font-size: 10px; }
  .lib-book-list { display: grid; gap: 8px; max-height: 280px; overflow: auto; }
  .lib-book-card { width: 100%; display: grid; grid-template-columns: 1fr auto; gap: 7px 12px; text-align: left; padding: 12px 13px !important; }
  .lib-book-card[aria-selected="true"] { border-color: var(--signal); background: #0a2529; box-shadow: inset 3px 0 var(--signal); }
  .lib-book-title { font-size: 13px; font-weight: 700; color: var(--ink); overflow: hidden; text-overflow: ellipsis; }
  .lib-book-meta { grid-column: 1 / -1; color: var(--dim); font-size: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .lib-status-chip { align-self: start; border: 1px solid #35506f; border-radius: 999px; padding: 3px 7px; color: #a9c4e8; font-size: 9px; white-space: nowrap; }
  .lib-primary-action { width: 100%; padding-block: 10px !important; }
  .lib-create-section { background: linear-gradient(135deg, #0a1726, #0a2026); }
  .lib-create-row { display: grid; grid-template-columns: 1fr auto; gap: 9px; }
  .lib-dialog-status { min-height: 18px; margin: 0; color: var(--dim); font-size: 11px; }
  .lib-dialog-status.err { color: var(--red); }
  @media (max-width: 620px) {
    .lib-dialog-inner { padding: 16px; }
    .lib-count, .lib-section-head span { display: none; }
    .lib-location summary code { max-width: 55%; }
    .lib-create-row { grid-template-columns: 1fr; }
  }
```

- [ ] **Step 5: Run the asset contract and verify it passes**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests
```

Expected: 2 tests pass.

- [ ] **Step 6: Commit the DOM and visual system**

```powershell
git add -- web/index.html tests/test_web_launcher.py
git commit -m "feat: redesign local library as book cards"
```

### Task 3: Render Chinese-status cards and safe selection behavior

**Files:**
- Modify: `web/app.js:826-953`
- Modify: `tests/test_web_launcher.py`

- [ ] **Step 1: Extend the static contract test for controller behavior**

Add to `WebLibraryPanelAssetTests.setUp()`:

```python
        self.app_js = (
            Path(__file__).resolve().parents[1] / "web" / "app.js"
        ).read_text(encoding="utf-8")
```

Add this test:

```python
    def test_library_controller_has_chinese_status_and_safe_selection(self):
        self.assertIn('OUTLINE_LOCKED: "大纲已锁定"', self.app_js)
        self.assertIn('IDEA: "构思中"', self.app_js)
        self.assertIn('aria-selected', self.app_js)
        self.assertIn('selectedBookDirectory', self.app_js)
        self.assertIn('libOpenBtn.disabled', self.app_js)
        self.assertIn('正在读取书库', self.app_js)
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests.test_library_controller_has_chinese_status_and_safe_selection
```

Expected: fail because the current controller appends `<option>` elements and
has no Chinese state map.

- [ ] **Step 3: Replace selector state and `renderBookList()`**

Add `libCount`, `libPathDisplay`, and selection state beside the existing DOM
lookups:

```javascript
  var libCount = document.getElementById("lib-count");
  var libPathDisplay = document.getElementById("lib-path-display");
  var selectedBookDirectory = "";
```

Replace `renderBookList()` and add the helpers below it:

```javascript
  var LIB_STAGE_LABELS = {
    INIT: "已立项",
    IDEA: "构思中",
    CONCEPT_APPROVED: "概念已通过",
    BIBLE_WRITTEN: "世界观已建立",
    OUTLINE_LOCKED: "大纲已锁定",
    DRAFTING: "写作中",
    READY_TO_RELEASE: "待发布",
    RELEASED: "已有章节发布"
  };

  function statusLabel(book) {
    if (book && book.released_chapter_count > 0) return "已有章节发布";
    return LIB_STAGE_LABELS[(book && book.stage) || ""] || "处理中";
  }

  function selectBookCard(directory) {
    selectedBookDirectory = directory || "";
    var cards = libBooks.querySelectorAll(".lib-book-card");
    Array.prototype.forEach.call(cards, function (card) {
      var selected = card.dataset.directory === selectedBookDirectory;
      card.setAttribute("aria-selected", selected ? "true" : "false");
    });
    libOpenBtn.disabled = !selectedBookDirectory;
  }

  function renderBookList(result) {
    if (!libBooks) return;
    libBooks.replaceChildren();
    selectedBookDirectory = "";
    var books = (result && (result.books || result.catalog)) || [];
    if (libCount) libCount.textContent = books.length + " 本创作";
    if (result && result.library) {
      libPathInput.value = result.library;
      libPathDisplay.textContent = result.library;
    }

    books.forEach(function (book) {
      var card = document.createElement("button");
      card.type = "button";
      card.className = "lib-book-card";
      card.setAttribute("role", "option");
      card.setAttribute("aria-selected", "false");
      card.dataset.directory = book.directory;
      card.title = "工作流状态：" + (book.stage || "unknown");

      var title = document.createElement("span");
      title.className = "lib-book-title";
      title.textContent = book.title || book.directory;
      var chip = document.createElement("span");
      chip.className = "lib-status-chip";
      chip.textContent = statusLabel(book);
      var meta = document.createElement("span");
      meta.className = "lib-book-meta";
      meta.textContent = (book.chapter_count || 0) + " 章 · " + book.directory;
      card.append(title, chip, meta);
      libBooks.appendChild(card);
    });

    var active = window.NWLocal.capabilities && window.NWLocal.capabilities.active_directory;
    if (active && books.some(function (book) { return book.directory === active; })) {
      selectBookCard(active);
    } else {
      libOpenBtn.disabled = true;
    }
    setLibStatus(books.length ? "已读取 " + books.length + " 本创作。" : "书库为空，可以创建新书。", false);
  }
```

Replace `loadLibraryDialog()` so the modal exposes a stable loading state even
when the local catalog responds quickly:

```javascript
  function loadLibraryDialog() {
    if (libDialog && !libDialog.open) libDialog.showModal();
    setLibStatus("正在读取书库……", false);
    libOpenBtn.disabled = true;
    return window.NWLocal.listBooks().then(function (result) {
      renderBookList(result);
      refreshLibPanel();
      return result;
    });
  }
```

Register one delegated selection handler after the library-button handlers:

```javascript
  if (libBooks) libBooks.addEventListener("click", function (event) {
    var card = event.target.closest(".lib-book-card");
    if (!card || !libBooks.contains(card)) return;
    selectBookCard(card.dataset.directory);
    setLibStatus("已选择：" + card.querySelector(".lib-book-title").textContent, false);
  });
```

Update `refreshLibPanel()` so both visible path locations stay synchronized:

```javascript
      if (libPathInput) libPathInput.value = cap.library;
      if (libPathDisplay) libPathDisplay.textContent = cap.library;
```

Replace `var directory = libBooks.value;` in the continue handler with:

```javascript
    var directory = selectedBookDirectory;
```

- [ ] **Step 4: Run the asset/controller tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit card rendering and selection**

```powershell
git add -- web/app.js tests/test_web_launcher.py
git commit -m "feat: add selectable Chinese-status book cards"
```

### Task 4: Coordinate chat creation and collision decisions in the UI

**Files:**
- Modify: `web/app.js:881-973`
- Modify: `tests/test_web_launcher.py`

- [ ] **Step 1: Add the coordinator registration contract test**

Add this method to `WebLibraryPanelAssetTests`:

```python
    def test_app_registers_a_collision_aware_project_creator(self):
        self.assertIn("setProjectCreator", self.app_js)
        self.assertIn("pendingCollision", self.app_js)
        self.assertIn("resolveCollisionDecision", self.app_js)
        self.assertIn("已取消创建新书", self.app_js)
```

- [ ] **Step 2: Run it and verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests.test_app_registers_a_collision_aware_project_creator
```

Expected: fail because the current collision buttons fire detached API calls
and never resolve the chat plan.

- [ ] **Step 3: Replace collision state and creation coordination**

Replace `pendingCollisionTitle` with:

```javascript
  var pendingCollision = null;
```

Replace `createWithDecision()` with:

```javascript
  function finishCreatedBook(result) {
    var directory = result && result.directory ? result.directory : "新创作";
    return finishBookSwitch("已打开：" + directory).then(function () {
      if (libNewTitle) libNewTitle.value = "";
      return result;
    });
  }

  function waitForCollisionDecision(title, matches) {
    if (pendingCollision) {
      return Promise.reject(new Error("已有一个同名确认正在等待处理。"));
    }
    collisionText.textContent = "已有同名创作：" + matches.map(function (item) {
      return item.directory;
    }).join("、") + "。请选择继续上次或建立新副本。";
    collisionDialog.showModal();
    return new Promise(function (resolve, reject) {
      pendingCollision = { title: title, resolve: resolve, reject: reject };
    });
  }

  function createWithDecision(title, decision) {
    setLibStatus("正在创建……", false);
    libCreateBtn.disabled = true;
    return window.NWLocal.createBook(title, decision).then(function (result) {
      if (result && result.status === "collision") {
        return waitForCollisionDecision(title, result.matches || []);
      }
      return finishCreatedBook(result);
    }).finally(function () {
      libCreateBtn.disabled = false;
    });
  }

  function resolveCollisionDecision(decision) {
    if (!pendingCollision) return;
    var pending = pendingCollision;
    pendingCollision = null;
    collisionDialog.close();
    if (!decision) {
      setLibStatus("已取消创建新书。", false);
      pending.resolve({ cancelled: true, title: pending.title });
      return;
    }
    createWithDecision(pending.title, decision).then(pending.resolve, pending.reject);
  }

  function createProjectForCommand(title) {
    return createWithDecision(title, null).then(function (result) {
      if (result && result.cancelled) {
        return { code: 0, out: "已取消创建新书。", err: "" };
      }
      var directory = result && result.directory ? result.directory : title;
      if (libDialog && libDialog.open) libDialog.close();
      return { code: 0, out: "已创建并打开：" + directory, err: "" };
    });
  }
```

Replace the three collision-button handlers with:

```javascript
  if (openLatestBtn) openLatestBtn.addEventListener("click", function () {
    resolveCollisionDecision("open_latest");
  });
  if (createCopyBtn) createCopyBtn.addEventListener("click", function () {
    resolveCollisionDecision("create_new");
  });
  if (cancelCollisionBtn) cancelCollisionBtn.addEventListener("click", function () {
    resolveCollisionDecision(null);
  });
```

Register the coordinator after these handlers:

```javascript
  if (localMode && window.NWLocal) {
    window.NWLocal.setProjectCreator(createProjectForCommand);
  }
```

Keep the manual `创建新书` handler routed through the same
`createWithDecision(title, null)` function so manual and chat creation share
collision behavior.

- [ ] **Step 4: Run focused and JavaScript tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests
node --test tests\js\test_local_adapter.mjs
```

Expected: 4 Python asset tests and 33 JavaScript adapter tests pass.

- [ ] **Step 5: Commit the UI coordinator**

```powershell
git add -- web/app.js tests/test_web_launcher.py
git commit -m "fix: coordinate chat book creation and collisions"
```

### Task 5: Update user documentation and run automated regressions

**Files:**
- Modify: `web/README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Document the new local behavior**

Add this paragraph to the local-library section of `web/README.md`:

```markdown
In local white-language mode, starting a new book routes `init` through the
library creator first. The page creates and activates the dated book directory,
then continues with its MCP child; it never sends `init` to a missing or
previously active book. Same-title requests pause for the same open/create-copy/
cancel decision used by the library panel. Existing books are displayed as
selectable cards with Chinese workflow status labels.
```

Add this Unreleased item to `CHANGELOG.md`:

```markdown
- Fixed local white-language new-book creation so `init` creates and activates
  a library project instead of failing with `transport: no active book`; the
  local library chooser now uses accessible Chinese-status book cards.
```

- [ ] **Step 2: Run the complete JavaScript suite**

Run:

```powershell
node --test tests\js\test_local_adapter.mjs
```

Expected: 33 tests pass, 0 fail.

- [ ] **Step 3: Run the complete Python suite**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Expected: all tests pass; Windows symlink capability tests may be skipped.

- [ ] **Step 4: Run release and local headless acceptance checks**

Run sequentially:

```powershell
.\.venv\Scripts\python.exe scripts\release_check.py
.\.venv\Scripts\python.exe _local_acceptance.py
```

Expected: `RELEASE_CHECK_PASS`, followed by all 8 local acceptance steps
reporting `OK` and both acceptance ports being released.

- [ ] **Step 5: Commit documentation**

```powershell
git add -- CHANGELOG.md web/README.md
git commit -m "docs: explain local chat book creation"
```

### Task 6: Browser QA on the reported path and responsive card layout

**Files:**
- Verify: `web/index.html`
- Verify: `web/app.js`
- Verify: `web/local.js`
- Verify on disk: `book/血迹_20260729/workflow.json`

- [ ] **Step 1: Restart the local-only launcher for a fresh asset nonce**

Stop the currently running development launcher with its existing terminal
session, then run:

```powershell
.\.venv\Scripts\python.exe -u -c "from pathlib import Path; from scripts.launch_web import Launcher,LauncherConfig; app=Launcher(LauncherConfig(open_browser=False), cloudflared=Path('cloudflared'), tunnel_factory=lambda executable,url: None); raise SystemExit(app.run())"
```

Expected: local 8080 and isolated public 8081 are ready; no Cloudflare process
is required.

- [ ] **Step 2: Verify the redesigned panel before mutation**

In the in-app Browser, open `http://localhost:8080/`, click `列表`, and verify:

- page title is `novel-workflow Live Runner · 网页实跑器`;
- badge is `本地 MCP · 可写磁盘`;
- each existing project is a card with a Chinese status chip;
- clicking one card sets `aria-selected="true"` and enables `继续创作`;
- no project opens until `继续创作` is clicked;
- console error/warn list is empty.

Capture one desktop screenshot.

- [ ] **Step 3: Reproduce the user's white-language creation flow**

With no active book selected, switch to `白话`, enter `开始一本新书`, then
provide `血迹` as the requested title and execute the proposed plan.

Expected:

- no `transport: no active book` text appears;
- the result says `已创建并打开：血迹_20260729` (or enters the collision flow
  if the prior failed trial has since created it);
- the header active-book label changes to the selected dated directory;
- `workflow.json` exists and its title is `血迹`;
- console error/warn list remains empty.

Capture the successful result and active-book header.

- [ ] **Step 4: Verify collision without overwriting**

Run the same `血迹` creation intent again.

Expected: the collision dialog appears before any action. Choose `取消` and
verify the chat plan resolves with `已取消创建新书。`; the current active book
and directory count do not change.

- [ ] **Step 5: Verify empty and API-error states without changing user data**

Create a disposable empty directory inside the workspace:

```powershell
$qaEmpty = (New-Item -ItemType Directory -Force -Path 'F:\bookworkflow\.qa-empty-library').FullName
```

In the library location disclosure, first enter
`F:\bookworkflow\does-not-exist-ui-qa` and click `应用路径`.

Expected: the modal stays open, displays the API error in its status line, and
keeps the current library unchanged.

Then enter `F:\bookworkflow\.qa-empty-library` and click `应用路径`.

Expected: the card area displays a clear empty state and `继续创作` stays
disabled. Restore `F:\bookworkflow\book` before continuing.

After restoration, verify and remove only the disposable directory created in
this step:

```powershell
$resolved = (Resolve-Path -LiteralPath 'F:\bookworkflow\.qa-empty-library').Path
if ($resolved -ne 'F:\bookworkflow\.qa-empty-library') { throw "unexpected QA path: $resolved" }
Remove-Item -LiteralPath $resolved
```

- [ ] **Step 6: Verify a narrow viewport**

Set a temporary viewport near 390x844 and reopen the library modal.

Expected: cards remain readable, the internal list scrolls, the create input
and button stack, focus rings are visible, and `继续创作` remains reachable.
Reset the temporary viewport afterwards.

- [ ] **Step 7: Verify public-port isolation remains unchanged**

Open `http://127.0.0.1:8081/` and verify the library header/panel is absent and
the public badge reads `公网演示 · 浏览器内存`. Check the local API path from
PowerShell:

```powershell
$localApiPath = "/api/local/capabilities"
curl.exe -sS -o NUL -w "%{http_code}" "http://127.0.0.1:8081$localApiPath"
```

Expected: HTTP `404`; public mode continues its in-memory Pyodide/replay path.

- [ ] **Step 8: Confirm clean repository state and create the final commit if needed**

Run:

```powershell
git diff --check
git status -sb
```

Expected: no whitespace errors and no uncommitted files. If browser QA exposed
a correction, stage only its scoped files, rerun the focused tests, and commit
with `fix: finish local library chat UX acceptance`.

### Task 7: Push the finished branch and verify GitHub CI

**Files:**
- Verify only; no source file is expected to change.

- [ ] **Step 1: Review the branch history and final diff**

```powershell
git log --oneline origin/codex/local-mcp-library-plan..HEAD
git diff --stat origin/codex/local-mcp-library-plan...HEAD
```

Expected: only the approved design/plan, adapter, panel, tests, and docs appear.

- [ ] **Step 2: Push the current branch**

```powershell
git push -u origin codex/local-mcp-library-plan
```

Expected: the remote branch advances and PR #1 updates.

- [ ] **Step 3: Wait for the existing PR checks**

```powershell
gh pr checks 1 --watch --interval 10
```

Expected: every check reports `pass`. Leave PR #1 in Draft unless the user
explicitly asks to mark it ready.
