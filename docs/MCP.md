# MCP server for novel-agent-workflow

> **Status (Unreleased, feat/mcp)** — stdio JSON-RPC 2.0 server for
> the six-role, gate-driven long-form fiction workflow. Zero runtime
> dependencies. Designed for Claude Code, Codex, and any other MCP
> client that can spawn a local stdio subprocess.

## 1. What this is, what it is not

- **It is** a thin, faithful MCP transport for the existing `novel-workflow`
  CLI surface. Every state-changing action and every read-only query is
  exposed as an MCP tool; `workflow.json` and the per-chapter state files
  are exposed as MCP resources; the six role charters are exposed as MCP
  prompts. The Python state machine in `core.py` is the single source of
  truth — the MCP server is a transport, not a parallel implementation.
- **It is not** a separate workflow engine, a hosted service, an HTTP
  API, an auth gateway, or a model router. There is no second state
  machine, no shadow database, no model integration. The repo's
  `dependencies = []` philosophy is preserved.

## 2. Why stdio, not HTTP

`stdio` is the only transport that matches how local coding agents
(Claude Code, Codex, Cursor, ...) actually run a workflow tool: they
spawn the server as a child process and speak newline-delimited
JSON-RPC 2.0 over `stdin` / `stdout`. The agent's own identity is the
authorization boundary — "who can run this subprocess" is "who can run
the agent", and the agent's own tool-use policy decides what to call.
There is no port, no network, no CORS, no auth header, no session. If
a future remote deployment is wanted, it is a separate, opt-in project
that would not live in this repo.

## 3. Wire protocol

- Transport: newline-delimited JSON (`\n` between frames, no embedded
  raw newlines inside a frame).
- Encoding: UTF-8. Every frame is a single JSON object terminated by
  `\n`. The server never writes a non-JSON byte to `stdout`.
- Notifications: the server ignores any incoming frame that lacks an
  `id` (these are `notifications/*`); it never replies to a notification.
- EOF: when `stdin` reaches EOF the server exits cleanly with return
  code 0. A parent can kill it with `SIGTERM`; that is also a clean exit.
- Logging: any diagnostic output the server writes goes to `stderr`,
  never `stdout`. `stdout` is reserved for JSON-RPC frames only.

### 3.1 Methods

| Method | Direction | Notes |
|---|---|---|
| `initialize` | client → server | Protocol version negotiation. See §3.2. |
| `notifications/initialized` | client → server | Acknowledged, no reply. |
| `ping` | client → server | Replies with `{}`. |
| `tools/list` | client → server | Static tool list (see §4). |
| `tools/call` | client → server | Dispatch a tool. Errors flow through the dual-channel error model (§5). |
| `resources/list` | client → server | Static resource templates (see §6). |
| `resources/read` | client → server | Read a `novel://...` URI. |
| `prompts/list` | client → server | Six role prompts (see §7). |
| `prompts/get` | client → server | Render a prompt with optional arguments. |

Unknown method → JSON-RPC error `-32601 Method not found`. Malformed
JSON → `-32700 Parse error`. Bad-typed params → `-32602 Invalid params`.
Internal exceptions → `-32603 Internal error` (the full traceback is
logged to `stderr`; the client only sees a short message).

### 3.2 Protocol version negotiation

The server advertises the following `SUPPORTED_VERSIONS` whitelist:

```
2025-06-18
2025-03-26
2024-11-05
```

If the client's `protocolVersion` is in the list, the server echoes it
back. If the client requests a version outside the list, the server
falls back to `2024-11-05` (the oldest supported) and returns the
fallback in the `result.protocolVersion`. The client is expected to
accept the fallback per the MCP spec's "server chooses" rule.

## 4. Tools

21 tools, all of which directly wrap a `core.py` API or the bounded
`mcp_server` write/read helpers. They are **not** shell commands; the
server never calls the `novel-workflow` CLI as a subprocess. The CLI
itself is a different transport for the same engine.

### 4.1 State-changing tools (project lifecycle)

