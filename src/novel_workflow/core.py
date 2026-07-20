"""Six-role, gate-driven long-form fiction workflow core.

Design summary
--------------
Project lifecycle:
    IDEA -> CONCEPT_REVIEW (+ repair) -> STORY_BIBLE ->
    OUTLINE_MASTER / OUTLINE_VOLUME / OUTLINE_CHAPTER (review + repair each) ->
    OUTLINE_LOCKED -> CHAPTER_ISSUED -> DRAFT_RECORDED ->
    CHAPTER_REVIEW -> (repair resets affected gates) -> READY_TO_RELEASE -> RELEASED

Six roles:
    controller, author, editor, reader, military_consultant, science_consultant

Chapter gates:
    author, editor, reader              -> PASS | FAIL
    military, science                   -> PASS | FAIL | SKIP_WITH_REASON
    release                             -> explicit command with receipt

Independence:
    editor and reader reviewers must not share the provenance entity recorded
    for the author, and the reader must differ from the editor. Author Role OS
    prewrite evidence is required before a draft is recorded.

False-completion guards:
    - chapters cannot be issued until OUTLINE_LOCKED
    - drafts cannot be recorded until chapter is ISSUED
    - chapter review gates cannot pass until a draft exists
    - release requires every chapter gate PASS or SKIP_WITH_REASON
    - repair resets affected gates to PENDING and removes stale release receipts
    - validate_chapter detects tampered states claiming RELEASED without evidence
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- Constants -------------------------------------------------------------

SIX_ROLES = (
    "controller",
    "author",
    "editor",
    "reader",
    "military_consultant",
    "science_consultant",
)

ROLE_CHARTER = {
    "controller": "Decomposes the project into stages, routes work, records state, verifies evidence, and blocks false completion. Does not author or review prose.",
    "author": "Produces the candidate draft from a chapter contract and the Author Role OS prewrite card. Owns voice, not gates.",
    "editor": "Independent review of structure, pacing, prose, DEAI (de-AI) compliance, and audience-respect. Provenance must differ from author.",
    "reader": "Independent review of real reading experience: clarity, immersion, over-explanation, fatigue. Provenance must differ from author and editor.",
    "military_consultant": "Domain review for tactics, force structure, conflict plausibility. May SKIP_WITH_REASON when no applicable content; may not be absent.",
    "science_consultant": "Domain review for physical, biological, technical plausibility. May SKIP_WITH_REASON when no applicable content; may not be absent.",
}

REVIEW_GATES = ("author", "editor", "reader")
DOMAIN_GATES = ("military", "science")
CHAPTER_GATES = REVIEW_GATES + DOMAIN_GATES
REQUIRED_GATES = CHAPTER_GATES  # release derives from these
PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP_WITH_REASON"
PENDING = "PENDING"

PROJECT_STAGES = (
    "IDEA",
    "CONCEPT_REVIEWED",
    "STORY_BIBLE",
    "OUTLINE_MASTER",
    "OUTLINE_VOLUME",
    "OUTLINE_CHAPTER",
    "OUTLINE_LOCKED",
)

OUTLINE_LEVELS = ("master", "volume", "chapter")

SCHEMA_VERSION = 2

# Structured intake is deliberately genre-neutral. Values may be strings,
# lists, or mappings, but every section must carry a substantive answer before
# concept review. The workflow asks for decisions; it never fills them from a
# private corpus or silently copies a previously read novel.
INTAKE_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("audience", "Reader promise", "Who is the intended reader and what experience is promised?"),
    ("genre", "Genre and positioning", "What is the primary genre, secondary elements, and market position?"),
    ("target_words", "Length plan", "What is the target total word count and acceptable range?"),
    ("premise", "Core premise", "Who faces what disruption, pursues what goal, against what resistance?"),
    ("world", "Background and world", "When and where does it happen, and which world rules cannot be broken?"),
    ("protagonist", "Protagonist", "What do they want, need, fear, know, and risk losing?"),
    ("supporting_cast", "Supporting cast", "Which relationships, incentives, and conflicts move the story?"),
    ("central_conflict", "Conflict engine", "What renewable conflict can sustain the planned length?"),
    ("stakes", "Stakes and cost", "What changes on personal, relational, and external levels if they fail?"),
    ("character_arc", "Character arc", "What belief or behaviour changes, through which costly turning points?"),
    ("style", "Style contract", "Specify POV, tense, tone, prose density, dialogue, pacing, and forbidden habits."),
    ("structure", "Structure plan", "What are the major phases, volume functions, escalation, midpoint, and ending?"),
    ("ending", "Ending and payoff", "What resolves, what remains open, and which promises must be paid off?"),
    ("boundaries", "Content boundaries", "What must the story avoid: themes, depictions, clichés, or platform risks?"),
    ("craft_patterns", "Abstract craft references", "Which abstract patterns may guide the work, and why? No copied text or private names."),
)
INTAKE_FIELD_KEYS = tuple(item[0] for item in INTAKE_FIELDS)


def _substantive(value: Any) -> bool:
    """Return whether an intake answer contains a real decision."""
    if value is None:
        return False
    if isinstance(value, str):
        return len(value.strip()) >= 2
    if isinstance(value, (list, tuple, set)):
        return bool(value) and all(_substantive(item) for item in value)
    if isinstance(value, dict):
        return bool(value) and all(str(k).strip() and _substantive(v) for k, v in value.items())
    if isinstance(value, (int, float)):
        return value > 0
    return bool(value)


def complete_intake_example() -> dict:
    """Return a fictional, provider-neutral intake used by demos and tests."""
    return {
        "audience": "adult speculative-fiction readers seeking grounded tension",
        "genre": "science fiction mystery with workplace survival pressure",
        "target_words": {"target": 90000, "range": "80000-100000"},
        "premise": "A relay repair lead must identify an impossible signal before the station is abandoned.",
        "world": "A remote orbital relay where light delay, scarce air, and strict safety rules shape daily life.",
        "protagonist": "A cautious repair lead wants to protect the crew but fears reporting uncertain evidence.",
        "supporting_cast": "A cost-driven manager, a risk-seeking technician, and a distant investigator have conflicting incentives.",
        "central_conflict": "Each attempt to verify the signal consumes safety margin and increases institutional pressure.",
        "stakes": "Failure risks the crew, their livelihoods, and evidence of a wider danger.",
        "character_arc": "The lead moves from protective silence to accountable truth-telling through costly choices.",
        "style": "close third person, past tense, restrained prose, concrete sensory feedback, no explanatory monologues",
        "structure": "four phases: anomaly, denial, costly verification, public choice and aftermath",
        "ending": "the signal is verified, the crew survives at a cost, and the wider source remains open",
        "boundaries": "no copied franchise lore, no effortless technical solutions, no glamorised preventable harm",
        "craft_patterns": ["escalate clue certainty while shrinking physical safety margin; use original scenes and terms"],
    }


def analyze_intake(interview: dict) -> dict:
    """Deterministically report structured-novel-intake completeness.

    The report is intentionally model-free and safe to run offline. It tells a
    beginner exactly which decision comes next. Extra fields are retained as
    user extensions; required fields are stable public workflow contracts.
    """
    if not isinstance(interview, dict):
        raise ValueError("interview must be a JSON object")
    completed = [key for key in INTAKE_FIELD_KEYS if _substantive(interview.get(key))]
    missing = [key for key in INTAKE_FIELD_KEYS if key not in completed]
    next_item = next((item for item in INTAKE_FIELDS if item[0] in missing), None)
    return {
        "status": "COMPLETE" if not missing else "INCOMPLETE",
        "required_count": len(INTAKE_FIELDS),
        "completed_count": len(completed),
        "completion_percent": round(len(completed) * 100 / len(INTAKE_FIELDS), 1),
        "completed_fields": completed,
        "missing_fields": missing,
        "next_question": None if next_item is None else {
            "field": next_item[0], "section": next_item[1], "question": next_item[2]
        },
        "copyright_boundary": (
            "Use prior reading only as abstract craft patterns. Do not copy protected "
            "expression, distinctive names, setting combinations, scenes, or private corpus text."
        ),
    }


# --- Utilities -------------------------------------------------------------

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_event(root: Path, event: dict) -> None:
    path = root / ".novel-workflow" / "events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": utcnow(), **event}, ensure_ascii=False) + "\n")


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _sha256_full(text: str) -> str:
    """Full 64-char sha256 hex digest, used for review attestation."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Field labels the reviewer must cite inside a PASS review artifact. Kept as
