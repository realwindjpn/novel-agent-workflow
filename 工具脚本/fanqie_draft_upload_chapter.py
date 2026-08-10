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
READY_GATE = PROJECT_DIR / '工具脚本' / 'ensure_fanqie_upload_txt_ready.py'
BOOK_ID = '7628216044850531352'
BOOK_NAME_ENC = '%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99'
DRAFT_URL = f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}&{BOOK_NAME_ENC}?type=2'
DEFAULT_SESSION = 'fanqie'
DEFAULT_VOLUME = None
DEFAULT_STATE = Path('/root/workspace/browser_profiles/fanqie/fanqie_state.json')


def run(cmd: str, timeout: int = 60) -> str:
    p = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    out = p.stdout
    # agent-browser 若 daemon 已运行，会把“--state ignored”警告写入 stdout，污染 get url / eval JSON。
    # 该警告不代表当前会话未登录；运行中会话应以实际页面状态为准。
    out = '\n'.join(line for line in out.splitlines() if not line.startswith('⚠ --state ignored:'))
    if p.returncode != 0:
        raise RuntimeError(f'命令失败({p.returncode}): {cmd}\n{out}')
    return out


def ab(session: str, command: str, timeout: int = 60, state_path: Path | None = None) -> str:
    # --state 只在冷启动时有用；daemon 已运行时会被忽略，还会污染 stdout。
    # 因此默认复用当前 fanqie 会话；需要从 state 冷启动时先在外部 close --all。
    state = f"--state {shlex.quote(str(state_path))} " if state_path and state_path.exists() and command.startswith('open ') else ''
    return run(f"agent-browser --session-name {shlex.quote(session)} {state}{command}", timeout=timeout)


def save_state(session: str, state_path: Path) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    run(f"agent-browser --session-name {shlex.quote(session)} state save {shlex.quote(str(state_path))}", timeout=30)


def backend_ok(session: str, state_path: Path | None = None) -> dict:
    ab(session, "open 'https://fanqienovel.com/main/writer/home'", timeout=60, state_path=state_path)
    time.sleep(2)
    url = ab(session, 'get url', timeout=30, state_path=state_path).strip()
    text = ab(session, 'snapshot -i', timeout=60, state_path=state_path)
    ok = ('/main/writer/login' not in url) and any(k in text for k in ['作品管理', '章节管理', '科武纪元', '工作台'])
    return {'ok': ok, 'url': url, 'text': text[:500]}


def js_eval(session: str, js: str, timeout: int = 60, state_path: Path | None = None):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.js', delete=False) as f:
        f.write(js)
        path = f.name
    try:
        out = ab(session, f"eval \"$(cat {shlex.quote(path)})\"", timeout=timeout, state_path=state_path)
    finally:
        Path(path).unlink(missing_ok=True)
    try:
        value = json.loads(out)
        # agent-browser 某些版本会把 eval 的 JSON 再包一层字符串。
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                pass
        return value
    except Exception:
        return out


def infer_volume(project_dir: Path, chapter: int) -> str:
    outline = project_dir / '科武纪元大纲 V8_完整版.md'
    if not outline.exists():
        raise FileNotFoundError(outline)
    text = outline.read_text(encoding='utf-8')
    volumes = []
    for line in text.splitlines():
        # 大纲可能带有 rg/nl 风格的行号前缀：`266|第169章 | 第四卷·登月 | ...`
        row = re.sub(r'^\s*\d+\|', '', line).strip()
        if not re.match(rf'^第{chapter}章\s*\|', row):
            continue
        parts = [part.strip() for part in row.split('|')]
        if len(parts) < 2:
            continue
        volume = parts[1].replace('·', '：')
        if volume:
            volumes.append(volume)
    volumes = list(dict.fromkeys(volumes))
    if not volumes:
        raise ValueError(f'大纲未找到第{chapter}章分卷')
    if len(volumes) > 1:
        raise ValueError(f'大纲第{chapter}章分卷不唯一: {volumes}')
    return volumes[0]


