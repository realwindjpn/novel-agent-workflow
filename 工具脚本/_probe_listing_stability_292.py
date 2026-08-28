#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列表字数稳定性探针：多次硬刷新读 292/291 行，判断 6434 是否服务端持久值或缓存残值。"""
import importlib.util
import json
import shlex
import sys
import time
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "fq", "/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u5de5\u5177\u811a\u672c/fanqie_draft_upload_chapter.py"
)
fq = importlib.util.module_from_spec(SPEC)
sys.modules["fq"] = fq
SPEC.loader.exec_module(fq)

SESSION = fq.DEFAULT_SESSION
STATE = fq.DEFAULT_STATE
LIST = ("https://fanqienovel.com/main/writer/chapter-manage/7628216044850531352"
        "&%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99?type=2")

JS = (
    "(() => {"
    " const t=document.body.innerText||'';"
    " const rows=t.split('\\n').map(s=>s.trim()).filter(Boolean);"
    " const pick=(k)=>{const i=rows.findIndex(r=>r.indexOf(k)===0); return i>=0?rows.slice(i,i+3):null;};"
    " return {c292:pick('\\u7b2c292\\u7ae0'), c291:pick('\\u7b2c291\\u7ae0')};"
    "})()"
)

reads = []
for i in range(4):
    fq.ab(SESSION, f"open {shlex.quote(LIST)}", timeout=60, state_path=STATE)
    time.sleep(6)
    r = fq.js_eval(SESSION, JS, timeout=90, state_path=STATE)
    reads.append({"attempt": i + 1, "result": r})
    print(json.dumps(reads[-1], ensure_ascii=False))
    time.sleep(4)

vals292 = [(r["result"] or {}).get("c292") for r in reads]
vals291 = [(r["result"] or {}).get("c291") for r in reads]
out = {
    "reads": reads,
    "distinct_292_words": sorted({v[1] for v in vals292 if v and len(v) > 1}),
    "distinct_291_words": sorted({v[1] for v in vals291 if v and len(v) > 1}),
}
print(json.dumps({k: out[k] for k in ("distinct_292_words", "distinct_291_words")}, ensure_ascii=False))
Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/"
     "output/takeover_292/listing_stability_probe_292.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
