# Structured Workbench Floating Chat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the structured desktop workbench as the default surface while supporting one main-window natural-language reply, automatic second-turn migration into a persistent draggable chat window, programmatic creative convergence, and two-stage formal handoff.

**Architecture:** Add three pure boundaries: a deterministic conversation router, a validated creative-coverage ledger, and a floating-window shell. The existing creative controller orchestrates model/storage/view ports, while `app.js` owns terminal integration and `chat.js` remains the formal plan-card executor; only the existing NWLocal/MCP/core boundary may mutate formal workflow state.

**Tech Stack:** Python 3.11 standard library, zero-build browser JavaScript, OpenAI-compatible chat completions, DOM/CSS desktop UI, Node `node:test`, Python `unittest`, local authenticated HTTP bridge.

---

## Preconditions and execution rules

- Work on branch `codex/local-mcp-library-plan`; do not create a new branch unless that branch is unavailable.
- Read the approved design before coding: `docs/superpowers/specs/2026-07-30-structured-workbench-floating-chat-design.md`.
- Preserve the user's separately running ngrok process. The launcher may manage only its own MCP child and cloudflared child.
- Never put an API key in source, fixtures, console output, screenshots, creative exports, or commits.
- Use UTF-8 explicitly for Chinese source and tests on Windows.
- Follow TDD for every task: failing test, observed failure, minimal implementation, focused pass, broader regression, commit.
- Do not combine tasks into one commit. Each task below has an explicit commit boundary so later review or rollback stays local.

## File map and responsibility lock

### Create

- `web/conversation-router.js`: pure deterministic command/natural classification, 15-minute continuity, first-round state, promotion decision, and reset reasons.
- `web/creative-coverage.js`: pure evidence validation, coverage merge, effective/completed round counters, 3/6/10 thresholds, critical-field versioning, and stale checks.
- `web/floating-chat.js`: desktop DOM shell, geometry persistence, drag, resize, minimize, viewport clamp, migration rendering, and operation/busy UI.
- `tests/js/test_conversation_router.mjs`: router classification, timeout, second-turn promotion, and reset tests.
- `tests/js/test_creative_coverage.mjs`: exact-quote evidence, conflict, threshold, assumptions, and stale tests.
- `tests/js/test_floating_chat.mjs`: DOM-free geometry reducer plus fake-DOM lifecycle tests.
- `tests/js/test_workbench_chat_integration.mjs`: static/integration contract for main quick reply, transactional migration, default structured surface, and formal handoff.

### Modify

- `web/local.js`: expose deterministic known-command detection and add `writeCreativeConversationState`.
- `scripts/creative_store.py`: creative schema v2, optional v1 migration, bounded `conversation-state.json`, ZIP inclusion/import.
- `scripts/launch_web.py`: authenticated `POST creative/conversation-state` route.
- `web/creative.js`: v2 empty/merge session and `writeConversationState` across local/browser/memory backends.
- `web/llm.js`: add `extractCoverage`; include coverage in compiler context; retain provider compatibility and typed errors.
- `web/creative-chat.js`: use coverage state machine, operation lifecycle, guided/forced-draft transitions, stale proposals, and validated handoff.
- `web/app.js`: default structured mode, terminal router, first quick round, transactional promotion, book-switch cancellation, and module wiring.
- `web/chat.js`: main quick-card rendering API and formal plan-card handoff only; remove active-book ordinary-input ownership.
- `web/index.html`: structured default DOM, floating window, launcher button, CSS, accessibility, and script order.
- `tests/test_creative_store.py`: v1/v2 state migration, validation, and ZIP tests.
- `tests/test_web_launcher.py`: new route security plus required asset/module/static UI contracts.
- `tests/js/test_creative_adapter.mjs`: conversation-state backend/fallback/ZIP behavior.
- `tests/js/test_local_adapter.mjs`: local bridge route and known-command detection.
- `tests/js/test_llm_adapter.mjs`: coverage extraction request/shape/failure tests.
- `tests/js/test_creative_chat.mjs`: busy lifecycle, coverage transitions, stale proposal, and handoff guard tests.
- `README.md`, `web/README.md`, `CHANGELOG.md`: desktop behavior, persistence contract, migration, and Unreleased entry.

## Shared contracts used by every task

Use these names exactly; do not introduce aliases in later tasks.

```js
// web/conversation-router.js
NWConversationRouter.createRouter({ now, continuityMs, isKnownCommandHead })
router.classify(text) // { kind: "command"|"natural", head }
router.beginNatural(text) // { surface: "main"|"floating", sessionId, quickRound? }
router.completeQuickRound({ sessionId, userTurnId, assistantTurnId, completedAt })
router.reset(reason)
router.snapshot()

// web/creative-coverage.js
NWCreativeCoverage.emptyConversationState()
NWCreativeCoverage.applyExtraction(state, extraction, turns, options)
NWCreativeCoverage.deriveTransition(state)
NWCreativeCoverage.isProposalStale(proposal, state)
NWCreativeCoverage.canHandoff(proposal, state)

// web/floating-chat.js
NWFloatChat.createWindow({ document, storage, viewport, onSubmit, onAction })
floatChat.open(bookId)
floatChat.migrate({ turns, pendingUserTurn })
floatChat.beginOperation({ kind })
floatChat.endOperation({ kind, outcome })
floatChat.minimize()
floatChat.restore()
floatChat.destroy()

// storage/model/controller additions
NWCreative.writeConversationState(state)
NWLocal.writeCreativeConversationState(state)
NWL.extractCoverage({ context, lastUserText })
creativeController.submit(text, { surface })
creativeController.submitProposalToWorkflow()
```

---

### Task 1: Deterministic command and conversation router

**Files:**
- Create: `web/conversation-router.js`
- Create: `tests/js/test_conversation_router.mjs`
- Modify: `web/local.js`
- Modify: `tests/js/test_local_adapter.mjs`
- Modify: `web/index.html`

