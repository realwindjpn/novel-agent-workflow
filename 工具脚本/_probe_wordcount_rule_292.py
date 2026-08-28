#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定位番茄 listing 字数口径：取 292/291 草稿页 innerHTML/textContent 多口径，对比 listing 值。"""
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

SESSION = fq.DEFAULT_SESSION
STATE = fq.DEFAULT_STATE
PAGES = {
    "292": "https://fanqienovel.com/main/writer/7628216044850531352/publish/7677509566518526488/?enter_from=modifydraft",
    "291": "https://fanqienovel.com/main/writer/7628216044850531352/publish/7677244660154122776/?enter_from=modifydraft",
}
LISTING = {"292": 6434, "291": 4161}

JS = (
    "(() => {"
    " const eds=Array.from(document.querySelectorAll('.ProseMirror'));"
    " let best=null,bl=-1; for(const e of eds){const t=e.textContent||''; if(t.length>bl){bl=t.length;best=e;}}"
    " const b=document.body.innerText||'';"
    " const mw=b.match(/\\u6b63\\u6587\\u5b57\\u6570\\s*\\n?\\s*([0-9]+)/);"
    " const html=best.innerHTML||'';"
    " const tc=best.textContent||'';"
    " const ps=Array.from(best.querySelectorAll('p'));"
    " return {pageWordLabel:mw?mw[1]:null, htmlLen:html.length, tcLen:tc.length,"
    "   pCount:ps.length, htmlSample:html.slice(0,600),"
    "   tagCounts:(()=>{const c={};for(const n of best.querySelectorAll('*')){c[n.tagName]=(c[n.tagName]||0)+1;}return c;})(),"
    "   tc:tc};"
    "})()"
)

out = {}
for ch, url in PAGES.items():
    fq.ab(SESSION, f"open {shlex.quote(url)}", timeout=60, state_path=STATE)
    time.sleep(6)
    r = fq.js_eval(SESSION, JS, timeout=120, state_path=STATE)
    if not isinstance(r, dict):
        out[ch] = {"error": str(r)[:400]}
        continue
    tc = r.pop("tc", "")
    norm = re.sub(r"\s", "", tc)
    cjk = len(re.findall(r"[\u4e00-\u9fff]", tc))
    halfwidth = len(re.findall(r"[\x21-\x7e]", tc))
    spaces = tc.count(" ")
    r.update({
        "tc_norm": len(norm), "tc_cjk": cjk, "tc_halfwidth": halfwidth, "tc_spaces": spaces,
        "listing": LISTING[ch],
        "listing_minus_norm": LISTING[ch] - len(norm),
        "halfwidth_plus_spaces": halfwidth + spaces,
        "html_len_vs_listing": r["htmlLen"] - LISTING[ch],
    })
    out[ch] = r
    print(ch, json.dumps({k: v for k, v in r.items() if k not in ("htmlSample",)}, ensure_ascii=False))

print("\n=== htmlSample 292 ===")
print((out.get("292") or {}).get("htmlSample", "")[:600])
Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/"
     "output/takeover_292/wordcount_rule_probe.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
