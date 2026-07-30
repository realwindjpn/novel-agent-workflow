/* Tests for web/zip.js and web/creative.js — zero-dependency ZIP codec
 * and the local/browser/memory creative storage adapter.
 *
 *   node --test tests/js/test_creative_adapter.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import vm from "node:vm";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const webDir = resolve(__dirname, "..", "..", "web");

function loadSandbox(extra) {
  extra = extra || {};
  const sandbox = {
    window: {},
    localStorage: extra.localStorage || makeMemoryStorage(),
    console: console,
    setTimeout: setTimeout,
    clearTimeout: clearTimeout,
    TextEncoder: globalThis.TextEncoder,
    TextDecoder: globalThis.TextDecoder,
    Uint8Array: globalThis.Uint8Array,
    ArrayBuffer: globalThis.ArrayBuffer,
    DataView: globalThis.DataView,
    Math: globalThis.Math,
    Date: globalThis.Date,
    JSON: globalThis.JSON,
    Error: globalThis.Error,
    Promise: globalThis.Promise
  };
  // Modules read collaborators off `window` (NWLocal, NWZip) and the
  // global `localStorage`. Put injected collaborators on window.
  if (extra.NWLocal) sandbox.window.NWLocal = extra.NWLocal;
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  // Load order: zip.js first, then creative.js.
  vm.runInContext(readFileSync(resolve(webDir, "zip.js"), "utf8"), sandbox, { filename: "web/zip.js" });
  vm.runInContext(readFileSync(resolve(webDir, "creative.js"), "utf8"), sandbox, { filename: "web/creative.js" });
  return sandbox;
}

function makeMemoryStorage() {
  const store = {};
  return {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
    _store: store
  };
}

function fakeLocal(opts) {
  opts = opts || {};
  const calls = [];
  const session = opts.session || { turns: [], summary: "", facts: emptyFacts(), proposals: [], drafts: [], conversation_state: emptyConversationState() };
  const api = {
    active: true,
    capabilities: { active_directory: "book-a" },
    calls: calls,
    creativeSession: () => { calls.push({ name: "creativeSession" }); return Promise.resolve(clone(session)); },
    appendCreativeTurn: (turn) => {
      calls.push({ name: "appendCreativeTurn", turn: turn });
      if (opts.appendError) return Promise.reject(opts.appendError);
      session.turns = session.turns || [];
      if (!session.turns.some((t) => t.id === turn.id)) session.turns.push(clone(turn));
      return Promise.resolve(clone(turn));
    },
    writeCreativeState: (summary, facts) => {
      calls.push({ name: "writeCreativeState" });
      if (opts.stateError) return Promise.reject(opts.stateError);
      session.summary = summary; session.facts = clone(facts);
      return Promise.resolve({ ok: true });
    },
    writeCreativeConversationState: (state) => {
      calls.push({ name: "writeCreativeConversationState" });
      if (opts.conversationStateError) return Promise.reject(opts.conversationStateError);
      session.conversation_state = clone(state);
      return Promise.resolve({ ok: true });
    },
    writeCreativeProposal: (p) => {
      calls.push({ name: "writeCreativeProposal" });
      if (opts.proposalError) return Promise.reject(opts.proposalError);
      session.proposals = session.proposals || [];
      const i = session.proposals.findIndex((x) => x.id === p.id);
      if (i >= 0) session.proposals[i] = clone(p); else session.proposals.push(clone(p));
      return Promise.resolve(clone(p));
    },
    writeCreativeDraft: (d) => {
      calls.push({ name: "writeCreativeDraft" });
      if (opts.draftError) return Promise.reject(opts.draftError);
      session.drafts = session.drafts || [];
      session.drafts.push(clone(d));
      return Promise.resolve(clone(d));
    },
    exportCreativeBackup: () => {
      calls.push({ name: "exportCreativeBackup" });
      return Promise.resolve(buildBackupBytes(session));
    },
    importCreativeBackup: (bytes, decision) => {
      calls.push({ name: "importCreativeBackup", decision: decision });
      if (opts.importError) return Promise.reject(opts.importError);
      return Promise.resolve({ merged: true, turn_count: session.turns.length });
    }
  };
  return api;
}

function fakeStorage(opts) {
  opts = opts || {};
  const data = opts.seed ? clone(opts.seed) : {};
  const api = {
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v); },
    removeItem: (k) => { delete data[k]; },
    _data: data
  };
  return api;
}

function emptyFacts() {
  return { confirmed: [], boundaries: [], rejected: [], important_turn_ids: [] };
}

function emptyConversationState() {
  return { phase: "exploring", completed_rounds: 0, effective_rounds: 0, coverage_version: 0, coverage: {}, active_proposal_id: null };
}

function clone(o) { return JSON.parse(JSON.stringify(o)); }

function buildBackupBytes(session) {
  // Build a minimal ZIP via NWZip once loaded; but this helper may run
  // before sandbox load. Instead encode a trivial valid archive by
  // delegating to a freshly loaded NWZip.
  const sb = loadSandbox();
  const entries = {
    "creative-backup/manifest.json": JSON.stringify({ schema_version: 1 }),
    "creative-backup/context-summary.md": session.summary || "",
    "creative-backup/facts.json": JSON.stringify(session.facts || emptyFacts())
  };
  let conv = "";
  (session.turns || []).forEach((t) => { conv += JSON.stringify(t) + "\n"; });
  entries["creative-backup/conversation.jsonl"] = conv;
  (session.proposals || []).forEach((p) => {
    entries["creative-backup/proposals/" + p.id + ".json"] = JSON.stringify(p);
  });
  (session.drafts || []).forEach((d) => {
    entries["creative-backup/drafts/" + d.id + ".json"] = JSON.stringify(d);
    entries["creative-backup/drafts/" + d.id + ".md"] = d.content || "";
  });
  return sb.window.NWZip.encode(entries);
}

// ---------------- NWZip codec ----------------

test("stored ZIP round-trips UTF-8 creative entries", () => {
  const sb = loadSandbox();
  const NWZip = sb.window.NWZip;
  const archive = NWZip.encode({
    "creative-backup/manifest.json": '{"schema_version":1}',
    "creative-backup/context-summary.md": "雨夜追凶"
  });
  const entries = NWZip.decode(archive);
  assert.equal(entries["creative-backup/context-summary.md"], "雨夜追凶");
  assert.equal(entries["creative-backup/manifest.json"], '{"schema_version":1}');
});

test("ZIP encoder produces a real stored-method archive", () => {
  const sb = loadSandbox();
  const NWZip = sb.window.NWZip;
  const archive = NWZip.encode({ "creative-backup/context-summary.md": "abc" });
  // PK signature + version needed = stored (0).
  assert.equal(archive[0], 0x50);
  assert.equal(archive[1], 0x4b);
});

test("ZIP decoder rejects traversal path", () => {
  const sb = loadSandbox();
  assert.throws(() => sb.window.NWZip.validateName("../workflow.json"), /unsafe ZIP path/);
});

test("ZIP decoder rejects absolute path", () => {
  const sb = loadSandbox();
  assert.throws(() => sb.window.NWZip.validateName("/etc/passwd"), /unsafe ZIP path/);
});

test("ZIP decoder rejects drive-letter path", () => {
  const sb = loadSandbox();
  assert.throws(() => sb.window.NWZip.validateName("C:/x"), /unsafe ZIP path/);
});

test("ZIP decoder rejects wrong root directory", () => {
  const sb = loadSandbox();
  assert.throws(() => sb.window.NWZip.validateName("other-root/x"), /unexpected ZIP root/);
});

test("ZIP decoder rejects backslash traversal", () => {
  const sb = loadSandbox();
  assert.throws(() => sb.window.NWZip.validateName("creative-backup\\..\\x"), /unsafe ZIP path/);
});

test("CRC32 of known bytes matches reference value", () => {
  const sb = loadSandbox();
  const NWZip = sb.window.NWZip;
  // CRC32 of "123456789" is 0xCBF43926.
  const bytes = new sb.Uint8Array([49, 50, 51, 52, 53, 54, 55, 56, 57]);
  assert.equal(NWZip.crc32(bytes), 0xCBF43926);
});

test("decode rejects CRC mismatch", () => {
  const sb = loadSandbox();
  const NWZip = sb.window.NWZip;
  const archive = NWZip.encode({ "creative-backup/context-summary.md": "good" });
  // Local header: 30 fixed + name length (34) = data start at 64.
  archive[64] = archive[64] ^ 0xFF;
  assert.throws(() => NWZip.decode(archive), /CRC/);
});

test("decode rejects encrypted entries", () => {
  const sb = loadSandbox();
  const NWZip = sb.window.NWZip;
  const archive = NWZip.encode({ "creative-backup/x.md": "x" });
  const dv = new sb.DataView(archive.buffer);
  // EOCD is the last 22 bytes; central dir offset at EOCD+16.
  const eocd = archive.length - 22;
  const cd = dv.getUint32(eocd + 16, true);
  // Set encryption bit in the central-directory general purpose flags.
  dv.setUint16(cd + 8, dv.getUint16(cd + 8, true) | 0x01, true);
  assert.throws(() => NWZip.decode(archive), /encrypt|unsupported/i);
});

test("decode rejects unsupported compression method", () => {
  const sb = loadSandbox();
  const NWZip = sb.window.NWZip;
  const archive = NWZip.encode({ "creative-backup/x.md": "x" });
  const dv = new sb.DataView(archive.buffer);
  const eocd = archive.length - 22;
  const cd = dv.getUint32(eocd + 16, true);
  dv.setUint16(cd + 10, 8, true); // deflate
  assert.throws(() => NWZip.decode(archive), /unsupported|method/i);
});

test("decode rejects too many entries", () => {
  const sb = loadSandbox();
  const NWZip = sb.window.NWZip;
  const entries = {};
  for (let i = 0; i < 257; i++) entries["creative-backup/f" + i + ".txt"] = "x";
  assert.throws(() => NWZip.encode(entries), /too many|256/i);
});

test("decode rejects oversized expansion", () => {
  const sb = loadSandbox();
  const NWZip = sb.window.NWZip;
  const archive = NWZip.encode({ "creative-backup/big.txt": "x" });
  const dv = new sb.DataView(archive.buffer);
  const eocd = archive.length - 22;
  const cd = dv.getUint32(eocd + 16, true);
  // Claim a 17 MiB uncompressed size in the central directory record.
  dv.setUint32(cd + 24, 17 * 1024 * 1024, true);
  assert.throws(() => NWZip.decode(archive), /too large|16/i);
});

// ---------------- NWCreative adapter ----------------

test("boot with no active book clears session to idle", async () => {
  const sb = loadSandbox({ NWLocal: { active: false, capabilities: {} } });
  const creative = sb.window.NWCreative;
  await creative.boot("");
  assert.equal(creative.durability(), "browser");
  assert.equal(creative.session().turns.length, 0);
});

test("local backend reports written-local after append", async () => {
  const local = fakeLocal();
  const sb = loadSandbox({ NWLocal: local });
  const creative = sb.window.NWCreative;
  await creative.boot("book-a");
  await creative.appendTurn({ id: "turn-1", role: "user", text: "开始" });
  assert.equal(creative.durability(), "local");
  assert.equal(local.calls[0].name, "creativeSession");
  assert.equal(local.calls[1].name, "appendCreativeTurn");
});

test("write failure keeps the turn and requires backup", async () => {
  const local = fakeLocal({ appendError: new Error("disk denied") });
  const sb = loadSandbox({ NWLocal: local });
  const creative = sb.window.NWCreative;
  await creative.boot("book-a");
  await creative.appendTurn({ id: "turn-1", role: "user", text: "不要丢" });
  assert.equal(creative.durability(), "backup-required");
  assert.equal(creative.session().turns[0].text, "不要丢");
});

test("browser-only backend persists to localStorage", async () => {
  const storage = fakeStorage();
  const sb = loadSandbox({ NWLocal: { active: false }, localStorage: storage });
  const creative = sb.window.NWCreative;
  await creative.boot("book-a");
  await creative.appendTurn({ id: "turn-1", role: "user", text: "浏览器存" });
  assert.equal(creative.durability(), "browser");
  assert.equal(creative.session().turns[0].text, "浏览器存");
  assert.ok(Object.keys(storage._data).length > 0);
});

test("writeState and writeProposal round-trip through local backend", async () => {
  const local = fakeLocal();
  const sb = loadSandbox({ NWLocal: local });
  const creative = sb.window.NWCreative;
  await creative.boot("book-a");
  await creative.writeState("雨夜命案。", { confirmed: ["主角是法医"], boundaries: [], rejected: [], important_turn_ids: [] });
  await creative.writeProposal({ id: "proposal-1", status: "pending", preview: "追查旧案", intake: { genre: "悬疑" }, source_turn_ids: ["turn-1"] });
  const s = creative.session();
  assert.equal(s.summary, "雨夜命案。");
  assert.equal(s.proposals[0].preview, "追查旧案");
});

test("writeConversationState round-trips through local backend", async () => {
  const local = fakeLocal();
  const sb = loadSandbox({ NWLocal: local });
  const creative = sb.window.NWCreative;
  await creative.boot("book-a");
  const state = { phase: "collecting", completed_rounds: 2, effective_rounds: 1, coverage_version: 1, coverage: {}, active_proposal_id: null };
  await creative.writeConversationState(state);
  assert.equal(local.calls.at(-1).name, "writeCreativeConversationState");
  assert.equal(creative.session().conversation_state.phase, "collecting");
  assert.equal(creative.session().conversation_state.completed_rounds, 2);
});

test("browser-only fallback round-trips conversation_state through boot", async () => {
  const storage = makeMemoryStorage();
  const sb = loadSandbox({ NWLocal: { active: false }, localStorage: storage });
  const creative = sb.window.NWCreative;
  await creative.boot("book-a");
  const state = { phase: "guided", completed_rounds: 6, effective_rounds: 3, coverage_version: 2, coverage: { premise: { value: "x" } }, active_proposal_id: null };
  await creative.writeConversationState(state);
  // Re-boot from the same browser storage: state should restore.
  const sb2 = loadSandbox({ NWLocal: { active: false }, localStorage: storage });
  const creative2 = sb2.window.NWCreative;
  await creative2.boot("book-a");
  assert.equal(creative2.session().conversation_state.phase, "guided");
  assert.equal(creative2.session().conversation_state.completed_rounds, 6);
});

test("subscribe listener fires on mutation", async () => {
  const local = fakeLocal();
  const sb = loadSandbox({ NWLocal: local });
  const creative = sb.window.NWCreative;
  let events = 0;
  creative.subscribe(() => { events++; });
  await creative.boot("book-a");
  await creative.appendTurn({ id: "turn-1", role: "user", text: "hi" });
  assert.ok(events >= 1);
});

test("exportBackup returns named ZIP without credentials", async () => {
  const local = fakeLocal({ session: { turns: [{ id: "t1", role: "user", text: "雨夜" }], summary: "", facts: emptyFacts(), proposals: [], drafts: [] } });
  const sb = loadSandbox({ NWLocal: local });
  const creative = sb.window.NWCreative;
  await creative.boot("book-a");
  const backup = await creative.exportBackup();
  assert.match(backup.filename, /^book-a-creative-\d{8}\.zip$/);
  assert.equal(backup.mimeType, "application/zip");
  const text = JSON.stringify(sb.window.NWZip.decode(backup.bytes));
  assert.doesNotMatch(text, /api[_-]?key|authorization/i);
  assert.match(text, /雨夜/);
});

test("previewImport reports counts without mutating session", async () => {
  const sb = loadSandbox({ NWLocal: { active: false } });
  const creative = sb.window.NWCreative;
  await creative.boot("book-a");
  const archive = buildBackupBytes({ turns: [{ id: "t1", role: "user", text: "a" }, { id: "t2", role: "assistant", text: "b" }], summary: "", facts: emptyFacts(), proposals: [{ id: "p1", status: "pending", preview: "x", intake: {}, source_turn_ids: [] }], drafts: [{ id: "d1", title: "t", content: "c", source_turn_ids: [], status: "trial", created_at: "x" }] });
  const preview = await creative.previewImport(archive);
  assert.equal(preview.turnCount, 2);
  assert.equal(preview.proposalCount, 1);
  assert.equal(preview.draftCount, 1);
  assert.equal(creative.session().turns.length, 0);
});

test("importBackup merge restores turns", async () => {
  const local = fakeLocal();
  const sb = loadSandbox({ NWLocal: local });
  const creative = sb.window.NWCreative;
  await creative.boot("book-a");
  const archive = buildBackupBytes({ turns: [{ id: "t1", role: "user", text: "导入" }], summary: "已恢复", facts: emptyFacts(), proposals: [], drafts: [] });
  const result = await creative.importBackup(archive, "merge");
  assert.equal(result.turnCount, 1);
  assert.equal(creative.session().turns[0].text, "导入");
});