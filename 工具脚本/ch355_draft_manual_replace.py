#!/usr/bin/env python3
"""355 草稿正文手动覆盖（脚本 saved:true 为假信号时的可靠路径）。

2026-09-25：fanqie_update_draft_chapter.py 报 ok/saved/verified 全绿，
但重开编辑页 + 预览页回读均为旧版（hasLin=false, hasOld=true）。
沿用 351 已验真的方式：adapter.view.dispatch 写正文 → 硬校验 → 点存草稿。
"""
import json, re, subprocess, sys, time
from pathlib import Path

SESSION = "fanqie"
DRAFT_URL = ("https://fanqienovel.com/main/writer/7628216044850531352/"
             "publish/7689273549055345176/?enter_from=modifydraft")
TXT = Path("/root/workspace/科武纪元/已投稿/第355章.txt")

raw = TXT.read_text(encoding="utf-8-sig").strip()
lines = raw.split("\n")
head = lines[0].strip()
rest = "\n".join(lines[1:])
body = rest.split("作者有话说：", 1)[0].strip()
assert body.endswith("（本章完）")
assert not body.startswith("第355章")
body_json = json.dumps(body, ensure_ascii=False)
norm_words = len(re.sub(r"\s+", "", body))
print("local body_words:", norm_words, "| json len:", len(body_json))


def ev(js, timeout=180):
    p = Path("/tmp/_ev.js")
    p.write_text(js, encoding="utf-8")
    r = subprocess.run(["agent-browser", "--session-name", SESSION, "--cdp", "9223",
                        "eval", js], capture_output=True, text=True, timeout=timeout)
    out = (r.stdout or "").strip()
    try:
        v = json.loads(out)
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return v
        return v
    except Exception:
        return out


def nav(url):
    subprocess.run(["agent-browser", "--session-name", SESSION, "--cdp", "9223",
                    "navigate", url], capture_output=True, text=True, timeout=90)


nav(DRAFT_URL)
time.sleep(12)

REPLACE = """
(() => {
 const body = __BODY__;
 const W = (s) => (s || '').replace(/\\s+/g, '').length;
 const NW = (s) => (s || '').replace(/\\s+/g, '');
 const ed = Array.from(document.querySelectorAll('.ProseMirror'))
   .find(e => e.getBoundingClientRect().width > 500 && e.getBoundingClientRect().x < 1100);
 if (!ed) return {ok:false, reason:'editor_not_found'};
 const before = ed.innerText || '';
 const view = (window.adapter && window.adapter.view) || ed.pmViewDesc?.view;
 if (!view) return {ok:false, reason:'no_adapter_view', beforeWords: W(before)};
 const state = view.state;
 let tr = state.tr;
 const allSel = state.selection.constructor.create(state.doc, 0, state.doc.content.size);
 tr.setSelection(allSel);
 tr.deleteSelection();
 // 按行分段写入（避免把换行符依赖交给 insertText 自动转换段落）
 const lines = body.split('\\n');
 for (let i = 0; i < lines.length; i++) {
   if (i > 0) { tr.insertText('\\n'); }
   if (lines[i]) { tr.insertText(lines[i]); }
 }
 view.dispatch(tr);
 const after = ed.innerText || '';
 const afterN = NW(after);
 const pageTxt = document.body.innerText || '';
 const pw = pageTxt.match(/正文字数\\s*([0-9]+)/);
 return {ok:true, method:'adapter.view.dispatch',
   beforeWords: W(before), afterWords: afterN.length,
   head30: afterN.slice(0,30), tail30: afterN.slice(-30),
   pageWordCount: pw ? parseInt(pw[1],10) : null,
   len: after.length};
})()
""".replace("__BODY__", body_json)

r = ev(REPLACE)
print("REPLACE:", json.dumps(r, ensure_ascii=False)[:400])
if not isinstance(r, dict) or not r.get("ok"):
    sys.exit("replace failed")

n = len(re.findall(r"[\u4e00-\u9fff]", body))
print("expect words:", norm_words, "| got:", r.get("afterWords"),
      "| page:", r.get("pageWordCount"))

# 硬校验：字数容差 + 首尾一致
exp_head = re.sub(r"\s+", "", body)[:30]
exp_tail = re.sub(r"\s+", "", body)[-30:]
if abs(int(r.get("afterWords", 0)) - norm_words) > 5:
    sys.exit(f"WORDS_FAIL got={r.get('afterWords')} expect={norm_words}")
if r.get("head30") != exp_head:
    sys.exit(f"HEAD_FAIL got={r.get('head30')!r} expect={exp_head!r}")
if r.get("tail30") != exp_tail:
    sys.exit(f"TAIL_FAIL got={r.get('tail30')!r} expect={exp_tail!r}")
print("BODY_VERIFY: PASS")

time.sleep(3)
SAVE = """
(() => {
 const b = Array.from(document.querySelectorAll('button'))
   .find(x => (x.innerText||'').trim() === '存草稿');
 if (!b) return {ok:false, reason:'save_button_not_found',
   btns: Array.from(document.querySelectorAll('button')).map(y=>(y.innerText||'').trim()).slice(0,15)};
 b.click();
 return {ok:true, clicked:true};
})()
"""
s = ev(SAVE, timeout=90)
print("SAVE:", json.dumps(s, ensure_ascii=False)[:300])
time.sleep(8)

VER = """
(() => {
 const t = document.body.innerText || '';
 const pw = t.match(/正文字数\\s*([0-9]+)/);
 return {pageWord: pw ? parseInt(pw[1],10) : null,
   toast: (t.match(/(保存成功|已保存|草稿已保存)/)||[null])[0]};
})()
"""
print("VERIFY:", json.dumps(ev(VER, timeout=90), ensure_ascii=False)[:200])
print("DONE")