- [ ] **Step 1: Write failing router tests**

Create `tests/js/test_conversation_router.mjs` with a VM loader matching the existing JS tests and these cases:

```js
test("known commands never enter natural chat", () => {
  const router = create({ known: ["status", "bible", "issue"] });
  assert.equal(router.classify("novel-workflow status .").kind, "command");
  assert.equal(router.classify("nw status .").kind, "command");
  assert.equal(router.classify("status . --human").kind, "command");
  assert.equal(router.classify("bible . --artifact bible.md").kind, "command");
  assert.equal(router.classify("help").kind, "command");
  assert.equal(router.classify("cat workflow.json").kind, "command");
});

test("unknown prose gets one main reply then promotes on second natural input", () => {
  const clock = fakeClock("2026-07-30T00:00:00Z");
  const router = create({ clock });
  const first = router.beginNatural("聊聊主角");
  assert.equal(first.surface, "main");
  router.completeQuickRound({
    sessionId: first.sessionId,
    userTurnId: "u1",
    assistantTurnId: "a1",
    completedAt: clock.now()
  });
  const second = router.beginNatural("他的困境是什么");
  assert.equal(second.surface, "floating");
  assert.deepEqual(second.quickRound, {
    sessionId: first.sessionId,
    userTurnId: "u1",
    assistantTurnId: "a1"
  });
});

test("command and fifteen-minute timeout reset continuity", () => {
  const clock = fakeClock("2026-07-30T00:00:00Z");
  const router = create({ clock });
  const first = router.beginNatural("给我一个方向");
  router.completeQuickRound({ sessionId: first.sessionId, userTurnId: "u1", assistantTurnId: "a1", completedAt: clock.now() });
  router.reset("command");
  assert.equal(router.beginNatural("换个方向").surface, "main");

  const next = router.beginNatural("先聊世界观");
  router.completeQuickRound({ sessionId: next.sessionId, userTurnId: "u2", assistantTurnId: "a2", completedAt: clock.now() });
  clock.advance(15 * 60 * 1000 + 1);
  assert.equal(router.beginNatural("继续").surface, "main");
});
```

Extend `tests/js/test_local_adapter.mjs`:

```js
test("isKnownCommandHead reuses the argv table", () => {
  const NWLocal = loadAdapter().window.NWLocal;
  assert.equal(NWLocal.isKnownCommandHead("idea"), true);
  assert.equal(NWLocal.isKnownCommandHead("outline-lock"), true);
  assert.equal(NWLocal.isKnownCommandHead("聊聊主角"), false);
});
```

- [ ] **Step 2: Run tests and observe the missing modules**

Run:

```powershell
node --test tests/js/test_conversation_router.mjs tests/js/test_local_adapter.mjs
```

Expected: `test_conversation_router.mjs` fails because `web/conversation-router.js` does not exist; local adapter test fails because `isKnownCommandHead` is undefined.

- [ ] **Step 3: Implement the router and command-head export**

Add this pure export beside `ARGV_TABLE` in `web/local.js` and expose it on the public API:

```js
function isKnownCommandHead(head) {
  return Object.prototype.hasOwnProperty.call(ARGV_TABLE, String(head || "").toLowerCase());
}
```

Create `web/conversation-router.js` with this state shape and behavior:

```js
(function () {
  "use strict";
  var AUX = { help: true, ls: true, cat: true, tree: true, clear: true, reset: true };

  function createRouter(options) {
    options = options || {};
    var now = options.now || function () { return Date.now(); };
    var continuityMs = options.continuityMs || 15 * 60 * 1000;
    var isKnownCommandHead = options.isKnownCommandHead || function () { return false; };
    var seq = 0;
    var quick = null;

    function headOf(text) {
      return String(text || "").trim().split(/\s+/)[0].toLowerCase();
    }
    function classify(text) {
      var head = headOf(text);
      if (!head) return { kind: "natural", head: "" };
      if (head === "novel-workflow" || head === "nw" || AUX[head] || isKnownCommandHead(head)) {
        return { kind: "command", head: head };
      }
      return { kind: "natural", head: head };
    }
    function freshSessionId() {
      seq += 1;
      return "quick-" + now().toString(36) + "-" + seq;
    }
    function beginNatural(text) {
      var current = now();
      if (quick && quick.completedAt != null && current - quick.completedAt <= continuityMs) {
        return { surface: "floating", sessionId: quick.sessionId, quickRound: Object.assign({}, quick), text: text };
      }
      quick = { sessionId: freshSessionId(), userTurnId: null, assistantTurnId: null, completedAt: null };
      return { surface: "main", sessionId: quick.sessionId, quickRound: null, text: text };
    }
    function completeQuickRound(record) {
      if (!quick || record.sessionId !== quick.sessionId) return false;
      quick = {
        sessionId: record.sessionId,
        userTurnId: record.userTurnId,
        assistantTurnId: record.assistantTurnId,
        completedAt: Number(record.completedAt)
      };
      return true;
    }
    function reset(reason) { quick = null; return reason || "reset"; }
    function snapshot() { return quick ? JSON.parse(JSON.stringify(quick)) : null; }
    return { classify: classify, beginNatural: beginNatural, completeQuickRound: completeQuickRound, reset: reset, snapshot: snapshot };
  }

  var api = { createRouter: createRouter };
  if (typeof window !== "undefined") window.NWConversationRouter = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
```

Load `conversation-router.js` after `local.js` and before `app.js` in `web/index.html`.

- [ ] **Step 4: Run focused tests**

Run the Step 2 command. Expected: all router and local adapter tests pass.

- [ ] **Step 5: Commit Task 1**

