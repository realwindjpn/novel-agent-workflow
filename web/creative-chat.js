/* web/creative-chat.js — freeform creative controller.
 *
 * The controller sits between the user's free-form creative conversation
 * and the formal novel-workflow pipeline. It manages a state machine
 * (idle → responding → compiling → proposal → committing → error),
 * delegates model calls to the injected llm.js adapter, persists every
 * turn / proposal / draft via the creative.js storage adapter, and
 * compiles a confirmed proposal into a formal `idea` plan that still
 * goes through the existing plan-card confirmation gate in chat.js.
 *
 * Two-confirmation gate:
 *   1. acceptProposal()  — marks proposal "accepted", offers the formal
 *      plan to the executor (chat.js renders a plan card).
 *   2. User clicks "执行" on the plan card — chat.js calls NWB.runSmart,
 *      which writes to the real project. The controller never writes to
 *      the core directly.
 *
 * Exposes window.NWCreativeChat = { createController, bind }.
 * Also module.exports for Node tests.
 */
(function () {
  "use strict";

  var AUTONOMY_RE = /(你|由你|模型).*(决定|做主)|你来定/;

  function detectAutonomy(text) {
    return AUTONOMY_RE.test(text || "");
  }

  /* ---- Controller factory ----
   *
   * ports = {
   *   model:    { creativeReply, extractCoverage, compileProposal, assessReadiness? },
   *   storage:  { boot, session, durability, appendTurn, writeState,
   *               writeProposal, writeDraft, writeConversationState,
   *               exportBackup, previewImport, importBackup, subscribe },
   *   executor: { offerExternalPlan },
   *   view:     { renderUser, renderAssistant, showError, renderProposal,
   *               clearProposal, setDurability, renderReadiness,
   *               renderImportChoices, clear,
   *               beginOperation, endOperation, renderCoverage,
   *               renderGuidedMode, markProposalStale },
   *   clock:    function () → ISO string,
   *   idGen:    function () → unique id string
   * }
   */
  function coverageApi() {
    return (typeof window !== "undefined") ? window.NWCreativeCoverage : null;
  }

  function createController(ports) {
    var state = "idle";
    var pendingProposal = null;
    var bookId = "";
    var autonomyGranted = false;
    var conversationState = null;
    var extractionFailures = 0;

    function COV() {
      var api = coverageApi();
      if (!api) throw new Error("NWCreativeCoverage not loaded");
      return api;
    }

    function getConversationState() {
      var sess = ports.storage.session();
      if (sess && sess.conversation_state) return sess.conversation_state;
      if (conversationState) return conversationState;
      return COV().emptyConversationState();
    }

    function modelContext() {
      var sess = ports.storage.session();
      return {
        book: bookId,
        turns: sess.turns || [],
        summary: sess.summary || "",
        facts: sess.facts || {},
        proposals: sess.proposals || [],
        drafts: sess.drafts || [],
        conversation_state: getConversationState()
      };
    }

    /* ---- boot: restore session from storage ---- */
    function boot(book) {
      bookId = book || "";
      return ports.storage.boot(bookId).then(function () {
        var sess = ports.storage.session();
        // Restore conversation state
        if (sess && sess.conversation_state) {
          conversationState = sess.conversation_state;
        } else {
          conversationState = COV().emptyConversationState();
        }
        // Render all conversation turns
        if (sess.turns) {
          sess.turns.forEach(function (t) {
            if (t.role === "user") ports.view.renderUser(t.text);
            else ports.view.renderAssistant(t.text);
          });
        }
        // Restore coverage view
        if (conversationState && conversationState.coverage) {
          ports.view.renderCoverage(conversationState.coverage);
        }
        // Restore the most recent pending proposal
        if (sess.proposals && sess.proposals.length > 0) {
          var pending = null;
          for (var i = sess.proposals.length - 1; i >= 0; i--) {
            if (sess.proposals[i].status === "pending" || sess.proposals[i].status === "accepted") {
              pending = sess.proposals[i];
              break;
            }
          }
          if (pending) {
            pendingProposal = pending;
            ports.view.renderProposal(pending);
            // Check staleness on restore
            if (COV().isProposalStale(pending, getConversationState())) {
              ports.view.markProposalStale("coverage changed since proposal");
            }
          }
        }
        ports.view.setDurability(ports.storage.durability());
        state = "idle";
      });
    }

    /* ---- clear: reset in-memory view, durable records untouched ---- */
    function clear() {
      pendingProposal = null;
      state = "idle";
      ports.view.clear();
    }

    /* ---- submit: user sends free-form text ---- */
    function submit(text, options) {
      options = options || {};
      var surface = options.surface || "floating";
      var autonomy = options.autonomy != null ? options.autonomy : detectAutonomy(text);
      autonomyGranted = autonomyGranted || autonomy;
      state = "responding";

      ports.view.beginOperation({ kind: "reply", surface: surface });
      var userTurn = {
        id: ports.idGen(),
        role: "user",
        text: text,
        ts: ports.clock()
      };
      ports.view.renderUser(text);

      return ports.storage.appendTurn(userTurn).then(function () {
        return ports.model.creativeReply({
          text: text,
          autonomy: autonomy,
          context: modelContext()
        });
      }).then(function (result) {
        var assistantTurn = {
          id: ports.idGen(),
          role: "assistant",
          text: result.reply,
          ts: ports.clock()
        };
        ports.view.renderAssistant(result.reply);
        return ports.storage.appendTurn(assistantTurn).then(function () { return result; });
      }).then(function () {
        ports.view.endOperation({ kind: "reply", outcome: "success" });
        state = "idle";
        // Coverage extraction — non-blocking for the reply itself
        return extractAndApplyCoverage(autonomy).catch(function () { /* handled inside */ });
      }).catch(function (err) {
        ports.view.endOperation({ kind: "reply", outcome: "error" });
        ports.view.showError(err);
        state = "error";
        // User turn is already persisted; no rule-engine fallback
      });
    }

    /* ---- letModelDecide: explicit autonomy grant ---- */
    function letModelDecide(text) {
      return submit(text, { autonomy: true });
    }

    function extractAndApplyCoverage(autonomy) {
      return ports.model.extractCoverage({
        context: modelContext(),
        autonomy: autonomyGranted
      }).then(function (extraction) {
        var turns = ports.storage.session().turns || [];
        var current = getConversationState();
        var nextState = COV().applyExtraction(current, extraction, turns, { autonomy: autonomyGranted });
        conversationState = nextState;
        ports.storage.writeConversationState(nextState);
        ports.view.renderCoverage(nextState.coverage);
        // Check stale proposal
        if (pendingProposal && COV().isProposalStale(pendingProposal, nextState)) {
          ports.view.markProposalStale("coverage_version changed");
        }
        applyTransition(nextState);
        extractionFailures = 0;
      }).catch(function () {
        extractionFailures += 1;
        if (extractionFailures >= 2) {
          ports.view.renderGuidedMode({ phase: "manual-checklist", missingFields: COV().REQUIRED });
        }
        // Do not roll back the reply
      });
    }

    function applyTransition(nextState) {
      var transition = COV().deriveTransition(nextState);
      if (transition.action === "auto-proposal") {
        generateProposal({ automatic: true });
      } else if (transition.action === "ask-missing") {
        var missing = COV().REQUIRED.filter(function (f) {
          var item = nextState.coverage[f];
          return !item || item.status === "conflicted";
        });
        ports.view.renderGuidedMode({ phase: nextState.phase, action: transition.action, missingFields: missing });
      } else if (transition.action === "force-draft") {
        generateProposal({ forcedDraft: true });
      }
    }

    /* ---- generateProposal: ask model to compile a formal proposal ---- */
    function generateProposal(options) {
      options = options || {};
      state = "compiling";
      ports.view.beginOperation({ kind: "compile", surface: "floating" });
      return ports.model.compileProposal({
        autonomy: autonomyGranted,
        context: modelContext(),
        forcedDraft: options.forcedDraft === true
      }).then(function (proposal) {
        proposal.id = proposal.id || ports.idGen();
        proposal.status = "pending";
        var cs = getConversationState();
        proposal.coverage_version = cs.coverage_version;
        proposal.coverage_snapshot = cs.coverage;
        pendingProposal = proposal;
        ports.view.renderProposal(proposal);
        return ports.storage.writeProposal(proposal);
      }).then(function () {
        ports.view.endOperation({ kind: "compile", outcome: "success" });
        state = "proposal";
      }).catch(function (err) {
        ports.view.endOperation({ kind: "compile", outcome: "error" });
        state = "error";
        ports.view.showError(err);
      });
    }

    /* ---- saveTrialDraft: persist a draft without formal execution ---- */
    function saveTrialDraft(title, content, sourceTurnIds) {
      var draft = {
        id: ports.idGen(),
        title: title,
        content: content,
        source_turn_ids: sourceTurnIds || [],
        status: "trial",
        created_at: ports.clock()
      };
      return ports.storage.writeDraft(draft).then(function () {
        state = "idle";
        return draft;
      });
    }

    /* ---- submitProposalToWorkflow: first confirmation — offer formal plan ----
     *
     * Two independent confirmation gates:
     *   1. This method (float submit) — validates canHandoff, marks proposal
     *      "accepted", offers the formal plan to the executor (plan card).
     *   2. User clicks "执行" on the plan card — chat.js calls NWB.runSmart,
     *      which writes to the real project. The controller never writes to
     *      the core directly.
     */
    function submitProposalToWorkflow() {
      if (!pendingProposal) return Promise.resolve();
      var currentState = getConversationState();
      if (COV().isProposalStale(pendingProposal, currentState)) {
        ports.view.showError({ message: "提案已过期，需要重新编译" });
        return Promise.resolve();
      }
      if (!COV().canHandoff(pendingProposal, currentState)) {
        ports.view.showError({ message: "缺少必填项或条件未满足，无法提交到主流程" });
        return Promise.resolve();
      }
      state = "committing";
      pendingProposal.status = "accepted";
      return ports.storage.writeProposal(pendingProposal).then(function () {
        var nextState = getConversationState();
        nextState.phase = "handed-off";
        conversationState = nextState;
        return ports.storage.writeConversationState(nextState);
      }).then(function () {
        var plan = formalIdeaPlan(pendingProposal);
        ports.executor.offerExternalPlan(plan);
        state = "idle";
      });
    }

    /* ---- acceptProposal: compatibility alias for submitProposalToWorkflow ---- */
    function acceptProposal() {
      return submitProposalToWorkflow();
    }

    /* ---- formalIdeaPlan: build the formal idea argv from a proposal ----
     *
     * The cmdDisplay intentionally hides the serialized intake JSON;
     * the actual argv carries the full 15-field intake for the CLI.
     */
    function formalIdeaPlan(proposal) {
      var summary = proposal.summary || proposal.preview;
      var intake = proposal.intake || {};
      return {
        kind: "custom",
        intent: "采用创意方案",
        explain: "把已确认的自然语言方案写入正式工作流。",
        cmdDisplay: "novel-workflow idea . --summary <已确认方案> --interview <内部结构化创意>",
        argv: ["idea", ".", "--summary", summary, "--interview", JSON.stringify(intake)],
        setup: {},
        source: "creative-compiler",
        proposalId: proposal.id,
        intake: true,
        resultSummary: function (ok, result) {
          if (ok) return "创意方案已写入正式工作流。";
          return "写入失败：" + ((result && result.err) || "未知错误");
        }
      };
    }

    /* ---- reviseProposal: go back to discussion ---- */
    function reviseProposal() {
      pendingProposal = null;
      ports.view.clearProposal();
      state = "idle";
    }

    /* ---- discardProposal: drop the pending proposal ---- */
    function discardProposal() {
      if (!pendingProposal) return;
      pendingProposal = null;
      ports.view.clearProposal();
      state = "idle";
    }

    /* ---- exportBackup: delegate to storage ---- */
    function exportBackup() {
      return ports.storage.exportBackup();
    }

    /* ---- importBackup: preview → merge attempt → collision choices ---- */
    function importBackup(bytes) {
      return ports.storage.previewImport(bytes).then(function (preview) {
        if (preview && preview.hasExisting) {
          // Attempt merge; if collision detected, ask user to choose
          return ports.storage.importBackup(bytes, "merge").then(function (result) {
            if (result && result.collision) {
              // Use JSON.parse so the array inherits the outer realm's
              // Array.prototype (JSON is shared from the host context),
              // avoiding cross-realm deepEqual failures in Node 22+.
              ports.view.renderImportChoices(JSON.parse('["merge","copy","cancel"]'));
            }
            return result;
          });
        }
        // No existing data — merge directly
        return ports.storage.importBackup(bytes, "merge");
      });
    }

    function currentState() {
      return state;
    }

    return {
      boot: boot,
      clear: clear,
      submit: submit,
      letModelDecide: letModelDecide,
      generateProposal: generateProposal,
      saveTrialDraft: saveTrialDraft,
      acceptProposal: acceptProposal,
      submitProposalToWorkflow: submitProposalToWorkflow,
      reviseProposal: reviseProposal,
      discardProposal: discardProposal,
      importBackup: importBackup,
      exportBackup: exportBackup,
      state: currentState
    };
  }

  /* ---- Browser singleton binding ----
   *
   * In the browser, a single controller is bound to the real ports
   * (model = window.NWL, storage = window.NWCreative, executor =
   * window.NWC, view = DOM adapter). This is wired up after all
   * dependent scripts have loaded.
   */
  function bind() {
    if (typeof document === "undefined") return null;
    var view = createDomView();
    var executor = createDomExecutor();
    var ports = {
      model: window.NWL,
      storage: window.NWCreative,
      executor: executor,
      view: view,
      clock: function () { return new Date().toISOString(); },
      idGen: function () {
        return "t-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
      }
    };
    var controller = createController(ports);
    controller._ports = ports;
    return controller;
  }

  function createDomView() {
    var scroll = document.getElementById("creative-scroll");
    if (!scroll) scroll = document.getElementById("chat-scroll");
    function esc(s) { return window.NWA ? window.NWA.escapeHtml(s || "") : (s || ""); }
    function append(role, text) {
      if (!scroll) return;
      var div = document.createElement("div");
      div.className = "chat-msg chat-" + role;
      div.innerHTML = '<div class="chat-bubble ' + (role === "user" ? "user-bubble" : "asst-bubble") + '">' + esc(text) + "</div>";
      scroll.appendChild(div);
      scroll.scrollTop = scroll.scrollHeight;
    }
    var proposalEl = document.getElementById("creative-proposal");
    return {
      renderUser: function (text) { append("user", text); },
      renderAssistant: function (text) { append("assistant", text); },
      showError: function (err) {
        append("assistant", "⚠ " + ((err && err.message) || err || "未知错误"));
      },
      renderProposal: function (p) {
        if (!proposalEl) return;
        proposalEl.style.display = "";
        var html = '<div class="proposal-card">' +
          '<div class="proposal-preview">' + esc(p.preview || "") + "</div>";
        if (p.summary) html += '<div class="proposal-summary">' + esc(p.summary) + "</div>";
        if (p.assumptions && p.assumptions.length) {
          html += '<div class="proposal-assumptions"><b>假设：</b>' +
            p.assumptions.map(esc).join("、") + "</div>";
        }
        if (p.uncertainties && p.uncertainties.length) {
          html += '<div class="proposal-uncertainties"><b>待确认：</b>' +
            p.uncertainties.map(esc).join("、") + "</div>";
        }
        html += '<div class="proposal-btns">' +
          '<button class="btn primary" data-act="accept">采纳并编译</button>' +
          '<button class="btn" data-act="discard">放弃</button>' +
          "</div></div>";
        proposalEl.innerHTML = html;
      },
      clearProposal: function () {
        if (!proposalEl) return;
        proposalEl.style.display = "none";
        proposalEl.innerHTML = "";
      },
      setDurability: function (s) {
        var el = document.getElementById("creative-durability");
        if (el) el.textContent = s;
      },
      beginOperation: function (info) {
        if (!scroll) return;
        var existing = scroll.querySelector(".chat-typing");
        if (existing) return; // at most one animation node
        var div = document.createElement("div");
        div.className = "chat-typing";
        div.setAttribute("aria-live", "polite");
        div.innerHTML = "<span></span><span></span><span></span>";
        scroll.appendChild(div);
        scroll.scrollTop = scroll.scrollHeight;
      },
      endOperation: function (info) {
        if (!scroll) return;
        var dots = scroll.querySelectorAll(".chat-typing");
        dots.forEach(function (n) { n.remove(); });
      },
      renderCoverage: function (coverage) {
        var el = document.getElementById("creative-coverage");
        if (!el) return;
        var keys = Object.keys(coverage || {});
        if (!keys.length) { el.innerHTML = ""; return; }
        el.innerHTML = keys.map(function (k) {
          var item = coverage[k];
          return '<div class="coverage-item coverage-' + item.status + '"><b>' + k + '</b>: ' + esc(item.value || "") + "</div>";
        }).join("");
      },
      renderGuidedMode: function (info) {
        var el = document.getElementById("creative-guided");
        if (!el) return;
        var missing = (info && info.missingFields) || [];
        el.innerHTML = '<div class="guided-mode">引导模式：补充 ' + missing.map(esc).join("、") + "</div>";
      },
      markProposalStale: function (reason) {
        var el = document.getElementById("creative-proposal");
        if (!el) return;
        var notice = el.querySelector(".proposal-stale");
        if (notice) return;
        notice = document.createElement("div");
        notice.className = "proposal-stale";
        notice.textContent = "内容已变化，需要重新编译";
        el.appendChild(notice);
      },
      renderReadiness: function (ready, reason) {
        var el = document.getElementById("creative-readiness");
        if (el) {
          el.textContent = ready ? "✓ 创意素材已齐备，可以编译方案" : (reason || "继续对话，积累素材");
          el.className = ready ? "ready yes" : "ready no";
        }
      },
      renderImportChoices: function (choices) {
        var el = document.getElementById("creative-import-choices");
        if (!el) return;
        el.innerHTML = choices.map(function (c) {
          return '<button class="btn" data-import-choice="' + c + '">' + c + "</button>";
        }).join("");
      },
      clear: function () {
        if (scroll) scroll.innerHTML = "";
        if (proposalEl) { proposalEl.style.display = "none"; proposalEl.innerHTML = ""; }
      }
    };
  }

  function createDomExecutor() {
    return {
      offered: [],
      executed: [],
      offerExternalPlan: function (plan) {
        this.offered.push(plan);
        // Delegate to chat.js plan-card rendering if available
        if (window.NWC && window.NWC.offerExternalPlan) {
          window.NWC.offerExternalPlan(plan);
        }
      }
    };
  }

  var api = {
    createController: createController,
    bind: bind,
    detectAutonomy: detectAutonomy
  };
  if (typeof window !== "undefined") window.NWCreativeChat = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
