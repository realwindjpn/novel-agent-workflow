# Freeform Runtime Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the real Windows launch and freeform runtime so the current page opens fresh, resumes the active book, calls the creative model correctly, and fills the available window.

**Architecture:** Keep `chat.js` as the single DOM composer/formal-plan owner while routing active-book ordinary text through a small workspace bridge exposed by `app.js`. Normalize model input and provider response handling in `llm.js`; keep formal MCP/core mutation behind the existing two-confirmation plan card.

**Tech Stack:** Python 3.11 standard library, Windows `webbrowser`, zero-build browser JavaScript, OpenAI-compatible HTTP, Node `node:test`, Python `unittest`.

**Execution status:** Completed and verified on 2026-07-30. The browser acceptance used both the in-app browser for layout/resume checks and the user's already-configured Chrome tab for the real provider generation check.

---

## File map

- Modify `scripts/launch_web.py`: open a versioned local URL immediately and disable local static caching.
- Modify `tests/test_web_launcher.py`: assert browser timing/query and cache headers.
- Modify `web/app.js`: initial creative boot, clean book switching, and `window.NWCW` composer bridge.
- Modify `web/chat.js`: delegate ordinary input to the active creative workspace and render state summary as plain text.
- Modify `web/creative-chat.js`: normalize model inputs from the restored session.
- Modify `web/llm.js`: compatible response extraction and real completion connection test.
- Modify `web/index.html`: single-column full-width white mode.
- Modify `tests/js/test_creative_chat.mjs`: verify real text/session context reaches all model calls.
- Modify `tests/js/test_llm_adapter.mjs`: verify compatible provider variants and generation-level connection test.
- Create `tests/js/test_chat_routing.mjs`: verify active creative routing prevents legacy fallback.
- Modify `CHANGELOG.md`: record the real-runtime fixes.

### Task 1: Open the current local build immediately

**Files:**
- Modify: `tests/test_web_launcher.py`
- Modify: `scripts/launch_web.py`

- [x] **Step 1: Write failing launcher tests**

Add assertions that the browser URL contains a non-empty `run` query value,
that it is opened after local readiness but before the tunnel URL is produced,
and that local static responses include `Cache-Control: no-store`.

- [x] **Step 2: Run the focused test and verify failure**

Run:

```powershell
python -m unittest tests.test_web_launcher.LauncherLifecycleTests tests.test_web_launcher.LocalApiHttpTests
```

Expected: the new URL/timing/cache assertions fail against the current launcher.

- [x] **Step 3: Implement versioned early browser opening**

Build the browser URL as `http://localhost:<port>/?run=<per-run-value>`, call
`_open_local_browser` immediately after private listener readiness, remove the
later duplicate open calls, and add `Cache-Control: no-store` only to the local
static handler responses.

- [x] **Step 4: Run focused tests**

Run the command from Step 2. Expected: PASS.

### Task 2: Restore and route the active creative workspace

**Files:**
- Modify: `tests/js/test_creative_chat.mjs`
- Create: `tests/js/test_chat_routing.mjs`
- Modify: `web/creative-chat.js`
- Modify: `web/app.js`
- Modify: `web/chat.js`

- [x] **Step 1: Write failing context and routing tests**

Assert that `controller.submit("雨夜开场")` passes:

```js
{
  text: "雨夜开场",
  autonomy: false,
  context: { book: "book-a", turns: /* restored turns */, summary: /* saved */ }
}
```

Assert that an active `window.NWCW.submit` receives composer text exactly once
and the legacy `NWL.tryLLM`/rule engine paths are not invoked.

- [x] **Step 2: Run tests and verify failure**

Run:

```powershell
node --test tests/js/test_creative_chat.mjs tests/js/test_chat_routing.mjs
```

Expected: current `{input, session}` contract and missing composer bridge fail.

- [x] **Step 3: Normalize context and expose the workspace bridge**

Add one helper in `creative-chat.js` that maps the stored session to the
`llm.js` contract for reply, readiness, and compilation. In `app.js`, boot the
active book after the initial capability handshake, clear the view before a
book change, and expose:

