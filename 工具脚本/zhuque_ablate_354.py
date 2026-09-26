#!/usr/bin/env python3
"""朱雀归因消融：354（唯一 PASS 样本，77.3% 人工）到底赢在哪一轴？

354 与 356 同时在三条轴上不同，本脚本逐轴拆开：
  A1 原样 5802 字              → 已知 77.3%
  A2 截到 3009 字（对齐 356 字数）→ 分离「字数」轴
  A3 截到 3009 字 + 打散短句（短句并入相邻长句）→ 再分离「句法」轴

只做诊断，不产出正文，不写回 新版/。
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zhuque_probe import CJK, detect, get_key  # noqa: E402

SRC = Path("/root/workspace/科武纪元/新版/第354章.md")
OUT = Path("/root/workspace/科武纪元/审核记录/ch354_ablation_20260926.json")
TARGET_CJK = 3009


def clip_cjk(text, limit):
    """按 CJK 计数截断，保留段落结构。"""
    out, n = [], 0
    for para in text.split("\n"):
        c = len(CJK.findall(para))
        if n + c > limit:
            out.append(para)
            break
        out.append(para)
        n += c
    return "\n".join(out)


def merge_short(text):
    """把 <=8 字的独立短句并入后一句，用逗号连接。不改字，只改断句。"""
    lines = []
    for para in text.split("\n"):
        s = para.strip()
        if not s:
            continue
        # 只处理纯叙述短句（无引号、无对话冒号）
        if len(CJK.findall(s)) <= 8 and '「' not in s and '：' not in s and '：' not in s:
            lines.append(("SHORT", s))
        else:
            lines.append(("NORM", s))
    out, buf = [], None
    for kind, s in lines:
        if kind == "SHORT":
            buf = s if buf is None else buf + s
        else:
            if buf is not None:
                out.append(buf)
                buf = None
            out.append(s)
    if buf is not None:
        out.append(buf)
    return "\n".join(out)


def measure(tag, text, key):
    res = detect(text, key)
    lr = res.get("labels_ratio") or {}
    cjk = len(CJK.findall(text))
    rec = {
        "tag": tag, "cjk": cjk,
        "human": round(float(lr.get("0", 0)) * 100, 1),
        "ai": round(float(lr.get("1", 0)) * 100, 1),
        "suspect": round(float(lr.get("2", 0)) * 100, 1),
        "n_segs": len(res.get("segment_labels") or []),
    }
    print(f"  {tag:34s} CJK={cjk:5d}  人工 {rec['human']:5.1f}%  "
          f"AI {rec['ai']:5.1f}%  疑似 {rec['suspect']:5.1f}%")
    return rec


if __name__ == "__main__":
    key = get_key()
    raw = SRC.read_text(encoding="utf-8")
    print("354 归因消融（对照：356 原样 3009 字 = 人工 11.3%）")
    a2 = clip_cjk(raw, TARGET_CJK)
    a3 = merge_short(a2)
    recs = [
        measure("A1 原样5802字(已测=77.3，仅复核)", raw, key),
        measure("A2 截到3009字", a2, key),
        measure("A3 截3009字+短句并入", a3, key),
    ]
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已写 {OUT}")