```powershell
git add web/conversation-router.js web/local.js web/index.html tests/js/test_conversation_router.mjs tests/js/test_local_adapter.mjs
git commit -m "feat: route terminal conversations deterministically"
```

---

### Task 2: Creative session schema v2 and conversation-state persistence

**Files:**
- Modify: `scripts/creative_store.py`
- Modify: `scripts/launch_web.py`
- Modify: `web/local.js`
- Modify: `web/creative.js`
- Modify: `tests/test_creative_store.py`
- Modify: `tests/test_web_launcher.py`
- Modify: `tests/js/test_local_adapter.mjs`
- Modify: `tests/js/test_creative_adapter.mjs`

- [ ] **Step 1: Write failing v1/v2 and route tests**

Add to `tests/test_creative_store.py`:

```python
def test_v1_session_gets_empty_conversation_state_without_rewrite(self) -> None:
    creative = self.book / "creative"
    creative.mkdir()
    (creative / "manifest.json").write_text(
        '{"schema_version":1,"turn_count":0,"proposal_count":0,"draft_count":0}',
        encoding="utf-8",
    )
    session = CreativeStore(self.book).read_session()
    self.assertEqual(session["schema_version"], 2)
    self.assertEqual(session["conversation_state"]["phase"], "exploring")
    self.assertFalse((creative / "conversation-state.json").exists())

def test_write_conversation_state_round_trips_and_is_in_zip(self) -> None:
    store = CreativeStore(self.book)
    state = {
        "phase": "collecting", "completed_rounds": 2,
        "effective_rounds": 1, "coverage_version": 1,
        "coverage": {}, "active_proposal_id": None,
    }
    store.write_conversation_state(state)
    self.assertEqual(store.read_session()["conversation_state"], state)
    with zipfile.ZipFile(io.BytesIO(store.export_zip())) as zf:
        self.assertIn("creative-backup/conversation-state.json", zf.namelist())

def test_conversation_state_rejects_invalid_phase_and_negative_counts(self) -> None:
    store = CreativeStore(self.book)
    with self.assertRaisesRegex(CreativeStoreError, "phase"):
        store.write_conversation_state({"phase": "magic"})
    with self.assertRaisesRegex(CreativeStoreError, "completed_rounds"):
        store.write_conversation_state({"phase": "exploring", "completed_rounds": -1})
```

Add an authenticated HTTP test to `tests/test_web_launcher.py` that opens `demo_20260728`, posts `{"conversation_state": state}` to `/api/local/creative/conversation-state`, then reads `/creative/session` and compares the stored value. Also assert the same route returns 404 on the public port.

Add JS adapter tests asserting:

```js
await NWLocal.writeCreativeConversationState(state);
assert.equal(calls[0].url, "/api/local/creative/conversation-state");
assert.deepEqual(JSON.parse(calls[0].opts.body), { conversation_state: state });
```

and browser-storage fallback round-trips `conversation_state` through `NWCreative.boot()`.

- [ ] **Step 2: Run the focused storage tests and verify failure**

```powershell
python -m unittest tests.test_creative_store tests.test_web_launcher.LocalApiTests
node --test tests/js/test_local_adapter.mjs tests/js/test_creative_adapter.mjs
```

Expected: failures mention missing `conversation_state`, missing route, and missing JS methods.

- [ ] **Step 3: Implement schema v2 and the narrow route**

In `scripts/creative_store.py` set `SCHEMA_VERSION = 2`, accept imported schemas `{1, 2}`, and add:

```python
PHASES = {"exploring", "collecting", "guided", "proposal-ready", "proposal", "handed-off"}

def _empty_conversation_state() -> dict[str, Any]:
    return {
        "phase": "exploring",
        "completed_rounds": 0,
        "effective_rounds": 0,
        "coverage_version": 0,
        "coverage": {},
        "active_proposal_id": None,
    }

def write_conversation_state(self, state: Mapping[str, Any]) -> None:
    clean = dict(_empty_conversation_state())
    clean.update(dict(state))
    if clean["phase"] not in PHASES:
        raise CreativeStoreError("conversation state phase is invalid")
    for key in ("completed_rounds", "effective_rounds", "coverage_version"):
        if not isinstance(clean[key], int) or clean[key] < 0:
            raise CreativeStoreError(f"{key} must be a non-negative integer")
    if not isinstance(clean["coverage"], dict):
        raise CreativeStoreError("coverage must be an object")
    if clean["active_proposal_id"] is not None and not isinstance(clean["active_proposal_id"], str):
        raise CreativeStoreError("active_proposal_id must be a string or null")
    self._ensure_root()
    self._atomic_json(self.root / "conversation-state.json", clean)
    self._write_manifest()
```

Return `_empty_conversation_state()` when the file is absent. Include the JSON file in ZIP export/import; v1 imports synthesize the empty state.

In `scripts/launch_web.py` dispatch and serve only this new route:

```python
elif route == ("POST", "creative/conversation-state"):
    self._serve_creative_conversation_state(handler)

def _serve_creative_conversation_state(self, handler):
    body = self._read_json(handler)
    state = body.get("conversation_state")
    if not isinstance(state, dict):
        self._send_error(handler, 400, "bad_request", "conversation_state is required.")
        return
    self._creative_store().write_conversation_state(state)
    self._send_json(handler, 200, {"ok": True})
```

Add `writeCreativeConversationState` to `web/local.js`. In `web/creative.js`, add `conversation_state` to `emptySession`, merge it by replacement, and expose:

```js
function writeConversationState(state) {
  session.conversation_state = clone(state);
  return persist("conversation-state", state).then(function () { notify(); });
}
```

Teach `persist` to call the local method and let browser/memory fallback use the existing full-session save.

- [ ] **Step 4: Run focused storage tests**

Run Step 2. Expected: all focused Python and JS storage/API tests pass.

- [ ] **Step 5: Commit Task 2**

