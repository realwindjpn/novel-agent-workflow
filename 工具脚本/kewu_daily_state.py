#!/usr/bin/env python3
"""科武纪元 MVP 日报状态工具

CLI:
  python3 工具脚本/kewu_daily_state.py init --dry-run
  python3 工具脚本/kewu_daily_state.py init
  python3 工具脚本/kewu_daily_state.py status
  python3 工具脚本/kewu_daily_state.py emit --msg "..."
  python3 工具脚本/kewu_daily_state.py emit --event-type GATE --task-id upload_117 --chapter 117 --detail "..."
  python3 工具脚本/kewu_daily_state.py decision-card --task <name>
  python3 工具脚本/kewu_daily_state.py plan-upload --dry-run
  python3 工具脚本/kewu_daily_state.py gate-upload --chapter 117 --dry-run

stdlib only, py_compile safe.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths (relative to this script's parent -> project root)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

SOURCE_DIR = os.path.join(PROJECT_ROOT, "新版")
UPLOADED_DIR = os.path.join(PROJECT_ROOT, "已投稿")
ENGINE_DIR = os.path.join(PROJECT_ROOT, "审核记录", "自循环落地_20260528")
STATE_FILE = os.path.join(ENGINE_DIR, "state.json")
EVENTS_FILE = os.path.join(ENGINE_DIR, "events.jsonl")
RULES_FILE = os.path.join(ENGINE_DIR, "rules.yaml")
DECISION_DIR = os.path.join(PROJECT_ROOT, "审核记录", "决策卡")

TOMATO_MIN_CHARS = 3000
TOMATO_YELLOW_MIN = 2500  # P0: three-color gate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_state():
    if os.path.isfile(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "version": "1.0",
        "upload_cursor": None,
        "next_upload_chapters": [],
        "pipeline_stage": "init",
        "last_updated": None,
    }


def _save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    state["last_updated"] = datetime.now().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _append_event(event_type, payload):
    os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
    entry = {
        "ts": datetime.now().isoformat(),
        "type": event_type,
        "payload": payload,
    }
    with open(EVENTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _scan_uploaded():
    """Scan 已投稿/第*.txt, return max chapter number."""
    if not os.path.isdir(UPLOADED_DIR):
        return 0
    pattern = re.compile(r"^第(\d+)章\.txt$")
    max_ch = 0
    for fname in os.listdir(UPLOADED_DIR):
        m = pattern.match(fname)
        if m:
            ch = int(m.group(1))
            if ch > max_ch:
                max_ch = ch
    return max_ch


def _source_path(chapter):
    return os.path.join(SOURCE_DIR, f"第{chapter}章.md")


def _uploaded_path(chapter):
    return os.path.join(UPLOADED_DIR, f"第{chapter}章.txt")


def _read_text_if_exists(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _strip_markdown_for_count(text):
    """Best-effort cleanup for source MD before tomato-style counting."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s{0,3}>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+[.)、]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_~]+", "", text)
    text = re.sub(r"^\s*-{3,}\s*$", "", text, flags=re.MULTILINE)
    return text


def _compact_count(text):
    return len(re.sub(r"\s+", "", text or ""))


def _first_nonempty_line(text):
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def _tomato_count(text, is_markdown=True):
    """番茄口径：去空白总字符数减标题字符数；源稿先做轻量MD清洗。"""
    if text is None:
        return None
    cleaned = _strip_markdown_for_count(text) if is_markdown else text
    total = _compact_count(cleaned)
    title = _first_nonempty_line(cleaned)
    return max(0, total - _compact_count(title))


def _chapter_plan(chapter):
    source = _source_path(chapter)
    uploaded = _uploaded_path(chapter)
    source_text = _read_text_if_exists(source)
    uploaded_text = _read_text_if_exists(uploaded)
    source_count = _tomato_count(source_text, is_markdown=True)
    uploaded_count = _tomato_count(uploaded_text, is_markdown=False)
    # P0 three-color gate
    if source_count is not None:
        if source_count >= TOMATO_MIN_CHARS:
            gate_color = 'GREEN'
        elif source_count >= TOMATO_YELLOW_MIN:
            gate_color = 'YELLOW'
        else:
            gate_color = 'RED'
    else:
        gate_color = None
    return {
        "chapter": chapter,
        "source_md": source,
        "source_md_exists": source_text is not None,
        "source_tomato_chars": source_count,
        "source_word_count_ok": bool(source_count is not None and source_count >= TOMATO_MIN_CHARS),
        "gate_color": gate_color,
        "uploaded_txt": uploaded,
        "uploaded_txt_exists": uploaded_text is not None,
        "uploaded_tomato_chars": uploaded_count,
        "ready_for_gate": bool(source_text is not None and source_count is not None and source_count >= TOMATO_MIN_CHARS),
    }