# plain strings (case-insensitive, whitespace-tolerant) so the evidence can be
# embedded in a markdown table, a YAML block, or a free-form paragraph. The
# hard gate is the presence *and* the value, not the formatting.
_REVIEWED_FULLTEXT_RE = re.compile(
    r"reviewed_fulltext\s*[:=]\s*['\"]?true['\"]?", re.I
)
_CANDIDATE_SHA_RE = re.compile(
    r"candidate_sha256\s*[:=]\s*['\"]?([0-9a-fA-F]{64})['\"]?", re.I
)
_CROSS_CHAPTER_RE = re.compile(
    r"CROSS_CHAPTER_CONSISTENCY\s*[:=]\s*['\"]?PASS['\"]?", re.I
)
_NUMERICAL_CONSISTENCY_RE = re.compile(
    r"NUMERICAL_CONSISTENCY\s*[:=]\s*['\"]?PASS['\"]?", re.I
)


def _require_review_fulltext_attestation(
    draft_text: str, review_text: str, gate: str
) -> None:
    """Hard gate: a PASS review must attest full-text review of the right draft.

    Raises ``ValueError`` when the review artifact lacks
    ``reviewed_fulltext: true`` or cites a ``candidate_sha256`` that does not
    equal the sha256 of the draft currently under review. This stops the
    common failure of reviewing a summary, a stale draft, or the wrong
    chapter.
    """
    if not _REVIEWED_FULLTEXT_RE.search(review_text):
        raise ValueError(
            f"{gate} PASS review missing reviewed_fulltext: true attestation"
        )
    m = _CANDIDATE_SHA_RE.search(review_text)
    if not m:
        raise ValueError(
            f"{gate} PASS review missing candidate_sha256 attestation"
        )
    cited = m.group(1).lower()
    actual = _sha256_full(draft_text)
    if cited != actual:
        raise ValueError(
            f"{gate} PASS review candidate_sha256 mismatch: review cites "
            f"{cited[:12]}... but current draft is {actual[:12]}..."
        )


