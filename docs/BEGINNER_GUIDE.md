# Beginner Guide: From One Idea to Chapter Issue

This guide assumes you only have one raw idea. It keeps you from drafting too early.

## 0. Install

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

## 1. Start a project

```bash
novel-workflow init demo --title "The Silent Relay"
```

This creates `workflow.json`, a `.novel-workflow/` state directory, and working folders for idea, bible, outlines, chapters, reviews, and releases.

## 2. Idea interview

Use `templates/idea_interview.md`. Answer only enough to make the concept reviewable:

- whose story is this?
- what do they want?
- what blocks them?
- what strange rule must the reader accept?
- what promise does the story make?
- what is at stake?

Record the idea:

```bash
novel-workflow idea demo --summary "A relay crew hears an impossible signal." --interview '{"protagonist":"repair lead","stakes":"truth may cost the crew their safe orbit"}'
```

## 3. Concept review and repair

Write a concept review artifact. The concept must PASS before the story bible exists.

```bash
printf '# Concept Review
PASS
' > demo/concept-review.md
novel-workflow concept-review demo PASS --artifact concept-review.md --reviewer controller:concept-reviewer
```

If the verdict is FAIL, repair the idea and re-review:

```bash
novel-workflow concept-repair demo --summary "Repaired one-sentence idea" PASS --artifact concept-review.md --reviewer controller:concept-reviewer
```

## 4. Story bible

Use `templates/story_bible.md`. Record it only after concept PASS:

```bash
printf '# Story Bible
World rules, characters, knowledge boundaries.
' > demo/story-bible.md
novel-workflow bible demo --artifact story-bible.md
```

## 5. Outline ladder

Use these templates in order:

1. `templates/outline_master.md`
2. `templates/outline_volume.md`
3. `templates/outline_chapter.md`

Each level must be written, reviewed, repaired if needed, and PASS before the next level.

```bash
novel-workflow outline-write demo master --artifact outlines/master.md
novel-workflow outline-review demo master PASS --artifact reviews/master-review.md --reviewer controller:master-reviewer
novel-workflow outline-write demo volume --artifact outlines/volume-1.md
novel-workflow outline-review demo volume PASS --artifact reviews/volume-review.md --reviewer controller:volume-reviewer
novel-workflow outline-write demo chapter --artifact outlines/chapter-1.md
novel-workflow outline-review demo chapter PASS --artifact reviews/chapter-outline-review.md --reviewer controller:chapter-reviewer
novel-workflow outline-lock demo
```

If any review FAILs, run `outline-repair` and review the repaired artifact. Chapter issue is blocked until all outline levels PASS.

## 6. Chapter issue

```bash
novel-workflow issue demo 1 --title "First Signal" --goal "Introduce the disputed signal without solving it"
```

This creates chapter state. It is not a draft.

## 7. Draft and reviews

Before drafting, fill `templates/author_role_os_prewrite.md`. The CLI rejects a draft if the prewrite card lacks the required Author Role OS sections.

```bash
novel-workflow draft demo 1 --artifact chapters/chapter-1-draft.md --prewrite chapters/chapter-1-prewrite.md --author author:writer-a
novel-workflow review demo 1 editor PASS --artifact reviews/chapter-1-editor.md --reviewer editor:editor-b
novel-workflow review demo 1 reader PASS --artifact reviews/chapter-1-reader.md --reviewer reader:reader-c
novel-workflow review demo 1 military SKIP_WITH_REASON --artifact reviews/chapter-1-military.md --reviewer military:military-d --reason "No tactics, force, command, or logistics content in this chapter."
novel-workflow review demo 1 science SKIP_WITH_REASON --artifact reviews/chapter-1-science.md --reviewer science:science-e --reason "No science or technical plausibility content in this chapter."
```

Editor PASS must contain `DEAI` and `Audience respect`. Reader PASS must contain `Real reading experience`, `Immersion`, and `Over-explanation`.

## 8. Repair and release

If a gate FAILs, repair the draft and name the affected gates:

```bash
novel-workflow repair demo 1 --artifact chapters/chapter-1-draft-r2.md --affected editor reader
```

Affected gates reset to `PENDING`, stale release receipts are removed, and those gates must be reviewed again.

