/* novel-workflow live runner — local-library adapter.
 *
 * Loaded BEFORE app.js / chat.js. When the launcher (scripts/launch_web.py)
 * is serving the SPA from a local port, it injects
 *   window.NWL_RUNTIME = { apiBase: "/api/local", token: "..." }
 * into index.html. In that case this adapter activates and exposes
 * window.NWLocal with a small, queue-safe API that mirrors NWB.runSmart /
 * NWB.runSeq but routes every call to the real Python MCP child
 * (no Pyodide, no fake replay).
 *
 * When NWL_RUNTIME is missing (e.g. the public 8081 static deploy, or
 * GitHub Pages), the adapter is a complete no-op — NWLocal.active stays
 * false and NWB / NWC continue to use the Pyodide engine as before.
 *
 * Public surface (window.NWLocal):
 *   active            — boolean
 *   capabilities      — last /api/local/capabilities payload
 *   stateCache        — mirror of the chat.js "project state" shape
 *   readState()       — sync; returns stateCache
 *   refreshState()    — async; populates stateCache from real workflow.json
 *   listBooks()       — GET /api/local/library
 *   chooseDirectory() — POST /api/local/select-directory
 *   setLibrary(p)     — POST /api/local/library
 *   openBook(dir)     — POST /api/local/open
 *   createBook(t)     — POST /api/local/create
 *   getTree()         — GET /api/local/tree
 *   getActive()       — GET /api/local/active
 *   runMcp(method, params) — POST /api/local/mcp
 *   argvToMcp(argv)   — pure: CLI argv -> { tool, arguments } | { kind }
 *   runSmart(setup, argv, intake) — same shape as NWB.runSmart
 *   runSeq(cmds)      — same shape as NWB.runSeq
 *   refreshFiles()    — calls /api/local/tree and rebuilds NWX
 */
