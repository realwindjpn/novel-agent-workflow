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
const llmSource = readFileSync(llmJsPath, "utf8");

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

[
  ["reasoning content", { choices: [{ message: { content: null, reasoning_content: "推理模型回复" } }] }, "推理模型回复"],
  ["array content", { choices: [{ message: { content: [{ type: "text", text: "分段回复" }] } }] }, "分段回复"],
  ["choice text", { choices: [{ text: "choice 回复" }] }, "choice 回复"],
  ["top-level output text", { output_text: "顶层回复" }, "顶层回复"]
].forEach(function ([label, payload, expected]) {
  test("creativeReply accepts " + label, async () => {
    const NWL = loadLLM(function () {
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload) });
    });
    const result = await NWL.creativeReply({ text: "继续", autonomy: false, context: {} });
    assert.equal(result.reply, expected);
  });
});

test("testConnection verifies a real chat completion", async () => {
  const calls = [];
  const NWL = loadLLM(function (url, opts) {
    calls.push({ url: url, opts: opts });
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(completion("ok"))
    });
  });

  const result = await NWL.testConnection();
  assert.equal(result.ok, true);
  assert.match(result.msg, /真实生成成功/);
  assert.match(calls[0].url, /\/chat\/completions$/);
  assert.equal(calls[0].opts.method, "POST");
  const body = JSON.parse(calls[0].opts.body);
  assert.equal(body.stream, false);
  assert.ok(body.messages.some((m) => m.role === "user"));
});

test("connection test keeps the popover visible long enough to show its result", () => {
  assert.match(llmSource, /saveForm\(\{ hide: false \}\)/);
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

// ---------------- extractCoverage ----------------

const COVERAGE_FIELDS = ["premise", "protagonist", "central_conflict", "stakes", "world", "style_audience", "ending_direction"];

test("extractCoverage sends only bounded turns and the seven allowed field names", async () => {
  const NWL = loadLLM({ content: JSON.stringify({ items: [] }) });
  const turns = [];
  for (let i = 0; i < 20; i++) turns.push({ id: "t" + i, role: i % 2 === 0 ? "user" : "assistant", text: "msg " + i });
  await NWL.extractCoverage({ context: { turns }, autonomy: false });
  const body = JSON.parse(NWL.__calls[0].opts.body);
  const sysText = body.messages[0].content;
  COVERAGE_FIELDS.forEach(function (f) { assert.ok(sysText.indexOf(f) >= 0, "field " + f + " should be in prompt"); });
  // only last 10 turns sent
  const turnsJson = sysText.split("\n").filter(function (l) { return l.indexOf("[") === 0; });
  assert.ok(turnsJson.length <= 10, "should bound turns to last 10, got " + turnsJson.length);
  assert.equal(body.temperature, 0.1);
});

test("extractCoverage returns empty items for valid empty extraction", async () => {
  const NWL = loadLLM({ content: JSON.stringify({ items: [] }) });
  const result = await NWL.extractCoverage({ context: { turns: [{ id: "u1", role: "user", text: "hi" }] }, autonomy: false });
  assert.equal(result.items.length, 0);
});

test("extractCoverage accepts exact evidence records", async () => {
  const extractionJson = JSON.stringify({
    items: [{
      field: "premise",
      value: "未清理的犯罪现场成为家族秘密的钥匙",
      status: "candidate",
      evidence: [{ turn_id: "u1", quote: "犯罪现场成为家族秘密的钥匙" }]
    }]
  });
  const NWL = loadLLM({ content: extractionJson });
  const result = await NWL.extractCoverage({ context: { turns: [{ id: "u1", role: "user", text: "犯罪现场成为家族秘密的钥匙" }] }, autonomy: false });
  assert.equal(result.items.length, 1);
  assert.equal(result.items[0].field, "premise");
  assert.equal(result.items[0].evidence[0].turn_id, "u1");
});

test("extractCoverage rejects unknown field with schema_error", async () => {
  const NWL = loadLLM({ content: JSON.stringify({ items: [{ field: "mood", value: "v", status: "candidate", evidence: [{ turn_id: "u1", quote: "v" }] }] }) });
  await assert.rejects(
    NWL.extractCoverage({ context: { turns: [{ id: "u1", role: "user", text: "v" }] }, autonomy: false }),
    (e) => e.code === "schema_error" && /field/i.test(e.message)
  );
});

test("extractCoverage rejects unknown status with schema_error", async () => {
  const NWL = loadLLM({ content: JSON.stringify({ items: [{ field: "premise", value: "v", status: "magic", evidence: [{ turn_id: "u1", quote: "v" }] }] }) });
  await assert.rejects(
    NWL.extractCoverage({ context: { turns: [{ id: "u1", role: "user", text: "v" }] }, autonomy: false }),
    (e) => e.code === "schema_error" && /status/i.test(e.message)
  );
});

test("extractCoverage rejects missing evidence with schema_error", async () => {
  const NWL = loadLLM({ content: JSON.stringify({ items: [{ field: "premise", value: "v", status: "candidate" }] }) });
  await assert.rejects(
    NWL.extractCoverage({ context: { turns: [{ id: "u1", role: "user", text: "v" }] }, autonomy: false }),
    (e) => e.code === "schema_error" && /evidence/i.test(e.message)
  );
});

test("extractCoverage reports provider error as typed ModelError", async () => {
  const NWL = loadLLM({ status: 500, body: "err" });
  await assert.rejects(
    NWL.extractCoverage({ context: { turns: [] }, autonomy: false }),
    (e) => e.code === "provider_http" && e instanceof NWL.ModelError
  );
});

test("extractCoverage reports parse error as typed ModelError", async () => {
  const NWL = loadLLM({ content: "not json at all" });
  await assert.rejects(
    NWL.extractCoverage({ context: { turns: [] }, autonomy: false }),
    (e) => e.code === "parse_error" || e.code === "schema_error"
  );
});

test("extractCoverage reports schema_error when items missing", async () => {
  const NWL = loadLLM({ content: JSON.stringify({ something: "else" }) });
  await assert.rejects(
    NWL.extractCoverage({ context: { turns: [] }, autonomy: false }),
    (e) => e.code === "schema_error" && /items/i.test(e.message)
  );
});

test("extractCoverage failure never changes a successful natural reply", async () => {
  const NWL = loadLLMSequence([
    { content: "先从旧案切入。" },
    { content: "broken json" }
  ]);
  const reply = await NWL.creativeReply({ text: "继续", autonomy: false, context: {} });
  assert.equal(reply.reply, "先从旧案切入。");
  await assert.rejects(
    NWL.extractCoverage({ context: { turns: [] }, autonomy: false }),
    (e) => e instanceof NWL.ModelError
  );
  // reply unchanged
  assert.equal(reply.reply, "先从旧案切入。");
});

test("extractCoverage sends autonomy flag in prompt", async () => {
  const NWL = loadLLM({ content: JSON.stringify({ items: [] }) });
  await NWL.extractCoverage({ context: { turns: [] }, autonomy: true });
  const sysText = JSON.parse(NWL.__calls[0].opts.body).messages[0].content;
  assert.match(sysText, /autonomy=true/);
});
