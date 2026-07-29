/* novel-workflow live runner — LLM (BYOK) layer for the white (plain-language) mode. (v4)
 *
 * v4: Web端 BYOK · 确认流不变
 *   - User-supplied OpenAI-compatible API key + base URL + model, persisted
 *     in localStorage. Browser direct call to /chat/completions.
 *   - LLM only emits a JSON plan. Every write still goes through the same
 *     plan-card confirmation flow as the rule engine; LLM never touches
 *     the filesystem. The security model is unchanged.
 *   - Falls back to the rule engine on: no key set, network failure, CORS
 *     rejection, parse failure, timeout, or explicit out_of_scope.
 *   - Exposes NWL (and settings UI helpers). The chat engine calls
 *     NWL.tryLLM(text, history) before falling through to its rule-based
 *     matcher, so the rule engine remains the safety net.
 */
(function () {
  "use strict";

  var STORAGE_PREFIX = "nwa.llm.";
  var DEFAULT_BASE = "https://api.openai.com/v1";
  var DEFAULT_MODEL = "gpt-4o-mini";
  var REQUEST_TIMEOUT_MS = 30000;
  var MAX_HISTORY_TURNS = 6;            // 3 user + 3 assistant messages
  var MAX_OUTPUT_TOKENS = 1024;

  /* ============================================================
   * Settings (localStorage-backed)
   * ============================================================ */
  function readSetting(k, fallback) {
    try {
      var v = localStorage.getItem(STORAGE_PREFIX + k);
      return v == null ? fallback : v;
    } catch (e) { return fallback; }
  }
  function writeSetting(k, v) {
    try { localStorage.setItem(STORAGE_PREFIX + k, v); } catch (e) { /* quota? private mode? — ignore */ }
  }
  function clearSettings() {
    try {
      Object.keys(localStorage).forEach(function (k) {
        if (k.indexOf(STORAGE_PREFIX) === 0) localStorage.removeItem(k);
      });
    } catch (e) {}
  }
  function isEnabled()   { return readSetting("enabled",   "0") === "1"; }
  function getApiKey()   { return readSetting("apiKey",   ""); }
  function getBaseUrl()  {
    var b = readSetting("baseUrl", DEFAULT_BASE);
    return b.replace(/\/+$/, "");
  }
  function getModel()    { return readSetting("model",   DEFAULT_MODEL); }
  function isProviderOpenAICompat() {
    // OpenAI-compatible: all providers we support (OpenAI / DeepSeek /
    // Moonshot / OpenRouter / Zhipu / 智谱 / 自部署 vLLM / OpenPipe etc.)
    // share the same /chat/completions schema. Anthropic is the odd one
    // out and is intentionally out of scope for v4.
    return true;
  }

  /* ============================================================
   * System prompt — static part (cached after first build)
   * ============================================================ */
  var STATIC_SYSTEM_PROMPT = [
    "你是 novel-workflow 网页实跑器的「白话模式 AI 助手」。你的职责是把用户的自然语言翻译成结构化的执行计划，让用户确认后再交由真实的 novel-workflow CLI 在浏览器内 WASM 执行。",
    "",
    "## 边界（铁律）",
    "1. 你只产出计划，不直接执行。任何写操作必须经用户在 plan card 上点 [执行] 才跑。",
    "2. 执行命令必须是真实的 `novel-workflow <sub> <args>` argv，能被 cli.py argparse 接受。",
    "3. 多步操作拆成 seq 数组，按顺序串行执行；任一步失败后续步骤自动停。",
    "4. 查询类不要走 plan——直接给 reply 文字回答。",
    "5. 不在能力范围的事老实说 out_of_scope，不要硬编。",
    "",
    "## 项目背景",
    "novel-workflow 是一本小说的「状态机驱动」写作流水线（realwindjpn/novel-agent-workflow）。项目根目录存 workflow.json（项目状态）和 .novel-workflow/（章节状态 + 事件流 + 发布凭证）。状态机硬门禁：每一步只能从前一阶段的合法状态进入，CLI 会拒绝非法跃迁。",
    "",
    "## CLI 命令目录（OpenAI 兼容，凭此选择正确的 argv）",
    "### 写命令（必须 plan card 确认）",
    "- `init <path> --title <TITLE>` — 立项（必填 title）",
    "- `idea <path> --summary <S> --interview <JSON>` — 录创意（interview 是 15 字段 JSON intake）",
    "- `concept-review <path> <PASS|FAIL> --artifact <PATH> --reviewer <NAME>` — 概念评审",
    "- `bible <path> --artifact <PATH>` — 写圣经",
    "- `outline-write <path> <master|volume|chapter> --artifact <PATH>` — 写大纲",
    "- `outline-review <path> <level> <PASS|FAIL> --artifact <PATH> --reviewer <NAME>` — 大纲评审",
    "- `outline-repair <path> <level> --artifact <P> <verdict> --review-artifact <P> --reviewer <NAME>` — 修大纲",
    "- `outline-lock <path>` — 锁定大纲",
    "- `issue <path> <chapter> --title <T> --goal <G>` — 签发章节",
    "- `draft <path> <chapter> --prewrite <P> --artifact <P> --author <NAME>` — 写候选稿",
    "- `review <path> <chapter> <gate> <PASS|FAIL|SKIP_WITH_REASON> --artifact <P> --reviewer <NAME> [--reason <R>]` — 五门评审",
    "- `release <path> <chapter>` — 发布（不可逆）",
    "",
    "### 读命令（不需要 plan card）",
    "- `status <path> [--chapter N] [--human]` — 项目/章节状态",
    "- `check <path> [--security] [--human]` — 安全扫描 / 总校验",
    "- `roles <path> [--human]` — 五角色独立性",
    "- `chapters <path> [--human]` — 章节列表",
    "- `intake-check <path> [--interview J] [--human]` — intake 校验",
    "- `concept-repair <path> [--summary S] [--interview J] <verdict> --artifact <P> --reviewer <N>` — 修概念",
    "- `repair <path> <chapter> --artifact <P> --affected <GATE...>` — 修章节",
    "",
    "### model 子命令（model routing，可选）",
    "- `model init-config [path] [--force]` — 写 model_routing.toml + .env.example",
    "- `model smoke [--config] [--role R] [--no-skip-missing-env]` — 烟测",
    "- `model route-plan --genre <G> [--risk R] [--no-skip-missing-env]`",
    "- `model budget --genre <G> [--risk R] [--revision-rounds N] [--input-tokens N] [--output-tokens N]`",
    "- `model model-ledger --genre <G> [--risk R] [-o PATH] [--no-skip-missing-env]`",
    "",
    "## 状态机阶段",
    "IDEA → (concept PASS) → (bible WRITTEN) → (outline master/volume/chapter 全部 PASS) → (outline_locked_at) → chapter 生命周期:",
    "  ISSUED → DRAFTED → IN_REVIEW → READY_TO_RELEASE → RELEASED",
    "  五门 author/editor/reader/military/science：author 自审默认满足；其余四门必须全 PASS 或 SKIP_WITH_REASON 才能 READY_TO_RELEASE。",
    "  BLOCKED = ISSUED 状态回退（需 repair）。",
    "",
    "## 回复格式（严格单行 JSON，无 markdown 包裹）",
    "A) 回答/查询：{\"kind\":\"answer\",\"reply\":\"《测试书》处于 OUTLINE_LOCKED 阶段，第 1 章 ISSUED 待写草稿。\"}",
    "B) 单步写：{\"kind\":\"plan\",\"intent\":\"...\",\"explain\":\"...\",\"cmdDisplay\":\"novel-workflow issue demo 2 --title X --goal Y\",\"argv\":[\"issue\",\"demo\",\"2\",\"--title\",\"X\",\"--goal\",\"Y\"]}",
    "   可选 needsCustom=true, customField=\"<占位符名>\", askFor={\"field\":\"<占位符>\",\"question\":\"...\"} — 当某个 argv 值需要用户填（如书名），用 <FIELD_NAME> 占位后让 plan 显示待填，由前端补 slot 卡片。",
    "C) 多步：{\"kind\":\"plan\",\"intent\":\"...\",\"explain\":\"...\",\"seq\":[{\"argv\":[...],\"setup\":{}}],\"cmdDisplay\":\"...\"}",
    "D) 反问：{\"kind\":\"ask\",\"reply\":\"新书要叫什么名字？\",\"slot\":{\"field\":\"<TITLE>\",\"question\":\"书名\"}}",
    "E) 不在能力范围：{\"kind\":\"out_of_scope\",\"reply\":\"不能改已发布章节；要重来请先重置。\"}",
    "",
    "## argv 占位符约定",
    "用 <NAME> 形式标需要前端替换或用户填的占位（如 <TITLE>、<SUMMARY>、<AUTHOR>、<PREWRITE>、<ARTIFACT>）。",
    "NEVER 凭空写不存在的子命令或参数。"
  ].join("\n");

  /* ============================================================
   * Per-turn prompt: inject current state + recent history
   * ============================================================ */
  function buildMessages(userText, history) {
    var stateBlock = buildStateBlock();
    var historyBlock = buildHistoryBlock(history || []);
    var sysParts = [STATIC_SYSTEM_PROMPT];
    if (stateBlock) sysParts.push("\n\n## 当前项目状态（nwb.readState() 真实返回，每轮注入）\n" + stateBlock);
    if (historyBlock) sysParts.push("\n\n## 最近对话（" + history.length + " 轮）\n" + historyBlock);
    sysParts.push("\n\n## 用户这一轮说：\n" + userText + "\n\n现在按格式返回单行 JSON：");
    return [{ role: "system", content: sysParts.join("") }, { role: "user", content: userText }];
  }
  function buildStateBlock() {
    var NWB = window.NWB;
    if (!NWB) return "";
    var st;
    try { st = NWB.readState(); } catch (e) { return ""; }
    if (!st) return "";
    try { return JSON.stringify(st, null, 2); } catch (e) { return ""; }
  }
  function buildHistoryBlock(history) {
    if (!history.length) return "";
    return history.map(function (h) { return "[" + h.role + "] " + h.text; }).join("\n");
  }

  /* ============================================================
   * LLM call: fetch POST to <base>/chat/completions
   * ============================================================ */
  function callLLM(messages, signal) {
    var key = getApiKey();
    if (!key) return Promise.reject(new Error("未设置 API key"));
    var base = getBaseUrl();
    var model = getModel();
    var url = base + "/chat/completions";
    var body = {
      model: model,
      messages: messages,
      temperature: 0.2,
      max_tokens: MAX_OUTPUT_TOKENS,
      stream: false
    };
    // OpenAI strict mode — most OpenAI-compat providers also support it; if not, the model still returns JSON-shaped text per system prompt.
    if (/^https?:\/\/(api\.openai\.com|api\.deepseek\.com|api\.moonshot\.cn|openrouter\.api\.)/.test(base)) {
      body.response_format = { type: "json_object" };
    }
    return fetch(url, {
      method: "POST",
      signal: signal,
      headers: { "Content-Type": "application/json", "Authorization": "Bearer " + key },
      body: JSON.stringify(body)
    }).then(function (resp) {
      if (!resp.ok) {
        return resp.text().then(function (t) {
          throw new Error("HTTP " + resp.status + " " + resp.statusText + " · " + t.slice(0, 200));
        });
      }
      return resp.json();
    }).then(function (j) {
      var choice = j && j.choices && j.choices[0];
      var msg = choice && choice.message;
      var txt = msg && (msg.content || msg.text || "");
      if (!txt) throw new Error("LLM 返回为空");
      return extractJson(txt);
    });
  }
  function extractJson(text) {
    // Defensive: strip code fences, then find first { and matching }.
    var s = text.replace(/^\s*```(?:json)?\s*/i, "").replace(/```\s*$/, "").trim();
    var first = s.indexOf("{");
    if (first < 0) throw new Error("LLM 返回无 JSON: " + s.slice(0, 80));
    var depth = 0, inStr = false, esc = false;
    for (var i = first; i < s.length; i++) {
      var c = s.charAt(i);
      if (esc) { esc = false; continue; }
      if (c === "\\") { esc = true; continue; }
      if (c === '"') { inStr = !inStr; continue; }
      if (inStr) continue;
      if (c === "{") depth++;
      else if (c === "}") { depth--; if (depth === 0) return JSON.parse(s.slice(first, i + 1)); }
    }
    throw new Error("LLM JSON 未闭合");
  }

  /* ============================================================
   * Plan shape validation & normalization
   *   Internal plan shapes (what planCard / executePlan / NWB.runSmart / runSeq expect):
   *     { kind: "tape", intent, explain, cmdDisplay, argv, setup, ... }  (from rule engine)
   *     { kind: "seq", intent, explain, cmdDisplay, seq: [{argv, setup}], resultSummary }
   *     { kind: "custom", intent, explain, cmdDisplay, argv, setup, needsCustom, askFor, ... }
   *     { kind: "reset", intent, explain, cmdDisplay, argv: ["__reset__"] }
   *   LLM output is mapped to these shapes.
   * ============================================================ */
  function normalizePlan(llm) {
    if (llm.kind !== "plan") return null;
    var intent = String(llm.intent || "").trim();
    var explain = String(llm.explain || "").trim();
    var cmdDisplay = String(llm.cmdDisplay || "").trim();
    if (!intent) intent = "执行计划";
    if (!explain) explain = "LLM 生成的计划";
    if (!cmdDisplay) {
      if (Array.isArray(llm.argv)) cmdDisplay = "novel-workflow " + llm.argv.join(" ");
      else if (Array.isArray(llm.seq)) {
        cmdDisplay = llm.seq.map(function (s) { return "novel-workflow " + (s.argv || []).join(" "); }).join("\n          &&   ");
      }
    }
    if (Array.isArray(llm.seq) && llm.seq.length > 0) {
      var seq = llm.seq.map(function (s) {
        return { argv: Array.isArray(s.argv) ? s.argv.slice() : [], setup: s.setup || {} };
      });
      return {
        kind: "seq",
        intent: intent, explain: explain, cmdDisplay: cmdDisplay, seq: seq,
        source: "llm",
        resultSummary: function (ok, r) {
          if (ok) return "全部子步骤已执行（" + seq.length + " 步）。";
          return "中间某步失败：" + ((r && r.err || "").split("\n")[0] || "exit " + (r && r.code));
        }
      };
    }
    if (Array.isArray(llm.argv)) {
      var plan = {
        kind: "custom",
        intent: intent, explain: explain, cmdDisplay: cmdDisplay,
        argv: llm.argv.slice(), setup: llm.setup || {},
        source: "llm",
        resultSummary: function (ok, r) {
          return ok ? "已执行。" : ("执行失败：" + ((r && r.err || "").split("\n")[0] || "exit " + (r && r.code)));
        }
      };
      if (llm.needsCustom && llm.askFor && llm.askFor.field) {
        plan.needsCustom = true;
        plan.customField = llm.askFor.field;
        plan.askFor = { field: llm.askFor.field, question: llm.askFor.question || ("请填 " + llm.askFor.field) };
        if (llm.intake) plan.intake = true;
      } else if (llm.intake) {
        plan.intake = true;
      }
      return plan;
    }
    return null;   // invalid — caller falls back
  }

  /* ============================================================
   * Public: tryLLM(text, history) -> Promise<normalizedResult>
   *   Returns one of:
   *     { kind: "plan", plan: {...internal shape...} }
   *     { kind: "ask",  reply, slot: {field, question} }
   *     { kind: "answer", reply }
   *     { kind: "out_of_scope", reply }
   *     { kind: "fallback", reason }   // chat.js should use rule engine
   * ============================================================ */
  function tryLLM(userText, history) {
    if (!isEnabled()) return Promise.resolve({ kind: "fallback", reason: "disabled" });
    if (!getApiKey())  return Promise.resolve({ kind: "fallback", reason: "no-key" });
    if (window.NWB && window.NWB.getMode && window.NWB.getMode() === "booting") {
      return Promise.resolve({ kind: "fallback", reason: "booting" });
    }
    var ac = window.AbortController ? new AbortController() : null;
    var timer = setTimeout(function () { if (ac) ac.abort(); }, REQUEST_TIMEOUT_MS);
    var messages = buildMessages(userText, history || []);
    return callLLM(messages, ac ? ac.signal : undefined)
      .then(function (j) {
        clearTimeout(timer);
        if (!j || !j.kind) return { kind: "fallback", reason: "bad-shape" };
        if (j.kind === "plan") {
          var plan = normalizePlan(j);
          if (!plan) return { kind: "fallback", reason: "bad-plan" };
          return { kind: "plan", plan: plan, intent: j.intent };
        }
        if (j.kind === "ask") {
          if (!j.slot || !j.slot.field) return { kind: "fallback", reason: "bad-ask" };
          return { kind: "ask", reply: j.reply || "", slot: { field: j.slot.field, question: j.slot.question || j.slot.field } };
        }
        if (j.kind === "answer") {
          return { kind: "answer", reply: j.reply || "" };
        }
        if (j.kind === "out_of_scope") {
          return { kind: "out_of_scope", reply: j.reply || "该操作不在能力范围。" };
        }
        return { kind: "fallback", reason: "unknown-kind:" + j.kind };
      })
      .catch(function (err) {
        clearTimeout(timer);
        var msg = (err && err.message) || String(err);
        return { kind: "fallback", reason: "error:" + msg.slice(0, 120) };
      });
  }

  /* ============================================================
   * Test connection: hit /models and return ok / err string
   * ============================================================ */
  function testConnection() {
    var key = getApiKey();
    if (!key) return Promise.resolve({ ok: false, msg: "未设置 API key" });
    var base = getBaseUrl();
    return fetch(base + "/models", {
      method: "GET",
      headers: { "Authorization": "Bearer " + key }
    }).then(function (r) {
      if (r.ok) return { ok: true, msg: "✓ 连接成功（" + r.status + "）" };
      return r.text().then(function (t) {
        return { ok: false, msg: "HTTP " + r.status + " · " + t.slice(0, 120) };
      });
    }).catch(function (e) {
      return { ok: false, msg: "网络/CORS 失败：" + (e && e.message || e) };
    });
  }

  /* ============================================================
   * Settings popover UI
   * ============================================================ */
  function ensureSettingsUI() {
    if (document.getElementById("llm-settings-pop")) return;
    var gear = document.getElementById("llm-gear");
    if (!gear) return;
    var pop = document.createElement("div");
    pop.id = "llm-settings-pop";
    pop.className = "llm-pop";
    pop.setAttribute("role", "dialog");
    pop.setAttribute("aria-label", "LLM 设置");
    pop.hidden = true;
    pop.innerHTML = [
      '<div class="llm-pop-head"><b>白话模式 · LLM 接入</b><span class="llm-pop-sub">BYOK · Key 仅存 localStorage，不上传</span></div>',
      '<label class="llm-row"><span>启用</span><input type="checkbox" id="llm-enabled"></label>',
      '<label class="llm-row"><span>Base URL</span><input type="text" id="llm-base" placeholder="https://api.openai.com/v1" autocomplete="off" spellcheck="false"></label>',
      '<label class="llm-row"><span>Model</span><input type="text" id="llm-model" placeholder="gpt-4o-mini" autocomplete="off" spellcheck="false"></label>',
      '<label class="llm-row"><span>API Key</span><input type="password" id="llm-key" placeholder="sk-..." autocomplete="off" spellcheck="false"></label>',
      '<div class="llm-pop-foot">',
      '  <button class="btn small" id="llm-test">测试连接</button>',
      '  <button class="btn small" id="llm-save">应用</button>',
      '  <button class="btn small" id="llm-clear">清空</button>',
      '  <span class="llm-pop-status" id="llm-status"></span>',
      '</div>'
    ].join("");
    document.body.appendChild(pop);

    function fillForm() {
      document.getElementById("llm-enabled").checked = isEnabled();
      document.getElementById("llm-base").value = getBaseUrl();
      document.getElementById("llm-model").value = getModel();
      document.getElementById("llm-key").value = getApiKey();
      document.getElementById("llm-status").textContent = "";
    }
    function saveForm() {
      writeSetting("enabled", document.getElementById("llm-enabled").checked ? "1" : "0");
      writeSetting("baseUrl", document.getElementById("llm-base").value.trim() || DEFAULT_BASE);
      writeSetting("model",   document.getElementById("llm-model").value.trim() || DEFAULT_MODEL);
      writeSetting("apiKey",  document.getElementById("llm-key").value.trim());
      document.getElementById("llm-status").textContent = "已保存";
      window.dispatchEvent(new CustomEvent("nwa.llm.settings-changed"));
      setTimeout(function () { pop.hidden = true; }, 350);
    }
    function clearAll() {
      clearSettings();
      fillForm();
      document.getElementById("llm-status").textContent = "已清空";
      window.dispatchEvent(new CustomEvent("nwa.llm.settings-changed"));
    }
    function doTest() {
      saveForm();   // test against latest values
      document.getElementById("llm-status").textContent = "测试中…";
      testConnection().then(function (r) {
        document.getElementById("llm-status").textContent = r.msg;
        document.getElementById("llm-status").style.color = r.ok ? "var(--ok)" : "var(--err)";
      });
    }
    function positionPop() {
      var r = gear.getBoundingClientRect();
      pop.style.top  = (r.bottom + 6) + "px";
      pop.style.right = Math.max(8, window.innerWidth - r.right) + "px";
    }
    gear.addEventListener("click", function (ev) {
      ev.stopPropagation();
      if (pop.hidden) { fillForm(); positionPop(); pop.hidden = false; }
      else pop.hidden = true;
    });
    document.addEventListener("click", function (ev) {
      if (pop.hidden) return;
      if (ev.target.closest("#llm-settings-pop, #llm-gear")) return;
      pop.hidden = true;
    });
    document.getElementById("llm-save").addEventListener("click", saveForm);
    document.getElementById("llm-test").addEventListener("click", doTest);
    document.getElementById("llm-clear").addEventListener("click", clearAll);
    window.addEventListener("resize", function () { if (!pop.hidden) positionPop(); });
  }

  /* ============================================================
   * AI status badge (in chat panel head): "LLM · <model>" when on
   * ============================================================ */
  function refreshBadge() {
    var badge = document.getElementById("chat-llm-badge");
    if (!badge) return;
    if (isEnabled() && getApiKey()) {
      var m = getModel();
      badge.textContent = "LLM · " + m;
      badge.classList.add("on");
      badge.title = "白话模式由 LLM 驱动（" + getBaseUrl() + "）。点 ⚙ 调整。";
    } else {
      badge.textContent = "规则引擎";
      badge.classList.remove("on");
      badge.title = isEnabled() ? "已启用 LLM 但未填 Key — 已降级规则引擎" : "白话模式由内置规则引擎驱动（20 类意图）。点 ⚙ 启用 LLM。";
    }
  }

  /* ============================================================
   * v5: separated creative / readiness / compiler model calls
   * ============================================================ */
  var INTAKE_KEYS = [
    "audience", "genre", "target_words", "premise", "world", "protagonist",
    "supporting_cast", "central_conflict", "stakes", "character_arc", "style",
    "structure", "ending", "boundaries", "craft_patterns"
  ];

  function ModelError(code, message, detail) {
    this.name = "ModelError";
    this.code = code;
    this.message = message || code;
    this.detail = detail || "";
    if (Error.captureStackTrace) Error.captureStackTrace(this, ModelError);
  }
  ModelError.prototype = Object.create(Error.prototype);
  ModelError.prototype.constructor = ModelError;

  function getCreativeTemperature() {
    var t = parseFloat(readSetting("creativeTemp", "0.85"));
    return isNaN(t) ? 0.85 : t;
  }

  /* Low-level provider request — returns the parsed chat-completion JSON.
   * Maps configuration, network/CORS, timeout, and HTTP failures to typed
   * ModelError codes. Never returns a silent fallback. */
  function requestProvider(messages, options) {
    options = options || {};
    if (!getApiKey()) return Promise.reject(new ModelError("not_configured", "未设置 API key"));
    var base = getBaseUrl();
    var model = getModel();
    var url = base + "/chat/completions";
    var body = {
      model: model,
      messages: messages,
      temperature: options.temperature,
      max_tokens: options.maxTokens,
      stream: false
    };
    if (options.json && /^https?:\/\/(api\.openai\.com|api\.deepseek\.com|api\.moonshot\.cn|openrouter\.api\.)/.test(base)) {
      body.response_format = { type: "json_object" };
    }
    var ac = window.AbortController ? new window.AbortController() : null;
    var timer = setTimeout(function () { if (ac) ac.abort(); }, options.timeout || REQUEST_TIMEOUT_MS);
    return fetch(url, {
      method: "POST",
      signal: ac ? ac.signal : undefined,
      headers: { "Content-Type": "application/json", "Authorization": "Bearer " + getApiKey() },
      body: JSON.stringify(body)
    }).then(function (resp) {
      clearTimeout(timer);
      if (!resp.ok) {
        return resp.text().then(function (t) {
          var e = new ModelError("provider_http", "HTTP " + resp.status + " " + resp.statusText, (t || "").slice(0, 200));
          e.status = resp.status;
          throw e;
        });
      }
      return resp.json();
    }, function (err) {
      clearTimeout(timer);
      if (ac && ac.signal && ac.signal.aborted) throw new ModelError("timeout", "请求超时");
      var msg = (err && err.message) || String(err);
      if (/cors|failed to fetch|networkerror|load failed/i.test(msg)) throw new ModelError("cors", msg);
      throw new ModelError("network", msg);
    });
  }

  function extractProviderText(payload) {
    var choice = payload && payload.choices && payload.choices[0];
    var msg = choice && choice.message;
    return (msg && (msg.content || msg.text)) || "";
  }

  function requestText(messages, options) {
    options = options || {};
    return requestProvider(messages, options).then(function (payload) {
      var text = extractProviderText(payload);
      if (!text || !text.trim()) throw new ModelError("empty_response", "模型返回为空");
      return text;
    });
  }

  function buildCreativeMessages(input) {
    input = input || {};
    var ctx = input.context || {};
    var facts = ctx.facts || {};
    var turns = ctx.turns || [];
    var recent = turns.slice(-6).map(function (t) { return "[" + t.role + "] " + t.text; }).join("\n");
    var sys = [
      "你是一位资深小说创作搭档。用户在自由创作工作区与你讨论创意。你的回复是自然语言散文，不要输出 JSON、CLI 命令或表单。",
      "你可以：提出有价值的创作问题；在获得授权后自行选择合理创意方向并说明重要假设；呈现或对比多个方向；质疑或替换尚未确认的想法；生成场景、对话、试写片段。",
      ctx.book ? "当前书籍：" + ctx.book : "",
      facts.confirmed && facts.confirmed.length ? "已确认事实：" + facts.confirmed.join("；") : "",
      facts.boundaries && facts.boundaries.length ? "禁区：" + facts.boundaries.join("；") : "",
      facts.rejected && facts.rejected.length ? "已被否定的方向：" + facts.rejected.join("；") : "",
      ctx.summary ? "长期摘要：" + ctx.summary : "",
      recent ? "最近对话：\n" + recent : "",
      input.autonomy
        ? "用户已授权「你来决定」：你可以自行做主选择合理创意方向，必须说明重要假设，不必反复把选择题推回给用户，但不得覆盖已确认事实或突破禁区。"
        : "用户未授权自主决定，请以讨论和提问为主，必要时给出建议。"
    ].filter(Boolean).join("\n");
    return [
      { role: "system", content: sys },
      { role: "user", content: input.text || "" }
    ];
  }

  function creativeReply(input) {
    if (!isEnabled()) return Promise.reject(new ModelError("not_configured", "LLM 未启用"));
    if (!getApiKey()) return Promise.reject(new ModelError("not_configured", "未设置 API key"));
    var messages = buildCreativeMessages(input);
    return requestText(messages, {
      temperature: getCreativeTemperature(), maxTokens: 3000, json: false
    }).then(function (reply) { return { reply: reply }; });
  }

  function buildReadinessMessages(input) {
    input = input || {};
    var ctx = input.context || {};
    var turns = ctx.turns || [];
    var recent = turns.slice(-8).map(function (t) { return "[" + t.role + "] " + t.text; }).join("\n");
    var sys = [
      "判断当前自由创作对话是否已经成熟到可以生成一份正式创意方案。只返回严格单行 JSON：{\"ready\":true|false,\"reason\":\"简短理由\"}。",
      recent ? "最近对话：\n" + recent : "",
      ctx.summary ? "长期摘要：" + ctx.summary : ""
    ].filter(Boolean).join("\n");
    return [
      { role: "system", content: sys },
      { role: "user", content: "判断成熟度" }
    ];
  }

  function validateReadiness(obj) {
    if (obj && typeof obj.ready === "boolean") {
      return { ready: obj.ready, reason: String(obj.reason || "") };
    }
    return { ready: false, reason: "" };
  }

  function assessReadiness(input) {
    if (!isEnabled() || !getApiKey()) return Promise.resolve({ ready: false, reason: "" });
    var messages = buildReadinessMessages(input);
    return requestText(messages, { temperature: 0.1, maxTokens: 300, json: true })
      .then(extractJson)
      .then(validateReadiness)
      .catch(function () { return { ready: false, reason: "" }; });
  }

  function buildCompilerMessages(input, isRepair) {
    input = input || {};
    var ctx = input.context || {};
    var facts = ctx.facts || {};
    var turns = ctx.turns || [];
    var recent = turns.slice(-10).map(function (t) { return "[" + t.role + "] " + t.text; }).join("\n");
    var fields = INTAKE_KEYS.join(", ");
    var sys = [
      "你是结构化编译器。把自由创作对话编译成一份正式创意方案。只返回严格 JSON，包含字段：preview(自然语言预览), summary(一句话), intake(对象，必须包含这 15 个键：" + fields + "), assumptions(数组), uncertainties(数组), draft_refs(数组), source_turn_ids(数组)。",
      "intake 的每个键必须有实质性内容。autonomy=" + (input.autonomy ? "true" : "false") + "：若为 true，可用合理默认补未明确字段，并在 assumptions 中说明。",
      ctx.book ? "书籍：" + ctx.book : "",
      facts.confirmed && facts.confirmed.length ? "已确认事实：" + facts.confirmed.join("；") : "",
      facts.boundaries && facts.boundaries.length ? "禁区：" + facts.boundaries.join("；") : "",
      ctx.summary ? "摘要：" + ctx.summary : "",
      recent ? "对话：\n" + recent : ""
    ].filter(Boolean).join("\n");
    if (isRepair) sys += "\n上一次输出校验失败，请修正并重新输出完整 JSON。";
    return [
      { role: "system", content: sys },
      { role: "user", content: "编译创意方案" }
    ];
  }

  function validateProposal(parsed, isRepair) {
    if (!parsed || typeof parsed !== "object") throw new ModelError("parse_error", "编译器返回非对象");
    if (!parsed.preview || typeof parsed.preview !== "string") throw new ModelError("schema_error", "缺少 preview");
    var intake = parsed.intake;
    if (!intake || typeof intake !== "object") throw new ModelError("schema_error", "缺少 intake");
    var missing = INTAKE_KEYS.filter(function (k) { return !(k in intake) || intake[k] === "" || intake[k] == null; });
    if (missing.length) {
      throw new ModelError("schema_error", "intake 缺少字段：" + missing.join(", "));
    }
    return parsed;
  }

  function compileOnce(input, isRepair) {
    if (!isEnabled() || !getApiKey()) return Promise.reject(new ModelError("not_configured", "未设置 API key"));
    var messages = buildCompilerMessages(input, isRepair);
    return requestText(messages, { temperature: 0.1, maxTokens: 2400, json: true })
      .then(function (text) {
        try { return extractJson(text); }
        catch (e) { throw new ModelError("parse_error", e && e.message ? e.message : "编译器返回非 JSON"); }
      })
      .then(function (parsed) { return validateProposal(parsed, isRepair); });
  }

  function compileProposal(input) {
    return compileOnce(input, false).catch(function (firstError) {
      if (firstError && firstError.code === "not_configured") throw firstError;
      // One automatic format/schema repair attempt.
      return compileOnce(input, true);
    });
  }

  /* ============================================================
   * Public surface
   * ============================================================ */
  window.NWL = {
    isEnabled: isEnabled,
    getApiKey: getApiKey,
    getBaseUrl: getBaseUrl,
    getModel: getModel,
    isProviderOpenAICompat: isProviderOpenAICompat,
    DEFAULT_BASE: DEFAULT_BASE,
    DEFAULT_MODEL: DEFAULT_MODEL,
    tryLLM: tryLLM,
    creativeReply: creativeReply,
    assessReadiness: assessReadiness,
    compileProposal: compileProposal,
    ModelError: ModelError,
    INTAKE_KEYS: INTAKE_KEYS,
    testConnection: testConnection,
    init: function () {
      ensureSettingsUI();
      refreshBadge();
      var self = this;
      window.addEventListener("nwa.llm.settings-changed", function () { refreshBadge(); });
    },
    refreshBadge: refreshBadge,
    /* Build an internal plan from a stored "ask" → user fills → re-ask. Used by chat.js for slot-then-retry. */
    fillPlaceholder: function (plan, field, value) {
      // Replace every <FIELD> occurrence in argv (string) and in setup values.
      function rep(s) { return String(s).split("<" + field + ">").join(value); }
      function deepRep(v) {
        if (typeof v === "string") return rep(v);
        if (Array.isArray(v)) return v.map(deepRep);
        if (v && typeof v === "object") {
          var o = {};
          Object.keys(v).forEach(function (k) { o[k] = deepRep(v[k]); });
          return o;
        }
        return v;
      }
      if (plan.argv) plan.argv = plan.argv.map(deepRep);
      if (plan.setup) plan.setup = deepRep(plan.setup);
      if (plan.cmdDisplay) plan.cmdDisplay = rep(plan.cmdDisplay);
      if (plan.seq) {
        plan.seq = plan.seq.map(function (s) {
          return { argv: (s.argv || []).map(deepRep), setup: deepRep(s.setup || {}) };
        });
      }
      plan.needsCustom = false;
      delete plan.askFor;
      return plan;
    },
    /* Test-only helper to flip the enabled flag without a DOM. */
    setEnabledForTest: function (on) { writeSetting("enabled", on ? "1" : "0"); }
  };
  if (typeof module !== "undefined" && module.exports) module.exports = window.NWL;
})();