def _entity(provenance: str) -> str:
    """Return the identity entity from a `role:identifier` provenance string.

    Two provenance strings sharing the same entity are treated as the same
    reviewer and therefore not independent. The role prefix is intentionally
    ignored so that `author:alice` and `editor:alice` collide.
    """
    if not provenance:
        return ""
    return provenance.split(":", 1)[1].strip().lower()


def _validate_artifact(root: Path, artifact: str) -> Path:
    if not artifact:
        raise ValueError("artifact path is required")
    artifact_path = (root / artifact).resolve()
    if root.resolve() not in artifact_path.parents and artifact_path != root.resolve():
        raise ValueError("artifact must stay inside project root")
    if not artifact_path.exists():
        raise ValueError(f"artifact missing: {artifact}")
    return artifact_path


def _record_artifact(root: Path, artifact: str, reviewer: str, extra: dict | None = None) -> dict:
    path = _validate_artifact(root, artifact)
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        text = ""
    rec: dict[str, Any] = {
        "path": artifact,
        "reviewer": reviewer,
        "checksum": _checksum(text),
        "sha256": _sha256_full(text),
        "recorded_at": utcnow(),
    }
    if extra:
        rec.update(extra)
    return rec


def _artifact_text(root: Path, artifact: str) -> str:
    return _validate_artifact(root, artifact).read_text(encoding="utf-8", errors="ignore")


def _require_keywords(text: str, labels: tuple[str, ...], context: str) -> None:
    normalized = text.casefold()
    missing = [label for label in labels if label.casefold() not in normalized]
    if missing:
        raise ValueError(f"{context} missing required evidence: {', '.join(missing)}")


def _validate_prewrite_evidence(root: Path, artifact: str) -> None:
    text = _artifact_text(root, artifact)
    _require_keywords(
        text,
        (
            "Chapter function",
            "Three-event chain",
            "Central choice",
            "Voice anchors",
            "Forbidden drift",
            "Human-writing constraints",
        ),
        "author_role_os prewrite card",
    )


def _validate_review_evidence(
    root: Path, gate: str, artifact: str, verdict: str, draft_text: str
) -> None:
    """Hard gates for a PASS review artifact.

    ``reviewed_fulltext: true`` and a ``candidate_sha256`` matching the draft
    under review are required on *every* PASS review (editor, reader, and the
    domain consultants when they PASS rather than skip). The editor and reader
    gates additionally require ``CROSS_CHAPTER_CONSISTENCY: PASS``. The
    science gate additionally requires ``NUMERICAL_CONSISTENCY: PASS``.

    These were previously documented conventions; they are now code gates so a
    PASS on a summary, a stale draft, or a review that skipped the
    cross-chapter / numerical checks is refused at ``review_chapter`` time.
    """
    if verdict != PASS:
        return
    text = _artifact_text(root, artifact)
    # Every PASS review must attest it read the full current draft.
    _require_review_fulltext_attestation(draft_text, text, gate)
    if gate == "editor":
        _require_keywords(text, ("DEAI", "Audience respect"), "editor PASS review")
        if not _CROSS_CHAPTER_RE.search(text):
            raise ValueError("editor PASS review missing CROSS_CHAPTER_CONSISTENCY: PASS")
    elif gate == "reader":
        _require_keywords(
            text,
            ("Real reading experience", "Immersion", "Over-explanation"),
            "reader PASS review",
        )
        if not _CROSS_CHAPTER_RE.search(text):
            raise ValueError("reader PASS review missing CROSS_CHAPTER_CONSISTENCY: PASS")
    elif gate == "science":
        if not _NUMERICAL_CONSISTENCY_RE.search(text):
            raise ValueError("science PASS review missing NUMERICAL_CONSISTENCY: PASS")


# Maps each chapter gate to the role name(s) whose reviewers may sign it.
# Domain gates accept both the short gate name (``military:``) and the full
# role name (``military_consultant:``) so documentation and CLI examples that
# use the six-role names work without surprising users. Review gates share
# their gate and role name.
GATE_ROLE_PREFIXES: dict[str, tuple[str, ...]] = {
    "author": ("author",),
    "editor": ("editor",),
    "reader": ("reader",),
    "military": ("military", "military_consultant"),
    "science": ("science", "science_consultant"),
}


def _require_reviewer_prefix(gate: str, reviewer: str) -> None:
    allowed = GATE_ROLE_PREFIXES.get(gate, (gate,))
    if not any(reviewer.startswith(f"{prefix}:") for prefix in allowed):
        choices = " or ".join(f"{p}:" for p in allowed)
        raise ValueError(f"{gate} reviewer provenance must be prefixed '{choices}'")


