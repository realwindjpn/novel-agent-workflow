#!/usr/bin/env python3
"""只读诊断：草稿箱 325 编辑页里 adapter.view 对应的 DOM 是否就是脚本挑中的正文编辑器。"""
import json, shlex, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import fanqie_update_draft_chapter as F

SESSION = F.DEFAULT_SESSION
STATE = Path('/root/workspace/browser_profiles/fanqie/fanqie_state.json')
EDIT = 'https://fanqienovel.com/main/writer/7628216044850531352/publish/7684075721026716184/?enter_from=modifydraft'

F.ab(SESSION, f"open {shlex.quote(EDIT)}", timeout=180, state_path=STATE)
st = None
for _ in range(40):
    time.sleep(2.0)
    st = F.js_eval(SESSION, "(()=>{const e=Array.from(document.querySelectorAll('.ProseMirror'));return {url:location.href,n:e.length,len:e.length?e[0].textContent.length:0}})()", state_path=STATE)
    if isinstance(st, dict) and st.get('n') and int(st.get('len') or 0) > 0:
        break
print('page:', json.dumps(st, ensure_ascii=False))

diag = F.js_eval(SESSION, r"""
(() => {
  const eds = Array.from(document.querySelectorAll('.ProseMirror'));
  const info = eds.map((e, i) => {
    const r = e.getBoundingClientRect();
    const t = (e.innerText || '').replace(/\s+/g, '');
    return {i, x: Math.round(r.x), w: Math.round(r.width), words: t.length,
            head: t.slice(0, 20), tail: t.slice(-20)};
  });
  const picked = eds.findIndex(e => e.getBoundingClientRect().x < 1100 && e.getBoundingClientRect().width > 500);
  const a = window.adapter;
  let ad = {present: !!a, hasView: !!(a && a.view), hasDispatch: !!(a && a.view && typeof a.view.dispatch === 'function')};
  if (a && a.view && a.view.dom) {
    ad.domIndex = eds.indexOf(a.view.dom);
    const at = (a.view.dom.innerText || '').replace(/\s+/g, '');
    ad.domWords = at.length;
    ad.domHead = at.slice(0, 20);
    ad.docSize = a.view.state ? a.view.state.doc.content.size : null;
  }
  const pw = (document.body.innerText || '').match(/正文字数\s*([0-9]+)/);
  const marks = {
    r7_new1: (document.body.innerText || '').includes('铁幕的眼睛一直盯在这批装备上'),
    r7_new2: (document.body.innerText || '').includes('检查站加派两名押运员上车'),
    r5_old1: (document.body.innerText || '').includes('铁幕的运输纵队没有因为谈判会场'),
    r5_old2: (document.body.innerText || '').includes('他把交接单递给接替押运的士官'),
  };
  return {count: eds.length, picked, editors: info, adapter: ad, pageWordCount: pw ? pw[1] : null, marks};
})()
""", state_path=STATE)
print(json.dumps(diag, ensure_ascii=False, indent=1))