```powershell
git add scripts/creative_store.py scripts/launch_web.py web/local.js web/creative.js tests/test_creative_store.py tests/test_web_launcher.py tests/js/test_local_adapter.mjs tests/js/test_creative_adapter.mjs
git commit -m "feat: persist creative convergence state"
```

---

### Task 3: Pure evidence ledger and program thresholds

**Files:**
- Create: `web/creative-coverage.js`
- Create: `tests/js/test_creative_coverage.mjs`
- Modify: `web/index.html`

- [ ] **Step 1: Write failing coverage tests**

Cover exact quote verification, conflict preservation, completed/effective counters, phase transitions, autonomy assumptions, and stale proposals:

```js
test("evidence quote must exist verbatim in the referenced turn", () => {
  const turns = [{ id: "u1", role: "user", text: "主角是一个害怕真相的法医" }];
  const ok = coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{ field: "protagonist", value: "害怕真相的法医", status: "candidate",
      evidence: [{ turn_id: "u1", quote: "害怕真相的法医" }] }]
  }, turns, { autonomy: false });
  assert.equal(ok.coverage.protagonist.value, "害怕真相的法医");
  assert.throws(() => coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{ field: "protagonist", value: "记者", status: "candidate",
      evidence: [{ turn_id: "u1", quote: "他是一名记者" }] }]
  }, turns, { autonomy: false }), /quote/);
});

test("confirmed evidence cannot be silently overwritten", () => {
  const state = seeded("protagonist", "法医", "confirmed", 1);
  const next = coverage.applyExtraction(state, extraction("protagonist", "记者", "u2", "记者"),
    [{ id: "u2", role: "user", text: "也许换成记者" }], { autonomy: false });
  assert.equal(next.coverage.protagonist.value, "法医");
  assert.equal(next.coverage.protagonist.status, "conflicted");
});

test("program derives proposal guided and forced-draft transitions", () => {
  assert.equal(coverage.deriveTransition(stateWithRequiredFive({ effective: 3 })).phase, "proposal-ready");
  assert.equal(coverage.deriveTransition(emptyAt({ completed: 6, effective: 1 })).phase, "guided");
  assert.equal(coverage.deriveTransition(emptyAt({ completed: 2, effective: 4 })).phase, "guided");
  assert.equal(coverage.deriveTransition(emptyAt({ completed: 10, effective: 0 })).action, "force-draft");
});

test("critical coverage version makes an old proposal stale", () => {
  const state = stateWithRequiredFive({ effective: 3, coverageVersion: 7 });
  assert.equal(coverage.isProposalStale({ coverage_version: 6, status: "pending" }, state), true);
  assert.equal(coverage.canHandoff({ coverage_version: 7, status: "pending", intake: completeIntake() }, state), true);
});
```

- [ ] **Step 2: Run the coverage test and observe module-not-found**

```powershell
node --test tests/js/test_creative_coverage.mjs
```

Expected: failure because `web/creative-coverage.js` does not exist.

- [ ] **Step 3: Implement the pure ledger**

Create the module with constants:

```js
var FIELDS = ["premise", "protagonist", "central_conflict", "stakes", "world", "style_audience", "ending_direction"];
var REQUIRED = ["premise", "protagonist", "central_conflict", "stakes", "style_audience"];
var CRITICAL = { premise: true, protagonist: true, central_conflict: true, stakes: true };
var STATUSES = { candidate: true, confirmed: true, assumed: true, conflicted: true };
```

`applyExtraction` must:

1. clone instead of mutating the input state;
2. reject unknown fields/statuses and empty values;
3. validate every `{turn_id, quote}` against the actual turn text;
4. derive `source_turn_ids` from evidence rather than trusting model output;
5. reject `assumed` unless `options.autonomy === true`;
6. preserve confirmed values and mark conflicts;
7. increment `coverage_version` when a critical field changes;
8. increment `completed_rounds` once per successful reply;
9. increment `effective_rounds` only when evidence changes or `options.explicitDecision` is true;
10. call `deriveTransition` and store the returned phase.

Use this exact transition order:

```js
function deriveTransition(state) {
  var requiredReady = REQUIRED.every(function (key) {
    var item = state.coverage[key];
    return item && item.status !== "conflicted";
  });
  if (requiredReady && state.effective_rounds >= 3) return { phase: "proposal-ready", action: "auto-proposal" };
  if (state.completed_rounds >= 10) return { phase: "guided", action: "force-draft" };
  if (state.completed_rounds >= 6 || state.effective_rounds >= 4) return { phase: "guided", action: "ask-missing" };
  if (Object.keys(state.coverage).length) return { phase: "collecting", action: null };
  return { phase: "exploring", action: null };
}
```

Expose the shared API under `window.NWCreativeCoverage` and CommonJS, then load it after `creative.js` and before `creative-chat.js`.

- [ ] **Step 4: Run coverage tests**

Run Step 2. Expected: all coverage tests pass.

- [ ] **Step 5: Commit Task 3**

```powershell
git add web/creative-coverage.js web/index.html tests/js/test_creative_coverage.mjs
git commit -m "feat: add programmatic creative coverage ledger"
```

---

### Task 4: Structured coverage extraction model call

**Files:**
- Modify: `web/llm.js`
- Modify: `tests/js/test_llm_adapter.mjs`

- [ ] **Step 1: Write failing extractor tests**

Add tests that assert `extractCoverage`:

- sends only bounded turns and the seven allowed field names;
- returns `{items: []}` for valid empty extraction;
- accepts exact evidence records;
- rejects unknown field/status and missing evidence;
- reports provider/parse/schema errors as typed `ModelError`;
- never changes a successful natural reply when extraction fails.

Use this representative response fixture:

