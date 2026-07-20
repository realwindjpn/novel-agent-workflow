---
name: long-fiction-workflow
description: Build or revise long-form fiction with a six-role, gate-driven workflow that takes a beginner from one idea to a reviewed outline, chapter issue, draft, independent review, repair, and release receipt.
---

# Long Fiction Workflow (Six-Role, Gate-Driven)

This skill is the public, tool-neutral core of the repository. It is designed for a beginner who has **one idea** and wants a safe route to **one released chapter** without skipping gates.

## The six roles

| Role | Owns | Cannot do |
|------|------|-----------|
| controller | stage routing, state recording, evidence verification, false-completion blocking | author or review prose |
| author | candidate draft from a chapter contract and Author Role OS prewrite card | approve gates |
| editor | independent structure / pacing / prose / DEAI / audience-respect review | share identity with author |
| reader | independent real reading-experience review | share identity with author or editor |
| military_consultant | tactics, force, command, conflict, logistics plausibility | be absent; may SKIP_WITH_REASON |
| science_consultant | physical, biological, technical, and world-rule plausibility | be absent; may SKIP_WITH_REASON |

Independence is enforced by provenance: `role:identifier`. The editor and reader identifiers must differ from the author identifier; reader must also differ from editor.

## Project lifecycle

```
IDEA
  -> idea interview
  -> concept review (+ repair if FAIL)
  -> story bible
  -> master outline  -> review (+ repair)
  -> volume outline  -> review (+ repair)
  -> chapter outline -> review (+ repair)
  -> OUTLINE_LOCKED
  -> chapter issued
  -> draft recorded (with Author Role OS prewrite card)
  -> editor / reader review
  -> military / science review (PASS, FAIL, or SKIP_WITH_REASON)
  -> READY_TO_RELEASE
  -> RELEASED by explicit command
```

## Hard gates

1. No story bible before concept PASS.
2. No outline level before the previous level is PASS.
3. No chapter issuance before OUTLINE_LOCKED.
4. No draft before a chapter is issued.
5. No draft without Author Role OS prewrite evidence.
6. No chapter review before a draft exists.
7. No RELEASED until every chapter gate is PASS or SKIP_WITH_REASON.
8. Repair resets affected gates to PENDING, removes stale release receipts, and requires re-review.
9. Military and science consultants may SKIP_WITH_REASON only with a written reason; they may not be left PENDING at release time.
10. Editor PASS must include DEAI and audience-respect evidence; reader PASS must include real reading-experience evidence.

## Evidence contract

Every gate transition records:
- the artifact path (inside the project root),
- the reviewer provenance (`role:identifier`),
- a checksum of the artifact contents,
- a timestamp,
- for domain skips, the reason text.

The append-only event trail lives in `.novel-workflow/events.jsonl`.

## CLI map

```
novel-workflow init <path> --title "..."
novel-workflow idea <path> --summary "..." --interview '{...}'
novel-workflow concept-review <path> PASS|FAIL --artifact ... --reviewer controller:...
novel-workflow concept-repair <path> --summary ... PASS|FAIL --artifact ... --reviewer controller:...
novel-workflow bible <path> --artifact ...
novel-workflow outline-write <path> master|volume|chapter --artifact ...
novel-workflow outline-review <path> master|volume|chapter PASS|FAIL --artifact ... --reviewer controller:...
novel-workflow outline-repair <path> <level> --artifact ... PASS|FAIL --review-artifact ... --reviewer ...
novel-workflow outline-lock <path>
novel-workflow issue <path> <n> --title ... --goal ...
novel-workflow draft <path> <n> --artifact ... --prewrite ... --author author:...
novel-workflow review <path> <n> <gate> PASS|FAIL|SKIP_WITH_REASON --artifact ... --reviewer ... [--reason ...]
novel-workflow repair <path> <n> --artifact ... --affected editor reader
novel-workflow release <path> <n>
novel-workflow status <path> [--chapter <n>]
novel-workflow chapters <path>
novel-workflow check <path> --security
novel-workflow roles <path>
```