def _load_project(root: Path) -> dict:
    p = root / "workflow.json"
    if not p.exists():
        raise ValueError("workflow.json missing; run init first")
    return load_json(p)


def _save_project(root: Path, proj: dict) -> None:
    proj["updated_at"] = utcnow()
    save_json(root / "workflow.json", proj)


def _require_stage(proj: dict, stage: str) -> None:
    reached = proj.get("stage")
    idx = PROJECT_STAGES.index(stage)
    if reached not in PROJECT_STAGES[: idx + 1]:
        raise ValueError(
            f"stage '{stage}' not reached (current: {reached}); earlier gates required"
        )


# --- Project lifecycle -----------------------------------------------------

def init_project(root: Path, title: str) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    for name in ("story-bible", "outlines", "chapters", "reviews", "releases", "idea", "assets"):
        (root / name).mkdir(exist_ok=True)
    proj = {
        "schema_version": SCHEMA_VERSION,
        "title": title,
        "stage": "IDEA",
        "roles": list(SIX_ROLES),
        "role_charter": dict(ROLE_CHARTER),
        "outline_levels": list(OUTLINE_LEVELS),
        "outline": {lvl: {"status": "PENDING", "artifact": None, "review": None} for lvl in OUTLINE_LEVELS},
        "concept": {"status": "PENDING", "artifact": None, "review": None},
        "bible": {"status": "PENDING", "artifact": None},
        "idea": None,
        "chapters": {},
    }
    _save_project(root, proj)
    append_event(root, {"type": "PROJECT_INITIALIZED", "title": title})
    return proj


def record_idea(root: Path, summary: str, interview: dict) -> dict:
    proj = _load_project(root)
    intake = analyze_intake(interview)
    idea = {
        "summary": summary,
        "interview": dict(interview),
        "intake_analysis": intake,
        "recorded_at": utcnow(),
    }
    proj["idea"] = idea
    _save_project(root, proj)
    (root / "idea" / "idea.json").parent.mkdir(parents=True, exist_ok=True)
    save_json(root / "idea" / "idea.json", idea)
    append_event(root, {"type": "IDEA_RECORDED", "summary": summary})
    return proj


def review_concept(root: Path, verdict: str, artifact: str, reviewer: str) -> dict:
    verdict = verdict.upper()
    if verdict not in {PASS, FAIL}:
        raise ValueError("concept verdict must be PASS or FAIL")
    proj = _load_project(root)
    if proj.get("idea") is None:
        raise ValueError("record an idea before concept review")
    intake = analyze_intake(proj["idea"].get("interview", {}))
    if intake["status"] != "COMPLETE":
        raise ValueError(
            "concept review requires complete structured intake; missing: "
            + ", ".join(intake["missing_fields"])
        )
    rec = _record_artifact(root, artifact, reviewer, {"verdict": verdict})
    proj["concept"] = {"status": verdict, "artifact": artifact, "review": rec}
    if verdict == PASS:
        proj["stage"] = "CONCEPT_REVIEWED"
    else:
        proj["stage"] = "IDEA"
    _save_project(root, proj)
    append_event(root, {"type": "CONCEPT_REVIEWED", "verdict": verdict, "reviewer": reviewer})
    return proj


def repair_concept(root: Path, new_summary: str | None, new_interview: dict | None, verdict: str, artifact: str, reviewer: str) -> dict:
    proj = _load_project(root)
    if proj.get("concept", {}).get("status") != FAIL:
        raise ValueError("repair_concept only valid after a FAIL concept review")
    if new_summary or new_interview:
        record_idea(root, new_summary or proj["idea"]["summary"], new_interview or proj["idea"]["interview"])
    return review_concept(root, verdict, artifact, reviewer)


def write_bible(root: Path, artifact: str) -> dict:
    proj = _load_project(root)
    if proj.get("concept", {}).get("status") != PASS:
        raise ValueError("story bible requires concept PASS")
    _validate_artifact(root, artifact)
    proj["bible"] = {"status": "WRITTEN", "artifact": artifact, "recorded_at": utcnow()}
    proj["stage"] = "STORY_BIBLE"
    _save_project(root, proj)
    append_event(root, {"type": "STORY_BIBLE_WRITTEN", "artifact": artifact})
    return proj


def write_outline(root: Path, level: str, artifact: str) -> dict:
    if level not in OUTLINE_LEVELS:
        raise ValueError(f"outline level must be one of {OUTLINE_LEVELS}")
    proj = _load_project(root)
    if proj.get("bible", {}).get("status") != "WRITTEN":
        raise ValueError("outline requires story bible")
    level_idx = OUTLINE_LEVELS.index(level)
    if level_idx > 0:
        prev = OUTLINE_LEVELS[level_idx - 1]
        if proj["outline"][prev]["status"] != PASS:
            raise ValueError(f"outline '{prev}' must be PASS before writing '{level}'")
    _validate_artifact(root, artifact)
    proj["outline"][level] = {"status": "WRITTEN", "artifact": artifact, "review": None}
    stage = f"OUTLINE_{level.upper()}"
    if stage in PROJECT_STAGES and PROJECT_STAGES.index(stage) > PROJECT_STAGES.index(proj.get("stage", "IDEA")):
        proj["stage"] = stage
    _save_project(root, proj)
    append_event(root, {"type": "OUTLINE_WRITTEN", "level": level, "artifact": artifact})
    return proj