```js
const extractionJson = JSON.stringify({
  items: [{
    field: "premise",
    value: "未清理的犯罪现场成为家族秘密的钥匙",
    status: "candidate",
    evidence: [{ turn_id: "u1", quote: "犯罪现场成为家族秘密的钥匙" }]
  }]
});
```

- [ ] **Step 2: Run the LLM adapter test and verify failure**

```powershell
node --test tests/js/test_llm_adapter.mjs
```

Expected: `NWL.extractCoverage is not a function`.

- [ ] **Step 3: Implement `extractCoverage`**

Add a separate low-temperature request; do not reuse the creative reply or compiler response:

```js
function buildCoverageMessages(input) {
  var ctx = input.context || {};
  var turns = (ctx.turns || []).slice(-10);
  var allowed = ["premise", "protagonist", "central_conflict", "stakes", "world", "style_audience", "ending_direction"];
  return [{
    role: "system",
    content: [
      "从对话中抽取新增或修正的小说结构素材，只返回严格 JSON。",
      "格式：{\"items\":[{\"field\":字段,\"value\":内容,\"status\":\"candidate|confirmed|assumed|conflicted\",\"evidence\":[{\"turn_id\":消息ID,\"quote\":消息中的逐字片段}]}]}",
      "允许字段：" + allowed.join(", "),
      "不得编造 quote；没有可靠证据时返回 {\"items\":[]}",
      "autonomy=" + (input.autonomy ? "true" : "false"),
      JSON.stringify(turns)
    ].join("\n")
  }, { role: "user", content: "抽取本轮新增素材" }];
}

function extractCoverage(input) {
  return requestText(buildCoverageMessages(input), { temperature: 0.1, maxTokens: 1200, json: true })
    .then(extractJson)
    .then(function (parsed) {
      if (!parsed || !Array.isArray(parsed.items)) throw new ModelError("schema_error", "素材抽取缺少 items");
      return parsed;
    });
}
```

Export `extractCoverage`. Keep `assessReadiness` temporarily for backward compatibility, but the controller must stop using it in Task 5.

- [ ] **Step 4: Run LLM adapter tests**

Run Step 2. Expected: all tests pass, including existing provider compatibility cases.

- [ ] **Step 5: Commit Task 4**

```powershell
git add web/llm.js tests/js/test_llm_adapter.mjs
git commit -m "feat: extract cited creative evidence"
```

---

### Task 5: Creative controller convergence, busy lifecycle, and stale proposals

**Files:**
- Modify: `web/creative-chat.js`
- Modify: `tests/js/test_creative_chat.mjs`

- [ ] **Step 1: Extend fake ports and write failing controller tests**

Extend the fake view with `operations`, `coverage`, `guided`, and `stale` records. Add tests:

```js
test("natural reply has a balanced operation lifecycle", async () => {
  const ports = fakePorts({ reply: "先从旧案切入。", extraction: { items: [] } });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.submit("聊聊方向", { surface: "floating" });
  assert.deepEqual(ports.view.operations, [
    { type: "begin", kind: "reply", surface: "floating" },
    { type: "end", kind: "reply", outcome: "success" }
  ]);
});

test("reply persists even when coverage extraction fails", async () => {
  const ports = fakePorts({ extractionError: new Error("extract failed") });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.submit("继续", { surface: "floating" });
  assert.deepEqual(ports.storage.turns.map((t) => t.role), ["user", "assistant"]);
  assert.equal(ports.storage.conversationStates.length, 0);
});

test("six rounds guide and ten rounds force a draft", async () => {
  const ports = fakePorts({ storedSession: sessionAtRound(5) });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.submit("继续补充", { surface: "floating" });
  assert.equal(ports.view.guided.at(-1).phase, "guided");

  ports.storage.setConversationState(stateAtRound(9));
  await controller.submit("再聊一次", { surface: "floating" });
  assert.equal(ports.model.compilerInputs.at(-1).forcedDraft, true);
});

test("critical evidence change makes proposal stale and blocks handoff", async () => {
  const ports = fakePorts({ storedSession: sessionWithProposalAtVersion(2), extraction: criticalUpdateAtVersion(3) });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.submit("主角改成记者", { surface: "floating" });
  assert.equal(ports.view.stale.at(-1), true);
  await controller.submitProposalToWorkflow();
  assert.equal(ports.executor.offered.length, 0);
});
```

- [ ] **Step 2: Run controller tests and observe missing lifecycle/state APIs**

```powershell
node --test tests/js/test_creative_chat.mjs
```

Expected: failures for missing view lifecycle, storage state writes, extraction, and handoff guard.

- [ ] **Step 3: Refactor the controller around the shared contracts**

Make `submit(text, options)` execute this order:

```js
view.beginOperation({ kind: "reply", surface: options.surface });
persist user turn;
model.creativeReply(...);
render and persist assistant turn;
view.endOperation({ kind: "reply", outcome: "success" });
model.extractCoverage(...);
coverage.applyExtraction(...);
storage.writeConversationState(nextState);
view.renderCoverage(nextState.coverage);
apply transition action;
```

On reply failure call `endOperation({kind:"reply", outcome:"error"})`, show the typed error, and keep the user turn. On extraction failure do not roll back the reply; increment a controller-only consecutive extraction failure counter and render the manual checklist after two failures.

Replace `assessReadiness` calls with coverage transitions. For `auto-proposal`, invoke `generateProposal({ automatic: true })`; for `ask-missing`, call `view.renderGuidedMode(missingFields)`; for `force-draft`, call the compiler with `{ forcedDraft: true }`.

Proposal records must include:

```js
proposal.coverage_version = conversationState.coverage_version;
proposal.coverage_snapshot = conversationState.coverage;
proposal.status = "pending";
```

Expose `submitProposalToWorkflow`; it calls `NWCreativeCoverage.canHandoff`, writes `accepted`, offers the external plan, and persists phase `handed-off`. Keep `acceptProposal` as a compatibility alias that calls the new method.