| Tool | Wraps | Required args |
|---|---|---|
| `init` | `core.init_project` | `path`, `title` |
| `idea` | `core.record_idea` | `path`, `summary`, `interview` (object) |
| `concept_review` | `core.review_concept` | `path`, `verdict`, `artifact`, `reviewer` |
| `concept_repair` | `core.repair_concept` | `path`, `verdict`, `artifact`, `reviewer`, optional `summary` / `interview` |
| `bible` | `core.write_bible` | `path`, `artifact` |
| `outline_write` | `core.write_outline` | `path`, `level`, `artifact` |
| `outline_review` | `core.review_outline` | `path`, `level`, `verdict`, `artifact`, `reviewer` |
| `outline_repair` | `core.repair_outline` | `path`, `level`, `artifact`, `verdict`, `review_artifact`, `reviewer` |
| `outline_lock` | `core.lock_outline` | `path` |
| `issue` | `core.issue_chapter` | `path`, `chapter`, `title`, `goal` |
| `draft` | `core.record_draft` | `path`, `chapter`, `artifact`, `prewrite`, `author` |
| `review` | `core.review_chapter` | `path`, `chapter`, `gate`, `verdict`, `artifact`, `reviewer`, optional `reason` |
| `repair` | `core.repair_chapter` | `path`, `chapter`, `artifact`, `affected` (array of gate names) |
| `release` | `core.release_chapter` | `path`, `chapter` |

### 4.2 Read-only tools

| Tool | Wraps | Required args |
|---|---|---|
| `intake_check` | `core.analyze_intake` | `interview` (object) |
| `status` | `core.load_json` + validators | `path`, optional `chapter` |
| `check` | `core.validate_project` / `validate_chapter` / `core.security_scan` | `path`, optional `security` |
| `roles` | `core.SIX_ROLES` + `ROLE_CHARTER` | — |
| `chapters` | `core.list_chapters` | `path` |

### 4.3 File tools (bounded by `limits`)

| Tool | Purpose |
|---|---|
| `write_artifact` | Write a text artifact inside the project root. Rejects paths that escape the root, rejects writes to `workflow.json` and `.novel-workflow/**` (state files must be mutated through the state machine tools, not by hand), and enforces `limits.max_artifact_bytes`. |
| `read_artifact` | Read a text artifact inside the project root. Same jail and size cap, also rejects reading state files (use `resources/read` for those). |

### 4.4 Tools that are intentionally not exposed

`novel-workflow model ...` (the optional model routing layer) is **not**
exposed in the first MCP release. The model layer is opt-in, can talk
to external HTTP endpoints, and depends on a TOML config the user
maintains by hand. Exposing it as MCP tools would mix "I want to drive
my book forward" (the workflow state machine) with "I want to wire up a
provider" (an editor concern). The model CLI subcommands remain
available via the `novel-workflow model ...` shell entry point; if a
later need appears, the same `register(sub)` pattern that
`model_cli.register` uses can be lifted into a new `mcp_server.model_*`
section without touching the state-machine tools.

## 5. Dual-channel error model

This is one of the two key patterns lifted from the project owner's
`Nyaecho/ailycode-mcp` reference. Two failure surfaces:

1. **Business errors** (the workflow refused a legal request, e.g. a
   `review` call on a chapter that has no draft) → the tool returns
   `{"content": [{"type": "text", "text": "..."}], "isError": true}`.
   The JSON-RPC envelope is `200 OK` (so the agent's tool call did
   "succeed" at the transport level), and the `isError` flag tells the
   agent to treat the textual content as a refusal rather than a result.
2. **Protocol errors** (unknown method, wrong arg shape, tool name
   not in the list) → JSON-RPC error responses with the standard
   `-32601` / `-32602` codes. These are the agent's fault, not the
   workflow's.

The split keeps the agent's retry / fall-back logic clean: transport
errors should never be retried with the same arguments, workflow
errors should never be retried without changing the call.

## 6. Resources

Three static resource templates. The server returns the template list
on `resources/list`; clients read individual resources by URI.

| URI template | Reads | Returns |
|---|---|---|
| `novel://state` | `<root>/workflow.json` | The full project state document (validated). |
| `novel://events` | `<root>/.novel-workflow/events.jsonl` | The event log, tail-truncated to `limits.max_events_jsonl_bytes` (default 10 MiB) if the file is larger. |
| `novel://chapter/{chapter}` | `<root>/.novel-workflow/chapter-{n}.json` | A per-chapter state document. |

The `novel://` URI scheme is informal — it is only meaningful to this
server and is not registered. Clients should not assume any other
server recognises it.

## 7. Prompts

Six role prompts, one per role in `SIX_ROLES`. Each `prompts/get` call
returns a single `user`-role message containing the role charter plus
the evidence contract that role must satisfy when signing a gate.
The prompts are deliberately terse and reference the workflow
concepts (`role:identifier` provenance, `reviewed_fulltext: true`,
`candidate_sha256` matching the draft, `CROSS_CHAPTER_CONSISTENCY: PASS`,
`NUMERICAL_CONSISTENCY: PASS`, `SKIP_WITH_REASON` for domain gates) so
the agent can map them back to the `tools/call` shapes without
additional discovery.

