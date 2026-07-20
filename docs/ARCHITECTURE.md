# Architecture

This document describes the runtime architecture of `novel-workflow`: the
project lifecycle, the chapter state machine, the six-role model, the
independence rules, the repair loop, the event trail, and the file layout.
It is the reference for contributors and for the public release scanner.

Everything is file-first and tool-neutral. There is no database, no network
call, and no provider coupling in runtime code. State lives as JSON files
under the project root; evidence lives as review artifacts the user supplies.

The optional model-routing layer is isolated in `model_adapter.py` and
`model_cli.py`. It is never needed by the core state machine. Its TOML schema
keeps keys in environment variables, supports HTTP-compatible and command
adapters, records fresh smoke timestamp/status/latency/failure, and allocates
only current semantic-response `PASS` candidates. The fixed routing surface
contains `author`, `editor`, and `reader`; consultants are selected from
genre and outline-risk signals. See `templates/model_routing.example.toml`.
No production provider/model roster is embedded. The same configured model
may be assigned to several roles, or roles may use different models. Review
independence is checked at the execution/provenance identity layer rather than
by comparing model names.

A lightweight router sits on the same provider-neutral metadata. It classifies
or accepts explicit task complexity tiers `C0` through `C3`, hard-filters
candidates by capabilities such as `text`, `vision`, `code`, `tools`, and
`long_context`, honors exact `provider`/`model` locks before automatic routing,
and otherwise sorts eligible candidates by health/quota/cost/confidence. Health
states are public enums: `unavailable`, `quota_exhausted`, `rate_limited`, and
`healthy`. The `model route-task` command emits a routing HUD trace containing
task, tier, role, provider/model, confidence, attempt, fallback, next_step, and
status; repeated route failures can be supplied as local failure counts to mark
a route `repair` before the next retry. This layer stores no keys and performs
no provider call by itself.

## 1. Two-layer state machine

The workflow separates a project-level lifecycle from a per-chapter state
machine. The chapter machine cannot start until the project reaches
`OUTLINE_LOCKED`.

### 1.1 Project lifecycle

```
IDEA
  |
  |  record_idea(summary, interview)
  v
[idea recorded]
  |
  |  review_concept(PASS)            (FAIL stays in IDEA; repair_concept rewrites)
  v
CONCEPT_REVIEWED
  |
  |  write_bible(artifact)
  v
STORY_BIBLE
  |
  |  write_outline(master, ...) -> review_outline(master, PASS)
  v
OUTLINE_MASTER
  |
  |  write_outline(volume, ...) -> review_outline(volume, PASS)
  v
OUTLINE_VOLUME
  |
  |  write_outline(chapter, ...) -> review_outline(chapter, PASS)
  v
OUTLINE_CHAPTER
  |
  |  lock_outline()   (all three levels must be PASS)
  v
OUTLINE_LOCKED   ----+----> issue_chapter(1) ... issue_chapter(N)
                     |
                     +------> chapters run independently (see 1.2)
```

Hard ordering rules enforced in `core.py`:

- `write_bible` requires `concept.status == PASS`.
- `write_outline(level)` requires the story bible written and the previous
  outline level to be `PASS`.
- `review_outline(level)` requires that level to be `WRITTEN` first.
- `lock_outline` requires every level in `(master, volume, chapter)` to be
  `PASS`. A `FAIL` or `WRITTEN` level blocks the lock.
- `issue_chapter` requires `stage == OUTLINE_LOCKED`.

A `FAIL` at the concept or any outline level is recoverable: call
`repair_concept` (re-record the idea, then re-review) or `repair_outline`
(rewrite the artifact, then re-review). Re-review that `PASS`-es moves the
stage forward.

### 1.2 Chapter state machine

Each chapter is a standalone state file at
`.novel-workflow/chapter-<n>.json`. Chapter machines are independent: you
can have chapter 3 in `RELEASED` while chapter 4 is still `IN_REVIEW`.

