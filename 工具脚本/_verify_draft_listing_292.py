#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""292 草稿箱 listing 终验：回读章号/标题/字数/修改时间/未发布状态/count，并打开草稿页读卷名。"""
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
CH = 292
TITLE = "\u80fd\u6e90\u74f6\u9888"
NEEDLE = f"\u7b2c{CH}\u7ae0 {TITLE}"

out = {"chapter": CH, "title": TITLE, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

# ---- 1) 草稿箱列表 ----
fq.ab(SESSION, f"open {shlex.quote(fq.DRAFT_URL)}", timeout=60, state_path=STATE)
time.sleep(2.5)
js_list = (
    "(() => {"
    " const txt=document.body.innerText||'';"
    f" const needle={NEEDLE!r};"
    " let count=0, from=0;"
    " while(true){ const i=txt.indexOf(needle, from); if(i<0) break; count+=1; from=i+needle.length; }"
    " const start=txt.indexOf('\\u540d\\u79f0');"
    " const end=txt.indexOf('\\u00a9 2026');"
    " const listText=(start>=0&&end>start)?txt.slice(start,end):txt.slice(0,2000);"
    " const rows=Array.from(document.querySelectorAll('tr,[class*=\"row\"]')).map(e=>(e.innerText||'').replace(/\\n+/g,' | ').trim()).filter(s=>s.includes(needle));"
    " const links=Array.from(document.querySelectorAll('a')).map(a=>a.href).filter(h=>h&&h.includes('modifydraft'));"
    " return {ok:true, count, listText, rows, links, url:location.href, tabText:txt.slice(0,300)};"
    "})()"
)
res = fq.js_eval(SESSION, js_list, state_path=STATE)
out["listing"] = res

if not isinstance(res, dict) or not res.get("ok"):
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit("LISTING_SCAN_FAIL")

# ---- 2) 打开该草稿编辑页读卷名/标题/章号/字数 ----
links = res.get("links") or []
vol = None
if links:
    fq.ab(SESSION, f"open {shlex.quote(links[0])}", timeout=60, state_path=STATE)
    time.sleep(3.5)
    js_vol = (
        "(() => {"
        " const txt=document.body.innerText||'';"
        " const m=txt.match(new RegExp('\\u6b63\\u6587\\u5b57\\u6570\\\\\\\\s*([0-9]+)'));"
        " const volEl=document.querySelector('.publish-header-volume-name')"
        "  || document.querySelector('.publish-maintain-volume')"
        "  || document.querySelector('.publish-maintain');"
        " const title=Array.from(document.querySelectorAll('input')).find(e=>e.placeholder==='\\u8bf7\\u8f93\\u5165\\u6807\\u9898')?.value;"
        " const num=Array.from(document.querySelectorAll('input')).find(e=>String(e.className).includes('byte-input')&&!e.placeholder)?.value;"
        " return {url:location.href, vol:volEl?(volEl.innerText||'').trim():null, title, num, word:m?m[1]:null,"
        "         published:txt.includes('\\u5df2\\u53d1\\u5e03'), pendingAudit:txt.includes('\\u5ba1\\u6838\\u4e2d')};"
        "})()"
    )
    vol = fq.js_eval(SESSION, js_vol, state_path=STATE)
out["draft_page"] = vol

# ---- 3) 判定 ----
expect_vol = fq.resolve_volume(fq.PROJECT_DIR, CH, None)
listing_hit = NEEDLE in (res.get("listText") or "")
checks = {
    "listing_needle_hit": listing_hit,
    "count_is_1": res.get("count") == 1,
    "outline_volume": expect_vol,
    "page_volume": (vol or {}).get("vol"),
    "volume_match": bool(vol and expect_vol and expect_vol in str(vol.get("vol") or "")),
    "page_title": (vol or {}).get("title"),
    "page_chapter_num": (vol or {}).get("num"),
    "page_word": (vol or {}).get("word"),
    "not_published": not bool((vol or {}).get("published")),
}
out["checks"] = checks
out["verdict"] = "DRAFT_LISTING_VERIFIED" if all(
    [checks["listing_needle_hit"], checks["count_is_1"], checks["volume_match"], checks["not_published"]]
) else "DRAFT_SAVE_VERIFICATION_FAIL"

print(json.dumps(out, ensure_ascii=False, indent=2))
Path(
    "/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/output/takeover_292/draft_listing_292.json"
).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
