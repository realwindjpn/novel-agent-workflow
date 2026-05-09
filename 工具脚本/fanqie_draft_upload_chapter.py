#!/usr/bin/env python3
"""番茄草稿箱上传辅助脚本。

流程：从草稿箱新建草稿 → 选分卷 → 填章号/标题/正文 → 添加图文作者有话说 → 存草稿 → 回草稿箱复核。
默认 dry-run，只做本地解析检查；加 --execute 才操作后台。
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

PROJECT_DIR = Path('/root/workspace/科武纪元')
BOOK_ID = '7628216044850531352'
BOOK_NAME_ENC = '%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99'
DRAFT_URL = f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}&{BOOK_NAME_ENC}?type=2'
DEFAULT_SESSION = 'fanqie'
DEFAULT_VOLUME = '第二卷：烽火'


def run(cmd: str, timeout: int = 60) -> str:
    p = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(f'命令失败({p.returncode}): {cmd}\n{p.stdout}')
    return p.stdout


def ab(session: str, command: str, timeout: int = 60) -> str:
    return run(f"agent-browser --session-name {shlex.quote(session)} {command}", timeout=timeout)


def js_eval(session: str, js: str, timeout: int = 60):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.js', delete=False) as f:
        f.write(js)
        path = f.name
    try:
        out = ab(session, f"eval \"$(cat {shlex.quote(path)})\"", timeout=timeout)
    finally:
        Path(path).unlink(missing_ok=True)
    try:
        return json.loads(out)
    except Exception:
        return out


def parse_chapter(project_dir: Path, chapter: int):
    txt = project_dir / '已投稿' / f'第{chapter}章.txt'
    if not txt.exists():
        raise FileNotFoundError(txt)
    s = txt.read_text(encoding='utf-8-sig')
    first = s.splitlines()[0].strip() if s.splitlines() else ''
    m = re.match(rf'^第{chapter}章\s+(.+)$', first)
    if not m:
        raise ValueError(f'首行标题异常: {first!r}')
    title = m.group(1).strip()
    if '作者有话说：' not in s:
        raise ValueError('缺作者有话说')
    body_part, note_tail = s.split('作者有话说：', 1)
    note = '作者有话说：' + note_tail.strip()
    lines = body_part.strip().splitlines()
    if lines and lines[0].strip().startswith(f'第{chapter}章'):
        body = '\n'.join(lines[1:]).strip()
    else:
        body = body_part.strip()
    if not body.endswith('（本章完）'):
        raise ValueError('正文未以（本章完）结束')
    if '作者有话说' in body:
        raise ValueError('正文仍含作者有话说')
    if len(note) > 300:
        raise ValueError(f'作者有话说超长: {len(note)}')
    return {'chapter': chapter, 'title': title, 'body': body, 'note': note, 'body_len': len(body), 'note_len': len(note)}


def ensure_volume(session: str, volume_name: str):
    js = """
(() => {
 const cur = document.querySelector('.publish-header-volume-name')?.innerText || '';
 return {current: cur};
})()
"""
    cur = js_eval(session, js)
    if isinstance(cur, dict) and cur.get('current') == volume_name:
        return cur
    ab(session, "click '.publish-header-volume-wrap'", timeout=30)
    time.sleep(0.8)
    js2 = f"""
(() => {{
 const target = {volume_name!r};
 const item = Array.from(document.querySelectorAll('.editor-volume-list-item-normal, .editor-volume-list-item'))
   .find(e => (e.innerText||e.textContent||'').trim() === target);
 if (!item) return {{ok:false, reason:'volume_not_found', text:document.body.innerText.slice(0,500)}};
 item.click();
 const ok = Array.from(document.querySelectorAll('button, .byte-btn')).find(e => (e.innerText||e.textContent||'').trim()==='确定' && e.getBoundingClientRect().width>0);
 if (!ok) return {{ok:false, reason:'confirm_not_found'}};
 ok.click();
 return {{ok:true}};
}})()
"""
    res = js_eval(session, js2)
    time.sleep(1)
    chk = js_eval(session, js)
    if not (isinstance(chk, dict) and chk.get('current') == volume_name):
        raise RuntimeError(f'分卷切换失败: {res} / {chk}')
    return chk


def fill_main(session: str, data: dict, volume_name: str):
    js = f"""
