#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读回 292 草稿编辑页正文，核对与本地 TXT 一致性（查是否重复写入）。"""
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
time.sleep(4)

js = (
    "(() => {"
    " const eds=Array.from(document.querySelectorAll('.ProseMirror'));"
    " const info=eds.map(e=>({cls:String(e.className).slice(0,60), len:(e.innerText||'').length,"
    "   head:(e.innerText||'').slice(0,80), tail:(e.innerText||'').slice(-80)}));"
    " const main=eds.map(e=>e.innerText||'').sort((a,b)=>b.length-a.length)[0]||'';"
    " const txt=document.body.innerText||'';"
    " const m=txt.match(new RegExp('\\u6b63\\u6587\\u5b57\\u6570\\\\\\\\s*([0-9]+)'));"
    " return {editors:info, mainLen:main.length, mainHead:main.slice(0,120), mainTail:main.slice(-160),"
    "   wordLabel:m?m[1]:null, endMarkerCount:(main.match(/\\uff08\\u672c\\u7ae0\\u5b8c\\uff09/g)||[]).length,"
    "   firstLineCount:(main.match(/\\u4f1a\\u8bae\\u5ba4\\u7684\\u6295\\u5f71\\u5c4f\\u6302\\u5728\\u5317\\u5899/g)||[]).length,"
    "   noteCount:(main.match(/\\u4f5c\\u8005\\u6709\\u8bdd\\u8bf4/g)||[]).length, main};"
    "})()"
)
res = fq.js_eval(SESSION, js, timeout=90, state_path=STATE)
if not isinstance(res, dict):
    print("RAW:", str(res)[:2000])
    sys.exit("READ_FAIL")

main = res.pop("main", "")
TXT = Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u5df2\u6295\u7a3f/\u7b2c292\u7ae0.txt")
local = TXT.read_text(encoding="utf-8")
local_body = local.split("\u4f5c\u8005\u6709\u8bdd\u8bf4\uff1a")[0]


def norm(s):
    return re.sub(r"\s", "", s)


res["local_body_norm_len"] = len(norm(local_body))
res["remote_norm_len"] = len(norm(main))
res["remote_cjk"] = len(re.findall(r"[\u4e00-\u9fff]", main))
res["local_body_cjk"] = len(re.findall(r"[\u4e00-\u9fff]", local_body))
res["remote_contains_local_body"] = norm(local_body) in norm(main)
res["exact_body_match"] = norm(local_body) == norm(main)
print(json.dumps(res, ensure_ascii=False, indent=2))
Path(
    "/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/output/takeover_292/draft_body_readback_292.json"
).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
Path(
    "/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/output/takeover_292/draft_remote_body_292.txt"
).write_text(main, encoding="utf-8")
