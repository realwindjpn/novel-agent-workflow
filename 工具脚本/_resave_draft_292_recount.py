#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""就地重存 292 草稿（不改正文、不新建），令平台重算字数，再回读列表。"""
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
URL = ("https://fanqienovel.com/main/writer/7628216044850531352/publish/"
       "7677509566518526488/?enter_from=modifydraft")
LIST = ("https://fanqienovel.com/main/writer/chapter-manage/7628216044850531352"
        "&%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99?type=2")

out = {}
fq.ab(SESSION, f"open {shlex.quote(URL)}", timeout=60, state_path=STATE)
time.sleep(5)

# 读保存前的字数标签与正文长度
pre = fq.js_eval(SESSION, (
    "(() => {"
    " const eds=Array.from(document.querySelectorAll('.ProseMirror'));"
    " let best=null,bl=-1; for(const e of eds){const t=e.textContent||''; if(t.length>bl){bl=t.length;best=e;}}"
    " const b=document.body.innerText||'';"
    " const m=b.match(/\\u6b63\\u6587\\u5b57\\u6570\\s*\\n?\\s*([0-9]+)/);"
    " return {bodyLen:(best.textContent||'').length, wordLabel:m?m[1]:null,"
    "   btns:Array.from(document.querySelectorAll('button,div,span')).map(n=>(n.innerText||'').trim())"
    "     .filter(t=>t==='\\u5b58\\u8349\\u7a3f'||t==='\\u5df2\\u4fdd\\u5b58'||t==='\\u4fdd\\u5b58\\u8349\\u7a3f').slice(0,6)};"
    "})()"), timeout=90, state_path=STATE)
out["pre"] = pre

# 触发一次 input 事件让编辑器 dirty（不改内容），再点存草稿
click = fq.js_eval(SESSION, (
    "(() => {"
    " const eds=Array.from(document.querySelectorAll('.ProseMirror'));"
    " let best=null,bl=-1; for(const e of eds){const t=e.textContent||''; if(t.length>bl){bl=t.length;best=e;}}"
    " best.dispatchEvent(new Event('input',{bubbles:true}));"
    " const nodes=Array.from(document.querySelectorAll('button,div,span'));"
    " const t=nodes.find(n=>(n.innerText||'').trim()==='\\u5b58\\u8349\\u7a3f');"
    " if(!t) return {clicked:false};"
    " t.click(); return {clicked:true};"
    "})()"), timeout=90, state_path=STATE)
out["click"] = click
time.sleep(8)

post = fq.js_eval(SESSION, (
    "(() => {"
    " const b=document.body.innerText||'';"
    " const m=b.match(/\\u6b63\\u6587\\u5b57\\u6570\\s*\\n?\\s*([0-9]+)/);"
    " return {wordLabel:m?m[1]:null, saved:b.includes('\\u5df2\\u4fdd\\u5b58'), head:b.slice(0,220)};"
    "})()"), timeout=90, state_path=STATE)
out["post"] = post

fq.ab(SESSION, f"open {shlex.quote(LIST)}", timeout=60, state_path=STATE)
time.sleep(6)
lst = fq.js_eval(SESSION, (
    "(() => {"
    " const t=document.body.innerText||'';"
    " const rows=t.split('\\n').map(s=>s.trim()).filter(Boolean);"
    " const i=rows.findIndex(r=>r.indexOf('\\u7b2c292\\u7ae0')===0);"
    " return {row:i>=0?rows.slice(i,i+3):null, count:(t.match(/\\u7b2c292\\u7ae0/g)||[]).length};"
    "})()"), timeout=90, state_path=STATE)
out["listing_after"] = lst

print(json.dumps(out, ensure_ascii=False, indent=2))
Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/"
     "output/takeover_292/draft_resave_recount_292.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
