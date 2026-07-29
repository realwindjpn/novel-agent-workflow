# Freeform Creative Workspace Design

Date: 2026-07-30
Status: approved in conversation; awaiting written-spec review

## Goal

Turn the current white-language command translator into a real creative
workspace. The model should be free to discuss, invent, revise, compare, and
draft without exposing CLI arguments or the workflow's 15-field intake form.
The existing core remains authoritative only when the user chooses to commit a
creative decision to the formal project.

The product must preserve both qualities:

1. Creative work feels like an open conversation with a capable novelist.
2. Formal project state remains reviewable, recoverable, and protected by the
   existing MCP/core state machine.

## Problem

The current page couples four responsibilities into one LLM response:

- creative thinking;
- intent classification;
- CLI argument construction;
- strict single-line JSON serialization.

The model is prompted as a command translator, uses a conservative generation
setting, and must fit every response into a small set of JSON result kinds. A
parse, network, provider, or shape failure silently falls back to the keyword
rule engine. Consequently, open prompts such as `你来决定` can end as
`没听懂`, and the user sees a 15-field JSON form instead of creative help.

The fixed 22-step guide also occupies the main visual hierarchy while the user
is still exploring. State-machine constraints that are useful at publication
time become constraints on ideation.

## Product principles

- The model creates; the compiler structures; the core commits and validates.
- Unconfirmed material never changes `workflow.json` or formal chapter state.
- `你来决定` is explicit permission for the model to make reasonable creative
  choices and disclose its important assumptions.
- The user sees natural-language proposals, not transport schemas or raw JSON.
- Manual generation is always available; model readiness suggestions are an
  optional convenience and never a blocking dependency.
- Errors are named accurately. Creative input never silently becomes a keyword
  menu because a model call failed.
- Local persistence is preferred, but inability to write must not lose work.

## Experience model

### Default workspace

After a local book is active, the creative workspace is the default surface.
The current `白话` label becomes `自由创作`. The center conversation receives
the primary width.

The current 22-step guide becomes a collapsed `创作进度` drawer. It opens
automatically only when the user reaches a formal checkpoint such as accepting
a proposal, locking an outline, issuing a chapter, reviewing, or releasing.
The file explorer is also collapsed by default and opens when the user chooses
to inspect a proposal, draft, or formal artifact.

The composer exposes three durable actions:

- `让模型决定`: grant autonomy for the current creative choice;
- `生成创意方案`: compile the conversation at any time;
- `保存为试写`: store selected prose as an informal draft.

A save indicator is always visible and has exactly three user-facing states:

- `已写入本地`;
- `仅浏览器保存`;
- `需要下载备份`.

### Free conversation

Ordinary messages are sent to a freeform creative model. The response is plain
natural language, not a CLI plan envelope. The model may:

- ask useful creative questions;
- choose details when authorized;
- present or compare alternatives;
- challenge or replace earlier unconfirmed ideas;
- generate scenes, dialogue, voice samples, or other trial prose;
- explain assumptions and uncertainties.

Confirmed facts, explicit prohibitions, and rejected directions are injected
as hard context. Everything else remains revisable.

When the model believes the conversation is mature enough, it may suggest
generating a proposal. The manual `生成创意方案` action remains available even
if readiness detection fails or is disabled.

### Proposal confirmation

The generated proposal is a natural-language card containing:

- core idea;
- genre and intended readers;
- protagonist, desire, dilemma, and stakes;
- world and central conflict;
- likely plot direction and ending tendency;
- assumptions introduced by the model;
- references to useful trial drafts.

The card actions are:

- `确认采用并写入`;
- `继续讨论`;
- `按意见重写`;
- `放弃方案`;
- `下载备份`.

`确认采用并写入` first shows the proposed formal changes in natural language.
Only the subsequent execute confirmation invokes the existing MCP/core command.

### Trial drafts

Before outline lock, the model may freely generate prose. Such prose is stored
under the creative workspace and clearly labeled `试写`. It is not a formal
chapter, cannot satisfy a draft/review gate, and cannot be released.

A later workflow may reference or promote a trial draft, but promotion creates
a new formal chapter artifact through the existing state-machine path. It does
not silently move or reinterpret the original draft.

## Architecture

```text
Freeform creative layer
conversation / assumptions / alternatives / trial prose
                 |
                 | user requests or accepts a proposal
                 v
Structured compiler layer
validated intake / bible / outline / formal command preview
                 |
                 | explicit execute confirmation
                 v
Existing MCP and core
workflow.json / gates / chapter ledger / release evidence
```

### Creative model call

The creative call returns plain text. It receives:

- the current book identity;
- confirmed creative facts;
- rejected directions and boundaries;
- the long-term conversation summary;
- a bounded window of recent turns;
- the current user message;
- whether the user granted autonomy for this choice.