(() => {{
 const bodyText = {data['body']!r};
 const setVal=(el,val)=>{{
  const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto,'value').set.call(el,val);
  el.dispatchEvent(new Event('input',{{bubbles:true}}));
  el.dispatchEvent(new Event('change',{{bubbles:true}}));
 }};
 const inputs=Array.from(document.querySelectorAll('input'));
 const num=inputs.find(e=>String(e.className).includes('byte-input')&&!e.placeholder);
 const title=inputs.find(e=>e.placeholder==='请输入标题');
 if (!num || !title) return {{ok:false, reason:'inputs_not_found'}};
 setVal(num,{str(data['chapter'])!r}); setVal(title,{data['title']!r});
 const ed=Array.from(document.querySelectorAll('.ProseMirror')).find(e=>e.getBoundingClientRect().x<1100 && e.getBoundingClientRect().width>500);
 if (!ed) return {{ok:false, reason:'editor_not_found'}};
 ed.innerHTML=''; ed.focus();
 document.execCommand('insertText', false, bodyText);
 ed.dispatchEvent(new InputEvent('input',{{bubbles:true,inputType:'insertText',data:bodyText}}));
 return {{ok:true, vol:document.querySelector('.publish-header-volume-name')?.innerText, num:num.value, title:title.value, hasNote:ed.innerText.includes('作者有话说'), bodyEnd:ed.innerText.slice(-80), len:ed.textContent.length}};
}})()
"""
    res = js_eval(session, js, timeout=90)
    if not isinstance(res, dict) or not res.get('ok') or res.get('vol') != volume_name or res.get('num') != str(data['chapter']) or res.get('title') != data['title'] or res.get('hasNote'):
        raise RuntimeError(f'正文填充校验失败: {res}')
    return res


def add_author_note(session: str, note: str):
    js_open = """
(() => {
 const add=Array.from(document.querySelectorAll('*')).find(e=>(e.innerText||e.textContent||'').trim()==='添加' && e.getBoundingClientRect().x<1000 && e.getBoundingClientRect().y>0);
 if(!add)return {ok:false, reason:'add_not_found'};
 add.click();
 return {ok:true};
})()
"""
    js_eval(session, js_open)
    time.sleep(0.8)
    # React tooltip content is sometimes not rendered as DOM; invoke first option's onClick directly.
    js_choose = """
(() => {
 const root=document.querySelector('#app');
 const key=Object.keys(root).find(k=>k.startsWith('__reactContainer$')||k.startsWith('__reactFiber$'));
 let target=null;
 function walk(n){ if(!n||target)return; const p=n.memoizedProps||{}; if(String(p.className||'')==='author-speak-type-selector-tooltip') target=n; walk(n.child); walk(n.sibling); }
 walk(root[key]);
 if(!target)return {ok:false, reason:'tooltip_not_found'};
 const items=target.memoizedProps.content.props.children;
 items[0].props.onClick({preventDefault(){},stopPropagation(){}});
 return {ok:true};
})()
"""
    res_choose = js_eval(session, js_choose)
    if not isinstance(res_choose, dict) or not res_choose.get('ok'):
        raise RuntimeError(f'添加图文失败: {res_choose}')
    time.sleep(0.8)
    js_note = f"""
(() => {{
 const note={note!r};
 const ed=Array.from(document.querySelectorAll('.tiptap.ProseMirror')).find(e=>e.getBoundingClientRect().y>0) || document.querySelector('.tiptap.ProseMirror');
 if(!ed)return {{ok:false, reason:'note_editor_not_found'}};
 ed.innerHTML=''; ed.focus();
 document.execCommand('insertText', false, note);
 ed.dispatchEvent(new InputEvent('input',{{bubbles:true,inputType:'insertText',data:note}}));
 return {{ok:true,text:ed.innerText,len:ed.innerText.length}};
}})()
"""
    res_note = js_eval(session, js_note)
    if not isinstance(res_note, dict) or res_note.get('text','').strip() != note:
        raise RuntimeError(f'作者有话说填充失败: {res_note}')
    js_save = """
