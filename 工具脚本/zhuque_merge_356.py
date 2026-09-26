#!/usr/bin/env python3
"""356 碎句体合句实验（补做，此前所有句法实验都做在 354 上）。

实测两章均句长差一倍：354=21.3 CJK/句，356=10.0 CJK/句；356 段数句数反而更多
（97段299句 vs 89段272句），对白段 18 vs 7 —— 谈判章对白把节奏打碎。
本脚本对 356 做多档合句（相邻短句并进前句，直到该句达到 cut 字），逐档送朱雀直连。

端点/鉴权/读数口径一律复用 zhuque_probe，不另造（上一版自造 URL 导致 DNS 解析失败）。

用法：python3 zhuque_merge_356.py
"""
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zhuque_probe as ZQ  # noqa: E402

SRC = Path("/root/workspace/科武纪元/新版/第356章.md")
CACHE = Path("/root/workspace/科武纪元/任务运行态/20260925_kewu_selfcycle_daily/output/ch356_sentence_merge.json")
CJK = re.compile(r"[\u4e00-\u9fff]")
SPLIT = re.compile(r"(?<=[。！？…])")


def merge(text: str, cut: float) -> str:
    out = []
    for para in text.split("\n"):
        s = para.strip()
        if not s or s.startswith("#") or s.startswith("（本章完"):
            out.append(para)
            continue
        sents = [x for x in SPLIT.split(s) if x.strip()]
        merged, buf = [], ""
        for x in sents:
            buf += x
            if len(CJK.findall(buf)) >= cut:
                merged.append(buf)
                buf = ""
        if buf:
            merged[-1] += buf if merged else buf
        out.append("".join(merged))
    return "\n".join(out)


def measure(text: str, key: str, label: str, tries: int = 5) -> dict | None:
    cjk = len(CJK.findall(text))
    sents = [s for s in SPLIT.split(text) if s.strip()]
    sl = [len(CJK.findall(s)) for s in sents]
    avg = round(sum(sl) / len(sl), 1) if sl else 0
    for i in range(tries):
        try:
            res = ZQ.detect(text, key)
            lr = res.get("labels_ratio") or {}
            segs = res.get("segment_labels") or []
            return {
                "label": label, "cjk": cjk, "avg_sent": avg, "n_sents": len(sents),
                "human": round(float(lr.get("0", 0)) * 100, 1),
                "ai": round(float(lr.get("1", 0)) * 100, 1),
                "suspect": round(float(lr.get("2", 0)) * 100, 1),
                "seg_dist": dict(sorted(Counter(s.get("label") for s in segs).items())),
            }
        except Exception as e:
            if i == tries - 1:
                print(f"    {label} 探测失败：{type(e).__name__} {e}", flush=True)
                return None
            wait = min(128, 21 * (2 ** i))
            print(f"    {label} 限流/异常，退避 {wait}s（第{i+1}次）", flush=True)
            time.sleep(wait)
    return None


def main() -> None:
    key = ZQ.get_key()
    src = SRC.read_text(encoding="utf-8")
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    results = {"baseline": cache.get("baseline")}
    base = measure(src, key, "baseline")
    if base:
        results["baseline"] = base
        print(f"  baseline      CJK={base['cjk']} 均句长={base['avg_sent']:5.1f} 人工={base['human']}%", flush=True)
    else:
        print("  baseline 探测失败，跳过（朱雀限流）", flush=True)
    CACHE.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    for cut in (12.0, 18.0, 25.0):
        name = f"merge_{cut}"
        if name in results and results[name]:
            continue
        r = measure(merge(src, cut), key, name)
        if r:
            results[name] = r
            print(f"  {name:12s} CJK={r['cjk']} 均句长={r['avg_sent']:5.1f} 人工={r['human']}%", flush=True)
        CACHE.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n" + "=" * 70)
    for k, v in results.items():
        if v:
            print(f"{k:12s} CJK={v['cjk']:5d} 均句长={v['avg_sent']:5.1f} 人工={v['human']:5.1f}%  段分布={v['seg_dist']}")
    print("=" * 70)
    print(f"（结果已落 {CACHE}）")


if __name__ == "__main__":
    main()
