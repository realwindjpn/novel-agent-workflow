#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""292 草稿终验：列表行(章号/标题/字数/时间/count) + 编辑页(卷名/章号/标题/未发布)。"""
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
URL = ("https://fanqienovel.com/main/writer/7628216044850531352/publish/"
       "7677509566518526488/?enter_from=modifydraft")
LIST = ("https://fanqienovel.com/main/writer/chapter-manage/7628216044850531352"
        "&%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99?type=2")

fq.ab(SESSION, f"open {shlex.quote(LIST)}", timeout=60, state_path=STATE)
time.sleep(6)
lst = fq.js_eval(SESSION, (
    "(() => {"
    " const t=document.body.innerText||'';"
    " const rows=t.split('\\n').map(s=>s.trim()).filter(Boolean);"
    " const i=rows.findIndex(r=>r.indexOf('\\u7b2c292\\u7ae0')===0);"
    " const links=Array.from(document.querySelectorAll('a')).map(a=>a.href).filter(h=>h.includes('modifydraft'));"
    " return {row:i>=0?rows.slice(i,i+3):null, occurrences:(t.match(/\\u7b2c292\\u7ae0/g)||[]).length,"
    "   draftTotalText:(rows.find(r=>r.indexOf('\\u5171')===0&&r.includes('\\u8349\\u7a3f'))||null), links:links};"
    "})()"), timeout=90, state_path=STATE)

fq.ab(SESSION, f"open {shlex.quote(URL)}", timeout=60, state_path=STATE)
time.sleep(6)
page = fq.js_eval(SESSION, (
    "(() => {"
    " const b=document.body.innerText||'';"
    " const inputs=Array.from(document.querySelectorAll('input[type=text]')).map(n=>n.value||'');"
    " const mv=b.match(/\\u7b2c[\\u4e00-\\u9fff]+\\u5377\\uff1a[\\u4e00-\\u9fff]+/g)||[];"
    " const mw=b.match(/\\u6b63\\u6587\\u5b57\\u6570\\s*\\n?\\s*([0-9]+)/);"
    " return {volCandidates:mv.slice(0,4), wordLabel:mw?mw[1]:null,"
    "   chapterNum:inputs[0]||null, title:inputs[1]||null,"
    "   published:/\\u5df2\\u53d1\\u5e03|\\u5ba1\\u6838\\u4e2d/.test(b), savedCloud:b.includes('\\u5df2\\u4fdd\\u5b58\\u5230\\u4e91\\u7aef'),"
    "   headText:b.slice(0,200)};"
    "})()"), timeout=90, state_path=STATE)

TXT = Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u5df2\u6295\u7a3f/\u7b2c292\u7ae0.txt")
local = TXT.read_text(encoding="utf-8")
lb = local.split("\u4f5c\u8005\u6709\u8bdd\u8bf4\uff1a")[0]
ll = [l.strip() for l in lb.split("\n") if l.strip()]
local_norm = len(re.sub(r"\s", "", "\n".join(ll[1:])))

OUTLINE_VOL = "\u7b2c\u516d\u5377\uff1a\u706b\u661f"
row = lst.get("row") or []
listing_word = int(row[1]) if len(row) > 1 and row[1].isdigit() else None
page_vol = next((v for v in (page.get("volCandidates") or []) if v == OUTLINE_VOL), None)

checks = {
    "listing_row": row,
    "listing_occurrences": lst.get("occurrences"),
    "count_is_1": lst.get("occurrences") == 1,
    "listing_title_hit": bool(row) and row[0] == "\u7b2c292\u7ae0 \u80fd\u6e90\u74f6\u9888",
    "listing_word": listing_word,
    "local_fanqie_body": local_norm,
    "word_delta": (listing_word - local_norm) if listing_word else None,
    "word_within_tolerance": (listing_word is not None and abs(listing_word - local_norm) <= 10),
    "page_chapter_num": page.get("chapterNum"),
    "page_title": page.get("title"),
    "page_word": page.get("wordLabel"),
    "outline_volume": OUTLINE_VOL,
    "page_volume": page_vol,
    "volume_match": page_vol == OUTLINE_VOL,
    "not_published": not page.get("published"),
    "saved_cloud": page.get("savedCloud"),
    "draft_total_text": lst.get("draftTotalText"),
}
checks["verdict"] = (
    "DRAFT_LISTING_VERIFIED" if all([
        checks["count_is_1"], checks["listing_title_hit"], checks["word_within_tolerance"],
        checks["volume_match"], checks["not_published"],
        checks["page_chapter_num"] == "292", checks["page_title"] == "\u80fd\u6e90\u74f6\u9888",
    ]) else "DRAFT_SAVE_VERIFICATION_FAIL"
)
out = {"listing": lst, "page": page, "checks": checks}
print(json.dumps(out, ensure_ascii=False, indent=2))
Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/"
     "output/takeover_292/draft_final_listing_verify_292.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