Its default generation setting should favor invention rather than command
determinism. The exact value remains configurable in the LLM settings.

The creative response is rendered immediately after escaping user-controlled
content. It is saved only after the full response succeeds.

### Readiness assessment

Readiness is deliberately separate from the creative response. A lightweight
structured assessment may run after sufficiently substantive turns and return
whether proposal generation should be offered plus a short reason. Failure of
this assessment is invisible to the conversation and never discards the model
reply. The manual proposal action is the guaranteed path.

### Structured compiler call

The compiler uses a conservative setting and a versioned schema. It converts
the saved creative context into:

- the complete core intake contract;
- a human proposal projection;
- a list of model assumptions;
- unresolved uncertainties;
- references to relevant drafts.

The compiler may fill unspecified fields with reasonable choices when the user
has granted autonomy. These choices must appear in `模型假设`. Explicit user
facts may not be overwritten.

Compiler output is validated before a proposal card is shown. One automatic
format-repair attempt is permitted. If validation still fails, the conversation
remains intact and the page reports the specific failure.

### Formal commit adapter

The existing `NWB`/`NWLocal` execution boundary remains the only route to
formal workflow mutations. The adapter receives validated compiler output and
constructs the real command only after user confirmation.

The core's required intake fields are unchanged. They become an internal commit
contract instead of a user-facing questionnaire.

## Persistence

Each local book may contain the following workspace without changing the
formal workflow schema:

```text
book-directory/
├─ workflow.json
├─ creative/
│  ├─ manifest.json
│  ├─ conversation.jsonl
│  ├─ context-summary.md
│  ├─ facts.json
│  ├─ proposals/
│  └─ drafts/
└─ chapters/
```

### Stored records

`manifest.json` records the workspace schema version, book identity, timestamps,
active proposal, and counts. `conversation.jsonl` is append-only and records
role, text, timestamp, and stable turn id. `facts.json` separates confirmed
facts, explicit boundaries, rejected directions, and user-marked important
notes.

Proposal directories contain a natural-language preview, validated compiler
data, status, source turn ids, and timestamps. Draft files are readable
Markdown with a small metadata sidecar or front matter.

### Resume behavior

Opening a book restores:

- recent conversation;
- the long-term summary;
- confirmed and rejected facts;
- the pending proposal, if any;
- trial-draft references.

The model context uses the long-term summary plus a bounded recent window so
token use does not grow without limit. The complete conversation remains on
disk. A user may mark a turn as important so summary refresh cannot remove its
meaning.

### Storage boundary

The browser never receives arbitrary filesystem write capability. Local mode
uses a dedicated creative-storage bridge scoped to the active book and the
fixed `creative/` subtree. It reuses the launcher's token, origin validation,
path jail, size ceilings, serialization queue, and active-book ownership.

Formal project files continue through MCP/core. Creative storage cannot write
`workflow.json`, chapter ledgers, release evidence, or paths outside its fixed
subtree.

Public mode has no access to local creative files. It uses browser storage when
available and otherwise keeps an in-memory session with an export warning.

## ZIP fallback and manual import

When local read/write is unavailable, the page switches to exportable-session
mode instead of blocking creative work.

The single downloaded ZIP contains:

```text
creative-backup/
├─ manifest.json
├─ conversation.jsonl
├─ context-summary.md
├─ facts.json
├─ proposals/
└─ drafts/
```

The page displays a persistent warning and a direct `下载创作备份` link. The
user may continue working in the current browser session.

`手动导入` uses a file picker and validates archive version, paths, sizes,
book identity, and required manifest fields before reading content. The import
preview shows book title, export time, turn count, proposal count, and draft
count.

If content already exists, the user must choose one of:

- merge non-conflicting records;
- import as a new creative-workspace copy;
- cancel.

Import never overwrites formal workflow files. Any subsequent formal commit
still requires proposal and execute confirmation.

## Error handling

The page distinguishes at least:

- model access not configured;
- provider or network failure;
- browser cross-origin rejection;
- request timeout;
- empty model response;
- compiler parse failure;
- compiler schema failure;
- local storage permission failure;
- local session unavailable;
- import validation failure.

The error appears next to the affected operation with a recovery action. A
model failure does not call the rule engine for open creative text. The rule
engine remains available only for explicit supported commands, simple offline
queries, and navigation help.

No error path may replace a user's creative message with `没听懂`. No failed
write may clear the unsaved buffer.

## Security and integrity

- API credentials retain the existing local-only browser storage behavior and
  are never placed in creative exports.
- All rendered model, user, filename, and imported text is escaped; formatting
  uses safe structured rendering rather than raw HTML strings.
- ZIP entries reject absolute paths, parent traversal, links, duplicate names,
  oversized files, excessive entry counts, and unsupported schema versions.
- Imported ids are de-duplicated before merge.
- Conversation append and proposal status changes are serialized.
- A proposal records the exact conversation turn ids and compiler version used
  to generate it.
