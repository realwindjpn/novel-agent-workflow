#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列表页 XHR 枚举 + 重放，读服务端草稿列表 word_number（先 hook 再原地取数据，不 reload）。"""
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
LIST = ("https://fanqienovel.com/main/writer/chapter-manage/7628216044850531352"
        "&%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99?type=2")

fq.ab(SESSION, f"open {shlex.quote(LIST)}", timeout=60, state_path=STATE)
time.sleep(8)

urls = fq.js_eval(SESSION, (
    "(() => performance.getEntriesByType('resource').map(e=>e.name)"
    " .filter(n=>n.includes('fanqienovel.com/api')||n.includes('fanqienovel.com/app')))()"
), timeout=90, state_path=STATE)
urls = [u for u in (urls or []) if isinstance(u, str)]
print("api urls:", len(urls))
for u in urls:
    print(" ", re.sub(r"(msToken|a_bogus)=[^&]+", r"\1=***", u)[:150])

out = {"api_urls": [re.sub(r"(msToken|a_bogus)=[^&]+", r"\1=***", u) for u in urls], "replays": []}
for u in urls:
    js = ("(async () => { try { const r=await fetch(%s,{credentials:'include'});"
          " const t=await r.text();"
          " return {status:r.status, len:t.length, hit:/6434|4885|4887|4161/.test(t),"
          "  head:t.slice(0,300), matchCtx:(()=>{const m=t.match(/.{0,120}(6434|4885|4887|4161).{0,120}/);return m?m[0]:null;})()};"
          "} catch(e){return {error:String(e)};} })()" % json.dumps(u))
    r = fq.js_eval(SESSION, js, timeout=120, state_path=STATE)
    if isinstance(r, dict) and r.get("hit"):
        su = re.sub(r"(msToken|a_bogus)=[^&]+", r"\1=***", u)
        print("=== HIT", su[:150])
        print("   ctx:", str(r.get("matchCtx"))[:400])
        out["replays"].append({"url": su, "resp": r})

Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/"
     "output/takeover_292/draft_list_api_fields2_292.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("hits:", len(out["replays"]))
