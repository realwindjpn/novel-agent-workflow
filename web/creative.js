/* web/creative.js — creative workspace storage adapter.
 *
 * Presents one interface over three backends, in priority order:
 *   1. local bridge (window.NWLocal) when active and a book is open;
 *   2. browser localStorage (key nwa.creative.<book-directory>);
 *   3. in-memory session (always exportable as a ZIP).
 *
 * Every mutation updates memory first, then attempts durable storage.
 * A failed durable write never rolls memory back. The durability state
 * is reported to the UI as one of: "local", "browser", "backup-required".
 *
 * Exposes window.NWCreative = { boot, session, durability, appendTurn,
 * writeState, writeProposal, writeDraft, exportBackup, previewImport,
 * importBackup, subscribe }. Also module.exports for Node tests.
 */
(function () {
  "use strict";

  var SCHEMA_VERSION = 1;
  var STORAGE_PREFIX = "nwa.creative.";
  var MAX_RECENT_TURNS = 200;

  var currentBook = "";
  var session = emptySession();
  var durabilityState = "browser";
  var listeners = [];
  var primaryBackend = "browser"; // "local" | "browser"
  var storageAvailable = detectStorage();

  function emptySession() {
    return {
      schema_version: SCHEMA_VERSION,
      turns: [],
      summary: "",
      facts: { confirmed: [], boundaries: [], rejected: [], important_turn_ids: [] },
      proposals: [],
      drafts: []
    };
  }

  function clone(o) { return JSON.parse(JSON.stringify(o)); }

  function detectStorage() {
    try {
      if (typeof localStorage === "undefined" || !localStorage) return false;
      var k = "__nwc_probe__";
      localStorage.setItem(k, "1");
      localStorage.removeItem(k);
      return true;
    } catch (e) { return false; }
  }

  function localBridge() {
    return (typeof window !== "undefined" && window.NWLocal && window.NWLocal.active) ? window.NWLocal : null;
  }

  function hasActiveBook() {
    var lb = localBridge();
    return !!(lb && lb.capabilities && lb.capabilities.active_directory);
  }

  function notify() {
    for (var i = 0; i < listeners.length; i++) {
      try { listeners[i]({ durability: durabilityState, book: currentBook }); } catch (e) {}
    }
  }

  function subscribe(fn) {
    if (typeof fn === "function") listeners.push(fn);
    return function () {
      var i = listeners.indexOf(fn);
      if (i >= 0) listeners.splice(i, 1);
    };
  }

  function boot(bookId) {
    currentBook = bookId || "";
    session = emptySession();
    listeners = listeners.slice();
    var lb = localBridge();
    if (lb && currentBook) {
      primaryBackend = "local";
      return lb.creativeSession().then(function (loaded) {
        session = loaded ? mergeSession(emptySession(), loaded) : emptySession();
        durabilityState = "local";
        notify();
      }).catch(function () {
        primaryBackend = storageAvailable ? "browser" : "browser";
        durabilityState = storageAvailable ? "browser" : "backup-required";
        loadFromBrowser();
        notify();
      });
    }
    primaryBackend = storageAvailable ? "browser" : "browser";
    durabilityState = storageAvailable ? "browser" : "backup-required";
    loadFromBrowser();
    notify();
    return Promise.resolve();
  }

  function clear() {
    currentBook = "";
    session = emptySession();
    durabilityState = storageAvailable ? "browser" : "backup-required";
    notify();
    return Promise.resolve();
  }

  function sessionSnapshot() { return clone(session); }
  function durability() { return durabilityState; }

  function loadFromBrowser() {
    if (!storageAvailable || !currentBook) return;
    try {
      var raw = localStorage.getItem(STORAGE_PREFIX + currentBook);
      if (raw) {
        var parsed = JSON.parse(raw);
        session = mergeSession(emptySession(), parsed);
      }
    } catch (e) { /* corrupt cache — keep memory */ }
  }

  function saveToBrowser() {
    if (!storageAvailable || !currentBook) return false;
    try {
      localStorage.setItem(STORAGE_PREFIX + currentBook, JSON.stringify(session));
      return true;
    } catch (e) { return false; }
  }

  function mergeSession(base, incoming) {
    var merged = base;
    if (incoming) {
      if (Array.isArray(incoming.turns)) {
        incoming.turns.forEach(function (t) {
          if (t && t.id && !merged.turns.some(function (x) { return x.id === t.id; })) merged.turns.push(t);
        });
      }
      if (typeof incoming.summary === "string" && incoming.summary) merged.summary = incoming.summary;
      if (incoming.facts) merged.facts = incoming.facts;
      if (Array.isArray(incoming.proposals)) {
        incoming.proposals.forEach(function (p) {
          if (p && p.id) {
            var i = merged.proposals.findIndex(function (x) { return x.id === p.id; });
            if (i >= 0) merged.proposals[i] = p; else merged.proposals.push(p);
          }
        });
      }
      if (Array.isArray(incoming.drafts)) {
        incoming.drafts.forEach(function (d) {
          if (d && d.id && !merged.drafts.some(function (x) { return x.id === d.id; })) merged.drafts.push(d);
        });
      }
    }
    return merged;
  }

  function appendTurn(turn) {
    if (!turn || !turn.id) return Promise.resolve();
    if (!session.turns.some(function (t) { return t.id === turn.id; })) {
      session.turns.push(clone(turn));
      while (session.turns.length > MAX_RECENT_TURNS) session.turns.shift();
    }
    return persist("turn", turn).then(function () { notify(); });
  }

  function writeState(summary, facts) {
    session.summary = summary || "";
    session.facts = facts || session.facts;
    return persist("state", { summary: summary, facts: facts }).then(function () { notify(); });
  }

  function writeProposal(proposal) {
    if (!proposal || !proposal.id) return Promise.resolve();
    var i = session.proposals.findIndex(function (x) { return x.id === proposal.id; });
    if (i >= 0) session.proposals[i] = clone(proposal);
    else session.proposals.push(clone(proposal));
    return persist("proposal", proposal).then(function () { notify(); });
  }

  function writeDraft(draft) {
    if (!draft || !draft.id) return Promise.resolve();
    if (!session.drafts.some(function (d) { return d.id === draft.id; })) session.drafts.push(clone(draft));
    return persist("draft", draft).then(function () { notify(); });
  }

  function persist(kind, payload) {
    if (primaryBackend === "local") {
      var lb = localBridge();
      if (!lb) { fallbackBrowser(); return Promise.resolve(); }
      var p;
      if (kind === "turn") p = lb.appendCreativeTurn(payload);
      else if (kind === "state") p = lb.writeCreativeState(payload.summary, payload.facts);
      else if (kind === "proposal") p = lb.writeCreativeProposal(payload);
      else if (kind === "draft") p = lb.writeCreativeDraft(payload);
      else p = Promise.resolve();
      return p.then(function () {
        durabilityState = "local";
      }).catch(function () {
        // Local write failed — keep memory, signal backup required.
        saveToBrowser();
        durabilityState = "backup-required";
      });
    }
    // browser / memory backend
    if (saveToBrowser()) {
      if (durabilityState === "backup-required") durabilityState = "backup-required";
      else durabilityState = "browser";
    } else {
      durabilityState = "backup-required";
    }
    return Promise.resolve();
  }

  function fallbackBrowser() {
    if (saveToBrowser()) durabilityState = "browser";
    else durabilityState = "backup-required";
  }

  // ---- ZIP export / import ----

  function sessionToEntries() {
    var entries = {
      "creative-backup/manifest.json": JSON.stringify({
        schema_version: SCHEMA_VERSION,
        book: currentBook,
        turn_count: session.turns.length,
        proposal_count: session.proposals.length,
        draft_count: session.drafts.length
      }),
      "creative-backup/context-summary.md": session.summary || "",
      "creative-backup/facts.json": JSON.stringify(session.facts),
      "creative-backup/conversation.jsonl": session.turns.map(function (t) { return JSON.stringify(t); }).join("\n") + (session.turns.length ? "\n" : "")
    };
    session.proposals.forEach(function (p) {
      entries["creative-backup/proposals/" + p.id + ".json"] = JSON.stringify(p);
    });
    session.drafts.forEach(function (d) {
      entries["creative-backup/drafts/" + d.id + ".md"] = d.content || "";
      entries["creative-backup/drafts/" + d.id + ".json"] = JSON.stringify(d);
    });
    return entries;
  }

  function dateStamp() {
    var d = new Date();
    var mm = String(d.getMonth() + 1).padStart(2, "0");
    var dd = String(d.getDate()).padStart(2, "0");
    return d.getFullYear() + mm + dd;
  }

  function exportBackup() {
    var filename = (currentBook || "creative") + "-creative-" + dateStamp() + ".zip";
    var lb = localBridge();
    if (lb && primaryBackend === "local") {
      return lb.exportCreativeBackup().then(function (bytes) {
        return { bytes: bytes, filename: filename, mimeType: "application/zip" };
      }).catch(function () {
        return { bytes: window.NWZip.encode(sessionToEntries()), filename: filename, mimeType: "application/zip" };
      });
    }
    return Promise.resolve({ bytes: window.NWZip.encode(sessionToEntries()), filename: filename, mimeType: "application/zip" });
  }

  function parseArchive(bytes) {
    var entries = window.NWZip.decode(bytes);
    var manifest = { schema_version: SCHEMA_VERSION };
    if (entries["creative-backup/manifest.json"]) {
      try { manifest = JSON.parse(entries["creative-backup/manifest.json"]); } catch (e) {}
    }
    var turns = [];
    var conv = entries["creative-backup/conversation.jsonl"] || "";
    conv.split("\n").forEach(function (line) {
      if (line.trim()) { try { turns.push(JSON.parse(line)); } catch (e) {} }
    });
    var proposals = [];
    var drafts = [];
    Object.keys(entries).forEach(function (name) {
      if (name.indexOf("creative-backup/proposals/") === 0) {
        try { proposals.push(JSON.parse(entries[name])); } catch (e) {}
      }
      if (name.indexOf("creative-backup/drafts/") === 0 && name.slice(-5) === ".json") {
        try { drafts.push(JSON.parse(entries[name])); } catch (e) {}
      }
    });
    var summary = entries["creative-backup/context-summary.md"] || "";
    var facts = session.facts;
    if (entries["creative-backup/facts.json"]) {
      try { facts = JSON.parse(entries["creative-backup/facts.json"]); } catch (e) {}
    }
    return {
      schemaVersion: manifest.schema_version || SCHEMA_VERSION,
      summary: summary,
      facts: facts,
      turns: turns,
      proposals: proposals,
      drafts: drafts
    };
  }

  function previewImport(bytes) {
    var parsed = parseArchive(bytes);
    return Promise.resolve({
      schemaVersion: parsed.schemaVersion,
      turnCount: parsed.turns.length,
      proposalCount: parsed.proposals.length,
      draftCount: parsed.drafts.length
    });
  }

  function importBackup(bytes, decision) {
    if (decision === "cancel") return Promise.resolve({ cancelled: true });
    var parsed = parseArchive(bytes);
    if (decision === "copy") {
      // Store as an inactive copy; active session unchanged.
      var copyId = "copy-" + dateStamp() + "-" + Math.random().toString(36).slice(2, 8);
      if (storageAvailable && currentBook) {
        try {
          var copies = [];
          var raw = localStorage.getItem(STORAGE_PREFIX + currentBook + ".copies");
          if (raw) copies = JSON.parse(raw);
          copies.push({ id: copyId, session: parsed });
          localStorage.setItem(STORAGE_PREFIX + currentBook + ".copies", JSON.stringify(copies));
        } catch (e) {}
      }
      return Promise.resolve({ copyId: copyId, turnCount: parsed.turns.length });
    }
    // merge (default)
    session = mergeSession(session, parsed);
    var lb = localBridge();
    if (lb && primaryBackend === "local") {
      return lb.importCreativeBackup(bytes, "merge").then(function () {
        durabilityState = "local";
        notify();
        return { turnCount: session.turns.length, proposalCount: session.proposals.length, draftCount: session.drafts.length };
      }).catch(function () {
        saveToBrowser();
        durabilityState = "backup-required";
        notify();
        return { turnCount: session.turns.length, proposalCount: session.proposals.length, draftCount: session.drafts.length };
      });
    }
    saveToBrowser();
    durabilityState = storageAvailable ? "browser" : "backup-required";
    notify();
    return Promise.resolve({ turnCount: session.turns.length, proposalCount: session.proposals.length, draftCount: session.drafts.length });
  }

  var api = {
    boot: boot,
    clear: clear,
    session: sessionSnapshot,
    durability: durability,
    appendTurn: appendTurn,
    writeState: writeState,
    writeProposal: writeProposal,
    writeDraft: writeDraft,
    exportBackup: exportBackup,
    previewImport: previewImport,
    importBackup: importBackup,
    subscribe: subscribe
  };
  if (typeof window !== "undefined") window.NWCreative = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
