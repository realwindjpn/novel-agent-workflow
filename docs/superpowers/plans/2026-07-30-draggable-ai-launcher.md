# Draggable AI Chat Launcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the fixed “对话” launcher with a persistent draggable “AI” button that has restrained hover/breathing feedback and never dismisses the open chat when the page outside is clicked.

**Architecture:** Keep launcher position independent from the floating-window geometry. `web/floating-chat.js` owns a pure position clamp plus the Pointer Events lifecycle, `web/app.js` supplies the existing open callback, and `web/index.html` owns the text and motion styling.

**Tech Stack:** Zero-build browser JavaScript, DOM Pointer Events, localStorage, CSS keyframes/media queries, Node `node:test`, in-app Browser QA.

---

## File map

- Modify `web/floating-chat.js`: launcher position reducer, persistence, click/drag threshold, pointer capture, resize clamp, cleanup.
- Modify `web/app.js`: replace the direct launcher click handler with `floatChat.bindLauncher()`.
- Modify `web/index.html`: `AI` label, hover/press/drag/breathing/reduced-motion styling.
- Modify `tests/js/test_floating_chat.mjs`: pure clamp and fake-DOM pointer lifecycle tests.
- Modify `tests/js/test_workbench_chat_integration.mjs`: static AI label, binding, motion, and outside-click permanence contracts.
- Modify `CHANGELOG.md`: Unreleased launcher behavior entry.

### Task 1: Launcher position and Pointer Events controller

**Files:**
- Modify: `tests/js/test_floating_chat.mjs`
- Modify: `web/floating-chat.js`

- [x] **Step 1: Add failing position and drag tests**

Add tests that exercise the public contracts directly:

```js
test("launcher position defaults bottom-right and clamps to the safe edge", () => {
  assert.deepEqual(
    JSON.parse(JSON.stringify(floatApi.clampLauncherPosition(null, { width: 1280, height: 720 }))),
    { left: 1204, top: 644 }
  );
  assert.deepEqual(
    JSON.parse(JSON.stringify(floatApi.clampLauncherPosition({ left: -40, top: 900 }, { width: 800, height: 600 }))),
    { left: 12, top: 536 }
  );
});

test("launcher drag suppresses activation and persists only on release", () => {
  const opts = fakeOptions();
  const shell = floatApi.createWindow(opts);
  const launcher = opts.document.getElementById("creative-float-launcher");
  let activations = 0;
  shell.bindLauncher(launcher, () => { activations += 1; });
  launcher.dispatch("pointerdown", pointer(1, 1210, 650));
  launcher.dispatch("pointermove", pointer(1, 900, 420));
  assert.equal(opts.storage.getItem(floatApi.LAUNCHER_STORAGE_KEY), null);
  launcher.dispatch("pointerup", pointer(1, 900, 420));
  launcher.dispatch("click", { preventDefault() {} });
  assert.equal(activations, 0);
  assert.ok(opts.storage.getItem(floatApi.LAUNCHER_STORAGE_KEY));
});

test("launcher click activates below the five-pixel drag threshold", () => {
  const opts = fakeOptions();
  const shell = floatApi.createWindow(opts);
  const launcher = opts.document.getElementById("creative-float-launcher");
  let activations = 0;
  shell.bindLauncher(launcher, () => { activations += 1; });
  launcher.dispatch("pointerdown", pointer(4, 1200, 640));
  launcher.dispatch("pointermove", pointer(4, 1203, 642));
  launcher.dispatch("pointerup", pointer(4, 1203, 642));
  launcher.dispatch("click", { detail: 1, preventDefault() {} });
  assert.equal(activations, 1);
});
```

Extend fake elements with `setPointerCapture`, `releasePointerCapture`, `hasPointerCapture`, and a fake `defaultView` resize target. The `pointer()` helper returns `{pointerId, button: 0, isPrimary: true, clientX, clientY, preventDefault(){}}`.

- [x] **Step 2: Run the focused test and observe failure**

Run:

```powershell
node --test tests/js/test_floating_chat.mjs
```

Expected: FAIL because `clampLauncherPosition`, `LAUNCHER_STORAGE_KEY`, and `bindLauncher` do not exist.

- [x] **Step 3: Implement the launcher controller**

Add these constants and pure reducer to `web/floating-chat.js`:

```js
var LAUNCHER_STORAGE_KEY = "nwa.float-launcher.position.v1";
var LAUNCHER_SIZE = 52;
var LAUNCHER_DEFAULT_GAP = 24;
var LAUNCHER_EDGE = 12;
var LAUNCHER_DRAG_THRESHOLD = 5;

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
```

Inside `createWindow()`, implement `bindLauncher(element, onActivate)` with these exact rules:

1. Read `{left, top}` from `LAUNCHER_STORAGE_KEY`, clamp it, and apply `left/top` while clearing `right/bottom`.
2. Track one primary pointer by id; ignore additional pointers.
3. Enter drag only when `Math.hypot(dx, dy) >= 5`.
4. Add `is-dragging` during drag and update clamped `left/top` on pointermove.
5. Persist only on pointerup, pointercancel, lostpointercapture, or resize—not during pointermove.
6. Suppress exactly the click produced after a drag; ordinary mouse and keyboard clicks call `onActivate()`.
7. Re-clamp and persist on window resize.
8. Return an unbind function and call it from `destroy()`.