(function () {
  "use strict";

  var runtime = (typeof window !== "undefined") ? window.NWL_RUNTIME : null;
  var active = !!(runtime && runtime.apiBase && runtime.token);

  // ---- public state (always defined, even when inactive) ----
  var capabilities = null;
  var stateCache = { projectExists: false, project: null, chapters: [] };

  // ---- HTTP helper ----
  function callApi(sub, init) {
    init = init || {};
    var method = (init.method || "GET").toUpperCase();
    var headers = { "Accept": "application/json" };
    if (active) {
      headers["Authorization"] = "Bearer " + runtime.token;
      headers["X-Library-Token"] = runtime.token;
    }
    var opts = { method: method, headers: headers, credentials: "same-origin" };
    if (init.body !== undefined && init.body !== null) {
      headers["Content-Type"] = "application/json";
      opts.body = typeof init.body === "string" ? init.body : JSON.stringify(init.body);
    }
    var url = runtime.apiBase + "/" + sub.replace(/^\/+/, "");
    return fetch(url, opts).then(function (r) {
      return r.text().then(function (txt) {
        var parsed = null;
        try { parsed = txt ? JSON.parse(txt) : null; } catch (e) { parsed = null; }
        if (!r.ok) {
          var msg = (parsed && parsed.error && parsed.error.message) || ("HTTP " + r.status);
          var code = (parsed && parsed.error && parsed.error.code) || ("http_" + r.status);
          var err = new Error(msg);
          err.code = code;
          err.status = r.status;
          err.payload = parsed;
          throw err;
        }
        return parsed;
      });
    });
  }

  // ---- argv → MCP tool-call mapping ----
  // The CLI uses kebab-case subcommands with --flag values; the MCP
  // server uses snake_case tool names with an arguments object. This
  // table is the single source of truth for that translation.
  // `path` argv slot is dropped on the floor (MCP is already rooted).
  // `positional` indices count from argv[1] (the subcommand itself is
  // argv[0]); chat.js plans have already factored the project path
  // out as a single token (e.g. "demo") which becomes "." for MCP.
  var ARGV_TABLE = {
    "init": {
      tool: "init", path: 0,
      argmap: [{ flag: "--title", key: "title", required: true }]
    },
    "idea": {
      tool: "idea", path: 0,
      argmap: [
        { flag: "--summary", key: "summary", required: true },
        { flag: "--interview", key: "interview", parse: parseJson, default: "{}" }
      ]
    },
    "intake-check": {
      tool: "intake_check", path: 0, emitPath: false,
      argmap: [
        { flag: "--interview", key: "interview", parse: parseJson, default: "{}" },
        { flag: "--human", key: "human", flag_only: true, drop: true }
      ]
    },
    "concept-review": {
      tool: "concept_review", path: 0,
      argmap: [
        { positional: 0, key: "verdict", required: true, choices: ["PASS", "FAIL"] },
        { flag: "--artifact", key: "artifact", required: true },
        { flag: "--reviewer", key: "reviewer", required: true }
      ]
    },
    "concept-repair": {
      tool: "concept_repair", path: 0,
      argmap: [
        { flag: "--summary", key: "summary" },
        { flag: "--interview", key: "interview", parse: parseJson, default: "{}" },
        { positional: 0, key: "verdict", required: true, choices: ["PASS", "FAIL"] },
        { flag: "--artifact", key: "artifact", required: true },
        { flag: "--reviewer", key: "reviewer", required: true }
      ]
    },
    "bible": {
      tool: "bible", path: 0,
      argmap: [{ flag: "--artifact", key: "artifact", required: true }]
    },
    "outline-write": {
      tool: "outline_write", path: 0,
      argmap: [
        { positional: 0, key: "level", required: true, choices: ["master", "volume", "chapter"] },
        { flag: "--artifact", key: "artifact", required: true }
      ]
    },
    "outline-review": {
      tool: "outline_review", path: 0,
      argmap: [
        { positional: 0, key: "level", required: true, choices: ["master", "volume", "chapter"] },
        { positional: 1, key: "verdict", required: true, choices: ["PASS", "FAIL"] },
        { flag: "--artifact", key: "artifact", required: true },
        { flag: "--reviewer", key: "reviewer", required: true }
      ]
    },
    "outline-repair": {
      tool: "outline_repair", path: 0,
      argmap: [
        { positional: 0, key: "level", required: true, choices: ["master", "volume", "chapter"] },
        { flag: "--artifact", key: "artifact", required: true },
        { positional: 1, key: "verdict", required: true, choices: ["PASS", "FAIL"] },
        { flag: "--review-artifact", key: "review_artifact", required: true },
        { flag: "--reviewer", key: "reviewer", required: true }
      ]
    },
    "outline-lock": { tool: "outline_lock", path: 0, argmap: [] },
    "issue": {
      tool: "issue", path: 0,
      argmap: [
        { positional: 0, key: "chapter", parse: parseInt, required: true },
        { flag: "--title", key: "title", required: true },
        { flag: "--goal", key: "goal", required: true }
      ]
    },
    "draft": {
      tool: "draft", path: 0,
      argmap: [
        { positional: 0, key: "chapter", parse: parseInt, required: true },
        { flag: "--artifact", key: "artifact", required: true },
        { flag: "--prewrite", key: "prewrite", required: true },
        { flag: "--author", key: "author", required: true }
      ]
    },
    "review": {
      tool: "review", path: 0,
      argmap: [
        { positional: 0, key: "chapter", parse: parseInt, required: true },
        { positional: 1, key: "gate", required: true },
        { positional: 2, key: "verdict", required: true, choices: ["PASS", "FAIL"] },
        { flag: "--artifact", key: "artifact", required: true },
        { flag: "--reviewer", key: "reviewer", required: true },
        { flag: "--reason", key: "reason" }
      ]
    },
    "repair": {
      tool: "repair", path: 0,
      argmap: [
        { positional: 0, key: "chapter", parse: parseInt, required: true },
        { flag: "--artifact", key: "artifact", required: true },
        { flag: "--affected", key: "affected", nargs: "+", required: true }
      ]
    },
    "release": {
      tool: "release", path: 0,
      argmap: [
        { positional: 0, key: "chapter", parse: parseInt, required: true }
      ]
    },
    "status": {
      tool: "status", path: 0,
      argmap: [
        { flag: "--chapter", key: "chapter", parse: parseInt },
        { flag: "--human", key: "human", flag_only: true, drop: true }
      ]
    },
    "check": {
      tool: "check", path: 0,
      argmap: [
        { flag: "--security", key: "security", flag_only: true },
        { flag: "--human", key: "human", flag_only: true, drop: true }
      ]
    },
    "roles": {
      tool: "roles", path: 0, emitPath: false,
      argmap: [{ flag: "--human", key: "human", flag_only: true, drop: true }]
    },
    "chapters": {
      tool: "chapters", path: 0,
      argmap: [{ flag: "--human", key: "human", flag_only: true, drop: true }]
    },
    "prewrite": { tool: "prewrite", path: 0, argmap: [
      { positional: 0, key: "chapter", parse: parseInt, required: true },
      { flag: "--author", key: "author", required: true }
    ] },
    "lock-check": { tool: "lock_check", path: 0, argmap: [] }
  };

  function parseJson(s) { try { return JSON.parse(s); } catch (e) { return {}; } }
  function parseInt10(s) { var n = parseInt(s, 10); if (!isFinite(n)) throw new Error("expected integer, got " + s); return n; }

  function argvToMcp(argv) {
    if (!argv || argv.length === 0) return { kind: "empty" };
    var cmd = argv[0];
    if (cmd === "__reset__" || cmd === "__ls__" || cmd === "__cat__" || cmd === "__tree__") {
      return { kind: cmd };
    }
    var spec = ARGV_TABLE[cmd];
    if (!spec) return { kind: "unknown", cmd: cmd };
    var args = {};
    var slotIdx = 0;  // counts non-flag tokens in argv order
    for (var i = 1; i < argv.length; i++) {
      var tok = argv[i];
      if (typeof tok === "string" && tok.indexOf("--") === 0) {
        var hit = null;
        for (var j = 0; j < spec.argmap.length; j++) {
          if (spec.argmap[j].flag === tok) { hit = spec.argmap[j]; break; }
        }
        if (!hit) throw new Error("unknown flag " + tok + " for " + cmd);
        if (hit.flag_only) {
          if (!hit.drop) args[hit.key] = true;
        } else if (hit.nargs) {
          var arr = [];
          if (hit.nargs === "+") {
            // collect every subsequent non-flag token
            i++;
            while (i < argv.length && (typeof argv[i] !== "string" || argv[i].indexOf("--") !== 0)) {
              arr.push(argv[i]);
              i++;
            }
            i--;  // outer for-loop will i++ again
          } else {
            i++;
            for (var k = 0; k < hit.nargs && i < argv.length; k++, i++) {
              arr.push(argv[i]);
            }
            i--;  // outer for-loop will i++ again
          }
          args[hit.key] = hit.parse ? arr.map(hit.parse) : arr;
        } else {
          i++;
          if (i >= argv.length) throw new Error("flag " + tok + " requires a value");
          args[hit.key] = hit.parse ? hit.parse(argv[i]) : argv[i];
        }
      } else {
        // positional: if this slot is the project-path slot, drop it
        if (spec.path !== null && slotIdx === spec.path) {
          slotIdx++;
          continue;
        }
        // map to argmap: realPositional shifts down by 1 after the path slot
        var realPos = (spec.path !== null && slotIdx > spec.path) ? slotIdx - 1 : slotIdx;
        var pos = null;
        for (var p = 0; p < spec.argmap.length; p++) {
          if (spec.argmap[p].positional === realPos) { pos = spec.argmap[p]; break; }
        }
        if (!pos) throw new Error("too many positionals for " + cmd);
        if (pos.flag_only) {
          args[pos.key] = true;
        } else {
          args[pos.key] = pos.parse ? pos.parse(tok) : tok;
        }
        slotIdx++;
      }
    }
    if (spec.path !== null && spec.emitPath !== false) args.path = ".";
    // Apply defaults for any argmap entry not yet provided; the default
    // is run through the same parser as a CLI-provided value.
    for (var r = 0; r < spec.argmap.length; r++) {
      var entry = spec.argmap[r];
      if (entry.default !== undefined && args[entry.key] === undefined) {
        args[entry.key] = entry.parse ? entry.parse(entry.default) : entry.default;
      }
    }
    for (var r2 = 0; r2 < spec.argmap.length; r2++) {
      var req = spec.argmap[r2];
      if (req.required && (args[req.key] === undefined || args[req.key] === null || args[req.key] === "")) {
        throw new Error("missing required: " + (req.flag || ("#" + req.positional)) + " for " + cmd);
      }
    }
    return { kind: "mcp", tool: spec.tool, arguments: args };
  }

  // ---- result normalisation ----
  // MCP returns either:
  //   { result: { content: [{type:"text", text:"..."}], isError: true } }
  //   { result: { content: [...], structuredContent: {...} } }
  //   { error: { code, message } }
  // NWB.runSmart consumers expect { code, out, err }.
  // isError → code 2 (state-machine rejection, like the live engine)
  // protocol error → code 1
  // success → code 0
  function normaliseRpcResponse(rpc) {
    var out = { code: 0, out: "", err: "" };
    if (!rpc) { out.code = 1; out.err = "empty response"; return out; }
    if (rpc.error) {
      out.code = 1;
      out.err = "[mcp " + (rpc.error.code || "ERR") + "] " + (rpc.error.message || "unknown");
      return out;
    }
    var r = rpc.result || rpc || {};
    var chunks = [];
    if (Array.isArray(r.content)) {
      r.content.forEach(function (c) {
        if (c && typeof c.text === "string") chunks.push(c.text);
      });
    }
    if (r.structuredContent && Object.keys(r.structuredContent).length) {
      chunks.push("```json\n" + JSON.stringify(r.structuredContent, null, 2) + "\n```");
    }
    var text = chunks.join("\n");
    if (r.isError) {
      out.code = 2;
      out.err = text || "tool refused (isError)";
      return out;
    }
    out.code = 0;
    out.out = text;
    return out;
  }

  function formatCmdLine(argv) {
    if (!argv || argv.length === 0) return "";
    var parts = ["novel-workflow"];
    for (var i = 0; i < argv.length; i++) {
      var a = argv[i];
      if (typeof a !== "string" || a.indexOf(" ") < 0) { parts.push(a); continue; }
      parts.push(JSON.stringify(a));
    }
    return parts.join(" ");
  }

  // ---- special markers (mirror the live engine semantics) ----
  function handleMarker(argv) {
    if (!argv || argv.length === 0) return Promise.resolve({ code: 0, out: "", err: "" });
    var cmd = argv[0];
    if (cmd === "__reset__") {
      // local mode: the project root IS the active book; "reset" is a
      // user-visible concept that lives in the demo. Surface this so
      // the chat doesn't lie about what happened.
      return Promise.resolve({
        code: 0,
        out: "(本地模式下，重置一本书请用「换一本书」：library 面板里切换或新建。)",
        err: ""
      });
    }
    if (cmd === "__ls__") {
      return getTree().then(function (snap) {
        var root = (argv[1] || "").replace(/^\/+/, "") || ".";
        var rows = (snap.entries || []).filter(function (e) {
          return e.path === root || e.path.indexOf(root + "/") === 0;
        });
        if (rows.length === 0) return { code: 0, out: "(empty)", err: "" };
        return { code: 0, out: rows.map(function (e) {
          return (e.type === "dir" ? "d " : "  ") + e.path;
        }).join("\n"), err: "" };
      });
    }
    if (cmd === "__tree__") {
      return getTree().then(function (snap) {
        var lines = (snap.entries || []).map(function (e) {
          return (e.type === "dir" ? "d " : "f ") + e.path + "  (" + (e.size || 0) + " B)";
        });
        return { code: 0, out: lines.join("\n") || "(empty)", err: "" };
      });
    }
    if (cmd === "__cat__") {
      var rel = (argv[1] || "").replace(/^\/+/, "");
      if (!rel) return Promise.resolve({ code: 1, out: "", err: "cat: missing path" });
      return runMcp("resources/read", { uri: "novel://artifact/" + rel })
        .then(function (rpc) { return normaliseRpcResponse(rpc); })
        .catch(function (e) { return { code: 1, out: "", err: "cat: " + (e.message || e) }; });
    }
    return Promise.resolve({ code: 1, out: "", err: "unknown marker: " + cmd });
  }

  // ---- public MCP plumbing ----
  function runMcp(method, params) {
    if (!active) return Promise.reject(new Error("local library not active"));
    return callApi("mcp", { method: "POST", body: { method: method, params: params || {} } });
  }

  // ---- state derivation (mirrors the live engine's nw_read_state) ----
  function buildStateFromWorkflow(workflow, chapterFiles) {
    var out = { projectExists: false, project: null, chapters: [] };
    if (!workflow || typeof workflow !== "object") return out;
    out.projectExists = true;
    var ol = workflow.outline || {};
    out.project = {
      title: workflow.title,
      stage: workflow.stage,
      concept: (workflow.concept || {}).status,
      bible: (workflow.bible || {}).status,
      outline: {
        master: (ol.master || {}).status,
        volume: (ol.volume || {}).status,
        chapter: (ol.chapter || {}).status
      },
      outlineLocked: !!workflow.outline_locked_at,
      chapters: workflow.chapters || {}
    };
    Object.keys(chapterFiles || {}).forEach(function (k) {
      var m = k.match(/^\.novel-workflow\/chapter-(\d+)\.json$/);
      if (!m) return;
      try {
        var st = JSON.parse(chapterFiles[k]);
        out.chapters.push({
          chapter: st.chapter,
          status: st.status,
          title: st.title,
          gates: st.gates || {}
        });
      } catch (e) { /* skip malformed */ }
    });
    return out;
  }

  function refreshState() {
    if (!active) return Promise.resolve(stateCache);
    return Promise.all([
      callApi("active").catch(function () { return { active: null, tree: null }; }),
      runMcp("tools/call", { name: "status", arguments: { path: ".", human: false } })
        .catch(function () { return null; })
    ]).then(function (res) {
      var activeInfo = res[0];
      var statusRpc = res[1];
      var statusResult = statusRpc && statusRpc.result ? statusRpc.result : statusRpc;
      var workflow = null;
      if (statusResult && Array.isArray(statusResult.content)) {
        statusResult.content.forEach(function (c) {
          if (c && typeof c.text === "string" && c.text.indexOf("{") >= 0) {
            try {
              var j = JSON.parse(c.text);
              if (j && j.project && j.project.title) workflow = j.project;
              else if (j && j.title) workflow = j;
            } catch (e) {}
          }
        });
      }
      var chapterFiles = {};
      if (activeInfo && activeInfo.tree && Array.isArray(activeInfo.tree.entries)) {
        // We don't have raw contents from the tree snapshot (it strips
        // file bodies to keep the response small). For state we only
        // need to know which chapter files exist; if you need the
        // full state, fall back to a status call with --human. The
        // chat summary handles missing chapters as "(none)".
      }
      stateCache = buildStateFromWorkflow(workflow, chapterFiles);
      if (api) api.stateCache = stateCache;
      return stateCache;
    });
  }

  // ---- file tree refresh (mirror of refreshFiles) ----
  function refreshFiles() {
    if (!active) return Promise.resolve();
    return getTree().then(function (snap) {
      if (window.NWX && typeof window.NWX.update === "function") {
        var files = {};
        (snap.entries || []).forEach(function (e) {
          if (e.type !== "file") return;
          files[e.path] = "";
        });
        window.NWX.update(files);
      }
      return refreshState();
    });
  }

  // ---- book / library operations ----
  function refreshCapabilities() {
    if (!active) return Promise.resolve(null);
    return callApi("capabilities").then(function (c) {
      capabilities = c;
      if (api) api.capabilities = c;
      return c;
    });
  }
  function listBooks() {
    if (!active) return Promise.resolve({ library: "", books: [] });
    return callApi("library");
  }
  function chooseDirectory() {
    if (!active) return Promise.reject(new Error("local library not active"));
    return callApi("select-directory", { method: "POST", body: {} })
      .then(function (r) {
        if (r && r.selected) return refreshCapabilities().then(function () { return r; });
        return r;
      });
  }
  function setLibrary(absPath) {
    if (!active) return Promise.reject(new Error("local library not active"));
    return callApi("library", { method: "POST", body: { path: absPath } })
      .then(function () { return refreshCapabilities(); });
  }
  function openBook(directory) {
    if (!active) return Promise.reject(new Error("local library not active"));
    return callApi("open", { method: "POST", body: { directory: directory } })
      .then(function () { return refreshCapabilities(); });
  }
  function createBook(title, decision) {
    if (!active) return Promise.reject(new Error("local library not active"));
    var body = { title: title };
    if (decision) body.decision = decision;
    return callApi("create", { method: "POST", body: body });
  }
  function getTree() {
    if (!active) return Promise.resolve({ root: "", entries: [], truncated: false, total_bytes: 0 });
    return callApi("tree");
  }
  function getActive() {
    if (!active) return Promise.resolve({ active: null, tree: null });
    return callApi("active");
  }

  // ---- runSmart / runSeq: queue-safe (mirror of NWB) ----
  var queue = Promise.resolve();
  function enqueue(fn) { var p = queue.then(fn); queue = p.catch(function () {}); return p; }

  function rewriteChapterArtifacts(setup, plan, artifactDir) {
    var rewrittenSetup = {};
    var pathMap = {};
    Object.keys(setup || {}).forEach(function (rel) {
      var next = rel;
      if (artifactDir && next.indexOf(artifactDir + "/") !== 0) {
        next = artifactDir + "/" + next.replace(/^chapters\//, "");
      }
      pathMap[rel] = next;
      rewrittenSetup[next] = setup[rel];
    });
    var rewrittenPlan = {
      kind: plan.kind,
      tool: plan.tool,
      arguments: Object.assign({}, plan.arguments || {})
    };
    ["artifact", "prewrite", "review_artifact"].forEach(function (key) {
      var value = rewrittenPlan.arguments[key];
      if (typeof value === "string" && pathMap[value]) {
        rewrittenPlan.arguments[key] = pathMap[value];
      }
    });
    return { setup: rewrittenSetup, plan: rewrittenPlan };
  }

  function chapterArtifactDir(chapter) {
    if (!chapter) return Promise.resolve("");
    return runMcp("resources/read", { uri: "novel://chapter/" + chapter })
      .then(function (rpc) {
        var resourceResult = rpc && rpc.result ? rpc.result : rpc;
        var contents = resourceResult && resourceResult.contents;
        if (!Array.isArray(contents) || !contents.length) return "";
        try {
          var payload = JSON.parse(contents[0].text || "{}");
          var state = payload.chapter || payload;
          return (state && state.artifact_dir) || "";
        } catch (e) { return ""; }
      });
  }

  function prepareSetup(setup, plan) {
    if (Object.keys(setup || {}).length === 0) return Promise.resolve(plan);
    var chapter = plan && plan.arguments && plan.arguments.chapter;
    return chapterArtifactDir(chapter).then(function (artifactDir) {
      var prepared = rewriteChapterArtifacts(setup, plan, artifactDir);
      var writes = Promise.resolve();
      Object.keys(prepared.setup).forEach(function (path) {
        writes = writes.then(function () {
          return runMcp("tools/call", {
            name: "write_artifact",
            arguments: { path: path, content: prepared.setup[path] }
          }).then(function (rpc) {
            var result = normaliseRpcResponse(rpc);
            if (result.code !== 0) throw new Error(result.err || "write_artifact failed");
          });
        });
      });
      return writes.then(function () { return prepared.plan; });
    });
  }

  var projectCreator = null;

  function setProjectCreator(fn) {
    projectCreator = typeof fn === "function" ? fn : null;
  }

  function runProjectCreator(title) {
    if (!projectCreator) {
      return Promise.resolve({
        code: 1,
        out: "",
        err: "本地新书创建器尚未就绪，请打开书库面板后重试。"
      });
    }
    return Promise.resolve()
      .then(function () { return projectCreator(title); })
      .then(function (result) {
        if (result && typeof result.code === "number") return result;
        return { code: 1, out: "", err: "本地新书创建器返回了无效结果。" };
      })
      .catch(function (error) {
        return {
          code: 1,
          out: "",
          err: "新书创建失败：" + ((error && error.message) || error)
        };
      });
  }

  function runSmart(setup, argv, intake) {
    if (!active) return Promise.resolve({ code: -1, out: "", err: "local library not active" });
    if (typeof setup === "string") { intake = argv; argv = setup; setup = {}; }
    setup = setup || {}; argv = argv || [];
    return enqueue(function () { return runSmartInner(setup, argv, !!intake); });
  }

  function runSmartInner(setup, argv, intake) {
    var marker = argv && argv[0];
    if (marker === "__reset__" || marker === "__ls__" || marker === "__cat__" || marker === "__tree__") {
      return handleMarker(argv);
    }
    var plan;
    try { plan = argvToMcp(argv); }
    catch (e) { return Promise.resolve({ code: 1, out: "", err: "argv parse: " + e.message }); }
    if (plan.kind === "unknown") {
      return Promise.resolve({ code: 1, out: "", err: "unsupported command: " + plan.cmd });
    }
    if (plan.kind === "empty") {
      return Promise.resolve({ code: 1, out: "", err: "no command" });
    }
    if (plan.tool === "init") {
      return runProjectCreator(plan.arguments.title);
    }
    // Echo to terminal (caller is expected to handle the cmd-line echo
    // themselves; we only echo the result so the local engine matches
    // the live one byte-for-byte from the user's perspective).
    return prepareSetup(setup, plan).then(function (preparedPlan) {
      return runMcp("tools/call", {
        name: preparedPlan.tool,
        arguments: preparedPlan.arguments
      });
    })
      .then(function (rpc) {
        var r = normaliseRpcResponse(rpc);
        if (r.code === 0) return refreshState().then(function () { return r; });
        return r;
      })
      .catch(function (e) {
        return { code: 1, out: "", err: "transport: " + (e.message || e) };
      });
  }

  function runSeq(cmds) {
    if (!active) return Promise.resolve({ results: [], last: { code: -1, out: "", err: "local library not active" } });
    return enqueue(function () {
      var results = [];
      var last = null;
      var p = Promise.resolve();
      (cmds || []).forEach(function (c) {
        p = p.then(function () {
          var argv = c.argv || [];
          return runSmartInner(c.setup || {}, argv, !!c.intake).then(function (r) {
            results.push(r); last = r;
            if (r.code === 1) {
              // short-circuit: this mirrors runSeq in NWB; we just
              // bail. The user can re-run after fixing the call.
              throw { __shortCircuit: true, result: r };
            }
            return r;
          }).catch(function (e) {
            if (e && e.__shortCircuit) throw e;
            var r = { code: 1, out: "", err: (e && e.message) || String(e) };
            results.push(r); last = r;
            return r;
          });
        });
      });
      return p.then(function () { return { results: results, last: last }; })
        .catch(function (e) {
          if (e && e.__shortCircuit) return { results: results, last: e.result };
          return { results: results, last: { code: 1, out: "", err: (e && e.message) || String(e) } };
        });
    });
  }

  // ---- attach to window ----
  var api = {
    active: active,
    capabilities: capabilities,
    stateCache: stateCache,
    argvToMcp: argvToMcp,
    refreshCapabilities: refreshCapabilities,
    listBooks: listBooks,
    chooseDirectory: chooseDirectory,
    setLibrary: setLibrary,
    openBook: openBook,
    createBook: createBook,
    getTree: getTree,
    getActive: getActive,
    runMcp: runMcp,
    setProjectCreator: setProjectCreator,
    readState: function () { return stateCache; },
    refreshState: refreshState,
    refreshFiles: refreshFiles,
    runSmart: runSmart,
    runSeq: runSeq,
    normaliseRpcResponse: normaliseRpcResponse,
    rewriteChapterArtifacts: rewriteChapterArtifacts,
    formatCmdLine: formatCmdLine
  };
  // ``window.NWL`` belongs to llm.js (the optional LLM adapter).  Keep the
  // local MCP bridge on its own global so loading llm.js cannot overwrite it.
  if (typeof window !== "undefined") window.NWLocal = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