def resolve_volume(project_dir: Path, chapter: int, explicit_volume: str | None) -> str:
    """以大纲卷属为硬真源；显式参数仅可复述，不得覆盖。"""
    inferred = infer_volume(project_dir, chapter)
    explicit = (explicit_volume or '').strip().replace('·', '：')
    if explicit and explicit != inferred:
        raise ValueError(
            f'分卷硬闸失败：第{chapter}章大纲卷属={inferred}，'
            f'显式参数={explicit}；拒绝上传'
        )
    return inferred


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
    # 番茄后台“作者有话说”模块自带标题，输入框只填内容；
    # 若带“作者有话说：”前缀，会在读者端显示成重复标题，且有脚本痕迹。
    note = note_tail.strip()
    note = re.sub(r'^(作者有话说[:：]\s*)+', '', note).strip()
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


def ensure_volume(session: str, volume_name: str, state_path: Path | None = None):
    js = """
(() => {
 const explicit = (document.querySelector('.publish-header-volume-name')?.innerText || '').trim();
 const maintain = document.querySelector('.publish-maintain-volume')?.innerText || '';
 const wrap = document.querySelector('.publish-header-volume-wrap')?.innerText || '';
 const m = (maintain + '\\n' + wrap).match(/第[一二三四五六七八九十]+卷[：:][^\\n]*/);
 let current = explicit || (m ? m[0].replace(/:/g, '：').trim() : '');
 // 新建草稿页首屏偶发 class 已在但 innerText 空；用 body 兜底
 if (!current) {
   const body = document.body?.innerText || '';
   const m2 = body.match(/第[一二三四五六七八九十]+卷[：:][^\\n]{0,20}/);
   if (m2) current = m2[0].replace(/:/g, '：').trim();
 }
 return {current, explicit, maintain, wrap};
})()
"""
    # 新建草稿后 SPA 未就绪时 class/文案皆空；先轮询再点选
    cur = None
    for _ in range(8):
        cur = js_eval(session, js, state_path=state_path)
        if isinstance(cur, dict) and cur.get('current') == volume_name:
            return cur
        if isinstance(cur, dict) and (cur.get('current') or cur.get('explicit') or cur.get('maintain') or cur.get('wrap')):
            break
        time.sleep(0.6)
    if isinstance(cur, dict) and cur.get('current') == volume_name:
        return cur
    clicked = False
    for selector in ['.publish-header-volume-wrap', '.publish-maintain-volume', '.publish-maintain']:
        try:
            ab(session, f"click '{selector}'", timeout=30, state_path=state_path)
            clicked = True
            break
        except Exception:
            continue
    if not clicked:
        # 番茄发布页偶尔改版，header 只显示文本无旧class；若页面文本已在目标卷，直接继续。
        for _ in range(5):
            cur = js_eval(session, js, state_path=state_path)
            if isinstance(cur, dict) and cur.get('current') == volume_name:
                return cur
            time.sleep(0.5)
        raise RuntimeError(f'分卷入口未找到: {cur}')
    time.sleep(0.8)
    js2 = f"""
(() => {{
 const target = {volume_name!r};
 const fiberKey = (el) => el && Object.keys(el).find(k => k.startsWith('__reactFiber$'));
 const fireFiberClick = (el) => {{
   for (let node = el; node; node = node.parentElement) {{
     const key = fiberKey(node);
     if (!key) continue;
     let f = node[key];
     for (let i=0; i<12 && f; i++, f=f.return) {{
       const p = f.memoizedProps;
       if (p && typeof p.onClick === 'function') {{
         p.onClick({{preventDefault(){{}}, stopPropagation(){{}}, target:node, currentTarget:node}});
         return true;
       }}
     }}
   }}
   return false;
 }};
 const item = Array.from(document.querySelectorAll('span, .editor-volume-list-item, .editor-volume-list-item-normal'))
   .find(e => (e.innerText||e.textContent||'').trim() === target && Object.keys(e).some(k => k.startsWith('__reactProps$') && typeof e[k].onClick === 'function'));
 if (!item) return {{ok:false, reason:'volume_not_found', text:document.body.innerText.slice(0,500)}};
 const before = Array.from(document.querySelectorAll('.editor-volume-list-item-normal.selected')).map(e=>(e.innerText||'').trim());
 const propsKey = Object.keys(item).find(k=>k.startsWith('__reactProps$'));
 if (propsKey && typeof item[propsKey].onClick === 'function') item[propsKey].onClick();
 else {{ item.click(); fireFiberClick(item); }}
 const after = Array.from(document.querySelectorAll('.editor-volume-list-item-normal.selected')).map(e=>(e.innerText||'').trim());
 const ok = Array.from(document.querySelectorAll('button, .byte-btn'))
   .find(e => (e.innerText||e.textContent||'').trim()==='确定');
 if (!ok) return {{ok:false, reason:'confirm_not_found', before, after}};
 const okProps = Object.keys(ok).find(k=>k.startsWith('__reactProps$'));
 if (okProps && typeof ok[okProps].onClick === 'function') ok[okProps].onClick();
 else {{ ok.click(); fireFiberClick(ok); }}
 return {{ok:true, before, after}};
}})()
"""
    # React 受控弹窗在自动化里偶发 header 不立刻刷新；若弹窗 selected 已变为目标卷，则继续后续填充，fill_main 会再次校验 vol。
    res = None
    chk = None
    for attempt in range(3):
        res = js_eval(session, js2, state_path=state_path)
        time.sleep(1)
        chk = js_eval(session, js, state_path=state_path)
        if isinstance(chk, dict) and chk.get('current') == volume_name:
            return chk
        if isinstance(res, dict) and volume_name in res.get('after', []):
            return {'current': volume_name, 'selected_only': True, 'raw_header': chk}
    raise RuntimeError(f'分卷切换失败: {res} / {chk}')