Every `beginOperation` must be paired from a `finally`-equivalent path so success, provider error, timeout, book switch, and clear leave no busy state.

- [ ] **Step 4: Run controller plus coverage tests**

```powershell
node --test tests/js/test_creative_chat.mjs tests/js/test_creative_coverage.mjs
```

Expected: all tests pass.

- [ ] **Step 5: Commit Task 5**

```powershell
git add web/creative-chat.js tests/js/test_creative_chat.mjs
git commit -m "feat: converge creative sessions programmatically"
```

---

### Task 6: Desktop floating chat shell and geometry persistence

**Files:**
- Create: `web/floating-chat.js`
- Create: `tests/js/test_floating_chat.mjs`
- Modify: `web/index.html`
- Modify: `tests/test_web_launcher.py`

- [ ] **Step 1: Write failing geometry and lifecycle tests**

Test the pure geometry reducer independently of DOM:

```js
test("default and restored geometry stay inside the viewport", () => {
  assert.deepEqual(floatApi.clampGeometry(null, { width: 1440, height: 900 }),
    { width: 420, height: 560, left: 1008, top: 328 });
  assert.deepEqual(floatApi.clampGeometry(
    { width: 900, height: 900, left: -50, top: 1000 },
    { width: 1200, height: 800 }
  ), { width: 720, height: 680, left: 12, top: 108 });
});

test("migration renders before source removal is acknowledged", async () => {
  const shell = floatApi.createWindow(fakeOptions());
  const result = await shell.migrate({
    turns: [{ id: "u1", role: "user", text: "方向" }, { id: "a1", role: "assistant", text: "悬疑" }],
    pendingUserTurn: { id: "u2", role: "user", text: "继续" }
  });
  assert.equal(result.rendered, true);
  assert.deepEqual(shell.messageIds(), ["u1", "a1", "u2"]);
});

test("operation nodes are unique and always removable", () => {
  const shell = floatApi.createWindow(fakeOptions());
  shell.beginOperation({ kind: "reply" });
  shell.beginOperation({ kind: "reply" });
  assert.equal(shell.busyCount(), 1);
  shell.endOperation({ kind: "reply", outcome: "error" });
  assert.equal(shell.busyCount(), 0);
});
```

Add static asset assertions to `tests/test_web_launcher.py` for `id="creative-float"`, titlebar, minimize/close controls, resize handle, launcher button, `aria-live`, and `floating-chat.js` script inclusion.

- [ ] **Step 2: Run tests and observe missing shell/assets**

```powershell
node --test tests/js/test_floating_chat.mjs
python -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests
```

Expected: missing module and missing DOM asset failures.

- [ ] **Step 3: Implement geometry reducer and DOM shell**

Implement constants exactly:

```js
var DEFAULT_SIZE = { width: 420, height: 560 };
var MIN_SIZE = { width: 340, height: 360 };
var EDGE = 12;
var STORAGE_KEY = "nwa.float-chat.geometry.v1";
```

`clampGeometry` must cap width at 80% viewport, height at 85%, then clamp `left/top` to 12px edges. Default placement is bottom-right. Persist `{width,height,left,top,minimized}` only after pointer-up, resize end, minimize, and close; do not write on every pointer move.

Add DOM IDs:

```html
<button id="creative-float-launcher" aria-label="打开自由对话">对话</button>
<section id="creative-float" hidden aria-label="自由对话窗口">
  <header id="creative-float-titlebar">
    <strong>自由对话</strong>
    <span id="creative-float-state" aria-live="polite"></span>
    <button id="creative-float-minimize" aria-label="最小化自由对话">—</button>
    <button id="creative-float-close" aria-label="隐藏自由对话">×</button>
  </header>
  <div id="creative-float-messages"></div>
  <div id="creative-float-coverage"></div>
  <div id="creative-float-proposal"></div>
  <div id="creative-float-composer">
    <input id="creative-float-input" aria-label="自由对话消息">
    <button id="creative-float-send">发送</button>
  </div>
  <div id="creative-float-resize" role="separator" aria-label="调整自由对话窗口大小"></div>
</section>
```

Use `position: fixed`; set `z-index` above drawers; apply the existing `.chat-typing` three-dot markup from `beginOperation`. Under `prefers-reduced-motion`, keep static dots.

- [ ] **Step 4: Run floating shell/static tests**

Run Step 2. Expected: all tests pass.

- [ ] **Step 5: Commit Task 6**

```powershell
git add web/floating-chat.js web/index.html tests/js/test_floating_chat.mjs tests/test_web_launcher.py
git commit -m "feat: add persistent desktop chat window"
```

---

### Task 7: Main quick reply and transactional second-turn migration

**Files:**
- Create: `tests/js/test_workbench_chat_integration.mjs`
- Modify: `web/app.js`
- Modify: `web/chat.js`
- Modify: `web/index.html`
- Modify: `tests/test_web_launcher.py`

- [ ] **Step 1: Write failing integration contracts**

Create a source/VM integration test that asserts:

```js
test("main terminal routes command directly and natural text through quick chat", () => {
  assert.match(appSource, /conversationRouter\.classify\(v\)/);
  assert.match(appSource, /classification\.kind === "command"/);
  assert.match(appSource, /startQuickConversation\(v\)/);
});

test("second natural input migrates before its model reply", () => {
  const migration = sourceBetween(appSource, "function promoteQuickConversation", "function cancelConversationUi");
  assert.ok(migration.indexOf("floatChat.migrate") < migration.indexOf("creativeController.submit"));
  assert.ok(migration.indexOf("removeQuickConversation") > migration.indexOf("rendered"));
});

test("structured workbench is the default surface", () => {
  assert.doesNotMatch(appSource, /setMode\("white"\).*boot/);
  assert.match(htmlSource, /id="mode-enc" class="on"/);
});
```

