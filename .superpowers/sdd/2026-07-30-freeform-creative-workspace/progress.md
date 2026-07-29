# SDD ledger — plan: docs/superpowers/plans/2026-07-30-freeform-creative-workspace.md

Baseline: 646c046 feat: expose active-book creative storage
Branch: codex/local-mcp-library-plan

## Task 5 — browser storage + ZIP codec (commit f75970f)
- web/zip.js: zero-dependency ZIP encode/decode with CRC32, path traversal guard
- web/creative.js: three-backend storage adapter (local → browser → memory)
- tests/js/test_creative_adapter.mjs: 22 tests (13 NWZip + 9 NWCreative)
- index.html + launch_web.py: script + nonce wiring

## Task 6 — model call separation (commit b5af4ff)
- web/llm.js: added creativeReply, assessReadiness, compileProposal, ModelError
- tests/js/test_llm_adapter.mjs: 14 tests covering all three calls + error types
- INTAKE_KEYS (15 fields) matching core.py INTAKE_FIELD_KEYS

## Task 8 — compile confirmed proposals + formal gate (pending commit)
- Aligned formalIdeaPlan with plan spec: added setup, source, proposalId,
  resultSummary; intent="采用创意方案"
- Trial draft format: added status="trial", created_at field
- Tests already in test_creative_chat.mjs (6 tests for Task 8), all pass
- offerExternalPlan in chat.js renders plan card as second confirmation
- web/creative-chat.js: createController(ports) with state machine
  (idle → responding → compiling → proposal → committing → error)
- Autonomy detection regex, non-blocking readiness check
- Two-confirmation gate: acceptProposal → offerExternalPlan → plan card click
- formalIdeaPlan: argv carries 15-field intake JSON, cmdDisplay hides it
- Import collision: preview → merge attempt → renderImportChoices
- web/chat.js: added offerExternalPlan to window.NWC (second confirmation)
- web/index.html + launch_web.py: creative-chat.js script + nonce wiring
- tests/js/test_creative_chat.mjs: 13 tests (7 Task 7 + 5 Task 8 + 1 Task 10)
- All 87 JS tests + 9 Python tests pass
