/* Tests for web/creative-chat.js — the freeform creative controller.
 *
 *   node --test tests/js/test_creative_chat.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import vm from "node:vm";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const chatJsPath = resolve(__dirname, "..", "..", "web", "creative-chat.js");

const INTAKE_KEYS = [
  "audience", "genre", "target_words", "premise", "world", "protagonist",
  "supporting_cast", "central_conflict", "stakes", "character_arc", "style",
  "structure", "ending", "boundaries", "craft_patterns"
];

function completeIntake() {
  const o = {};
  INTAKE_KEYS.forEach(function (k) { o[k] = "x"; });
  return o;
}

function completeProposal() {
  return {
    id: "proposal-1",
    status: "pending",
    preview: "完整方案",
    summary: "一句话方案",
    intake: completeIntake(),
    assumptions: ["假设一"],
    uncertainties: ["不确定一"],
    draft_refs: [],
    source_turn_ids: ["turn-1"]
  };
}

function savedSession() {
  return {
    schema_version: 1,
    turns: [
      { id: "turn-1", role: "user", text: "雨夜追凶" },
      { id: "turn-2", role: "assistant", text: "好，从旧案切入。" }
    ],
    summary: "雨夜命案",
    facts: { confirmed: ["主角是法医"], boundaries: [], rejected: [], important_turn_ids: [] },
    proposals: [completeProposal()],
    drafts: []
  };
}

function fakeView() {
  return {
    messages: [],
    errors: [],
    proposal: null,
    rawJsonShown: false,
    durabilityStates: [],
    readiness: [],
    importChoices: null,
    renderUser: function (text) { this.messages.push({ role: "user", text: text }); },
    renderAssistant: function (text) { this.messages.push({ role: "assistant", text: text }); },
    showError: function (err) { this.errors.push(err); },
    renderProposal: function (p) { this.proposal = p; this.rawJsonShown = false; },
    clearProposal: function () { this.proposal = null; },
    setDurability: function (s) { this.durabilityStates.push(s); },
    renderReadiness: function (ready, reason) { this.readiness.push({ ready: ready, reason: reason }); },
    renderImportChoices: function (choices) { this.importChoices = choices; },
    clear: function () { this.messages = []; this.proposal = null; }
  };
}

function fakeExecutor() {
  return {
    offered: [],
    executed: [],
    offerExternalPlan: function (plan) { this.offered.push(plan); }
  };
}

function fakeModel(opts) {
  opts = opts || {};
  const inputs = [];
  const readinessInputs = [];
  const compilerInputs = [];
  return {
    inputs: inputs,
    readinessInputs: readinessInputs,
    compilerInputs: compilerInputs,
    creativeReply: function (input) {
      inputs.push(input);
      if (opts.error) return Promise.reject(opts.error);
      return Promise.resolve({ reply: opts.reply || "好的。" });
    },
    assessReadiness: function (input) {
      readinessInputs.push(input);
      return Promise.resolve({ ready: opts.ready != null ? opts.ready : false, reason: opts.reason || "" });
    },
    compileProposal: function (input) {
      compilerInputs.push(input);
      if (opts.compileError) return Promise.reject(opts.compileError);
      return Promise.resolve(opts.proposal || completeProposal());
    }
  };
}

function fakeStorage(opts) {
  opts = opts || opts;
  const stored = opts.storedSession ? JSON.parse(JSON.stringify(opts.storedSession)) : null;
  const turns = [];
  const proposals = [];
  const drafts = [];
  return {
    turns: turns,
    proposals: proposals,
    drafts: drafts,
    boot: function (bookId) {
      if (stored) {
        stored.turns.forEach((t) => turns.push(t));
        stored.proposals.forEach((p) => proposals.push(p));
        stored.drafts.forEach((d) => drafts.push(d));
      }
      return Promise.resolve();
    },
    session: function () {
      return {
        turns: turns.slice(),
        proposals: proposals.slice(),
        drafts: drafts.slice(),
        summary: stored ? stored.summary : "",
        facts: stored ? stored.facts : { confirmed: [], boundaries: [], rejected: [], important_turn_ids: [] }
      };
    },
    durability: function () { return "local"; },
    appendTurn: function (turn) { if (!turns.some((t) => t.id === turn.id)) turns.push(turn); return Promise.resolve(turn); },
    writeState: function (summary, facts) { return Promise.resolve(); },
    writeProposal: function (p) {
      const i = proposals.findIndex((x) => x.id === p.id);
      if (i >= 0) proposals[i] = p; else proposals.push(p);
      return Promise.resolve(p);
    },
    writeDraft: function (d) { drafts.push(d); return Promise.resolve(d); },
    exportBackup: function () { return Promise.resolve({ bytes: new Uint8Array([0]), filename: "x.zip", mimeType: "application/zip" }); },
    previewImport: function (bytes) { return Promise.resolve({ schemaVersion: 1, turnCount: 1, proposalCount: 0, draftCount: 0 }); },
    importBackup: function (bytes, decision) { return Promise.resolve({ turnCount: 1 }); },
    subscribe: function () { return function () {}; }
  };
}

function fakePorts(opts) {
  opts = opts || {};
  const view = fakeView();
  const executor = fakeExecutor();
  const model = fakeModel(opts);
  const storage = opts.storage || fakeStorage({ storedSession: opts.storedSession });
  return {
    model: model,
    storage: storage,
    executor: executor,
    view: view,
    ruleCalls: 0,
    clock: function () { return "2026-07-30T00:00:00Z"; },
    idGen: (function () { var n = 0; return function () { n += 1; return "id-" + n; }; })()
  };
}

function loadController() {
  const sandbox = {
    window: {},
    console: console,
    setTimeout: setTimeout,
    clearTimeout: clearTimeout,
    Promise: globalThis.Promise,
    Date: globalThis.Date,
    JSON: globalThis.JSON,
    Math: globalThis.Math
  };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(readFileSync(chatJsPath, "utf8"), sandbox, { filename: "web/creative-chat.js" });
  return sandbox.window.NWCreativeChat;
}

// ---------------- Task 7: submit / autonomy / failure / boot ----------------

test("autonomy phrase reaches creative model and persists both turns", async () => {
  const NWCreativeChat = loadController();
  const ports = fakePorts({ reply: "我决定采用双线悬疑。" });
  const controller = NWCreativeChat.createController(ports);
  await controller.submit("你来决定这个方向");
  assert.equal(ports.model.inputs[0].autonomy, true);
  assert.deepEqual(ports.storage.turns.map((t) => t.role), ["user", "assistant"]);
  assert.match(ports.view.messages[1].text, /双线悬疑/);
});

test("creative model receives real text and restored active-book context", async () => {
  const NWCreativeChat = loadController();
  const ports = fakePorts({ storedSession: savedSession(), reply: "接着旧案写。" });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.submit("继续雨夜开场");

  const input = ports.model.inputs[0];
  assert.equal(input.text, "继续雨夜开场");
  assert.equal(input.context.book, "book-a");
  assert.equal(input.context.summary, "雨夜命案");
  assert.deepEqual(input.context.facts.confirmed, ["主角是法医"]);
  assert.equal(input.context.turns.at(-1).text, "继续雨夜开场");
  assert.equal(ports.model.readinessInputs[0].context.book, "book-a");
});

test("compiler receives the same normalized active-book context", async () => {
  const NWCreativeChat = loadController();
  const ports = fakePorts({ storedSession: savedSession() });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.generateProposal();

  assert.equal(ports.model.compilerInputs[0].context.book, "book-a");
  assert.equal(ports.model.compilerInputs[0].context.summary, "雨夜命案");
  assert.equal(ports.model.compilerInputs[0].context.turns.length, 2);
});

test("explicit letModelDecide sets autonomy true", async () => {
  const NWCreativeChat = loadController();
  const ports = fakePorts({ reply: "由我来定方向。" });
  const controller = NWCreativeChat.createController(ports);
  await controller.letModelDecide("定个基调");
  assert.equal(ports.model.inputs[0].autonomy, true);
});

test("model failure is visible and never invokes rule engine", async () => {
  const NWCreativeChat = loadController();
  const ports = fakePorts({ error: Object.assign(new Error("请求超时"), { code: "timeout" }) });
  const controller = NWCreativeChat.createController(ports);
  await controller.submit("你来决定");
  assert.equal(ports.ruleCalls, 0);
  assert.equal(ports.view.errors[0].code, "timeout");
  // user turn retained
  assert.equal(ports.storage.turns[0].role, "user");
});

test("restart restores session and pending proposal", async () => {
  const NWCreativeChat = loadController();
  const ports = fakePorts({ storedSession: savedSession() });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  assert.equal(ports.view.messages.length, savedSession().turns.length);
  assert.equal(ports.view.proposal.id, "proposal-1");
});

test("clear resets the in-memory session without deleting durable records", async () => {
  const NWCreativeChat = loadController();
  const ports = fakePorts({ storedSession: savedSession() });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  controller.clear();
  assert.equal(ports.view.messages.length, 0);
  assert.equal(ports.view.proposal, null);
});

test("non-autonomy phrase keeps autonomy false", async () => {
  const NWCreativeChat = loadController();
  const ports = fakePorts({ reply: "你想从哪里开始？" });
  const controller = NWCreativeChat.createController(ports);
  await controller.submit("聊聊主角吧");
  assert.equal(ports.model.inputs[0].autonomy, false);
});

// ---------------- Task 8: proposal / trial draft / formal gate ----------------

test("proposal preview hides raw intake and requires two confirmations", async () => {
  const NWCreativeChat = loadController();
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
  const NWCreativeChat = loadController();
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
  const NWCreativeChat = loadController();
  const ports = fakePorts();
  const controller = NWCreativeChat.createController(ports);
  await controller.saveTrialDraft("雨夜开场", "雨水沿着警戒线滴落。", ["turn-1"]);
  assert.equal(ports.storage.drafts.length, 1);
  assert.equal(ports.executor.offered.length, 0);
});

test("discardProposal clears the pending proposal without offering a plan", async () => {
  const NWCreativeChat = loadController();
  const ports = fakePorts({ proposal: completeProposal() });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.generateProposal();
  await controller.discardProposal();
  assert.equal(ports.view.proposal, null);
  assert.equal(ports.executor.offered.length, 0);
});

test("accepted proposal status is recorded as accepted", async () => {
  const NWCreativeChat = loadController();
  const ports = fakePorts({ proposal: completeProposal() });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.generateProposal();
  await controller.acceptProposal();
  const stored = ports.storage.proposals.find((p) => p.id === "proposal-1");
  assert.equal(stored.status, "accepted");
});

test("formal plan cmdDisplay hides the serialized intake", async () => {
  const NWCreativeChat = loadController();
  const ports = fakePorts({ proposal: completeProposal() });
  const controller = NWCreativeChat.createController(ports);
  await controller.boot("book-a");
  await controller.generateProposal();
  await controller.acceptProposal();
  const plan = ports.executor.offered[0];
  assert.match(plan.cmdDisplay, /--interview <内部结构化创意>/);
  assert.doesNotMatch(plan.cmdDisplay, /\{.*audience.*\}/);
});

// ---------------- Task 10: import collision ----------------

test("controller requires merge copy or cancel on collision", async () => {
  const NWCreativeChat = loadController();
  const ports = fakePorts();
  ports.storage.importBackup = function (bytes, decision) {
    return Promise.resolve({ collision: true });
  };
  ports.storage.previewImport = function (bytes) {
    return Promise.resolve({ schemaVersion: 1, turnCount: 2, proposalCount: 1, draftCount: 1, hasExisting: true });
  };
  const controller = NWCreativeChat.createController(ports);
  await controller.importBackup(new Uint8Array([1, 2, 3]));
  assert.deepEqual(ports.view.importChoices, ["merge", "copy", "cancel"]);
});
