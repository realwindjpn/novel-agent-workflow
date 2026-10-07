#!/usr/bin/env python3
"""番茄已发布章节正文替换脚本。

输入本地 `已投稿/第N章.txt`，移除首行章号标题，只替换正文编辑器内容。
提交时 AI 使用固定选“是”。若出现发布/上传字数限制等阻塞提示，停止并返回错误，不继续硬点。
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import tempfile
import time
from pathlib import Path
import sys as _s; _s.path.insert(0, str(Path(__file__).parent) if 'Path' in dir() else __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from outline_canon import outline_path as _canon_path

PROJECT_DIR = Path('/root/workspace/科武纪元')
BOOK_ID = '7628216044850531352'
BOOK_NAME_ENC = '%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99'
MANAGE_URL = f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}&{BOOK_NAME_ENC}?type=1'
DRAFT_URL = f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}&{BOOK_NAME_ENC}?type=2'
DEFAULT_SESSION = 'fanqie'


def run(cmd: str, timeout: int = 60) -> str:
    p = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(f'命令失败({p.returncode}): {cmd}\n{p.stdout}')
    return p.stdout


def ab(session: str, command: str, timeout: int = 60) -> str:
    return run(f"agent-browser --session-name {shlex.quote(session)} --cdp 9223 {command}", timeout=timeout)


def js_eval(session: str, js: str, timeout: int = 60):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.js', delete=False) as f:
        f.write(js)
        p = Path(f.name)
    try:
        out = ab(session, f"eval \"$(cat {shlex.quote(str(p))})\"", timeout=timeout)
    finally:
        p.unlink(missing_ok=True)
    try:
        return json.loads(out)
    except Exception:
        return out


def parse_txt(project_dir: Path, chapter: int):
    p = project_dir / '已投稿' / f'第{chapter}章.txt'
    s = p.read_text(encoding='utf-8-sig')
    lines = s.strip().splitlines()
    first = lines[0].strip() if lines else ''
    m = re.match(rf'^第{chapter}章\s+(.+)$', first)
    if not m:
        raise ValueError(f'首行标题异常: {first}')
    title = m.group(1).strip()
    body = '\n'.join(lines[1:]).strip()
    if '作者有话说：' in body:
        body = body.split('作者有话说：', 1)[0].strip()
    if not body.endswith('（本章完）'):
        raise ValueError('正文未以（本章完）结束')
    if body.startswith(f'第{chapter}章'):
        raise ValueError('正文仍含章号标题')
    return {'chapter': chapter, 'title': title, 'body': body, 'body_len': len(body)}


def infer_volume(project_dir: Path, chapter: int) -> str:
    outline = _canon_path()
    text = outline.read_text(encoding='utf-8')
    pattern = rf'第{chapter}章\s*\|\s*([^|\n]+?)\s*\|'
    m = re.search(pattern, text)
    if not m:
        raise ValueError(f'大纲未找到第{chapter}章分卷')
    volume = m.group(1).strip().replace('·', '：')
    if not volume:
        raise ValueError(f'第{chapter}章分卷为空')
    return volume


def choose_volume(session: str, volume: str):
    ab(session, f"open {shlex.quote(MANAGE_URL)}", timeout=60)
    time.sleep(2)
    js = f"""
(() => {{
 const cur=document.querySelector('.byte-select-view-value')?.innerText || '';
 if (cur === {volume!r}) return {{ok:true, current:cur}};
 const sel=document.querySelector('.chapter-select-left .byte-select-view') || document.querySelector('.byte-select-view');
 if(!sel) return {{ok:false, reason:'select_not_found'}};
 sel.click();
 return {{ok:true, opened:true, current:cur}};
}})()
"""
    r = js_eval(session, js)
    time.sleep(0.8)
    js2 = f"""
(() => {{
 const target={volume!r};
 if ((document.querySelector('.byte-select-view-value')?.innerText||'') === target) return {{ok:true, current:target}};
 const opt=Array.from(document.querySelectorAll('.byte-select-option')).find(e=>(e.innerText||e.textContent||'').trim()===target);
 if(!opt) return {{ok:false, reason:'option_not_found', text:document.body.innerText.slice(-200)}};
 opt.click();
 return {{ok:true, clicked:true}};
}})()
"""
    r2 = js_eval(session, js2)
    time.sleep(2)
    chk = js_eval(session, "(() => ({current:document.querySelector('.byte-select-view-value')?.innerText||'', text:document.body.innerText.slice(0,300)}))()")
    if not isinstance(chk, dict) or chk.get('current') != volume:
        raise RuntimeError(f'分卷切换失败: {r} / {r2} / {chk}')


def search_and_open(session: str, data: dict):
    # 平台线上标题可能与本地标题略不同；旧章定位以章号为准，避免“第39章 南海对峙/南部海域对峙”这类标题差异导致找不到。
    target = f"第{data['chapter']}章"
    js = f"""