## Whole-book layer

Above the single-chapter loop, the workflow maintains a project-level
chapter ledger and an asset registry so a long-form project does not lose
continuity across chapters.

### Chapter progress ledger

`workflow.json.chapters` is a summary keyed by chapter number. Every
`issue`, `review`, `repair`, and `release` mirrors the chapter's status,
gates, and release time into the ledger. Use `novel-workflow chapters
<path>` to see whole-book progress at a glance. The per-chapter state file
under `.novel-workflow/` remains the source of truth; the ledger is a
read-only summary.

### Asset cards

Four card templates live under `templates/`:

- `character_card.md` - identity, goal, knowledge boundary, ability/cost, emotional/physical state, voice fingerprint, version.
- `scene_card.md` - layout, sensory palette, rules, continuity anchors, version.
- `object_card.md` - function, constraints, continuity state, version.
- `concept_card.md` - world-rules, technology, factions, institutions, version.

The chapter contract's `asset_cards_used` field records which cards (and
which versions) a chapter depends on. Cards are versioned: a justified
in-story change bumps the version and appends to the change log; an
unjustified change is a blocking error at the editor gate.

Conflict resolution uses three labels:

- `ASSET_CONFLICT` - two cards contradict each other.
- `TEXT_ERROR` - the draft violates a confirmed card.
- `REASONABLE_GROWTH` - a change with a triggering event; update the card.

### Long-chapter segmentation

The chapter contract's `segment_plan` field lets the author declare how a
long chapter is split into segments (for example, one segment per
viewpoint or per scene). Each segment should stay under roughly 3000 words
and carry its own continuity anchor so a repair can target a segment
without rewriting the whole chapter.

### Cross-chapter consistency

The editor and reader gates carry a `CROSS_CHAPTER_CONSISTENCY` field
covering: previous-chapter end-state, pronoun and name consistency, object
position continuity, terminology and title consistency, and communication
visibility state. This is a template-level gate; the state machine does not
block on it, but a `FAIL` is a blocking review verdict.

### Source alignment

`record_draft` compares the draft title against the chapter outline title
and rejects a mismatch as `SOURCE_MISMATCH`. This prevents a chapter that
is well-written but written against the wrong outline from entering
review.

## Progression route (beginner to long-form)

| Level | Introduces | Guards against |
|-------|-----------|----------------|
| L1 multi-chapter serial | chapter ledger, serial issue | cross-chapter name/pronoun/object drift |
| L2 asset management | character/scene/object/concept cards with versions | same-name setting drift, character-state disconnect |
| L3 character-consistency gate | six-dimension score in editor/reader (any <=2 FAIL) | unjustified change, knowledge leak, costless new ability |
| L4 cross-chapter consistency | CROSS_CHAPTER_CONSISTENCY field | cut channel silently restored, object teleporting |
| L5 numerical consistency | science consultant NUMERICAL_CONSISTENCY | hard-sci numbers contradicting themselves |
| L6 outline alignment | draft title vs chapter outline title (SOURCE_MISMATCH) | writing the wrong chapter well |
| L7 post-draft DEAI machine scan | NOT_BUT / enumeration / summary-tone tags, flag only | AI tone graded "acceptable" and passed |
| L8 mechanical typo gate | deterministic typo list scan | model review cannot catch homophones |
| L9 format cleanup | strip wikilinks, balance quotes, trim, forbidden words | publish-format pollution |
| L10 sustained-progress discipline | close each chapter loop before claiming done | "will continue" treated as "done" |

The beginner route (single chapter, no assets, no cross-chapter) is the
minimum viable path. Each level adds a gate or an asset layer; none is
required to ship a first chapter.

## Audience-respect principle

Lower the barrier, not the reader's intelligence. Keep necessary complexity and subtext. Prefer evidence, actions, choices, and consequences over repeated explanations, stereotypes, or formulaic stimulation. The editor and reader gates enforce this; the controller only records and blocks.