Extend static Python tests to assert the quick-card container exists inside the terminal panel and the old full-width `body.white main` default does not activate on boot.

- [ ] **Step 2: Run integration/static tests and verify failure**

```powershell
node --test tests/js/test_workbench_chat_integration.mjs
python -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests
```

Expected: missing integration functions/DOM contracts.

- [ ] **Step 3: Wire the router, quick card, controller, and float shell**

Expose a main quick-card view from `chat.js`:

```js
window.NWQuickChat = {
  begin: function (sessionId, userTurn) {},
  beginOperation: function (sessionId) {},
  complete: function (sessionId, assistantTurn) {},
  fail: function (sessionId, error) {},
  getTurnIds: function (sessionId) {},
  remove: function (sessionId) {},
  collapse: function (sessionId) {}
};
```

Quick nodes must use `data-quick-session` and `data-turn-id`; `remove` may only delete nodes with the requested session id.

In `app.js`, create one router using `NWLocal.isKnownCommandHead`. Replace terminal Enter handling:

```js
var classification = conversationRouter.classify(v);
if (classification.kind === "command") {
  conversationRouter.reset("command");
  enqueue(function () { return handleLine(v); });
  return;
}
var decision = conversationRouter.beginNatural(v);
if (decision.surface === "main") startQuickConversation(v, decision);
else promoteQuickConversation(v, decision);
```

`startQuickConversation` must call `creativeController.submit(text, {surface:"main", view: quickView})` and complete the router only after both persisted turns exist.

`promoteQuickConversation` must:

1. resolve the two stored turn ids from `NWCreative.session()`;
2. append/persist the second user turn exactly once;
3. call `floatChat.migrate`;
4. remove main nodes only when migration returns `{rendered:true}`;
5. call the controller for the assistant half without re-appending the second user turn;
6. on failure retain/collapse the main card and expose Retry.

Add a direct launcher-button path that opens the float shell and binds its composer immediately.

On command, 15-minute timeout, book switch, or explicit end, call `router.reset(reason)`. Book switch also cancels UI operations and loads the new book before accepting another message.

- [ ] **Step 4: Run integration plus controller/router tests**

```powershell
node --test tests/js/test_workbench_chat_integration.mjs tests/js/test_conversation_router.mjs tests/js/test_creative_chat.mjs tests/js/test_floating_chat.mjs
python -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests
```

Expected: all focused tests pass.

- [ ] **Step 5: Commit Task 7**

```powershell
git add web/app.js web/chat.js web/index.html tests/js/test_workbench_chat_integration.mjs tests/test_web_launcher.py
git commit -m "feat: promote continued chat into floating window"
```

---

### Task 8: Validated proposal handoff to the structured workbench

**Files:**
- Modify: `web/creative-chat.js`
- Modify: `web/floating-chat.js`
- Modify: `web/chat.js`
- Modify: `web/app.js`
- Modify: `tests/js/test_creative_chat.mjs`
- Modify: `tests/js/test_workbench_chat_integration.mjs`

- [ ] **Step 1: Write failing handoff tests**

Add controller tests:

```js
test("incomplete forced draft cannot enter the workbench", async () => {
  const ports = fakePorts({ storedSession: incompleteForcedDraftSession() });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.submitProposalToWorkflow();
  assert.equal(ports.executor.offered.length, 0);
  assert.match(ports.view.errors.at(-1).message, /缺少|未完成/);
});

test("valid proposal requires float submit then workbench execute", async () => {
  const ports = fakePorts({ storedSession: validProposalSession() });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.submitProposalToWorkflow();
  assert.equal(ports.executor.offered.length, 1);
  assert.equal(ports.executor.executed.length, 0);
  assert.equal(ports.storage.latestConversationState.phase, "handed-off");
});
```

Add integration assertions that a handoff minimizes the float, switches/scrolls to the structured workbench, and renders the existing plan card; it must not call `NWB.runSmart` until the plan card execute action.

- [ ] **Step 2: Run handoff tests and verify failure**

```powershell
node --test tests/js/test_creative_chat.mjs tests/js/test_workbench_chat_integration.mjs
```

Expected: incomplete/stale handoff is not guarded or phase/minimize integration is missing.

- [ ] **Step 3: Implement the two independent confirmation gates**

In the float proposal card expose these actions:

- `继续讨论`
- `重新编译`
- `由模型补齐缺项` when autonomy is false and required evidence is missing
- `提交到主流程` enabled only when `canHandoff` is true

On submit, the controller re-reads storage state, rejects stale/incomplete coverage, writes proposal `accepted`, writes phase `handed-off`, then calls `executor.offerExternalPlan(plan)`.

In `app.js`, the executor callback must:

```js
floatChat.minimize();
document.body.classList.remove("white");
document.getElementById("term-panel").scrollIntoView({ block: "nearest" });
window.NWC.offerExternalPlan(plan);
```

The existing plan-card `执行` handler remains the only place that calls `NWB.runSmart`. After success, mark proposal `committed`; after failure, leave it `accepted` and display the core error.

- [ ] **Step 4: Run handoff/controller tests**

Run Step 2. Expected: all tests pass and executor is still untouched before the second confirmation.

- [ ] **Step 5: Commit Task 8**

```powershell
git add web/creative-chat.js web/floating-chat.js web/chat.js web/app.js tests/js/test_creative_chat.mjs tests/js/test_workbench_chat_integration.mjs
git commit -m "feat: hand validated proposals to the workbench"
```

---

### Task 9: Documentation, asset contract, and complete automated regression

**Files:**
- Modify: `README.md`
- Modify: `web/README.md`
- Modify: `CHANGELOG.md`
- Modify: `tests/test_web_launcher.py`

- [ ] **Step 1: Add failing final asset/security contracts**