(() => {{
 const input=Array.from(document.querySelectorAll('input')).find(e=>e.placeholder==='搜索章节');
 if(input) {{
   Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input, {('第'+str(data['chapter'])+'章')!r});
   input.dispatchEvent(new Event('input',{{bubbles:true}}));
   input.dispatchEvent(new KeyboardEvent('keydown',{{bubbles:true,key:'Enter',code:'Enter',keyCode:13}}));
 }}
 return {{ok:true, hasInput:!!input}};
}})()
"""
    js_eval(session, js)
    time.sleep(2)
    # If search failed, try all pagination pages.
    for _ in range(5):
        js_find = f"""
(() => {{
 const target={target!r};
 const rows=Array.from(document.querySelectorAll('tr,.arco-table-tr'));
 const row=rows.find(r=>(r.innerText||'').includes(target));
 if(row) {{
   const a=row.querySelector('a.link') || Array.from(row.querySelectorAll('a')).find(e=>!(e.innerText||'').trim().startsWith('第')) || row.querySelector('a');
   if(!a) return {{ok:false, reason:'edit_link_not_found', row:row.innerText}};
   a.click();
   return {{ok:true, opened:true, row:row.innerText}};
 }}
 const pages=Array.from(document.querySelectorAll('.arco-pagination-item')).filter(e=>/^\d+$/.test((e.innerText||'').trim()));
 const active=pages.findIndex(e=>String(e.className).includes('active'));
 const next=pages[active+1];
 if(next) {{ next.click(); return {{ok:false, advanced:true, page:next.innerText}}; }}
 return {{ok:false, reason:'row_not_found', text:document.body.innerText.slice(document.body.innerText.indexOf('章节名称'), document.body.innerText.indexOf('章节名称')+600)}};
}})()
"""
        r = js_eval(session, js_find)
        if isinstance(r, dict) and r.get('opened'):
            time.sleep(3)
            return r
        time.sleep(2)
    raise RuntimeError(f'找不到章节: {target}')


def replace_body(session: str, data: dict):
    js = f"""
(() => {{
 const body={data['body']!r};
 const num=Array.from(document.querySelectorAll('input')).find(e=>String(e.className).includes('byte-input')&&!e.placeholder)?.value;
 const title=Array.from(document.querySelectorAll('input')).find(e=>e.placeholder==='请输入标题')?.value;
 const ed=Array.from(document.querySelectorAll('.ProseMirror')).find(e=>e.getBoundingClientRect().x<1100 && e.getBoundingClientRect().width>500);
 if(!ed) return {{ok:false, reason:'editor_not_found'}};
 ed.innerHTML=''; ed.focus();
 document.execCommand('insertText', false, body);
 ed.dispatchEvent(new InputEvent('input',{{bubbles:true,inputType:'insertText',data:body}}));
 return {{ok:true,num,title,start:ed.innerText.slice(0,40),end:ed.innerText.slice(-80),hasTitle:ed.innerText.startsWith('第{data['chapter']}章'), hasNote:ed.innerText.includes('作者有话说')}};
}})()
"""
    r = js_eval(session, js, timeout=90)
    if not isinstance(r, dict) or not r.get('ok') or r.get('num') != str(data['chapter']) or r.get('hasTitle') or r.get('hasNote'):
        raise RuntimeError(f'替换正文校验失败: {r}')
    return r


def submit(session: str, data: dict):
    # 先处理夜间审核提示/继续编辑等浮层，再点下一步。
    js_eval(session, """
(() => {
  const labels=['我知道了','继续编辑'];
  const btn=Array.from(document.querySelectorAll('button')).find(b=>labels.includes((b.innerText||'').trim()) && b.getBoundingClientRect().width>0);
  if(btn) btn.click();
  return {dismissed:!!btn, text:btn?.innerText||''};
})()
""")
    time.sleep(0.8)
    next_result = js_eval(session, """
(() => {
  const btn=document.querySelector('button.auto-editor-next') || Array.from(document.querySelectorAll('button')).find(b=>(b.innerText||'').trim()==='下一步' && b.getBoundingClientRect().width>0);
  if(!btn) return {ok:false,reason:'next_not_found'};
  if(btn.disabled) return {ok:false,reason:'next_disabled'};
  btn.click(); return {ok:true};
})()
""")
    if not isinstance(next_result, dict) or not next_result.get('ok'):
        raise RuntimeError(f'下一步点击失败: {next_result}')
    time.sleep(2)
    txt = js_eval(session, "(() => document.body.innerText)()")
    if isinstance(txt, str) and ('超过上传发布字数限制' in txt or '超过' in txt and '字数限制' in txt):
        raise RuntimeError('出现字数/上传发布限制，已停止提交')
    # 可能先出现错别字确认框，点提交
    js_submit = """