def fill_main(session: str, data: dict, volume_name: str, state_path: Path | None = None):
    # 2026-05-10 修正：正文只吃已投稿TXT拆出的纯正文，不从MD/富文本粘贴。
    # ProseMirror 用逐段 <p> 写入，避免 execCommand('insertText') 把换行解析成多余空段或吞段落。
    # 注意：粘贴前须由 parse_chapter() 从 已投稿TXT 拆出正文/作者有话说；草稿页正文框绝不直接吃 MD。
    js = f"""
(() => {{
 const bodyText = {data['body']!r};
 const setVal=(el,val)=>{{
  const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto,'value').set.call(el,val);
  el.dispatchEvent(new Event('input',{{bubbles:true}}));
  el.dispatchEvent(new Event('change',{{bubbles:true}}));
 }};
 const esc=(s)=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
 const toHtml=(txt)=>txt.split(/\\n+/).map(x=>x.trim()).filter(Boolean).map(x=>`<p>${{esc(x)}}</p>`).join('');
 const inputs=Array.from(document.querySelectorAll('input'));
 const num=inputs.find(e=>String(e.className).includes('byte-input')&&!e.placeholder);
 const title=inputs.find(e=>e.placeholder==='请输入标题');
 if (!num || !title) return {{ok:false, reason:'inputs_not_found'}};
 setVal(num,{str(data['chapter'])!r}); setVal(title,{data['title']!r});
 const ed=Array.from(document.querySelectorAll('.ProseMirror')).find(e=>e.getBoundingClientRect().x<1100 && e.getBoundingClientRect().width>500);
 if (!ed) return {{ok:false, reason:'editor_not_found'}};
 ed.focus(); ed.innerHTML=toHtml(bodyText);
 ed.dispatchEvent(new InputEvent('input',{{bubbles:true,inputType:'insertText',data:bodyText}}));
 ed.dispatchEvent(new Event('change',{{bubbles:true}}));
 const rendered=ed.innerText;
 return {{ok:true, vol:document.querySelector('.publish-header-volume-name')?.innerText, num:num.value, title:title.value, hasNote:rendered.includes('作者有话说'), bodyEnd:rendered.slice(-80), len:ed.textContent.length, blankRun:/\\n{{3,}}/.test(rendered)}};
}})()
"""
    res = js_eval(session, js, timeout=90, state_path=state_path)
    if not isinstance(res, dict) or not res.get('ok') or res.get('vol') != volume_name or res.get('num') != str(data['chapter']) or res.get('title') != data['title'] or res.get('hasNote') or res.get('blankRun'):
        raise RuntimeError(f'正文填充校验失败: {res}')
    return res


