#!/usr/bin/env python3
"""寄存器移植实验：356 的失败是否来自「文体寄存器」而非结构/字数/句法？

已排除：
  字数轴  354 截到 3020 字仍 83.8%（对照 356 原样 3009 字 = 11.3%）
  句法轴  354 短句并入 / 356 短句并入，均零影响
  结构轴  356 删末段复述段，零影响

本轮直接把 354 的正文块换进 356，测读数是否随寄存器比例线性移动。
  C1 356 原样                          （11.3% 基线）
  C2 356 前 6 段替换为 354 前 6 段        （约 1/3 篇幅换寄存器）
  C3 356 前 12 段替换为 354 前 12 段      （约 1/2 篇幅换寄存器）
  C4 354 截 1500 字单独送测              （纯 354 寄存器，独立确认）

只做诊断，不产出正文，不写回 新版/。
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zhuque_probe import CJK, detect, get_key  # noqa: E402

CH354 = Path("/root/workspace/科武纪元/新版/第354章.md")
CH356 = Path("/root/workspace/科武纪元/新版/第356章.md")
OUT = Path("/root/workspace/科武纪元/审核记录/ch356_register_transplant_20260926.json")


def paras(path):
    raw = path.read_text(encoding="utf-8")
    lines = raw.split("\n")
    title = lines[0]
    body = [l for l in lines[1:] if l.strip()]
    return title, body


def clip_cjk(body, limit):
    out, n = [], 0
    for p in body:
        c = len(CJK.findall(p))
        if n + c > limit and out:
            break
        out.append(p)
        n += c
    return out


def splice(title, donor_head, body_356):
    head = "".join(donor_head[:1])
    return head + "\n" + "\n".join(donor_head[1:] + body_356)


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
    t354, b354 = paras(CH354)
    t356, b356 = paras(CH356)
    print("寄存器移植（356 基线 11.3%；354 寄存器独立值见 C4）")

    c2 = splice(t356, b354[:6], b356[6:])
    c3 = splice(t356, b354[:12], b356[12:])
    c4 = t354 + "\n" + "\n".join(clip_cjk(b354, 1500))

    recs = [
        measure("C1 356 原样", t356 + "\n" + "\n".join(b356), key),
        measure("C2 356 换入354前6段", c2, key),
        measure("C3 356 换入354前12段", c3, key),
        measure("C4 354 前1500字单独", c4, key),
    ]
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已写 {OUT}")
