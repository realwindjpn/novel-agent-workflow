/* Tests for web/floating-chat.js — desktop floating chat shell.
 *
 *   node --test tests/js/test_floating_chat.mjs
 *
 * Covers the pure geometry reducer (no DOM) and a fake-DOM lifecycle
 * (open / migrate / begin-end operation / minimize / restore / destroy).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import vm from "node:vm";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const floatJsPath = resolve(__dirname, "..", ".. " , "web", "floating-chat.js");

function loadFloatApi() {
  const src = readFileSync(resolve(__dirname, "..", "..", "web", "floating-chat.js"), "utf8");
  const moduleObj = { exports: {} };
  const sandbox = {
    module: moduleObj,
    exports: moduleObj.exports,
    window: {},
    console: console,
  };
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox, { filename: "web/floating-chat.js" });
  return moduleObj.exports;
}

const floatApi = loadFloatApi();

/* ---- fake DOM helpers ---- */

function fakeDoc() {
  const nodes = new Map();
  let idc = 0;
  function makeEl(tag, id) {
    const el = {
      tagName: tag,
      id: id || null,
      children: [],
      childNodes: [],
      style: {},
      attributes: {},
      dataset: {},
      hidden: false,
      classList: { _s: new Set(), add(c){this._s.add(c);}, remove(c){this._s.delete(c);}, contains(c){return this._s.has(c);}, toggle(c,f){if(f===undefined){this._s.has(c)?this._s.delete(c):this._s.add(c);}else if(f){this._s.add(c);}else{this._s.delete(c);}} },
      _text: "",
      _html: "",
      _listeners: {},
      appendChild(c) { this.children.push(c); this.childNodes.push(c); c.parentNode = this; return c; },
      removeChild(c) { this.children = this.children.filter(x => x !== c); this.childNodes = this.childNodes.filter(x => x !== c); return c; },
      remove() { if (this.parentNode) { this.parentNode.removeChild(this); } },
      insertBefore(c, ref) { this.children.push(c); this.childNodes.push(c); c.parentNode = this; return c; },
      querySelector(sel) { return null; },
      querySelectorAll(sel) { return []; },
      setAttribute(k, v) { this.attributes[k] = v; },
      getAttribute(k) { return this.attributes[k] || null; },
      removeAttribute(k) { delete this.attributes[k]; },
      addEventListener(t, fn) { (this._listeners[t] = this._listeners[t] || []).push(fn); },
      removeEventListener(t, fn) { if (this._listeners[t]) this._listeners[t] = this._listeners[t].filter(f => f !== fn); },
      get textContent() { return this._text; },
      set textContent(v) { this._text = String(v); },
      get innerHTML() { return this._html; },
      set innerHTML(v) { this._html = String(v); this.children = []; this.childNodes = []; },
      get firstChild() { return this.childNodes[0] || null; },
      cloneNode() { return makeEl(this.tagName, this.id); },
      scrollIntoView() {},
      focus() {},
      blur() {},
      getBoundingClientRect() { return { left: 0, top: 0, width: 420, height: 560, right: 420, bottom: 560 }; },
    };
    return el;
  }
  const doc = {
    createElement(tag) { return makeEl(tag); },
    createTextNode(t) { return makeEl("#text"); },
    getElementById(id) {
      if (!nodes.has(id)) { const el = makeEl("div", id); nodes.set(id, el); }
      return nodes.get(id);
    },
    body: makeEl("body"),
    documentElement: makeEl("html"),
    head: makeEl("head"),
    querySelector(sel) { return null; },
    querySelectorAll(sel) { return []; },
    addEventListener() {},
  };
  doc.body.appendChild = function(c) { this.children.push(c); this.childNodes.push(c); c.parentNode = this; return c; };
  return doc;
}

function fakeStorage() {
  const store = {};
  return {
    getItem(k) { return k in store ? store[k] : null; },
    setItem(k, v) { store[k] = String(v); },
    removeItem(k) { delete store[k]; },
    _store: store,
  };
}

function fakeOptions(overrides) {
  const opts = Object.assign({}, overrides || {});
  opts.document = opts.document || fakeDoc();
  opts.storage = opts.storage || fakeStorage();
  opts.viewport = opts.viewport || { width: 1440, height: 900 };
  opts.onSubmit = opts.onSubmit || (function () {});
  opts.onAction = opts.onAction || (function () {});
  return opts;
}

