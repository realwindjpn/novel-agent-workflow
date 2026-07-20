# Review Report

Generic template for editor or reader reviews. Both gates use this report;
the domain consultants use `templates/domain_review.md`.

## Chapter

- Chapter:
- Gate: editor | reader
- Reviewer provenance:

## Source artifact

- Path:
- Checksum (recorded by workflow):

## Full-text attestation

- reviewed_fulltext: true | false

The reviewer must confirm they read the entire candidate draft, not a
summary. A `PASS` with `reviewed_fulltext: false` is invalid. This field
exists because the most common review failure is reviewing a summary instead
of the full text.

## Candidate checksum

- candidate_sha256: (the workflow records the draft checksum; the reviewer
  cites it here to attest the draft they read is the draft under review)

## Verdict

- PASS
- FAIL

## Evidence citations

Cite paragraph or line numbers for every claim.

-

## Blocking issues (if FAIL)

-

## Optional improvements

-

## Audience-respect check

- DEAI (editor): pass / fail - evidence:
- Real reading experience (reader): pass / fail - evidence:
- Over-explanation: yes / no - where:
- Stereotype shortcut: yes / no - where:
- Necessary complexity preserved: yes / no - note:

## Character-state consistency (editor / reader)

Score each dimension 1-5. Any score of 2 or below is a FAIL. Cite the
paragraph where the inconsistency occurs.

- Identity and affiliation:
- Current goal:
- Knowledge boundary:
- Ability and cost:
- Emotional and physical state:
- Voice and behaviour fingerprint:

## Cross-chapter consistency (editor / reader)

- CROSS_CHAPTER_CONSISTENCY: PASS | FAIL
- Previous-chapter end-state衔接 (does this chapter open where the last left off):
- Pronoun and name consistency:
- Object position continuity:
- Terminology and title consistency:
- Communication visibility state (if a channel was cut, is it still cut):
