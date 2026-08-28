#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""服务端权威比对：edit_article 接口 content(HTML) 反解为段落，与本地定稿逐段比对。"""
import html as htmllib
import importlib.util
import json
import re
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
ITEM = "7677509566518526488"

fq.ab(SESSION, f"open https://fanqienovel.com/main/writer/{BOOK}/publish/{ITEM}/?enter_from=modifydraft",
      timeout=60, state_path=STATE)
time.sleep(7)
tmpl = fq.js_eval(SESSION, (
    "(() => {const e=performance.getEntriesByType('resource')"
    " .map(x=>x.name).filter(n=>n.includes('edit_article')); return e.slice(-1)[0]||null;})()"
), timeout=90, state_path=STATE)
if not isinstance(tmpl, str):
    sys.exit("NO_EDIT_ARTICLE_URL")

url = re.sub(r"item_id=\d+", f"item_id={ITEM}", tmpl)
js = ("(async () => { const r=await fetch(%s,{credentials:'include'});"
      " const j=await r.json(); const d=j.data||{};"
      " return {status:r.status, title:d.title||null, content:d.content||'',"
      "  volume:d.volume_name||d.volume||null, keys:Object.keys(d)};"
      " })()" % json.dumps(url))
res = fq.js_eval(SESSION, js, timeout=150, state_path=STATE)
if not isinstance(res, dict):
    print("RAW", str(res)[:800]); sys.exit("FETCH_FAIL")

content = res.pop("content", "")

def html_to_paras(h):
    h = re.sub(r"<typo[^>]*>", "", h)
    h = h.replace("</typo>", "")
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    parts = re.findall(r"<p[^>]*>(.*?)</p>", h, flags=re.S | re.I)
    if not parts:
        parts = [h]
    out = []
    for p in parts:
        t = re.sub(r"<[^>]+>", "", p)
        t = htmllib.unescape(t).strip()
        if t:
            out.append(t)
    return out

remote = html_to_paras(content)

TXT = Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u5df2\u6295\u7a3f/\u7b2c292\u7ae0.txt")
local = TXT.read_text(encoding="utf-8")
lb = local.split("\u4f5c\u8005\u6709\u8bdd\u8bf4\uff1a")[0]
ll = [l.strip() for l in lb.split("\n") if l.strip()]
local_paras = ll[1:]

norm = lambda s: re.sub(r"\s", "", s)
mismatch = next(({"idx": i, "remote": a[:180], "local": b[:180]}
                 for i, (a, b) in enumerate(zip(remote, local_paras)) if a != b), None)
out = {
    "api_status": res.get("status"),
    "api_title": res.get("title"),
    "api_data_keys": res.get("keys"),
    "remote_para_count": len(remote),
    "local_para_count": len(local_paras),
    "paras_equal_sequence": remote == local_paras,
    "first_mismatch": mismatch,
    "remote_body_norm": len(norm("\n".join(remote))),
    "local_body_norm": len(norm("\n".join(local_paras))),
    "remote_body_cjk": len(re.findall(r"[\u4e00-\u9fff]", "".join(remote))),
    "local_body_cjk": len(re.findall(r"[\u4e00-\u9fff]", "".join(local_paras))),
    "remote_content_html_len": len(content),
    "end_marker_count": sum(1 for p in remote if p == "\uff08\u672c\u7ae0\u5b8c\uff09"),
    "duplicate_para_count": len(remote) - len(set(remote)),
    "listing_word_field": 6434,
    "editor_word_label": 4885,
    "verdict": ("SERVER_CONTENT_IDENTICAL_TO_LOCAL" if remote == local_paras
                else "SERVER_CONTENT_MISMATCH"),
}
print(json.dumps(out, ensure_ascii=False, indent=2))
Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/"
     "output/takeover_292/server_content_verify_292.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