```
                 issue_chapter
INIT ----------> ISSUED
                   |
                   |  record_draft(artifact, prewrite_artifact, author:<id>)
                   |     (validates the Author Role OS prewrite card)
                   v
                 IN_REVIEW <-------------------------+
                   |                                |
                   |  review_chapter(gate, ...)     |
                   |  for each gate in              |
                   |  (author, editor, reader,      |
                   |   military, science)           |
                   |                                |
                   +---- any FAIL ----> BLOCKED     |
                   |                                |
                   |  all gates PASS / SKIP         |
                   +----> READY_TO_RELEASE          |
                   |                                |
                   |  release_chapter()             |
                   v                                |
                 RELEASED                           |
                   ^                                |
                   |  repair_chapter resets gates --+
                   |  and removes the stale receipt
                   |  (REWORK is implicit: a new
                   |   draft flips status back to
                   |   IN_REVIEW)
```

Statuses:

| status | meaning |
|--------|---------|
| `ISSUED` | Chapter contract recorded; no draft yet. |
| `IN_REVIEW` | Draft recorded; at least one gate is still `PENDING` or reviews in progress. |
| `BLOCKED` | At least one review gate returned `FAIL`. |
| `READY_TO_RELEASE` | Every gate is `PASS` or `SKIP_WITH_REASON`. `RELEASED` is not automatic. |
| `RELEASED` | Explicit `release_chapter` succeeded; receipt written under `releases/`. |

`RELEASED` is reached only by an explicit `release_chapter` call, never by
the last review. This is the core anti-false-completion rule: every review
may push status toward `READY_TO_RELEASE`, but only the release command flips
it to `RELEASED` and writes the receipt.

## 2. Six roles

| role | owns | evidence contract | cannot do |
|------|------|-------------------|-----------|
| `controller` | stage routing, state recording, evidence verification, blocking false completion | project and chapter state files, event trail, release receipt | author or review prose |
| `author` | the candidate draft, produced from the chapter contract plus the Author Role OS prewrite card | draft artifact and prewrite card checksum | approve review gates |
| `editor` | independent craft review: structure, pacing, prose, DEAI compliance, audience-respect | `editor:<id>` review artifact with DEAI and audience-respect evidence | share identity with the author |
| `reader` | independent real reading-experience review: clarity, immersion, fatigue, over-explanation | `reader:<id>` review artifact with reading-experience evidence | share identity with the author or editor |
| `military_consultant` | tactics, force structure, command, conflict, logistics plausibility | `military:<id>` PASS / FAIL / SKIP_WITH_REASON | be left PENDING at release |
| `science_consultant` | physical, biological, technical, world-rule plausibility | `science:<id>` PASS / FAIL / SKIP_WITH_REASON | be left PENDING at release |

Provenance is recorded as `role:identifier`. The identifier is opaque to the
core (it can be a human handle, an agent label, or a local execution tag) and
is lower-cased and compared by entity, ignoring the role prefix. Two entries
sharing an entity are treated as the same reviewer.

The identifier names the execution/review identity, not merely the base model.
Thus one underlying model can legally perform separate author, editor, and
reader calls when each call has an independent context and distinct identifier;
reusing the same identifier for self-review remains blocked.

## 3. Chapter gates

There are five chapter gates, split into review gates and domain gates.

| gate | kind | allowed verdicts | evidence required on PASS |
|------|------|------------------|---------------------------|
| `author` | review | set to PASS when a draft with a valid prewrite card is recorded | draft artifact + prewrite card |
| `editor` | review | PASS, FAIL | DEAI section + audience-respect section + `reviewed_fulltext: true` + `candidate_sha256` matching the draft + `CROSS_CHAPTER_CONSISTENCY: PASS` |
| `reader` | review | PASS, FAIL | real reading-experience, immersion, over-explanation sections + `reviewed_fulltext: true` + `candidate_sha256` matching the draft + `CROSS_CHAPTER_CONSISTENCY: PASS` |
| `military` | domain | PASS, FAIL, SKIP_WITH_REASON | for PASS: `reviewed_fulltext: true` + `candidate_sha256` matching the draft; for SKIP: a written reason |
| `science` | domain | PASS, FAIL, SKIP_WITH_REASON | for PASS: `reviewed_fulltext: true` + `candidate_sha256` matching the draft + `NUMERICAL_CONSISTENCY: PASS`; for SKIP: a written reason |