(() => {
 const btn=Array.from(document.querySelectorAll('*')).find(e => (e.innerText||e.textContent||'').trim()==='保存' && e.getBoundingClientRect().width>0 && e.getBoundingClientRect().x<1000);
 if(!btn)return {ok:false, reason:'save_not_found'};
 btn.click(); return {ok:true, text:btn.innerText};
})()
"""
    res_save = js_eval(session, js_save)
    time.sleep(1.5)
    js_check = f"""
(() => {{
 const txt=document.body.innerText;
 const body=Array.from(document.querySelectorAll('.ProseMirror')).find(e=>e.textContent.includes('（本章完）'));
 return {{hasNote:txt.includes({note!r}), moduleControls:txt.includes('编辑删除'), bodyHasNote:body?.innerText.includes('作者有话说'), word:(txt.match(/正文字数\n(\d+)/)||[])[1]}};
}})()
"""
    chk = js_eval(session, js_check)
    if not isinstance(chk, dict) or not chk.get('hasNote') or not chk.get('moduleControls') or chk.get('bodyHasNote'):
        raise RuntimeError(f'作者有话说保存后校验失败: {res_save} / {chk}')
    return chk


def save_and_verify(session: str, data: dict):
    ab(session, "click 'button.auto-editor-save-btn'", timeout=30)
    time.sleep(3)
    js = """
(() => ({url:location.href, saved:document.body.innerText.includes('已保存到云端')||document.body.innerText.includes('已保存'), word:(document.body.innerText.match(/正文字数\n(\d+)/)||[])[1], vol:document.querySelector('.publish-header-volume-name')?.innerText, title:Array.from(document.querySelectorAll('input')).find(e=>e.placeholder==='请输入标题')?.value, num:Array.from(document.querySelectorAll('input')).find(e=>String(e.className).includes('byte-input')&&!e.placeholder)?.value}))()
"""
    saved = js_eval(session, js)
    if not isinstance(saved, dict) or not saved.get('saved') or saved.get('num') != str(data['chapter']):
        raise RuntimeError(f'顶部存草稿失败: {saved}')
    ab(session, f"open {shlex.quote(DRAFT_URL)}", timeout=60)
    time.sleep(2)
    js2 = f"""
(() => {{
 const rows=[];
 const cells=Array.from(document.querySelectorAll('[role=cell], td, .byte-table-cell')).map(e=>(e.innerText||e.textContent||'').trim()).filter(Boolean);
 const txt=document.body.innerText;
 return {{ok:txt.includes('第{data['chapter']}章 {data['title']}'), listText:txt.slice(txt.indexOf('名称'), txt.indexOf('© 2026'))}};
}})()
"""
    listing = js_eval(session, js2)
    if not isinstance(listing, dict) or not listing.get('ok'):
        raise RuntimeError(f'草稿箱复核失败: {listing}')
    return {'saved': saved, 'listing': listing}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapter', type=int, required=True)
    ap.add_argument('--project-dir', type=Path, default=PROJECT_DIR)
    ap.add_argument('--session', default=DEFAULT_SESSION)
    ap.add_argument('--volume', default=DEFAULT_VOLUME)
    ap.add_argument('--execute', action='store_true', help='实际操作番茄后台；默认只解析检查')
    args = ap.parse_args()

    data = parse_chapter(args.project_dir, args.chapter)
    print(json.dumps({k: v for k, v in data.items() if k not in ('body','note')} | {'note': data['note']}, ensure_ascii=False, indent=2))
    if not args.execute:
        print('DRY_RUN_OK')
        return

    ab(args.session, f"open {shlex.quote(DRAFT_URL)}", timeout=60)
    time.sleep(2)
    ab(args.session, "click 'button:has-text(\"新建草稿\")'", timeout=30)
    time.sleep(3)
    ensure_volume(args.session, args.volume)
    fill = fill_main(args.session, data, args.volume)
    note = add_author_note(args.session, data['note'])
    final = save_and_verify(args.session, data)
    print(json.dumps({'fill': fill, 'note': note, 'final': final}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
