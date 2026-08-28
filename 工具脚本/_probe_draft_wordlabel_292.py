#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓 292 草稿编辑页平台自身字数计数器 + 列表行字数，定位口径差异。"""
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
URL = "https://fanqienovel.com/main/writer/7628216044850531352/publish/7677509566518526488/?enter_from=modifydraft"

fq.ab(SESSION, f"open {shlex.quote(URL)}", timeout=60, state_path=STATE)
time.sleep(5)

js = (
    "(() => {"
    " const body=document.body.innerText||'';"
    " const hits=[];"
    " const re1=/([0-9]{2,6})\\s*\\u5b57/g; let m;"
    " while((m=re1.exec(body))!==null){ hits.push({num:m[1], ctx:body.slice(Math.max(0,m.index-40), m.index+12)}); }"
    " const re2=/\\u5b57\\u6570[^0-9]{0,6}([0-9]{2,6})/g;"
    " const hits2=[]; while((m=re2.exec(body))!==null){ hits2.push({num:m[1], ctx:body.slice(Math.max(0,m.index-30), m.index+20)}); }"
    " return {headText:body.slice(0,900), wordHits:hits.slice(0,20), wordHits2:hits2.slice(0,20)};"
    "})()"
)
res = fq.js_eval(SESSION, js, timeout=120, state_path=STATE)
print("=== EDIT PAGE ===")
print(json.dumps(res, ensure_ascii=False, indent=2)[:6000])

LIST = ("https://fanqienovel.com/main/writer/chapter-manage/7628216044850531352"
        "&%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99?type=2")
fq.ab(SESSION, f"open {shlex.quote(LIST)}", timeout=60, state_path=STATE)
time.sleep(5)
js2 = (
    "(() => {"
    " const t=document.body.innerText||'';"
    " const rows=t.split('\\n').map(s=>s.trim()).filter(Boolean);"
    " return {rows:rows.slice(-40)};"
    "})()"
)
res2 = fq.js_eval(SESSION, js2, timeout=120, state_path=STATE)
print("=== LIST PAGE ===")
print(json.dumps(res2, ensure_ascii=False, indent=2)[:4000])

Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/output/takeover_292/draft_wordlabel_probe_292.json").write_text(
    json.dumps({"edit": res, "list": res2}, ensure_ascii=False, indent=2), encoding="utf-8")
