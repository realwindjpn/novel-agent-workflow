# Novel Agent Workflow

[中文](docs/README.zh-CN.md) · [Beginner Guide](docs/BEGINNER_GUIDE.md)

[![CI](https://github.com/realwindjpn/novel-agent-workflow/actions/workflows/ci.yml/badge.svg)](https://github.com/realwindjpn/novel-agent-workflow/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](pyproject.toml)
[![Runtime deps](https://img.shields.io/badge/runtime_deps-0-green.svg)](pyproject.toml)

A file-first, tool-neutral, gate-driven workflow for taking a fiction idea from first spark to reviewed outline and chapter issue.

This project does **not** promise one-click novels. It provides contracts, role separation, review evidence, recovery state, and release gates for humans, local tools, or AI agents.

## Core product

Beginner path:

```mermaid
flowchart LR
  A[idea interview] --> B[concept review / repair]
  B --> C[story bible]
  C --> D[master outline]
  D --> E[volume outline]
  E --> F[chapter outline]
  F --> G{all outline PASS?}
  G -- no --> D
  G -- yes --> H[outline lock]
  H --> I[issue chapter]
  I --> J[author draft]
  J --> K[independent reviews]
  K --> L{all gates PASS?}
  L -- no --> M[repair]
  M --> J
  L -- yes --> N[release receipt]
```

A chapter cannot be issued until every outline level is `PASS` and the outline is locked.

## Six roles

| Role | Responsibility | Evidence contract |
|---|---|---|
| `controller` | Routes stages, records state, verifies evidence, blocks false completion. | State files, event trail, release receipt. |
| `author` | Writes a candidate draft from the chapter contract and Author Role OS prewrite card. | Draft artifact plus prewrite checksum. |
| `editor` | Independent craft review: structure, pacing, prose, DEAI, audience respect. | `editor:<id>` review with cited evidence. |
| `reader` | Independent real reading-experience review: clarity, immersion, fatigue, over-explanation. | `reader:<id>` review with cited experience. |
| `military_consultant` | Reviews tactics, force, conflict, command, logistics when applicable. | `military:<id>` PASS/FAIL or SKIP_WITH_REASON. |
| `science_consultant` | Reviews physical, biological, technical, and world-rule plausibility when applicable. | `science:<id>` PASS/FAIL or SKIP_WITH_REASON. |

Editor and reader identities must differ from the author, and the reader identity must differ from the editor. Military and science consultants may return `SKIP_WITH_REASON` when no applicable content exists, but they may not be absent.

## Chapter gates

Required chapter gates are:

- `author`: candidate draft exists and has an Author Role OS prewrite card.
- `editor`: DEAI and audience-respect evidence is present and PASS.
- `reader`: real reading-experience evidence is present and PASS.
- `military`: PASS, FAIL, or SKIP_WITH_REASON with written reason.
- `science`: PASS, FAIL, or SKIP_WITH_REASON with written reason.

When a repair changes a draft, affected gates reset to `PENDING`; stale release receipts are removed and the affected gates must be reviewed again.

## Human-friendly terminal output (opt-in)

Every command emits machine-readable JSON by default so scripts, tests, and the optional model-routing HUD keep working. For interactive use, append `--human` to inspection commands to get a colored, scannable summary. Color is auto-disabled when stdout is piped, when `NO_COLOR` is set, or when `TERM=dumb`, so CI logs and pipe-friendly automation stay clean.

```text
$ novel-workflow status demo --chapter 1 --human
── project · The Silent Relay ──────────────────────────────────────────────

  stage:        OUTLINE_LOCKED
  errors:       none

── chapter · #1 ──────────────────────────────────────────────────────────

  chapter:      #1 — First Signal
  status:       ● READY
  author:       author:noa
  editor:       ✓ PASS  editor:mal
  reader:       ✓ PASS  reader:jun
  military:     – SKIP  military:bea  — No applicable content this chapter.
  science:      – SKIP  science:kim  — No applicable content this chapter.
  errors:       none
  next:         novel-workflow release <project> 1
```

`--human` is opt-in on `status`, `check`, `chapters`, `roles`, and `intake-check`. The renderer lives in `src/novel_workflow/_visual.py`: pure stdlib, `NO_COLOR`-aware, and never embeds provider or model names in style codes. See `tests/test_visual.py` for the no-TTY and `NO_COLOR` guarantees.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .

novel-workflow init demo --title "The Silent Relay"
# Fill all 15 structured fields in templates/idea_interview.md first.
novel-workflow intake-check demo --interview '{"audience":"...","genre":"...","target_words":{"target":90000},"premise":"...","world":"...","protagonist":"...","supporting_cast":"...","central_conflict":"...","stakes":"...","character_arc":"...","style":"...","structure":"...","ending":"...","boundaries":"...","craft_patterns":["..."]}'
novel-workflow idea demo --summary "A relay crew hears an impossible signal." --interview '{complete structured intake JSON}'

printf '# Concept Review
PASS
' > demo/concept-review.md
novel-workflow concept-review demo PASS --artifact concept-review.md --reviewer controller:concept-a

printf '# Story Bible
A repair crew maintains an old relay above a moon.
' > demo/bible.md
novel-workflow bible demo --artifact bible.md

printf '# Master Outline
Story spine.
' > demo/master.md
printf '# Master Review
PASS
' > demo/master-review.md
novel-workflow outline-write demo master --artifact master.md
novel-workflow outline-review demo master PASS --artifact master-review.md --reviewer controller:master-a

printf '# Volume Outline
Volume function.
' > demo/volume.md
printf '# Volume Review
PASS
' > demo/volume-review.md
novel-workflow outline-write demo volume --artifact volume.md
novel-workflow outline-review demo volume PASS --artifact volume-review.md --reviewer controller:volume-a

printf '# Chapter Outline
Chapter function.
' > demo/chapter-outline.md
printf '# Chapter Outline Review
PASS
' > demo/chapter-outline-review.md
novel-workflow outline-write demo chapter --artifact chapter-outline.md
novel-workflow outline-review demo chapter PASS --artifact chapter-outline-review.md --reviewer controller:chapter-a

novel-workflow outline-lock demo
novel-workflow issue demo 1 --title "First Signal" --goal "Introduce the disputed signal"
```

See `docs/BEGINNER_GUIDE.md` for a full draft/review/release walkthrough.

## MCP server (Model Context Protocol)

An embedded, zero-dependency stdio MCP server ships in the same package. The
core workflow stays file-first and tool-neutral; the MCP surface is a thin
adapter that hands the state machine to any MCP-aware agent.

```bash
# Talk to the server over stdin/stdout (newline-delimited JSON-RPC 2.0).
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"demo"}}}' \
  | novel-workflow mcp
```

The server exposes:

- **21 state-machine tools** — one per public CLI command (`init`, `idea`,
  `concept-review`, `bible`, `outline-write`, `outline-review`, `outline-repair`,
  `outline-lock`, `issue`, `draft`, `review`, `repair`, `release`, `status`,
  `intake-check`, `prewrite`, `lock-check`, `read-artifact`, `write-artifact`,
  `read-chapter`, `events`), each with a full JSON Schema and the same
  evidence contract the CLI enforces.
- **3 resources** — `novel://state` (live `workflow.json`), `novel://events`
  (append-only JSONL tail), `novel://chapter/{n}` (per-chapter gate status).
- **6 prompts** — one per role (`controller`, `author`, `editor`, `reader`,
  `military_consultant`, `science_consultant`) with the role's evidence
  contract embedded in the prompt text so the agent cannot accidentally
  skip the contract.
- **Dual-channel errors** — protocol errors (parse / unknown method / missing
  params) come back as JSON-RPC errors with standard codes `-32700 / -32601 /
  -32602 / -32603`; business errors (gate not met, role:identifier
  collision, illegal transition) come back as a normal response with
  `isError: true` and a redacted message. Agents can branch on the channel.
- **Project jail** — `write-artifact` and `read-artifact` cannot touch
  `workflow.json` or `.novel-workflow/**`. Those files are only reachable
  through the state-machine tools, so the agent cannot bypass the state
  machine by writing state files directly.
- **Single-source limits** — `workflow.json["limits"]` (with defaults in
  `core.DEFAULT_LIMITS` and the unique read entry `core.load_limits()`) is
  shared by CLI, MCP, and the web runner. There is no second copy.
- **`initialize.instructions` injection** — the server returns a six-role
  philosophy text on initialize so the agent inherits the same discipline
  the CLI would have applied.

Full design, wire protocol, tool/resource/prompt catalogs, and a CLI
transcript live in [`docs/MCP.md`](docs/MCP.md). Tests are in
`tests/test_mcp_server.py` (31 cases covering protocol negotiation, the
dual-channel error model, the project jail, the full state-machine path
from idea to release, and `max_chapters` enforcement).

## Web live runner (browser SPA)

A zero-build, zero-backend browser UI ships under [`web/`](web/). It runs
the same Python package in the browser through Pyodide, so the 22-step
state machine, the gates, the `workflow.json` / `events.jsonl` file
format, and the `core.load_limits()` single-source limits are the same
on every surface. The web runner is a **third entry point** into the
same contract, not a fork.

The three entry points are independent code paths: the CLI
(`novel-workflow ...`), the MCP server (`novel-workflow mcp`), and this
web SPA. They share no runtime code — the web side does not import from
the CLI, the CLI does not import from the web. What they share is
**one core source contract**: `web/sources.js` is a verbatim snapshot of
`src/novel_workflow/*.py`, regenerated by a single script:

```bash
python scripts/gen_web_sources.py
```

Change a Python file, regenerate, and the browser catches up. The list
of mounted files at the top of `scripts/gen_web_sources.py` is the
canonical reference for what the SPA actually loads; hand-edits to
`web/sources.js` are silently overwritten. There is no second copy of
any package code, no second copy of any limit value, and no second
deny-list. The scanner, the state machine, and the limits block live
in one place each.

Two modes share the same engine and project state: **Code** (the
original 22-step walkthrough, terminal, file tree) and **Plain Chinese
(白话)** (natural-language intent layer with confirm-before-execute
cards). An optional LLM BYOK layer is opt-in: when no key is set, or
the chosen endpoint is unreachable, the runner falls back silently to
the rule-based intent engine — no degraded state, no half-promises.

### Windows one-click start (local + temporary public URL)

With Python 3.11+ and
[`cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
installed, double-click:

```text
一键启动.cmd
```

The launcher starts **two** HTTP listeners and then opens a random
`https://….trycloudflare.com` Quick Tunnel that fronts only the public one:

| URL                                | Backend                     | Purpose                                                                              |
|------------------------------------|-----------------------------|--------------------------------------------------------------------------------------|
| `http://localhost:8080` (default)  | local API + static SPA      | MCP-backed, **disk-writable**, talks to a per-book `novel-workflow mcp --root` child |
| `http://localhost:8081` (default)  | static SPA only             | Pyodide, **memory-only** — same UI, no disk writes                                    |
| `https://….trycloudflare.com`      | reverse-proxies `127.0.0.1:8081` | Temporary public read-only mirror; the local `/api/local/*` routes are 404 here |

Both pages show a runtime badge so you can never confuse the two surfaces:
**本地 MCP · 可写磁盘** vs **公网演示 · 浏览器内存**. The public URL has no
login protection: anyone with the link can access the page while the
launcher is running. Press Ctrl+C or close the launcher window to stop
both servers and the cloudflared tunnel; the launcher owns shutdown of
the MCP child, both HTTP servers, and the tunnel.

Optional command-line use:

```powershell
.\一键启动.cmd --port 9090 --public-port 9091
.\一键启动.cmd --library-root D:\MyBooks
.\一键启动.cmd --no-tunnel   # 与现有 ngrok 等穿透并行，只启动本地服务
.\一键启动.cmd --no-browser
python3 scripts/launch_web.py --help
```

Manual local-only fallback (any static server works, but it will be the
public / memory-only side — the local MCP API needs the launcher):

```bash
cd web
python3 -m http.server 8081
# open http://localhost:8081
```

Pyodide fetches its own interpreter and packages from a public CDN on
first load (~10s); subsequent loads are cached. If the WASM engine
takes too long to respond, the page falls back to a recorded Replay
mode so the flow is still explorable. See [`web/README.md`](web/README.md)
for the file layout, the snapshot refresh contract, and the mode-by-mode
behavior.

## Local MCP library and persistent workspace

The launcher keeps a **persistent local book library** on your machine and
serves the page from a real `novel-workflow mcp --root <book>` child process
(one per active book). Two surfaces share the same code path; pick the one
that matches the room you are in.

### What the library is

- Default location: `<repo>/book` (`F:\bookworkflow\book` in this checkout; override with `--library-root <path>`, e.g. `D:\MyBooks`). Each book is one immediate subdirectory containing its own `workflow.json`; symlinks, junctions, and escapes outside the library root are rejected.
- Naming: books created from the page are named `<title>_YYYYMMDD` (the date the directory was reserved). Re-creating the same title bumps the suffix: `验收书_20260728`, then `验收书_20260728(1)`, `验收书_20260728(2)`, … The page prompts you with three options when a collision is detected: *open the latest*, *create a new one*, or *cancel*.
- Titles go through a Windows-safe normaliser: trailing dots, control chars, and reserved device names (`CON`, `PRN`, …) are rewritten. The picker does not interpolate any user input into the PowerShell source.
- Reopen: pick the book from the list and the launcher starts a fresh MCP child rooted at that directory. Existing `workflow.json` / `.novel-workflow/*.json` / `chapters/` / `releases/` files are honoured; no migration step is run.
- Chapter workspaces: the first time you issue a chapter, the page creates `chapters/第NNN章_YYYYMMDD/` next to `workflow.json` (zero-padded to three digits). Subsequent prewrite / draft / review / repair writes from the page land inside that directory. Restart the launcher and the same chapter directory is picked up automatically.

### Two surfaces, one engine

| Mode          | URL                        | Engine    | Disk writes | Use it for                                                |
|---------------|----------------------------|-----------|-------------|-----------------------------------------------------------|
| Local MCP     | `http://localhost:8080`    | stdio MCP | **Yes**     | Real writing; persistent across restarts; multi-book      |
| Public replay | `http://localhost:8081`    | Pyodide   | No          | Demos; sharing a read-only link; reviewing the contract   |

The local port serves `/api/local/*` over a per-launcher token with exact
origin checks (only `http://localhost:<port>` and `http://127.0.0.1:<port>`
can mutate state). The public port has no `/api/local/*` routes; any
request there returns 404. The local API never exposes `initialize` — the
browser cannot recreate the MCP session, only call allowlisted methods
(`ping`, `tools/list`, `tools/call`, `resources/list`, `resources/read`,
`prompts/list`, `prompts/get`).

Every persisted mutation you see in the local SPA is the result of a real
MCP `tools/call` round-trip. The local API reads the catalog and a bounded
file snapshot directly, and nothing else.

### Manual controls

- **Pick library**: header `LIBRARY · 换库` button opens the Windows folder picker (PowerShell STA, fixed script body, no shell interpolation) or a manual path input on macOS / Linux. Returned path is validated to be an existing directory.
- **Create / open**: the book list is read on demand from the configured library root; `读取已有创作` repopulates the list, and `继续创作` switches the active MCP child.
- **Two MiB ceiling**: every API response is capped at 2 MiB; `workflow.json`, `.novel-workflow/*.json*`, Markdown / text artifacts, and release receipts are the only categories included. Binary or unreadable entries appear as `'<binary>'` without aborting the whole snapshot.

### Shutdown and ownership

Closing the launcher (Ctrl+C, closing the window, or `Launcher.stop()`)
runs an idempotent `LauncherResources.close()` that stops the local
session, shuts down both HTTP servers, waits for their threads, and kills
the cloudflared tunnel. The MCP child is attached to the same Windows
Job Object as `cloudflared`, so closing the launcher takes the child with
it. The launcher never touches unrelated `ngrok` processes on your
machine.

## Optional model routing

The core workflow remains offline and model-free. If you want external model
assistance, initialize a separate provider-neutral configuration:

```bash
novel-workflow model init-config model_routing.toml
novel-workflow model smoke --config model_routing.toml
novel-workflow model route-plan --config model_routing.toml \
  --genre sci-fi --risk physics --risk combat
novel-workflow model model-ledger --config model_routing.toml \
  --genre sci-fi -o model-ledger.jsonl
```

The configuration stores environment-variable names only. Every run performs
a fresh semantic-response smoke before allocating roles; old ledger results
cannot authorize a new run. Candidates may use an OpenAI-compatible HTTP
endpoint or a custom command adapter. `author`, `editor`, and `reader` are
always considered; consultant roles are selected from genre and outline-risk
signals, so military and science are not global defaults. See
`templates/model_routing.example.toml` and `templates/env.example`.

The repository does not ship or recommend a production model roster. Users
configure their own providers and models. One model may serve multiple roles,
or different models may serve different roles. Independence means separate
role executions and distinct provenance identifiers for author/editor/reader
evidence; it does not require different underlying model names.

Before an expensive run, use `model budget` to estimate selected-role calls,
input/output tokens, and (only when you supply pricing) a cost range. Revision
rounds multiply usage: five active model roles over three full passes means 15
role calls. Use `model route-plan` to inspect `continuity`: one current-PASS
candidate is `READY_SINGLE_ROUTE` and therefore at risk; two or more are
`READY_WITH_FALLBACK`. Runtime integrations should persist each completed role
before starting the next and use `execute_with_fallback` to move to the next
current-PASS candidate after a route failure. Exhausted chains must become an
explicit blocked state, never a silent hang or false completion.

For a no-network routing decision/HUD, use `model route-task`. It supports
C0-C3 tiers, capability hard filters (`text`, `vision`, `code`, `tools`,
`long_context`, etc.), exact `--provider/--model` locks, health states
`unavailable | quota_exhausted | rate_limited | healthy`, cost/quota/confidence
sorting, and `repair` status when repeated failures are supplied:

```bash
novel-workflow model route-task --config model_routing.toml \
  --task "review a long technical chapter" --role editor --tier C3 \
  --capability long_context --capability tools
```

```bash
novel-workflow model budget --config model_routing.toml \
  --genre sci-fi --risk physics --risk combat \
  --revision-rounds 3 --input-tokens-per-call 12000 \
  --output-tokens-per-call 2500
```

the CLI would have applied.

Full design, wire protocol, tool/resource/prompt catalogs, and a CLI
transcript live in [`docs/MCP.md`](docs/MCP.md). Tests are in
`tests/test_mcp_server.py` (31 cases covering protocol negotiation, the
dual-channel error model, the project jail, the full state-machine path
from idea to release, and `max_chapters` enforcement).

the CLI would have applied.

the CLI would have applied.

Full design, wire protocol, tool/resource/prompt catalogs, and a CLI
transcript live in [`docs/MCP.md`](docs/MCP.md). Tests are in
`tests/test_mcp_server.py` (31 cases covering protocol negotiation, the
dual-channel error model, the project jail, the full state-machine path
from idea to release, and `max_chapters` enforcement).

## Included

- zero-runtime-dependency Python CLI
- file-first state machine
- append-only JSONL event trail
- six-role public skills and templates
- fictional demo project
- release scanner for secrets, absolute home paths, forbidden tracked working files, tests, and CLI smoke
- browser live runner under web/ (zero-build SPA; same core source contract as CLI and MCP)

## Not included

- manuscripts or private story bibles
- account state, cookies, browser profiles, credentials, or route files
- publishing automation
- model calls or hosted service integrations
- proprietary prompts or copied third-party repository code

## Verify

```bash
python -m unittest discover -s tests -v
python scripts/release_check.py
```

## License

Apache License 2.0. See [LICENSE](LICENSE), [NOTICE](NOTICE), and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
