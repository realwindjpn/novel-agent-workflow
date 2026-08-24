#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第292章 R8 定点返修回收验收（确定性）。

验收链：
1. 首尾锚点 / 行数 / 净 CJK / SHA 变化
2. 三处修复命中：旧写法归零 + 新写法各 1 次
3. 保留锚点：351 / 274 / 5326 / 5600 全在
4. diff 越界核查：unified_diff 改动行位必须只落在 L36 / L40 / L70
"""
from __future__ import annotations
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

BASE = Path("/root/workspace/科武纪元/任务运行态/20260823_kewu_selfcycle_daily/output")
SRC = BASE / "candidate_292_r7.md"
RAW = BASE / "candidate_292_r8_raw.md"
CLEAN = BASE / "candidate_292_r8.md"
REPORT = BASE / "verify_292_r8_report.json"

SRC_SHA = "72d1dd28e290da75edd2d796105eb191b618be69099bcb230e2bd4d1f90f5eed"

OLD_TOKENS = [
    "频段选 5.8 吉赫兹",
    "每平方厘米 0.4 毫瓦",
    "第 3 至 13 月稳态月产 30 件，总产出 351 件。",
]
NEW_TOKENS = [
    "频段选 2.45 吉赫兹",
    "每平方厘米 0.004 毫瓦",
    "第 3 至 13 月稳态月产 30 件，第 14 月停线切并网，总产出 351 件。",
]
KEEP_TOKENS = ["351", "274", "5326", "5600"]
EXPECT_LINES = {36, 40, 70}


def cjk(t: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", t))


def sanitize(t: str) -> str:
    lines = t.splitlines()
    # 剥 Thinking completed / 已经完成思考 类 UI 残留首行
    while lines and re.match(r"^\s*(Thinking completed|已经完成思考|思考完成)\s*$", lines[0]):
        lines.pop(0)
    # 剥首行前置的 markdown 标题符号，与源稿格式对齐（源稿首行为裸标题）
    if lines and re.match(r"^#+\s*第292章", lines[0]):
        lines[0] = re.sub(r"^#+\s*", "", lines[0])
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines) + "\n"


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    assert hashlib.sha256(src.encode()).hexdigest() == SRC_SHA, "SRC_SHA_MISMATCH"
    raw = RAW.read_text(encoding="utf-8")
    clean = sanitize(raw)
    CLEAN.write_text(clean, encoding="utf-8")
    back = CLEAN.read_text(encoding="utf-8")

    src_lines = src.splitlines()
    body_lines = back.splitlines()
    new_sha = hashlib.sha256(back.encode()).hexdigest()

    # diff 越界核查（以源稿行号为基准，1-indexed）
    changed = []
    sm = difflib.SequenceMatcher(None, src_lines, body_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        for i in range(i1, i2):
            changed.append(i + 1)
        if tag == "insert":
            changed.append(i1 + 1)
    changed_set = sorted(set(changed))

    r = {
        "src_sha256": SRC_SHA,
        "src_net_cjk": cjk(src),
        "src_lines": len(src_lines),
        "raw_path": str(RAW),
        "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "clean_path": str(CLEAN),
        "clean_sha256": new_sha,
        "clean_net_cjk": cjk(back),
        "clean_lines": len(body_lines),
        "first_line": body_lines[0] if body_lines else "",
        "last_line": body_lines[-1] if body_lines else "",
        "first_line_ok": bool(body_lines) and body_lines[0].strip() == "第292章 能源瓶颈",
        "last_line_ok": bool(body_lines) and body_lines[-1].strip() == "（本章完）",
        "cjk_hard_min_3200": cjk(back) >= 3200,
        "cjk_safety_max_10000": cjk(back) <= 10000,
        "sha_changed": new_sha != SRC_SHA,
        "line_count_equal": len(body_lines) == len(src_lines),
        "old_token_counts": {t: back.count(t) for t in OLD_TOKENS},
        "new_token_counts": {t: back.count(t) for t in NEW_TOKENS},
        "keep_token_counts": {t: back.count(t) for t in KEEP_TOKENS},
        "changed_src_lines": changed_set,
        "changed_within_expected": set(changed_set) == EXPECT_LINES,
        "no_display_prefix": re.search(r"(?m)^\d+\|", back) is None,
        "no_markdown_heading": re.search(r"(?m)^#", back) is None,
    }

    fails = []
    if not r["first_line_ok"]:
        fails.append("FIRST_LINE")
    if not r["last_line_ok"]:
        fails.append("LAST_LINE")
    if not r["cjk_hard_min_3200"]:
        fails.append("CJK_BELOW_3200")
    if not r["cjk_safety_max_10000"]:
        fails.append("CJK_ABOVE_10000")
    if not r["sha_changed"]:
        fails.append("SHA_UNCHANGED")
    if not r["line_count_equal"]:
        fails.append("LINE_COUNT_DRIFT")
    for t, c in r["old_token_counts"].items():
        if c != 0:
            fails.append(f"OLD_TOKEN_REMAINS:{t[:20]}={c}")
    for t, c in r["new_token_counts"].items():
        if c != 1:
            fails.append(f"NEW_TOKEN_COUNT:{t[:24]}={c}")
    for t, c in r["keep_token_counts"].items():
        if c < 1:
            fails.append(f"KEEP_TOKEN_LOST:{t}")
    if not r["changed_within_expected"]:
        fails.append(f"DIFF_OUT_OF_SCOPE:{changed_set}")
    if not r["no_display_prefix"]:
        fails.append("DISPLAY_PREFIX")
    if not r["no_markdown_heading"]:
        fails.append("MARKDOWN_HEADING")

    r["fails"] = fails
    r["verdict"] = "R8_VERIFY_PASS" if not fails else "R8_VERIFY_FAIL"
    REPORT.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if not fails else 5


if __name__ == "__main__":
    sys.exit(main())
