/* web/floating-chat.js — desktop floating chat shell.
 *
 * Owns ONLY the floating window UI and its geometry state:
 * create / show / drag / resize / minimize / restore / viewport clamp /
 * busy animation and main-window record migration.
 *
 * It does NOT understand model prompts, proposal schema, or formal commands.
 * Those belong to creative-chat.js / chat.js / app.js.
 *
 *   node --test tests/js/test_floating_chat.mjs
 */
(function (global) {
  "use strict";

  var DEFAULT_SIZE = { width: 420, height: 560 };
  var MIN_SIZE = { width: 340, height: 360 };
  var EDGE = 12;
  var STORAGE_KEY = "nwa.float-chat.geometry.v1";
  var LAUNCHER_STORAGE_KEY = "nwa.float-launcher.position.v1";
  var LAUNCHER_SIZE = 52;
  var LAUNCHER_DEFAULT_GAP = 24;
  var LAUNCHER_EDGE = 12;
  var LAUNCHER_DRAG_THRESHOLD = 5;

  /* ---- pure geometry reducer (no DOM) ---- */

  function clampGeometry(restored, viewport) {
    var vw = viewport.width;
    var vh = viewport.height;
    var maxW = Math.floor(vw * 0.8);
    var maxH = Math.floor(vh * 0.85);

    var g = restored
      ? { width: restored.width, height: restored.height, left: restored.left, top: restored.top }
      : { width: DEFAULT_SIZE.width, height: DEFAULT_SIZE.height, left: 0, top: 0 };

    // cap to max
    g.width = Math.min(g.width, maxW);
    g.height = Math.min(g.height, maxH);
    // enforce min
    g.width = Math.max(g.width, MIN_SIZE.width);
    g.height = Math.max(g.height, MIN_SIZE.height);

    if (!restored) {
      // default placement: bottom-right
      g.left = vw - g.width - EDGE;
      g.top = vh - g.height - EDGE;
    }

    // clamp left/top to EDGE
    if (g.left < EDGE) g.left = EDGE;
    if (g.top < EDGE) g.top = EDGE;
    // keep right/bottom inside viewport
    if (g.left + g.width > vw - EDGE) g.left = vw - g.width - EDGE;
    if (g.top + g.height > vh - EDGE) g.top = vh - g.height - EDGE;
    // re-clamp floor
    if (g.left < EDGE) g.left = EDGE;
    if (g.top < EDGE) g.top = EDGE;

    return { width: g.width, height: g.height, left: g.left, top: g.top };
  }

  function clampLauncherPosition(saved, viewport) {
    var left = saved && Number.isFinite(saved.left)
      ? saved.left : viewport.width - LAUNCHER_SIZE - LAUNCHER_DEFAULT_GAP;
    var top = saved && Number.isFinite(saved.top)
      ? saved.top : viewport.height - LAUNCHER_SIZE - LAUNCHER_DEFAULT_GAP;
    return {
      left: Math.max(LAUNCHER_EDGE, Math.min(left, viewport.width - LAUNCHER_SIZE - LAUNCHER_EDGE)),
      top: Math.max(LAUNCHER_EDGE, Math.min(top, viewport.height - LAUNCHER_SIZE - LAUNCHER_EDGE))
    };
  }

  function readLauncherPosition(storage) {
    if (!storage) return null;
    try {
      var raw = storage.getItem(LAUNCHER_STORAGE_KEY);
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      if (!Number.isFinite(parsed.left) || !Number.isFinite(parsed.top)) return null;
      return { left: parsed.left, top: parsed.top };
    } catch (e) {
      return null;
    }
  }

  function persistLauncherPosition(storage, position) {
    if (!storage || !position) return;
    try {
      storage.setItem(LAUNCHER_STORAGE_KEY, JSON.stringify({ left: position.left, top: position.top }));
    } catch (e) {
      /* private mode / quota: position persistence is best-effort */
    }
  }

  function persistGeometry(storage, geo, minimized) {
    if (!storage) return;
    try {
      storage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          width: geo.width,
          height: geo.height,
          left: geo.left,
          top: geo.top,
          minimized: !!minimized,
        })
      );
    } catch (e) {
      /* storage may be unavailable (private mode) — geometry is best-effort */
    }
  }

  function readGeometry(storage) {
    if (!storage) return null;
    try {
      var raw = storage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var p = JSON.parse(raw);
      if (typeof p.width !== "number" || typeof p.height !== "number") return null;
      return p;
    } catch (e) {
      return null;
    }
  }

  /* ---- DOM shell ---- */

  function createWindow(options) {
    var doc = options.document;
    var storage = options.storage;
    var viewport = options.viewport;
    var onSubmit = options.onSubmit || function () {};
    var onAction = options.onAction || function () {};

    var floatEl = null;
    var messagesEl = null;
    var coverageEl = null;
    var proposalEl = null;
    var stateEl = null;
    var inputEl = null;
    var sendEl = null;
    var resizeEl = null;
    var titlebarEl = null;
    var geo = null;
    var openBookId = null;
    var busyNodes = []; // unique by kind
    var migratedIds = [];
    var bound = false;
    var geometryBound = false;
    var pointerMode = null;
    var pointerStart = null;
    var launcherUnbind = null;

    function ensureEls() {
      floatEl = doc.getElementById("creative-float");
      messagesEl = doc.getElementById("creative-float-messages");
      coverageEl = doc.getElementById("creative-float-coverage");
      proposalEl = doc.getElementById("creative-float-proposal");
      stateEl = doc.getElementById("creative-float-state");
      inputEl = doc.getElementById("creative-float-input");
      sendEl = doc.getElementById("creative-float-send");
      resizeEl = doc.getElementById("creative-float-resize");
      titlebarEl = doc.getElementById("creative-float-titlebar");
    }

    function applyGeo() {
      if (!floatEl) return;
      floatEl.style.width = geo.width + "px";
      floatEl.style.height = geo.height + "px";
      floatEl.style.left = geo.left + "px";
      floatEl.style.top = geo.top + "px";
    }

    function bindComposer() {
      if (bound) return;
      bound = true;
      if (sendEl && sendEl.addEventListener) {
        sendEl.addEventListener("click", function () {
          if (inputEl && inputEl.value) {
            onSubmit(inputEl.value);
            inputEl.value = "";
          }
        });
      }
      if (inputEl && inputEl.addEventListener) {
        inputEl.addEventListener("keydown", function (e) {
          if (e && e.key === "Enter") {
            if (inputEl.value) {
              onSubmit(inputEl.value);
              inputEl.value = "";
            }
          }
        });
      }
    }

    function pointerDown(mode, e) {
      if (e && e.button != null && e.button !== 0) return;
      if (mode === "drag" && e && e.target && e.target.closest && e.target.closest("button, input")) return;
      pointerMode = mode;
      pointerStart = {
        x: e && typeof e.clientX === "number" ? e.clientX : 0,
        y: e && typeof e.clientY === "number" ? e.clientY : 0,
        geo: { width: geo.width, height: geo.height, left: geo.left, top: geo.top }
      };
      if (e && e.preventDefault) e.preventDefault();
    }

    function pointerMove(e) {
      if (!pointerMode || !pointerStart) return;
      var x = e && typeof e.clientX === "number" ? e.clientX : pointerStart.x;
      var y = e && typeof e.clientY === "number" ? e.clientY : pointerStart.y;
      var dx = x - pointerStart.x;
      var dy = y - pointerStart.y;
      var next = pointerMode === "drag"
        ? {
            width: pointerStart.geo.width,
            height: pointerStart.geo.height,
            left: pointerStart.geo.left + dx,
            top: pointerStart.geo.top + dy
          }
        : {
            width: pointerStart.geo.width + dx,
            height: pointerStart.geo.height + dy,
            left: pointerStart.geo.left,
            top: pointerStart.geo.top
          };
      geo = clampGeometry(next, viewport);
      applyGeo();
      if (e && e.preventDefault) e.preventDefault();
    }

    function pointerUp() {
      if (!pointerMode) return;
      pointerMode = null;
      pointerStart = null;
      persistGeometry(storage, geo, !!(floatEl && floatEl.hidden));
    }

    function bindGeometry() {
      if (geometryBound) return;
      geometryBound = true;
      if (titlebarEl && titlebarEl.addEventListener) {
        titlebarEl.addEventListener("pointerdown", function (e) { pointerDown("drag", e); });
      }
      if (resizeEl && resizeEl.addEventListener) {
        resizeEl.addEventListener("pointerdown", function (e) { pointerDown("resize", e); });
      }
      if (doc && doc.addEventListener) {
        doc.addEventListener("pointermove", pointerMove);
        doc.addEventListener("pointerup", pointerUp);
        doc.addEventListener("pointercancel", pointerUp);
      }
    }

    function bindLauncher(element, onActivate) {
      if (!element) return function () {};
      if (launcherUnbind) launcherUnbind();

      var view = (doc && doc.defaultView) || global;
      var activePointerId = null;
      var start = null;
      var position = null;
      var dragging = false;
      var suppressClick = false;

      function currentViewport() {
        return {
          width: view && Number.isFinite(view.innerWidth) ? view.innerWidth : viewport.width,
          height: view && Number.isFinite(view.innerHeight) ? view.innerHeight : viewport.height
        };
      }

      function applyPosition(next) {
        position = clampLauncherPosition(next, currentViewport());
        element.style.right = "auto";
        element.style.bottom = "auto";
        element.style.left = position.left + "px";
        element.style.top = position.top + "px";
      }

      function onPointerDown(e) {
        if (activePointerId !== null) return;
        if (e && e.isPrimary === false) return;
        if (e && e.button != null && e.button !== 0) return;
        activePointerId = e && e.pointerId != null ? e.pointerId : 1;
        start = {
          x: e && Number.isFinite(e.clientX) ? e.clientX : 0,
          y: e && Number.isFinite(e.clientY) ? e.clientY : 0,
          left: position.left,
          top: position.top
        };
        dragging = false;
        element.classList.add("is-pressed");
        try {
          if (element.setPointerCapture) element.setPointerCapture(activePointerId);
        } catch (captureError) {
          /* document listeners below keep dragging usable without capture */
        }
      }

      function pointerMatches(e) {
        return activePointerId !== null && (!e || e.pointerId == null || e.pointerId === activePointerId);
      }

      function onPointerMove(e) {
        if (!pointerMatches(e) || !start) return;
        var x = e && Number.isFinite(e.clientX) ? e.clientX : start.x;
        var y = e && Number.isFinite(e.clientY) ? e.clientY : start.y;
        var dx = x - start.x;
        var dy = y - start.y;
        if (!dragging && Math.hypot(dx, dy) < LAUNCHER_DRAG_THRESHOLD) return;
        if (!dragging) {
          dragging = true;
          element.classList.remove("is-pressed");
          element.classList.add("is-dragging");
        }
        applyPosition({ left: start.left + dx, top: start.top + dy });
        if (e && e.preventDefault) e.preventDefault();
      }

      function finishPointer(e, suppressGeneratedClick) {
        if (!pointerMatches(e)) return;
        var finishedId = activePointerId;
        if (dragging) {
          persistLauncherPosition(storage, position);
          suppressClick = !!suppressGeneratedClick;
        }
        activePointerId = null;
        start = null;
        dragging = false;
        element.classList.remove("is-pressed");
        element.classList.remove("is-dragging");
        try {
          if (element.hasPointerCapture && element.hasPointerCapture(finishedId)) {
            element.releasePointerCapture(finishedId);
          }
        } catch (releaseError) {
          /* losing capture is already an end condition */
        }
      }

      function onPointerUp(e) { finishPointer(e, true); }
      function onPointerCancel(e) { finishPointer(e, false); }
      function onLostPointerCapture(e) { finishPointer(e, false); }

      function onClick(e) {
        if (suppressClick) {
          suppressClick = false;
          if (e && e.preventDefault) e.preventDefault();
          return;
        }
        if (typeof onActivate === "function") onActivate();
      }

      function onResize() {
        applyPosition(position);
        persistLauncherPosition(storage, position);
      }

      applyPosition(readLauncherPosition(storage));
      element.addEventListener("pointerdown", onPointerDown);
      element.addEventListener("pointermove", onPointerMove);
      element.addEventListener("pointerup", onPointerUp);
      element.addEventListener("pointercancel", onPointerCancel);
      element.addEventListener("lostpointercapture", onLostPointerCapture);
      element.addEventListener("click", onClick);
      if (doc && doc.addEventListener) {
        doc.addEventListener("pointermove", onPointerMove);
        doc.addEventListener("pointerup", onPointerUp);
        doc.addEventListener("pointercancel", onPointerCancel);
      }
      if (view && view.addEventListener) view.addEventListener("resize", onResize);

      launcherUnbind = function () {
        element.removeEventListener("pointerdown", onPointerDown);
        element.removeEventListener("pointermove", onPointerMove);
        element.removeEventListener("pointerup", onPointerUp);
        element.removeEventListener("pointercancel", onPointerCancel);
        element.removeEventListener("lostpointercapture", onLostPointerCapture);
        element.removeEventListener("click", onClick);
        if (doc && doc.removeEventListener) {
          doc.removeEventListener("pointermove", onPointerMove);
          doc.removeEventListener("pointerup", onPointerUp);
          doc.removeEventListener("pointercancel", onPointerCancel);
        }
        if (view && view.removeEventListener) view.removeEventListener("resize", onResize);
        launcherUnbind = null;
      };
      return launcherUnbind;
    }

    function prepareGeometry() {
      var restored = readGeometry(storage);
      geo = clampGeometry(restored, viewport);
      applyGeo();
      bindGeometry();
    }

    function open(bookId) {
      ensureEls();
      openBookId = bookId;
      prepareGeometry();
      if (floatEl) floatEl.hidden = false;
      bindComposer();
      persistGeometry(storage, geo, false);
    }

    function renderTurn(turn) {
      if (!messagesEl) return;
      if (!turn || !turn.id || migratedIds.indexOf(turn.id) >= 0) return;
      var bubble = doc.createElement("div");
      bubble.id = "float-msg-" + turn.id;
      bubble.dataset.turnId = turn.id;
      bubble.dataset.role = turn.role;
      bubble.textContent = turn.text;
      messagesEl.appendChild(bubble);
      migratedIds.push(turn.id);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function migrate(data) {
      ensureEls();
      if (!geo) prepareGeometry();
      var keepHidden = !!(data && data.preserveVisibility && floatEl && floatEl.hidden);
      if (floatEl && !keepHidden) floatEl.hidden = false;
      migratedIds = [];
      if (messagesEl) messagesEl.innerHTML = "";
      var turns = data.turns || [];
      for (var i = 0; i < turns.length; i++) renderTurn(turns[i]);
      if (data.pendingUserTurn) renderTurn(data.pendingUserTurn);
      bindComposer();
      persistGeometry(storage, geo, keepHidden);
      return { rendered: true };
    }

    function appendTurn(turn) {
      ensureEls();
      renderTurn(turn);
      return { rendered: true, id: turn && turn.id };
    }

    function restoreConversation(bookId, turns) {
      ensureEls();
      var restored = readGeometry(storage);
      if (!restored) return false;
      openBookId = bookId;
      geo = clampGeometry(restored, viewport);
      applyGeo();
      bindGeometry();
      bindComposer();
      migratedIds = [];
      if (messagesEl) messagesEl.innerHTML = "";
      (turns || []).forEach(renderTurn);
      if (floatEl) floatEl.hidden = !!restored.minimized;
      return true;
    }

    function setComposerBusy(on) {
      if (inputEl) inputEl.disabled = !!on;
      if (sendEl) sendEl.disabled = !!on;
    }

    function beginOperation(op) {
      ensureEls();
      // unique by kind — replace existing same-kind busy node
      for (var i = 0; i < busyNodes.length; i++) {
        if (busyNodes[i].kind === op.kind) return;
      }
      var node = doc.createElement("div");
      node.className = "chat-typing";
      node.dataset.kind = op.kind;
      var d1 = doc.createElement("i");
      var d2 = doc.createElement("i");
      var d3 = doc.createElement("i");
      node.appendChild(d1);
      node.appendChild(d2);
      node.appendChild(d3);
      if (messagesEl) messagesEl.appendChild(node);
      busyNodes.push({ kind: op.kind, node: node });
      setComposerBusy(true);
    }

    function endOperation(op) {
      for (var i = 0; i < busyNodes.length; i++) {
        if (busyNodes[i].kind === op.kind) {
          if (busyNodes[i].node && busyNodes[i].node.remove) busyNodes[i].node.remove();
          busyNodes.splice(i, 1);
          break;
        }
      }
      if (!busyNodes.length) setComposerBusy(false);
    }

    function cancelOperations(reason) {
      for (var i = 0; i < busyNodes.length; i++) {
        if (busyNodes[i].node && busyNodes[i].node.remove) busyNodes[i].node.remove();
      }
      busyNodes = [];
      setComposerBusy(false);
      if (reason) setState(reason === "book-switch" ? "已切换创作" : "已停止生成");
    }

    function busyCount() {
      return busyNodes.length;
    }

    function messageIds() {
      return migratedIds.slice();
    }

    function minimize() {
      ensureEls();
      cancelOperations("minimized");
      if (floatEl) floatEl.hidden = true;
      persistGeometry(storage, geo, true);
    }

    function restore() {
      ensureEls();
      if (floatEl) floatEl.hidden = false;
      persistGeometry(storage, geo, false);
    }

    function destroy() {
      cancelOperations("destroyed");
      if (launcherUnbind) launcherUnbind();
      if (floatEl && floatEl.remove) floatEl.remove();
      busyNodes = [];
      migratedIds = [];
      bound = false;
      // recreate element reference for subsequent open
      if (doc && doc.createElement) {
        // getElementById will lazily create in fake DOM; real DOM keeps it removed
      }
    }

    function renderCoverage(html) {
      if (coverageEl) coverageEl.innerHTML = html || "";
    }

    function renderProposal(html) {
      if (proposalEl) proposalEl.innerHTML = html || "";
    }

    function setState(text) {
      if (stateEl) stateEl.textContent = text || "";
    }

    return {
      open: open,
      migrate: migrate,
      appendTurn: appendTurn,
      restoreConversation: restoreConversation,
      bindLauncher: bindLauncher,
      beginOperation: beginOperation,
      endOperation: endOperation,
      cancelOperations: cancelOperations,
      busyCount: busyCount,
      messageIds: messageIds,
      minimize: minimize,
      restore: restore,
      destroy: destroy,
      renderCoverage: renderCoverage,
      renderProposal: renderProposal,
      setState: setState,
    };
  }

  var api = {
    clampGeometry: clampGeometry,
    clampLauncherPosition: clampLauncherPosition,
    createWindow: createWindow,
    DEFAULT_SIZE: DEFAULT_SIZE,
    MIN_SIZE: MIN_SIZE,
    EDGE: EDGE,
    STORAGE_KEY: STORAGE_KEY,
    LAUNCHER_STORAGE_KEY: LAUNCHER_STORAGE_KEY,
    LAUNCHER_SIZE: LAUNCHER_SIZE,
    LAUNCHER_EDGE: LAUNCHER_EDGE,
    LAUNCHER_DRAG_THRESHOLD: LAUNCHER_DRAG_THRESHOLD,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (typeof global !== "undefined") global.NWFloatChat = api;
  if (typeof window !== "undefined") window.NWFloatChat = api;
})(typeof window !== "undefined" ? window : this);
