#!/usr/bin/env bash
# Full end-to-end demo for novel-agent-workflow.
#
# Runs the complete six-role pipeline in a throwaway directory:
#   init -> idea -> concept-review -> bible ->
#   outline (master/volume/chapter, write+review each) -> lock ->
#   issue -> draft (with Author Role OS prewrite) ->
#   editor PASS (independent) -> reader PASS (independent) ->
#   military SKIP_WITH_REASON -> science SKIP_WITH_REASON ->
#   release -> security check
#
# The review artifacts embed the hard-gate fields the core now enforces on
# every PASS: reviewed_fulltext: true, candidate_sha256 matching the draft,
# and CROSS_CHAPTER_CONSISTENCY: PASS for editor/reader.  Domain skips carry
# a written reason.
#
# Usage:  bash examples/demo_novel/run_full_demo.sh [dest_dir]
# Default dest_dir is a fresh temp dir under /tmp.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
DEST="${1:-$(mktemp -d -t novel-demo-XXXXXX)}"
mkdir -p "$DEST"

PY="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src:${PYTHONPATH:-}"

echo "demo dest: $DEST"
cd "$DEST"

# --- 1. init + idea ---
"$PY" -m novel_workflow.cli init "$DEST" --title "The Silent Relay" >/dev/null
"$PY" -m novel_workflow.cli idea "$DEST" \
  --summary "A repair crew hears an impossible signal." \
  --interview '{"protagonist":"repair lead","stakes":"truth may cost safe orbit"}' >/dev/null

# --- 2. concept review ---
printf '# Concept Review\nPASS\n' > concept-review.md
"$PY" -m novel_workflow.cli concept-review "$DEST" PASS \
  --artifact concept-review.md --reviewer controller:concept-a >/dev/null

# --- 3. story bible ---
cp "$HERE/story-bible/world.md" "$DEST/bible.md"
"$PY" -m novel_workflow.cli bible "$DEST" --artifact bible.md >/dev/null

# --- 4. outlines (master / volume / chapter), each written then reviewed ---
for level in master volume chapter; do
  printf '# %s Outline\nPASS\n' "$level" > "outline-$level.md"
  printf '# %s Review\nPASS\n' "$level" > "outline-$level-review.md"
  "$PY" -m novel_workflow.cli outline-write "$DEST" "$level" --artifact "outline-$level.md" >/dev/null
  "$PY" -m novel_workflow.cli outline-review "$DEST" "$level" PASS \
    --artifact "outline-$level-review.md" --reviewer "controller:outline-$level-a" >/dev/null
done

# --- 5. lock + issue ---
"$PY" -m novel_workflow.cli outline-lock "$DEST" >/dev/null
"$PY" -m novel_workflow.cli issue "$DEST" 1 \
  --title "First Signal" \
  --goal "Establish the relay and the disputed measurement without explaining the signal" >/dev/null

# --- 6. Author Role OS prewrite card (must contain all required headings) ---
cat > prewrite.md <<'PRE'
# Prewrite card
Chapter function: introduce the disputed signal.
POV and tense: repair lead, past tense.
Entry state: crew is tired and under pressure.
Three-event chain: false alarm / impossible delay / risky confirmation.
Central choice and cost: report truth, lose safety.
Voice anchors: cold metal, delayed light, dry air.
Forbidden drift: do not solve the signal yet.
Human-writing constraints: no explanatory monologue; subtext preserved.
PRE

# --- 7. draft ---
cat > draft.md <<'DRAFT'
# First Signal

The relay ticked. Mira counted the delay and frowned. Three seconds was
impossible. She said nothing; the log said it for her.
DRAFT

# Compute the draft sha256 so the review attestation can cite it.
DRAFT_SHA="$("$PY" -c "import hashlib,sys; print(hashlib.sha256(open('draft.md','rb').read()).hexdigest())")"
echo "draft sha256: $DRAFT_SHA"

"$PY" -m novel_workflow.cli draft "$DEST" 1 \
  --artifact draft.md --prewrite prewrite.md --author author:mira >/dev/null

# --- 8. editor PASS (independent of author) ---
cat > editor-review.md <<ED
# Editor Review
DEAI: no formulaic prose or explanation dump.
Audience respect: preserves inference and necessary complexity.
Structure: contract goal is delivered.
reviewed_fulltext: true
candidate_sha256: $DRAFT_SHA
CROSS_CHAPTER_CONSISTENCY: PASS
ED
"$PY" -m novel_workflow.cli review "$DEST" 1 editor PASS \
  --artifact editor-review.md --reviewer editor:bo >/dev/null

# --- 9. reader PASS (independent of author and editor) ---
cat > reader-review.md <<RD
# Reader Review
Real reading experience: clear and tense.
Immersion: stable.
Over-explanation: no blocking restatement.
End-state pull: yes.
reviewed_fulltext: true
candidate_sha256: $DRAFT_SHA
CROSS_CHAPTER_CONSISTENCY: PASS
RD
"$PY" -m novel_workflow.cli review "$DEST" 1 reader PASS \
  --artifact reader-review.md --reviewer reader:cao >/dev/null

# --- 10. domain consultants: SKIP_WITH_REASON (recorded decision, not absence) ---
printf '# Military Review\nNo applicable content checked.\n' > military-review.md
"$PY" -m novel_workflow.cli review "$DEST" 1 military SKIP_WITH_REASON \
  --artifact military-review.md --reviewer military:dia \
  --reason "No tactical or force-structure content in this chapter." >/dev/null

printf '# Science Review\nNo applicable content checked.\n' > science-review.md
"$PY" -m novel_workflow.cli review "$DEST" 1 science SKIP_WITH_REASON \
  --artifact science-review.md --reviewer science:eve \
  --reason "No quantitative physical claim in this chapter." >/dev/null

# --- 11. status before release (should be READY_TO_RELEASE, not RELEASED) ---
echo "--- status before release ---"
"$PY" -m novel_workflow.cli status "$DEST" --chapter 1 | "$PY" -c "import json,sys; d=json.load(sys.stdin); print('chapter status:', d['chapter']['status']); print('gates:', d['chapter']['gates'])"

# --- 12. release (explicit command, writes receipt) ---
"$PY" -m novel_workflow.cli release "$DEST" 1 >/dev/null
echo "release receipt written: $([ -f releases/chapter-1.json ] && echo yes || echo no)"

# --- 13. security check on the demo project ---
echo "--- security check ---"
"$PY" -m novel_workflow.cli check "$DEST" --security | "$PY" -c "import json,sys; d=json.load(sys.stdin); print('project_errors:', d['project_errors']); print('chapter_errors:', d['chapter_errors']); print('security_findings:', d['security_findings'])"

echo "--- final status ---"
"$PY" -m novel_workflow.cli status "$DEST" --chapter 1 | "$PY" -c "import json,sys; d=json.load(sys.stdin); print('chapter status:', d['chapter']['status']); print('released_at:', d['chapter'].get('released_at'))"

echo
echo "DEMO_COMPLETE: $DEST"