(() => {
 const btn=Array.from(document.querySelectorAll('button')).find(b=>['提交','确认发布'].includes(b.innerText.trim()) && b.getBoundingClientRect().width>0);
 if(!btn)return {ok:false, reason:'submit_or_confirm_not_found', text:document.body.innerText.slice(0,500)};
 btn.click(); return {ok:true, text:btn.innerText.trim()};
})()
"""
    r1 = js_eval(session, js_submit)
    time.sleep(2)
    txt2 = js_eval(session, "(() => document.body.innerText)()")
    if isinstance(txt2, str) and ('超过上传发布字数限制' in txt2 or ('超过' in txt2 and '字数限制' in txt2)):
        raise RuntimeError('出现字数/上传发布限制，已停止提交')
    # 发布设置：AI 使用选 是
    js_ai_yes = """
(() => {
 const yes=Array.from(document.querySelectorAll('label,.arco-radio')).find(e=>(e.innerText||e.textContent||'').trim()==='是' && e.getBoundingClientRect().x<1000);
 if(yes) yes.click();
 const btn=Array.from(document.querySelectorAll('button')).find(b=>b.innerText.trim()==='确认发布' && b.getBoundingClientRect().width>0);
 if(!btn)return {ok:false, reason:'confirm_not_found', text:document.body.innerText.slice(0,500)};
 btn.click(); return {ok:true};
})()
"""
    r2 = js_eval(session, js_ai_yes)
    time.sleep(3)
    txt3 = js_eval(session, "(() => document.body.innerText)()")
    if isinstance(txt3, str) and ('超过上传发布字数限制' in txt3 or ('超过' in txt3 and '字数限制' in txt3)):
        raise RuntimeError('出现字数/上传发布限制，提交未完成')
    return {'step1': r1, 'step2': r2}


def verify(session: str, data: dict, volume: str):
    choose_volume(session, volume)
    target=f"第{data['chapter']}章"
    for _ in range(5):
        js = f"""
(() => {{
 const row=Array.from(document.querySelectorAll('tr,.arco-table-tr')).find(r=>(r.innerText||'').includes({target!r}));
 if(row) return {{found:true,row:row.innerText}};
 const pages=Array.from(document.querySelectorAll('.arco-pagination-item')).filter(e=>/^\d+$/.test((e.innerText||'').trim()));
 const active=pages.findIndex(e=>String(e.className).includes('active'));
 const next=pages[active+1];
 if(next) {{next.click(); return {{found:false, advanced:true}};}}
 return {{found:false, text:document.body.innerText.slice(0,300)}};
}})()
"""
        r=js_eval(session, js)
        if isinstance(r, dict) and r.get('found'):
            return r
        time.sleep(2)
    raise RuntimeError('提交后列表复核失败')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--chapter', type=int, required=True)
    ap.add_argument('--project-dir', type=Path, default=PROJECT_DIR)
    ap.add_argument('--session', default=DEFAULT_SESSION)
    ap.add_argument('--volume', default=None, help='覆盖大纲自动推断分卷；默认按大纲第N章行解析')
    ap.add_argument('--area', type=int, default=1, choices=[1, 2],
                    help='1=已发布章节（type=1，默认）；2=草稿箱（type=2）。'
                         '2026-09-25：351 只在草稿箱未发布，需 --area 2 才能定位到。')
    ap.add_argument('--skip-volume', action='store_true',
                    help='跳过分卷切换（草稿箱列表无分卷筛选器时必须跳过）')
    ap.add_argument('--execute', action='store_true')
    args=ap.parse_args()
    data=parse_txt(args.project_dir,args.chapter)
    volume = args.volume or infer_volume(args.project_dir, args.chapter)
    print(json.dumps({**{k:v for k,v in data.items() if k!='body'}, 'volume': volume,
                      'area': args.area}, ensure_ascii=False, indent=2))
    if not args.execute:
        print('DRY_RUN_OK')
        return
    if args.area == 2:
        # 导航到草稿箱列表
        ab(args.session, f'navigate {shlex.quote(DRAFT_URL)}', timeout=90)
        time.sleep(6)
    if args.area == 1 or not args.skip_volume:
        choose_volume(args.session,volume)
    opened=search_and_open(args.session,data)
    replaced=replace_body(args.session,data)
    submitted=submit(args.session,data)
    verified=verify(args.session,data,volume)
    print(json.dumps({'opened':opened,'replaced':replaced,'submitted':submitted,'verified':verified},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