def _safe_task_name(text):
    return re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "_", str(text)).strip("_") or "task"


def _decision_card_path(task_id, today=None):
    today = today or datetime.now().strftime("%Y%m%d")
    return os.path.join(DECISION_DIR, today, f"{_safe_task_name(task_id)}.md")


def _build_gate_card(chapter, plan):
    state = _load_state()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task_id = f"UPLOAD_CH{chapter}"
    status = "GATE_GREEN_PASS" if plan.get("ready_for_gate") else "GATE_RED_BLOCK"
    decision = "ALLOW_PRETEST_GATE_ONLY" if plan.get("ready_for_gate") else "BLOCK_SIXROLE_TEST"
    return f"""# 决策卡: {task_id}

- 日期: {now_str}
- task_id: {task_id}
- chapter: {chapter}
- status: {status}
- upload_cursor: {state.get('upload_cursor', 'N/A')}
- next_upload_chapters: {state.get('next_upload_chapters', [])}
- pipeline_stage: {state.get('pipeline_stage', 'N/A')}

## Gate Checks

- source_md_exists: {plan['source_md_exists']}
- source_md: {plan['source_md']}
- source_tomato_chars: {plan['source_tomato_chars']}
- source_word_count_ok: {plan['source_word_count_ok']}
- uploaded_txt_exists: {plan['uploaded_txt_exists']}
- uploaded_txt: {plan['uploaded_txt']}
- uploaded_tomato_chars: {plan['uploaded_tomato_chars']}
- ready_for_gate: {plan['ready_for_gate']}

## Decision

{decision}

## Boundary

只做上传前置闸门；未启动精修；未生成/修改已投稿TXT；未触发草稿箱上传。
"""

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(dry_run=False):
    """Scan uploaded chapters, set cursor and next chapters."""
    max_ch = _scan_uploaded()
    next_two = [max_ch + 1, max_ch + 2]
    now = datetime.now().isoformat()

    result = {
        "upload_cursor": max_ch,
        "next_upload_chapters": next_two,
        "scanned_at": now,
    }

    if dry_run:
        print("[DRY-RUN] Would write state:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    state = _load_state()
    state["upload_cursor"] = max_ch
    state["next_upload_chapters"] = next_two
    state["pipeline_stage"] = "ready"
    _save_state(state)

    _append_event("INIT", result)

    print("[INIT] State updated:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_status():
    """Print current state as JSON summary."""
    state = _load_state()
    max_ch = _scan_uploaded()
    state["scanned_max_uploaded"] = max_ch
    print(json.dumps(state, ensure_ascii=False, indent=2))


def cmd_emit(msg=None, event_type=None, task_id=None, chapter=None, detail=None):
    """Append a structured event to events.jsonl, backward compatible with --msg."""
    etype = event_type or "EMIT"
    payload = {}
    if msg is not None:
        payload["message"] = msg
    if task_id is not None:
        payload["task_id"] = task_id
    if chapter is not None:
        payload["chapter"] = chapter
    if detail is not None:
        try:
            payload["detail"] = json.loads(detail)
        except json.JSONDecodeError:
            payload["detail"] = detail
    if not payload:
        payload["message"] = ""
    _append_event(etype, payload)
    print(json.dumps({"event_type": etype, "payload": payload}, ensure_ascii=False, indent=2))


def cmd_decision_card(task):
    """Generate a generic decision card markdown file."""
    card_path = _decision_card_path(task)
    os.makedirs(os.path.dirname(card_path), exist_ok=True)

    state = _load_state()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    content = f"""# 决策卡: {task}

- **日期**: {now_str}
- **upload_cursor**: {state.get('upload_cursor', 'N/A')}
- **next_upload_chapters**: {state.get('next_upload_chapters', [])}
- **pipeline_stage**: {state.get('pipeline_stage', 'N/A')}

## 决策

> TODO: 填写决策内容

## 依据

> TODO: 填写决策依据

## 影响范围

> TODO: 填写影响范围
"""

    with open(card_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[DECISION-CARD] Written: {card_path}")


def cmd_plan_upload(dry_run=False):
    """Read state.next_upload_chapters and print upload preflight JSON. No writes."""
    state = _load_state()
    chapters = state.get("next_upload_chapters") or []
    result = {
        "dry_run": bool(dry_run),
        "upload_cursor": state.get("upload_cursor"),
        "next_upload_chapters": chapters,
        "chapters": [_chapter_plan(int(ch)) for ch in chapters],
        "writes": [],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_gate_upload(chapter, dry_run=False):
    """Create an upload gate decision card, or print path in dry-run mode."""
    plan = _chapter_plan(chapter)
    task_id = f"UPLOAD_CH{chapter}"
    card_path = _decision_card_path(task_id)

    if dry_run:
        print(json.dumps({"dry_run": True, "chapter": chapter, "decision_card": card_path, "writes": []}, ensure_ascii=False, indent=2))
        return

    os.makedirs(os.path.dirname(card_path), exist_ok=True)
    content = _build_gate_card(chapter, plan)
    with open(card_path, "w", encoding="utf-8") as f:
        f.write(content)
    event_type = "GATE_GREEN_PASS" if plan["ready_for_gate"] else "GATE_RED_BLOCK"
    _append_event(event_type, {
        "task_id": task_id,
        "chapter": chapter,
        "detail": {
            "decision_card": card_path,
            "ready_for_gate": plan["ready_for_gate"],
            "source_tomato_chars": plan["source_tomato_chars"],
            "source_md_exists": plan["source_md_exists"],
            "failed_check": None if plan["ready_for_gate"] else "source_tomato_chars>=3000",
        },
    })
    print(json.dumps({
        "status": event_type,
        "task_id": task_id,
        "chapter": chapter,
        "decision_card": card_path,
    }, ensure_ascii=False, indent=2))

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="科武纪元 日报状态工具 MVP")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Scan 已投稿 and init state")
    p_init.add_argument("--dry-run", action="store_true", help="Preview without writing")

    sub.add_parser("status", help="Print state summary")

    p_emit = sub.add_parser("emit", help="Append custom event")
    p_emit.add_argument("--msg", required=False, help="Event message")
    p_emit.add_argument("--event-type", required=False, help="Structured event type")
    p_emit.add_argument("--task-id", required=False, help="Task id")
    p_emit.add_argument("--chapter", type=int, required=False, help="Chapter number")
    p_emit.add_argument("--detail", required=False, help="Detail string or JSON object")

    p_dc = sub.add_parser("decision-card", help="Generate decision card")
    p_dc.add_argument("--task", required=True, help="Task name for card")

    p_plan = sub.add_parser("plan-upload", help="Preflight next upload chapters from state")
    p_plan.add_argument("--dry-run", action="store_true", help="Read-only JSON output")

    p_gate = sub.add_parser("gate-upload", help="Create upload gate decision card")
    p_gate.add_argument("--chapter", type=int, required=True, help="Chapter number")
    p_gate.add_argument("--dry-run", action="store_true", default=False, help="Preview without writing")
    p_gate.add_argument("--write", dest="dry_run", action="store_false", help="Write decision card and append event (compat; default)")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(dry_run=args.dry_run)
    elif args.command == "status":
        cmd_status()
    elif args.command == "emit":
        cmd_emit(
            msg=args.msg,
            event_type=args.event_type,
            task_id=args.task_id,
            chapter=args.chapter,
            detail=args.detail,
        )
    elif args.command == "decision-card":
        cmd_decision_card(args.task)
    elif args.command == "plan-upload":
        cmd_plan_upload(dry_run=args.dry_run)
    elif args.command == "gate-upload":
        cmd_gate_upload(chapter=args.chapter, dry_run=args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
