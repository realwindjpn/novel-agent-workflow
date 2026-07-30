/*
 * web/conversation-router.js — deterministic terminal input classification
 * and one-shot quick-conversation continuity.
 *
 * The main terminal accepts both explicit CLI commands and a single round
 * of natural-language quick reply. This module decides which path an input
 * takes WITHOUT consulting a model: it uses a fixed auxiliary-command set
 * plus a caller-supplied isKnownCommandHead predicate (backed by the same
 * argv table the MCP bridge dispatches against).
 *
 * Continuity rule: the first natural-language message opens a main-window
 * quick card; once that round completes (both turns persisted), a second
 * natural message within `continuityMs` (default 15 minutes) promotes the
 * conversation into the floating window. A command, an explicit reset, a
 * book switch, or elapsing the continuity window all clear the sequence so
 * the next natural message starts fresh on the main surface.
 *
 * Public surface (window.NWConversationRouter):
 *   createRouter({ now, continuityMs, isKnownCommandHead }) -> router
 *     router.classify(text)            -> { kind, head }
 *     router.beginNatural(text)        -> { surface, sessionId, quickRound?, text }
 *     router.completeQuickRound(rec)   -> bool
 *     router.reset(reason)             -> reason
 *     router.snapshot()                -> deep copy | null
 *
 * This module is pure: no DOM, no network, no storage. It owns only the
 * in-memory quick-round sequence.
 */
(function () {
  "use strict";

  // Auxiliary terminal helpers that are always commands regardless of the
  // argv table (they are handled by the local shell, not MCP tools).
  var AUX = { help: true, ls: true, cat: true, tree: true, clear: true, reset: true };

  function createRouter(options) {
    options = options || {};
    var now = options.now || function () { return Date.now(); };
    var continuityMs = options.continuityMs != null ? options.continuityMs : 15 * 60 * 1000;
    var isKnownCommandHead = options.isKnownCommandHead || function () { return false; };
    var seq = 0;
    var quick = null; // { sessionId, userTurnId, assistantTurnId, completedAt }

    function headOf(text) {
      return String(text == null ? "" : text).trim().split(/\s+/)[0].toLowerCase();
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

    // Returns the migration-relevant quickRound fields only (the ids the
    // floating window needs to replay the first round). completedAt is an
    // internal timer and is intentionally excluded from the public payload.
    function quickRoundPayload() {
      if (!quick) return null;
      return {
        sessionId: quick.sessionId,
        userTurnId: quick.userTurnId,
        assistantTurnId: quick.assistantTurnId,
      };
    }

    function beginNatural(text) {
      var current = now();
      if (quick && quick.completedAt != null && current - quick.completedAt <= continuityMs) {
        return { surface: "floating", sessionId: quick.sessionId, quickRound: quickRoundPayload(), text: text };
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
        completedAt: Number(record.completedAt),
      };
      return true;
    }

    function reset(reason) {
      quick = null;
      return reason || "reset";
    }

    function snapshot() {
      return quick ? JSON.parse(JSON.stringify(quick)) : null;
    }

    return {
      classify: classify,
      beginNatural: beginNatural,
      completeQuickRound: completeQuickRound,
      reset: reset,
      snapshot: snapshot,
    };
  }

  var api = { createRouter: createRouter };
  if (typeof window !== "undefined") window.NWConversationRouter = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();