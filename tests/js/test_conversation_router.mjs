/* Tests for web/conversation-router.js — deterministic command/natural
 * classification, 15-minute continuity, first-round state, second-turn
 * promotion, and reset reasons.
 *
 *   node --test tests/js/test_conversation_router.mjs
 *
 * Loads conversation-router.js by evaluating it in a Node vm context with a
 * stub window/module so the IIFE-bound module runs without a browser.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import vm from "node:vm";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const routerJsPath = resolve(__dirname, "..", "..", "web", "conversation-router.js");

function loadRouter() {
  const src = readFileSync(routerJsPath, "utf8");
  const moduleObj = { exports: {} };
  const sandbox = {
    module: moduleObj,
    exports: moduleObj.exports,
    window: {},
    console: console,
  };
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox, { filename: "web/conversation-router.js" });
  return moduleObj.exports;
}

const NWConversationRouter = loadRouter();

// Cross-realm deep-equal: objects created inside the vm context have a
// different Object.prototype than the test realm, and node:assert/strict
// treats deepEqual as strict. Compare via JSON so the assertion is
// realm-agnostic (mirrors the eqObj helper in test_local_adapter.mjs).
function deepEq(actual, expected, msg) {
  const norm = (o) => {
    if (o === null || typeof o !== "object") return JSON.stringify(o);
    if (Array.isArray(o)) return "[" + o.map(norm).join(",") + "]";
    const keys = Object.keys(o).sort();
    return "{" + keys.map(k => JSON.stringify(k) + ":" + norm(o[k])).join(",") + "}";
  };
  const a = norm(actual);
  const e = norm(expected);
  assert.equal(a, e, msg || ("expected " + e + " got " + a));
}

function fakeClock(iso) {
  let t = Date.parse(iso);
  return {
    now: () => t,
    advance: (ms) => { t += ms; },
  };
}

function create(opts) {
  opts = opts || {};
  const known = opts.known ? new Set(opts.known) : null;
  return NWConversationRouter.createRouter({
    now: opts.clock ? opts.clock.now : undefined,
    isKnownCommandHead: known ? (h) => known.has(h) : undefined,
  });
}

// ---------------- classification ----------------

test("known commands never enter natural chat", () => {
  const router = create({ known: ["status", "bible", "issue"] });
  assert.equal(router.classify("novel-workflow status .").kind, "command");
  assert.equal(router.classify("nw status .").kind, "command");
  assert.equal(router.classify("status . --human").kind, "command");
  assert.equal(router.classify("bible . --artifact bible.md").kind, "command");
  assert.equal(router.classify("help").kind, "command");
  assert.equal(router.classify("cat workflow.json").kind, "command");
});

test("auxiliary commands ls/tree/clear/reset are commands", () => {
  const router = create({ known: ["status"] });
  assert.equal(router.classify("ls").kind, "command");
  assert.equal(router.classify("tree").kind, "command");
  assert.equal(router.classify("clear").kind, "command");
  assert.equal(router.classify("reset").kind, "command");
});

test("empty or whitespace input is natural with empty head", () => {
  const router = create({});
  assert.equal(router.classify("").kind, "natural");
  assert.equal(router.classify("   ").kind, "natural");
  assert.equal(router.classify("").head, "");
});

test("unknown prose is natural", () => {
  const router = create({ known: ["status", "bible", "issue"] });
  assert.equal(router.classify("聊聊主角").kind, "natural");
  assert.equal(router.classify("他的困境是什么").kind, "natural");
  assert.equal(router.classify("给我一个方向").kind, "natural");
});

test("classify does not mutate router state", () => {
  const router = create({ known: ["status"] });
  router.classify("novel-workflow status .");
  router.classify("随便聊聊");
  assert.equal(router.snapshot(), null);
});

// ---------------- first round / promotion ----------------

test("unknown prose gets one main reply then promotes on second natural input", () => {
  const clock = fakeClock("2026-07-30T00:00:00Z");
  const router = create({ clock });
  const first = router.beginNatural("聊聊主角");
  assert.equal(first.surface, "main");
  assert.equal(first.quickRound, null);
  router.completeQuickRound({
    sessionId: first.sessionId,
    userTurnId: "u1",
    assistantTurnId: "a1",
    completedAt: clock.now(),
  });
  const second = router.beginNatural("他的困境是什么");
  assert.equal(second.surface, "floating");
  deepEq(second.quickRound, {
    sessionId: first.sessionId,
    userTurnId: "u1",
    assistantTurnId: "a1",
  });
});

test("first natural input without a completed round stays on main", () => {
  const clock = fakeClock("2026-07-30T00:00:00Z");
  const router = create({ clock });
  const first = router.beginNatural("给我一个方向");
  assert.equal(first.surface, "main");
  // no completeQuickRound yet
  const second = router.beginNatural("继续聊");
  assert.equal(second.surface, "main");
  assert.equal(second.quickRound, null);
});

test("sessionId is stable for the same quick sequence", () => {
  const clock = fakeClock("2026-07-30T00:00:00Z");
  const router = create({ clock });
  const first = router.beginNatural("聊聊主角");
  router.completeQuickRound({
    sessionId: first.sessionId,
    userTurnId: "u1",
    assistantTurnId: "a1",
    completedAt: clock.now(),
  });
  const second = router.beginNatural("继续");
  assert.equal(second.sessionId, first.sessionId);
});

// ---------------- reset / timeout ----------------

test("command and fifteen-minute timeout reset continuity", () => {
  const clock = fakeClock("2026-07-30T00:00:00Z");
  const router = create({ clock });
  const first = router.beginNatural("给我一个方向");
  router.completeQuickRound({
    sessionId: first.sessionId,
    userTurnId: "u1",
    assistantTurnId: "a1",
    completedAt: clock.now(),
  });
  router.reset("command");
  assert.equal(router.beginNatural("换个方向").surface, "main");

  const next = router.beginNatural("先聊世界观");
  router.completeQuickRound({
    sessionId: next.sessionId,
    userTurnId: "u2",
    assistantTurnId: "a2",
    completedAt: clock.now(),
  });
  clock.advance(15 * 60 * 1000 + 1);
  assert.equal(router.beginNatural("继续").surface, "main");
});

test("just-under-fifteen-minutes still promotes", () => {
  const clock = fakeClock("2026-07-30T00:00:00Z");
  const router = create({ clock });
  const first = router.beginNatural("给我一个方向");
  router.completeQuickRound({
    sessionId: first.sessionId,
    userTurnId: "u1",
    assistantTurnId: "a1",
    completedAt: clock.now(),
  });
  clock.advance(15 * 60 * 1000);
  assert.equal(router.beginNatural("继续").surface, "floating");
});

test("reset returns the reason and clears snapshot", () => {
  const clock = fakeClock("2026-07-30T00:00:00Z");
  const router = create({ clock });
  router.beginNatural("聊");
  assert.equal(router.reset("command"), "command");
  assert.equal(router.snapshot(), null);
});

test("completeQuickRound ignores mismatched sessionId", () => {
  const clock = fakeClock("2026-07-30T00:00:00Z");
  const router = create({ clock });
  const first = router.beginNatural("聊");
  const ok = router.completeQuickRound({
    sessionId: "wrong-id",
    userTurnId: "u1",
    assistantTurnId: "a1",
    completedAt: clock.now(),
  });
  assert.equal(ok, false);
  // sequence still incomplete -> next natural stays main
  assert.equal(router.beginNatural("继续").surface, "main");
});

test("snapshot returns a deep copy", () => {
  const clock = fakeClock("2026-07-30T00:00:00Z");
  const router = create({ clock });
  const first = router.beginNatural("聊");
  router.completeQuickRound({
    sessionId: first.sessionId,
    userTurnId: "u1",
    assistantTurnId: "a1",
    completedAt: clock.now(),
  });
  const snap = router.snapshot();
  assert.equal(snap.userTurnId, "u1");
  snap.userTurnId = "tampered";
  assert.equal(router.snapshot().userTurnId, "u1");
});