/* ---- geometry reducer tests (pure, no DOM) ---- */

test("default and restored geometry stay inside the viewport", () => {
  assert.deepEqual(JSON.parse(JSON.stringify(floatApi.clampGeometry(null, { width: 1440, height: 900 }))),
    { width: 420, height: 560, left: 1008, top: 328 });
  // width cap = 80% viewport (1200*0.8=960); restored 900 < 960 stays 900.
  // height cap = 85% (800*0.85=680); 900 -> 680. left -50 -> EDGE 12.
  // top: 1000 clamped so top+height <= vh-EDGE (800-12=788) -> top=108.
  assert.deepEqual(JSON.parse(JSON.stringify(floatApi.clampGeometry(
    { width: 900, height: 900, left: -50, top: 1000 },
    { width: 1200, height: 800 }
  ))), { width: 900, height: 680, left: 12, top: 108 });
});

test("geometry never exceeds 80% width and 85% height of viewport", () => {
  const g = floatApi.clampGeometry(
    { width: 5000, height: 5000, left: 0, top: 0 },
    { width: 1000, height: 1000 }
  );
  assert.ok(g.width <= 800, "width capped at 80%");
  assert.ok(g.height <= 850, "height capped at 85%");
  assert.ok(g.left >= 12);
  assert.ok(g.top >= 12);
});

test("min size enforced", () => {
  const g = floatApi.clampGeometry(
    { width: 100, height: 100, left: 0, top: 0 },
    { width: 1000, height: 1000 }
  );
  assert.ok(g.width >= 340);
  assert.ok(g.height >= 360);
});

/* ---- DOM lifecycle tests ---- */

test("open shows the window and binds geometry", () => {
  const opts = fakeOptions();
  const shell = floatApi.createWindow(opts);
  shell.open("book-a");
  assert.equal(opts.document.getElementById("creative-float").hidden, false);
});

test("migration renders before source removal is acknowledged", async () => {
  const opts = fakeOptions();
  const shell = floatApi.createWindow(opts);
  const result = await shell.migrate({
    turns: [{ id: "u1", role: "user", text: "方向" }, { id: "a1", role: "assistant", text: "悬疑" }],
    pendingUserTurn: { id: "u2", role: "user", text: "继续" }
  });
  assert.equal(result.rendered, true);
  assert.deepEqual(JSON.parse(JSON.stringify(shell.messageIds())), ["u1", "a1", "u2"]);
});

test("operation nodes are unique and always removable", () => {
  const opts = fakeOptions();
  const shell = floatApi.createWindow(opts);
  shell.open("book-a");
  shell.beginOperation({ kind: "reply" });
  shell.beginOperation({ kind: "reply" });
  assert.equal(shell.busyCount(), 1);
  shell.endOperation({ kind: "reply", outcome: "error" });
  assert.equal(shell.busyCount(), 0);
});

test("minimize hides then restore reveals", () => {
  const opts = fakeOptions();
  const shell = floatApi.createWindow(opts);
  shell.open("book-a");
  shell.minimize();
  assert.equal(opts.document.getElementById("creative-float").hidden, true);
  shell.restore();
  assert.equal(opts.document.getElementById("creative-float").hidden, false);
});

test("destroy cleans up the DOM node", () => {
  const opts = fakeOptions();
  const shell = floatApi.createWindow(opts);
  shell.open("book-a");
  shell.destroy();
  // after destroy, open should recreate cleanly without error
  shell.open("book-b");
  assert.equal(opts.document.getElementById("creative-float").hidden, false);
});

test("geometry persisted after open", () => {
  const opts = fakeOptions();
  const shell = floatApi.createWindow(opts);
  shell.open("book-a");
  const raw = opts.storage.getItem("nwa.float-chat.geometry.v1");
  assert.ok(raw, "geometry key written");
  const parsed = JSON.parse(raw);
  assert.ok("width" in parsed && "height" in parsed && "left" in parsed && "top" in parsed);
});

test("beginOperation pairs with endOperation leaving no busy state on error path", () => {
  const opts = fakeOptions();
  const shell = floatApi.createWindow(opts);
  shell.open("book-a");
  shell.beginOperation({ kind: "reply" });
  shell.endOperation({ kind: "reply", outcome: "error" });
  shell.beginOperation({ kind: "compile" });
  shell.endOperation({ kind: "compile", outcome: "success" });
  assert.equal(shell.busyCount(), 0);
});
