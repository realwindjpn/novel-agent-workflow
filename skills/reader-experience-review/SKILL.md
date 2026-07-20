---
name: reader-experience-review
description: Independent reader review of real reading experience - clarity, immersion, fatigue, over-explanation. Provenance must differ from author and editor.
---

# Reader - Real Reading-Experience Review

The reader reviewer is **independent** of both the author and the editor. The reader does not copy-edit; the reader reports what it actually felt like to read this chapter cold.

## What the reader checks

1. **Clarity without hand-holding** - could a first-time reader follow the chapter? Where did you have to re-read?
2. **Immersion** - where did the world break? Where did you notice you were reading words instead of living the scene?
3. **Fatigue** - where did attention drop? Was any beat too long?
4. **Over-explanation** - did the chapter tell you what you already saw?
5. **Subtext preserved** - did the chapter trust you to infer, or did it flatten the meaning?
6. **End-state pull** - did the ending make you want the next chapter?

## Evidence requirement

A `PASS` reader review artifact must include:

- a `Real reading experience` summary,
- an `Immersion` note, and
- an `Over-explanation` note.

The workflow rejects a reader `PASS` that omits these sections. This keeps the gate about experience, not about a single word.

## Character-state consistency (reader view)

The reader checks whether characters *feel* continuous, not whether they
match a database. Before `PASS`, score each dimension 1-5; any score of 2
or below is a blocking `FAIL`. Cite the moment.

- **Identity** - did you ever forget who a character was, or confuse two?
- **Goal** - did a character suddenly want something with no setup?
- **Knowledge** - did a character act on information they should not have?
- **Ability** - did a character do something they could not previously do, with no cost?
- **Emotional state** - did a character's mood shift without a triggering beat?
- **Voice** - did a character start sounding like generic narration, or like another character?

The reader does not need the character cards. The reader needs to feel that
the people are the same people. If a character breaks, the reader will
usually notice it as a "wait, what?" moment before the editor can cite it.

## Verdict

- `PASS` - the chapter reads; no blocking experience problems.
- `FAIL` - at least one blocking experience problem, cited with the moment (paragraph or beat) where it occurred.

## Output

Use `templates/reader_review.md`. Record with:

```
novel-workflow review <path> <chapter> reader PASS|FAIL \
  --artifact reader-review.md --reviewer reader:<your-name>
```

Independence and evidence are enforced: your identifier must differ from the author's and the editor's, and a PASS must carry the required sections.

## Why this gate exists separately from the editor

The editor checks craft. The reader checks experience. A chapter can be well-built and still feel exhausting, or technically clean and still over-explain. Both must pass independently.