```js
window.NWCW = {
  isActive: function () { return Boolean(activeDirectory && creativeController); },
  submit: function (text) { return creativeController.submit(text); }
};
```

In `chat.js`, route the composer to `NWCW.submit(text)` before rendering through
or invoking any legacy LLM/rule path. The creative controller owns rendering
for that branch.

- [x] **Step 4: Run focused tests**

Run the command from Step 2. Expected: PASS.

### Task 3: Make provider testing and response parsing truthful

**Files:**
- Modify: `tests/js/test_llm_adapter.mjs`
- Modify: `web/llm.js`

- [x] **Step 1: Write failing compatibility tests**

Cover these payloads:

```js
{ choices: [{ message: { reasoning_content: "推理模型回复" } }] }
{ choices: [{ message: { content: [{ type: "text", text: "分段回复" }] } }] }
{ choices: [{ text: "choice 回复" }] }
{ output_text: "顶层回复" }
```

Also assert `testConnection()` POSTs to `/chat/completions` with a minimal
message and returns success only when usable generated text is present.

- [x] **Step 2: Run the adapter test and verify failure**

Run:

```powershell
node --test tests/js/test_llm_adapter.mjs
```

Expected: response variants are treated as empty and connection test uses
`/models`.

- [x] **Step 3: Implement one shared provider text extractor**

Normalize string/array content, `message.text`, `reasoning_content`,
`choice.text`, and `output_text`. Reuse it in both legacy/formal and creative
requests. Change `testConnection()` to a low-token non-streaming completion and
return a concise provider/model success message without logging the API key or
response body.

- [x] **Step 4: Run the adapter test**

Run the command from Step 2. Expected: PASS.

### Task 4: Fill the window and render summaries safely

**Files:**
- Modify: `tests/test_web_launcher.py`
- Modify: `web/index.html`
- Modify: `web/chat.js`

- [x] **Step 1: Add failing static contracts**

Assert that white mode defines a single-column main grid, that `#chat-panel`
spans the full grid, and that `refreshStateSummary` does not add `<b>` strings
to a call to `assistantMsg`.

- [x] **Step 2: Run the static contract tests and verify failure**

Run:

```powershell
python -m unittest tests.test_web_launcher.WebAssetTests
```

Expected: full-width and plain-summary contracts fail.

- [x] **Step 3: Implement layout and safe text rendering**

Add:

```css
body.white main { grid-template-columns: minmax(0, 1fr); }
body.white #chat-panel { grid-column: 1 / -1; }
```

Keep the side panels as existing fixed overlay drawers. Replace summary HTML
fragments with readable Unicode/plain text before passing them to
`assistantMsg`.

- [x] **Step 4: Run the static contract tests**

Run the command from Step 2. Expected: PASS.

### Task 5: Regression and real browser acceptance

**Files:**
- Modify: `CHANGELOG.md`

- [x] **Step 1: Record the repair**

Add an Unreleased entry covering early fresh launch, active-book resume,
creative composer routing, compatible model responses, truthful connection
testing, full-width layout, and plain status summaries.

- [x] **Step 2: Run all JavaScript tests**

Run:

```powershell
Get-ChildItem tests/js/test_*.mjs | ForEach-Object { node --test $_.FullName }
```

Expected: all tests pass.

- [x] **Step 3: Run Python and release checks**

Run:

```powershell
python -m unittest discover -s tests
python scripts/release_check.py
```

Expected: Python suite passes and output includes `RELEASE_CHECK_PASS`.

- [x] **Step 4: Restart only the bookworkflow launcher**

Stop the identified `scripts/launch_web.py` process tree only after verifying
its command line belongs to `F:\bookworkflow`. Do not stop or modify ngrok.
Start `一键启动.cmd` and verify listeners 8080/8081 return the intended local
and public surfaces.

- [x] **Step 5: Verify with the in-app browser**

Confirm the versioned URL loads without manual refresh, the active book and
saved turns restore, the chat fills the window, a real configured model call
returns visible prose or a precise provider error, and no ordinary creative
message produces a `bible` command.

- [x] **Step 6: Inspect repository state and hand off**

Run `git diff --check`, report changed files and exact test results, and leave
the repaired launcher running for user testing. Do not push without a separate
user request.
