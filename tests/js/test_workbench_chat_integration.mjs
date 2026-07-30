/* Integration contracts for the structured workbench floating chat (Task 7+8).
 *
 *   node --test tests/js/test_workbench_chat_integration.mjs
 *
 * These are source-level / static contracts: they read app.js, chat.js and
 * index.html as text and assert that the wiring exists in the right order,
 * without spinning up a browser. Runtime behavior is covered by the focused
 * unit tests for the router, controller, coverage and float shell.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const webDir = resolve(__dirname, "..", "..", "web");

const appSource = readFileSync(resolve(webDir, "app.js"), "utf8");
const chatSource = readFileSync(resolve(webDir, "chat.js"), "utf8");
const htmlSource = readFileSync(resolve(webDir, "index.html"), "utf8");

function sourceBetween(src, startMarker, endMarker) {
  const s = src.indexOf(startMarker);
  const e = src.indexOf(endMarker, s + startMarker.length);
  assert.ok(s >= 0, `start marker "${startMarker}" not found`);
  assert.ok(e > s, `end marker "${endMarker}" not found after start`);
  return src.slice(s, e);
}

test("main terminal routes command directly and natural text through quick chat", () => {
  assert.match(appSource, /conversationRouter\.classify\(v\)/);
  assert.match(appSource, /classification\.kind === "command"/);
  assert.match(appSource, /startQuickConversation\(v/);
});

test("second natural input migrates before its model reply", () => {
  const migration = sourceBetween(appSource, "function promoteQuickConversation", "function cancelConversationUi");
  assert.ok(migration.indexOf("floatChat.migrate") < migration.indexOf("creativeController.submit"),
    "floatChat.migrate must come before creativeController.submit");
  assert.ok(migration.indexOf("removeQuickConversation") > migration.indexOf("rendered"),
    "removeQuickConversation must come after migration rendered check");
});

test("structured workbench is the default surface", () => {
  // boot must NOT switch to white mode
  assert.doesNotMatch(appSource, /setMode\("white"\)[\s\S]*boot/);
  assert.match(htmlSource, /id="mode-enc" class="on"/);
});

test("NWQuickChat API exposed from chat.js", () => {
  assert.match(chatSource, /NWQuickChat/);
  assert.match(chatSource, /begin: function/);
  assert.match(chatSource, /data-quick-session/);
  assert.match(chatSource, /data-turn-id/);
});

test("quick card container exists inside the terminal panel", () => {
  assert.match(htmlSource, /id="quick-card-area"/);
});

test("successful quick reply includes a continuation hint and rejects blank cards", () => {
  assert.match(chatSource, /quick-continuation-hint/);
  assert.match(chatSource, /再发一条自然语言/);
  assert.match(appSource, /typeof reply !== "string" \|\| !reply\.trim\(\)/);
  assert.match(appSource, /\.catch\(function \(err\) \{\s*qc\.fail/);
});

test("floating replies resync persisted turns and expose errors", () => {
  assert.match(appSource, /syncFloatFromStorage/);
  assert.match(appSource, /fc\.appendTurn/);
  assert.match(appSource, /floatChat\.cancelOperations/);
});

test("floating window uses the workbench dark semantic colors", () => {
  assert.match(htmlSource, /#creative-float\s*\{[^}]*background:\s*var\(--surface-1\)/s);
  assert.match(htmlSource, /#creative-float-messages\s*>\s*\[data-role="assistant"\]\s*\{[^}]*background:\s*var\(--surface-2\)/s);
});

test("float launcher opens the float shell directly", () => {
  assert.match(appSource, /creative-float-launcher/);
  assert.match(appSource, /floatChat\.open/);
});

test("AI launcher is draggable, animated, and independent from outside clicks", () => {
  assert.match(htmlSource, /id="creative-float-launcher"[^>]*>AI<\/button>/);
  assert.match(htmlSource, /@keyframes ai-launcher-breathe/);
  assert.match(htmlSource, /#creative-float-launcher\.is-dragging/);
  assert.match(htmlSource, /@media \(hover: hover\) and \(pointer: fine\)/);
  assert.match(htmlSource, /prefers-reduced-motion:[^}]+[\s\S]*#creative-float-launcher/);
  assert.match(appSource, /floatChat\.bindLauncher/);
  assert.doesNotMatch(appSource, /document\.addEventListener\("click"[\s\S]{0,300}floatChat\.minimize/);
});

test("command path resets the conversation router", () => {
  assert.match(appSource, /conversationRouter\.reset\("command"\)/);
});

test("handoff minimizes float, scrolls to workbench, and renders plan card", () => {
  // app.js onHandoff callback must minimize the float + scroll + offerExternalPlan
  assert.match(appSource, /onHandoff/);
  assert.match(appSource, /floatChat\.minimize\(\)/);
  assert.match(appSource, /scrollIntoView/);
  assert.match(appSource, /offerExternalPlan/);
  // the plan-card execute handler in chat.js is the only runSmart caller
  assert.match(chatSource, /NWB\.runSmart/);
});

test("no core mutation before the final plan-card execute click", () => {
  // app.js must not call NWB.runSmart directly anywhere
  assert.doesNotMatch(appSource, /NWB\.runSmart/);
});
