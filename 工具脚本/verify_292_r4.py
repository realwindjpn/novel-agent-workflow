#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第292章 R4 候选机器门禁验收（确定性，无 LLM 判断）。

验收项：
1. 首行 = 第292章 能源瓶颈
2. 末行 = （本章完）
3. 净 CJK >= 3200
4. 核心锚点保留：母线配额表／陈若水／L1 枢纽原位／总质量 16.9 吨
5. 12 处定点修复命中（新写法存在 + 旧写法归零）
6. 原 R3 canonical 未被改动（SHA 仍 9512bc...6586）
7. 剧情行数不低于 R3 的 84 行（允许 ±2 因删句合并）
8. 无 UI 残留（Thinking completed / 已经完成思考）
9. 无展示层前缀 ^\\d+\\|
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
from pathlib import Path

BASE = Path("/root/workspace/科武纪元/任务运行态/20260823_kewu_selfcycle_daily/output")
R3 = BASE / "candidate_292_r3.md"
R3_SHA = "9512bcfb9a6d7101ac05480b307096ba44e9c548475f01050ddf83f266866586"

# (编号, 旧写法 must be gone, 新写法 must exist or None for deletion)
FIXES = [
    (1, '"整流转换 74%。他拿 0.62 乘 0.74，链路总效率取整 46%。"',
     '"整流转换 74%。"他拿 0.62 乘 0.74'),
    (2, "每错一次损失 5 工时精磨工时", "每错一次损失 5 个精磨工时"),
    (3, "他拿 5.4 去除 0.3", "他拿 5.4 除以 0.3"),
    (4, "沃罗诺夫最后一个进气闸门", "沃罗诺夫最后一个进的气闸门"),
    (5, "每 687 天扫过 L1 一次", "每 24.6 小时扫过 L1 一次"),
    (5.1, "遮挡期最长 4.7 小时", "遮挡期最长 54 分钟"),
    (6, "配额只够第一班 4 件进炉。", "配额只够第一班 4 件里进 1 件炉"),
    (7, "第一班四件进炉 06:00", "第一班一件进炉 06:00"),
    (8, "14 个月，月产 30，总产出 351 件。", "前两个月爬产"),
    (9, "帕特尔把终端塞回包里。", "帕特尔把终端合上，压在基准表上面。"),
    (10, "帕特尔把终端合上。", "帕特尔把终端推到一边。"),
    (11, "他不想让任何人先看见这行字。", None),
    (12, None, "他看了一眼自己搁在桌上的笔，没拿。"),
]

ANCHORS = ["母线配额表", "陈若水", "L1 枢纽原位", "总质量 16.9 吨"]
KEEP_NUMBERS = ["180", "420", "913", "949", "5200", "16.9", "351", "274", "5326",
                "590", "31%", "62%", "74%", "46%"]
UI_RESIDUE = ["Thinking completed", "已经完成思考", "已深度思考"]


def cjk(t: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", t))


def main(path: str) -> int:
    p = Path(path)
    t = p.read_text(encoding="utf-8")
    lines = [l for l in t.splitlines() if l.strip()]
    r3 = R3.read_text(encoding="utf-8")
    r3_now = hashlib.sha256(r3.encode("utf-8")).hexdigest()

    res: dict = {"path": str(p)}
    res["sha256"] = hashlib.sha256(t.encode("utf-8")).hexdigest()
    res["chars"] = len(t)
    res["cjk"] = cjk(t)
    res["lines"] = len(lines)
    res["first_line"] = lines[0] if lines else ""
    res["last_line"] = lines[-1] if lines else ""

    checks = {}
    checks["first_line_ok"] = res["first_line"].lstrip("# ").strip() == "第292章 能源瓶颈"
    checks["last_line_ok"] = res["last_line"].strip() == "（本章完）"
    checks["cjk_ok"] = res["cjk"] >= 3200
    checks["lines_ok"] = res["lines"] >= 82
    checks["r3_untouched"] = (r3_now == R3_SHA)
    checks["sha_changed"] = (res["sha256"] != R3_SHA)
    checks["no_ui_residue"] = all(u not in t for u in UI_RESIDUE)
    checks["no_display_prefix"] = re.search(r"(?m)^\d+\|", t) is None

    anchors = {a: (a in t) for a in ANCHORS}
    checks["anchors_ok"] = all(anchors.values())
    res["anchors"] = anchors

    nums = {n: (n in t) for n in KEEP_NUMBERS}
    checks["numbers_ok"] = all(nums.values())
    res["numbers_kept"] = nums

    fixes = {}
    for num, old, new in FIXES:
        item = {}
        if old is not None:
            item["old_gone"] = (old not in t)
        if new is not None:
            item["new_present"] = (new in t)
        item["hit"] = all(item.values())
        fixes[str(num)] = item
    res["fixes"] = fixes
    checks["fixes_ok"] = all(v["hit"] for v in fixes.values())
    res["fixes_hit"] = sum(1 for v in fixes.values() if v["hit"])
    res["fixes_total"] = len(fixes)

    res["checks"] = checks
    res["verdict"] = "PASS" if all(checks.values()) else "FAIL"
    res["failed"] = [k for k, v in checks.items() if not v]

    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["verdict"] == "PASS" else 4


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