A gate is satisfied for release when it is `PASS`, or - for domain gates
only - `SKIP_WITH_REASON` with a recorded reason. `release_chapter` fails if
any gate is `PENDING` or `FAIL`.

The PASS attestation fields (`reviewed_fulltext`, `candidate_sha256`,
`CROSS_CHAPTER_CONSISTENCY`, `NUMERICAL_CONSISTENCY`) are enforced in code by
`_validate_review_evidence` at `review_chapter` time, not just by convention.
A PASS on a summary, a stale draft, or a review that skipped the
cross-chapter / numerical check is refused.

## 4. Independence

Independence is enforced on three pairs:

- `editor` reviewer must not share an entity with `author`.
- `reader` reviewer must not share an entity with `author`.
- `reader` reviewer must not share an entity with `editor`.

The author's entity comes from the `author:<id>` provenance recorded at draft
time. The check is done by `_check_independence` in `core.py`, at every
review call, and is re-checked by `validate_chapter` at release time so a
tampered state file claiming `RELEASED` with colluding reviewers is flagged.

## 5. Repair loop

A draft revision is not silent. `repair_chapter(chapter, new_draft, affected_gates)`:

1. Records the new draft artifact under the existing author provenance.
2. Resets every gate listed in `affected_gates` back to `PENDING` (the
   `author` gate is re-set automatically because the new draft re-satisfies
   it).
3. Removes the stored reviewer provenance and artifact for each reset gate,
   so re-review must be a fresh signature.
4. Deletes a stale release receipt under `releases/chapter-<n>.json`, if one
   exists.
5. Pushes a `CHAPTER_REPAIR` event with the reset gate list.
6. Flips status back to `IN_REVIEW`.

The repaired chapter then walks the normal review path again. Because the
stale receipt is deleted, a released chapter cannot silently ship a draft
that has already been superseded.

## 6. Event trail

All transitions append a single JSON line to
`.novel-workflow/events.jsonl`. Event types:

- `PROJECT_INITIALIZED`
- `IDEA_RECORDED`
- `CONCEPT_REVIEWED`
- `STORY_BIBLE_WRITTEN`
- `OUTLINE_WRITTEN`
- `OUTLINE_REVIEWED`
- `OUTLINE_LOCKED`
- `CHAPTER_ISSUED`
- `DRAFT_RECORDED`
- `CHAPTER_GATE_RECORDED`
- `CHAPTER_REPAIR`
- `CHAPTER_RELEASED`

The trail is append-only and intentionally carries no provider, model, token,
latency, or account fields. It records reviewer provenance strings exactly as
supplied, so if the user includes private data in a provenance label it ends
up in the local trail — but the trail is gitignored and never shipped in the
release.

## 7. File layout

```
<project-root>/
  workflow.json                         # project state (stage, outline, bible, idea)
  idea/idea.json                        # recorded idea + interview
  story-bible/                          # bible artifacts (user-supplied paths)
  outlines/                             # outline artifacts (user-supplied paths)
  chapters/                             # chapter contracts / drafts (user-supplied paths)
  reviews/                              # review artifacts (user-supplied paths)
  releases/chapter-<n>.json             # release receipts (written by core)
  .novel-workflow/
    events.jsonl                        # append-only event trail (gitignored)
    chapter-<n>.json                    # per-chapter state (gitignored)
```

Only `workflow.json` is tracked by the project itself; every artifact path
under `story-bible/`, `outlines/`, `chapters/`, `reviews/` is a path the user
chooses and is recorded inside `workflow.json` or the chapter state. The
`.novel-workflow/` directory is gitignored, so cloning a public example does
not leak the local event trail.

## 8. Release scanner

`scripts/release_check.py` is the public release gate. It enumerates the
files that would be published - git-tracked files plus untracked, non-ignored
files - and checks them for:

- secret-like values,
- absolute home paths (paths beginning with the system root or home
  directory, or a Windows user folder),
- external service coupling (endpoint variables, model identifier
  variables, bare web addresses, bearer tokens),
- internal working-artifact filenames appearing in tracked content (the
  write-ahead log and the release checklist covered by `.gitignore`),
- tracked internal files or directories (those same names, plus the
  `output/` directory and the local state directory).

