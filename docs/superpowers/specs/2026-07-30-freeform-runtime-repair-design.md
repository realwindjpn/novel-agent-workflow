# Freeform Runtime Repair Design

Date: 2026-07-30
Status: approved in conversation

## Goal

Make the shipped local creative workspace behave like the approved freeform
design during a real Windows launch: open the current build immediately,
resume the active book without asking to create it again, route ordinary input
to the creative model, show provider failures accurately, and use the full
window when the side drawers are closed.

## Confirmed failures

1. The launcher waits for the public tunnel before opening the local page and
   reuses an unchanged URL. An existing browser tab can therefore remain on an
   old document until the user refreshes it.
2. Initial local boot refreshes capabilities and files but never boots the
   active book's creative session.
3. `chat.js` still owns the composer and sends every message through the old
   JSON command translator/rule engine. The new creative controller is only
   reached by secondary toolbar buttons.
4. `creative-chat.js` passes `{input, session}` while `llm.js` expects
   `{text, context}`. The provider therefore receives an empty user message and
   no restored creative context when the new controller is used.
5. The settings connection test calls only `GET /models`; it does not verify a
   chat completion. Provider text extraction accepts only
   `message.content/message.text` and treats compatible response variants as
   empty.
6. White mode hides the side panels without replacing the three-column grid.
7. The formal-state summary passes HTML tags to a text renderer, so literal
   `<b>` markup is visible.

## Architecture

The composer has one owner and one explicit boundary:

```text
composer
  -> active local book: creative controller -> creative LLM/storage
  -> no active book or explicit formal command: legacy command helper
  -> accepted compiled proposal: legacy plan card -> MCP/core execution
```

`app.js` exposes a small `NWCW` workspace bridge containing `isActive()` and
`submit(text)`. `chat.js` keeps the DOM composer and formal plan-card machinery,
but checks this bridge before invoking any legacy LLM or keyword rule. Model
failure remains visible in the creative conversation and never falls through
to a formal pipeline command.

## Launch behavior

The launcher opens the local page as soon as the private local listener is
healthy. It appends a per-run query value so an already-open browser tab must
navigate to the current run. Local static responses use `Cache-Control:
no-store` so the HTML and zero-build JavaScript are revalidated on every
launch. Starting cloudflared continues in the background after the local page
opens and remains isolated from unrelated ngrok processes.

## Resume behavior

After the local capability handshake, `app.js` boots the creative controller
for `active_directory`. Switching books clears the rendered creative view
before restoring the selected book, preventing mixed or duplicated turns.
Opening an existing book does not call project creation and ordinary creative
text does not enter the legacy `init` flow.

## Model compatibility

The model adapter receives a normalized context:

```js
{
  text,
  autonomy,
  context: {
    book,
    turns,
    summary,
    facts,
    proposals,
    drafts
  }
}
```

Provider text extraction supports string content, array content parts,
`message.text`, `message.reasoning_content`, `choice.text`, and top-level
`output_text`. The connection test sends a minimal non-streaming chat
completion instead of treating a model-list response as proof of generation.
Errors display a typed category and HTTP/provider detail without displaying or
persisting credentials.

## Layout and rendering

White mode uses a single `minmax(0, 1fr)` main column and places the chat panel
across the complete grid. The progress and files panels remain fixed overlay
drawers when opened. Formal-state summaries stay plain text and contain no HTML
markup, avoiding both literal tags and unsafe rendering.

## Acceptance criteria

1. One-click launch opens a versioned local URL before tunnel readiness.
2. Refreshing or relaunching restores the active book's saved creative turns.
3. Ordinary creative input calls `creativeReply` exactly once and never calls
   the rule engine, `bible`, or another formal command.
4. The provider receives the real user text and restored bounded context.
5. Compatible response variants produce visible text; a genuinely empty
   response reports a specific error.
6. The connection test proves an actual completion can be generated.
7. With both drawers closed, the conversation fills the desktop width.
8. State summaries show readable plain text with no literal HTML tags.
9. Existing CLI, MCP, plan confirmation, local/public isolation, and ngrok
   independence continue to pass their regression checks.

## Non-goals

- Changing core workflow gates or allowing `bible` before concept PASS.
- Exposing the local API or credentials through the public listener.
- Managing or terminating user-owned ngrok processes.
- Replacing the provider-neutral OpenAI-compatible configuration format.
