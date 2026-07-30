(function () {
  "use strict";

  var FIELDS = ["premise", "protagonist", "central_conflict", "stakes", "world", "style_audience", "ending_direction"];
  var REQUIRED = ["premise", "protagonist", "central_conflict", "stakes", "style_audience"];
  var CRITICAL = { premise: true, protagonist: true, central_conflict: true, stakes: true };
  var STATUSES = { candidate: true, confirmed: true, assumed: true, conflicted: true };
  var REQUIRED_INTAKE = REQUIRED;

  function emptyConversationState() {
    return {
      phase: "exploring",
      completed_rounds: 0,
      effective_rounds: 0,
      coverage_version: 0,
      coverage: {},
      active_proposal_id: null,
    };
  }

  function clone(o) {
    return o === undefined || o === null ? o : JSON.parse(JSON.stringify(o));
  }

  function turnTextMap(turns) {
    var map = {};
    (turns || []).forEach(function (t) {
      if (t && t.id != null) map[t.id] = String(t.text || "");
    });
    return map;
  }

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

  function validateItem(raw, textMap, autonomy) {
    if (!raw || typeof raw !== "object") throw new Error("coverage item must be an object");
    var field = raw.field;
    if (!FIELDS.hasOwnProperty(field) && FIELDS.indexOf(field) < 0) {
      // FIELDS is an array; use indexOf
    }
    if (FIELDS.indexOf(String(field)) < 0) throw new Error("unknown coverage field: " + field);
    var value = String(raw.value == null ? "" : raw.value).trim();
    if (!value) throw new Error("coverage value is empty for field " + field);
    var status = raw.status;
    if (!STATUSES[String(status)]) throw new Error("unknown coverage status: " + status);
    if (status === "assumed" && !autonomy) throw new Error("assumed status requires autonomy");
    var evidence = raw.evidence;
    if (!Array.isArray(evidence) || evidence.length === 0) {
      throw new Error("coverage item for " + field + " requires at least one evidence record");
    }
    var sourceIds = [];
    var seen = {};
    evidence.forEach(function (ev) {
      if (!ev || typeof ev !== "object") throw new Error("invalid evidence record");
      var tid = ev.turn_id;
      var quote = String(ev.quote == null ? "" : ev.quote);
      if (!tid) throw new Error("evidence turn_id is required");
      if (!(tid in textMap)) throw new Error("evidence turn_id not found: " + tid);
      if (!quote) throw new Error("evidence quote is required");
      if (String(textMap[tid]).indexOf(quote) < 0) {
        throw new Error("evidence quote not found verbatim in turn " + tid);
      }
      if (!seen[tid]) { seen[tid] = true; sourceIds.push(tid); }
    });
    return {
      field: field,
      value: value,
      status: status,
      evidence: clone(evidence),
      source_turn_ids: sourceIds,
      updated_at: raw.updated_at || new Date().toISOString(),
    };
  }

  function applyExtraction(state, extraction, turns, options) {
    options = options || {};
    var autonomy = options.autonomy === true;
    var explicitDecision = options.explicitDecision === true;
    if (!extraction || !Array.isArray(extraction.items)) {
      throw new Error("extraction must contain an items array");
    }
    var next = clone(state);
    if (!next.coverage) next.coverage = {};
    var textMap = turnTextMap(turns);
    var versionChanged = false;
    var evidenceChanged = false;

    extraction.items.forEach(function (raw) {
      var item = validateItem(raw, textMap, autonomy);
      var existing = next.coverage[item.field];
      if (existing && existing.status === "confirmed" && item.value !== existing.value) {
        // mark conflict, preserve confirmed value
        next.coverage[item.field] = {
          value: existing.value,
          source_turn_ids: existing.source_turn_ids,
          evidence: existing.evidence,
          status: "conflicted",
          updated_at: item.updated_at,
        };
        if (CRITICAL[item.field]) versionChanged = true;
        return;
      }
      var isNew = !existing;
      var valueChanged = existing && existing.value !== item.value;
      var statusUpgraded = existing && existing.status !== item.status;
      if (isNew || valueChanged || statusUpgraded) {
        next.coverage[item.field] = item;
        if (CRITICAL[item.field]) versionChanged = true;
        evidenceChanged = true;
      } else {
        // same value/status, maybe merge evidence
        next.coverage[item.field] = item;
      }
    });

    next.completed_rounds = (next.completed_rounds || 0) + 1;
    if (evidenceChanged || explicitDecision) {
      next.effective_rounds = (next.effective_rounds || 0) + 1;
    }
    if (versionChanged) {
      next.coverage_version = (next.coverage_version || 0) + 1;
    }
    var transition = deriveTransition(next);
    next.phase = transition.phase;
    return next;
  }

  function isProposalStale(proposal, state) {
    if (!proposal || !state) return false;
    if (proposal.status === "committed") return false;
    var propVersion = proposal.coverage_version;
    if (typeof propVersion === "number" && typeof state.coverage_version === "number") {
      if (propVersion < state.coverage_version) return true;
    }
    return false;
  }

  function canHandoff(proposal, state) {
    if (!proposal || !state) return false;
    if (proposal.status !== "pending") return false;
    if (isProposalStale(proposal, state)) return false;
    var intake = proposal.intake;
    if (!intake || typeof intake !== "object") return false;
    var ok = REQUIRED_INTAKE.every(function (f) {
      return typeof intake[f] === "string" && intake[f].trim().length > 0;
    });
    if (!ok) return false;
    return true;
  }

  var api = {
    emptyConversationState: emptyConversationState,
    applyExtraction: applyExtraction,
    deriveTransition: deriveTransition,
    isProposalStale: isProposalStale,
    canHandoff: canHandoff,
    FIELDS: FIELDS,
    REQUIRED: REQUIRED,
    CRITICAL: CRITICAL,
    STATUSES: STATUSES,
  };
  if (typeof window !== "undefined") window.NWCreativeCoverage = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