def add_author_note(session: str, note: str, state_path: Path | None = None):
    js_open = """
(() => {
 const add=Array.from(document.querySelectorAll('*')).find(e=>(e.innerText||e.textContent||'').trim()==='添加' && e.getBoundingClientRect().x<1000 && e.getBoundingClientRect().y>0);
 if(!add)return {ok:false, reason:'add_not_found'};
 add.click();
 return {ok:true};
})()
"""
    js_eval(session, js_open, state_path=state_path)
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
    res_choose = js_eval(session, js_choose, state_path=state_path)
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
    res_note = js_eval(session, js_note, state_path=state_path)
    if not isinstance(res_note, dict) or res_note.get('text','').strip() != note:
        raise RuntimeError(f'作者有话说填充失败: {res_note}')
    js_save = """
(() => {
 const btn=Array.from(document.querySelectorAll('*')).find(e => (e.innerText||e.textContent||'').trim()==='保存' && e.getBoundingClientRect().width>0 && e.getBoundingClientRect().x<1000);
 if(!btn)return {ok:false, reason:'save_not_found'};
 btn.click(); return {ok:true, text:btn.innerText};
})()
"""
    res_save = js_eval(session, js_save, state_path=state_path)
    time.sleep(1.5)
    js_check = f"""
(() => {{
 const txt=document.body.innerText;
 const body=Array.from(document.querySelectorAll('.ProseMirror')).find(e=>e.textContent.includes('（本章完）'));
 const m=txt.match(new RegExp('正文字数\\\\s*([0-9]+)'));
 return {{hasNote:txt.includes({note!r}), moduleControls:txt.includes('编辑删除'), bodyHasNote:body?.innerText.includes('作者有话说'), word:m?m[1]:null}};
}})()
"""
    chk = js_eval(session, js_check, state_path=state_path)
    if not isinstance(chk, dict) or not chk.get('hasNote') or not chk.get('moduleControls') or chk.get('bodyHasNote'):
        raise RuntimeError(f'作者有话说保存后校验失败: {res_save} / {chk}')
    return chk


def draft_listing_scan(session: str, chapter: int, title: str, state_path: Path | None = None) -> dict:
    """打开草稿箱，统计同名「第N章 标题」出现次数。用于防重复新建。"""
    ab(session, f"open {shlex.quote(DRAFT_URL)}", timeout=60, state_path=state_path)
    time.sleep(2)
    needle = f'第{chapter}章 {title}'
    js = f"""
(() => {{
 const needle={needle!r};
 const txt=document.body.innerText || '';
 let count=0, from=0;
 while(true){{
   const i=txt.indexOf(needle, from);
   if(i<0) break;
   count += 1;
   from = i + needle.length;
 }}
 const start=txt.indexOf('名称');
 const end=txt.indexOf('© 2026');
 const listText=(start>=0 && end>start) ? txt.slice(start, end) : txt.slice(0, 1200);
 return {{ok:true, needle, count, listText}};
}})()
"""
    res = js_eval(session, js, state_path=state_path)
    if not isinstance(res, dict) or not res.get('ok'):
        raise RuntimeError(f'草稿箱扫描失败: {res}')
    return res


