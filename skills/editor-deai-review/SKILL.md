---
name: editor-deai-review
description: Independent editor review covering structure, pacing, prose, DEAI compliance, and audience-respect. Provenance must differ from the author.
---

# Editor - DEAI Review

The editor is an **independent** reviewer. The editor's provenance (`editor:identifier`) must not share an identifier with the author. The editor does not rewrite; the editor records evidence and a verdict.

## Scope

1. **Structure** - does the chapter deliver its contract goal? Does the three-event chain land?
2. **Pacing** - does any beat overstay or rush? Is the end-state earned?
3. **Prose** - is the sentence-level craft consistent with the story bible's voice anchors?
4. **DEAI compliance** - the de-AI checklist (see `templates/deai_checklist.md`).
5. **Audience-respect** - lower the barrier, not the intelligence. Flag over-explanation, demographic stereotyping, formulaic stimulation, and lost subtext.

## DEAI checklist (what to flag as FAIL)

- Explanatory monologue that restates what the reader just witnessed.
- Repeated "not X, but Y" / "not just X, it was Y" constructions.
- Emotional labels where action or object would carry the beat.
- Thesaurus inflation; words the voice would not use.
- Listicle rhythm (beat, beat, beat, summary).
- Stereotype shortcuts for minor characters.
- Tone flattening - everything described at the same intensity.
- Hollow metaphors - pretty but not load-bearing.

## Evidence requirement

A `PASS` editor review artifact must include both:

- a `DEAI` section citing what was checked, and
- an `Audience respect` section citing preserved subtext and necessary complexity.

The workflow rejects an editor `PASS` that omits these sections. This prevents a single-word "PASS" from satisfying the gate.

## Character-state consistency (six-dimension score)

Before a `PASS`, score the candidate against the character cards cited in
the chapter contract's `asset_cards_used`. Each dimension is 1-5; any score
of 2 or below is a blocking `FAIL`. Cite the paragraph.

- **Identity and affiliation** - is the character the same person, faction, and role as their card?
- **Current goal** - does the character pursue their stated want/need, or is the drift justified by an in-story event?
- **Knowledge boundary** - does the character act only on what they know? Acting on information they do not have is a blocking error unless the leak is explained.
- **Ability and cost** - does the character use only abilities their card grants, and pay the stated cost? A new ability with no trigger and no cost is a blocking error.
- **Emotional and physical state** - does the character's register and condition match their last-known state, or change for a justified reason?
- **Voice and behaviour fingerprint** - do the three concrete markers from the card appear? Has the voice drifted into generic prose?

When a character changes in a justified way (a triggering event in-story),
update the card and bump its version rather than silently editing. Flag
unjustified change as `ASSET_CONFLICT` or `TEXT_ERROR`; justified change is
`REASONABLE_GROWTH`.

## Cross-chapter consistency

The editor is responsible for continuity across chapter boundaries. Before
`PASS`, set `CROSS_CHAPTER_CONSISTENCY: PASS | FAIL` and check:

- **Previous-chapter end-state** - does this chapter open where the last left off (location, time, emotional register)?
- **Pronoun and name consistency** - are names and pronouns stable? A character referred to by surname in chapter 3 should not become a first-name in chapter 4 without reason.
- **Object position continuity** - if an object was on the desk at the end of the last chapter, is it still there?
- **Terminology and title consistency** - are world terms, ranks, and place names spelled and used consistently?
- **Communication visibility state** - if a channel was cut or a character was absent, is that state preserved? A cut channel silently restored is a blocking error.

## Source alignment (SOURCE_MISMATCH)

Before reviewing, confirm the draft title matches the chapter outline title.
The workflow enforces this at draft-recording time; if a mismatch slips
through (for example an edited state file), the editor must `FAIL` with
`SOURCE_MISMATCH` cited. A chapter that is well-written but written against
the wrong outline is a blocking failure.

## Verdict

- `PASS` - no blocking issues; optional improvements may be listed.
- `FAIL` - at least one blocking issue, cited with line or paragraph reference.

## Output

Use `templates/review_report.md`. Record with:

```
novel-workflow review <path> <chapter> editor PASS|FAIL \
  --artifact editor-review.md --reviewer editor:<your-name>
```

The workflow enforces independence and evidence at recording time. If your identifier matches the author's, or if a PASS omits DEAI/audience-respect evidence, the command is rejected.