- A formal commit records the accepted proposal id without making creative
  storage authoritative over core state.

## Component boundaries

### `web/llm.js`

- Split freeform creative calls from structured compiler calls.
- Stop parsing every creative reply as JSON.
- Expose detailed typed failures rather than a silent fallback result.
- Keep provider configuration and request concerns in one module.

### `web/chat.js`

- Own creative conversation, autonomy intent, proposal actions, and visible
  recovery states.
- Never route failed creative text to the keyword menu.
- Render plain replies and proposal cards safely.
- Coordinate save-after-turn without owning filesystem details.

### New creative storage adapter

- Present one interface for local bridge, browser storage, memory, ZIP export,
  and ZIP import.
- Report durability state to the UI.
- Keep the local/public implementation distinction outside chat logic.

### `web/app.js` and `web/index.html`

- Make the creative workspace the default local book surface.
- Add progress/file drawers, durable actions, proposal card layout, import,
  export, and save-state indicators.
- Preserve code mode as an advanced and diagnostic surface.

### Local launcher bridge

- Add narrowly scoped creative read, append, proposal, draft, export, and import
  operations under the active book.
- Reuse the current authentication, origin, size, queue, and path protections.
- Expose no generic path write endpoint.

### Existing core and MCP workflow

- Keep formal state transitions and validation unchanged.
- Receive only validated, user-confirmed compiler output.
- Remain independent of the browser's freeform conversation implementation.

## Migration and compatibility

Existing books without a `creative/` directory open with an empty creative
workspace. The directory is created lazily after the first successfully saved
turn. Existing `workflow.json`, chapters, and artifacts require no migration.

Code mode, CLI, and formal MCP tools retain their current behavior. A book can
be used entirely without the creative workspace.

Old browser sessions have no durable conversation to migrate. Existing formal
state remains visible and is injected as read-only context when a new creative
session begins.

## Verification

### Unit and contract tests

- A free creative reply may be arbitrary natural language and is not JSON
  parsed.
- `你来决定` sets autonomy context and produces a creative response.
- A provider/parse failure shows its reason and never invokes the keyword rule
  engine for creative text.
- Compiler validation accepts a complete contract, repairs one malformed
  response, and preserves the session after unrecoverable failure.
- Unconfirmed proposals and drafts cannot mutate formal state.
- Local creative paths cannot escape the active book's `creative/` subtree.
- ZIP export excludes credentials and formal project internals.
- ZIP import rejects traversal, links, oversized content, and invalid schemas.
- Merge behavior is deterministic and never silently overwrites.

### Browser acceptance

1. Start or open a local book and enter the free creative workspace.
2. Ask the model to decide the creative direction.
3. Verify a substantive natural-language response and no CLI/JSON/intake form.
4. Generate a proposal manually and through a model readiness suggestion.
5. Continue discussing, rewrite the proposal, then confirm it.
6. Verify the natural-language preview precedes formal execution.
7. Restart the launcher, reopen the book, and resume the same conversation.
8. Create a trial scene before outline lock and verify it is not a formal
   chapter.
9. Simulate local write failure, download one ZIP, clear browser state, import
   the ZIP, and recover the session.
10. Verify the public page cannot read the local session.
11. Verify model and storage failures show specific recovery messages.
12. Verify desktop and narrow layouts keep composer, proposal confirmation,
    progress drawer, and backup action reachable.
13. Verify formatted status text renders as formatting rather than literal HTML
    tags.

### Regression

- Run the complete JavaScript and Python suites.
- Run release and security checks.
- Run local/public isolation acceptance.
- Confirm one-click local-only startup remains compatible with a separately
  running tunnel process.

## Acceptance criteria

1. `你来决定这个创意方向` yields useful creative content rather than
   `没听懂`.
2. Normal creative conversation contains no visible CLI, JSON, or 15-field
   questionnaire.
3. The model and user can freely revise unconfirmed ideas.
4. The model may create trial prose before outline lock without creating a
   formal chapter.
5. Proposal generation is available manually and may be suggested by the model.
6. Only a two-stage proposal/execute confirmation mutates formal project state.
7. Reopening a book resumes its saved creative session.
8. Local write failure exposes a working ZIP download and manual-import path.
9. Imports are previewed, bounded, and collision-safe.
10. The 22-step pipeline is a secondary progress drawer during creation.
11. Public mode remains memory/browser-only and isolated from local files.
12. Errors are explicit and never silently masquerade as keyword
    misunderstanding.

## Non-goals

- Removing or weakening formal review, release, and overwrite protections.
- Allowing the browser arbitrary filesystem access.
- Making trial drafts releasable without promotion through formal workflow.
- Synchronizing creative sessions across different machines or accounts.
- Building collaborative multi-user editing in this change.
- Replacing the provider-neutral model configuration system.
