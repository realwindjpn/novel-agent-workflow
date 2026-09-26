#!/usr/bin/env python3
"""对照实验 v2：带退避与断点续存的来源轴对照。

首轮结果（第84章，早期章）= 人工 0.0%，已推翻「早期章普遍高分」的来源轴假设。
429 限流后改为：每条结果即时落盘，429 指数退避，重跑自动跳过已测样本。

只读诊断，不改正文。
"""
import json
import random
import re
import sys
import time
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zhuque_probe import CJK, clean, detect, get_key  # noqa: E402

OUT = Path("/root/workspace/科武纪元/审核记录/zhuque_source_axis_20260926.json")
EARLY = [6, 59, 68, 84, 86, 92, 96, 100, 111, 124, 132, 142]
LATE = [330, 335, 345, 350, 352, 353, 354, 355, 356]


def pick(n, root):
    for d in (root / "已投稿" / f"第{n}章.txt", root / "新版" / f"第{n}章.md"):
        if d.exists() and len(CJK.findall(d.read_text(encoding="utf-8"))) > 800:
            return d
    return None


def run(tag, path, key, recs, done):
    keyname = str(path)
    if keyname in done:
        return done[keyname]
    delay = 20
    for attempt in range(5):
        try:
            text = clean(path)
            res = detect(text, key, timeout=200)
            lr = res.get("labels_ratio") or {}
            rec = {"tag": tag, "ch": path.stem, "path": keyname,
                   "cjk": len(CJK.findall(text)),
                   "human": round(float(lr.get("0", 0)) * 100, 1),
                   "suspect": round(float(lr.get("2", 0)) * 100, 1)}
            print(f"  {tag} {path.stem:12s} CJK={rec['cjk']:5d}  "
                  f"人工 {rec['human']:5.1f}%  疑似 {rec['suspect']:5.1f}%", flush=True)
            done[keyname] = rec
            recs.append(rec)
            OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")
            time.sleep(8)
            return rec
        except urllib.error.HTTPError as e:
            if e.code == 429:
                w = delay + random.randint(0, 8)
                print(f"    429 限流，退避 {w}s（第{attempt+1}次）", flush=True)
                time.sleep(w)
                delay = min(delay * 2, 120)
                continue
            print(f"    HTTP {e.code} 跳过 {path.stem}", flush=True)
            return None
        except Exception as e:  # noqa: BLE001
            print(f"    ERR {type(e).__name__} 跳过 {path.stem}", flush=True)
            return None
    return None


def main():
    key = get_key()
    root = Path("/root/workspace/科武纪元")
    recs = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    done = {r["path"]: r for r in recs}

    for tag, chapters in (("早期", EARLY), ("近期", LATE)):
        print(f"{tag}章：", flush=True)
        for n in chapters:
            p = pick(n, root)
            if p:
                run(tag, p, key, recs, done)

    def stat(rs):
        v = sorted(r["human"] for r in rs)
        return {"n": len(v), "median": v[len(v) // 2] if v else None,
                "min": v[0] if v else None, "max": v[-1] if v else None,
                "pass40": sum(1 for x in v if x >= 40)}

    early = stat([r for r in recs if r["tag"] == "早期"])
    late = stat([r for r in recs if r["tag"] == "近期"])
    print("\n汇总（人工占比）")
    for nm, s in (("早期", early), ("近期", late)):
        if s["n"]:
            print(f"  {nm} n={s['n']} 中位 {s['median']}%  范围 {s['min']}~{s['max']}%  "
                  f"过40线 {s['pass40']}/{s['n']}")
    OUT.write_text(json.dumps({"summary": {"early": early, "late": late},
                               "records": recs}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"\n已写 {OUT}")


if __name__ == "__main__":
    main()
