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
   *   model:    { creativeReply, assessReadiness, compileProposal },
   *   storage:  { boot, session, durability, appendTurn, writeState,
   *               writeProposal, writeDraft, exportBackup, previewImport,
   *               importBackup, subscribe },
   *   executor: { offerExternalPlan },
   *   view:     { renderUser, renderAssistant, showError, renderProposal,
   *               clearProposal, setDurability, renderReadiness,
   *               renderImportChoices, clear },
   *   clock:    function () → ISO string,
   *   idGen:    function () → unique id string
   * }
   */
  function createController(ports) {
    var state = "idle";
    var pendingProposal = null;
    var bookId = "";
    var autonomyGranted = false;

    function modelContext() {
      var sess = ports.storage.session();
      return {
        book: bookId,
        turns: sess.turns || [],
        summary: sess.summary || "",
        facts: sess.facts || {},
        proposals: sess.proposals || [],
        drafts: sess.drafts || []
      };
    }

    /* ---- boot: restore session from storage ---- */
    function boot(book) {
      bookId = book || "";
      return ports.storage.boot(bookId).then(function () {
        var sess = ports.storage.session();
        // Render all conversation turns
        if (sess.turns) {
          sess.turns.forEach(function (t) {
            if (t.role === "user") ports.view.renderUser(t.text);
            else ports.view.renderAssistant(t.text);
          });
        }
        // Restore the most recent pending proposal
        if (sess.proposals && sess.proposals.length > 0) {
          var pending = null;
          for (var i = sess.proposals.length - 1; i >= 0; i--) {
            if (sess.proposals[i].status === "pending") {
              pending = sess.proposals[i];
              break;
            }
          }
          if (pending) {
            pendingProposal = pending;
            ports.view.renderProposal(pending);
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
    function submit(text) {
      return doSubmit(text, detectAutonomy(text));
    }

    /* ---- letModelDecide: explicit autonomy grant ---- */
    function letModelDecide(text) {
      return doSubmit(text, true);
    }

    function doSubmit(text, autonomy) {
      state = "responding";
      autonomyGranted = autonomyGranted || autonomy;
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
        return ports.storage.appendTurn(assistantTurn);
      }).then(function () {
        state = "idle";
        // Non-blocking readiness assessment — never blocks the conversation
        ports.model.assessReadiness({
          text: text,
          context: modelContext()
        }).then(function (r) {
          ports.view.renderReadiness(r.ready, r.reason);
        });
      }).catch(function (err) {
        state = "error";
        ports.view.showError(err);
        // User turn is already persisted; no rule-engine fallback
      });
    }

    /* ---- generateProposal: ask model to compile a formal proposal ---- */
    function generateProposal() {
      state = "compiling";
      return ports.model.compileProposal({
        autonomy: autonomyGranted,
        context: modelContext()
      }).then(function (proposal) {
        pendingProposal = proposal;
        ports.view.renderProposal(proposal);
        return ports.storage.writeProposal(proposal);
      }).then(function () {
        state = "proposal";
      }).catch(function (err) {
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

    /* ---- acceptProposal: first confirmation — offer formal plan ---- */
    function acceptProposal() {
      if (!pendingProposal) return Promise.resolve();
      state = "committing";
      pendingProposal.status = "accepted";
      return ports.storage.writeProposal(pendingProposal).then(function () {
        var plan = formalIdeaPlan(pendingProposal);
        ports.executor.offerExternalPlan(plan);
        state = "idle";
      });
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
