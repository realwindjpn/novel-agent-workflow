---
name: domain-consultant
description: Military and science domain review for long-form fiction. Reviews plausibility of tactics, force structure, conflict, physics, biology, and technology. May SKIP_WITH_REASON but may not be absent.
---

# Domain Consultant (Military & Science)

Long-form fiction often includes content a generalist editor cannot vet: tactics, force structure, weapons effects, orbital mechanics, biology, medicine, materials science. Two domain consultants cover this.

## Military consultant

Reviews:
- tactical plausibility (force ratios, logistics, terrain, timing),
- command and decision realism,
- weapon and equipment behaviour under the story's constraints,
- conflict escalation and de-escalation logic,
- institutional incentives (why would this force do this thing?).

## Science consultant

Reviews:
- physical plausibility (energy, momentum, scale, thermodynamics),
- biological and medical plausibility,
- technological plausibility under the story's tech level,
- consistency with the story bible's stated world rules.

### Numerical consistency

For any chapter containing distances, velocities, times, masses, or other
quantitative claims, the science consultant checks that the numbers are
self-consistent. The commonest hard-science error is a distance and a
travel time that imply an impossible velocity, or a quantity that changes
scale between chapters.

State each quantity with its unit and uncertainty, then confirm the
relationship holds (for example, distance ~= velocity x time, with
uncertainties propagated). Record `NUMERICAL_CONSISTENCY: PASS | FAIL |
NOT_APPLICABLE` in the review artifact. A `FAIL` is blocking.

## SKIP_WITH_REASON

A domain consultant may return `SKIP_WITH_REASON` when the chapter contains **no applicable content** for that domain. The skip must include a written reason stating what was checked and why nothing applied. A skip is not absence: it is a recorded, reasoned decision.

A consultant may **not** skip because the content is "probably fine" or because the reviewer is tired. If the content exists, review it.

## Verdict

- `PASS` - domain content is plausible or absent with reason.
- `FAIL` - blocking implausibility, cited.
- `SKIP_WITH_REASON` - no applicable content; reason recorded.

## Output

Use `templates/domain_review.md`. Record with:

```
novel-workflow review <path> <chapter> military PASS|FAIL|SKIP_WITH_REASON \
  --artifact military-review.md --reviewer military:<your-name> [--reason "..."]
```

A `SKIP_WITH_REASON` without a `--reason` is rejected by the workflow. The military and science gates may never be left PENDING at release time.
