# Changelog

## Unreleased

- Fixed the real local creative-workspace runtime: one-click launch now opens
  a per-run, non-cached local URL before tunnel readiness; the active book and
  saved conversation restore during initial boot; and the main composer routes
  ordinary text exclusively through the freeform controller instead of the
  legacy command/rule pipeline. Model setup now verifies a real completion,
  accepts common OpenAI-compatible response shapes, and passes the actual user
  text plus restored context. White mode fills the window when drawers are
  closed, and formal-state summaries no longer display literal HTML tags.
- Added a freeform creative workspace that replaces the rigid command
  translator with free-form conversation. The model and user discuss story
  ideas; confirmed proposals are compiled into the formal `idea` command
  through a two-confirmation gate (accept → plan card → execute). Per-book
  persistence (local bridge → browser → memory) with ZIP backup/import
  ensures no creative work is lost. Autonomy phrases ("你来决定") grant the
  model decision authority. Trial drafts persist without triggering formal
  chapter creation. Model failures display inline without rule-engine
  fallback. Creative routes are isolated to the local port.
- Fixed local white-language new-book creation so `init` creates and activates
  a library project instead of failing with `transport: no active book`; the
  local library chooser now uses accessible Chinese-status book cards.
- Added provider-neutral, opt-in model routing with TOML configuration and
  environment-only key names.
- Added fresh preflight semantic smoke, fallback allocation, redacted failure
  records, dynamic consultant selection, HTTP-compatible and command adapters.
- Added `model init-config`, `model smoke`, `model route-plan`, and
  `model model-ledger` CLI commands plus tests and public templates.
- Added an embedded, zero-dependency stdio MCP server (`novel-workflow mcp`):
  hand-rolled JSON-RPC 2.0 over newline-delimited frames, dual-channel errors
  (business `isError:true` vs protocol JSON-RPC errors), 21 state-machine tools,
  3 resources (state / events / chapter state), 6 prompts (one per role with
  evidence-contract text), single-source `workflow.json["limits"]` block
  shared by CLI / MCP / web runner via `core.load_limits()`, and a project
  jail that funnels `workflow.json` and `.novel-workflow/**` through
  state-machine tools only. See `docs/MCP.md` for the design and a CLI
  transcript.
- Added a persistent local book library: dated `title_YYYYMMDD[(n)]` directory
  reservation, collision-aware discovery, chapter artifact layout
  (`chapters/第NNN章_YYYYMMDD`), bounded JSON-RPC bridge to the local
  stdio MCP child, and a dual HTTP-server launcher (local `8080` MCP-backed
  and disk-writable, public `8081`/Quick Tunnel Pyodide memory-only) with
  token + Origin enforcement and isolated shutdown. `scripts/launch_web.py`
  accepts a headless mode (no `cloudflared`) for sandbox/CI smoke; the
  browser SPA exposes a collision-free `NWLocal` library adapter and a
  library panel for manual path entry, Windows folder selection, reopening,
  collision-aware creation, and normal `NWB` workflow operations. The default
  library is `<repo>/book`; MCP artifact writes preserve caller-supplied UTF-8
  bytes and LF line endings on Windows. See
  `docs/superpowers/specs/2026-07-28-local-mcp-library-design.md`.

## 0.2.0

- Six-role beginner path from one idea to released chapter.
- Idea interview, concept review/repair, story bible, master/volume/chapter outline review/repair, outline lock, chapter issue.
- Outline all-PASS gate blocks chapter issuance.
- Author Role OS prewrite evidence required before a draft is recorded.
- Editor DEAI and audience-respect evidence; reader real reading-experience evidence; both required for PASS.
- Military and science consultants may SKIP_WITH_REASON with written reason but cannot be absent.
- Repair resets affected gates to PENDING and removes stale release receipts.
- READY_TO_RELEASE distinct from RELEASED; release requires an explicit command.
- Expanded illegal-transition and false-completion tests.
- Public beginner guides in English and Chinese.
- Release gate scans tracked plus untracked public files and enforces internal file isolation.

## 0.1.0

- Initial clean-room public release.
- File-first chapter contracts and append-only events.
- Six required release gates.
- CLI, tests, templates, skills, and fictional demo.
- Security and private-coupling release checks.
