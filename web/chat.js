/* novel-workflow live runner — white (plain-language) mode engine. (v3)
 *
 * v3 changes (frontend polish):
 *   - Plans are derived verbatim from NW_TAPE steps: the chat builds the
 *     plan's argv and setup from a tape step, so REPLAY mode can match
 *     argv byte-for-byte and play back the recorded stdout. (Previously
 *     plans diverged from tape — wrong author id, only one review step,
 *     outline ran review without first writing the artifact, etc.)
 *   - Multi-step plans (write+review, all four review gates) go through
 *     NWB.runSeq which queues the whole sequence as one slot, with
 *     replay matching each step independently.
 *   - Status queries (现在到哪了 / 第 N 章状态 / 章节列表) read the project
 *     state directly via NWB.readState() instead of shelling out — they
 *     work in both LIVE and REPLAY with no engine call at all.
 *   - REPLAY mode rejects only the genuinely-unsupported plans (init
 *     title, idea intake, outline-repair) with an honest message; every
 *     other plan runs from the recording.
 *   - runLive / runSmart failures in REPLAY show the actual reason, not
 *     a generic "engine not live".
 *   - Bug fix: handlePendingCancel used to set pending=null then read
 *     pending.plan → null deref.
 *   - Typing indicator while commands are in flight.
 *   - Mode switch uses body.white class; the mobile tab logic in app.js
 *     stays in sync.
 */
