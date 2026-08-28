#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓草稿箱列表接口（type=2）原始 JSON，读 292/291 的服务端 word_number 字段。"""
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

# hook fetch/XHR 以捕获草稿列表响应
fq.ab(SESSION, "open about:blank", timeout=60, state_path=STATE)
time.sleep(1)
fq.ab(SESSION, f"open {shlex.quote(LIST)}", timeout=60, state_path=STATE)
time.sleep=getattr(time,'sleep')
time.sleep(4)

hook = fq.js_eval(SESSION, (
    "(() => { if(window.__cap) return 'already';"
    " window.__cap=[];"
    " const of=window.fetch;"
    " window.fetch=async function(...a){ const r=await of.apply(this,a);"
    "   try{ const c=r.clone(); const u=String(a[0]&&a[0].url?a[0].url:a[0]);"
    "     c.text().then(t=>{ if(t && t.length<400000) window.__cap.push({url:u,body:t}); }); }catch(e){}"
    "   return r; };"
    " const oo=XMLHttpRequest.prototype.open, os=XMLHttpRequest.prototype.send;"
    " XMLHttpRequest.prototype.open=function(m,u){ this.__u=u; return oo.apply(this,arguments); };"
    " XMLHttpRequest.prototype.send=function(){ this.addEventListener('load',()=>{"
    "   try{ window.__cap.push({url:this.__u, body:String(this.responseText||'').slice(0,400000)});}catch(e){} });"
    "   return os.apply(this,arguments); };"
    " return 'hooked'; })()"
), timeout=90, state_path=STATE)
print("hook:", hook)

# 触发列表重新加载（切 tab / reload）
fq.js_eval(SESSION, "(() => {location.reload(); return 1;})()", timeout=60, state_path=STATE)
time.sleep(9)

cap = fq.js_eval(SESSION, (
    "(() => (window.__cap||[]).map(c=>({url:c.url,"
    " hit:/6434|4885|4887|4161/.test(c.body), len:c.body.length,"
    " body:(/6434|4885|4887|4161/.test(c.body)?c.body.slice(0,6000):'')})))()"
), timeout=120, state_path=STATE)

hits = [c for c in (cap or []) if isinstance(c, dict) and c.get("hit")]
print("captured:", len(cap or []), "hits:", len(hits))
out = {"captured_count": len(cap or []), "hits": []}
for h in hits:
    u = re.sub(r"(msToken|a_bogus)=[^&]+", r"\1=***", str(h.get("url")))
    print("--- HIT", u[:160])
    body = h.get("body", "")
    nums = {}
    try:
        j = json.loads(body)

        def walk(o, p=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    np = f"{p}.{k}" if p else k
                    if isinstance(v, (dict, list)):
                        walk(v, np)
                    elif re.search(r"word|count|title|order", k, re.I):
                        nums[np] = v
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f"{p}[{i}]")
        walk(j)
    except Exception as e:
        nums = {"parse_error": str(e)}
    picked = {k: v for k, v in nums.items()
              if str(v) in ("6434", "4885", "4887", "4161") or "title" in k.lower()}
    print(json.dumps(picked, ensure_ascii=False, indent=2)[:2500])
    out["hits"].append({"url": u, "fields": picked, "raw_head": body[:1500]})

Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/"
     "output/takeover_292/draft_list_api_fields_292.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
