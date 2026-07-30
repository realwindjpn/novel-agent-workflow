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
    var geo = null;
    var openBookId = null;
    var busyNodes = []; // unique by kind
    var migratedIds = [];
    var bound = false;

    function ensureEls() {
      floatEl = doc.getElementById("creative-float");
      messagesEl = doc.getElementById("creative-float-messages");
      coverageEl = doc.getElementById("creative-float-coverage");
      proposalEl = doc.getElementById("creative-float-proposal");
      stateEl = doc.getElementById("creative-float-state");
      inputEl = doc.getElementById("creative-float-input");
      sendEl = doc.getElementById("creative-float-send");
      resizeEl = doc.getElementById("creative-float-resize");
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

    function open(bookId) {
      ensureEls();
      openBookId = bookId;
      var restored = readGeometry(storage);
      geo = clampGeometry(restored, viewport);
      applyGeo();
      if (floatEl) floatEl.hidden = false;
      bindComposer();
      persistGeometry(storage, geo, false);
    }

    function renderTurn(turn) {
      if (!messagesEl) return;
      var bubble = doc.createElement("div");
      bubble.id = "float-msg-" + turn.id;
      bubble.dataset.turnId = turn.id;
      bubble.dataset.role = turn.role;
      bubble.textContent = turn.text;
      messagesEl.appendChild(bubble);
      migratedIds.push(turn.id);
    }

    function migrate(data) {
      ensureEls();
      if (floatEl) floatEl.hidden = false;
      migratedIds = [];
      if (messagesEl) messagesEl.innerHTML = "";
      var turns = data.turns || [];
      for (var i = 0; i < turns.length; i++) renderTurn(turns[i]);
      if (data.pendingUserTurn) renderTurn(data.pendingUserTurn);
      bindComposer();
      return { rendered: true };
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
    }

    function endOperation(op) {
      for (var i = 0; i < busyNodes.length; i++) {
        if (busyNodes[i].kind === op.kind) {
          if (busyNodes[i].node && busyNodes[i].node.remove) busyNodes[i].node.remove();
          busyNodes.splice(i, 1);
          break;
        }
      }
    }

    function busyCount() {
      return busyNodes.length;
    }

    function messageIds() {
      return migratedIds.slice();
    }

    function minimize() {
      ensureEls();
      if (floatEl) floatEl.hidden = true;
      persistGeometry(storage, geo, true);
    }

    function restore() {
      ensureEls();
      if (floatEl) floatEl.hidden = false;
      persistGeometry(storage, geo, false);
    }

    function destroy() {
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
      beginOperation: beginOperation,
      endOperation: endOperation,
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
    createWindow: createWindow,
    DEFAULT_SIZE: DEFAULT_SIZE,
    MIN_SIZE: MIN_SIZE,
    EDGE: EDGE,
    STORAGE_KEY: STORAGE_KEY,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (typeof global !== "undefined") global.NWFloatChat = api;
  if (typeof window !== "undefined") window.NWFloatChat = api;
})(typeof window !== "undefined" ? window : this);
