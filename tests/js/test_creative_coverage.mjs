/* Tests for web/creative-coverage.js — pure evidence validation, coverage
 * merge, effective/completed round counters, 3/6/10 thresholds, critical-field
 * versioning, and stale checks.
 *
 *   node --test tests/js/test_creative_coverage.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import vm from "node:vm";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const covJsPath = resolve(__dirname, "..", "..", "web", "creative-coverage.js");

function loadCoverage() {
  const src = readFileSync(covJsPath, "utf8");
  const moduleObj = { exports: {} };
  const sandbox = {
    module: moduleObj,
    exports: moduleObj.exports,
    window: {},
    console: console,
  };
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox, { filename: "web/creative-coverage.js" });
  return moduleObj.exports;
}

const coverage = loadCoverage();

// ---------- helpers ----------

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

function seeded(field, value, status, version) {
  const state = coverage.emptyConversationState();
  state.coverage_version = version;
  state.coverage[field] = {
    value: value,
    source_turn_ids: ["u1"],
    evidence: [{ turn_id: "u1", quote: value }],
    status: status,
    updated_at: "2026-07-30T00:00:00Z",
  };
  return state;
}

function extraction(field, value, turnId, quote) {
  return {
    items: [{
      field: field,
      value: value,
      status: "candidate",
      evidence: [{ turn_id: turnId, quote: quote }],
    }],
  };
}

function item(field, value, turnId, quote, status) {
  return {
    field: field,
    value: value,
    status: status || "candidate",
    evidence: [{ turn_id: turnId, quote: quote }],
  };
}

function emptyAt(overrides) {
  const s = coverage.emptyConversationState();
  Object.assign(s, overrides || {});
  return s;
}

function stateWithRequiredFive(overrides) {
  const s = coverage.emptyConversationState();
  const required = ["premise", "protagonist", "central_conflict", "stakes", "style_audience"];
  required.forEach(function (f, i) {
    s.coverage[f] = {
      value: "val-" + f,
      source_turn_ids: ["u" + (i + 1)],
      evidence: [{ turn_id: "u" + (i + 1), quote: "val-" + f }],
      status: "confirmed",
      updated_at: "2026-07-30T00:00:00Z",
    };
  });
  Object.assign(s, overrides || {});
  return s;
}

function completeIntake() {
  return {
    premise: "p",
    protagonist: "pr",
    central_conflict: "c",
    stakes: "s",
    style_audience: "sa",
  };
}

// ---------- empty state ----------

test("emptyConversationState has exploring phase and zero counters", () => {
  const s = coverage.emptyConversationState();
  assert.equal(s.phase, "exploring");
  assert.equal(s.completed_rounds, 0);
  assert.equal(s.effective_rounds, 0);
  assert.equal(s.coverage_version, 0);
  assert.equal(s.active_proposal_id, null);
  deepEq(s.coverage, {});
});

// ---------- evidence quote verification ----------

test("evidence quote must exist verbatim in the referenced turn", () => {
  const turns = [{ id: "u1", role: "user", text: "主角是一个害怕真相的法医" }];
  const ok = coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{
      field: "protagonist", value: "害怕真相的法医", status: "candidate",
      evidence: [{ turn_id: "u1", quote: "害怕真相的法医" }],
    }],
  }, turns, { autonomy: false });
  assert.equal(ok.coverage.protagonist.value, "害怕真相的法医");
  assert.throws(() => coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{
      field: "protagonist", value: "记者", status: "candidate",
      evidence: [{ turn_id: "u1", quote: "他是一名记者" }],
    }],
  }, turns, { autonomy: false }), /quote/);
});

test("evidence referencing unknown turn id is rejected", () => {
  const turns = [{ id: "u1", role: "user", text: "一段文本" }];
  assert.throws(() => coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{
      field: "premise", value: "val", status: "candidate",
      evidence: [{ turn_id: "uX", quote: "一段文本" }],
    }],
  }, turns, { autonomy: false }), /turn|quote|evidence/i);
});

test("empty extraction is accepted and increments completed round", () => {
  const turns = [{ id: "u1", role: "user", text: "随便聊聊" }];
  const next = coverage.applyExtraction(coverage.emptyConversationState(), { items: [] }, turns, { autonomy: false });
  assert.equal(next.completed_rounds, 1);
  assert.equal(next.effective_rounds, 0);
});

// ---------- conflict preservation ----------

test("confirmed evidence cannot be silently overwritten", () => {
  const state = seeded("protagonist", "法医", "confirmed", 1);
  const next = coverage.applyExtraction(state, extraction("protagonist", "记者", "u2", "记者"),
    [{ id: "u2", role: "user", text: "也许换成记者" }], { autonomy: false });
  assert.equal(next.coverage.protagonist.value, "法医");
  assert.equal(next.coverage.protagonist.status, "conflicted");
});

test("candidate can be upgraded to confirmed with new evidence", () => {
  const state = seeded("protagonist", "法医", "candidate", 1);
  const next = coverage.applyExtraction(state, {
    items: [{
      field: "protagonist", value: "法医", status: "confirmed",
      evidence: [{ turn_id: "u2", quote: "法医" }],
    }],
  }, [{ id: "u2", role: "user", text: "就用法医" }], { autonomy: false });
  assert.equal(next.coverage.protagonist.value, "法医");
  assert.equal(next.coverage.protagonist.status, "confirmed");
});

// ---------- field/status validation ----------

test("unknown field is rejected", () => {
  const turns = [{ id: "u1", role: "user", text: "x" }];
  assert.throws(() => coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{ field: "mood", value: "v", status: "candidate", evidence: [{ turn_id: "u1", quote: "x" }] }],
  }, turns, { autonomy: false }), /field/i);
});

test("unknown status is rejected", () => {
  const turns = [{ id: "u1", role: "user", text: "x" }];
  assert.throws(() => coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{ field: "premise", value: "v", status: "magic", evidence: [{ turn_id: "u1", quote: "x" }] }],
  }, turns, { autonomy: false }), /status/i);
});

test("empty value is rejected", () => {
  const turns = [{ id: "u1", role: "user", text: "x" }];
  assert.throws(() => coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{ field: "premise", value: "  ", status: "candidate", evidence: [{ turn_id: "u1", quote: "x" }] }],
  }, turns, { autonomy: false }), /value|empty/i);
});

test("assumed status requires autonomy option", () => {
  const turns = [{ id: "u1", role: "user", text: "假定的世界" }];
  assert.throws(() => coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{ field: "world", value: "假定的世界", status: "assumed", evidence: [{ turn_id: "u1", quote: "假定的世界" }] }],
  }, turns, { autonomy: false }), /assumed|autonomy/i);

  const ok = coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{ field: "world", value: "假定的世界", status: "assumed", evidence: [{ turn_id: "u1", quote: "假定的世界" }] }],
  }, turns, { autonomy: true });
  assert.equal(ok.coverage.world.status, "assumed");
});

// ---------- counters ----------

test("completed_rounds increments once per successful extraction", () => {
  const turns = [{ id: "u1", role: "user", text: "聊" }];
  const s1 = coverage.applyExtraction(coverage.emptyConversationState(), { items: [] }, turns, { autonomy: false });
  assert.equal(s1.completed_rounds, 1);
  const s2 = coverage.applyExtraction(s1, { items: [] }, turns, { autonomy: false });
  assert.equal(s2.completed_rounds, 2);
});

test("effective_rounds increments when evidence changes", () => {
  const turns = [{ id: "u1", role: "user", text: "主角是侦探" }];
  const s1 = coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{ field: "protagonist", value: "侦探", status: "candidate", evidence: [{ turn_id: "u1", quote: "侦探" }] }],
  }, turns, { autonomy: false });
  assert.equal(s1.effective_rounds, 1);
  // same evidence again -> no effective increment
  const s2 = coverage.applyExtraction(s1, {
    items: [{ field: "protagonist", value: "侦探", status: "candidate", evidence: [{ turn_id: "u1", quote: "侦探" }] }],
  }, turns, { autonomy: false });
  assert.equal(s2.effective_rounds, 1);
});

test("effective_rounds increments on explicitDecision", () => {
  const turns = [{ id: "u1", role: "user", text: "确认" }];
  const s1 = coverage.applyExtraction(coverage.emptyConversationState(), { items: [] }, turns, { explicitDecision: true });
  assert.equal(s1.effective_rounds, 1);
});

// ---------- coverage version ----------

test("critical field change increments coverage_version", () => {
  const turns = [{ id: "u1", role: "user", text: "新创意" }];
  const s1 = coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{ field: "premise", value: "新创意", status: "candidate", evidence: [{ turn_id: "u1", quote: "新创意" }] }],
  }, turns, { autonomy: false });
  assert.ok(s1.coverage_version >= 1);
  const turns2 = [{ id: "u2", role: "user", text: "另一个核心" }];
  const s2 = coverage.applyExtraction(s1, {
    items: [{ field: "central_conflict", value: "另一个核心", status: "candidate", evidence: [{ turn_id: "u2", quote: "另一个核心" }] }],
  }, turns2, { autonomy: false });
  assert.ok(s2.coverage_version > s1.coverage_version);
});

test("non-critical field change does not increment coverage_version", () => {
  const turns = [{ id: "u1", role: "user", text: "风格" }];
  const s1 = coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{ field: "world", value: "风格", status: "candidate", evidence: [{ turn_id: "u1", quote: "风格" }] }],
  }, turns, { autonomy: false });
  const v1 = s1.coverage_version;
  const turns2 = [{ id: "u2", role: "user", text: "结局倾向描述" }];
  const s2 = coverage.applyExtraction(s1, {
    items: [{ field: "ending_direction", value: "结局倾向描述", status: "candidate", evidence: [{ turn_id: "u2", quote: "结局倾向描述" }] }],
  }, turns2, { autonomy: false });
  assert.equal(s2.coverage_version, v1);
});

// ---------- deriveTransition ----------

test("program derives proposal guided and forced-draft transitions", () => {
  assert.equal(coverage.deriveTransition(stateWithRequiredFive({ effective_rounds: 3 })).phase, "proposal-ready");
  assert.equal(coverage.deriveTransition(emptyAt({ completed_rounds: 6, effective_rounds: 1 })).phase, "guided");
  assert.equal(coverage.deriveTransition(emptyAt({ completed_rounds: 2, effective_rounds: 4 })).phase, "guided");
  assert.equal(coverage.deriveTransition(emptyAt({ completed_rounds: 10, effective_rounds: 0 })).action, "force-draft");
});

test("exploring stays exploring with no coverage", () => {
  assert.equal(coverage.deriveTransition(coverage.emptyConversationState()).phase, "exploring");
});

test("collecting when coverage exists but thresholds not met", () => {
  const s = emptyAt({});
  s.coverage = { world: { value: "v", status: "candidate" } };
  assert.equal(coverage.deriveTransition(s).phase, "collecting");
});

test("conflicted required field blocks proposal-ready", () => {
  const s = stateWithRequiredFive({ effective_rounds: 3 });
  s.coverage.premise.status = "conflicted";
  assert.notEqual(coverage.deriveTransition(s).phase, "proposal-ready");
});

// ---------- stale / handoff ----------

test("critical coverage version makes an old proposal stale", () => {
  const state = stateWithRequiredFive({ effective_rounds: 3, coverage_version: 7 });
  assert.equal(coverage.isProposalStale({ coverage_version: 6, status: "pending" }, state), true);
  assert.equal(coverage.isProposalStale({ coverage_version: 7, status: "pending" }, state), false);
});

test("canHandoff requires matching version, pending status, and complete intake", () => {
  const state = stateWithRequiredFive({ effective_rounds: 3, coverage_version: 7 });
  assert.equal(coverage.canHandoff({ coverage_version: 7, status: "pending", intake: completeIntake() }, state), true);
  assert.equal(coverage.canHandoff({ coverage_version: 6, status: "pending", intake: completeIntake() }, state), false);
  assert.equal(coverage.canHandoff({ coverage_version: 7, status: "accepted", intake: completeIntake() }, state), false);
  assert.equal(coverage.canHandoff({ coverage_version: 7, status: "pending", intake: { premise: "p" } }, state), false);
});

// ---------- immutability ----------

test("applyExtraction does not mutate the input state", () => {
  const original = coverage.emptyConversationState();
  const turns = [{ id: "u1", role: "user", text: "主角是侦探" }];
  coverage.applyExtraction(original, {
    items: [{ field: "protagonist", value: "侦探", status: "candidate", evidence: [{ turn_id: "u1", quote: "侦探" }] }],
  }, turns, { autonomy: false });
  assert.equal(original.completed_rounds, 0);
  assert.equal(Object.keys(original.coverage).length, 0);
});

test("source_turn_ids derived from evidence not trusted", () => {
  const turns = [{ id: "u1", role: "user", text: "主角是侦探" }];
  const next = coverage.applyExtraction(coverage.emptyConversationState(), {
    items: [{
      field: "protagonist", value: "侦探", status: "candidate",
      evidence: [{ turn_id: "u1", quote: "侦探" }],
      source_turn_ids: ["fabricated-id"],
    }],
  }, turns, { autonomy: false });
  deepEq(next.coverage.protagonist.source_turn_ids, ["u1"]);
});
