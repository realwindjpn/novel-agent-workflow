#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""已发布章节修改后正文回读验真（三重核）。

背景：fanqie_modify_uploaded_chapter.py 的 verified 只回读列表行状态（如「修改审核中」），
不比对正文。列表字数与编辑页字数口径不同，单看计数差不能判污染。
按 memory 铁律：正文实际文本须以重开 modifydraft 后 ProseMirror 全文与本地正文
**同一规范化函数**逐字相等为硬证。

用法: python3 verify_uploaded_body.py <章号> [<章号> ...]
"""
import json, re, shlex, subprocess, sys, tempfile, time, unicodedata
from pathlib import Path

CH = Path('/root/workspace/科武纪元')
BOOK_ID = '7628216044850531352'
BOOK_NAME_ENC = '%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AA%E4%B8%96%E4%BF%AE%E4%BB%99'
MANAGE = f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}&{BOOK_NAME_ENC}?type=1'
SESSION = 'fanqie'


def ab(cmd, timeout=60):
    p = subprocess.run(f'agent-browser --session-name {SESSION} --cdp 9223 {cmd}',
                       shell=True, text=True, capture_output=True, timeout=timeout)
    return p.stdout


def js_eval(js, timeout=60):
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
    """统一规范化：去零宽/全角空白、归一换行、去首尾空白。"""
    s = unicodedata.normalize('NFKC', s or '')
    s = re.sub(r'[\u200b-\u200f\ufeff\u00a0]', '', s)
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    s = re.sub(r'[ \t\u3000]+', '', s)
    return s.strip()


def paras(s: str) -> list:
    """按段落边界切分，忽略段落之间的换行数量差异。

    ProseMirror 的 innerText 在每个块级元素后补一个换行（段落间呈 \\n\\n），
    本地纯文本是单换行。逐字相等必须建立在**段落序列**上而非字符流上，
    否则永远判不等。空白是表示差异，正文字符才是硬证。
    """
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


def list_row(ch: int):
    """在当前分卷列表里定位章行。找不到则翻页（最多 12 页）后重试。

    章节管理按发布日期倒序、每页 16 条，目标章常在靠后页；
    平台有时搜索框尚未挂载，只能靠分页遍历。
    """
    target = f'第{ch}章'
    for page in range(12):
        js = f"""(() => {{
 const rows=[...document.querySelectorAll('tr,.arco-table-tr')];
 const r=rows.find(x=>(x.innerText||'').includes({target!r}));
 if(r){{ const c=(r.innerText||'').split('\\n').map(s=>s.trim()).filter(Boolean);
   return {{found:true, text:c, status:c.find(x=>/已发布|修改审核中|审核中|待发布|草稿/.test(x))||''}}; }}
 const pages=[...document.querySelectorAll('.arco-pagination-item, li[class*=pagination-item]')];
 return {{found:false, pageCount:pages.length, pageTexts:pages.map(p=>(p.innerText||'').trim())}};
}})()"""
        r = js_eval(js)
        if isinstance(r, dict) and r.get('found'):
            r['_page'] = page + 1
            return r
        if not isinstance(r, dict) or not r.get('pageCount'):
            break
        nxt = f"""(() => {{
 const pages=[...document.querySelectorAll('.arco-pagination-item, li[class*=pagination-item]')];
 const cur=pages.findIndex(p=>p.className.includes('active'));
 const t=pages[cur+1];
 if(!t) return {{ok:false, atLast:true, cur}};
 t.click(); return {{ok:true, to:{page+2}}};
}})()"""
        n = js_eval(nxt)
        time.sleep(2.2)
        if not isinstance(n, dict) or not n.get('ok'):
            break
    return {'found': False, 'reason': 'not_found_in_volume'}


def open_editor(ch: int) -> bool:
    js = f"""(() => {{
 const rows=[...document.querySelectorAll('tr,.arco-table-tr')];
 const r=rows.find(x=>(x.innerText||'').includes('第{ch}章'));
 if(!r) return {{ok:false, reason:'row_not_found'}};
 const a=r.querySelector('a.link')||[...r.querySelectorAll('a')].find(e=>!(e.innerText||'').trim().startsWith('第'))||r.querySelector('a');
 if(!a) return {{ok:false, reason:'link_not_found'}};
 a.click();
 return {{ok:true}};
}})()"""
    r = js_eval(js)
    time.sleep(3.5)
    return bool(isinstance(r, dict) and r.get('ok'))


def read_editor_body():
    js = """(() => {
 const pm=document.querySelector('.ProseMirror')||document.querySelector('[contenteditable]');
 if(!pm) return {ok:false, reason:'editor_not_found', url:location.href};
 return {ok:true, text: pm.innerText, len: pm.innerText.length};
})()"""
    return js_eval(js)


def close_editor():
    js = """(() => {
 for (const sel of ['button','a','span']) {
   const el=[...document.querySelectorAll(sel)].find(e=>(e.innerText||'').trim()==='取消');
   if(el){el.click();return {ok:true,via:'取消'};}
 }
 return {ok:false};
})()"""
    return js_eval(js)


def infer_volume(ch: int) -> str:
    import re as _re
    outline = CH / '科武纪元大纲 V8_完整版.md'
    text = outline.read_text(encoding='utf-8')
    m = _re.search(rf'第{ch}章\s*\|\s*([^|\n]+?)\s*\|', text)
    if not m:
        raise RuntimeError(f'大纲未找到第{ch}章分卷')
    return m.group(1).strip().replace('·', '：')


def choose_volume(volume: str):
    """切到指定分卷。列表默认停在某卷，跨卷章节翻页也找不到。"""
    js = """(() => {
 const cur=document.querySelector('.byte-select-view-value')?.innerText||'';
 if (cur === %s) return {ok:true, current:cur};
 const sel=document.querySelector('.chapter-select-left .byte-select-view')||document.querySelector('.byte-select-view');
 if(!sel) return {ok:false, reason:'select_not_found'};
 sel.click(); return {ok:true, opened:true, current:cur};
})()""" % repr(volume)
    js_eval(js)
    time.sleep(1.2)
    js2 = """(() => {
 const target=%s;
 if ((document.querySelector('.byte-select-view-value')?.innerText||'') === target) return {ok:true};
 const opt=[...document.querySelectorAll('.byte-select-option')].find(e=>(e.innerText||'').trim()===target);
 if(!opt) return {ok:false, reason:'option_not_found'};
 opt.click(); return {ok:true, clicked:true};
})()""" % repr(volume)
    js_eval(js2)
    time.sleep(2.5)


def main(chs):
    results = []
    for ch in chs:
        print(f"\n{'='*56}\n第{ch}章")
        try:
            vol = infer_volume(ch)
        except Exception as e:
            print(f'  ❌ {e}')
            results.append({'ch': ch, 'ok': False, 'reason': 'volume_unknown'}); continue
        ab(f'open {shlex.quote(MANAGE)}')
        time.sleep(3.5)
        choose_volume(vol)
        row = list_row(ch)
        if not isinstance(row, dict) or not row.get('found'):
            print(f"  ❌ 列表未定位（分卷={vol}）: {row}")
            results.append({'ch': ch, 'ok': False, 'reason': 'row_not_found'}); continue
        print(f"  列表行(第{row.get('_page','?')}页): {row.get('text')}")
        st = row.get('status', '')
        if not open_editor(ch):
            print('  ❌ 未能打开编辑页')
            results.append({'ch':ch,'ok':False,'reason':'open_failed'}); continue
        ed = read_editor_body()
        if not isinstance(ed, dict) or not ed.get('ok'):
            print(f"  ❌ 编辑页读取失败: {ed}")
            results.append({'ch':ch,'ok':False,'reason':'read_failed'}); continue
        close_editor(); time.sleep(1)
        loc = local_body(ch)
        pa, pb = paras(ed.get('text','')), paras(loc)
        same = pa == pb
        cjk_o = len(re.findall(r'[一-鿿]', loc))
        cjk_p = len(re.findall(r'[一-鿿]', ed.get('text','')))
        print(f"  本地 CJK={cjk_o}  页面 CJK={cjk_p}  段落 {len(pb)}→{len(pa)}  逐段相等={same}  平台状态={st}")
        if not same:
            n = max(len(pa), len(pb))
            for i in range(n):
                x = pa[i] if i < len(pa) else '<缺>'
                y = pb[i] if i < len(pb) else '<缺>'
                if x != y:
                    print(f"  首个差异 段#{i+1}")
                    print(f"    页面: {x[:120]}")
                    print(f"    本地: {y[:120]}")
                    break
        results.append({'ch':ch,'ok':same,'cjk_local':cjk_o,'cjk_page':cjk_p,
                        'paras_local':len(pb),'paras_page':len(pa),'status':st})
    print(f"\n{'='*56}")
    ok = sum(1 for r in results if r.get('ok'))
    print(f"验真: {ok}/{len(results)} 章正文逐字一致")
    for r in results:
        print(f"  第{r['ch']}章 {'✅' if r.get('ok') else '❌'} {r.get('cjk_local')}→{r.get('cjk_page')} {r.get('status','')}")
    Path('/tmp/verify_result.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if ok == len(results) else 1


if __name__ == '__main__':
    sys.exit(main([int(x) for x in sys.argv[1:]]))
