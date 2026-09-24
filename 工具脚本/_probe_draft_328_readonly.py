#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读：把草稿编辑页正文与本地 v5d 逐段比对。"""
import json, re, shlex, sys, time
from pathlib import Path
sys.path.insert(0, '/root/workspace/科武纪元/工具脚本')
import fanqie_update_draft_chapter as F

SESSION = F.DEFAULT_SESSION
STATE = Path('/root/workspace/browser_profiles/fanqie/fanqie_state.json')
URL = 'https://fanqienovel.com/main/writer/7628216044850531352/publish/7685948129987789336/?enter_from=modifydraft'

F.ab(SESSION, f"open {shlex.quote(URL)}", timeout=180, state_path=STATE)
time.sleep(6)
res = F.js_eval(SESSION, r"""
(() => {
  const bodyEd = Array.from(document.querySelectorAll('.ProseMirror')).find(e => (e.innerText||'').includes('（本章完）'));
  if (!bodyEd) return {ok:false};
  const paras = Array.from(bodyEd.querySelectorAll('p')).map(p => (p.innerText||'').trim()).filter(Boolean);
  return {ok:true, count: paras.length, paras};
})()
""", state_path=STATE)
(P_OUT := Path('/tmp/draft_328_body.json')).write_text(json.dumps(res, ensure_ascii=False), encoding='utf-8')

local = Path('/root/workspace/科武纪元/任务运行态/20260915_kewu_328_330/author_328_candidate_v5d.md').read_text(encoding='utf-8')
lp = [l.strip() for l in local.split('\n') if l.strip()]
dp = [x.strip() for x in res.get('paras', [])]
print('remote paras:', len(dp), '| local lines:', len(lp))
diff = [(i, a, b) for i, (a, b) in enumerate(zip(lp, dp)) if a != b]
print('mismatch count:', len(diff))
for i, a, b in diff[:6]:
    print('---- idx', i)
    print('  local :', a[:110])
    print('  remote:', b[:110])
if len(lp) != len(dp):
    print('LEN DIFF: local', len(lp), 'remote', len(dp))
    print('local tail:', lp[len(dp)-1:][:3])
    print('remote tail:', dp[len(lp)-1:][:3])
print('COMPARE_DONE')
