/* Guide panel: derives 22 steps from NW_TAPE, groups them by stage, renders
 * clickable + keyboard-activatable cards. Step state icons: ✓ done, ✗ err,
 * spinner running, number idle. Reset uses a two-step armed confirm. */
(function () {
  "use strict";

  var stepsEl = document.getElementById("guide-steps");
  var btnRunAll = document.getElementById("btn-runall");
  var btnReset = document.getElementById("btn-reset");

  var RESET_ARM_WINDOW_MS = 3000;
  var resetArmedTimer = null;

  var byId = {};                       // id -> step
  var byOrder = [];                    // steps in pipeline order
  var doneSet = {};
  var errSet = {};
  var runningId = null;

  function init() {
    var tape = window.NW_TAPE;
    byOrder = (tape.steps || []).map(function (s) { byId[s.id] = s; return s; });
    render();
  }

  // State icon: spinner when running, ✓ when done, ✗ when err, index number otherwise
  function stateIco(globalIdx, s) {
    if (runningId === s.id) {
      return '<i class="spin st-ico" aria-hidden="true"></i>';
    }
    if (doneSet[s.id]) {
      return '<span class="st-ico" aria-label="已完成">✓</span>';
    }
    if (errSet[s.id]) {
      return '<span class="st-ico" aria-label="失败">✗</span>';
    }
    return String(globalIdx);
  }

  function render() {
    stepsEl.innerHTML = "";
    var byStage = {};
    byOrder.forEach(function (s) {
      (byStage[s.stage] = byStage[s.stage] || []).push(s);
    });
    var stageNames = Object.keys(byStage);
    var globalIdx = 0;
    stageNames.forEach(function (stage) {
      var block = document.createElement("div");
      block.className = "stage-block";
      var title = document.createElement("div");
      title.className = "stage-title";
      title.textContent = stage + " · " + byStage[stage].length;
      block.appendChild(title);
      byStage[stage].forEach(function (s) {
        globalIdx++;
        var card = document.createElement("div");
        card.className = "step" +
          (doneSet[s.id] ? " done" : "") +
          (errSet[s.id] ? " err" : "") +
          (runningId === s.id ? " running" : "");
        card.dataset.id = s.id;
        card.tabIndex = 0;
        card.setAttribute("role", "button");
        var aria = s.title + "（" + (doneSet[s.id] ? "已完成" : errSet[s.id] ? "失败" : runningId === s.id ? "执行中" : "待执行") + "）";
        card.setAttribute("aria-label", aria);
        card.innerHTML =
          '<div class="idx">' + stateIco(globalIdx, s) + '</div>' +
          '<div class="body">' +
            '<div class="t">' + window.NWA.escapeHtml(s.title) + '</div>' +
            '<div class="d">' + window.NWA.escapeHtml(s.desc) + '</div>' +
            '<div class="c">' + window.NWA.escapeHtml(s.display) + '</div>' +
          '</div>';
        card.addEventListener("click", function () { window.NWR.runStep(s.id); });
        card.addEventListener("keydown", function (e) {
          if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") {
            e.preventDefault();
            window.NWR.runStep(s.id);
          }
        });
        block.appendChild(card);
      });
      stepsEl.appendChild(block);
    });
  }

  function setDone(id, done) {
    if (done) { doneSet[id] = true; delete errSet[id]; }
    else { delete doneSet[id]; }
    if (runningId === id) runningId = null;
    render();
  }

  function setRunning(id) { runningId = id; render(); }

  function setError(id) {
    errSet[id] = true; delete doneSet[id];
    if (runningId === id) runningId = null;
    render();
  }

  function reset() {
    doneSet = {}; errSet = {}; runningId = null;
    render();
  }

  function disarmReset() {
    if (resetArmedTimer) { clearTimeout(resetArmedTimer); resetArmedTimer = null; }
    btnReset.classList.remove("armed");
    btnReset.textContent = "RESET";
  }

  function applyReset() {
    disarmReset();
    window.NWR.reset();
  }

  btnRunAll.addEventListener("click", async function () {
    if (btnRunAll.disabled) return;
    btnRunAll.disabled = true;
    try {
      for (var i = 0; i < byOrder.length; i++) {
        if (!doneSet[byOrder[i].id]) {
          await window.NWR.runStep(byOrder[i].id);
          await new Promise(function (r) { setTimeout(r, 350); });
        }
      }
    } finally {
      btnRunAll.disabled = !window.NWR.canRun();
    }
  });

  btnReset.addEventListener("click", function () {
    // Two-step confirm: first click arms, second click within window fires.
    if (btnReset.classList.contains("armed")) {
      applyReset();
      return;
    }
    btnReset.classList.add("armed");
    btnReset.textContent = "RESET?";
    if (resetArmedTimer) clearTimeout(resetArmedTimer);
    resetArmedTimer = setTimeout(disarmReset, RESET_ARM_WINDOW_MS);
  });

  // Cancel armed state if the user clicks anywhere else or tabs away
  document.addEventListener("click", function (e) {
    if (btnReset.classList.contains("armed") && e.target !== btnReset) {
      disarmReset();
    }
  }, true);
  btnReset.addEventListener("blur", disarmReset);

  window.NWG = {
    init: init, setDone: setDone, setRunning: setRunning,
    setError: setError, reset: reset,
    byId: function (id) { return byId[id]; }
  };
})();
