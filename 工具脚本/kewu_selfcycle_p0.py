#!/usr/bin/env python3
"""
科武纪元 自循环 P0 确定性状态脚本（单链隔离改造 2026-08-13）
──────────────────────────────────
功能：
  1. 任务状态机（单一真源）：只读 任务运行态/<task_id>/state.json 的
     `upload_queue` 推导活跃上传队列。不再以 `已投稿/` 扫描推队列。
  2. 创建 locks/ raw/ reports/ 目录
  3. 写 state.json / queue.json / events.jsonl 到 审核记录/自循环体系会议_YYYYMMDD/
  4. 检查 新版/ git diff → 仅报告不改
  5. 生成 reports/p0_state_report.md

约束：幂等；不改正文；不上传；中文路径兼容。

用法：
  python3 kewu_selfcycle_p0.py --state 任务运行态/<task_id>/state.json
  python3 kewu_selfcycle_p0.py --task 任务运行态/<task_id>
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── 常量 ──────────────────────────────────────
ROOT = Path("/root/workspace/科武纪元")
PUBLISHED = ROOT / "已投稿"
NEW_EDITION = ROOT / "新版"
REVIEW_BASE = ROOT / "审核记录"
LOCKS = ROOT / "locks"
RAW = ROOT / "raw"
REPORTS = ROOT / "reports"
TASK_RUNTIME = Path("/root/workspace/任务运行态")

TODAY = datetime.now()
DATE_TAG = TODAY.strftime("%Y%m%d")
MEETING_DIR = REVIEW_BASE / f"自循环体系会议_{DATE_TAG}"

CHAPTER_RE = re.compile(r"第(\d+)章")


# ── 工具函数 ───────────────────────────────────
def log(msg: str):
    ts = TODAY.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def safe_json_write(path: Path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.rename(path)


def append_event(events_path: Path, event: dict):
    line = json.dumps(event, ensure_ascii=False)
    with open(events_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── 参数解析 ───────────────────────────────────
def parse_args() -> dict:
    args = {"state": None, "task": None}
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--state" and i + 1 < len(argv):
            args["state"] = argv[i + 1]
            i += 2
        elif argv[i] == "--task" and i + 1 < len(argv):
            args["task"] = argv[i + 1]
            i += 2
        else:
            i += 1
    return args


# ── 任务状态机（单一真源）──────────────────────
def resolve_state_path(args: dict) -> Path | None:
    if args.get("state"):
        return Path(args["state"])
    if args.get("task"):
        return Path(args["task"]) / "state.json"
    return None


def read_task_state(state_path: Path | None) -> dict | None:
    if state_path is None or not state_path.exists():
        return None
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception as e:
        log(f"WARN: 读 state 失败: {e}")
        return None


def derive_queue_from_state(state: dict | None) -> list[int]:
    """只从任务 state.json 推导活跃上传队列；绝不扫描已投稿推队列。"""
    if not state:
        return []
    raw = state.get("upload_queue") or state.get("active_queue") or []
    out: list[int] = []
    for x in raw:
        try:
            out.append(int(x))
        except (TypeError, ValueError):
            pass
    return out


# ── 1. 扫描已投稿最大章号（仅信息参考）─────────
def scan_published_max() -> int:
    """返回已投稿目录中最大章号（仅信息，不用于推导活跃队列）。"""
    max_ch = 0
    if not PUBLISHED.exists():
        return 0
    for f in PUBLISHED.iterdir():
        m = CHAPTER_RE.search(f.name)
        if m and f.suffix == ".txt":
            ch = int(m.group(1))
            if ch > max_ch:
                max_ch = ch
    return max_ch


# ── 2. 检查新版 git diff ──────────────────────
def check_new_edition_diff() -> dict:
    result = {"has_diff": False, "files": [], "summary": ""}
    try:
        r = subprocess.run(
            ["git", "diff", "--stat", "--", "新版/"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=15
        )
        out = r.stdout.strip()
        if out:
            result["has_diff"] = True
            for line in out.splitlines():
                if "章" in line:
                    parts = line.split("|")
                    if parts:
                        result["files"].append(parts[0].strip())
            result["summary"] = out.splitlines()[-1] if out else ""
    except Exception as e:
        result["summary"] = f"git diff error: {e}"
    return result


# ── 3. 检查新版有哪些章节 ─────────────────────
def scan_new_edition_chapters() -> list[int]:
    chapters = set()
    if not NEW_EDITION.exists():
        return []
    for f in NEW_EDITION.iterdir():
        m = CHAPTER_RE.search(f.name)
        if m and f.suffix == ".md":
            chapters.add(int(m.group(1)))
    return sorted(chapters)


# ── 主流程 ─────────────────────────────────────
def main():
    log("═══ 科武自循环 P0 启动（状态机版） ═══")

    for d in [LOCKS, RAW, REPORTS, MEETING_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        log(f"DIR OK: {d.relative_to(ROOT)}")

    # ── 1. 已投稿扫描（仅信息，不推导活跃队列）──
    max_published = scan_published_max()
    log(f"已投稿最高: 第{max_published}章（仅信息，不用于推导队列）")

    # ── 2. 任务状态机：活跃队列只读 state.json ──
    args = parse_args()
    state_path = resolve_state_path(args)
    task_state = read_task_state(state_path)
    queue = derive_queue_from_state(task_state)
    if state_path is not None and task_state is None:
        log(f"WARN: state 缺失或不可读: {state_path}")
    log(f"活跃上传队列(来自 state.json): {queue if queue else '∅'}")

    # ── 3. 新版章节扫描 ──
    new_ed_chapters = scan_new_edition_chapters()
    log(f"新版/ 章节数: {len(new_ed_chapters)}")

    # ── 4. 检查新版 git diff ──
    diff_info = check_new_edition_diff()
    now_hour = datetime.now().hour
    is_night_window = 0 <= now_hour < 6
    if diff_info["has_diff"]:
        log(f"新版/ 有未提交 diff: {len(diff_info['files'])} 文件")
        if not is_night_window:
            log("→ 非凌晨窗口，仅报告，不改正文")
    else:
        log("新版/ 无未提交 diff")

    new_ed_set = set(new_ed_chapters)

    # ── 5. 阻塞检测 ──
    blocks: list[str] = []
    if not queue:
        blocks.append(
            "STATE_MISSING_ACTIVE_QUEUE: 未提供任务 state.json 的 upload_queue，"
            "且不以已投稿/推队列"
        )
    for ch in queue:
        if ch not in new_ed_set:
            blocks.append(f"第{ch}章 新版/ 无源稿，无法精修")

    # ── 6. 写 state.json ──
    state = {
        "schema": "kewu-selfcycle-p0-v2",
        "timestamp": TODAY.isoformat(),
        "published_max": max_published,       # 信息参考
        "upload_queue": queue,                # 来自任务 state.json
        "queue_source": "task_state_json",
        "new_edition_range": [new_ed_chapters[0], new_ed_chapters[-1]] if new_ed_chapters else [],
        "new_edition_count": len(new_ed_chapters),
        "new_edition_diff": diff_info,
        "night_window": is_night_window,
        "blocks": blocks,
    }
    safe_json_write(MEETING_DIR / "state.json", state)
    log(f"WRITE: {(MEETING_DIR / 'state.json').relative_to(ROOT)}")

    # ── 7. 写 queue.json ──
    qitems = []
    for ch in queue:
        exists = ch in new_ed_set
        qitems.append({
            "chapter": ch,
            "status": "ready" if exists else "blocked_no_source",
            "source": f"新版/第{ch}章.md" if exists else None,
            "target": f"已投稿/第{ch}章.txt",
            "review_passed": False,
            "uploaded": False,
        })
    queue_obj = {"generated_at": TODAY.isoformat(), "items": qitems}
    safe_json_write(MEETING_DIR / "queue.json", queue_obj)
    log(f"WRITE: {(MEETING_DIR / 'queue.json').relative_to(ROOT)}")

    # ── 8. events.jsonl ──
    append_event(MEETING_DIR / "events.jsonl", {
        "ts": TODAY.isoformat(),
        "type": "p0_scan",
        "published_max": max_published,
        "queue": queue,
        "queue_source": "task_state_json",
        "blocks": blocks,
        "night_window": is_night_window,
    })
    log(f"APPEND: {(MEETING_DIR / 'events.jsonl').relative_to(ROOT)}")

    # ── 9. 报告 ──
    report_lines = [
        "# 科武自循环 P0 状态报告（状态机版）",
        "",
        f"- 生成时间: {TODAY.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 已投稿最高(信息): 第{max_published}章",
        f"- 活跃上传队列(任务 state.json): {queue if queue else '∅'}",
        f"- 新版章节数: {len(new_ed_chapters)}",
        f"- 凌晨窗口: {'是' if is_night_window else '否'}",
        "",
        "## 队列详情",
        "",
    ]
    for item in qitems:
        report_lines.append(f"- 第{item['chapter']}章: `{item['status']}` | 源: {item['source'] or '无'}")
    if diff_info["has_diff"]:
        report_lines += ["", "## 新版/ 未提交变更", ""]
        for f in diff_info["files"]:
            report_lines.append(f"- {f}")
        if not is_night_window:
            report_lines += ["", "> ⚠ 非凌晨窗口，仅报告，不改正文"]
    if blocks:
        report_lines += ["", "## 阻塞项", ""]
        for b in blocks:
            report_lines.append(f"- ❌ {b}")
    report_lines += ["", "## 目录状态", ""]
    for d in [LOCKS, RAW, REPORTS, MEETING_DIR]:
        report_lines.append(f"- `{d.relative_to(ROOT)}/`: ✅ 已就绪")
    (REPORTS / "p0_state_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    log(f"WRITE: {(REPORTS / 'p0_state_report.md').relative_to(ROOT)}")

    log("═══ P0 完成 ═══")
    log(f"活跃队列: {queue if queue else '∅（无 state.json upload_queue）'}")
    if blocks:
        log(f"阻塞: {len(blocks)} 项")


if __name__ == "__main__":
    main()