def review_outline(root: Path, level: str, verdict: str, artifact: str, reviewer: str) -> dict:
    if level not in OUTLINE_LEVELS:
        raise ValueError(f"outline level must be one of {OUTLINE_LEVELS}")
    verdict = verdict.upper()
    if verdict not in {PASS, FAIL}:
        raise ValueError("outline verdict must be PASS or FAIL")
    proj = _load_project(root)
    ol = proj["outline"][level]
    if ol.get("status") != "WRITTEN":
        raise ValueError(f"outline '{level}' must be written before review")
    rec = _record_artifact(root, artifact, reviewer, {"verdict": verdict})
    proj["outline"][level] = {"status": verdict, "artifact": ol["artifact"], "review": rec}
    if verdict == FAIL:
        # allow rewrite; status becomes PENDING so lock_outline blocks
        proj["outline"][level]["status"] = FAIL
    _save_project(root, proj)
    append_event(root, {"type": "OUTLINE_REVIEWED", "level": level, "verdict": verdict, "reviewer": reviewer})
    return proj


def repair_outline(root: Path, level: str, new_artifact: str, verdict: str, review_artifact: str, reviewer: str) -> dict:
    if level not in OUTLINE_LEVELS:
        raise ValueError(f"outline level must be one of {OUTLINE_LEVELS}")
    proj = _load_project(root)
    if proj["outline"][level].get("status") != FAIL:
        raise ValueError("repair_outline only valid after a FAIL review")
    write_outline(root, level, new_artifact)
    return review_outline(root, level, verdict, review_artifact, reviewer)


def lock_outline(root: Path) -> dict:
    proj = _load_project(root)
    for level in OUTLINE_LEVELS:
        if proj["outline"][level].get("status") != PASS:
            raise ValueError(f"outline '{level}' is not PASS; cannot lock")
    proj["stage"] = "OUTLINE_LOCKED"
    proj["outline_locked_at"] = utcnow()
    _save_project(root, proj)
    append_event(root, {"type": "OUTLINE_LOCKED"})
    return proj


def _chapter_state_path(root: Path, chapter: int) -> Path:
    return root / ".novel-workflow" / f"chapter-{chapter}.json"


