#!/usr/bin/env python3
"""朱雀 AIGC 实测（腾讯 EdgeOne Makers API 直连）——科武通用探针。

用法：python3 zhuque_probe.py 文件.md [文件2.md ...] [--segs]

label 方向已标定（2026-09-23，热点项目 zhuque_calibration_corrected.json）：
  0 = 人工特征 / 1 = AI特征 / 2 = 疑似AI
锚点：朱自清散文 1266 字 → label 0 100%；AI 腔公文 → label 1 100%。

注意：
- 整篇送测（is_merge=True），不拆段；短文本(<600字)会塌成单一 label，读数不可用。
- 目标线：人工占比 >= 40%。
- 改字级(<3% CJK)不重测，沿用上版读数；整篇重写/句式改动必须重测。
"""
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ENV_CANDIDATES = [
    Path("/root/workspace/热点文章/20260922_游戏中的中国味/.env"),
    Path("/root/.hermes/.env"),
]
URL = "https://ai-gateway.edgeone.link/v1/providers/zhuque-text/classify"
CJK = re.compile(r"[\u4e00-\u9fff]")
LABELS = {"0": "人工特征", "1": "AI特征", "2": "疑似AI"}


def get_key():
    for p in ENV_CANDIDATES:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("EDGEONE_ZHUQUE_API_KEY="):
                return line.split("=", 1)[1].strip()
    for k in ("EDGEONE_ZHUQUE_API_KEY",):
        if os.environ.get(k):
            return os.environ[k]
    raise SystemExit("找不到 EDGEONE_ZHUQUE_API_KEY")


def detect(text, key, timeout=200):
    body = json.dumps({"text": text, "is_merge": True}).encode("utf-8")
    req = urllib.request.Request(
        URL, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def clean(path):
    raw = Path(path).read_text(encoding="utf-8")
    out = []
    for line in raw.split("\n"):
        s = re.sub(r"^#+\s*", "", line).strip()
        if s:
            out.append(s)
    return "\n".join(out)


def run(path, key, show_segs=False):
    text = clean(path)
    cjk = len(CJK.findall(text))
    if cjk < 800:
        print(f"[SKIP] {path}: CJK={cjk} <800，短文本读数不可用")
        return None
    res = detect(text, key)
    lr = res.get("labels_ratio") or {}
    segs = res.get("segment_labels") or []
    rec = {
        "file": path.rsplit("/", 1)[-1],
        "cjk": cjk,
        "human": round(float(lr.get("0", 0)) * 100, 1),
        "ai": round(float(lr.get("1", 0)) * 100, 1),
        "suspect": round(float(lr.get("2", 0)) * 100, 1),
        "n_segs": len(segs),
    }
    print(f"--- {rec['file']}  CJK={cjk} ---")
    print(f"  人工 {rec['human']}%  AI特征 {rec['ai']}%  疑似AI {rec['suspect']}%")
    print(f"  段数 {len(segs)} 分布 {dict(sorted(Counter(s.get('label') for s in segs).items()))}")
    if show_segs:
        for i, s in enumerate(segs, 1):
            print(f"    seg{i} label={LABELS.get(str(s.get('label')), s.get('label'))} "
                  f"conf={s.get('confidence')} chars={s.get('length') or s.get('char_count')}")
    print(f"  判定：{'PASS' if rec['human'] >= 40 else 'FAIL'}（目标 人工>=40%）")
    rec["verdict"] = "PASS" if rec["human"] >= 40 else "FAIL"
    return rec


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    show_segs = "--segs" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(2)
    key = get_key()
    out = [r for r in (run(p, key, show_segs) for p in args) if r]
    if len(out) == 1:
        Path("/root/workspace/科武纪元/审核记录/zhuque_latest.json").write_text(
            json.dumps(out[0], ensure_ascii=False, indent=1), encoding="utf-8")
        print("\n已写 审核记录/zhuque_latest.json")
