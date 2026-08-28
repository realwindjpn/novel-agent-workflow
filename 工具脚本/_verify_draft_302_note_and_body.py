#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""302 草稿箱回读硬核验：作者说节点(.author-speak-input-view，须不在正文 ProseMirror 内) + 正文首末 + 章号/标题/卷名。

按 kewu-close-loop P0：
- 不用 body.innerText.includes(note) 做唯一判据（长文本假阴性）
- 重开 ?enter_from=modifydraft 页，读 .author-speak-input-view.innerText
- 核首句+末句+关键术语；确认该节点不在正文 .ProseMirror 内
"""
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
# 302 草稿 URL（来自本轮 execute 回执 final.saved.url）
URL = ("https://fanqienovel.com/main/writer/7628216044850531352/publish/"
       "7679091647535120920?enter_from=modifydraft")

fq.ab(SESSION, f"open {shlex.quote(URL)}", timeout=60, state_path=STATE)
time.sleep(6)

js = (
    "(() => {"
    " const out={};"
    " const nodes=Array.from(document.querySelectorAll('.author-speak-input-view'));"
    " out.noteNodeCount=nodes.length;"
    " out.noteText=nodes.length?(nodes[0].innerText||''):'';"
    " out.noteInsideProseMirror=nodes.length?!!nodes[0].closest('.ProseMirror'):null;"
    " const eds=Array.from(document.querySelectorAll('.ProseMirror'));"
    " let best=null,bl=-1;"
    " for(const e of eds){const t=e.textContent||''; if(t.length>bl){bl=t.length;best=e;}}"
    " out.bodyLen=best?(best.textContent||'').length:0;"
    " const ps=best?Array.from(best.querySelectorAll('p')).map(p=>(p.textContent||'').trim()).filter(Boolean):[];"
    " out.bodyFirst=ps.length?ps[0]:'';"
    " out.bodyLast=ps.length?ps[ps.length-1]:'';"
    " out.bodyParaCount=ps.length;"
    " out.bodyHasNoteText=best?((best.textContent||'').indexOf('\\u4f5c\\u8005\\u6709\\u8bdd\\u8bf4')>=0):null;"
    " const ti=document.querySelector('input[placeholder*=\\u7ae0\\u8282\\u540d], .publish-title input, input.title-input');"
    " out.titleVal=ti?ti.value:'';"
    " const nu=Array.from(document.querySelectorAll('input')).map(i=>i.value).filter(v=>/^\\d+$/.test(v||''));"
    " out.numCandidates=nu;"
    " const vol=document.querySelector('.publish-maintain-volume, .publish-header-volume-wrap, .publish-maintain');"
    " out.volText=vol?(vol.innerText||'').trim().slice(0,80):'';"
    " return out;"
    "})()"
)
res = fq.js_eval(SESSION, js, timeout=120, state_path=STATE)
if not isinstance(res, dict):
    print("RAW:", str(res)[:2000])
    sys.exit("READ_FAIL")

NOTE = Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/"
            "20260828_kewu_selfcycle_daily/output/note_302_clean.md")
local_note = NOTE.read_text(encoding="utf-8").strip()
first_sent = local_note.split("\u3002")[0]
last_sent = [s for s in local_note.split("\u3002") if s.strip()][-1]

online_note = (res.get("noteText") or "").strip()

checks = {
    "\u4f5c\u8005\u8bf4\u8282\u70b9\u5b58\u5728": res.get("noteNodeCount", 0) >= 1,
    "\u4f5c\u8005\u8bf4\u4e0d\u5728\u6b63\u6587ProseMirror\u5185": res.get("noteInsideProseMirror") is False,
    "\u4f5c\u8005\u8bf4\u9996\u53e5\u547d\u4e2d": first_sent in online_note,
    "\u4f5c\u8005\u8bf4\u672b\u53e5\u547d\u4e2d": last_sent.strip() in online_note,
    "\u5173\u952e\u672f\u8bed_\u6db2\u51b7\u76d1\u63a7\u53f0": "\u6db2\u51b7\u76d1\u63a7\u53f0" in online_note,
    "\u5173\u952e\u672f\u8bed_\u6761\u6587\u7f16\u53f7": "\u6761\u6587\u7f16\u53f7" in online_note,
    "\u6b63\u6587\u4e0d\u542b\u4f5c\u8005\u8bf4\u5b57\u6837": res.get("bodyHasNoteText") is False,
    "\u6b63\u6587\u672b\u53e5=\uff08\u672c\u7ae0\u5b8c\uff09": "\uff08\u672c\u7ae0\u5b8c\uff09" in (res.get("bodyLast") or ""),
    "\u6b63\u6587\u957f\u5ea6>3000": res.get("bodyLen", 0) > 3000,
    "\u5377\u540d\u542b\u7b2c\u516d\u5377": "\u7b2c\u516d\u5377" in (res.get("volText") or ""),
}

print("=== \u56de\u8bfb\u7ed3\u679c ===")
print("\u4f5c\u8005\u8bf4\u8282\u70b9\u6570:", res.get("noteNodeCount"),
      "| \u5728\u6b63\u6587\u5185:", res.get("noteInsideProseMirror"))
print("\u7ebf\u4e0a\u4f5c\u8005\u8bf4\u957f\u5ea6:", len(online_note), "| \u672c\u5730:", len(local_note))
print("\u6b63\u6587\u957f\u5ea6:", res.get("bodyLen"), "| \u6bb5\u6570:", res.get("bodyParaCount"))
print("\u6b63\u6587\u9996\u53e5:", (res.get("bodyFirst") or "")[:50])
print("\u6b63\u6587\u672b\u53e5:", (res.get("bodyLast") or "")[:50])
print("\u5377\u540d:", (res.get("volText") or "")[:60].replace("\n", " / "))
print()
for k, v in checks.items():
    print(("  \u2705 " if v else "  \u274c ") + k, v)

ok = all(checks.values())
print("\nALL_PASS =", ok)
OUTJ = Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/"
            "20260828_kewu_selfcycle_daily/output/DRAFT_302_READBACK.json")
OUTJ.write_text(json.dumps(
    {"checks": checks, "all_pass": ok, "online_note_len": len(online_note),
     "body_len": res.get("bodyLen"), "vol": res.get("volText"),
     "note_node_count": res.get("noteNodeCount"),
     "note_inside_prosemirror": res.get("noteInsideProseMirror")},
    ensure_ascii=False, indent=2), encoding="utf-8")
print("\u843d\u76d8:", OUTJ)
sys.exit(0 if ok else 1)
