# Structured Novel Intake

Use this workbook before concept review. It guides a beginner from a raw spark
to decisions that can support a story bible and layered outlines. Do not rush to
an outline while required sections remain blank.

The prompts are genre-neutral. Prior reading may inform **abstract craft
patterns** such as escalation cadence, clue placement, relationship pressure,
or payoff distance. Do not copy protected wording, distinctive names, scenes,
setting combinations, character packages, or private corpus text.

## Step 1 — Reader promise

- `audience`: Who is the intended reader? Include age band where relevant,
  genre expectations, reading context, and the feeling promised at the end of
  a typical chapter.
- `genre`: Primary genre, secondary elements, platform/market position, and
  three comparison dimensions without copying a named work.
- `target_words`: Target total words, acceptable range, approximate number of
  volumes, chapters per volume, and chapter length.

## Step 2 — Core premise

- `premise`: Who faces what disruption, pursues what concrete goal, and meets
  what durable resistance? Why does the story begin now?
- `central_conflict`: What renewable conflict engine can sustain the target
  length rather than resolving after one incident?
- `stakes`: Personal, relational, social/world stakes and the visible cost of
  failure or victory.
- `ending`: Expected ending type, final choice, emotional landing, promises
  that must be paid off, and questions deliberately left open.

## Step 3 — Background and world

- `world`: Time, place, technology or magic level, social order, economy,
  institutions, geography, daily life, non-negotiable rules, and the cost of
  breaking those rules.
- Distinguish familiar genre conventions from this story's specific twist.
- State what information is public, secret, disputed, or misunderstood.

## Step 4 — People and relationships

- `protagonist`: External want, internal need, fear, flaw, useful ability,
  ability cost, knowledge boundary, moral line, voice/behaviour fingerprint,
  starting state, and possible ending state.
- `supporting_cast`: Antagonistic force, allies, rivals, intimate relationships,
  mentors/dependants, each party's incentive, leverage, secret, and conflict
  with the protagonist.
- `character_arc`: Starting false belief or protective habit, pressure points,
  costly choices, midpoint change, relapse, final proof of change or refusal.

## Step 5 — Style contract

- `style`: POV, tense, narrative distance, tone, humour, darkness, prose
  density, dialogue ratio, sensory density, pacing, chapter-end behaviour,
  explanation tolerance, and forbidden habits.
- Describe observable techniques. Avoid vague labels such as "beautiful" or
  "cinematic" without saying what appears on the page.

## Step 6 — Structure and escalation

- `structure`: Opening disturbance, first irreversible choice, major phases or
  volume functions, escalation ladder, midpoint reversal, low point, climax,
  denouement, subplot jobs, revelation order, foreshadow/payoff distances, and
  where character changes become visible.
- A master outline states the whole-story causal spine. Volume outlines state
  each volume's function and state change. Chapter outlines state scene-level
  goal, conflict, choice, cost, new information, continuity, and hook.

## Step 7 — Boundaries and originality

- `boundaries`: Content the story must avoid, platform/legal risks, clichés the
  user dislikes, representation limits, prohibited endings, and facts requiring
  professional review.
- `craft_patterns`: Abstract lessons from prior reading or analysis. Record the
  pattern, why it works, how this project will transform it, and an originality
  check. Never paste source prose or recreate a distinctive package.

## Required JSON keys

All fifteen keys are required before concept review:

```json
{
  "audience": "...",
  "genre": "...",
  "target_words": {"target": 800000, "range": "700000-900000", "volumes": 5, "chapter_words": 3000},
  "premise": "...",
  "world": "...",
  "protagonist": "...",
  "supporting_cast": "...",
  "central_conflict": "...",
  "stakes": "...",
  "character_arc": "...",
  "style": "...",
  "structure": "...",
  "ending": "...",
  "boundaries": "...",
  "craft_patterns": ["pattern + transformation + originality check"]
}
```

## Guided use

Check answers at any time:

```bash
novel-workflow intake-check <path> --interview '{...}'
```

The report gives completion percentage, missing fields, and exactly one next
question. Record the completed intake:

```bash
novel-workflow idea <path> \
  --summary "One-sentence premise." \
  --interview '{...}'
```

Concept review is blocked until `intake-check` reports `COMPLETE`.
