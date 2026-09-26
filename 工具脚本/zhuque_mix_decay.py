#!/usr/bin/env python3
"""决定性对照：会议体裁本身能不能过朱雀 40% 线？

已证事实：
  移植实验（把 354 文本换进 356）：0%→11.3%，20%→18.7%，100%→66.0%
  本轮 r1（按 354 寄存器改写 356）：指标全面向 354 靠，朱雀 11.3%→9.1%
  r1 画像：unit/句 0.346→0.618（354=0.744）、num/句 0.44→0.78（354=0.97）、
           hedge/千字 5.0→2.5（354=1.2）——写法确实改了，读数却降了

矛盾点：指标全面改善但读数下降。合理解释是「混合寄存器有毒」——
朱雀判的是整篇单一寄存器，一半 354 一半会议观察，比纯会议更糟。

本轮做反向衰减曲线：往 354（纯寄存器，66%）里掺入会议体裁文本，
测掺多少会把读数打到 40% 以下。
  E1 354 原样（0% 会议体）              已知 66.0%
  E2 354 + 10% r1 会议体
  E3 354 + 25% r1 会议体
  E4 354 + 40% r1 会议体
若衰减陡峭 → 会议章在结构上无法过线，属体裁限制，须用户裁决而非继续返修。

只做诊断，不产出正文，不写回 新版/。
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zhuque_probe import CJK, detect, get_key  # noqa: E402

CH354 = Path("/root/workspace/科武纪元/新版/第354章.md")
R1 = Path("/root/workspace/科武纪元/任务运行态/20260925_kewu_selfcycle_daily/output/ch356_zhuque_rewrite_r1.md")
OUT = Path("/root/workspace/科武纪元/审核记录/ch354_mix_decay_20260926.json")


def paras(p):
    lines = [l for l in p.read_text(encoding="utf-8").split("\n") if l.strip()]
    return lines[0], lines[1:]


def clip(body, limit):
    out, n = [], 0
    for x in body:
        c = len(CJK.findall(x))
        if n + c > limit and out:
            break
        out.append(x)
        n += c
    return out


def measure(tag, text, key):
    res = detect(text, key)
    lr = res.get("labels_ratio") or {}
    cjk = len(CJK.findall(text))
    rec = {"tag": tag, "cjk": cjk,
           "human": round(float(lr.get("0", 0)) * 100, 1),
           "ai": round(float(lr.get("1", 0)) * 100, 1),
           "suspect": round(float(lr.get("2", 0)) * 100, 1)}
    print(f"  {tag:26s} CJK={cjk:5d}  人工 {rec['human']:5.1f}%  "
          f"AI {rec['ai']:5.1f}%  疑似 {rec['suspect']:5.1f}%")
    return rec


if __name__ == "__main__":
    key = get_key()
    t354, b354 = paras(CH354)
    t1, b1 = paras(R1)
    # r1 去掉首行标题后即为会议体文本
    mix_src = b1
    n354 = len(b354)
    print("会议体掺入 354 的衰减曲线（354 原样 66.0% 为基线）")
    recs = []
    for pct in (0, 10, 25, 40):
        k = int(n354 * pct / 100)
        if k == 0:
            text = t354 + "\n" + "\n".join(b354)
        else:
            inject = mix_src[:k]
            # 插在中段，避免只影响尾部
            mid = n354 // 2
            merged = b354[:mid] + inject + b354[mid:]
            text = t354 + "\n" + "\n".join(merged)
        recs.append(measure(f"E 掺{pct}%", text, key))
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已写 {OUT}")
