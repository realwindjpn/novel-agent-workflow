---
name: author-role-os
description: Pre-write operating system for the author role. Produces a human-writing constraint card and a chapter-specific prewrite brief before any prose is drafted.
---

# Author Role OS

The Author Role OS is a **pre-write** constraint system. It runs before the author writes a single line of chapter prose. Its output is a *prewrite card* that the workflow records alongside the draft as evidence that the author engaged with voice, stakes, and human-writing constraints.

## When to use

- Before producing the first draft of any chapter.
- Before producing a revised draft after a repair cycle.

## Inputs

- The chapter contract (goal, must-include, must-not-include, end-state).
- The story bible (world, characters, knowledge boundaries, timeline).
- The current outline lock state (must be LOCKED).

## Prewrite card fields

1. **Chapter function** - one sentence: what does this chapter do in the volume?
2. **POV and tense** - who sees, when.
3. **Entry state** - where the reader is at chapter open.
4. **Three-event chain** - the spine of the chapter.
5. **Central choice and cost** - what the protagonist decides and what it costs.
6. **Voice anchors** - three concrete sensory or tonal anchors that should appear.
7. **Forbidden drift** - at least one thing this chapter must *not* do.
8. **Human-writing constraints** - see checklist below.

## Human-writing constraints

Before drafting, the author confirms:

- No explanatory monologue that tells the reader what they just saw.
- No "not X, but Y" formula repetition.
- No demographic stereotype as character shortcut.
- No listicle pacing (three beats then summary).
- No emotional label where an action would carry it.
- No thesaurus-grade vocabulary inflation.
- Subtext is preserved; the reader is trusted to infer.

These are constraints, not style preferences. The editor and reader gates check for their violation.

## Long-chapter segmentation

When a chapter exceeds roughly 3000 words, split it into segments in the
chapter contract's `segment_plan` (one segment per viewpoint or per scene).
Each segment carries its own continuity anchor - the entry state, the voice
anchors, and the forbidden drift for that segment. This lets a repair
target one segment without rewriting the whole chapter, and lets the editor
cite drift at segment granularity.

## Asset versioning

Before drafting, confirm the character/scene/object/concept cards the
chapter depends on (listed in the chapter contract's `asset_cards_used`).
Draft against the cited versions. If the story requires a character to
change, write the triggering event into the chapter, then update the card
and bump its version - do not silently edit. An unjustified change is a
blocking editor error (`ASSET_CONFLICT` or `TEXT_ERROR`); a justified
change is `REASONABLE_GROWTH`.

## Evidence requirement

The workflow rejects a draft if the prewrite card lacks any of: `Chapter function`, `Three-event chain`, `Central choice`, `Voice anchors`, `Forbidden drift`, or `Human-writing constraints`. This keeps the prewrite card from becoming a token gesture.

## Output

Write the prewrite card to a markdown file (template: `templates/author_role_os_prewrite.md`) and pass it to:

```
novel-workflow draft <path> <chapter> --artifact draft.md --prewrite prewrite.md --author author:<your-name>
```

The workflow records the prewrite checksum alongside the draft. A draft without a complete prewrite card is rejected.