Expose `clampLauncherPosition`, `LAUNCHER_STORAGE_KEY`, and the launcher constants from the module API.

- [x] **Step 4: Run focused tests**

Run the Step 2 command. Expected: all floating-chat tests pass.

- [x] **Step 5: Commit Task 1**

```powershell
git add web/floating-chat.js tests/js/test_floating_chat.mjs
git commit -m "feat: make AI chat launcher draggable"
```

### Task 2: AI visual treatment and application wiring

**Files:**
- Modify: `tests/js/test_workbench_chat_integration.mjs`
- Modify: `web/app.js`
- Modify: `web/index.html`
- Modify: `CHANGELOG.md`

- [x] **Step 1: Add failing static contracts**

Add assertions:

```js
test("AI launcher is draggable, animated, and independent from outside clicks", () => {
  assert.match(htmlSource, /id="creative-float-launcher"[^>]*>AI<\/button>/);
  assert.match(htmlSource, /@keyframes ai-launcher-breathe/);
  assert.match(htmlSource, /#creative-float-launcher\.is-dragging/);
  assert.match(htmlSource, /prefers-reduced-motion:[^}]+[\s\S]*#creative-float-launcher/);
  assert.match(appSource, /floatChat\.bindLauncher/);
  assert.doesNotMatch(appSource, /document\.addEventListener\("click"[\s\S]{0,300}floatChat\.minimize/);
});
```

- [x] **Step 2: Run and observe failure**

```powershell
node --test tests/js/test_workbench_chat_integration.mjs
```

Expected: FAIL because the button still says `对话`, has no launcher animation, and app wiring still uses a direct click listener.

- [x] **Step 3: Wire the controller and add motion CSS**

In `web/app.js`, replace the direct launcher click listener with:

```js
if (floatLauncher) {
  var launcherShell = ensureFloatChat();
  launcherShell.bindLauncher(floatLauncher, function () {
    var dir = window.NWLocal && window.NWLocal.capabilities
      ? window.NWLocal.capabilities.active_directory : "";
    launcherShell.open(dir || "placeholder");
  });
}
```

In `web/index.html`, change the text to `AI`. Use explicit transitions (`transform`, `border-color`, `box-shadow`, `background-color`) capped at 180ms. Add:

```css
@keyframes ai-launcher-breathe {
  0%, 100% { transform: translateY(0); box-shadow: 0 5px 18px rgba(142,123,216,.32); }
  50% { transform: translateY(-3px); box-shadow: 0 9px 26px rgba(142,123,216,.55); }
}
```

Gate hover under `@media (hover: hover) and (pointer: fine)`, pause motion while pressed or dragging, use `cursor: grab/grabbing`, and disable transform animation under `prefers-reduced-motion` while retaining border/color feedback.

Add an Unreleased CHANGELOG bullet covering draggable saved position, motion feedback, reduced-motion, and outside-click permanence.

- [x] **Step 4: Run JS regression**

```powershell
node --test tests/js/*.mjs
```

Expected: all JS tests pass.

- [x] **Step 5: Commit Task 2**

```powershell
git add CHANGELOG.md web/app.js web/index.html tests/js/test_workbench_chat_integration.mjs
git commit -m "feat: polish AI chat launcher interaction"
```

### Task 3: Real-browser acceptance and release gate

**Files:**
- Modify only if acceptance exposes a defect: files from Tasks 1–2
- Do not commit screenshots or local QA data

- [x] **Step 1: Reload the running local page**

Open `http://localhost:8080/`, reload after the code changes, and verify the title plus meaningful structured-workbench DOM and zero relevant console warnings/errors.

- [x] **Step 2: Verify pointer and persistence behavior**

At a 1280×720 desktop viewport:

1. confirm the button reads `AI`;
2. hover and visually confirm the border/glow/scale feedback;
3. drag it by more than 5px and verify the chat does not open;
4. reload and verify the new position persists;
5. click without dragging and verify the chat opens;
6. click the pipeline and terminal outside the chat and verify the chat remains visible;
7. use the explicit minimize button and verify only then it hides.

- [x] **Step 3: Verify reduced-motion and viewport clamp contracts**

Use the automated reducer tests for reduced-motion/static contracts and resize clamp. Confirm the visible button remains within the 12px viewport edge after reload.

- [x] **Step 4: Run final checks**

```powershell
node --test tests/js/*.mjs
$env:PYTHONPATH='F:\bookworkflow\src'; py -3.11 scripts\release_check.py
git diff --check
git status -sb
```

Expected: all JS tests pass, `RELEASE_CHECK_PASS`, no whitespace errors, and only the plan checkbox update remains.

- [x] **Step 5: Mark plan complete, commit, and push**

Change every completed checkbox in this plan to `[x]`, then:

```powershell
git add docs/superpowers/plans/2026-07-30-draggable-ai-launcher.md
git commit -m "docs: complete draggable AI launcher plan"
git push -u origin codex/local-mcp-library-plan
```

Expected: remote branch HEAD equals local HEAD without force-push.

## Definition of done

- The launcher reads `AI`, drags with a 5px threshold, and never misfires open after a drag.
- Position persists independently from chat-window geometry and clamps on resize.
- Hover, press, breathing, dragging, and reduced-motion states satisfy the approved design.
- Clicking outside an open chat never dismisses it.
- Focused, full JS, release, browser, and Git checks pass.