Generic ecosystem vocabulary (`openai`, `claude`, `hermes`, `codex`,
`gemini`, `qwen`, `deepseek` and similar) is intentionally not blocked.
These are common nouns a public tutorial may legitimately use; blocking
them would produce false positives without catching real leaks. The
scanner blocks real private coupling: secret values, absolute paths,
hardcoded endpoint variables, the internal working-artifact filenames, and
the specific private project / infrastructure identifiers listed in
`_security.py`.

The CLI `check --security` command uses the same deny-list and the same
file enumeration (git-tracked plus untracked, non-ignored) so the two
surfaces cannot drift. Build artifacts (`build/`), the gitignored internal
working files, and the local state directory are not scanned by either
surface. The scanner self-excludes its own source files by path relative
to the project root, never by bare filename, so a contributor's same-named
file elsewhere is still scanned.

It then asserts the internal patterns (the write-ahead log, the release
checklist, the output directory, and the local state directory) are
ignored by `.gitignore`, runs the unit tests, and runs a CLI smoke test that
proves a chapter cannot be issued before the outline is locked. The scanner
exits 0 only when every check passes and prints `RELEASE_CHECK_PASS`.

The scanner is path-relative, not name-based: only the exact scanner source
file and the deny-list-bearing core modules self-exclude, so a contributor's
module with the same name as a core file, or a stray internal artifact in a
subdirectory, is still scanned.

## 9. Continuity and compute budget

The optional routing layer distinguishes preflight availability from runtime
continuity. Fresh semantic smoke still authorizes candidates. A route plan now
also emits a `continuity` report:

- `READY_WITH_FALLBACK`: at least two current-PASS candidates for the role.
- `READY_SINGLE_ROUTE`: runnable, but one outage can stop the role.
- `BLOCKED_NO_ROUTE`: no candidate may run.

`execute_with_fallback` is the provider-neutral runtime primitive. It attempts
only fresh-PASS candidates in configured order, redacts each failure, returns
the successful candidate plus the prior failure trail, and raises an explicit
exhausted-chain error when no route remains. It does not hide a broken role or
turn it into PASS.

Continuity also depends on checkpoints. A runner must persist each completed
role artifact and its provenance before starting the next role. On resume it
must find the first incomplete role and continue there. This prevents an
editor outage from discarding an already completed author draft, and prevents
a restart from paying again for successful role calls. The core chapter state
and review artifacts provide this durable boundary; hosted orchestration is an
external integration concern.

Compute is multiplicative across revision loops. `model budget` estimates:

`selected model roles × full passes × tokens per call`

The command reports calls and input/output/total tokens. Monetary estimates are
calculated only from optional user-supplied per-million-token prices on
candidates. Missing prices produce `pricing_complete=false` and unknown cost;
the tool never invents vendor prices. The full-pass estimate is deliberately
conservative: targeted re-review can cost less, while external retries can cost
more.

## 10. What the architecture deliberately does not do

- It does not call models. The author, editor, reader, and consultants are
  roles filled by humans or external agents; the core only records and
  verifies.
- It does not store provider names, model identifiers, API keys, cookies, or
  account state. `provider_class` is not a field; only `role:identifier`
  provenance is recorded, and the identifier is opaque to the core.
- It does not auto-release. `READY_TO_RELEASE` is a holding state; release is
  always an explicit command with a receipt.
- It does not let a `FAIL` become silent. `repair_chapter` is the only path
  out of `BLOCKED`, and it resets the affected gates so a re-review signature
  is required.

## 11. Extension points

- **Storage backend.** Everything is JSON files read and written through
  `load_json` / `save_json`. Swapping in another backend means replacing
  those helpers; the public API does not change.
- **New review gate.** Add the gate name to the chapter's `gates` map at
  issue time and to the `_derive_chapter_status` / `_gate_satisfied` helpers.
  Keep the independence rules consistent if the new gate has reviewer
  provenance.
- **Project-level stage.** Extend `PROJECT_STAGES`, add the transition in
  `core.py`, and add a CLI subcommand. Update `release_check.py`'s required
  file list only if a new public file ships.
- **Domain consultant.** The two built-in domain gates are `military` and
  `science`. Adding a third (for example `history`) means extending
  `DOMAIN_GATES` and reusing the `SKIP_WITH_REASON` semantics.