def save_and_verify(session: str, data: dict, volume_name: str, state_path: Path | None = None):
    ab(session, "click 'button.auto-editor-save-btn'", timeout=30, state_path=state_path)
    time.sleep(3)
    js = """
(() => { const txt=document.body.innerText; const m=txt.match(new RegExp('正文字数\\\\s*([0-9]+)')); return {url:location.href, saved:txt.includes('已保存到云端')||txt.includes('已保存'), word:m?m[1]:null, vol:document.querySelector('.publish-header-volume-name')?.innerText, title:Array.from(document.querySelectorAll('input')).find(e=>e.placeholder==='请输入标题')?.value, num:Array.from(document.querySelectorAll('input')).find(e=>String(e.className).includes('byte-input')&&!e.placeholder)?.value}; })()
"""
    saved = js_eval(session, js, state_path=state_path)
    # 番茄有时点“存草稿”后不立即刷新“已保存到云端”文案，但草稿 URL、章号、标题、字数已落页。
    # 以草稿箱列表复核作为最终证据，不在此处因 saved 文案滞后中断。
    if (
        not isinstance(saved, dict)
        or saved.get('num') != str(data['chapter'])
        or saved.get('title') != data['title']
        or saved.get('vol') != volume_name
    ):
        raise RuntimeError(f'顶部存草稿失败: {saved}')
    listing = draft_listing_scan(session, data['chapter'], data['title'], state_path=state_path)
    if not listing.get('count'):
        raise RuntimeError(f'草稿箱复核失败(未命中): {listing}')
    listing = {
        'ok': True,
        'listText': listing.get('listText'),
        'count': listing.get('count'),
        'needle': listing.get('needle'),
        'duplicate': int(listing.get('count') or 0) > 1,
    }
    return {'saved': saved, 'listing': listing}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapter', type=int, required=True)
    ap.add_argument('--project-dir', type=Path, default=PROJECT_DIR)
    ap.add_argument('--session', default=DEFAULT_SESSION)
    ap.add_argument('--volume', default=DEFAULT_VOLUME, help='目标分卷；默认按大纲第N章行推断')
    ap.add_argument('--state', type=Path, default=DEFAULT_STATE, help='持久化 auth state JSON；默认 /root/workspace/browser_profiles/fanqie/fanqie_state.json')
    ap.add_argument('--check-login', action='store_true', help='只验证作家后台登录态；成功后保存state')
    ap.add_argument('--execute', action='store_true', help='实际操作番茄后台；默认只解析检查')
    ap.add_argument(
        '--force-new',
        action='store_true',
        help='即使草稿箱已有同名「第N章 标题」也强制再点「新建草稿」。默认拒绝，防双草稿。',
    )
    ap.add_argument(
        '--allow-duplicate-listing',
        action='store_true',
        help='保存后若 listing 同名>1 仍视为成功（仅告警）。默认 duplicate 时返回码非0，提示人工清理。',
    )
    args = ap.parse_args()

    # 分卷必须先过大纲硬闸。即使TXT门禁未齐，也先暴露错误卷属，
    # 避免调用方用旧的 --volume 参数绕过权威大纲。
    volume = resolve_volume(args.project_dir, args.chapter, args.volume)

    if args.check_login:
        ok = backend_ok(args.session, args.state)
        if ok.get('ok'):
            save_state(args.session, args.state)
        print(json.dumps(ok | {'state': str(args.state)}, ensure_ascii=False, indent=2))
        return

    if READY_GATE.exists() and args.project_dir == PROJECT_DIR:
        gate = subprocess.run([sys.executable, str(READY_GATE), '--chapter', str(args.chapter)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if gate.returncode != 0:
            raise RuntimeError('上传TXT完备门禁失败，请先运行 ensure_fanqie_upload_txt_ready.py --write 修复：\n' + gate.stdout)

    data = parse_chapter(args.project_dir, args.chapter)
    print(json.dumps({k: v for k, v in data.items() if k not in ('body','note')} | {'note': data['note'], 'volume': volume}, ensure_ascii=False, indent=2))
    if not args.execute:
        print('DRY_RUN_OK')
        return

    login = backend_ok(args.session, args.state)
    if not login.get('ok'):
        raise RuntimeError(f'作家后台未登录，请扫码或导入cookie后重试: {login}')
    save_state(args.session, args.state)

    # 幂等门禁：草稿箱已有同名「第N章 标题」时，默认禁止再点「新建草稿」。
    # 根因备忘：2026-08-05 第245章 被看板 worker 与主控各 execute 一次 → 同名双草稿。
    pre = draft_listing_scan(args.session, data['chapter'], data['title'], state_path=args.state)
    if int(pre.get('count') or 0) > 0 and not args.force_new:
        report = {
            'error': 'DRAFT_ALREADY_EXISTS',
            'chapter': data['chapter'],
            'title': data['title'],
            'existing_count': pre.get('count'),
            'listText': pre.get('listText'),
            'hint': '同名草稿已在箱内。勿重复 --execute。清理旧项后重跑，或显式 --force-new（不推荐）。',
            'state': str(args.state),
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    # 若当前已在新建草稿页，可直接续跑；否则进入新建草稿编辑页。
    # 2026-08-05 根因：纯 click「新建草稿」常点到包裹 DIV，不导航；真实入口是
    # /main/writer/{BOOK_ID}/publish/?enter_from=newdraft
    NEW_DRAFT_URL = f'https://fanqienovel.com/main/writer/{BOOK_ID}/publish/?enter_from=newdraft'
    cur = ab(args.session, "get url", timeout=30, state_path=args.state).strip()
    if '/publish/' not in cur:
        # 优先直达 URL（比点按钮稳）
        ab(args.session, f"open {shlex.quote(NEW_DRAFT_URL)}", timeout=60, state_path=args.state)
        entered = False
        for _ in range(15):
            time.sleep(0.7)
            cur2 = ab(args.session, "get url", timeout=30, state_path=args.state).strip()
            if '/publish/' in cur2:
                entered = True
                break
        if not entered:
            # 回退：打开草稿箱，找真实 <a href> 再跳
            ab(args.session, f"open {shlex.quote(DRAFT_URL)}", timeout=60, state_path=args.state)
            href = None
            for _ in range(12):
                time.sleep(0.8)
                hit = js_eval(args.session, """
(() => {
 const e=[...document.querySelectorAll('a')].find(x => {
   const t=(x.innerText||x.textContent||'').replace(/\\s+/g,'').trim();
   const h=x.getAttribute('href')||'';
   return t==='新建草稿' || h.includes('enter_from=newdraft');
 });
 return e ? {ok:true, href:e.getAttribute('href')||e.href||null, text:(e.innerText||'').trim()} : {ok:false, head:(document.body.innerText||'').slice(0,300)};
})()
""", state_path=args.state)
                if isinstance(hit, dict) and hit.get('ok') and hit.get('href'):
                    href = hit['href']
                    break
            if not href:
                raise RuntimeError(f'新建草稿失败: 直达与链接均未就绪 url={ab(args.session,"get url",timeout=30,state_path=args.state).strip()}')
            if href.startswith('/'):
                href = 'https://fanqienovel.com' + href
            ab(args.session, f"open {shlex.quote(href)}", timeout=60, state_path=args.state)
            for _ in range(12):
                time.sleep(0.7)
                if '/publish/' in ab(args.session, "get url", timeout=30, state_path=args.state).strip():
                    entered = True
                    break
            if not entered:
                raise RuntimeError(f'新建草稿后未进入编辑页: href={href} url={ab(args.session,"get url",timeout=30,state_path=args.state).strip()}')
    ensure_volume(args.session, volume, state_path=args.state)
    fill = fill_main(args.session, data, volume, state_path=args.state)
    note = add_author_note(args.session, data['note'], state_path=args.state)
    final = save_and_verify(args.session, data, volume, state_path=args.state)
    # 上传成功后自动同步 sync_kewu
    sync_result = 'SYNC_SKIPPED'
    if isinstance(final, dict) and final.get('listing', {}).get('ok'):
        try:
            sync_cmd = [
                sys.executable,
                str(args.project_dir / '工具脚本' / 'sync_kewu.py'),
                '--chapter', str(args.chapter),
                '--no-git', '--no-vector',
            ]
            sync_proc = subprocess.run(
                sync_cmd, text=True, capture_output=True, timeout=120,
            )
            if sync_proc.returncode == 0:
                sync_result = 'SYNC_OK'
                print(f'sync_kewu: {sync_proc.stdout[:500]}', file=sys.stderr)
            else:
                sync_result = 'SYNC_FAILED'
                print(f'sync_kewu failed: {sync_proc.stderr[:300]}', file=sys.stderr)
        except Exception as e:
            sync_result = 'SYNC_FAILED'
            print(f'sync_kewu exception: {e}', file=sys.stderr)
    save_state(args.session, args.state)
    report = {
        'fill': fill,
        'note': note,
        'final': final,
        'sync': sync_result,
        'state': str(args.state),
        'pre_existing_count': pre.get('count'),
        'force_new': bool(args.force_new),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # 保存后仍出现同名>1：默认非0，避免调用方把重复当成功闭环
    if (
        isinstance(final, dict)
        and int(final.get('listing', {}).get('count') or 0) > 1
        and not args.allow_duplicate_listing
    ):
        print(
            'WARNING: listing duplicate after save; set --allow-duplicate-listing to suppress exit 3',
            file=sys.stderr,
        )
        raise SystemExit(3)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
