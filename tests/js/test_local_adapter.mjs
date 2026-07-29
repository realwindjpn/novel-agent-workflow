/* Tests for web/local.js — argv → MCP tool-call mapping and result
 * normalisation. Loads local.js by evaluating it in a Node vm context
 * with a stub window/module so the IIFE-bound adapter runs without
 * touching the network.
 *
 *   node --test tests/js/test_local_adapter.mjs
 *
 * Or via the existing python pytest suite (preferred; the python
 * harness picks up *.py tests only — these stay JS because the SUT
 * is itself a script-tag-loaded JS file, and a Node test is the
 * cheapest way to assert the pure mapping table).
 *
 * Note on deep-equal: the IIFE runs inside a vm context, so its object
 * literals have a different Object.prototype than the test file. The
 * `eqObj` helper compares via JSON so the test stays realm-agnostic.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import vm from "node:vm";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const localJsPath = resolve(__dirname, "..", "..", "web", "local.js");

function loadLocal(runtime) {
  const src = readFileSync(localJsPath, "utf8");
  const moduleObj = { exports: {} };
  const sandbox = {
    module: moduleObj,
    exports: moduleObj.exports,
    window: { NWL_RUNTIME: runtime || null },
    document: { addEventListener: () => {} },
    fetch: () => Promise.reject(new Error("fetch called in test (must stub)")),
    console: console,
  };
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox, { filename: "web/local.js" });
  return moduleObj.exports;
}

function eqObj(actual, expected, msg) {
  // Compare as JSON with sorted keys, so the assertion is robust to
  // insertion order (path is set after flag args in the loop).
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

// ---------------- argv → MCP tool-call mapping ----------------

test("argvToMcp: init with --title maps to {tool:'init', arguments:{path:'.', title:'X'}}", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp(["init", "demo", "--title", "My Book"]);
  assert.equal(r.kind, "mcp");
  assert.equal(r.tool, "init");
  eqObj(r.arguments, { path: ".", title: "My Book" });
});

test("argvToMcp: idea with --summary maps to interview default '{}'", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp(["idea", "demo", "--summary", "a one-liner"]);
  assert.equal(r.tool, "idea");
  assert.equal(r.arguments.path, ".");
  assert.equal(r.arguments.summary, "a one-liner");
  eqObj(r.arguments.interview, {});
});

test("argvToMcp: idea with --interview JSON string parses the object", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp([
    "idea", "demo",
    "--summary", "x",
    "--interview", JSON.stringify({ audience: "adult", genre: "fantasy" })
  ]);
  assert.equal(r.arguments.summary, "x");
  eqObj(r.arguments.interview, { audience: "adult", genre: "fantasy" });
});

test("argvToMcp: status drops CLI-only --human before MCP", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp(["status", "demo", "--human"]);
  assert.equal(r.tool, "status");
  assert.equal(r.arguments.human, undefined);
});

test("argvToMcp: status with --chapter int parses integer", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp(["status", "demo", "--chapter", "3", "--human"]);
  assert.equal(r.arguments.chapter, 3);
  assert.equal(r.arguments.human, undefined);
});

test("argvToMcp: review with positional [chapter, gate, verdict]", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp([
    "review", "demo", "1", "editor", "PASS",
    "--artifact", "story-bible/reviews/editor-c1.md",
    "--reviewer", "editor:mal"
  ]);
  assert.equal(r.tool, "review");
  assert.equal(r.arguments.chapter, 1);
  assert.equal(r.arguments.gate, "editor");
  assert.equal(r.arguments.verdict, "PASS");
  assert.equal(r.arguments.artifact, "story-bible/reviews/editor-c1.md");
  assert.equal(r.arguments.reviewer, "editor:mal");
});

test("argvToMcp: repair with --affected nargs '+' collects multiple values", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp([
    "repair", "demo", "2",
    "--artifact", "story-bible/reviews/editor-c2.md",
    "--affected", "pacing", "consistency", "voice"
  ]);
  assert.equal(r.tool, "repair");
  assert.equal(r.arguments.chapter, 2);
  eqObj(r.arguments.affected, ["pacing", "consistency", "voice"]);
});

test("argvToMcp: outline-review maps --review-artifact to review_artifact (snake)", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp([
    "outline-review", "demo", "master", "PASS",
    "--artifact", "outlines/master.md",
    "--reviewer", "editor:mal"
  ]);
  assert.equal(r.tool, "outline_review");
  assert.equal(r.arguments.level, "master");
  assert.equal(r.arguments.verdict, "PASS");
});

test("argvToMcp: outline-repair maps --review-artifact to review_artifact", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp([
    "outline-repair", "demo", "master",
    "--artifact", "outlines/master.md",
    "FAIL",
    "--review-artifact", "outlines/master.review.md",
    "--reviewer", "editor:mal"
  ]);
  assert.equal(r.tool, "outline_repair");
  assert.equal(r.arguments.level, "master");
  assert.equal(r.arguments.verdict, "FAIL");
  assert.equal(r.arguments.artifact, "outlines/master.md");
  assert.equal(r.arguments.review_artifact, "outlines/master.review.md");
});

test("argvToMcp: issue with positional chapter + --title + --goal", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp([
    "issue", "demo", "1", "--title", "启程", "--goal", "主角离开家乡"
  ]);
  assert.equal(r.tool, "issue");
  assert.equal(r.arguments.chapter, 1);
  assert.equal(r.arguments.title, "启程");
  assert.equal(r.arguments.goal, "主角离开家乡");
});

test("argvToMcp: draft with --author and --prewrite", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp([
    "draft", "demo", "1",
    "--artifact", "chapters/c1.md",
    "--prewrite", "story-bible/prewrite/c1.md",
    "--author", "author:mal"
  ]);
  assert.equal(r.tool, "draft");
  assert.equal(r.arguments.chapter, 1);
  assert.equal(r.arguments.author, "author:mal");
});

test("argvToMcp: release with positional chapter", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp(["release", "demo", "1"]);
  assert.equal(r.tool, "release");
  assert.equal(r.arguments.chapter, 1);
});

test("argvToMcp: outline-lock has no flags beyond path", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp(["outline-lock", "demo"]);
  assert.equal(r.tool, "outline_lock");
  eqObj(r.arguments, { path: "." });
});

test("argvToMcp: intake-check consumes CLI path but omits it for MCP", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp(["intake-check", "demo", "--interview", "{}", "--human"]);
  assert.equal(r.tool, "intake_check");
  assert.equal(r.arguments.path, undefined);
  eqObj(r.arguments.interview, {});
  assert.equal(r.arguments.human, undefined);
});

test("argvToMcp: special markers __reset__ / __ls__ / __cat__ / __tree__ return {kind}", () => {
  const NWL = loadLocal(null);
  for (const m of ["__reset__", "__ls__", "__cat__", "__tree__"]) {
    const r = NWL.argvToMcp([m]);
    assert.equal(r.kind, m, "marker: " + m);
  }
});

test("argvToMcp: unknown command returns {kind:'unknown', cmd}", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp(["nonsense", "demo"]);
  assert.equal(r.kind, "unknown");
  assert.equal(r.cmd, "nonsense");
});

test("argvToMcp: missing required --title throws", () => {
  const NWL = loadLocal(null);
  assert.throws(() => NWL.argvToMcp(["init", "demo"]), /title/);
});

test("argvToMcp: unknown --flag throws", () => {
  const NWL = loadLocal(null);
  assert.throws(() => NWL.argvToMcp(["init", "demo", "--title", "X", "--bogus", "Y"]), /bogus/);
});

test("argvToMcp: check keeps --security and drops CLI-only --human", () => {
  const NWL = loadLocal(null);
  const r = NWL.argvToMcp(["check", "demo", "--security", "--human"]);
  assert.equal(r.tool, "check");
  assert.equal(r.arguments.security, true);
  assert.equal(r.arguments.human, undefined);
});

// ---------------- RPC result normalisation ----------------

test("normaliseRpcResponse: success -> code 0, text in out", () => {
  const NWL = loadLocal(null);
  const r = NWL.normaliseRpcResponse({
    result: { content: [{ type: "text", text: "OK" }] }
  });
  assert.equal(r.code, 0);
  assert.equal(r.out, "OK");
  assert.equal(r.err, "");
});

test("normaliseRpcResponse: isError -> code 2, text in err", () => {
  const NWL = loadLocal(null);
  const r = NWL.normaliseRpcResponse({
    result: {
      content: [{ type: "text", text: "no intake complete" }],
      isError: true
    }
  });
  assert.equal(r.code, 2);
  assert.equal(r.err, "no intake complete");
  assert.equal(r.out, "");
});

test("normaliseRpcResponse: protocol error -> code 1, message in err", () => {
  const NWL = loadLocal(null);
  const r = NWL.normaliseRpcResponse({
    error: { code: -32602, message: "bad params" }
  });
  assert.equal(r.code, 1);
  assert.match(r.err, /bad params/);
  assert.match(r.err, /-32602/);
});

test("normaliseRpcResponse: structuredContent appended as JSON block", () => {
  const NWL = loadLocal(null);
  const r = NWL.normaliseRpcResponse({
    result: {
      content: [{ type: "text", text: "human prose" }],
      structuredContent: { stage: "DRAFTING" }
    }
  });
  assert.equal(r.code, 0);
  assert.match(r.out, /human prose/);
  assert.match(r.out, /"stage":\s*"DRAFTING"/);
});

test("normaliseRpcResponse: accepts direct MCP result body from local API", () => {
  const NWL = loadLocal(null);
  const r = NWL.normaliseRpcResponse({
    content: [{ type: "text", text: "direct" }],
    isError: true
  });
  assert.equal(r.code, 2);
  assert.equal(r.err, "direct");
});

// ---------------- formatCmdLine ----------------

test("formatCmdLine: argv with spaces quotes the value", () => {
  const NWL = loadLocal(null);
  const s = NWL.formatCmdLine(["init", "demo", "--title", "My Book"]);
  assert.equal(s, "novel-workflow init demo --title \"My Book\"");
});

// ---------------- active flag ----------------

test("NWL.active is false when window.NWL_RUNTIME is missing", () => {
  const NWL = loadLocal(null);
  assert.equal(NWL.active, false);
});

test("NWL.active is true when window.NWL_RUNTIME is injected", () => {
  const NWL = loadLocal({ apiBase: "/api/local", token: "abc" });
  assert.equal(NWL.active, true);
});

test("NWL.active stays false when token is missing", () => {
  const NWL = loadLocal({ apiBase: "/api/local" });
  assert.equal(NWL.active, false);
});

test("local init delegates to the registered project creator and skips MCP", async () => {
  const NWL = loadLocal({ apiBase: "/api/local", token: "abc" });
  const calls = [];
  NWL.setProjectCreator(async (title) => {
    calls.push(title);
    return { code: 0, out: "琛€杩筥20260729", err: "" };
  });

  const result = await NWL.runSmart(
    {}, ["init", "demo", "--title", "琛€杩?"], false
  );

  assert.deepEqual(calls, ["琛€杩?"]);
  assert.equal(result.code, 0);
  assert.match(result.out, /琛€杩筥20260729/);
  assert.equal(result.err, "");
});

test("local init reports a setup error when no project creator is registered", async () => {
  const NWL = loadLocal({ apiBase: "/api/local", token: "abc" });
  const result = await NWL.runSmart(
    {}, ["init", "demo", "--title", "琛€杩?"], false
  );
  assert.equal(result.code, 1);
  assert.match(result.err, /鏂颁功鍒涘缓鍣?/);
});

test("local init converts project-creator rejection to a transport result", async () => {
  const NWL = loadLocal({ apiBase: "/api/local", token: "abc" });
  NWL.setProjectCreator(async () => {
    throw new Error("create failed");
  });
  const result = await NWL.runSmart(
    {}, ["init", "demo", "--title", "琛€杩?"], false
  );
  assert.equal(result.code, 1);
  assert.match(result.err, /create failed/);
});

test("browser global is NWLocal and does not collide with llm.js NWL", () => {
  const src = readFileSync(localJsPath, "utf8");
  assert.match(src, /window\.NWLocal\s*=\s*api/);
  assert.doesNotMatch(src, /window\.NWL\s*=\s*api/);
});

test("chapter setup and artifact arguments are rewritten under artifact_dir", () => {
  const NWL = loadLocal(null);
  const prepared = NWL.rewriteChapterArtifacts(
    { "prewrite.md": "pre", "draft.md": "draft" },
    {
      kind: "mcp", tool: "draft",
      arguments: {
        path: ".", chapter: 1, prewrite: "prewrite.md",
        artifact: "draft.md", author: "author:test"
      }
    },
    "chapters/第001章_20260729"
  );
  eqObj(prepared.setup, {
    "chapters/第001章_20260729/prewrite.md": "pre",
    "chapters/第001章_20260729/draft.md": "draft"
  });
  assert.equal(prepared.plan.arguments.prewrite, "chapters/第001章_20260729/prewrite.md");
  assert.equal(prepared.plan.arguments.artifact, "chapters/第001章_20260729/draft.md");
});
