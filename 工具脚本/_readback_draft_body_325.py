#!/usr/bin/env python3
"""只读：从草稿编辑页 adapter.view.dom（真正的正文编辑器）读回 325 正文，做禁句/定稿句命中判定。"""
import json, shlex, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import fanqie_update_draft_chapter as F

SESSION = F.DEFAULT_SESSION
STATE = Path('/root/workspace/browser_profiles/fanqie/fanqie_state.json')
EDIT = ('https://fanqienovel.com/main/writer/7628216044850531352/publish/'
        '7684075721026716184/?enter_from=modifydraft')

F.ab(SESSION, f"open {shlex.quote(EDIT)}", timeout=180, state_path=STATE)
for _ in range(40):
    time.sleep(2.0)
    st = F.js_eval(SESSION,
                   "(()=>{const a=window.adapter;return {ok:!!(a&&a.view&&a.view.dom),"
                   "len:(a&&a.view&&a.view.dom)?a.view.dom.innerText.length:0}})()",
                   state_path=STATE)
    if isinstance(st, dict) and st.get('ok') and int(st.get('len') or 0) > 500:
        break
print('editor_ready:', json.dumps(st, ensure_ascii=False))

res = F.js_eval(SESSION, r"""
(() => {
  const a = window.adapter;
  if (!(a && a.view && a.view.dom)) return {ok:false};
  const t = (a.view.dom.innerText || '').replace(/\s+/g, '');
  const probe = {
    r5_old1: t.includes('铁幕的运输纵队没有因为谈判会场'),
    r5_old2: t.includes('他把交接单递给接替押运的士官'),
    r7_new1: t.includes('铁幕的眼睛一直盯在这批装备上'),
    r7_new2: t.includes('检查站加派两名押运员上车'),
  };
  const cjk = (t.match(/[\u4e00-\u9fff]/g) || []).length;
  return {ok:true, chars:t.length, cjk, head:t.slice(0,40), tail:t.slice(-40), probe};
})()
""", state_path=STATE)
print(json.dumps(res, ensure_ascii=False, indent=1))

lst = F.find_draft_row(SESSION, 325, '三线联动', state_path=STATE)
print('listing_row:', json.dumps(lst, ensure_ascii=False))
