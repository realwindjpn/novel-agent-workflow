#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""310草稿终验：列表唯一、编辑页卷名/章号/标题/正文首尾/作者说独立节点/未发布。"""
import importlib.util, json, re, shlex, sys, time
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    'fq', '/root/workspace/科武纪元/工具脚本/fanqie_draft_upload_chapter.py')
fq = importlib.util.module_from_spec(SPEC)
sys.modules['fq'] = fq
SPEC.loader.exec_module(fq)
SESSION = fq.DEFAULT_SESSION
STATE = fq.DEFAULT_STATE
DRAFT_ID = '7680754290259919384'
URL = f'https://fanqienovel.com/main/writer/7628216044850531352/publish/{DRAFT_ID}?enter_from=modifydraft'
LIST = ('https://fanqienovel.com/main/writer/chapter-manage/7628216044850531352&'
        '%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99?type=2')
TXT = Path('/root/workspace/科武纪元/已投稿/第310章.txt')
OUT = Path('/root/workspace/科武纪元/任务运行态/20260901_kewu_selfcycle_daily/output/DRAFT_310_READBACK.json')
NEEDLE = '第310章 火星秘藏'

local = TXT.read_text(encoding='utf-8-sig')
note = local.split('作者有话说：', 1)[1].strip()
body = local.split('作者有话说：', 1)[0].strip().splitlines()[1:]
paras = [x.strip() for x in body if x.strip()]
first, last = paras[0], paras[-1]

fq.ab(SESSION, f'open {shlex.quote(LIST)}', timeout=90, state_path=STATE)
time.sleep(5)
lst = fq.js_eval(SESSION, """(() => {const rows=Array.from(document.querySelectorAll('tr.arco-table-tr'));const norm=s=>(s||'').replace(/\\s+/g,' ').trim();const hits=rows.filter(r=>norm(r.innerText).includes('第310章 火星秘藏'));return {count:hits.length,row:hits.length?norm(hits[0].innerText):null};})()""", timeout=90, state_path=STATE)

fq.ab(SESSION, f'open {shlex.quote(URL)}', timeout=90, state_path=STATE)
time.sleep(6)
page = fq.js_eval(SESSION, """(() => {const nodes=Array.from(document.querySelectorAll('.author-speak-input-view'));const eds=Array.from(document.querySelectorAll('.ProseMirror'));let best=null,bl=-1;for(const e of eds){const t=e.innerText||'';if(t.length>bl){bl=t.length;best=e;}}const ps=best?Array.from(best.querySelectorAll('p')).map(p=>(p.innerText||'').trim()).filter(Boolean):[];const inputs=Array.from(document.querySelectorAll('input'));const num=inputs.map(x=>x.value).find(v=>v==='310')||null;const title=inputs.map(x=>x.value).find(v=>v==='火星秘藏')||null;const vol=document.querySelector('.publish-maintain-volume, .publish-header-volume-wrap, .publish-maintain');const publishButtons=Array.from(document.querySelectorAll('button')).map(x=>(x.innerText||'').trim()).filter(Boolean);return {noteCount:nodes.length,noteText:nodes.length?(nodes[0].innerText||''):'',noteInside:nodes.length?!!nodes[0].closest('.ProseMirror'):null,bodyFirst:ps[0]||'',bodyLast:ps[ps.length-1]||'',bodyParaCount:ps.length,bodyLen:best?(best.innerText||'').replace(/\\s+/g,'').length:0,bodyHasNote:best?(best.innerText||'').includes('作者有话说'):null,num,title,vol:vol?(vol.innerText||'').trim():'',publishButtons,url:location.href};})()""", timeout=120, state_path=STATE)

checks = {
    'listing_count_1': lst.get('count') == 1,
    'listing_title': bool(lst.get('row')) and NEEDLE in lst['row'],
    'num_310': page.get('num') == '310',
    'title_match': page.get('title') == '火星秘藏',
    'volume_match': '第七卷：铁幕' in page.get('vol', ''),
    'draft_edit_route': 'enter_from=modifydraft' in page.get('url', ''),
    'note_node': page.get('noteCount', 0) >= 1,
    'note_separate': page.get('noteInside') is False,
    'note_exact': re.sub(r'\s+', '', note) == re.sub(r'\s+', '', page.get('noteText', '')),
    'body_no_note': page.get('bodyHasNote') is False,
    'body_first': first == page.get('bodyFirst'),
    'body_last': last == page.get('bodyLast'),
    'body_len_gt3000': page.get('bodyLen', 0) > 3000,
}
res = {'chapter': 310, 'draft_id': DRAFT_ID, 'listing': lst, 'page': page,
       'local_paras': len(paras),
       'checks': checks,
       'verdict': 'DRAFT_SAVED_NOT_PUBLISHED' if all(checks.values()) else 'DRAFT_SAVE_VERIFICATION_FAIL'}
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(res, ensure_ascii=False, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