When every gate is satisfied, the chapter becomes `READY_TO_RELEASE`. It becomes `RELEASED` only after an explicit release command:

```bash
novel-workflow release demo 1
novel-workflow check demo --security
```

## 9. Whole-book view

Once you have more than one chapter, use the ledger to see the whole book:

```bash
novel-workflow chapters demo
```

This reads `workflow.json.chapters` (mirrored on every issue/review/repair/release) and shows each chapter's status, gates, and release time. The per-chapter state file under `.novel-workflow/` is the source of truth; the ledger is a read-only summary.

## 10. Progression route (beginner to long-form)

The beginner route above is the minimum viable path: one idea to one released chapter, no assets, no cross-chapter checks. Long-form fiction adds gates and asset layers. None is required to ship a first chapter.

| Level | Introduces | Guards against |
|-------|-----------|----------------|
| L1 multi-chapter serial | chapter ledger, serial issue | cross-chapter name/pronoun/object drift |
| L2 asset management | character / scene / object / concept cards with versions | same-name setting drift, character-state disconnect |
| L3 character-consistency gate | six-dimension score in editor/reader (any <=2 is FAIL) | unjustified change, knowledge leak, costless new ability |
| L4 cross-chapter consistency | `CROSS_CHAPTER_CONSISTENCY` field | a cut channel silently restored, an object teleporting |
| L5 numerical consistency | science consultant `NUMERICAL_CONSISTENCY` | hard-sci numbers contradicting themselves |
| L6 outline alignment | draft title vs chapter outline title (`SOURCE_MISMATCH`) | writing the wrong chapter well |
| L7 post-draft DEAI machine scan | NOT_BUT / enumeration / summary-tone tags, flag only | AI tone graded "acceptable" and passed |
| L8 mechanical typo gate | deterministic typo list scan | model review cannot catch homophones |
| L9 format cleanup | strip wikilinks, balance quotes, trim, forbidden words | publish-format pollution |
| L10 sustained-progress discipline | close each chapter loop before claiming done | "will continue" treated as "done" |

To use asset cards, fill `templates/character_card.md` (and scene/object/concept), store them under `assets/`, and list the cards a chapter depends on in the chapter contract's `asset_cards_used` field. Bump a card's version when a justified in-story change happens; an unjustified change is a blocking editor error.

## 11. Ten pitfalls and how this workflow guards against them

1. **Skipping review and reporting done.** The state machine refuses `release` until every gate is PASS or SKIP_WITH_REASON. "Fixed the draft" is not "closed the loop."
2. **Treating an outline update as a finished chapter.** Outline and chapter are independent states. The outline must be LOCKED before a chapter can be issued; editing the outline after lock requires outline repair, not a silent chapter edit.
3. **One execution impersonating several independent roles.** Users may reuse one underlying model across roles or choose a different model for each role. Provenance is `role:identifier`: author, editor, and reader need separate calls/contexts and distinct identifiers. Same-execution self-review is rejected.
4. **Reviewing a summary instead of the full text.** The review report template requires `reviewed_fulltext: true`. A PASS without it is invalid by convention; future scanner work can enforce this.
5. **A prewrite card filled in as a ritual.** `record_draft` rejects a prewrite card missing any of six required sections. A bare "notes" file does not pass.
6. **Repairing a draft and reporting PASS without re-review.** `repair` resets the affected gates to PENDING and deletes the stale release receipt. Those gates must be reviewed again.
7. **A well-written chapter written against the wrong outline.** `record_draft` compares the draft title to the chapter outline title and rejects a mismatch as `SOURCE_MISMATCH`.
8. **AI tone graded "acceptable" and waved through.** The editor PASS requires a DEAI section; the DEAI checklist enumerates eight violation classes. A one-word PASS is rejected.
9. **A character changing for no reason.** The editor and reader templates carry a six-dimension character-consistency score; any dimension at 2 or below is a blocking FAIL. Unjustified change is `ASSET_CONFLICT` or `TEXT_ERROR`; justified change is `REASONABLE_GROWTH` with a card version bump.
10. **"Will continue" treated as "done."** `READY_TO_RELEASE` is not `RELEASED`. Release requires an explicit command and produces a receipt. A repair revokes the receipt. There is no path from "gates passed" to "shipped" without the release command.
