#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""292 草稿正文结构硬核验：ProseMirror doc textContent + 段落节点数 + 重复段检测。"""
import importlib.util
import json
import re
import shlex
import sys
import time
from collections import Counter
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "fq", "/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u5de5\u5177\u811a\u672c/fanqie_draft_upload_chapter.py"
)
fq = importlib.util.module_from_spec(SPEC)
sys.modules["fq"] = fq
SPEC.loader.exec_module(fq)

SESSION = fq.DEFAULT_SESSION
STATE = fq.DEFAULT_STATE
URL = ("https://fanqienovel.com/main/writer/7628216044850531352/publish/"
       "7677509566518526488/?enter_from=modifydraft")

fq.ab(SESSION, f"open {shlex.quote(URL)}", timeout=60, state_path=STATE)
time.sleep(5)

js = (
    "(() => {"
    " const eds=Array.from(document.querySelectorAll('.ProseMirror'));"
    " let best=null, bestLen=-1;"
    " for(const e of eds){ const tc=e.textContent||''; if(tc.length>bestLen){bestLen=tc.length;best=e;} }"
    " const ps=Array.from(best.querySelectorAll('p')).map(p=>(p.textContent||''));"
    " return {textContent:best.textContent||'', innerText:best.innerText||'',"
    "   pCount:ps.length, pTexts:ps, childCount:best.children.length,"
    "   tagCounts:(()=>{const c={};for(const n of best.querySelectorAll('*')){c[n.tagName]=(c[n.tagName]||0)+1;}return c;})()};"
    "})()"
)
res = fq.js_eval(SESSION, js, timeout=120, state_path=STATE)
if not isinstance(res, dict):
    print("RAW:", str(res)[:2000]); sys.exit("READ_FAIL")

tc = res.pop("textContent", "")
it = res.pop("innerText", "")
ps = res.pop("pTexts", [])

TXT = Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u5df2\u6295\u7a3f/\u7b2c292\u7ae0.txt")
local = TXT.read_text(encoding="utf-8")
lb = local.split("\u4f5c\u8005\u6709\u8bdd\u8bf4\uff1a")[0]
llines = [l.strip() for l in lb.split("\n") if l.strip()]
local_paras = llines[1:]  # 去标题行

norm = lambda s: re.sub(r"\s", "", s)
rps = [p.strip() for p in ps if p.strip()]
dup = [t for t, c in Counter(rps).items() if c > 1]

out = {
    "remote_pCount_all": res["pCount"],
    "remote_pCount_nonempty": len(rps),
    "remote_childCount": res["childCount"],
    "remote_tagCounts": res["tagCounts"],
    "remote_textContent_len": len(tc),
    "remote_textContent_norm": len(norm(tc)),
    "remote_innerText_len": len(it),
    "remote_innerText_norm": len(norm(it)),
    "local_para_count": len(local_paras),
    "local_body_norm": len(norm("\n".join(local_paras))),
    "paras_equal_sequence": rps == local_paras,
    "duplicate_paragraphs": dup[:10],
    "duplicate_count": len(dup),
    "first_para_occurrences": rps.count(local_paras[0]) if local_paras else None,
    "end_marker_occurrences": sum(1 for p in rps if p == "\uff08\u672c\u7ae0\u5b8c\uff09"),
    "listing_reported_wordcount": 6434,
    "local_fanqie_body_norm": len(norm("\n".join(local_paras))),
}
if rps != local_paras:
    out["first_mismatch"] = next(
        ({"idx": i, "remote": a[:160], "local": b[:160]}
         for i, (a, b) in enumerate(zip(rps, local_paras)) if a != b), None)
print(json.dumps(out, ensure_ascii=False, indent=2))
Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/"
     "output/takeover_292/draft_structure_verify_292.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
