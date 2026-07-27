# Changelog

## Unreleased

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