(function () {
  "use strict";

  /* ============================================================
   * DOM refs
   * ============================================================ */
  var modeSwitchEnc = document.getElementById("mode-enc");
  var modeSwitchWhi = document.getElementById("mode-whi");
  var termPanel = document.getElementById("term-panel");
  var chatPanel = document.getElementById("chat-panel");
  var chatScroll = document.getElementById("chat-scroll");
  var chatInput = document.getElementById("chat-input");
  var chatHint = document.getElementById("chat-hint");
  var chatSend = document.getElementById("chat-send");

  /* ============================================================
   * Session state
   * ============================================================ */
  var mode = "encode";                // encode | white
  var pending = null;                 // {kind:"plan", plan, div} when waiting on user
  var lastResult = null;
  var hasGreeted = false;

  function esc(s) { return window.NWA.escapeHtml(s || ""); }
  function ansi(s) { return window.NWA.ansiToHtml(s || ""); }

  /* ============================================================
   * Mode switch (v3: body class — mobile + desktop both honour it)
   * ============================================================ */
  function setMode(m) {
    mode = m;
    if (m === "white") {
      modeSwitchWhi.classList.add("on"); modeSwitchEnc.classList.remove("on");
      document.body.classList.add("white");
      if (!hasGreeted) { hasGreeted = true; greet(); }
      setTimeout(function () { chatInput.focus(); }, 0);
    } else {
      modeSwitchEnc.classList.add("on"); modeSwitchWhi.classList.remove("on");
      document.body.classList.remove("white");
    }
  }
  modeSwitchEnc.addEventListener("click", function () { setMode("encode"); });
  modeSwitchWhi.addEventListener("click", function () { setMode("white"); });

  /* ============================================================
   * Tape-derived plan builder
   * ============================================================ */
  function tapeStepById(id) {
    var tape = window.NW_TAPE && window.NW_TAPE.steps;
    if (!tape) return null;
    for (var i = 0; i < tape.length; i++) if (tape[i].id === id) return tape[i];
    return null;
  }
  /* Build a plan that wraps a single tape step verbatim. Chat-time
   * intent/explain text is layered on top, but argv + setup + display
   * come straight from the recording so REPLAY can match. */
  function tapeCmd(id, intent, explain) {
    var s = tapeStepById(id);
    if (!s) return { kind: "_missing", intent: intent, explain: explain + "（引导中未找到）" };
    return {
      kind: "tape",
      intent: intent, explain: explain,
      cmdDisplay: s.display,
      argv: s.argv.slice(),
      setup: s.setup || {},
      display: s.display,
      id: s.id,
      resultSummary: function (ok, r) {
        if (ok) return id + " 步骤已执行。";
        return id + " 步骤失败：" + ((r && r.err || "").split("\n")[0] || "exit " + (r && r.code));
      }
    };
  }
  /* Build a plan that runs a list of tape steps in order. */
  function tapeSeq(ids, intent, explain) {
    var cmds = [];
    for (var i = 0; i < ids.length; i++) {
      var s = tapeStepById(ids[i]);
      if (!s) return { kind: "_missing", intent: intent, explain: explain + "（缺 " + ids[i] + "）" };
      cmds.push({ setup: s.setup || {}, argv: s.argv.slice() });
    }
    var summaryLines = ids.map(function (i) { return "  · " + i; }).join("\n");
    return {
      kind: "seq",
      intent: intent, explain: explain,
      cmdDisplay: cmds.map(function (c) { return "novel-workflow " + c.argv.join(" "); }).join("\n          &&   "),
      seq: cmds,
      resultSummary: function (ok, r) {
        if (ok) return "全部子步骤已执行：\n" + summaryLines;
        return "中间某步失败：" + ((r && r.err || "").split("\n")[0] || "exit " + (r && r.code));
      }
    };
  }

  /* ============================================================
   * Chat UI primitives (with typing indicator)
   * ============================================================ */
  function appendBubble(role, html) {
    var div = document.createElement("div");
    div.className = "chat-msg chat-" + role;
    div.innerHTML = html;
    chatScroll.appendChild(div);
    chatScroll.scrollTop = chatScroll.scrollHeight;
    return div;
  }
  function userMsg(text) { appendBubble("user", '<div class="chat-bubble user-bubble">' + esc(text) + "</div>"); }
  function assistantMsg(text) { appendBubble("assistant", '<div class="chat-bubble asst-bubble">' + esc(text) + "</div>"); }
  function assistantHtml(html) { appendBubble("assistant", '<div class="chat-bubble asst-bubble">' + html + "</div>"); }
  function showTyping() {
    var d = appendBubble("assistant", '<div class="chat-bubble asst-bubble"><span class="chat-typing"><i></i><i></i><i></i></span></div>');
    return d;
  }
  function planCard(plan) {
    var div = document.createElement("div");
    div.className = "chat-msg chat-assistant";
    var intentHtml = '<div class="plan-intent">' + esc(plan.intent) + "</div>";
    var explainHtml = '<div class="plan-explain">' + esc(plan.explain) + "</div>";
    var cmdHtml = '<div class="plan-cmd">$ <span>' + esc(plan.cmdDisplay) + "</span></div>";
    var btnsHtml = '<div class="plan-btns">' +
      '<button class="btn primary" data-plan-act="run">▶ 执行</button>' +
      '<button class="btn" data-plan-act="cancel">取消</button>' +
      "</div>";
    div.innerHTML = '<div class="plan-card">' + intentHtml + explainHtml + cmdHtml + btnsHtml + "</div>";
    chatScroll.appendChild(div); chatScroll.scrollTop = chatScroll.scrollHeight;
    div.querySelector('[data-plan-act="run"]').addEventListener("click", function () {
      pending = null;
      div.querySelector(".plan-card").classList.add("running");
      div.querySelectorAll("button").forEach(function (b) { b.disabled = true; });
      executePlan(plan, div);
    });
    div.querySelector('[data-plan-act="cancel"]').addEventListener("click", function () {
      pending = null;
      div.querySelector(".plan-card").classList.add("cancelled");
      div.querySelectorAll("button").forEach(function (b) { b.disabled = true; });
      assistantMsg("已取消。你可以换个说法，或说「下一步」继续流水线。");
    });
    return div;
  }
  function slotCard(question, onSubmit) {
    var div = document.createElement("div");
    div.className = "chat-msg chat-assistant";
    div.innerHTML = '<div class="slot-card">' +
      '<div class="slot-q">需要补一个参数</div>' +
      '<div class="slot-label">' + esc(question) + "</div>" +
      '<input class="slot-input" type="text" autocomplete="off" spellcheck="false" placeholder="在这里输入，回车提交">' +
      "</div>";
    chatScroll.appendChild(div); chatScroll.scrollTop = chatScroll.scrollHeight;
    var inp = div.querySelector(".slot-input");
    setTimeout(function () { inp.focus(); }, 0);
    inp.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        ev.preventDefault();
        var v = inp.value.trim();
        if (!v) return;
        div.querySelectorAll("input").forEach(function (i) { i.disabled = true; });
        div.querySelector(".slot-card").classList.add("filled");
        onSubmit(v);
      }
    });
  }

  /* ============================================================
   * Greeting + capability hint
   * ============================================================ */
  function greet() {
    assistantHtml(
      '<div class="greet-title">嗨，我是你这本小说的<strong> 白话模式</strong> 助手</div>' +
      '<div class="greet-body">用自然语言告诉我你想做什么，我把它翻译成真实的 <code>novel-workflow</code> 命令执行。所有写操作都会先给你看将要执行什么，确认后再跑。' +
      '<div class="greet-chips">' +
      '<button class="chip" data-q="现在到哪了">现在到哪了？</button>' +
      '<button class="chip" data-q="下一步">下一步该做什么</button>' +
      '<button class="chip" data-q="开始一本新书">开始一本新书</button>' +
      '<button class="chip" data-q="发布第 1 章">发布第 1 章</button>' +
      '<button class="chip" data-q="help">列出我都会什么</button>' +
      "</div></div>"
    );
    chatScroll.querySelectorAll(".chip").forEach(function (c) {
      c.addEventListener("click", function () {
        var q = c.getAttribute("data-q");
        chatInput.value = q;
        handleChatSubmit();
      });
    });
    refreshStateSummary("让我先看一眼项目状态——", " 完成后我会告诉你：");
  }

  /* ============================================================
   * State summary (truthful, derived from workflow.json / chapters)
   * ============================================================ */
  function refreshStateSummary(prefix, suffix) {
    var NWB = window.NWB; if (!NWB) return;
    var st = NWB.readState();
    if (!st) { return; }
    var lines = [];
    if (!st.projectExists) {
      lines.push("项目还没立项。说「开始一本新书」或「创建项目」我来帮你建。");
    } else {
      var p = st.project;
      lines.push("<b>《" + esc(p.title || "未命名") + "》</b> · 当前阶段 <b>" + esc(p.stage || "IDEA") + "</b>");
      var conceptTxt = {PENDING: "未完成", PASS: "已通过", FAIL: "未通过"}[p.concept] || p.concept;
      var bibleTxt = {PENDING: "未写", WRITTEN: "已写"}[p.bible] || p.bible;
      lines.push("· 概念评审：" + esc(conceptTxt) + "  ·  圣经：" + esc(bibleTxt));
      var om = {PENDING: "未写", WRITTEN: "已写", PASS: "已通过", FAIL: "未通过"}[p.outline.master] || p.outline.master;
      var ov = {PENDING: "未写", WRITTEN: "已写", PASS: "已通过", FAIL: "未通过"}[p.outline.volume] || p.outline.volume;
      var oc = {PENDING: "未写", WRITTEN: "已写", PASS: "已通过", FAIL: "未通过"}[p.outline.chapter] || p.outline.chapter;
      lines.push("· 大纲：master " + esc(om) + " · volume " + esc(ov) + " · chapter " + esc(oc));
      lines.push("· 大纲锁定：" + (p.outlineLocked ? "<b style=\"color:var(--ok)\">已锁定</b>" : "<b style=\"color:var(--warn)\">未锁定</b>"));
      if (st.chapters.length === 0) {
        lines.push("· 章节：还没有签发任何章节。");
      } else {
        st.chapters.forEach(function (c) {
          var gateSummary = summarizeGates(c.gates);
          lines.push("· 第 " + c.chapter + " 章 <b>《" + esc(c.title) + "》</b> · " + esc(c.status) + "（" + gateSummary + "）");
        });
      }
      lines.push(nextStepHint(p, st.chapters));
    }
    assistantMsg((prefix || "") + "\n" + lines.join("\n") + (suffix || ""));
  }
  function summarizeGates(gates) {
    if (!gates) return "无门禁";
    var required = ["author", "editor", "reader"];
    var pass = 0, skip = 0, pending = 0;
    required.forEach(function (g) {
      var v = gates[g];
      if (v === "PASS") pass++;
      else if (v === "SKIP_WITH_REASON") skip++;
      else pending++;
    });
    var parts = [];
    if (pass) parts.push(pass + " 门通过");
    if (skip) parts.push(skip + " 门跳过");
    if (pending) parts.push(pending + " 门未审");
    return parts.join("，");
  }
  function nextStepHint(p, chapters) {
    if (p.stage === "IDEA" || !p.concept || p.concept === "PENDING") return "下一步：录入创意、跑概念评审。";
    if (p.concept === "FAIL") return "下一步：修概念（先修复再 review）。说「重做概念」我来帮你。";
    if (!p.bible || p.bible === "PENDING") return "下一步：写圣经。说「写圣经」我会跑。";
    var o = p.outline;
    if (o.master === "PENDING") return "下一步：写 master 级大纲。说「写大纲」我会跑。";
    if (o.master === "FAIL" || o.volume === "FAIL" || o.chapter === "FAIL") return "下一步：修失败的大纲级别。说「修大纲」我会重做。";
    if (o.master !== "PASS" || o.volume !== "PASS" || o.chapter !== "PASS") {
      if (o.volume === "PENDING") return "下一步：写 volume 级大纲并通过评审。";
      if (o.chapter === "PENDING") return "下一步：写 chapter 级大纲并通过评审。";
    }
    if (!p.outlineLocked) return "下一步：锁定大纲。说「锁定大纲」我会跑。";
    if (chapters.length === 0) return "下一步：签发第 1 章。说「签发第 1 章」我会跑。";
    var next = chapters[chapters.length - 1];
    var ns = next.status;
    if (ns === "ISSUED" || ns === "BLOCKED") return "下一步：写候选稿。说「写第 " + next.chapter + " 章草稿」我会跑。";
    if (ns === "IN_REVIEW") return "下一步：把剩余门禁跑完（editor / reader / military / science）。";
    if (ns === "READY_TO_RELEASE") return "下一步：显式 release。说「发布第 " + next.chapter + " 章」我会跑。";
    if (ns === "RELEASED") return "下一步：再签发下一章，或跑安全检查。说「安全检查」会做扫描。";
    return "当前项目状态机处于 " + esc(p.stage) + "，可继续。";
  }

  /* ============================================================
   * Plan execution (v3: tape-derived, runSmart / runSeq)
   * ============================================================ */
  function executePlan(plan, planDiv) {
    var NWB = window.NWB;
    if (NWB.getMode() === "booting") {
      assistantMsg("引擎还在启动中，等它到 LIVE 或 REPLAY 再执行。可以先看「现在到哪了」我等下再算。");
      planDiv.querySelector(".plan-card").classList.add("errored");
      return;
    }
    var typing = showTyping();
    var p;
    if (plan.kind === "seq") p = NWB.runSeq(plan.seq);
    else if (plan.kind === "tape" || plan.kind === "custom") p = NWB.runSmart(plan.setup || {}, plan.argv || [], !!plan.intake);
    else if (plan.kind === "reset") p = NWB.runSmart({}, ["__reset__"], false);
    else p = NWB.runSmart(plan.setup || {}, plan.argv || [], !!plan.intake);
    p.then(function (result) {
      if (typing && typing.parentNode) typing.parentNode.removeChild(typing);
      var r = plan.kind === "seq" ? (result && result.last) : result;
      lastResult = r;
      var ok = (r && r.code === 0);
      var cls = ok ? "ok" : (r && r.code === 2 ? "blocked" : "err");
      planDiv.querySelector(".plan-card").classList.add("done-" + cls);
      var sumDiv = document.createElement("div");
      sumDiv.className = "plan-result plan-result-" + cls;
      var headTxt = ok ? "✓ 已执行" : (r && r.code === 2 ? "✗ 状态机拒绝" : "✗ 失败（exit " + (r && r.code) + "）");
      sumDiv.innerHTML = '<div class="plan-result-head">' + headTxt + "</div>" +
        '<div class="plan-result-body">' + esc(plan.resultSummary(ok, r)) + "</div>" +
        '<div class="plan-result-actions"><button class="btn small" data-act="show-out">查看完整输出</button> ' +
        (ok ? '<button class="btn small primary" data-act="refresh">刷新状态摘要</button>' : "") + "</div>";
      planDiv.querySelector(".plan-card").appendChild(sumDiv);
      sumDiv.querySelector('[data-act="show-out"]').addEventListener("click", function () { showLastOutput(plan.cmdDisplay); });
      if (ok) {
        var btn = sumDiv.querySelector('[data-act="refresh"]');
        if (btn) btn.addEventListener("click", function () { chatInput.value = "现在到哪了"; handleChatSubmit(); });
      }
      NWB.refreshFiles();
      if (ok) refreshStateSummary("—— 状态已更新 ——", "");
    }, function (err) {
      if (typing && typing.parentNode) typing.parentNode.removeChild(typing);
      planDiv.querySelector(".plan-card").classList.add("errored");
      assistantMsg("执行出错：" + ((err && err.message) || err));
    });
  }

  function showLastOutput(cmd) {
    if (!lastResult) return;
    var div = document.createElement("div");
    div.className = "chat-msg chat-assistant";
    var out = lastResult.out || "";
    var err = lastResult.err || "";
    var head = '<div class="lastcmd-head">$ ' + esc(cmd) + "  ·  exit " + (lastResult.code || 0) + "</div>";
    var body = (out ? '<pre class="lastcmd-out">' + ansi(out) + "</pre>" : "");
    var errb = (err ? '<pre class="lastcmd-err">' + ansi(err) + "</pre>" : "");
    div.innerHTML = '<div class="lastcmd-card">' + head + body + errb + "</div>";
    chatScroll.appendChild(div); chatScroll.scrollTop = chatScroll.scrollHeight;
  }

  /* ============================================================
   * Intent matcher (rule-based, priority order)
   * ============================================================ */
  function match(text) {
    var t = text.trim();
    if (!t) return null;
    var low = t.toLowerCase();

    if (pending && pending.kind === "plan") {
      if (/^(确认|好|可以|执行|嗯|ok|yes|y|✓)$/i.test(low)) return { kind: "_pending_run" };
      if (/^(取消|算了|不|no|n|✗|×)$/i.test(low)) return { kind: "_pending_cancel" };
    }

    if (/^(help|帮助|怎么用|你会什么|能干啥|能力|功能)$/i.test(low)) return { kind: "help" };

    if (/^(重置|清空|重来|reset)/i.test(t)) return { kind: "reset" };

    if (/状态|进度|到哪了|怎么样了|如何了|什么情况|进展/.test(t)) return { kind: "query_status" };
    if (/第\s*(\d+)\s*章.*(状态|怎样|进度|怎么样|如何|详情)/.test(t)) {
      var m1 = t.match(/第\s*(\d+)\s*章/);
      return { kind: "query_chapter", n: parseInt(m1[1], 10) };
    }
    if (/^(角色|评审团|谁审|五角色|独立|independence)/i.test(t)) return { kind: "query_roles" };
    if (/^(章节列表|所有章节|有哪些章|章节|chapters)/i.test(low)) return { kind: "query_chapters" };
    if (/^(安全检查|检查项目|敏感|泄密|security|check)/i.test(low)) return { kind: "query_security" };
    if (/^(校验|check|check all|check all)/i.test(low)) return { kind: "query_check" };

    if (/^ls(\s|$)/.test(low) || /看看文件|文件列表|有什么文件|文件树|目录/.test(t)) return { kind: "query_ls" };
    if (/^cat\s+/.test(low) || /^(打开|看看|看一下)\s*(.+\.json|\S+)/.test(t)) {
      var mm = t.match(/^(?:打开|看看|看一下)?\s*(\S+\.(json|jsonl|md|py))/i);
      if (mm) return { kind: "query_cat", path: mm[1] };
    }
    if (/^(tree|递归|tree$)/i.test(low)) return { kind: "query_tree" };
    if (/事件|events|日志|event\s*log/.test(t)) return { kind: "query_cat", path: ".novel-workflow/events.jsonl" };
    if (/工作流|workflow\.json/.test(t)) return { kind: "query_cat", path: "workflow.json" };
    if (/发布凭证|凭证|receipt/.test(t)) {
      var mch = t.match(/第\s*(\d+)\s*章/);
      return { kind: "query_cat", path: "releases/chapter-" + (mch ? mch[1] : "1") + ".json" };
    }

    if (/^下一步$|^接下来|^继续$|^接着干|^下一棒/.test(t)) return { kind: "do_next" };

    if (/开始|创建|立项|新书|开一本|建项目|^init$|建一本/.test(t)) return { kind: "act_init" };
    if (/(录|写|记|加)(入|一下)?(创意|点子|idea)|^idea$/.test(t)) return { kind: "act_idea" };
    if (/概念评审|评审概念|concept/.test(t)) return { kind: "act_concept_review" };
    if (/(写|录入|加|录)(圣经|世界观|设定)|bible/.test(t)) return { kind: "act_bible" };
    if (/(写|做|加)(master|级|第一级)大纲|写大纲/.test(t)) return { kind: "act_outline_master" };
    if (/(写|做|加)volume.*大纲|写卷纲/.test(t)) return { kind: "act_outline_volume" };
    if (/(写|做|加)chapter.*大纲|写章纲/.test(t)) return { kind: "act_outline_chapter" };
    if (/(写|做|补|修).*(大纲|outline)/.test(t)) return { kind: "act_outline_repair" };
    if (/锁定大纲|^lock$|outline-lock|大纲锁定/.test(t)) return { kind: "act_outline_lock" };
    if (/(签发|领|开)(第\s*(\d+)\s*章|第\s*(\d+)\s*回)|issue/.test(t)) {
      var mn = t.match(/第\s*(\d+)\s*[章节回]/);
      return { kind: "act_issue", n: mn ? parseInt(mn[1], 10) : 1 };
    }
    if (/(写|交|提)(第\s*(\d+)\s*章)?(草稿|候选稿|正文)|draft/.test(t)) {
      var mn2 = t.match(/第\s*(\d+)\s*章/);
      return { kind: "act_draft", n: mn2 ? parseInt(mn2[1], 10) : 1 };
    }
    if (/(评|跑|过)(第\s*(\d+)\s*章)?(五门|评审|门禁|reviews?)/.test(t)) {
      var mn3 = t.match(/第\s*(\d+)\s*章/);
      return { kind: "act_reviews_all", n: mn3 ? parseInt(mn3[1], 10) : 1 };
    }
    if (/(评|跑)(editor|editor 门)/.test(t)) return { kind: "act_review", gate: "editor" };
    if (/(评|跑)(reader|reader 门)/.test(t)) return { kind: "act_review", gate: "reader" };
    if (/(评|跑)(military|军事)/.test(t)) return { kind: "act_review", gate: "military" };
    if (/(评|跑)(science|科学|科幻)/.test(t)) return { kind: "act_review", gate: "science" };
    if (/(评|跑)(author|作者)/.test(t)) return { kind: "act_review", gate: "author" };
    if (/(发布|release|上架|发出去)(第\s*(\d+)\s*章)?/.test(t)) {
      var mn4 = t.match(/第\s*(\d+)\s*章/);
      return { kind: "act_release", n: mn4 ? parseInt(mn4[1], 10) : 1 };
    }

    return null;
  }

  /* ============================================================
   * Plan builders (v3: tape-derived, n=1 constraint, needsCustom only
   * for genuinely user-supplied parameters)
   * ============================================================ */
  function planFor(m) {
    switch (m.kind) {
      case "act_init": return {
        kind: "custom",
        intent: "创建新项目（init）",
        explain: "立项会建一个 demo/ 目录并写入 workflow.json，定义书名、阶段、角色。回放不支持自定义书名（请切到 LIVE 引擎）。",
        cmdDisplay: 'novel-workflow init demo --title "<待你填>"',
        argv: ["init", "demo", "--title", "<TITLE>"],
        needsCustom: true, customField: "title", intake: false,
        askFor: { field: "title", question: "书名叫什么？" },
        resultSummary: function (ok, r) {
          return ok ? "项目已立项，workflow.json 落盘。" : ("执行失败：" + ((r && r.err || "").split("\n")[0] || "exit " + (r && r.code)));
        }
      };
      case "act_idea": return {
        kind: "custom",
        intent: "录入创意（idea）",
        explain: "需要 15 字段 intake 完整才能过概念评审；这里用仓库自带的示例访谈填底，summary 用你说的。回放未录制自定义 summary 的 idea（请切 LIVE）。",
        cmdDisplay: 'novel-workflow idea demo --summary "<待你填>" --interview <15 字段示例>',
        argv: ["idea", "demo", "--summary", "<SUMMARY>", "--interview", "<INTAKE>"],
        needsCustom: true, customField: "summary", intake: true,
        askFor: { field: "summary", question: "用一句话描述这本书的创意（intake 我用示例数据）" },
        resultSummary: function (ok) { return ok ? "创意已录，idea.json 写入 demo/idea/。" : "录入失败（看下方完整输出）。"; }
      };
      case "act_concept_review": return tapeCmd("concept-review", "跑概念评审（concept-review PASS）", "前提：intake 完整且 idea 已录。评审材料与评审人用引导预置的版本。");
      case "act_bible": return tapeCmd("bible", "写故事圣经（bible）", "圣经文件用引导预置的版本，世界观/设定一应俱全。");
      case "act_outline_master": return tapeSeq(["outline-write-master", "outline-review-master"], "写 master 级大纲并通过评审", "连续两步：先写大纲文件，再以 PASS 跑评审。");
      case "act_outline_volume": return tapeSeq(["outline-write-volume", "outline-review-volume"], "写 volume 级大纲并通过评审", "连续两步：先写大纲，再评审。");
      case "act_outline_chapter": return tapeSeq(["outline-write-chapter", "outline-review-chapter"], "写 chapter 级大纲并通过评审", "连续两步：先写大纲，再评审。");
      case "act_outline_repair": return {
        kind: "custom",
        intent: "修大纲（outline-repair）",
        explain: "把当前 FAIL 的大纲级别走 repair 流程。该命令未在引导录制中，回放不可用（请切 LIVE）。",
        cmdDisplay: "novel-workflow outline-repair demo master",
        argv: ["outline-repair", "demo", "master"],
        resultSummary: function (ok) { return ok ? "大纲修复完成，重新走 review。" : "修复失败，看输出。"; }
      };
      case "act_outline_lock": return tapeCmd("outline-lock", "锁定大纲（outline-lock）", "前提：master/volume/chapter 三级全部 PASS。锁定后才能签发章节。");
      case "act_issue": return onlyCh1(m.n, tapeCmd("issue", "签发第 " + m.n + " 章（issue）", "前提：大纲已锁定。第 " + m.n + " 章用引导预置的标题/目标。"));
      case "act_draft": return onlyCh1(m.n, tapeCmd("draft", "写第 " + m.n + " 章候选稿（draft）", "写 prewrite + draft 候选稿，author 取自引导预置的 author:mira。"));
      case "act_reviews_all": return onlyCh1(m.n, tapeSeq(["review-editor", "review-reader", "review-military", "review-science"], "连续跑第 " + m.n + " 章的五门评审", "editor → reader → military(SKIP) → science(SKIP) 四步，author 门候选稿自审默认满足。"));
      case "act_review": return tapeCmd("review-" + m.gate, m.gate + " 门评审（" + (m.gate === "military" || m.gate === "science" ? "SKIP_WITH_REASON" : "PASS") + "）", "默认评审材料 / 评审人用引导预置。military / science 这两门默认 SKIP_WITH_REASON（因为示例小说无军事/科幻内容）。");
      case "act_release": return onlyCh1(m.n, tapeCmd("release", "显式发布第 " + m.n + " 章（release）", "前提：五门全 PASS（或 SKIP_WITH_REASON），状态 READY_TO_RELEASE。release 不可逆，会落发布凭证。"));
      case "do_next": return null;
    }
    return null;
  }
  function onlyCh1(n, plan) {
    if (n === 1) return plan;
    return {
      kind: "custom",
      intent: "暂不支持第 " + n + + " 章",
      explain: "演示项目目前只备了第 1 章的完整引导录制（issue / draft / 五门评审 / release）。第 " + n + " 章需要 LIVE 引擎 + 真实材料，或先把第 1 章跑完，再签发下一章。",
      cmdDisplay: "novel-workflow <第 " + n + " 章尚未准备>",
      argv: [],
      resultSummary: function () { return "未执行：演示项目当前只备第 1 章。"; }
    };
  }

  /* ============================================================
   * Query dispatch (v3: status uses readState; replay-aware friendly
   * messages for commands not in the recording)
   * ============================================================ */
  function runQuery(m) {
    var NWB = window.NWB;
    var engine = NWB.getMode();
    if (engine === "booting") { assistantMsg("引擎还在启动中，等它到 LIVE 或 REPLAY 再查。"); return; }
    var typing;
    switch (m.kind) {
      case "query_status":
        refreshStateSummary("—— 当前状态 ——", "");
        return;
      case "query_chapter":
        if (m.n !== 1) { assistantMsg("演示项目目前只备了第 1 章的实时录制；第 " + m.n + " 章状态可切 LIVE 后查，或等流水线跑完自动推进。"); return; }
        NWB.runLive({}, ["status", "demo", "--chapter", "1", "--human"], false).then(function (r) {
          if (r.code === 0) showLastOutput("novel-workflow status demo --chapter 1 --human");
          else assistantMsg("查询失败：" + ((r.err || "").split("\n")[0] || "exit " + r.code));
        });
        return;
      case "query_chapters":
        refreshStateSummary("—— 章节列表 ——", "");
        return;
      case "query_roles":
        if (engine === "replay") { assistantMsg("回放未录制 roles 命令（白话模式只跑录制过的引导命令）。切到 LIVE 引擎后可查五角色独立性。"); return; }
        typing = showTyping();
        NWB.runSmart({}, ["roles", "demo", "--human"], false).then(function (r) {
          if (typing && typing.parentNode) typing.parentNode.removeChild(typing);
          if (r.code === 0) showLastOutput("novel-workflow roles demo --human");
          else assistantMsg("roles 命令失败：" + ((r.err || "").split("\n")[0] || "exit " + r.code));
        });
        return;
      case "query_security":
        if (engine === "replay") { assistantMsg("回放未录制 security check；切 LIVE 引擎后可跑安全扫描。"); return; }
        typing = showTyping();
        NWB.runSmart({}, ["check", "demo", "--security", "--human"], false).then(function (r) {
          if (typing && typing.parentNode) typing.parentNode.removeChild(typing);
          if (r.code === 0) showLastOutput("novel-workflow check demo --security --human");
          else assistantMsg("安全检查失败：" + ((r.err || "").split("\n")[0] || "exit " + r.code));
        });
        return;
      case "query_check":
        if (engine === "replay") { assistantMsg("回放未录制 check all；切 LIVE 引擎后可跑校验。"); return; }
        typing = showTyping();
        NWB.runSmart({}, ["check", "demo", "--human"], false).then(function (r) {
          if (typing && typing.parentNode) typing.parentNode.removeChild(typing);
          if (r.code === 0) showLastOutput("novel-workflow check demo --human");
          else assistantMsg("check 命令失败：" + ((r.err || "").split("\n")[0] || "exit " + r.code));
        });
        return;
      case "query_ls":
        typing = showTyping();
        NWB.runSmart({}, ["__ls__", "demo"], false).then(function (r) {
          if (typing && typing.parentNode) typing.parentNode.removeChild(typing);
          if (r.out) assistantHtml('<pre class="lastcmd-out">' + ansi(r.out) + "</pre>");
          else assistantMsg("(空)");
        });
        return;
      case "query_tree":
        typing = showTyping();
        NWB.runSmart({}, ["__tree__", "demo"], false).then(function (r) {
          if (typing && typing.parentNode) typing.parentNode.removeChild(typing);
          if (r.out) assistantHtml('<pre class="lastcmd-out">' + ansi(r.out) + "</pre>");
          else assistantMsg("(空)");
        });
        return;
      case "query_cat":
        typing = showTyping();
        NWB.runSmart({}, ["__cat__", "demo/" + m.path], false).then(function (r) {
          if (typing && typing.parentNode) typing.parentNode.removeChild(typing);
          if (r.code === 0) showLastOutput("cat demo/" + m.path);
          else assistantMsg("cat demo/" + m.path + " 失败：" + ((r.err || "").split("\n")[0] || "exit " + r.code));
        });
        return;
    }
  }

  /* ============================================================
   * Pending confirmation handlers (v3: null-safe cancel)
   * ============================================================ */
  function handlePendingRun() {
    if (!pending || pending.kind !== "plan") return false;
    var plan = pending.plan, planDiv = pending.div;
    pending = null;
    planDiv.querySelector(".plan-card").classList.add("running");
    planDiv.querySelectorAll("button").forEach(function (b) { b.disabled = true; });
    executePlan(plan, planDiv);
    return true;
  }
  function handlePendingCancel() {
    if (!pending || pending.kind !== "plan") return false;
    var d = pending.div;
    pending = null;
    if (d) {
      d.querySelector(".plan-card").classList.add("cancelled");
      d.querySelectorAll("button").forEach(function (b) { b.disabled = true; });
    }
    assistantMsg("已取消。");
    return true;
  }

  /* ============================================================
   * "next step" driver: pick the next undone guide step
   * ============================================================ */
  function doNextStep() {
    var NWB = window.NWB;
    var st = NWB.readState();
    if (!st || !st.projectExists) {
      assistantMsg("项目还没立项，说「开始一本新书」或「创建项目」开始吧。");
      return;
    }
    var p = st.project;
    var order = [
      { cond: !p.bible || p.bible === "PENDING", build: function () { return tapeCmd("bible", "写故事圣经（bible）", "圣经文件用引导预置的版本。"); } },
      { cond: p.outline.master === "PENDING", build: function () { return tapeSeq(["outline-write-master", "outline-review-master"], "写 master 级大纲并通过评审", "连续两步：先写再评。"); } },
      { cond: p.outline.master === "FAIL" || p.outline.volume === "FAIL" || p.outline.chapter === "FAIL", build: function () { return planFor({ kind: "act_outline_repair" }); } },
      { cond: p.outline.volume !== "PASS" && p.outline.volume !== "FAIL", build: function () { return tapeSeq(["outline-write-volume", "outline-review-volume"], "写 volume 级大纲并通过评审", "连续两步：先写再评。"); } },
      { cond: p.outline.chapter !== "PASS" && p.outline.chapter !== "FAIL", build: function () { return tapeSeq(["outline-write-chapter", "outline-review-chapter"], "写 chapter 级大纲并通过评审", "连续两步：先写再评。"); } },
      { cond: !p.outlineLocked, build: function () { return tapeCmd("outline-lock", "锁定大纲（outline-lock）", "前提：三级全部 PASS。"); } }
    ];
    if (st.chapters.length > 0) {
      var last = st.chapters[st.chapters.length - 1];
      order.push({ cond: last.status === "ISSUED" || last.status === "BLOCKED", build: function () { return onlyCh1(last.chapter, tapeCmd("draft", "写第 " + last.chapter + " 章候选稿（draft）", "author 取自引导预置。")); } });
      order.push({ cond: last.status === "IN_REVIEW", build: function () { return onlyCh1(last.chapter, tapeSeq(["review-editor", "review-reader", "review-military", "review-science"], "连续跑第 " + last.chapter + " 章的五门评审", "editor → reader → military(SKIP) → science(SKIP)。")); } });
      order.push({ cond: last.status === "READY_TO_RELEASE", build: function () { return onlyCh1(last.chapter, tapeCmd("release", "显式发布第 " + last.chapter + " 章（release）", "五门全 PASS 后可发布。")); } });
    } else {
      order.push({ cond: true, build: function () { return onlyCh1(1, tapeCmd("issue", "签发第 1 章（issue）", "前提：大纲已锁定。")); } });
    }
    for (var i = 0; i < order.length; i++) {
      if (order[i].cond) {
        var plan = order[i].build();
        if (!plan || plan.kind === "_missing") continue;
        assistantHtml("根据当前状态，下一步建议：");
        var planDiv = planCard(plan);
        pending = { kind: "plan", plan: plan, div: planDiv };
        return;
      }
    }
    assistantMsg("流水线全跑完了。可以「再签发下一章」或「重置」从新来过。");
  }

  /* ============================================================
   * Main submit handler (v4: LLM first, rule engine as fallback)
   * ============================================================ */
  var llmHistory = [];   // bounded LLM context (max 6 turns)
  function llmPushHistory(role, text) {
    llmHistory.push({ role: role, text: text });
    while (llmHistory.length > 12) llmHistory.shift();
  }
  function llmTurnContext() { return llmHistory.slice(); }

  function dispatchLLMResult(r, userText) {
    if (r.kind === "plan") {
      llmPushHistory("user", userText);
      llmPushHistory("assistant", "[plan] " + (r.intent || r.plan.intent));
      var d = planCard(r.plan);
      pending = { kind: "plan", plan: r.plan, div: d };
      return;
    }
    if (r.kind === "ask") {
      llmPushHistory("user", userText);
      llmPushHistory("assistant", "[ask] " + (r.reply || ""));
      if (r.reply) assistantMsg(r.reply);
      var field = r.slot.field;
      var question = r.slot.question || ("请填 " + field);
      slotCard(question, function (value) {
        userMsg(value);
        // Re-call LLM with combined context so it can complete the plan.
        var combined = userText + "\n\n[补充] " + value;
        var typing = showTyping();
        window.NWL.tryLLM(combined, llmTurnContext()).then(function (rr) {
          if (typing && typing.parentNode) typing.parentNode.removeChild(typing);
          if (rr.kind === "fallback") {
            assistantHtml('<i>LLM 暂时不可用（' + esc(rr.reason || "") + '），已用规则引擎兜底。请直接说关键参数。</i>');
            runRuleEngine(userText + " " + value);
          } else {
            dispatchLLMResult(rr, combined);
          }
        });
      });
      return;
    }
    if (r.kind === "answer") {
      llmPushHistory("user", userText);
      llmPushHistory("assistant", r.reply || "");
      assistantMsg(r.reply || "");
      return;
    }
    if (r.kind === "out_of_scope") {
      llmPushHistory("user", userText);
      llmPushHistory("assistant", "[out_of_scope] " + (r.reply || ""));
      assistantMsg(r.reply || "该操作不在能力范围。");
      return;
    }
    runRuleEngine(userText);
  }

  function runRuleEngine(text) {
    var m = match(text);
    if (!m) {
      assistantHtml('没听懂。试试这些：' +
        '<div class="hint-grid">' +
        '<button class="chip" data-q="现在到哪了">现在到哪了？</button>' +
        '<button class="chip" data-q="下一步">下一步</button>' +
        '<button class="chip" data-q="开始一本新书">开始一本新书</button>' +
        '<button class="chip" data-q="签发第 1 章">签发第 1 章</button>' +
        '<button class="chip" data-q="写第 1 章草稿">写第 1 章草稿</button>' +
        '<button class="chip" data-q="发布第 1 章">发布第 1 章</button>' +
        '<button class="chip" data-q="help">help</button>' +
        '</div>');
      chatScroll.querySelectorAll(".chip").forEach(function (c) {
        c.addEventListener("click", function () { chatInput.value = c.getAttribute("data-q"); handleChatSubmit(); });
      });
      return;
    }

    if (m.kind === "_pending_run") { handlePendingRun(); return; }
    if (m.kind === "_pending_cancel") { handlePendingCancel(); return; }

    if (m.kind === "help") {
      assistantHtml('<div class="cap-list">' +
        '<b>我能做什么（全部映射到真实的 novel-workflow 命令）：</b>' +
        '<ul>' +
        '<li><b>查</b>：现在到哪了 / 第 N 章状态 / 角色 / 章节列表 / 安全检查 / 看文件 / 看 workflow.json / 看 events.jsonl / 看发布凭证</li>' +
        '<li><b>写</b>：创建项目 · 录创意 · 概念评审 · 写圣经 · 写大纲（master/volume/chapter）· 修大纲 · 锁定大纲 · 签发第 N 章 · 写第 N 章草稿 · 跑五门评审 · 发布第 N 章</li>' +
        '<li><b>控</b>：下一步（自动判断流水线该做哪一步）· 重置</li>' +
        '<li>所有<em>写操作</em>都会先给你看「将要执行的真实命令」，点 [执行] 才跑；点 [取消] 不动</li>' +
        '<li>缺参数时会反问你（比如「开始一本新书」会问书名）</li>' +
        '<li>回放模式只跑录制过的引导命令；自定义书名/创意的 plan 与 roles/security/check 需要 LIVE 引擎</li>' +
        '</ul></div>');
      return;
    }
    if (m.kind === "reset") {
      var plan = {
        kind: "reset",
        intent: "重置项目（reset）",
        explain: "会清空 demo/ 目录，已签发/已发布的章节、发布凭证、所有事件流全部丢失。不可撤销。",
        cmdDisplay: "rm -rf demo/   (via nw_rm)",
        argv: ["__reset__"],
        resultSummary: function (ok) { return ok ? "项目已清空。" : "重置失败。"; }
      };
      var d = planCard(plan);
      pending = { kind: "plan", plan: plan, div: d };
      return;
    }
    if (m.kind === "do_next") { doNextStep(); return; }

    if (m.kind.indexOf("query_") === 0) { runQuery(m); return; }

    var plan = planFor(m);
    if (!plan) { assistantMsg("这个动作没找到对应计划。"); return; }
    if (plan.kind === "_missing") { assistantMsg(plan.intent + "：" + plan.explain); return; }
    if (plan.askFor) {
      var f = plan.askFor.field;
      slotCard(plan.askFor.question, function (value) {
        if (f === "title") plan.argv[plan.argv.length - 1] = value;
        if (f === "summary") {
          var i = plan.argv.indexOf("--summary");
          plan.argv[i + 1] = value;
        }
        plan.cmdDisplay = plan.cmdDisplay.replace("<待你填>", value);
        userMsg(value);
        assistantMsg("好的——下面是要执行的命令：");
        var d = planCard(plan);
        pending = { kind: "plan", plan: plan, div: d };
      });
      return;
    }
    var d = planCard(plan);
    pending = { kind: "plan", plan: plan, div: d };
  }

  function handleChatSubmit() {
    var text = chatInput.value.trim();
    if (!text) return;
    chatInput.value = "";
    userMsg(text);

    // Pending confirmation short-circuit (do not even attempt LLM).
    if (pending && pending.kind === "plan") {
      var low = text.toLowerCase();
      if (/^(确认|好|可以|执行|嗯|ok|yes|y|✓)$/i.test(low)) { handlePendingRun(); return; }
      if (/^(取消|算了|不|no|n|✗|×)$/i.test(low)) { handlePendingCancel(); return; }
    }

    // v4: try LLM first if enabled + key set, rule engine as silent fallback.
    if (window.NWL && window.NWL.isEnabled() && window.NWL.getApiKey()) {
      var typing = showTyping();
      window.NWL.tryLLM(text, llmTurnContext()).then(function (r) {
        if (typing && typing.parentNode) typing.parentNode.removeChild(typing);
        if (r.kind === "fallback") {
          runRuleEngine(text);    // silent — no banner noise
        } else {
          dispatchLLMResult(r, text);
        }
      });
      return;
    }

    runRuleEngine(text);
  }

  chatSend.addEventListener("click", handleChatSubmit);
  chatInput.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter") { ev.preventDefault(); handleChatSubmit(); }
  });
  chatPanel.addEventListener("click", function (ev) {
    if (ev.target.closest("input, button, a, .plan-card, .slot-card, .chip")) return;
    chatInput.focus();
  });

  window.NWC = { setMode: setMode, refresh: refreshStateSummary };

  /* v4: wire up the LLM settings popover + badge (llm.js's IIFE has
   * already registered window.NWL by the time chat.js runs, since
   * llm.js is loaded before chat.js). */
  if (window.NWL && window.NWL.init) window.NWL.init();
})();
