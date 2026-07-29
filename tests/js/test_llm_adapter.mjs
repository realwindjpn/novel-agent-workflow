/* Tests for web/llm.js — separated freeform creative, readiness, and
 * compiler model calls with typed ModelError failures.
 *
 *   node --test tests/js/test_llm_adapter.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import vm from "node:vm";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const llmJsPath = resolve(__dirname, "..", "..", "web", "llm.js");

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

function completeCompilerJson() {
  return JSON.stringify({
    preview: "完整方案",
    summary: "一句话方案",
    intake: completeIntake(),
    assumptions: ["假设一"],
    uncertainties: ["不确定一"],
    draft_refs: [],
    source_turn_ids: ["turn-1"]
  });
}

function makeSettings(enabled, key) {
  return {
    "nwa.llm.enabled": enabled ? "1" : "0",
    "nwa.llm.apiKey": key || "sk-test",
    "nwa.llm.baseUrl": "https://provider.test/v1",
    "nwa.llm.model": "test-model",
    "nwa.llm.creativeTemp": "0.85"
  };
}

function storageFrom(seed) {
  const data = Object.assign({}, seed);
  return {
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v); },
    removeItem: (k) => { delete data[k]; }
  };
}

function completion(content) {
  return {
    choices: [{ message: { content: content, role: "assistant" } }]
  };
}

function loadLLM(stub) {
  // stub: { content } | { status, body } | a fetch impl
  const calls = [];
  let seq = stub && Array.isArray(stub) ? stub.slice() : null;
  let single = stub && stub.content !== undefined ? stub : null;
  let httpFail = stub && stub.status !== undefined ? stub : null;
  const fetchImpl = stub && typeof stub === "function" ? stub : function (url, opts) {
    calls.push({ url: url, opts: opts });
    if (httpFail) {
      return Promise.resolve({
        ok: false,
        status: httpFail.status,
        statusText: "rate limited",
        text: () => Promise.resolve(httpFail.body || "")
      });
    }
    const payload = seq ? seq.shift() : single;
    const body = completion(payload.content);
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(body)
    });
  };
  const sandbox = {
    window: {
      NWB: { readState: () => null, getMode: () => "live" },
      AbortController: globalThis.AbortController,
      dispatchEvent: () => {},
      CustomEvent: function () {}
    },
    AbortController: globalThis.AbortController,
    localStorage: storageFrom(makeSettings(true)),
    document: {
      getElementById: () => null,
      addEventListener: () => {},
      body: { appendChild: () => {} }
    },
    fetch: fetchImpl,
    console: console,
    setTimeout: setTimeout,
    clearTimeout: clearTimeout
  };
  sandbox.window.NWL_settings_for_test = makeSettings(true);
  vm.createContext(sandbox);
  vm.runInContext(readFileSync(llmJsPath, "utf8"), sandbox, { filename: "web/llm.js" });
  const NWL = sandbox.window.NWL;
  NWL.__calls = calls;
  return NWL;
}

function loadLLMSequence(responses) {
  return loadLLM(responses);
}

// ---------------- creativeReply ----------------

test("creativeReply returns plain prose without JSON parsing", async () => {
  const NWL = loadLLM({ content: "我会把方向定为现实主义悬疑，从雨夜旧案切入。" });
  const result = await NWL.creativeReply({ text: "你来决定", autonomy: true, context: {} });
  assert.equal(result.reply, "我会把方向定为现实主义悬疑，从雨夜旧案切入。");
});

test("creativeReply rejects with not_configured when disabled", async () => {
  const NWL = loadLLM({ content: "x" });
  NWL.setEnabledForTest(false);
  await assert.rejects(
    NWL.creativeReply({ text: "hi", autonomy: false, context: {} }),
    (e) => e.code === "not_configured"
  );
});

test("creativeReply exposes typed provider failure", async () => {
  const NWL = loadLLM({ status: 429, body: "busy" });
  await assert.rejects(
    NWL.creativeReply({ text: "继续", autonomy: false, context: {} }),
    (error) => error.code === "provider_http" && error.status === 429
  );
});

test("creativeReply exposes network failure as cors/network", async () => {
  const NWL = loadLLM(function () { return Promise.reject(new TypeError("Failed to fetch")); });
  await assert.rejects(
    NWL.creativeReply({ text: "继续", autonomy: false, context: {} }),
    (error) => error.code === "cors" || error.code === "network"
  );
});

test("creativeReply rejects on empty response", async () => {
  const NWL = loadLLM({ content: "   " });
  await assert.rejects(
    NWL.creativeReply({ text: "继续", autonomy: false, context: {} }),
    (e) => e.code === "empty_response"
  );
});

test("creativeReply sends autonomy flag in prompt context", async () => {
  const NWL = loadLLM({ content: "好的。" });
  await NWL.creativeReply({ text: "你来决定", autonomy: true, context: {} });
  const sys = NWL.__calls[0].opts.body;
  const parsed = typeof sys === "string" ? JSON.parse(sys) : sys;
  const sysText = parsed.messages[0].content;
  assert.match(sysText, /autonomy|自主|你来决定/i);
});

// ---------------- assessReadiness ----------------

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

test("assessReadiness returns ready true with reason", async () => {
  const NWL = loadLLM({ content: JSON.stringify({ ready: true, reason: "创意已收敛" }) });
  const ready = await NWL.assessReadiness({ context: {} });
  assert.equal(ready.ready, true);
  assert.match(ready.reason, /收敛/);
});

// ---------------- compileProposal ----------------

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

test("compileProposal throws schema_error after repair still fails", async () => {
  const NWL = loadLLMSequence([
    { content: '{"preview":"x","intake":{"genre":"x"}}' },
    { content: '{"preview":"y","intake":{"genre":"y"}}' }
  ]);
  await assert.rejects(
    NWL.compileProposal({ context: {}, autonomy: true }),
    (e) => e.code === "schema_error"
  );
  assert.equal(NWL.__calls.length, 2);
});

test("compileProposal rejects parse error when not JSON", async () => {
  const NWL = loadLLMSequence([
    { content: "totally not json" },
    { content: "still not json" }
  ]);
  await assert.rejects(
    NWL.compileProposal({ context: {}, autonomy: true }),
    (e) => e.code === "parse_error" || e.code === "schema_error"
  );
});

test("INTAKE_KEYS matches the 15 core intake fields", () => {
  const NWL = loadLLM({ content: "x" });
  assert.equal(NWL.INTAKE_KEYS.length, 15);
  INTAKE_KEYS.forEach(function (k) { assert.ok(NWL.INTAKE_KEYS.indexOf(k) >= 0, k); });
});

test("legacy tryLLM still returns fallback for command mode", async () => {
  const NWL = loadLLM({ content: JSON.stringify({ kind: "answer", reply: "ok" }) });
  const r = await NWL.tryLLM("现在到哪了", []);
  assert.equal(r.kind, "answer");
  assert.equal(r.reply, "ok");
});

test("ModelError carries code and detail", () => {
  const NWL = loadLLM({ content: "x" });
  const e = new NWL.ModelError("timeout", "超时", "30s");
  assert.equal(e.code, "timeout");
  assert.equal(e.name, "ModelError");
  assert.match(e.detail, /30s/);
  assert.equal(typeof e.message, "string");
});
