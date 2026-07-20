"""Command-line interface for the six-role novel workflow."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import (
    CHAPTER_GATES,
    DOMAIN_GATES,
    OUTLINE_LEVELS,
    SIX_ROLES,
    analyze_intake,
    init_project,
    record_idea,
    review_concept,
    repair_concept,
    write_bible,
    write_outline,
    review_outline,
    repair_outline,
    lock_outline,
    issue_chapter,
    record_draft,
    review_chapter,
    repair_chapter,
    release_chapter,
    list_chapters,
    load_json,
    security_scan,
    validate_chapter,
    validate_project,
)


def emit(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _proj_path(ns) -> Path:
    return Path(ns.path)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="novel-workflow")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("init"); a.add_argument("path"); a.add_argument("--title", required=True)
    a = sub.add_parser("idea"); a.add_argument("path"); a.add_argument("--summary", required=True); a.add_argument("--interview", default="{}")
    a = sub.add_parser("intake-check"); a.add_argument("path"); a.add_argument("--interview", default="")
    a = sub.add_parser("concept-review"); a.add_argument("path"); a.add_argument("verdict"); a.add_argument("--artifact", required=True); a.add_argument("--reviewer", required=True)
    a = sub.add_parser("concept-repair"); a.add_argument("path"); a.add_argument("--summary", default=""); a.add_argument("--interview", default="{}"); a.add_argument("verdict"); a.add_argument("--artifact", required=True); a.add_argument("--reviewer", required=True)
    a = sub.add_parser("bible"); a.add_argument("path"); a.add_argument("--artifact", required=True)
    a = sub.add_parser("outline-write"); a.add_argument("path"); a.add_argument("level", choices=OUTLINE_LEVELS); a.add_argument("--artifact", required=True)
    a = sub.add_parser("outline-review"); a.add_argument("path"); a.add_argument("level", choices=OUTLINE_LEVELS); a.add_argument("verdict"); a.add_argument("--artifact", required=True); a.add_argument("--reviewer", required=True)
    a = sub.add_parser("outline-repair"); a.add_argument("path"); a.add_argument("level", choices=OUTLINE_LEVELS); a.add_argument("--artifact", required=True); a.add_argument("verdict"); a.add_argument("--review-artifact", required=True); a.add_argument("--reviewer", required=True)
    a = sub.add_parser("outline-lock"); a.add_argument("path")
    a = sub.add_parser("issue"); a.add_argument("path"); a.add_argument("chapter", type=int); a.add_argument("--title", required=True); a.add_argument("--goal", required=True)
    a = sub.add_parser("draft"); a.add_argument("path"); a.add_argument("chapter", type=int); a.add_argument("--artifact", required=True); a.add_argument("--prewrite", required=True); a.add_argument("--author", required=True)
    a = sub.add_parser("review"); a.add_argument("path"); a.add_argument("chapter", type=int); a.add_argument("gate", choices=CHAPTER_GATES); a.add_argument("verdict"); a.add_argument("--artifact", required=True); a.add_argument("--reviewer", required=True); a.add_argument("--reason", default="")
    a = sub.add_parser("repair"); a.add_argument("path"); a.add_argument("chapter", type=int); a.add_argument("--artifact", required=True); a.add_argument("--affected", nargs="+", required=True)
    a = sub.add_parser("release"); a.add_argument("path"); a.add_argument("chapter", type=int)
    a = sub.add_parser("status"); a.add_argument("path"); a.add_argument("--chapter", type=int, default=None)
    a = sub.add_parser("check"); a.add_argument("path"); a.add_argument("--security", action="store_true")
    a = sub.add_parser("roles"); a.add_argument("path")
    a = sub.add_parser("chapters"); a.add_argument("path")

    # Opt-in model routing layer. Core workflow stays no-network; this only
    # registers the subcommands. The model_cli module imports model_adapter,
    # which is stdlib-only and never imported by core.
    from . import model_cli
    model_cli.register(sub)

    ns = p.parse_args(argv)
    if getattr(ns, "_model_handler", None) is not None:
        return model_cli.run(ns)
    root = _proj_path(ns)
    try:
        if ns.command == "init":
            emit(init_project(root, ns.title))
        elif ns.command == "idea":
            interview = json.loads(ns.interview) if ns.interview else {}
            emit(record_idea(root, ns.summary, interview))
        elif ns.command == "intake-check":
            if ns.interview:
                interview = json.loads(ns.interview)
            else:
                idea_path = root / "idea" / "idea.json"
                if not idea_path.exists():
                    raise ValueError("no recorded idea; pass --interview JSON or run idea first")
                interview = load_json(idea_path).get("interview", {})
            report = analyze_intake(interview)
            emit(report)
            return 0 if report["status"] == "COMPLETE" else 1
        elif ns.command == "concept-review":
            emit(review_concept(root, ns.verdict, ns.artifact, ns.reviewer))
        elif ns.command == "concept-repair":
            interview = json.loads(ns.interview) if ns.interview else {}
            emit(repair_concept(root, ns.summary or None, interview or None, ns.verdict, ns.artifact, ns.reviewer))
        elif ns.command == "bible":
            emit(write_bible(root, ns.artifact))
        elif ns.command == "outline-write":
            emit(write_outline(root, ns.level, ns.artifact))
        elif ns.command == "outline-review":
            emit(review_outline(root, ns.level, ns.verdict, ns.artifact, ns.reviewer))
        elif ns.command == "outline-repair":
            emit(repair_outline(root, ns.level, ns.artifact, ns.verdict, ns.review_artifact, ns.reviewer))
        elif ns.command == "outline-lock":
            emit(lock_outline(root))
        elif ns.command == "issue":
            emit(issue_chapter(root, ns.chapter, ns.title, ns.goal))
        elif ns.command == "draft":
            emit(record_draft(root, ns.chapter, ns.artifact, ns.prewrite, ns.author))
        elif ns.command == "review":
            emit(review_chapter(root, ns.chapter, ns.gate, ns.verdict, ns.artifact, ns.reviewer, ns.reason))
        elif ns.command == "repair":
            emit(repair_chapter(root, ns.chapter, ns.artifact, ns.affected))
        elif ns.command == "release":
            emit(release_chapter(root, ns.chapter))
        elif ns.command == "status":
            proj = load_json(root / "workflow.json")
            result: dict = {"project": proj, "project_errors": validate_project(proj)}
            if ns.chapter is not None:
                sp = root / ".novel-workflow" / f"chapter-{ns.chapter}.json"
                if sp.exists():
                    st = load_json(sp)
                    result["chapter"] = st
                    result["chapter_errors"] = validate_chapter(st)
            emit(result)
        elif ns.command == "check":
            states: dict[str, list[str]] = {}
            nw = root / ".novel-workflow"
            if nw.exists():
                for cp in nw.glob("chapter-*.json"):
                    states[cp.name] = validate_chapter(load_json(cp))
            proj = load_json(root / "workflow.json")
            proj_errors = validate_project(proj)
            findings = security_scan(root) if ns.security else []
            emit({"project_errors": proj_errors, "chapter_errors": states, "security_findings": findings})
            return 1 if proj_errors or any(states.values()) or findings else 0
        elif ns.command == "roles":
            from .core import ROLE_CHARTER
            emit({"roles": list(SIX_ROLES), "charter": ROLE_CHARTER})
        elif ns.command == "chapters":
            emit({"chapters": list_chapters(root)})
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        emit({"error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
