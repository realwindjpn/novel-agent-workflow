import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const root = resolve(__dirname, "..", "..");
const chat = readFileSync(resolve(root, "web", "chat.js"), "utf8");
const app = readFileSync(resolve(root, "web", "app.js"), "utf8");

test("active creative workspace owns ordinary composer input", () => {
  const handlerStart = chat.indexOf("function handleChatSubmit()");
  const handlerEnd = chat.indexOf("chatSend.addEventListener", handlerStart);
  const handler = chat.slice(handlerStart, handlerEnd);
  const creativeRoute = handler.indexOf("window.NWCW.isActive()");
  const legacyRoute = handler.indexOf("window.NWL.tryLLM");

  assert.ok(creativeRoute >= 0, "missing active creative route");
  assert.ok(legacyRoute > creativeRoute, "legacy model runs before creative route");
  assert.match(handler, /window\.NWCW\.submit\(text\)/);
});

test("app exposes an active-book creative workspace bridge", () => {
  assert.match(app, /window\.NWCW\s*=\s*\{/);
  assert.match(app, /isActive:\s*function/);
  assert.match(app, /submit:\s*function/);
  assert.match(app, /bootCreativeForActiveBook\(\)/);
});
