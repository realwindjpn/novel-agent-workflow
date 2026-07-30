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

test("float launcher opens the float shell directly", () => {
  assert.match(appSource, /creative-float-launcher/);
  assert.match(appSource, /floatChat\.open/);
});

test("command path resets the conversation router", () => {
  assert.match(appSource, /conversationRouter\.reset\("command"\)/);
});