def _extract_title(text: str) -> str:
    """Best-effort title extraction from an outline or draft artifact.

    Looks for a ``Title (working): X`` line first (the chapter-outline
    template convention), then a markdown level-1 heading ``# X``. Returns
    the stripped title or an empty string when neither is present.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("title (working):"):
            return stripped.split(":", 1)[1].strip()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.lower().startswith("# chapter"):
            return stripped[2:].strip()
    return ""


def _check_source_alignment(root: Path, draft_artifact: str) -> None:
    """Reject a draft whose title disagrees with the chapter outline title.

    Implements the SOURCE_MISMATCH guard: the editor must never review a
    chapter that was written against the wrong outline. The chapter outline
    artifact path is read from the project's locked outline. If both the
    outline and the draft expose a title and they differ (case-insensitive),
    recording the draft is refused.
    """
    proj = _load_project(root)
    outline_artifact = proj.get("outline", {}).get("chapter", {}).get("artifact")
    if not outline_artifact:
        return
    try:
        outline_text = _artifact_text(root, outline_artifact)
    except ValueError:
        return
    draft_text = _artifact_text(root, draft_artifact)
    outline_title = _extract_title(outline_text)
    draft_title = _extract_title(draft_text)
    if outline_title and draft_title and outline_title.lower() != draft_title.lower():
        raise ValueError(
            f"SOURCE_MISMATCH: draft title '{draft_title}' does not match "
            f"chapter outline title '{outline_title}'"
        )


def _chapter_ledger_entry(state: dict) -> dict:
    """Build a compact ledger summary from a chapter state object."""
    return {
        "status": state.get("status"),
        "title": state.get("title"),
        "goal": state.get("goal"),
        "gates": dict(state.get("gates", {})),
        "released_at": state.get("released_at"),
        "updated_at": state.get("updated_at"),
    }


def _sync_chapter_ledger(root: Path, state: dict) -> None:
    """Mirror a chapter's status into the project-level chapters ledger.

    The ledger lives in ``workflow.json.chapters`` keyed by chapter number
    (as a string). It is a *summary* - the per-chapter state file remains
    the source of truth. This lets ``list_chapters`` and the CLI ``chapters``
    command show whole-book progress without opening every chapter file.
    """
    proj = _load_project(root)
    chapters = proj.setdefault("chapters", {})
    chapters[str(state["chapter"])] = _chapter_ledger_entry(state)
    _save_project(root, proj)


def list_chapters(root: Path) -> dict:
    """Return the whole-book chapter ledger.

    Merges the persisted ledger in ``workflow.json`` with any per-chapter
    state files on disk, so a chapter whose ledger entry is stale (e.g. the
    state file was edited directly) is still reflected. Returns a dict
    keyed by chapter number string, each value a ledger entry.
    """
    proj = _load_project(root)
    ledger: dict[str, dict] = {}
    existing = proj.get("chapters", {})
    if isinstance(existing, dict):
        for k, v in existing.items():
            ledger[str(k)] = dict(v)
    nw = root / ".novel-workflow"
    if nw.exists():
        for cp in sorted(nw.glob("chapter-*.json"), key=lambda p: int(p.stem.split("-", 1)[1])):
            try:
                state = load_json(cp)
            except (OSError, ValueError):
                continue
            num = str(state.get("chapter") or cp.stem.split("-", 1)[1])
            ledger[num] = _chapter_ledger_entry(state)
    return ledger


def issue_chapter(root: Path, chapter: int, title: str, goal: str, contract: dict | None = None) -> dict:
    proj = _load_project(root)
    if proj.get("stage") != "OUTLINE_LOCKED":
        raise ValueError("outline must be LOCKED before issuing a chapter")
    state_path = _chapter_state_path(root, chapter)
    if state_path.exists():
        raise ValueError(f"chapter {chapter} already exists")
    c = {
        "schema_version": SCHEMA_VERSION,
        "chapter": chapter,
        "title": title,
        "goal": goal,
        "contract": contract or {},
        "status": "ISSUED",
        "draft": None,
        "prewrite": None,
        "author_provenance": None,
        "gates": {g: PENDING for g in CHAPTER_GATES},
        "skip_reasons": {},
        "artifacts": {},
        "independence": {},
        "revisions": [],
        "updated_at": utcnow(),
    }
    save_json(state_path, c)
    _sync_chapter_ledger(root, c)
    append_event(root, {"type": "CHAPTER_ISSUED", "chapter": chapter, "title": title})
    return c


def record_draft(root: Path, chapter: int, artifact: str, prewrite_artifact: str, author_provenance: str) -> dict:
    proj = _load_project(root)
    state_path = _chapter_state_path(root, chapter)
    if not state_path.exists():
        raise ValueError(f"chapter {chapter} not issued; cannot record draft")
    state = load_json(state_path)
    if state["status"] not in {"ISSUED", "BLOCKED", "IN_REVIEW"}:
        raise ValueError(f"chapter {chapter} status '{state['status']}' cannot accept draft")
    if not author_provenance.startswith("author:"):
        raise ValueError("author_provenance must be prefixed 'author:'")
    _validate_prewrite_evidence(root, prewrite_artifact)
    _check_source_alignment(root, artifact)
    pre = _record_artifact(root, prewrite_artifact, author_provenance, {"kind": "author_role_os_prewrite"})
    draft = _record_artifact(root, artifact, author_provenance, {"kind": "draft"})
    state["draft"] = draft
    state["prewrite"] = pre
    state["author_provenance"] = author_provenance
    state["gates"]["author"] = PASS  # author gate = a candidate exists with prewrite
    state["artifacts"]["author"] = draft
    state["independence"]["author"] = author_provenance
    state["status"] = "IN_REVIEW"
    state["updated_at"] = utcnow()
    save_json(state_path, state)
    _sync_chapter_ledger(root, state)
    append_event(root, {"type": "DRAFT_RECORDED", "chapter": chapter, "author": author_provenance})
    return state


def _check_independence(state: dict, gate: str, reviewer: str) -> None:
    author_ent = _entity(state.get("author_provenance", ""))
    reviewer_ent = _entity(reviewer)
    if not author_ent or not reviewer_ent:
        raise ValueError("reviewer provenance must be `role:identifier`")
    if author_ent == reviewer_ent:
        raise ValueError(f"independence violation: {gate} reviewer shares entity with author")
    if gate == "reader":
        editor_ent = _entity(state.get("independence", {}).get("editor", ""))
        if editor_ent and editor_ent == reviewer_ent:
            raise ValueError("independence violation: reader shares entity with editor")


def review_chapter(root: Path, chapter: int, gate: str, verdict: str, artifact: str, reviewer: str, reason: str = "") -> dict:
    if gate not in CHAPTER_GATES:
        raise ValueError(f"unknown chapter gate: {gate}")
    _require_reviewer_prefix(gate, reviewer)
    state_path = _chapter_state_path(root, chapter)
    state = load_json(state_path)
    if state.get("draft") is None:
        raise ValueError(f"chapter {chapter}: cannot review before a draft is recorded")
    verdict = verdict.upper()
    if gate in DOMAIN_GATES:
        if verdict not in {PASS, FAIL, SKIP}:
            raise ValueError(f"domain gate {gate} verdict must be PASS, FAIL, or SKIP_WITH_REASON")
        if verdict == SKIP and not reason.strip():
            raise ValueError(f"domain gate {gate} SKIP_WITH_REASON requires a reason")
    else:
        if verdict not in {PASS, FAIL}:
            raise ValueError(f"review gate {gate} verdict must be PASS or FAIL")
    _check_independence(state, gate, reviewer)
    draft_artifact = state["draft"]["path"]
    draft_text = _artifact_text(root, draft_artifact)
    _validate_review_evidence(root, gate, artifact, verdict, draft_text)
    rec = _record_artifact(root, artifact, reviewer, {"verdict": verdict, "reason": reason})
    state["gates"][gate] = verdict
    state["artifacts"][gate] = rec
    state["independence"][gate] = reviewer
    if verdict == SKIP:
        state["skip_reasons"][gate] = reason
    elif gate in state.get("skip_reasons", {}):
        del state["skip_reasons"][gate]
    state["status"] = _derive_chapter_status(state)
    state["updated_at"] = utcnow()
    save_json(state_path, state)
    _sync_chapter_ledger(root, state)
    append_event(root, {"type": "CHAPTER_GATE_RECORDED", "chapter": chapter, "gate": gate, "verdict": verdict, "reviewer": reviewer})
    return state


def repair_chapter(root: Path, chapter: int, new_draft_artifact: str, affected_gates: list[str]) -> dict:
    state_path = _chapter_state_path(root, chapter)
    state = load_json(state_path)
    if state.get("draft") is None:
        raise ValueError(f"chapter {chapter}: cannot repair without an existing draft")
    author = state.get("author_provenance") or "author:repair"
    draft = _record_artifact(root, new_draft_artifact, author, {"kind": "draft", "revision": True})
    state["draft"] = draft
    state["artifacts"]["author"] = draft
    reset: list[str] = []
    for g in affected_gates:
        if g not in CHAPTER_GATES:
            raise ValueError(f"unknown affected gate: {g}")
        if g == "author":
            continue
        state["gates"][g] = PENDING
        state["artifacts"].pop(g, None)
        state["independence"].pop(g, None)
        state.get("skip_reasons", {}).pop(g, None)
        reset.append(g)
    state["status"] = "IN_REVIEW"
    state.pop("released_at", None)
    receipt_path = root / "releases" / f"chapter-{chapter}.json"
    if receipt_path.exists():
        receipt_path.unlink()
    state["revisions"].append({"at": utcnow(), "reset_gates": reset, "draft": new_draft_artifact})
    state["updated_at"] = utcnow()
    save_json(state_path, state)
    _sync_chapter_ledger(root, state)
    append_event(root, {"type": "CHAPTER_REPAIR", "chapter": chapter, "reset_gates": reset})
    return state


def _derive_chapter_status(state: dict) -> str:
    gates = state.get("gates", {})
    if any(gates.get(g) == FAIL for g in CHAPTER_GATES):
        return "BLOCKED"
    if all(_gate_satisfied(g, gates.get(g)) for g in CHAPTER_GATES):
        return "READY_TO_RELEASE"
    return "IN_REVIEW"


def _gate_satisfied(gate: str, verdict: str) -> bool:
    if gate in DOMAIN_GATES:
        return verdict in {PASS, SKIP}
    return verdict == PASS


def release_chapter(root: Path, chapter: int) -> dict:
    state_path = _chapter_state_path(root, chapter)
    state = load_json(state_path)
    if state.get("draft") is None:
        raise ValueError(f"chapter {chapter}: no draft to release")
    gates = state.get("gates", {})
    missing = [g for g in CHAPTER_GATES if not _gate_satisfied(g, gates.get(g))]
    if missing:
        raise ValueError(f"chapter {chapter}: gates not satisfied: {missing}")
    if any(gates.get(g) == FAIL for g in CHAPTER_GATES):
        raise ValueError(f"chapter {chapter}: cannot release with FAIL gates")
    state["status"] = "RELEASED"
    state["released_at"] = utcnow()
    state["updated_at"] = utcnow()
    save_json(state_path, state)
    _sync_chapter_ledger(root, state)
    receipt = {
        "chapter": chapter,
        "title": state["title"],
        "status": "RELEASED",
        "released_at": state["released_at"],
        "gates": state["gates"],
        "skip_reasons": state.get("skip_reasons", {}),
    }
    (root / "releases").mkdir(parents=True, exist_ok=True)
    save_json(root / "releases" / f"chapter-{chapter}.json", receipt)
    append_event(root, {"type": "CHAPTER_RELEASED", "chapter": chapter})
    return state


# --- Validation ------------------------------------------------------------

def validate_chapter(state: dict) -> list[str]:
    errors: list[str] = []
    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported chapter schema_version")
    gates = state.get("gates", {})
    for g in CHAPTER_GATES:
        v = gates.get(g)
        if g in DOMAIN_GATES:
            if v not in {PENDING, PASS, FAIL, SKIP}:
                errors.append(f"invalid domain gate: {g}={v}")
        else:
            if v not in {PENDING, PASS, FAIL}:
                errors.append(f"invalid gate: {g}={v}")
    if state.get("status") == "RELEASED":
        if not all(_gate_satisfied(g, gates.get(g)) for g in CHAPTER_GATES):
            errors.append("false completion: RELEASED without all gates satisfied")
        if state.get("draft") is None:
            errors.append("false completion: RELEASED without draft")
        # independence on release
        ind = state.get("independence", {})
        author_ent = _entity(state.get("author_provenance", ""))
        for g in ("editor", "reader"):
            if not ind.get(g):
                errors.append(f"false completion: RELEASED without {g} reviewer provenance")
            elif _entity(ind[g]) == author_ent:
                errors.append(f"false completion: {g} shares entity with author")
        if _entity(ind.get("reader", "")) and _entity(ind.get("reader", "")) == _entity(ind.get("editor", "")):
            errors.append("false completion: reader shares entity with editor")
        for g in DOMAIN_GATES:
            if gates.get(g) == SKIP and not state.get("skip_reasons", {}).get(g):
                errors.append(f"false completion: {g} SKIP_WITH_REASON missing reason")
    if state.get("status") == "BLOCKED" and not any(gates.get(g) == FAIL for g in CHAPTER_GATES):
        # BLOCKED is allowed only via FAIL
        pass  # not an error; repairs also set IN_REVIEW
    return errors


def validate_project(proj: dict) -> list[str]:
    errors: list[str] = []
    if proj.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported project schema_version")
    if proj.get("stage") == "OUTLINE_LOCKED":
        for lvl in OUTLINE_LEVELS:
            if proj["outline"][lvl].get("status") != PASS:
                errors.append(f"OUTLINE_LOCKED but {lvl} not PASS")
    if set(proj.get("roles", [])) != set(SIX_ROLES):
        errors.append("role set mismatch")
    return errors


# --- Security scan ---------------------------------------------------------

def _scan_candidate_files(root: Path) -> list[tuple[str, Path]]:
    """Enumerate files the scanner should inspect, as (rel, path) pairs.

    The scanner inspects exactly the files that would be published: git-tracked
    files plus untracked, non-ignored files. This keeps the CLI ``check
    --security`` surface identical to ``scripts/release_check.py``. Scanning
    the whole working tree with ``rglob`` would otherwise inspect build
    artifacts (``build/``), the gitignored internal working files
    (``WAL.md``, ``SECURITY_RELEASE_CHECKLIST.md``), and other local-only
    files, producing false positives and hiding real leaks under noise.

    When the project root is not inside a git repository, the scanner falls
    back to walking the tree but still skips gitignored paths via
    ``git check-ignore`` so a non-git checkout is not scanned wholesale.

    The scanner's own source files are excluded by path relative to root,
    never by bare filename, so a contributor's same-named file is still
    scanned.
    """
    from ._security import SELF_EXCLUDE_RELS, TEXT_EXT

    import subprocess

    root_resolved = root.resolve()
    candidates: list[tuple[str, Path]] = []

    def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(root_resolved), *args],
            capture_output=True,
            text=True,
        )

    rels: set[str] = set()
    proc = _git(["ls-files"])
    if proc.returncode == 0:
        rels.update(line for line in proc.stdout.splitlines() if line)
        proc2 = _git(["ls-files", "--others", "--exclude-standard"])
        if proc2.returncode == 0:
            rels.update(line for line in proc2.stdout.splitlines() if line)
    else:
        # Not a git repo: walk the tree, but still honour .gitignore via
        # check-ignore so local-only files are skipped.
        for path in root_resolved.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            if any(part in {"output", ".novel-workflow", "build", "dist"} for part in path.parts):
                continue
            try:
                rel = path.resolve().relative_to(root_resolved).as_posix()
            except ValueError:
                continue
            ci = _git(["check-ignore", "-q", rel])
            if ci.returncode == 0:
                continue
            rels.add(rel)

    # License / ignore files: license text legitimately contains URLs and
    # brand names; .gitignore lists the internal patterns by name. These are
    # not code files and skipping them does not hide a leak - the same set is
    # skipped by scripts/release_check.py so the two surfaces agree.
    _NONCODE_SKIP = frozenset({".gitignore", "LICENSE", "NOTICE"})

    for rel in sorted(rels):
        if rel in SELF_EXCLUDE_RELS or rel in _NONCODE_SKIP:
            continue
        path = root_resolved / rel
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXT and path.name not in {"LICENSE", "NOTICE"}:
            continue
        candidates.append((rel, path))
    return candidates


def security_scan(root: Path) -> list[str]:
    """Scan publishable files for secrets, absolute paths, and private coupling.

    Uses the shared deny-list in :mod:`novel_workflow._security` so the CLI
    ``check --security`` command and ``scripts/release_check.py`` cannot drift.
    The scanner self-excludes its own source files by path, not filename.
    """
    from ._security import deny_list_findings

    findings: list[str] = []
    for rel, path in _scan_candidate_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        findings.extend(deny_list_findings(rel, text))
    return sorted(set(findings))