## 8. Limits — one config, three surfaces

`workflow.json` carries an optional `limits` block:

```json
"limits": {
  "max_artifact_bytes": 1048576,
  "max_read_bytes": 1048576,
  "max_events_jsonl_bytes": 10485760,
  "max_chapters": 500
}
```

`core.load_limits(root)` is the single read entry point. It returns a
fully-merged dict: every field always present, missing or invalid
fields fall back to `core.DEFAULT_LIMITS`. Three surfaces consume it:

- the **MCP server** enforces it for `write_artifact`, `read_artifact`,
  the `novel://events` tail-truncation, and for refusing a new
  `issue` past `max_chapters`;
- the **CLI** uses the same loader when a future
  `novel-workflow check --limits` is added (out of scope for this
  release);
- the **web runner** (Pyodide WASM build) can call `load_limits` from
  the same `core.py` it already mounts, with no extra plumbing.

Two non-configurable invariants that belong to the engine, not to the
config file:

- `non_interactive = "deny"`: there is no silent confirm-and-proceed
  path. State transitions are explicit; recovery is `repair`, not
  auto-overwrite.
- The state file jail: `write_artifact` and `read_artifact` refuse
  `workflow.json` and `.novel-workflow/**` paths so the only way to
  mutate state is through the state machine tools.

## 9. Initialize instructions (the discipline hook)

The `initialize` response's `instructions` field is the place to put
the workflow philosophy where the agent will see it once and keep
seeing it. The current text:

- Names the six roles and the `role:identifier` provenance rule.
- States the independence rule (editor ≠ author, reader ≠ author and
  reader ≠ editor).
- States the false-completion rule (RELEASED is only ever written by
  `release_chapter`, never inferred from "last review passed").
- States the repair rule (repair resets affected gates to PENDING and
  removes stale reviewer provenance and old release receipts).
- Tells the agent to read `docs/BEGINNER_GUIDE.md` and the role's own
  `skills/<role>/SKILL.md` before producing any artifact.

This is a direct lift of the "instructions = habits" pattern from
`ailycode-mcp`. The text is short on purpose: agents that get long
instructions tend to paraphrase them away; the version here is
short enough to be quoted verbatim.

## 10. Security

- The server is a child process of the agent. The agent's sandbox is
  the sandbox.
- All disk writes are confined to the project root (jail) and bounded
  by `limits.max_artifact_bytes`. State files are unreachable via
  `write_artifact`.
- There is no network code. The MCP server never imports
  `model_adapter` and never opens a socket.
- `security_scan` (`novel-workflow check --security`) is reachable
  as a tool but only scans; it never modifies state.
- `events.jsonl` is append-only at the engine level
  (`core.append_event`); the MCP server does not change that.

## 11. Compatibility

- The server requires Python ≥ 3.11 (matches the rest of the package).
- It depends only on the package's own `core` and the Python standard
  library. `pyproject.toml` `dependencies = []` stays empty.
- It is opt-in: the existing CLI is unchanged. The new
  `novel-workflow mcp --root <project>` entry point is the only
  addition to the CLI surface.

## 12. CLI / config example

In `~/.config/claude-code/mcp.json` (or the equivalent for any other
client):

```json
{
  "mcpServers": {
    "novel-workflow": {
      "command": "novel-workflow",
      "args": ["mcp", "--root", "/path/to/mybook"]
    }
  }
}
```

The server's project root can also be a freshly-initialised empty
directory: the first tool call most projects need is `init` to create
the `workflow.json` and the standard sub-directories
(`story-bible/`, `outlines/`, `chapters/`, `reviews/`, `releases/`,
`idea/`, `assets/`).

## 13. Testing

`tests/test_mcp_server.py` covers the wire protocol and the
state-machine plumbing without needing a running agent. Cases
include protocol-version negotiation (hit + fallback), tool dispatch
with both `isError` and JSON-RPC error channels, jail enforcement for
`write_artifact` / `read_artifact`, limits enforcement, resources
(`/state`, `/events`, `/chapter/N`), prompts (`/author`, etc.),
notification silence, EOF clean shutdown, and a full end-to-end run
(init → idea → concept → bible → outline × 3 → lock → issue →
write_artifact draft/prewrite → draft → review × 5 → release) to
prove the tool schemas and the `core` API still line up.
