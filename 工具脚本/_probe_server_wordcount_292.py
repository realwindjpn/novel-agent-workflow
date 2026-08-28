#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取服务端 edit_article 接口的权威字数字段（292 与 291 对照）。"""
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
BOOK = "7628216044850531352"
ITEMS = {"292": "7677509566518526488", "291": "7677244660154122776"}

# 打开 292 编辑页，取到带签名的 edit_article URL 模板
fq.ab(SESSION, f"open https://fanqienovel.com/main/writer/{BOOK}/publish/{ITEMS['292']}/?enter_from=modifydraft",
      timeout=60, state_path=STATE)
time.sleep(7)

tmpl = fq.js_eval(SESSION, (
    "(() => {const e=performance.getEntriesByType('resource')"
    " .map(x=>x.name).filter(n=>n.includes('edit_article')); return e.slice(-1)[0]||null;})()"
), timeout=90, state_path=STATE)
print("tmpl:", (re.sub(r"(msToken|a_bogus)=[^&]+", r"\1=***", tmpl) if isinstance(tmpl, str) else tmpl))

out = {"template_found": bool(tmpl)}
if isinstance(tmpl, str):
    for ch, item in ITEMS.items():
        url = re.sub(r"item_id=\d+", f"item_id={item}", tmpl)
        js = (
            "(async () => { try {"
            f" const r=await fetch({json.dumps(url)},{{credentials:'include'}});"
            " const t=await r.text(); let j=null; try{j=JSON.parse(t);}catch(e){}"
            " const flat={}; (function walk(o,p){ if(o&&typeof o==='object'){ for(const k in o){"
            "   const v=o[k]; const np=p?p+'.'+k:k;"
            "   if(v&&typeof v==='object'){ walk(v,np); }"
            "   else if(/word|count|len/i.test(k)){ flat[np]=v; } } } })(j,'');"
            " return {status:r.status, wordFields:flat, keysTop:j?Object.keys(j):null, raw:t.slice(0,600)};"
            "} catch(e){ return {error:String(e)}; } })()"
        )
        r = fq.js_eval(SESSION, js, timeout=120, state_path=STATE)
        out[ch] = r
        print(f"=== {ch} ===")
        print(json.dumps(r, ensure_ascii=False, indent=2)[:2500])

Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/"
     "output/takeover_292/server_wordcount_probe.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
