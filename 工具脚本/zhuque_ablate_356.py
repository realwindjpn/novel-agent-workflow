#!/usr/bin/env python3
"""356 病灶消融：找出本章自身被判疑似AI 的具体机制。

354 已证：字数轴、句法轴都不是原因（截断/合句零影响）。
本轮只测 356 自身的三个候选病灶，每个只动一处，不改语义：
  B1 原样                       → 噪声基线
  B2 删末段整章复述（L96）        → 测「AI 式总结段」
  B3 纯动作短句并入邻句（「…了。」类）→ 测「无信息量碎句」
  B4 删 L96 + 合句              → 组合

只做诊断，不产出正文，不写回 新版/。
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zhuque_probe import CJK, detect, get_key  # noqa: E402

SRC = Path("/root/workspace/科武纪元/新版/第356章.md")
OUT = Path("/root/workspace/科武纪元/审核记录/ch356_ablation_20260926.json")

# 纯动作短句：去掉人名后主体为单动作，句长<=12，无引号无数字
ACTION_ONLY = re.compile(r"^[^「」]{1,14}$")


def is_lowinfo(line):
    s = line.strip()
    if not s or '「' in s or '（' in s:
        return False
    c = len(CJK.findall(s))
    if c > 12 or c == 0:
        return False
    # 含对话/心理/判断词的保留
    if any(k in s for k in ('说', '问', '看', '想', '算', '认得', '知道', '听', '记', '不是', '意味着')):
        return False
    return True


def merge_action_short(text):
    out, buf = [], None
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        if is_lowinfo(s):
            buf = s if buf is None else buf + s
        else:
            if buf is not None:
                out.append(buf)
                buf = None
            out.append(s)
    if buf is not None:
        out.append(buf)
    return "\n".join(out)


def drop_last_para(text):
    lines = text.rstrip().split("\n")
    # 末段「（本章完）」前那一段
    idx = max(i for i, l in enumerate(lines) if l.strip() == "（本章完）")
    return "\n".join(lines[: idx - 1] + lines[idx:])


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
    print(f"  {tag:30s} CJK={cjk:5d}  人工 {rec['human']:5.1f}%  "
          f"AI {rec['ai']:5.1f}%  疑似 {rec['suspect']:5.1f}%")
    return rec


if __name__ == "__main__":
    key = get_key()
    raw = SRC.read_text(encoding="utf-8")
    b2 = drop_last_para(raw)
    b3 = merge_action_short(raw)
    b4 = merge_action_short(b2)
    print("356 病灶消融（对照：354 截3009字 = 人工 83.8%）")
    recs = [
        measure("B1 原样", raw, key),
        measure("B2 删末段复述", b2, key),
        measure("B3 合动作短句", b3, key),
        measure("B4 删复述+合句", b4, key),
    ]
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已写 {OUT}")
