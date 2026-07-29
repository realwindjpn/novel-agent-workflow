/* novel-workflow live runner — engine orchestrator.
 *
 * Two execution modes:
 *   LIVE   — Pyodide (CPython 3.12 WASM) mounts the package source into its
 *            in-browser filesystem, runs the real cli.main() against a
 *            tty-claimed stdout, and exposes filesystem helpers.
 *   REPLAY — when WASM cannot load, the recorded tape (sandbox CPython 3.11
 *            run, verbatim stdout) plays back. Only guided commands and a
 *            literal "novel-workflow <args>" match to a recorded step.
 *
 * Single delivery channel: every command echoes to the terminal, every
 * completion (live or replay) refreshes the file explorer.
 */
(function () {
  "use strict";

  var PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
  var BOOT_TIMEOUT_MS = 60000;

  var termScroll = document.getElementById("term-scroll");
  var termInput = document.getElementById("term-input");
  var termHint = document.getElementById("term-hint");
  var engineBadge = document.getElementById("engine-badge");
  var engineText = document.getElementById("engine-text");
  var filesModeHint = document.getElementById("files-mode");
  var btnRunAll = document.getElementById("btn-runall");

  // The launcher (scripts/launch_web.py) injects window.NWL_RUNTIME when
  // serving the SPA from a local port. local.js then exposes window.NWLocal
  // and sets NWLocal.active = true. In that case we skip Pyodide entirely
  // and route every command through the real Python MCP child.
  var localMode = !!(window.NWLocal && window.NWLocal.active);
  var mode = localMode ? "local" : "booting";  // booting | local | live | replay
  var pyodide = null;
  var pyReady = null;         // Promise resolving on first boot (or null in local)
  var history = [];
  var histIdx = -1;
  var wave = new window.NWA.Waveform(document.getElementById("wave"));
  var replayIdx = -1;         // highest step id completed in replay mode

  /* ---------------- terminal helpers ---------------- */
  function appendLine(html, cls) {
    var div = document.createElement("div");
    div.className = "tline" + (cls ? " " + cls : "");
    div.innerHTML = html;
    termScroll.appendChild(div);
    termScroll.scrollTop = termScroll.scrollHeight;
    return div;
  }
  function bootLog(msg, ok) {
    appendLine('[<span class="' + (ok ? "ok" : "dim") + '">' + (ok ? " ok " : "....") + "</span>] " + msg, "boot");
  }
  function cmdLine(prompt, line) {
    appendLine('<span class="prompt">' + window.NWA.escapeHtml(prompt) + "</span> " +
               window.NWA.escapeHtml(line), "t-cmd");
  }
  function outBlock(text, kind) {
    var cls = kind === "err" ? "t-err" : "t-out";
    appendLine(window.NWA.ansiToHtml(text || ""), cls);
  }
  function exitBadge(code) {
    if (code === 0 || code === undefined || code === null) return "";
    var tag = "exit " + code;
    if (code === 2) tag = "exit 2 · 状态机拒绝";
    return '<span class="t-exit">' + window.NWA.escapeHtml(tag) + "</span>";
  }
  function newline() { appendLine(""); }

  /* ---------------- v3 · toast + busy + execution queue ----------------
   * Single-rail: term input + guide step clicks + chat bridge all go
   * through enqueue(); the previous Pyodide call must finish before the
   * next one starts, so a typed command never interleaves with a guide
   * step in the engine. UI gives immediate feedback: term prompt spins,
   * and click/Enter on a busy run is a no-op with a hint toast. */
  var toastEl = null, toastTimer = null;
  function toast(msg) {
    if (!toastEl) toastEl = document.getElementById("toast");
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove("show"); }, 2200);
  }
  var execBusy = false;
  function setBusy(on) {
    execBusy = on;
    var row = document.getElementById("term-input-row");
    if (row) row.classList.toggle("busy", !!on);
    // Keep run-all button enabled: it already awaits each step. Only
    // disable direct-step clicks via NWR.runStep guard (below).
  }
  var execQueue = [];
  function enqueue(fn) {
    return new Promise(function (resolve, reject) {
      execQueue.push({ fn: fn, res: resolve, rej: reject });
      pump();
    });
  }
  function pump() {
    if (execBusy) return;
    var job = execQueue.shift();
    if (!job) { setBusy(false); return; }
    execBusy = true; setBusy(true);
    Promise.resolve()
      .then(job.fn)
      .then(function (v) { job.res(v); }, function (e) { job.rej(e); })
      .then(function () { execBusy = false; pump(); });
  }

  /* ---------------- v3 · boot progress bar phases ---------------- */
  var bootBar = null, bootFill = null;
  function setBootPhase(pct, done) {
    if (!bootFill) {
      bootBar = document.getElementById("boot-bar");
      bootFill = document.getElementById("boot-bar-fill");
    }
    if (!bootFill) return;
    bootFill.style.width = Math.max(5, Math.min(100, pct)) + "%";
    if (done && bootBar) bootBar.classList.add("done");
  }

  /* ---------------- file refresh ---------------- */
  var stateCache = { projectExists: false, project: null, chapters: [] };
  function setStateCache(s) { stateCache = s || { projectExists: false, project: null, chapters: [] }; }
  function refreshState() {
    if (mode === "booting") return Promise.resolve();
    if (mode === "local") {
      return window.NWLocal.refreshState().then(function (s) {
        if (s) setStateCache(s);
      }).catch(function () { /* keep previous cache on transient failure */ });
    }
    if (mode === "live") {
      return liveEval("nw_read_state()").then(function (s) {
        try { setStateCache(JSON.parse(s)); } catch (e) { /* leave stale */ }
      }).catch(function () { /* keep previous cache on transient failure */ });
    }
    // replay: derive synchronously from latest tape step
    if (replayIdx < 0) { setStateCache({ projectExists: false, project: null, chapters: [] }); return Promise.resolve(); }
    setStateCache(deriveReplayState());
    return Promise.resolve();
  }
  async function refreshFiles() {
    if (mode === "local") {
      try { await window.NWLocal.refreshFiles(); }
      catch (e) { window.NWX.update({}); }
      return refreshState();
    }
    try {
      var treeJson = mode === "live"
        ? await pyodide.runPythonAsync("nw_tree('demo')")
        : currentReplayTree();
      window.NWX.update(JSON.parse(treeJson));
    } catch (e) {
      window.NWX.update({});
    }
    return refreshState();
  }

  function currentReplayTree() {
    if (replayIdx < 0) return "{}";
    return JSON.stringify(window.NW_TAPE.steps[replayIdx].tree);
  }

  /* ---------------- execution: live ---------------- */
  function bootPyodide() {
    var chain = new Promise(function (resolve, reject) {
      var t0 = Date.now();
      (function waitPyodide() {
        if (typeof loadPyodide === "function") return resolve();
        if (Date.now() - t0 > BOOT_TIMEOUT_MS) return reject(new Error("Pyodide CDN 加载超时"));
        setTimeout(waitPyodide, 60);
      })();
    }).then(function () {
      setBootPhase(45);
      bootLog("拉取 Pyodide v0.26.4 (CPython 3.12 WASM) …", false);
      return loadPyodide({ indexURL: PYODIDE_CDN });
    }).then(function (py) {
      pyodide = py;
      setBootPhase(70);
      bootLog("挂载 novel_workflow 源码 (7 文件 / " +
              (Object.values(window.NW_SOURCES).reduce(function (a, b) { return a + b.length; }, 0) / 1024).toFixed(1) + " KB) …",
              false);
      try {
        py.FS.mkdirTree("/home/pyodide/pkg/novel_workflow");
        Object.keys(window.NW_SOURCES).forEach(function (name) {
          py.FS.writeFile("/home/pyodide/pkg/novel_workflow/" + name,
                          window.NW_SOURCES[name], { encoding: "utf8" });
        });
      } catch (e) {
        bootLog("写源码失败（" + e.message + "），继续尝试 BOOT_PY…", false);
      }
      setBootPhase(88);
      bootLog("运行引导脚本 (sys.path / subprocess stub / tty stdout) …", false);
      return py.runPythonAsync(BOOT_PY);
    });
    // Hard timeout for the whole chain: loadPyodide + FS write + BOOT_PY.
    // In a constrained sandbox the WASM compile can take 30-120s; past 150s we
    // bail to REPLAY rather than hang the page forever.
    var hardTimeout = new Promise(function (_, reject) {
      setTimeout(function () { reject(new Error("WASM 引擎整体超时 (150s)")); }, 150000);
    });
    return Promise.race([chain, hardTimeout]).then(function () {
      mode = "live";
      setBootPhase(100, true);
      setEngine("live", "公网演示 · 浏览器内存");
      termInput.disabled = false;
      termInput.placeholder = "novel-workflow 真实命令 · help / ls / cat / tree / clear / reset";
      btnRunAll.disabled = false;
      bootLog("就绪：真实 novel_workflow.cli 已加载，输入命令直接执行。", true);
      wave.pulse(1.2);
      return refreshFiles();
    });
  }

  var BOOT_PY = [
    "import sys, os, io, json, shlex, types, contextlib",
    "sys.path.insert(0, '/home/pyodide/pkg')",
    "os.chdir('/home/pyodide')",
    "os.environ['TERM'] = 'xterm-256color'",
    "os.environ.pop('NO_COLOR', None)",
    "try:",
    "    import subprocess  # noqa: F401",
    "except Exception:",
    "    pass",
    "# pyodide ships a subprocess that raises at call time; we replace it with",
    "# an explicit stub so security_scan (and any future caller) gets a clear",
    "# OSError instead of a cryptic emscripten message.",
    "_sp = types.ModuleType('subprocess')",
    "def _unavailable(*a, **k):",
    "    raise OSError('subprocess is unavailable in the browser runtime')",
    "_sp.run = _unavailable; _sp.Popen = _unavailable",
    "_sp.call = _unavailable; _sp.check_call = _unavailable",
    "_sp.check_output = _unavailable",
    "_sp.getoutput = _unavailable; _sp.getstatusoutput = _unavailable",
    "_sp.PIPE = -1; _sp.STDOUT = -2; _sp.DEVNULL = -3",
    "class _CPE(Exception): pass",
    "class _TO(Exception): pass",
    "_sp.CalledProcessError = _CPE; _sp.TimeoutExpired = _TO",
    "_sp.SubprocessError = type('SubprocessError', (Exception,), {})",
    "sys.modules['subprocess'] = _sp",
    "from novel_workflow import cli as _cli",
    "from novel_workflow.core import complete_intake_example",
    "",
    "class _Tty(io.StringIO):",
    "    def isatty(self): return True",
    "",
    "def nw_run(line):",
    "    argv = shlex.split(line or '')",
    "    if argv and argv[0] in ('novel-workflow', 'nw'):",
    "        argv = argv[1:]",
    "    if not argv:",
    "        return json.dumps({'code': 0, 'out': '', 'err': ''})",
    "    out, err = _Tty(), _Tty()",
    "    code = 0",
    "    try:",
    "        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):",
    "            code = _cli.main(argv)",
    "    except SystemExit as e:",
    "        code = e.code if isinstance(e.code, int) else 0",
    "    except Exception as e:",
    "        err.write('unhandled error: ' + type(e).__name__ + ': ' + str(e) + '\\n')",
    "        code = 99",
    "    return json.dumps({'code': code, 'out': out.getvalue(), 'err': err.getvalue()})",
    "",
    "def nw_run_argv(json_argv):",
    "    argv = json.loads(json_argv)",
    "    out, err = _Tty(), _Tty()",
    "    code = 0",
    "    try:",
    "        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):",
    "            code = _cli.main(argv)",
    "    except SystemExit as e:",
    "        code = e.code if isinstance(e.code, int) else 0",
    "    except Exception as e:",
    "        err.write('unhandled error: ' + type(e).__name__ + ': ' + str(e) + '\\n')",
    "        code = 99",
    "    return json.dumps({'code': code, 'out': out.getvalue(), 'err': err.getvalue()})",
    "",
    "def nw_write(path, content):",
    "    import pathlib",
    "    p = pathlib.Path(path)",
    "    p.parent.mkdir(parents=True, exist_ok=True)",
    "    p.write_text(content, encoding='utf-8')",
    "",
    "def nw_intake():",
    "    return json.dumps(complete_intake_example(), ensure_ascii=False)",
    "",
    "def nw_tree(root='demo'):",
    "    import pathlib",
    "    base = pathlib.Path(root)",
    "    result = {}",
    "    if not base.exists():",
    "        return json.dumps(result)",
    "    for p in sorted(base.rglob('*')):",
    "        if p.is_file():",
    "            try:",
    "                result[str(p.relative_to(base))] = p.read_text(encoding='utf-8', errors='replace')",
    "            except Exception:",
    "                result[str(p.relative_to(base))] = '<binary>'",
    "    return json.dumps(result)",
    "",
    "def nw_rm(root='demo'):",
    "    import shutil, pathlib",
    "    p = pathlib.Path(root)",
    "    if p.exists(): shutil.rmtree(p)",
    "",
    "def nw_ls(path='.'):",
    "    import pathlib",
    "    p = pathlib.Path(path)",
    "    if not p.exists(): return f'ls: {path}: no such file or directory\\n'",
    "    return '\\n'.join(sorted(q.name + ('/' if q.is_dir() else '') for q in p.iterdir())) + '\\n'",
    "",
    "def nw_cat(path):",
    "    import pathlib",
    "    p = pathlib.Path(path)",
    "    if not p.exists(): return f'cat: {path}: no such file or directory\\n'",
    "    return p.read_text(encoding='utf-8', errors='replace')",
    "",
    "def nw_read_state():",
    "    import pathlib",
    "    base = pathlib.Path('demo')",
    "    out = {'projectExists': False, 'project': None, 'chapters': []}",
    "    if not base.exists(): return json.dumps(out)",
    "    wf = base / 'workflow.json'",
    "    if wf.exists():",
    "        proj = json.loads(wf.read_text(encoding='utf-8', errors='replace'))",
    "        out['projectExists'] = True",
    "        ol = proj.get('outline', {})",
    "        out['project'] = {",
    "            'title': proj.get('title'),",
    "            'stage': proj.get('stage'),",
    "            'concept': proj.get('concept', {}).get('status'),",
    "            'bible': proj.get('bible', {}).get('status'),",
    "            'outline': {",
    "                'master': ol.get('master', {}).get('status') if isinstance(ol.get('master'), dict) else None,",
    "                'volume': ol.get('volume', {}).get('status') if isinstance(ol.get('volume'), dict) else None,",
    "                'chapter': ol.get('chapter', {}).get('status') if isinstance(ol.get('chapter'), dict) else None,",
    "            },",
    "            'outlineLocked': bool(proj.get('outline_locked_at')),",
    "            'chapters': proj.get('chapters', {}),",
    "        }",
    "    nw = base / '.novel-workflow'",
    "    if nw.exists():",
    "        for p in sorted(nw.glob('chapter-*.json')):",
    "            try:",
    "                st = json.loads(p.read_text(encoding='utf-8', errors='replace'))",
    "                out['chapters'].append({",
    "                    'chapter': st.get('chapter'),",
    "                    'status': st.get('status'),",
    "                    'title': st.get('title'),",
    "                    'gates': st.get('gates', {}),",
    "                })",
    "            except Exception: pass",
    "    return json.dumps(out, ensure_ascii=False)"
  ].join("\n");

  /* ---------------- execution: replay ---------------- */
  function setEngine(cls, label) {
    engineBadge.className = "engine-badge " + cls;
    engineText.textContent = label;
  }
  function fallbackToReplay(reason) {
    mode = "replay";
    setBootPhase(100, true);
    setEngine("replay", "公网演示 · 浏览器内存");
    termInput.disabled = false;
    termInput.placeholder = "回放模式：键入与引导完全一致的真实命令，或敲 help / clear / reset";
    btnRunAll.disabled = false;
    filesModeHint.textContent = "文件状态：按引导步骤进度快照（沙箱实跑）";
    bootLog("回放模式（" + reason + "）——按引导步骤执行，输出与文件树为沙箱实跑逐字录制。", true);
    wave.pulse(0.8);
  }

  function replayRunStep(step) {
    cmdLine("~/relay $", step.display);
    outBlock(step.stdout);
    if (step.code) appendLine(exitBadge(step.code));
    var idx = window.NW_TAPE.steps.findIndex(function (s) { return s.id === step.id; });
    if (idx > replayIdx) replayIdx = idx;
    return refreshFiles().then(function () { wave.pulse(step.code ? 0.6 : 1.0); return step.code; });
  }

  function replayRunLine(line) {
    var match = null;
    for (var i = window.NW_TAPE.steps.length - 1; i >= 0; i--) {
      if (window.NW_TAPE.steps[i].display === line) { match = window.NW_TAPE.steps[i]; break; }
    }
    if (!match) {
      outBlock("回放模式仅支持引导步骤中逐字出现的命令；或切到 live 引擎（拉取 WASM 完成后即可自由输入）。\n", "err");
      return Promise.resolve();
    }
    return replayRunStep(match);
  }

  /* ---------------- line dispatcher ---------------- */
  function handleLine(line) {
    if (line.trim() === "") return Promise.resolve();
    var argv = line.split(/\s+/);
    var head = argv[0];
    if (head === "clear") { termScroll.innerHTML = ""; return Promise.resolve(); }
    if (head === "help") {
      cmdLine("~/relay $", line);
      outBlock([
        "novel-workflow <sub> <args>    真实命令（live）或回放匹配（replay）",
        "                              25 子命令见 cli.py / model_cli.py",
        "                              例: status demo --chapter 1 --human",
        "                                  roles demo --human / chapters demo --human",
        "                                  check demo --security --human",
        "ls [path]   cat <file>   tree [path]   辅助浏览",
        "clear       清屏",
        "reset       清空 demo/ 回到初始（每步引导重置状态）",
        "help        本帮助"
      ].join("\n"));
      return Promise.resolve();
    }
    cmdLine("~/relay $", line);
    if (head === "reset") {
      if (mode === "live") {
        return pyodide.runPythonAsync("nw_rm('demo')").then(function () {
          window.NWG.reset(); return refreshFiles();
        });
      } else {
        replayIdx = -1; window.NWG.reset(); return refreshFiles();
      }
    }
    if (mode === "live") {
      return dispatchLive(line);
    } else {
      return replayRunLine(line);
    }
  }

  function dispatchLive(line) {
    if (line.split(/\s+/)[0] === "ls") {
      return pyodide.runPythonAsync("nw_ls(" + JSON.stringify(line.slice(2).trim() || "demo") + ")")
        .then(function (t) { outBlock(t); wave.pulse(0.5); });
    }
    if (line.split(/\s+/)[0] === "cat") {
      return pyodide.runPythonAsync("nw_cat(" + JSON.stringify(line.slice(3).trim()) + ")")
        .then(function (t) { outBlock(t); wave.pulse(0.5); });
    }
    if (line === "tree" || line.split(/\s+/)[0] === "tree") {
      var p = line.slice(4).trim() || "demo";
      return pyodide.runPythonAsync("nw_tree(" + JSON.stringify(p) + ")").then(function (json) {
        var tree = JSON.parse(json);
        var lines = [];
        Object.keys(tree).forEach(function (f) { lines.push(" " + f + "  (" + tree[f].length + " B)"); });
        outBlock(lines.join("\n") || "(empty)"); wave.pulse(0.5);
      });
    }
    if (line.indexOf("novel-workflow ") === 0 || line.indexOf("nw ") === 0) {
      return pyodide.runPythonAsync("nw_run(" + JSON.stringify(line) + ")").then(function (json) {
        var r = JSON.parse(json);
        if (r.out) outBlock(r.out);
        if (r.err) outBlock(r.err, "err");
        if (r.code) appendLine(exitBadge(r.code));
        wave.pulse(r.code ? 0.6 : 1.0);
        return refreshFiles();
      });
    }
    outBlock("未识别命令：" + line.split(/\s+/)[0] + "（直接敲 novel-workflow <子命令> 即可）", "err");
    return Promise.resolve();
  }

  /* ---------------- guide step execution ---------------- */
  window.NWR = {
    canRun: function () { return mode === "live" || mode === "replay" || mode === "local"; },
    runStep: function (id) {
      var step = window.NWG.byId(id);
      if (!step) return Promise.resolve();
      if (execBusy) {
        // Already running something else: show a hint, don't double-run
        // (run-all awaits each, so its own calls go through; only direct
        // click / Enter from the user are guarded here).
        toast("上一条命令还在执行…");
        return Promise.resolve();
      }
      window.NWG.setRunning(id);
      return enqueue(function () {
        var runner = mode === "live" ? liveRunStep
          : (mode === "local" ? localRunStep : replayRunStep);
        return runner(step)
          .then(function (code) {
            if (code === 0 || code === undefined) window.NWG.setDone(id, true);
            else window.NWG.setError(id);
            return code;
          })
          .catch(function (e) {
            outBlock("error: " + (e && e.message || e), "err");
            window.NWG.setError(id);
          });
      });
    },
    reset: function () {
      return enqueue(function () {
        if (mode === "live") {
          return liveEval("nw_rm('demo')").then(function () {
            window.NWG.reset();
            wave.pulse(0.4); return refreshFiles();
          });
        }
        if (mode === "local") {
          return window.NWLocal.runSmart({}, ["__reset__"], false).then(function (r) {
            if (r.err) outBlock(r.err, "err");
            return refreshFiles();
          });
        }
        replayIdx = -1;
        window.NWG.reset();
        window.NWX.reset();
        wave.pulse(0.4);
        return refreshFiles();
      });
    }
  };

  function localRunStep(step) {
    cmdLine("~/relay $", step.display);
    if (step.id === "init" && stateCache.projectExists) {
      outBlock("项目已由本地书库初始化，继续后续步骤。\n");
      return Promise.resolve(0);
    }
    return window.NWLocal.runSmart(step.setup || {}, step.argv.slice(), step.id === "idea")
      .then(function (r) {
        if (r.out) outBlock(r.out);
        if (r.err) outBlock(r.err, "err");
        if (r.code) appendLine(exitBadge(r.code));
        wave.pulse(r.code ? 0.6 : 1.0);
        return refreshFiles().then(function () { return r.code; });
      });
  }

  function liveRunStep(step) {
    cmdLine("~/relay $", step.display);
    return writeSetup(step).then(function () {
      var argv = step.argv.slice();
      if (step.id === "idea") {
        return pyodide.runPythonAsync("nw_intake()").then(function (intake) {
          // cli.main does json.loads(ns.interview) -> must be a JSON string,
          // not a parsed object.
          argv[argv.indexOf("--interview") + 1] = intake;
          return runArgv(argv);
        });
      }
      return runArgv(argv);
    }).then(function (code) { return code; });
  }
  function writeSetup(step) {
    var setup = step.setup || {};
    var entries = Object.keys(setup);
    if (entries.length === 0) return Promise.resolve();
    var p = Promise.resolve();
    entries.forEach(function (rel) {
      p = p.then(function () {
        return pyodide.runPythonAsync(
          "nw_write(" + JSON.stringify("demo/" + rel) + ", " + JSON.stringify(setup[rel]) + ")"
        );
      });
    });
    return p;
  }
  function runArgv(argv) {
    return pyodide.runPythonAsync("nw_run_argv(" + JSON.stringify(JSON.stringify(argv)) + ")")
      .then(function (json) {
        var r = JSON.parse(json);
        if (r.out) outBlock(r.out);
        if (r.err) outBlock(r.err, "err");
        if (r.code) appendLine(exitBadge(r.code));
        wave.pulse(r.code ? 0.6 : 1.0);
        return refreshFiles().then(function () { return r.code; });
      });
  }

  /* ---------------- NWB bridge for chat (白话模式) ----------------
   * Exposes a thin, replay-aware API:
   *   getMode()           -> "booting" | "live" | "replay"
   *   runLive(setup, argv, intake) -> Promise<{code,out,err}> (live only)
   *   readState()         -> project state JSON (live + replay)
   *   refreshFiles()      -> re-pull file tree
   *   filesSnapshot()     -> current file tree object (replay)
   *   echo(cmd,out,err,code) -> write into terminal scrollback
   *   resetLive()         -> wipe demo/ (live)
   */
  function liveEval(py) { return pyodide.runPythonAsync(py); }

  /* ---- v3 · replay argv matcher (白话模式 + replay 引擎) ----
   * Tape step argv are an exact-record of the real CLI invocation. When
   * the chat builds a plan from a tape step, its argv matches one step
   * byte-for-byte, so we can play back the recorded stdout and bump
   * replayIdx so subsequent state summaries stay consistent. */
  function argvEqual(a, b) {
    if (!a || !b || a.length !== b.length) return false;
    for (var i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
    return true;
  }
  function findTapeStep(argv) {
    var tape = window.NW_TAPE && window.NW_TAPE.steps;
    if (!tape) return null;
    for (var i = 0; i < tape.length; i++) if (argvEqual(argv, tape[i].argv)) return tape[i];
    return null;
  }
  function replayRunArgv(argv) {
    if (argv[0] === "__reset__") {
      cmdLine("~/relay $", "rm -rf demo/");
      replayIdx = -1; window.NWG.reset();
      return refreshFiles().then(function () { return { code: 0, out: "", err: "" }; });
    }
    if (argv[0] === "__ls__") {
      cmdLine("~/relay $", "ls " + (argv[1] || "demo"));
      var tree = currentReplayTreeObj();
      var dirs = {};
      Object.keys(tree).forEach(function (k) {
        var top = k.split("/")[0];
        dirs[top] = (dirs[top] || 0) + 1;
      });
      var lines = Object.keys(dirs).sort().map(function (d) { return d + "/  (" + dirs[d] + ")"; });
      return Promise.resolve({ code: 0, out: lines.join("\n") + "\n", err: "" });
    }
    if (argv[0] === "__cat__") {
      cmdLine("~/relay $", "cat " + (argv[1] || ""));
      var tree2 = currentReplayTreeObj();
      var rel = (argv[1] || "").replace(/^demo\//, "");
      if (tree2[rel] === undefined) return Promise.resolve({ code: 1, out: "", err: "cat: " + (argv[1] || "") + ": no such file or directory\n" });
      return Promise.resolve({ code: 0, out: tree2[rel], err: "" });
    }
    if (argv[0] === "__tree__") {
      cmdLine("~/relay $", "tree " + (argv[1] || "demo"));
      var tree3 = currentReplayTreeObj();
      var lines3 = Object.keys(tree3).map(function (f) { return " " + f + "  (" + tree3[f].length + " B)"; });
      return Promise.resolve({ code: 0, out: lines3.join("\n") || "(empty)", err: "" });
    }
    var step = findTapeStep(argv);
    if (!step) {
      cmdLine("~/relay $", "novel-workflow " + argv.join(" "));
      outBlock("回放未录制此命令：" + argv.join(" ") + "（白话模式在 REPLAY 下只能跑录制过的引导命令）。\n", "err");
      return Promise.resolve({ code: -1, out: "", err: "unrecorded" });
    }
    return replayRunStep(step).then(function () { return { code: step.code || 0, out: step.stdout, err: "" }; });
  }
  function currentReplayTreeObj() {
    if (replayIdx < 0) return {};
    return window.NW_TAPE.steps[replayIdx].tree || {};
  }

  function liveReadState() {
    if (mode === "local") return window.NWLocal.refreshState();
    if (mode === "live") return liveEval("nw_read_state()").then(function (s) { return JSON.parse(s); });
    // replay: derive from latest tape step tree
    if (replayIdx < 0) return Promise.resolve({ projectExists: false, project: null, chapters: [] });
    return Promise.resolve(deriveReplayState());
  }
  function deriveReplayState() {
    var tree = window.NW_TAPE.steps[replayIdx].tree || {};
    var out = { projectExists: false, project: null, chapters: [] };
    if (!tree["workflow.json"]) return out;
    var proj = JSON.parse(tree["workflow.json"]);
    out.projectExists = true;
    var ol = proj.outline || {};
    out.project = {
      title: proj.title, stage: proj.stage,
      concept: (proj.concept || {}).status,
      bible: (proj.bible || {}).status,
      outline: {
        master: (ol.master || {}).status, volume: (ol.volume || {}).status, chapter: (ol.chapter || {}).status
      },
      outlineLocked: !!proj.outline_locked_at,
      chapters: proj.chapters || {}
    };
    Object.keys(tree).forEach(function (k) {
      var m = k.match(/^\.novel-workflow\/chapter-(\d+)\.json$/);
      if (m) {
        try {
          var st = JSON.parse(tree[k]);
          out.chapters.push({ chapter: st.chapter, status: st.status, title: st.title, gates: st.gates || {} });
        } catch (e) {}
      }
    });
    return out;
  }
  function liveRunCustom(setup, argv, intake) {
    // Echo command to terminal so encoding mode sees history
    var cmdStr = "novel-workflow " + argv.join(" ");
    if (argv[0] === "__reset__") cmdStr = "rm -rf demo/";
    else if (argv[0] === "__ls__") cmdStr = "ls " + (argv[1] || "demo");
    else if (argv[0] === "__cat__") cmdStr = "cat " + (argv[1] || "");
    else if (argv[0] === "__tree__") cmdStr = "tree " + (argv[1] || "demo");
    cmdLine("~/relay $", cmdStr);
    var entries = Object.keys(setup || {});
    var p = Promise.resolve();
    entries.forEach(function (rel) {
      p = p.then(function () {
        return liveEval("nw_write(" + JSON.stringify("demo/" + rel) + ", " + JSON.stringify(setup[rel]) + ")");
      });
    });
    return p.then(function () {
      // Handle special markers
      if (argv[0] === "__reset__") {
        return liveEval("nw_rm('demo')").then(function () { return refreshFiles(); }).then(function () { return { code: 0, out: "", err: "" }; });
      }
      if (argv[0] === "__ls__") {
        return liveEval("nw_ls(" + JSON.stringify(argv[1] || "demo") + ")").then(function (t) { return { code: 0, out: t, err: "" }; });
      }
      if (argv[0] === "__cat__") {
        return liveEval("nw_cat(" + JSON.stringify(argv[1] || "") + ")").then(function (t) { return { code: t.indexOf("cat:") === 0 ? 1 : 0, out: t, err: "" }; });
      }
      if (argv[0] === "__tree__") {
        return liveEval("nw_tree(" + JSON.stringify(argv[1] || "demo") + ")").then(function (j) {
          var tree = JSON.parse(j);
          var lines = Object.keys(tree).map(function (f) { return " " + f + "  (" + tree[f].length + " B)"; });
          return { code: 0, out: lines.join("\n") || "(empty)", err: "" };
        });
      }
      // normal command path
      var effectiveArgv = argv.slice();
      if (intake) {
        var i = effectiveArgv.indexOf("<INTAKE>");
        if (i >= 0) {
          return liveEval("nw_intake()").then(function (intakeStr) {
            effectiveArgv[i] = intakeStr;
            return runArgv(effectiveArgv);
          });
        }
      }
      return runArgv(effectiveArgv);
    }).then(function (r) {
      // Echo output to terminal
      if (r.out) outBlock(r.out);
      if (r.err) outBlock(r.err, "err");
      if (r.code) appendLine(exitBadge(r.code));
      wave.pulse(r.code ? 0.6 : 1.0);
      return r;
    });
  }

  window.NWB = {
    getMode: function () { return mode; },
    /* v4: readState is now SYNC (returns cached state). The cache is
     * refreshed by refreshState() after every command; chat.js can
     * call this synchronously to read the project state for the LLM
     * prompt and for the status summary without a Promise round-trip. */
    readState: function () { return stateCache; },
    refreshState: function () { return refreshState(); },
    refreshFiles: function () { return refreshFiles(); },
    filesSnapshot: function () { return window.NWX ? window.NWX.current() : null; },
    echo: function (cmd, out, err, code) {
      cmdLine("~/relay $", cmd);
      if (out) outBlock(out);
      if (err) outBlock(err, "err");
      if (code) appendLine(exitBadge(code));
    },
    /* Single command, live OR replay OR local. Queues behind any in-flight run. */
    runSmart: function (setup, argv, intake) {
      if (mode === "booting") return Promise.resolve({ code: -1, out: "", err: "engine booting" });
      if (mode === "local") return window.NWLocal.runSmart(setup, argv, intake);
      return enqueue(function () {
        if (mode === "live") return liveRunCustom(setup || {}, argv || [], !!intake);
        return replayRunArgv(argv || []);
      });
    },
    /* Multiple commands in order, stop on first non-zero exit. Queues the
     * whole sequence as one queue slot (does not interleave with other
     * enqueued work). Returns the array of per-step results plus last
     * result for convenience. */
    runSeq: function (cmds) {
      if (mode === "booting") return Promise.resolve({ results: [], last: { code: -1, out: "", err: "engine booting" } });
      if (mode === "local") return window.NWLocal.runSeq(cmds);
      return enqueue(function () {
        var results = [];
        var last = null;
        var p = Promise.resolve();
        (cmds || []).forEach(function (c) {
          p = p.then(function () {
            if (mode === "live") return liveRunCustom(c.setup || {}, c.argv || [], !!c.intake);
            return replayRunArgv(c.argv || []);
          }).then(function (r) {
            results.push(r); last = r;
            if (r.code !== 0 && r.code !== undefined) { /* short-circuit */ }
            return r;
          });
        });
        return p.then(function () { return { results: results, last: last }; });
      });
    },
    /* Back-compat: NWR-style live-only run, queued. */
    runLive: function (setup, argv, intake) {
      if (mode === "booting") return Promise.resolve({ code: -1, out: "", err: "engine booting" });
      return enqueue(function () {
        if (mode !== "live") return replayRunArgv(argv || []);
        return liveRunCustom(setup || {}, argv || [], !!intake);
      });
    }
  };

  /* ---------------- input wiring ---------------- */
  termInput.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter") {
      ev.preventDefault();
      var v = termInput.value;
      termInput.value = "";
      if (v.trim() === "") return;
      history.push(v); histIdx = history.length;
      enqueue(function () { return handleLine(v); });
    } else if (ev.key === "ArrowUp") {
      ev.preventDefault();
      if (history.length === 0) return;
      histIdx = Math.max(0, histIdx - 1);
      termInput.value = history[histIdx];
    } else if (ev.key === "ArrowDown") {
      ev.preventDefault();
      if (history.length === 0) return;
      histIdx = Math.min(history.length, histIdx + 1);
      termInput.value = history[histIdx] || "";
    }
  });
  termInput.addEventListener("focus", function () { termInput.select(); });
  document.addEventListener("click", function (ev) {
    if (mode === "booting") return;
    if (ev.target.closest("input, button, .f-row, .step")) return;
    termInput.focus();
  });

  /* ---------------- library panel (local mode) ---------------- */
  // In local mode the user can switch the active library directory or
  // pick a different book from the catalog. Public-mode SPAs (no
  // NWL_RUNTIME) leave this dormant.
  var libBookName = document.getElementById("lib-book-name");
  var libPickBtn = document.getElementById("lib-pick");
  var libListBtn = document.getElementById("lib-list");
  var libDialog = document.getElementById("lib-dialog");
  var libCloseBtn = document.getElementById("lib-close");
  var libPathInput = document.getElementById("lib-path");
  var libApplyBtn = document.getElementById("lib-apply");
  var libBrowseBtn = document.getElementById("lib-browse");
  var libRefreshBtn = document.getElementById("lib-refresh");
  var libBooks = document.getElementById("lib-books");
  var libOpenBtn = document.getElementById("lib-open");
  var libCount = document.getElementById("lib-count");
  var libPathDisplay = document.getElementById("lib-path-display");
  var libNewTitle = document.getElementById("lib-new-title");
  var libCreateBtn = document.getElementById("lib-create");
  var libStatus = document.getElementById("lib-status");
  var collisionDialog = document.getElementById("lib-collision");
  var collisionText = document.getElementById("lib-collision-text");
  var openLatestBtn = document.getElementById("lib-open-latest");
  var createCopyBtn = document.getElementById("lib-create-copy");
  var cancelCollisionBtn = document.getElementById("lib-cancel-collision");
  var pendingCollision = null;
  var selectedBookDirectory = "";
  if (localMode) document.body.classList.add("local-mode");

  function setLibStatus(text, isError) {
    if (!libStatus) return;
    libStatus.textContent = text || "";
    libStatus.classList.toggle("err", !!isError);
  }

  function refreshLibPanel() {
    if (!window.NWLocal) return;
    var cap = window.NWLocal.capabilities;
    if (cap && cap.active_directory) libBookName.textContent = cap.active_directory;
    else if (cap && cap.library) libBookName.textContent = "(选一本书)";
    else libBookName.textContent = "—";
    if (cap && cap.library) {
      libBookName.title = cap.library;
      if (libPathInput) libPathInput.value = cap.library;
      if (libPathDisplay) libPathDisplay.textContent = cap.library;
    }
  }

  var LIB_STAGE_LABELS = {
    INIT: "已立项",
    IDEA: "构思中",
    CONCEPT_APPROVED: "概念已通过",
    BIBLE_WRITTEN: "世界观已建立",
    OUTLINE_LOCKED: "大纲已锁定",
    DRAFTING: "写作中",
    READY_TO_RELEASE: "待发布",
    RELEASED: "已有章节发布"
  };

  function statusLabel(book) {
    if (book && book.released_chapter_count > 0) return "已有章节发布";
    return LIB_STAGE_LABELS[(book && book.stage) || ""] || "处理中";
  }

  function selectBookCard(directory) {
    selectedBookDirectory = directory || "";
    var cards = libBooks.querySelectorAll(".lib-book-card");
    Array.prototype.forEach.call(cards, function (card) {
      var selected = card.dataset.directory === selectedBookDirectory;
      card.setAttribute("aria-selected", selected ? "true" : "false");
    });
    libOpenBtn.disabled = !selectedBookDirectory;
  }

  function renderBookList(result) {
    if (!libBooks) return;
    libBooks.replaceChildren();
    selectedBookDirectory = "";
    var books = (result && (result.books || result.catalog)) || [];
    if (libCount) libCount.textContent = books.length + " 本创作";
    if (result && result.library) {
      libPathInput.value = result.library;
      libPathDisplay.textContent = result.library;
    }
    books.forEach(function (book) {
      var card = document.createElement("button");
      card.type = "button";
      card.className = "lib-book-card";
      card.setAttribute("role", "option");
      card.setAttribute("aria-selected", "false");
      card.dataset.directory = book.directory;
      card.title = "工作流状态：" + (book.stage || "unknown");

      var title = document.createElement("span");
      title.className = "lib-book-title";
      title.textContent = book.title || book.directory;
      var chip = document.createElement("span");
      chip.className = "lib-status-chip";
      chip.textContent = statusLabel(book);
      var meta = document.createElement("span");
      meta.className = "lib-book-meta";
      meta.textContent = (book.chapter_count || 0) + " 章 · " + book.directory;
      card.append(title, chip, meta);
      libBooks.appendChild(card);
    });
    if (books.length === 0) {
      var empty = document.createElement("div");
      empty.className = "lib-book-empty";
      empty.textContent = "这里还没有创作，可以从下方创建第一本书。";
      libBooks.appendChild(empty);
    }

    var active = window.NWLocal.capabilities && window.NWLocal.capabilities.active_directory;
    if (active && books.some(function (book) { return book.directory === active; })) {
      selectBookCard(active);
    } else {
      libOpenBtn.disabled = true;
    }
    setLibStatus(books.length ? "已读取 " + books.length + " 本创作。" : "书库为空，可以创建新书。", false);
  }

  function loadLibraryDialog() {
    if (libDialog && !libDialog.open) libDialog.showModal();
    setLibStatus("正在读取书库……", false);
    libOpenBtn.disabled = true;
    return window.NWLocal.listBooks().then(function (result) {
      renderBookList(result);
      refreshLibPanel();
      return result;
    });
  }

  function finishBookSwitch(message) {
    return window.NWLocal.refreshCapabilities()
      .then(function () { refreshLibPanel(); return refreshFiles(); })
      .then(function () { return window.NWLocal.listBooks(); })
      .then(function (result) {
        renderBookList(result);
        setLibStatus(message, false);
      });
  }

  function finishCreatedBook(result) {
    var directory = result && result.directory ? result.directory : "新创作";
    return finishBookSwitch("已打开：" + directory).then(function () {
      if (libNewTitle) libNewTitle.value = "";
      return result;
    });
  }

  function waitForCollisionDecision(title, matches) {
    if (pendingCollision) {
      return Promise.reject(new Error("已有一个同名确认正在等待处理。"));
    }
    collisionText.textContent = "已有同名创作：" + matches.map(function (item) {
      return item.directory;
    }).join("、") + "。请选择继续上次或建立新副本。";
    collisionDialog.showModal();
    return new Promise(function (resolve, reject) {
      pendingCollision = { title: title, resolve: resolve, reject: reject };
    });
  }

  function createWithDecision(title, decision) {
    setLibStatus("正在创建……", false);
    libCreateBtn.disabled = true;
    return window.NWLocal.createBook(title, decision).then(function (result) {
      if (result && result.status === "collision") {
        return waitForCollisionDecision(title, result.matches || []);
      }
      return finishCreatedBook(result);
    }).finally(function () {
      libCreateBtn.disabled = false;
    });
  }

  function resolveCollisionDecision(decision) {
    if (!pendingCollision) return;
    var pending = pendingCollision;
    pendingCollision = null;
    collisionDialog.close();
    if (!decision) {
      setLibStatus("已取消创建新书。", false);
      pending.resolve({ cancelled: true, title: pending.title });
      return;
    }
    createWithDecision(pending.title, decision).then(pending.resolve, pending.reject);
  }

  function createProjectForCommand(title) {
    return createWithDecision(title, null).then(function (result) {
      if (result && result.cancelled) {
        return { code: 0, out: "已取消创建新书。", err: "" };
      }
      var directory = result && result.directory ? result.directory : title;
      if (libDialog && libDialog.open) libDialog.close();
      return { code: 0, out: "已创建并打开：" + directory, err: "" };
    });
  }

  if (libPickBtn) libPickBtn.addEventListener("click", function () {
    if (!localMode) return;
    loadLibraryDialog().catch(function (e) { setLibStatus((e && e.message) || e, true); });
  });
  if (libListBtn) libListBtn.addEventListener("click", function () {
    if (!localMode) return;
    loadLibraryDialog().catch(function (e) { setLibStatus((e && e.message) || e, true); });
  });
  if (libBooks) libBooks.addEventListener("click", function (event) {
    var card = event.target.closest(".lib-book-card");
    if (!card || !libBooks.contains(card)) return;
    selectBookCard(card.dataset.directory);
    setLibStatus("已选择：" + card.querySelector(".lib-book-title").textContent, false);
  });
  if (libCloseBtn) libCloseBtn.addEventListener("click", function () { libDialog.close(); });
  if (libRefreshBtn) libRefreshBtn.addEventListener("click", function () {
    window.NWLocal.listBooks().then(renderBookList)
      .catch(function (e) { setLibStatus((e && e.message) || e, true); });
  });
  if (libApplyBtn) libApplyBtn.addEventListener("click", function () {
    var path = (libPathInput.value || "").trim();
    if (!path) { setLibStatus("请输入绝对书库路径。", true); return; }
    setLibStatus("正在切换书库……", false);
    window.NWLocal.setLibrary(path)
      .then(function () { refreshLibPanel(); return window.NWLocal.listBooks(); })
      .then(renderBookList)
      .catch(function (e) { setLibStatus((e && e.message) || e, true); });
  });
  if (libBrowseBtn) libBrowseBtn.addEventListener("click", function () {
    setLibStatus("等待 Windows 文件夹选择……", false);
    window.NWLocal.chooseDirectory().then(function (r) {
      if (!r || !r.selected) { setLibStatus("已取消选择。", false); return null; }
      return window.NWLocal.refreshCapabilities().then(function () {
        refreshLibPanel(); return window.NWLocal.listBooks();
      }).then(renderBookList);
    }).catch(function (e) { setLibStatus((e && e.message) || e, true); });
  });
  if (libOpenBtn) libOpenBtn.addEventListener("click", function () {
    var directory = selectedBookDirectory;
    if (!directory) { setLibStatus("请先选择一本已有创作。", true); return; }
    setLibStatus("正在打开……", false);
    window.NWLocal.openBook(directory)
      .then(function () { return finishBookSwitch("已继续：" + directory); })
      .catch(function (e) { setLibStatus((e && e.message) || e, true); });
  });
  if (libCreateBtn) libCreateBtn.addEventListener("click", function () {
    var title = (libNewTitle.value || "").trim();
    if (!title) { setLibStatus("请输入书名。", true); return; }
    createWithDecision(title, null)
      .catch(function (e) { setLibStatus((e && e.message) || e, true); });
  });
  if (openLatestBtn) openLatestBtn.addEventListener("click", function () {
    resolveCollisionDecision("open_latest");
  });
  if (createCopyBtn) createCopyBtn.addEventListener("click", function () {
    resolveCollisionDecision("create_new");
  });
  if (cancelCollisionBtn) cancelCollisionBtn.addEventListener("click", function () {
    resolveCollisionDecision(null);
  });
  if (collisionDialog) collisionDialog.addEventListener("cancel", function (event) {
    event.preventDefault();
    resolveCollisionDecision(null);
  });

  if (localMode && window.NWLocal) {
    window.NWLocal.setProjectCreator(createProjectForCommand);
  }

  /* ---------------- boot ---------------- */
  appendLine('<b>RELAY·OS</b> · novel-workflow 网页实跑器', "t-cmd");
  if (localMode) {
    appendLine("—— 本地模式：通过 launcher 直连真实 Python MCP 进程 ——", "dim");
    newline();
    setBootPhase(60);
    bootLog("检测到 NWL_RUNTIME，跳过 Pyodide 加载。", true);
    setEngine("local", "本地 MCP · 可写磁盘");
    termInput.disabled = false;
    termInput.placeholder = "本地模式：直接敲 novel-workflow 真实命令（每条命令实跑在你本机）。help / ls / cat / tree / clear";
    btnRunAll.disabled = false;
    filesModeHint.textContent = "文件状态：来自你本机 active book 目录（实时）";
    Promise.resolve()
      .then(function () { return window.NWLocal.refreshCapabilities(); })
      .then(function () { refreshLibPanel(); return refreshFiles(); })
      .then(function () { setBootPhase(100, true); wave.pulse(1.0); })
      .catch(function (e) {
        bootLog("本地 API 握手失败：" + ((e && e.message) || e), false);
      });
  } else {
    appendLine("—— 浏览器内 WASM CPython 执行仓库原版 Python CLI ——", "dim");
    newline();
    setBootPhase(15);
    bootLog("探测 WASM 引擎 (Pyodide) …", false);
    setEngine("", "BOOTING · 拉取解释器");
    pyReady = bootPyodide().catch(function (e) {
      bootLog("WASM 引擎加载失败：" + (e && e.message || e), false);
      fallbackToReplay("CDN 不可达或 WASM 加载失败");
    });
  }

  /* ---------------- v3 · mobile tab switch (≤760px) ---------------- */
  document.body.setAttribute("data-mview", "term");
  var mtabs = document.getElementById("mobile-tabs");
  if (mtabs) mtabs.addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-view]"); if (!b) return;
    document.body.setAttribute("data-mview", b.getAttribute("data-view"));
    mtabs.querySelectorAll("button").forEach(function (x) { x.classList.toggle("on", x === b); });
  });
  [document.getElementById("mode-enc"), document.getElementById("mode-whi")].forEach(function (b) {
    if (!b) return;
    b.addEventListener("click", function () {
      document.body.setAttribute("data-mview", "term");
      if (mtabs) mtabs.querySelectorAll("button").forEach(function (x) {
        x.classList.toggle("on", x.getAttribute("data-view") === "term");
      });
    });
  });

  window.NWG.init();
})();
