#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""292 草稿页字数审计：全量 dump 所有 ProseMirror + 平台字数标签 + 重复段检测。"""
import importlib.util
import json
import re
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

URL = "https://fanqienovel.com/main/writer/7628216044850531352/publish/7677509566518526488/?enter_from=modifydraft"
SESSION = fq.DEFAULT_SESSION
STATE = fq.DEFAULT_STATE

fq.ab(SESSION, f"open {shlex.quote(URL)}", timeout=60, state_path=STATE)
time.sleep(5)

js = (
    "(() => {"
    " const eds=Array.from(document.querySelectorAll('.ProseMirror'));"
    " const all=eds.map((e,i)=>({idx:i, cls:String(e.className).slice(0,80),"
    "   len:(e.innerText||'').length, text:(e.innerText||'')}));"
    " const body=document.body.innerText||'';"
    " const labels=Array.from(document.querySelectorAll('*')).map(n=>n.childElementCount===0?(n.innerText||'').trim():'')"
    "   .filter(t=>t && t.length<40 && /\\u5b57\\u6570|\\u5b57$/.test(t)).slice(0,40);"
    " const inputs=Array.from(document.querySelectorAll('input,textarea')).map(n=>({t:n.type||n.tagName, v:(n.value||'').slice(0,120)}));"
    " return {editors:all, labels:labels, inputs:inputs, bodyTextTail:body.slice(-1200)};"
    "})()"
)
res = fq.js_eval(SESSION, js, timeout=120, state_path=STATE)
if not isinstance(res, dict):
    print("RAW:", str(res)[:3000])
    sys.exit("READ_FAIL")

TXT = Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u5df2\u6295\u7a3f/\u7b2c292\u7ae0.txt")
local = TXT.read_text(encoding="utf-8")
local_body_full = local.split("\u4f5c\u8005\u6709\u8bdd\u8bf4\uff1a")[0]
lines = [l for l in local_body_full.split("\n") if l.strip()]
local_body_no_title = "\n".join(lines[1:])
local_note = local.split("\u4f5c\u8005\u6709\u8bdd\u8bf4\uff1a")[1] if "\u4f5c\u8005\u6709\u8bdd\u8bf4\uff1a" in local else ""

norm = lambda s: re.sub(r"\s", "", s)
FIRST = "\u4f1a\u8bae\u5ba4\u7684\u6295\u5f71\u5c4f\u6302\u5728\u5317\u5899"
END = "\uff08\u672c\u7ae0\u5b8c\uff09"

out = {"editors": [], "labels": res.get("labels"), "inputs": res.get("inputs"),
       "bodyTextTail": res.get("bodyTextTail")}
total_norm = 0
for e in res["editors"]:
    t = e.get("text", "")
    total_norm += len(norm(t))
    out["editors"].append({
        "idx": e["idx"], "cls": e["cls"], "innerLen": e["len"],
        "norm_len": len(norm(t)), "cjk": len(re.findall(r"[\u4e00-\u9fff]", t)),
        "first_sentence_hits": len(re.findall(re.escape(FIRST), t)),
        "end_marker_hits": len(re.findall(re.escape(END), t)),
        "head": t[:100], "tail": t[-100:],
    })
out["all_editors_norm_total"] = total_norm
out["local"] = {
    "body_no_title_norm": len(norm(local_body_no_title)),
    "body_with_title_norm": len(norm(local_body_full)),
    "note_norm": len(norm(local_note)),
    "body_raw_len": len(local_body_full),
    "body_no_title_raw_len": len(local_body_no_title),
}
main = max((e.get("text", "") for e in res["editors"]), key=len, default="")
out["match"] = {
    "remote_main_norm": len(norm(main)),
    "exact_vs_local_no_title": norm(main) == norm(local_body_no_title),
    "listing_reported": 6434,
}
print(json.dumps(out, ensure_ascii=False, indent=2)[:12000])
Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/output/takeover_292/draft_wordcount_audit_292.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
