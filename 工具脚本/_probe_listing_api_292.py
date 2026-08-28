#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓草稿箱列表接口原始 JSON，取平台权威字数字段（不猜口径）。"""
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

fq.ab(SESSION, f"open {shlex.quote(LIST)}", timeout=60, state_path=STATE)
time.sleep(7)

# 1) 列出本页所有 XHR/fetch 资源 URL
urls = fq.js_eval(SESSION, (
    "(() => performance.getEntriesByType('resource')"
    " .filter(e=>e.initiatorType==='xmlhttprequest'||e.initiatorType==='fetch')"
    " .map(e=>e.name).slice(0,80))()"
), timeout=90, state_path=STATE)
print("=== XHR URLS ===")
print(json.dumps(urls, ensure_ascii=False, indent=2)[:4000])

out = {"xhr_urls": urls}

# 2) 对疑似草稿/章节列表接口重放 fetch，取原始 JSON
cands = [u for u in (urls or []) if isinstance(u, str) and
         any(k in u for k in ("draft", "chapter", "book", "item_list", "list"))]
out["candidates"] = cands
replays = []
for u in cands[:12]:
    js = (
        "(async () => { try {"
        f" const r = await fetch({json.dumps(u)}, {{credentials:'include'}});"
        " const t = await r.text();"
        " return {status:r.status, len:t.length, body:t.slice(0,4000)};"
        "} catch(e) {return {error:String(e)};} })()"
    )
    r = fq.js_eval(SESSION, js, timeout=120, state_path=STATE)
    hit = False
    if isinstance(r, dict) and isinstance(r.get("body"), str):
        hit = ("6434" in r["body"]) or ("4885" in r["body"]) or ("4887" in r["body"]) or ("4161" in r["body"])
    replays.append({"url": u, "hit_wordcount_tokens": hit, "resp": r})
    print(f"--- {u[:120]} hit={hit}")
out["replays"] = replays

Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/"
     "output/takeover_292/listing_api_probe_292.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("SAVED")
