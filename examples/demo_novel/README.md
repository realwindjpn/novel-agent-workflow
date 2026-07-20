# Demo: The Silent Relay

A fictional, non-production example. It shows how the workflow records
evidence-backed gates using relative paths. No manuscript, private
configuration, account state, or service route is used.

## Full end-to-end pipeline

`run_full_demo.sh` runs the complete six-role pipeline in a throwaway
directory and is the canonical example. It exercises every gate the core
enforces:

```
init -> idea -> concept-review (PASS) -> bible ->
outline master/volume/chapter (write + review each) -> lock ->
issue -> draft (with Author Role OS prewrite card) ->
editor PASS (independent) -> reader PASS (independent) ->
military SKIP_WITH_REASON -> science SKIP_WITH_REASON ->
READY_TO_RELEASE -> release (explicit command) -> security check
```

Run it:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .

bash examples/demo_novel/run_full_demo.sh
```

The script prints the chapter status before release (`READY_TO_RELEASE`,
not `RELEASED`), writes the release receipt, and runs a security check that
returns no findings. Pass a destination directory to keep the demo project:

```bash
bash examples/demo_novel/run_full_demo.sh /tmp/my-demo
```

### Hard gates the demo satisfies

Every PASS review artifact embeds the fields the core now enforces in code,
not just by convention:

- `reviewed_fulltext: true` - the reviewer read the whole draft, not a summary.
- `candidate_sha256:` - the sha256 of the draft under review, so a stale or
  wrong-chapter draft is rejected.
- `CROSS_CHAPTER_CONSISTENCY: PASS` - editor and reader gates only.
- Domain consultants `SKIP_WITH_REASON` carry a written reason; a skip is a
  recorded decision, not absence.

## Static sample contents

The demo also ships static sample artifacts so a beginner can inspect each
stage without running the script:

- `story-bible/world.md` - one-paragraph world note used as the story bible.
- `outlines/chapter-1.md` - a single chapter outline entry.

These static files stop at the chapter-outline stage. To see draft, review,
release, and the security check, run `run_full_demo.sh` or follow
`docs/BEGINNER_GUIDE.md`.