Update `WebLibraryPanelAssetTests` to assert all new scripts load before `app.js`, the structured mode is default, quick/floating DOM controls exist, reduced-motion CSS exists, and the public handler still has no `/api/local/creative/*` routes.

Add a deny-list-oriented assertion that the three new JS modules contain no key-shaped fixture or fixed provider endpoint.

- [ ] **Step 2: Run final static contracts and verify documentation gaps**

```powershell
python -m unittest tests.test_web_launcher.WebLibraryPanelAssetTests tests.test_web_launcher.LocalApiTests
```

Expected before docs/assets are complete: one or more new static contract assertions fail.

- [ ] **Step 3: Document the final behavior**

Update documentation with these exact user-visible rules:

- structured desktop workbench is the default;
- first natural-language reply appears temporarily in the main terminal area;
- second natural message migrates to the floating window;
- floating geometry is browser-local, while conversation/coverage/proposals are book-local and ZIP-backed;
- 6 completed rounds enter guided mode and 10 completed rounds force a structured draft;
- only float submit plus workbench execute may mutate formal state;
- command allowlist never delegates execution classification to the model;
- no mobile guarantee in this release.

Add a concise Unreleased CHANGELOG entry. Do not duplicate the full design spec.

- [ ] **Step 4: Run every JS and Python test plus release check**

```powershell
$files = Get-ChildItem tests/js/test_*.mjs | Sort-Object Name
foreach ($file in $files) {
  node --test $file.FullName
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
python -m unittest discover -s tests
python scripts/release_check.py
```

Expected: every JS suite passes; Python reports no failures; final output contains `RELEASE_CHECK_PASS`.

- [ ] **Step 5: Commit Task 9**

```powershell
git add README.md web/README.md CHANGELOG.md tests/test_web_launcher.py
git commit -m "docs: explain structured workbench conversations"
```

---

### Task 10: Windows launcher and real-browser acceptance

**Files:**
- Modify only if acceptance reveals a defect: files owned by Tasks 1–9
- Do not commit screenshots, logs, downloaded ZIPs, or QA books

- [ ] **Step 1: Run headless local/public isolation acceptance**

```powershell
python _local_acceptance.py
```

Expected: all eight steps pass; local capabilities return 200 with token; public capabilities return 404; both ports and MCP child close cleanly.

- [ ] **Step 2: Restart only this repository's launcher**

Before stopping anything, inspect PID command lines for ports 8080/8081 and verify they belong to `F:\bookworkflow\scripts\launch_web.py`. Stop only that launcher and its verified descendants. Do not stop PID/name matches belonging to `F:\feishu_mcp` or ngrok.

Start through:

```powershell
Start-Process -FilePath "$env:ComSpec" -ArgumentList '/c','一键启动.cmd' -WorkingDirectory 'F:\bookworkflow' -WindowStyle Hidden
```

Expected: 8080 and 8081 listen; one launcher-owned cloudflared process targets 8081; unrelated ngrok remains alive.

- [ ] **Step 3: Verify page health in Browser before interaction**

Using the Browser plugin, verify:

- page URL/title are correct;
- meaningful structured workbench DOM is present;
- no framework overlay;
- no relevant console error/warning;
- desktop screenshot shows pipeline, terminal, and files as the main surface.

- [ ] **Step 4: Verify quick reply and transactional promotion**

With an existing QA book or a clearly labeled QA turn:

1. enter one natural-language message in the main terminal;
2. verify user bubble, three-dot animation, natural reply, and continuation hint;
3. enter a second natural message;
4. verify the float opens before the second reply;
5. verify first user/assistant plus second user are present in the float;
6. verify main quick nodes disappear only after successful rendering;
7. verify the second reply and animation occur only in the float;
8. reload and confirm conversation restores in the float but not as main quick cards.

- [ ] **Step 5: Verify geometry and command isolation**

Drag, resize, minimize, restore, scroll the main page, and reload. Confirm geometry persists and remains within 12px viewport bounds. Then submit one known command and one intentionally invalid `novel-workflow` command; both must stay in the terminal and neither may open the float.

- [ ] **Step 6: Verify convergence and handoff without bypass**

Use seeded browser/controller fixtures for 6/10 thresholds if producing ten real model turns is costly. Verify guided mode, forced draft, incomplete submit disabled, autonomy assumptions visible, stale proposal blocking, first float confirmation, main plan card, and no core mutation before the final execute click.

- [ ] **Step 7: Verify all animation termination paths**

Exercise success, provider error, timeout simulation, minimize during generation, close during generation, and book switch. After every path assert there is no `.chat-typing` node and send controls are enabled again.

- [ ] **Step 8: Final repository audit and handoff commit if needed**

```powershell
git diff --check
git status --short --branch
git log --oneline --decorate -12
```

Expected: clean working tree, no untracked QA artifacts, all Task 1–9 commits visible in order. If Task 10 required a defect fix, repeat the relevant focused test and full release check, then commit only that fix as `fix: complete floating chat acceptance`.

---

## Definition of done

- The structured workbench is the default desktop surface.
- First natural input receives exactly one main-window response.
- Second continuous natural input migrates transactionally and replies in the float.
- Known and invalid-prefixed commands never become natural chat.
- The float is fixed to viewport, draggable, resizable, minimizable, accessible, and geometry-persistent.
- Conversation, evidence ledger, and proposals persist per book through local/browser/memory and ZIP paths.
- Exact evidence quotes validate against real turn text.
- Program state, not readiness prose, drives automatic proposal, guided mode, and forced draft.
- Busy animation appears and cleans up on every model operation/termination path.
- Stale or incomplete proposals cannot enter the workbench.
- Float submit and workbench execute remain two independent gates.
- Local/public isolation, launcher cleanup, cloudflared ownership, and unrelated ngrok survival pass.
- All JS/Python/release checks pass and the repository is clean.
