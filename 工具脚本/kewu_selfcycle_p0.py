#!/usr/bin/env python3
"""
科武纪元 自循环 P0 确定性状态脚本
──────────────────────────────────
功能：
  1. 扫描 已投稿/第*.txt → 最大章号 N → 输出 N+1, N+2 为上传队列
  2. 创建 locks/ raw/ reports/ 目录
  3. 写 state.json / queue.json / events.jsonl 到审核记录/自循环体系会议_YYYYMMDD/
  4. 检查 新版/ git diff → 0点前只报告不改
  5. 生成 reports/p0_state_report.md
约束：幂等；不改正文；不上传；中文路径兼容。
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

TODAY = datetime.now()
DATE_TAG = TODAY.strftime("%Y%m%d")
MEETING_DIR = REVIEW_BASE / f"自循环体系会议_{DATE_TAG}"

CHAPTER_RE = re.compile(r"第(\d+)章")


# ── 工具函数 ───────────────────────────────────
def log(msg: str):
    ts = TODAY.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def safe_json_write(path: Path, data: dict | list):
    """原子写 JSON，先写 .tmp 再 rename"""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.rename(path)


def append_event(events_path: Path, event: dict):
    """追加一行 JSON 到 events.jsonl"""
    line = json.dumps(event, ensure_ascii=False)
    with open(events_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── 1. 扫描已投稿最大章号 ─────────────────────
def scan_published_max() -> int:
    """返回已投稿目录中最大章号"""
    max_ch = 0
    if not PUBLISHED.exists():
        log(f"WARN: {PUBLISHED} 不存在")
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
    """检查 新版/ 目录 git diff，返回变更摘要"""
    result = {"has_diff": False, "files": [], "summary": ""}
    try:
        # staged + unstaged
        r = subprocess.run(
            ["git", "diff", "--stat", "--", "新版/"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=15
        )
        out = r.stdout.strip()
        if out:
            result["has_diff"] = True
            # 提取文件名
            for line in out.splitlines():
                if "章" in line:
                    # 提取中文文件名
                    parts = line.split("|")
                    if parts:
                        fname = parts[0].strip()
                        result["files"].append(fname)
            result["summary"] = out.splitlines()[-1] if out else ""
    except Exception as e:
        result["summary"] = f"git diff error: {e}"
    return result


# ── 3. 检查新版有哪些章节 ─────────────────────
def scan_new_edition_chapters() -> list[int]:
    """扫描 新版/ 目录所有章号"""
    chapters = set()
    if not NEW_EDITION.exists():
        return []
    for f in NEW_EDITION.iterdir():
        m = CHAPTER_RE.search(f.name)
        if m and f.suffix == ".md":
            ch = int(m.group(1))
            chapters.add(ch)
    return sorted(chapters)


# ── 主流程 ─────────────────────────────────────
def main():
    log("═══ 科武自循环 P0 启动 ═══")

    # ── 确保目录存在 ──
    for d in [LOCKS, RAW, REPORTS, MEETING_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        log(f"DIR OK: {d.relative_to(ROOT)}")

    # ── 1. 扫描已投稿 ──
    max_published = scan_published_max()
    next_1 = max_published + 1
    next_2 = max_published + 2
    log(f"已投稿最高: 第{max_published}章 → 上传队列: 第{next_1}章, 第{next_2}章")

    # ── 2. 新版章节扫描 ──
    new_ed_chapters = scan_new_edition_chapters()
    log(f"新版/ 章节数: {len(new_ed_chapters)}, 范围: {new_ed_chapters[0] if new_ed_chapters else '?'}~{new_ed_chapters[-1] if new_ed_chapters else '?'}")

    # ── 3. 检查新版 git diff ──
    diff_info = check_new_edition_diff()
    now_hour = datetime.now().hour
    before_midnight = now_hour < 0 or True  # 0点 = hour==0；脚本随时可跑，标记当前时间
    is_after_midnight = now_hour >= 0  # 始终 true，实际逻辑：0-24均算"可报告"
    # 真正的0点后判断：当前时间在 00:00-06:00 为凌晨窗口
    is_night_window = 0 <= now_hour < 6
    log(f"当前时间 {TODAY.strftime('%H:%M')} | 凌晨窗口(0-6时): {'是' if is_night_window else '否'}")

    if diff_info["has_diff"]:
        log(f"新版/ 有未提交 diff: {len(diff_info['files'])} 文件")
        for f in diff_info["files"]:
            log(f"  - {f}")
        if not is_night_window:
            log("→ 非凌晨窗口，仅报告，不改正文")
    else:
        log("新版/ 无未提交 diff")

    # ── 4. 判断队列章节在新版是否存在 ──
    new_ed_set = set(new_ed_chapters)
    q1_exists = next_1 in new_ed_set
    q2_exists = next_2 in new_ed_set
    log(f"第{next_1}章 新版存在: {'是' if q1_exists else '否'}")
    log(f"第{next_2}章 新版存在: {'是' if q2_exists else '否'}")

    # ── 5. 写 state.json ──
    state = {
        "schema": "kewu-selfcycle-p0-v1",
        "timestamp": TODAY.isoformat(),
        "published_max": max_published,
        "upload_queue": [next_1, next_2],
        "new_edition_range": [new_ed_chapters[0], new_ed_chapters[-1]] if new_ed_chapters else [],
        "new_edition_count": len(new_ed_chapters),
        "queue_source_exists": {"next_1": q1_exists, "next_2": q2_exists},
        "new_edition_diff": diff_info,
        "night_window": is_night_window,
        "blocks": []
    }

    # 阻塞检测
    if not q1_exists:
        state["blocks"].append(f"第{next_1}章 新版/ 无源稿，无法精修")
    if not q2_exists:
        state["blocks"].append(f"第{next_2}章 新版/ 无源稿，无法精修")

    state_path = MEETING_DIR / "state.json"
    safe_json_write(state_path, state)
    log(f"WRITE: {state_path.relative_to(ROOT)}")

    # ── 6. 写 queue.json ──
    queue = {
        "generated_at": TODAY.isoformat(),
        "items": []
    }
    for ch in [next_1, next_2]:
        exists = ch in new_ed_set
        queue["items"].append({
            "chapter": ch,
            "status": "ready" if exists else "blocked_no_source",
            "source": f"新版/第{ch}章.md" if exists else None,
            "target": f"已投稿/第{ch}章.txt",
            "review_passed": False,
            "uploaded": False
        })

    queue_path = MEETING_DIR / "queue.json"
    safe_json_write(queue_path, queue)
    log(f"WRITE: {queue_path.relative_to(ROOT)}")

    # ── 7. 追加 events.jsonl ──
    events_path = MEETING_DIR / "events.jsonl"
    event = {
        "ts": TODAY.isoformat(),
        "type": "p0_scan",
        "published_max": max_published,
        "queue": [next_1, next_2],
        "blocks": state["blocks"],
        "night_window": is_night_window
    }
    append_event(events_path, event)
    log(f"APPEND: {events_path.relative_to(ROOT)}")

    # ── 8. 生成报告 ──
    report_lines = [
        f"# 科武自循环 P0 状态报告",
        f"",
        f"- 生成时间: {TODAY.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 已投稿最高: 第{max_published}章",
        f"- 上传队列: 第{next_1}章, 第{next_2}章",
        f"- 新版章节数: {len(new_ed_chapters)}",
        f"- 凌晨窗口: {'是' if is_night_window else '否'}",
        f"",
        f"## 队列详情",
        f"",
    ]
    for item in queue["items"]:
        ch = item["chapter"]
        st = item["status"]
        src = item["source"] or "无"
        report_lines.append(f"- 第{ch}章: `{st}` | 源: {src}")

    if diff_info["has_diff"]:
        report_lines.append(f"")
        report_lines.append(f"## 新版/ 未提交变更")
        report_lines.append(f"")
        for f in diff_info["files"]:
            report_lines.append(f"- {f}")
        if not is_night_window:
            report_lines.append(f"")
            report_lines.append(f"> ⚠ 非凌晨窗口，仅报告，不改正文")

    if state["blocks"]:
        report_lines.append(f"")
        report_lines.append(f"## 阻塞项")
        report_lines.append(f"")
        for b in state["blocks"]:
            report_lines.append(f"- ❌ {b}")

    report_lines.append(f"")
    report_lines.append(f"## 目录状态")
    report_lines.append(f"")
    for d in [LOCKS, RAW, REPORTS, MEETING_DIR]:
        report_lines.append(f"- `{d.relative_to(ROOT)}/`: ✅ 已就绪")

    report_path = REPORTS / "p0_state_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    log(f"WRITE: {report_path.relative_to(ROOT)}")

    # ── 汇总 ──
    log("═══ P0 完成 ═══")
    log(f"上传队列: 第{next_1}章({'有源稿' if q1_exists else '❌缺源稿'}) / 第{next_2}章({'有源稿' if q2_exists else '❌缺源稿'})")
    if state["blocks"]:
        log(f"阻塞: {len(state['blocks'])} 项")
    else:
        log("无阻塞，队列就绪")


if __name__ == "__main__":
    main()
