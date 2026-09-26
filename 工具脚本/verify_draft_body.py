#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""草稿箱（type=2）正文回读验真：与 verify_uploaded_body.py 同规范化，逐段硬比对。

用法: python3 verify_draft_body.py <章号> [<章号> ...]
"""
import json, re, shlex, subprocess, sys, tempfile, time, unicodedata
from pathlib import Path

CH = Path('/root/workspace/科武纪元')
BOOK_ID = '7628216044850531352'
BOOK_NAME_ENC = '%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99'
DRAFT_MANAGE = f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}&{BOOK_NAME_ENC}?type=2'
SESSION = 'fanqie'


def ab(cmd, timeout=90):
    p = subprocess.run(f'agent-browser --session-name {SESSION} --cdp 9223 {cmd}',
                       shell=True, text=True, capture_output=True, timeout=timeout)
    return p.stdout


def js_eval(js, timeout=90):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.js', delete=False) as f:
        f.write(js); p = Path(f.name)
    try:
        out = ab(f'eval "$(cat {shlex.quote(str(p))})"', timeout=timeout)
    finally:
        p.unlink(missing_ok=True)
    try:
        return json.loads(out)
    except Exception:
        return out


def norm(s: str) -> str:
    s = unicodedata.normalize('NFKC', s or '')
    s = re.sub(r'[\u200b-\u200f\ufeff\u00a0]', '', s)
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    s = re.sub(r'[ \t\u3000]+', '', s)
    return s.strip()


def paras(s: str) -> list:
    s = norm(s)
    out = []
    for chunk in re.split(r'\n+', s):
        c = chunk.strip()
        if c:
            out.append(c)
    return out


def local_body(ch: int) -> str:
    p = CH / '已投稿' / f'第{ch}章.txt'
    body = p.read_text(encoding='utf-8-sig').strip().splitlines()
    body = '\n'.join(body[1:]).strip()
    if '作者有话说：' in body:
        body = body.split('作者有话说：', 1)[0].strip()
    return body


def local_note(ch: int) -> str:
    p = CH / '已投稿' / f'第{ch}章.txt'
    t = p.read_text(encoding='utf-8-sig')
    if '作者有话说：' not in t:
        return ''
    return t.split('作者有话说：', 1)[1].strip()


def list_rows():
    """草稿箱列表全量行（含标题/字数/时间/草稿ID链接）。"""
    js = """(() => {
 const rows=[...document.querySelectorAll('tr,.arco-table-tr')];
 return rows.map(r=>{
   const t=(r.innerText||'').split('\\n').map(s=>s.trim()).filter(Boolean);
   const a=r.querySelector('a[href*="publish"]');
   return {text:t, href:a?a.getAttribute('href'):''};
 }).filter(x=>x.text.length);
})()"""
    return js_eval(js)


def infer_volume(ch: int) -> str:
    outline = CH / '科武纪元大纲 V8_完整版.md'
    text = outline.read_text(encoding='utf-8')
    m = re.search(rf'第{ch}章\s*\|\s*([^|\n]+?)\s*\|', text)
    if not m:
        raise RuntimeError(f'大纲未找到第{ch}章分卷')
    return m.group(1).strip().replace('·', '：')


def open_draft_editor(ch: int) -> bool:
    js = f"""(() => {{
 const rows=[...document.querySelectorAll('tr,.arco-table-tr')];
 const r=rows.find(x=>(x.innerText||'').includes('第{ch}章'));
 if(!r) return {{ok:false, reason:'row_not_found'}};
 const a=r.querySelector('a[href*="publish"]')||r.querySelector('a');
 if(!a) return {{ok:false, reason:'link_not_found'}};
 a.click();
 return {{ok:true, href:a.getAttribute('href')}};
}})()"""
    r = js_eval(js)
    time.sleep(4.0)
    return bool(isinstance(r, dict) and r.get('ok'))


def read_editor():
    js = """(() => {
 const pm=document.querySelector('.ProseMirror')||document.querySelector('[contenteditable]');
 const note=document.querySelector('.author-speak-input-view');
 return {ok: !!pm, text: pm?pm.innerText:'', note: note?note.innerText:'', url: location.href};
})()"""
    return js_eval(js)


def main(chs):
    results = []
    ab(f'open {shlex.quote(DRAFT_MANAGE)}')
    time.sleep(4.0)
    rows = list_rows()
    text_all = json.dumps(rows, ensure_ascii=False)
    for ch in chs:
        print(f"\n{'='*56}\n第{ch}章 草稿箱验真")
        try:
            vol = infer_volume(ch)
        except Exception as e:
            print(f'  ❌ {e}')
            results.append({'ch': ch, 'ok': False, 'reason': 'volume_unknown'}); continue
        hits = [r for r in rows if isinstance(r, dict) and f'第{ch}章' in json.dumps(r.get('text'), ensure_ascii=False)]
        print(f"  大纲推断卷={vol}；草稿箱同名命中 {len(hits)} 条 -> {[h.get('text')[:4] for h in hits]}")
        if len(hits) != 1:
            results.append({'ch': ch, 'ok': False, 'reason': f'listing_count={len(hits)}'}); continue
        if not open_draft_editor(ch):
            print('  ❌ 未能打开草稿编辑页')
            results.append({'ch': ch, 'ok': False, 'reason': 'open_failed'}); continue
        ed = read_editor()
        if not isinstance(ed, dict) or not ed.get('ok'):
            print(f"  ❌ 编辑区未取到：{ed}")
            results.append({'ch': ch, 'ok': False, 'reason': 'editor_not_found'}); continue
        lb, rb = paras(local_body(ch)), paras(ed.get('text', ''))
        same = lb == rb
        print(f"  正文段落数 本地={len(lb)} 平台={len(rb)} 逐段相等={same}")
        if not same:
            for i, (a, b) in enumerate(zip(lb, rb)):
                if a != b:
                    print(f"    首个差异段 #{i}:")
                    print(f"      本地: {a[:80]}")
                    print(f"      平台: {b[:80]}")
                    break
        ln, rn = paras(local_note(ch)), paras(ed.get('note', ''))
        note_same = (not ln) or (ln == rn)
        print(f"  作者说段落数 本地={len(ln)} 平台={len(rn)} 相等={note_same}")
        # 卷名回读
        cur_vol = js_eval("(() => { const v=document.querySelector('.publish-maintain-volume')||document.querySelector('.publish-header-volume-wrap'); return v?(v.innerText||'').trim():''; })()")
        vol_ok = vol in json.dumps(cur_vol, ensure_ascii=False)
        print(f"  编辑页卷名回读={cur_vol} 与大纲一致={vol_ok}")
        results.append({'ch': ch, 'ok': bool(same and note_same and vol_ok),
                        'body_equal': same, 'note_equal': note_same, 'volume_ok': vol_ok,
                        'paras': [len(lb), len(rb)]})
    print("\n汇总:", json.dumps(results, ensure_ascii=False))
    return 0 if all(r.get('ok') for r in results) else 1


if __name__ == '__main__':
    sys.exit(main([int(x) for x in sys.argv[1:]]))
