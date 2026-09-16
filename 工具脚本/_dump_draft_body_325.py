#!/usr/bin/env python3
"""只读：dump 草稿编辑页正文全文到文件，与本地 新版/第325章.md 做确定性 diff。"""
import json, shlex, sys, time, difflib, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import fanqie_update_draft_chapter as F

SESSION = F.DEFAULT_SESSION
STATE = Path('/root/workspace/browser_profiles/fanqie/fanqie_state.json')
EDIT = ('https://fanqienovel.com/main/writer/7628216044850531352/publish/'
        '7684075721026716184/?enter_from=modifydraft')
DUMP = Path('/root/workspace/任务运行态/20260911_ch325_author/output/draft_body_dump_1250.txt')

F.ab(SESSION, f"open {shlex.quote(EDIT)}", timeout=180, state_path=STATE)
st = None
for _ in range(40):
    time.sleep(2.0)
    st = F.js_eval(SESSION,
                   "(()=>{const a=window.adapter;return {ok:!!(a&&a.view&&a.view.dom),"
                   "len:(a&&a.view&&a.view.dom)?a.view.dom.innerText.length:0}})()",
                   state_path=STATE)
    if isinstance(st, dict) and st.get('ok') and int(st.get('len') or 0) > 500:
        break
print('editor_ready:', json.dumps(st, ensure_ascii=False))

body = F.js_eval(SESSION, "(()=>{const a=window.adapter;return a.view.dom.innerText})()",
                 state_path=STATE)
DUMP.write_text(body or '', encoding='utf-8')
print('dumped', len(body or ''), '->', DUMP)

local = Path('/root/workspace/科武纪元/新版/第325章.md').read_text(encoding='utf-8')


def norm(s):
    s = re.sub(r'\s+', '', s)
    return s


a, b = norm(local), norm(body or '')
print('local_norm', len(a), 'draft_norm', len(b), 'equal', a == b)
if a != b:
    sm = difflib.SequenceMatcher(None, a, b)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            print(tag, 'local[', i1, i2, ']=', repr(a[i1:i2][:120]),
                  '| draft[', j1, j2, ']=', repr(b[j1:j2][:120]))
