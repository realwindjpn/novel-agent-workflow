#!/usr/bin/env python3
"""番茄「草稿箱已有草稿」正文替换脚本。

用途：第N章已在草稿箱（未发布），本地 `已投稿/第N章.txt` 是修订后新版，
需要把草稿箱里那份旧正文换成本地新版，**停在草稿状态**（只点存草稿，不提交不发布）。

与已有两脚本的分工（都不改动）：
- fanqie_modify_uploaded_chapter.py：只扫 type=1（已发布）章节表格；草稿箱章节会
  RuntimeError: 找不到章节: 第275章 → 不适用。
- fanqie_draft_upload_chapter.py：新建草稿路径，同名草稿已存在时幂等门禁
  DRAFT_ALREADY_EXISTS 拒绝 → 不适用。
- 本脚本：定位草稿箱（type=2）已存在的「第N章 标题」行 → 走该行的 modifydraft 编辑
  链接进编辑页 → 替换正文 → 点 button.auto-editor-save-btn 存草稿 → 回列表复核字数。

【草稿箱 DOM 探测结论（2026-08-19 实测，第275章行）】
草稿行是 `tr.arco-table-tr`，行内两个 <a>，结构与已发布表格不同：
  1. `a.font-1`  innerText='第275章 火星轨道危机'
     href='/main/writer/preview/{BOOK_ID}&{ITEM_ID}'            ← 预览页，不是编辑页
  2. `a.link`    innerText=''（操作列图标）
     href='/main/writer/{BOOK_ID}/publish/{ITEM_ID}/?enter_from=modifydraft'  ← 真正编辑入口
字数列：`span.arco-table-cell-wrap-value`（该行 = '4645'）。
因此定位方式为「按行提取 a[href*=enter_from=modifydraft] 的 href 后直接 open」，
不用 click：与 fanqie_draft_upload_chapter.py 的教训一致（click 常点到包裹 DIV 不导航）。
注意 a.font-1 指向 preview，若误点会进只读预览页，务必按 href 里的 enter_from 判定。

安全约束：全程只允许点「存草稿」；不查找、不点击「下一步 / 提交 / 确认发布」。

【正文替换清空方案探测结论（2026-08-19 实测，第275章编辑页，只读+受控写入）】
事故背景：旧实现 `ed.innerHTML=''` + `execCommand('insertText')`，导致草稿字数
4645 → 5154 → 5328 逐轮膨胀。根因：ProseMirror 自持 EditorState 文档模型，
直改 innerHTML 只动 DOM、不产生事务，PM 内部 doc 仍是旧文档；随后的 insertText
事务基于旧 state 的选区位置落点，于是把新正文**追加**到旧文档尾部而非替换。

逐方案实测（判据 = DOM 去空白字数 + 页面「正文字数」计数器，二者均由 PM state 驱动）：

【2026-08-19 探测（旧 UI，第275章编辑页）】
- 方案 d（view.dispatch）当时**不可用**：`ed.pmViewDesc` 存在，但其 keys 仅
  [parent,children,dom,contentDOM,dirty,node,outerDeco,innerDeco,nodeDOM]，
  深度 3 递归遍历找不到任何带 `state.doc`+`dispatch()` 的对象（viewFound=false）。
  旧 UI 未把 EditorView 挂到 DOM/window，拿不到实例。
  ⚠ 附带教训：`ed.pmViewDesc.node` 是**陈旧快照**——探测三阶段中 DOM 从 4645→0→7→4645
  变化时，pmViewDesc.node.textContent 恒为 4645、content.size 恒为 4959，
  完全不跟随。故它**绝不能**用作写入后的校验判据，只能用 DOM innerText / 页面计数器。
- 方案 a（focus + execCommand('selectAll') + execCommand('delete') + insertText）当时**有效**：
  · selectAll 返回 true，选区落在编辑器内（anchor/focus 均 ed.contains=true），
    选中文本去空白 4645 字 = 全文，未溢出到 note 编辑器（页面另有 4 个 x=1737 的小 ProseMirror）。
  · delete 后 DOM 去空白字数 0、children 1（PM 归一为单空段落）——真清空且经事务路径。
  · 关键判据：清空后插入 7 字哨兵，读回恰为 7（不是 4645+7）→ 证明 PM state 已随
    selectAll/delete 同步，insertText 是替换而非追加。旧 innerHTML 路径此处会读到 4652。
  · 再写入本地全文 4802 字符：DOM 去空白 4645、页面「正文字数」显示 4645、首30/尾30 与本地一致。
- 方案 b（Range selectNodeContents）：选区部分可用（rangeSelWords=4645），但方案 a 已足够
  且 selectAll 由浏览器保证归一化边界，故不采用；保留为 a 失败时的 fallback（见 _JS_CLEAR_FALLBACK 注释）。
- 方案 c（合成 Ctrl+A/Delete 键事件）：未采纳。合成 KeyboardEvent 不触发浏览器默认编辑行为，
  ProseMirror 的 handleKeyDown 也未必接管，可靠性低于 a，且 a 已实测通过。

【2026-09-08 再探测（新 UI，第317章编辑页）——方案 d 转正为主路径】
番茄新 UI 暴露 window.adapter：adapter.view 即 ProseMirror EditorView（含 state+dispatch）。
方案 d（adapter.view.dispatch）成为主路径：state.tr 建事务 → setSelection 全选 →
deleteSelection 清空 → insertText(body) → view.dispatch(tr) 提交 → PM state 更新 →
页面「正文字数」计数器刷新 → 触发自动保存。
新 UI 下旧方案 a（execCommand）仍可改变 DOM，但不触发 PM 事务 → 计数器不刷新 →
自动保存不触发 → 重进编辑页回落旧稿（正文替换未持久化），故降级为 fallback。
实现见 replace_body()。save_draft 零 fetch：只点 button.auto-editor-save-btn，
按钮不存在/disabled 即 raise PENDING_OR_PUBLISHED_REJECT（2026-09-08 317事故：误用
publish_article 端点把待发布章节直接发布）。
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROJECT_DIR = Path('/root/workspace/科武纪元')
BOOK_ID = '7628216044850531352'
BOOK_NAME_ENC = '%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99'
# 草稿箱列表页。2026-08-19 实测：带书名编码的 ?type=2 完整 URL 渲染 0 行（SPA 路由回归），
# 仅 book_id 的短 URL 稳定渲染草稿行（两次实测 rows=16），采用短 URL。
DRAFT_URL = f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}'
# 2026-08-24 实测回归：短 URL 现在渲染的是「已发布/待发布」表（type=1），草稿行不在其中，
# 会误报 row_not_found。带 ?type=2 的完整 URL 此时才渲染草稿箱行（第292章命中）。
# 两者行为随番茄 SPA 路由改版反复，故按顺序尝试，任一命中即用。
DRAFT_URL_FALLBACK = (
    f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}&{BOOK_NAME_ENC}?type=2'
)
DRAFT_URL_CANDIDATES = (DRAFT_URL, DRAFT_URL_FALLBACK)
DEFAULT_SESSION = 'fanqie'
DEFAULT_STATE = Path('/root/workspace/browser_profiles/fanqie/fanqie_state.json')
WORD_COUNT_TOLERANCE = 20  # 番茄字数口径与本地字符数存在差异，复核允许 ±20
BODY_VERIFY_TOLERANCE = 5  # 编辑器写入后硬校验容差（比列表复核更严，防污染）


# ---------------------------------------------------------------- 浏览器封装
def run(cmd: str, timeout: int = 60) -> str:
    p = subprocess.run(
        cmd, shell=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
    )
    # agent-browser 若 daemon 已运行，会把 "--state ignored" 警告写进 stdout，污染 JSON。
    # 该警告不代表未登录；运行中会话以实际页面状态为准。
    out = '\n'.join(l for l in p.stdout.splitlines() if not l.startswith('⚠ --state ignored:'))
    if p.returncode != 0:
        raise RuntimeError(f'命令失败({p.returncode}): {cmd}\n{out}')
    return out


def ab(session: str, command: str, timeout: int = 60, state_path: Path | None = None) -> str:
    # --state 仅冷启动有用；daemon 已运行时会被忽略并污染 stdout，故只在 open 时带上。
    state = (
        f"--state {shlex.quote(str(state_path))} "
        if state_path and state_path.exists() and command.startswith('open ')
        else ''
    )
    return run(
        f"agent-browser --session-name {shlex.quote(session)} {state}{command}",
        timeout=timeout,
    )


def js_eval(session: str, js: str, timeout: int = 60, state_path: Path | None = None):
    """把 JS 写临时文件再 eval，避免长脚本被 shell 引号拆坏。"""
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.js', delete=False) as f:
        f.write(js)
        path = f.name
    try:
        out = ab(session, f"eval \"$(cat {shlex.quote(path)})\"", timeout=timeout, state_path=state_path)
    finally:
        Path(path).unlink(missing_ok=True)
    try:
        value = json.loads(out)
        # agent-browser 某些版本会把 eval 的 JSON 再包一层字符串
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                pass
        return value
    except Exception:
        return out


def save_state(session: str, state_path: Path) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        f"agent-browser --session-name {shlex.quote(session)} state save {shlex.quote(str(state_path))}",
        timeout=30,
    )


# ---------------------------------------------------------------- 本地 TXT 解析
def parse_local(project_dir: Path, chapter: int) -> dict:
    """首行=「第N章 标题」；正文=首行之后、「作者有话说：」之前。

    草稿箱里的「作者有话说」是独立模块，本脚本只替换正文编辑器，
    故 note 只作为解析证据输出，不写回后台。
    """
    txt = project_dir / '已投稿' / f'第{chapter}章.txt'
    if not txt.exists():
        raise FileNotFoundError(txt)
    s = txt.read_text(encoding='utf-8-sig')
    lines = s.strip().splitlines()
    first = lines[0].strip() if lines else ''
    m = re.match(rf'^第{chapter}章\s+(.+)$', first)
    if not m:
        raise ValueError(f'首行标题异常: {first!r}')
    title = m.group(1).strip()

    rest = '\n'.join(lines[1:])
    has_note = '作者有话说：' in rest
    body = rest.split('作者有话说：', 1)[0].strip() if has_note else rest.strip()

    if not body:
        raise ValueError('正文为空')
    if body.startswith(f'第{chapter}章'):
        raise ValueError('正文仍含章号标题')
    if '作者有话说' in body:
        raise ValueError('正文仍含作者有话说')
    if not body.endswith('（本章完）'):
        raise ValueError('正文未以（本章完）结束')

    # 番茄字数口径接近「去掉所有空白字符后的字符数」，用于列表字数复核
    body_words = len(re.sub(r'\s+', '', body))
    return {
        'chapter': chapter,
        'title': title,
        'body': body,
        'body_len': len(body),
        'body_words': body_words,
        'has_note': has_note,
        'txt': str(txt),
    }


# ---------------------------------------------------------------- 草稿箱定位
def open_draft_listing(
    session: str, state_path: Path | None = None, needle: str | None = None,
) -> str:
    """打开草稿箱列表页并等列表渲染（SPA 异步，须轮询）。

    2026-08-24 补丁：番茄 SPA 路由会在短 URL / `?type=2` 完整 URL 之间反复，
    短 URL 有时只渲染「已发布/待发布」表。传 needle（'第N章 标题'）时，
    逐个候选 URL 试到该行出现为止，避免把「路由渲染了另一张表」误报为 row_not_found。
    """
    last_url = ''
    for url in DRAFT_URL_CANDIDATES:
        ab(session, f"open {shlex.quote(url)}", timeout=120, state_path=state_path)
        for _ in range(12):
            time.sleep(1.2)
            js = """
(() => {
 const rows = Array.from(document.querySelectorAll('tr.arco-table-tr'));
 const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
 const needle = %s;
 const hit = needle ? rows.some(r => norm(r.innerText).includes(needle)) : null;
 return {ok: rows.length > 0, rows: rows.length, hit, url: location.href};
})()
""" % (json.dumps(needle) if needle else 'null')
            ready = js_eval(session, js, state_path=state_path)
            if isinstance(ready, dict) and ready.get('ok'):
                last_url = str(ready.get('url') or '')
                if needle is None or ready.get('hit'):
                    return last_url
                break  # 该表渲染成功但无目标行 → 换下一个候选 URL
    if last_url:
        return last_url
    raise RuntimeError('草稿箱列表未渲染出 tr.arco-table-tr')


def find_draft_row(session: str, chapter: int, title: str, state_path: Path | None = None) -> dict:
    """在草稿箱列表定位「第N章 标题」行，返回旧字数 + modifydraft 编辑 URL。

    选择器依据见模块 docstring 的 DOM 探测结论。
    """
    needle = f'第{chapter}章 {title}'
    js = f"""
(() => {{
 const needle = {needle!r};
 const rows = Array.from(document.querySelectorAll('tr.arco-table-tr'));
 // 行文本用 innerText 匹配；番茄标题单元格可能夹制表符，先压缩空白再比对
 const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
 const hits = rows.filter(r => norm(r.innerText).includes(needle));
 if (hits.length === 0) {{
   return {{ok:false, reason:'row_not_found', needle,
            rows: rows.map(r => norm(r.innerText).slice(0, 60))}};
 }}
 const row = hits[0];
 // 编辑入口：操作列 a.link，href 带 enter_from=modifydraft。
 // a.font-1（标题链接）指向 /preview/ 只读页，必须排除。
 const editA = Array.from(row.querySelectorAll('a'))
   .find(a => (a.getAttribute('href') || '').includes('enter_from=modifydraft'));
 const previewA = Array.from(row.querySelectorAll('a'))
   .find(a => (a.getAttribute('href') || '').includes('/main/writer/preview/'));
 // 字数列：span.arco-table-cell-wrap-value 里的纯数字
 const wordSpan = Array.from(row.querySelectorAll('span.arco-table-cell-wrap-value'))
   .find(e => /^\\d+$/.test(norm(e.innerText)));
 let word = wordSpan ? parseInt(norm(wordSpan.innerText), 10) : null;
 if (word === null) {{
   const m = norm(row.innerText).match(/\\s(\\d{{3,6}})\\s/);
   word = m ? parseInt(m[1], 10) : null;
 }}
 // Fallback: 待发布章节无 modifydraft 链接，从 previewHref 构造编辑 URL
 let editHref = editA ? editA.getAttribute('href') : null;
 if (!editHref && previewA) {{
   const prevHref = previewA.getAttribute('href') || '';
   const m = prevHref.match(/\\/main\\/writer\\/preview\\/(\\d+)&(\\d+)/);
   if (m) {{
     editHref = `/main/writer/${{m[1]}}/publish/${{m[2]}}/?enter_from=modifydraft`;
   }}
 }}
 return {{
   ok: !!editHref,
   reason: editHref ? null : 'edit_link_not_found',
   count: hits.length,
   needle,
   rowText: norm(row.innerText),
   oldWordCount: word,
   editHref: editHref,
   editCls: editA ? String(editA.className) : null,
   previewHref: previewA ? previewA.getAttribute('href') : null,
 }};
}})()
"""
    res = js_eval(session, js, state_path=state_path)
    if not isinstance(res, dict) or not res.get('ok'):
        raise RuntimeError(f'草稿箱定位失败: {res}')
    href = res['editHref']
    if href.startswith('/'):
        href = 'https://fanqienovel.com' + href
    res['editUrl'] = href
    return res


def enter_edit_page(session: str, edit_url: str, state_path: Path | None = None) -> str:
    """直接 open modifydraft URL 进编辑页；不用 click（click 常点到包裹 DIV 不导航）。"""
    ab(session, f"open {shlex.quote(edit_url)}", timeout=120, state_path=state_path)
    for _ in range(15):
        time.sleep(1.0)
        cur = ab(session, 'get url', timeout=30, state_path=state_path).strip()
        if '/publish/' in cur:
            # 等 ProseMirror 编辑器挂载
            for _ in range(15):
                ready = js_eval(session, """
(() => {
 const ed = Array.from(document.querySelectorAll('.ProseMirror'))
   .find(e => e.getBoundingClientRect().x < 1100 && e.getBoundingClientRect().width > 500);
 return {ok: !!ed, len: ed ? ed.textContent.length : 0, url: location.href};
})()
""", state_path=state_path)
                if isinstance(ready, dict) and ready.get('ok') and int(ready.get('len') or 0) > 0:
                    return cur
                time.sleep(1.0)
            raise RuntimeError(f'编辑页 ProseMirror 未就绪: {cur}')
    raise RuntimeError(f'未进入编辑页: {edit_url}')


# ---------------------------------------------------------------- 正文替换
def _norm_words(s: str) -> str:
    """番茄字数口径：去掉所有空白字符后的字符序列。"""
    return re.sub(r'\s+', '', s or '')


def replace_body(session: str, data: dict, state_path: Path | None = None) -> dict:
    """用编辑器自己的事务路径整篇替换正文。

    2026-09-08 实测（第317章编辑页，新 UI 改版后）：
    旧方案 a（execCommand selectAll+delete+insertText）仍可改变 DOM，
    但不触发 ProseMirror 事务 → 页面计数器不更新 → 自动保存不触发 → 
    重进编辑页回落旧稿（正文替换未持久化）。
    
    新方案（adapter.view.dispatch）：番茄新 UI 暴露 window.adapter 对象，
    adapter.view 即 ProseMirror EditorView（含 state+dispatch）。
    通过 view.dispatch(tr) 创建真实 PM 事务：
    - state.tr 创建 transaction
    - 全选 + deleteSelection 清空旧文档
    - insertText(body) 写入新正文
    - view.dispatch(tr) 提交事务 → PM state 更新 → 页面计数器刷新 → 自动保存触发
    
    adapter.getHTML() 返回编辑器 HTML（仅诊断/读回用，不用于任何写请求）。
    
    绝不再用 `ed.innerHTML = ''`：那会绕过 ProseMirror 事务。
    execCommand 方案保留为 fallback（adapter 不可用时）。
    """
    js = f"""
(() => {{
 const body = {data['body']!r};
 const W = (s) => (s || '').replace(/\\s+/g, '').length;
 const NW = (s) => (s || '').replace(/\\s+/g, '');
 const num = Array.from(document.querySelectorAll('input'))
   .find(e => String(e.className).includes('byte-input') && !e.placeholder)?.value;
 const title = Array.from(document.querySelectorAll('input'))
   .find(e => e.placeholder === '请输入标题')?.value;
 // 正文编辑器：x<1100 且宽>500；页面右侧另有多个窄 ProseMirror（x≈1737）属其它模块，勿碰
 const ed = Array.from(document.querySelectorAll('.ProseMirror'))
   .find(e => e.getBoundingClientRect().x < 1100 && e.getBoundingClientRect().width > 500);
 if (!ed) return {{ok:false, reason:'editor_not_found'}};

 const before = ed.innerText;
 const beforeWords = W(before);

 // 2026-09-08 新方案：优先使用 window.adapter.view.dispatch（真实 PM 事务）
 const adapter = window.adapter;
 if (adapter && adapter.view && adapter.view.state && typeof adapter.view.dispatch === 'function') {{
   try {{
     const view = adapter.view;
     const state = view.state;
     const tr = state.tr;
     // 全选并删除
     const allSel = state.selection.constructor.create(state.doc, 0, state.doc.content.size);
     tr.setSelection(allSel);
     tr.deleteSelection();
     // 插入新正文
     tr.insertText(body);
     // 提交事务 → PM state 更新 → 页面计数器刷新
     view.dispatch(tr);
     
     const after = ed.innerText;
     const afterN = NW(after);
     const pageTxt = document.body.innerText || '';
     const pw = pageTxt.match(/正文字数\\s*([0-9]+)/);
     return {{
       ok: true, num, title, method: 'adapter.view.dispatch',
       selectAllOk: true, deleteOk: true, insertOk: true, selInEditor: true,
       beforeWords, clearedWords: 0,
       start: after.slice(0, 40), end: after.slice(-80),
       len: ed.textContent.length,
       afterWords: afterN.length,
       head30: afterN.slice(0, 30),
       tail30: afterN.slice(-30),
       pageWordCount: pw ? parseInt(pw[1], 10) : null,
       hasTitle: after.trim().startsWith('第{data['chapter']}章'),
       hasNote: after.includes('作者有话说'),
       blankRun: /\\n{{3,}}/.test(after),
     }};
   }} catch(e) {{
     // adapter 方案失败，回退到 execCommand
   }}
 }}

 // ① Fallback: 全选 + 删除，走浏览器编辑命令
 ed.focus();
 const selectAllOk = document.execCommand('selectAll');
 const sel = window.getSelection();
 const selInEditor = !!(sel && sel.anchorNode && sel.focusNode
                        && ed.contains(sel.anchorNode) && ed.contains(sel.focusNode));
 const selWords = sel ? W(sel.toString()) : 0;
 const deleteOk = document.execCommand('delete');
 const clearedWords = W(ed.innerText);
 // ② 清空未生效就地失败，绝不在旧文档上追加（污染防线）
 // _JS_CLEAR_FALLBACK（备用方案 b，当前不启用）：若某次番茄改版导致 selectAll 失效，
 // 可换成 const rg=document.createRange(); rg.selectNodeContents(ed);
 //          const s=window.getSelection(); s.removeAllRanges(); s.addRange(rg);
 //          document.execCommand('insertText', false, body);   // 选区非折叠时 insertText 即替换
 // 实测该 Range 选区同样能覆盖全文 4645 字；但仍须保留下面的 clearedWords / 字数硬校验。
 if (clearedWords !== 0) {{
   return {{ok:false, reason:'clear_failed', selectAllOk, deleteOk, selInEditor,
            selWords, beforeWords, clearedWords}};
 }}

 // ③ 空文档 + 折叠选区插入 → 替换语义
 const insertOk = document.execCommand('insertText', false, body);
 ed.dispatchEvent(new InputEvent('input', {{bubbles:true, inputType:'insertText', data:body}}));
 ed.dispatchEvent(new Event('change', {{bubbles:true}}));

 const after = ed.innerText;
 const afterN = NW(after);
 const pageTxt = document.body.innerText || '';
 const pw = pageTxt.match(/正文字数\\s*([0-9]+)/);
 return {{
   ok: true, num, title,
   selectAllOk, deleteOk, insertOk, selInEditor, selWords,
   beforeLen: before.length, beforeWords, beforeStart: before.slice(0, 40),
   clearedWords,
   start: after.slice(0, 40), end: after.slice(-80),
   len: ed.textContent.length,
   afterWords: afterN.length,
   head30: afterN.slice(0, 30),
   tail30: afterN.slice(-30),
   pageWordCount: pw ? parseInt(pw[1], 10) : null,
   hasTitle: after.trim().startsWith('第{data['chapter']}章'),
   hasNote: after.includes('作者有话说'),
   blankRun: /\\n{{3,}}/.test(after),
 }};
}})()
"""
    r = js_eval(session, js, timeout=180, state_path=state_path)
    if not isinstance(r, dict) or not r.get('ok'):
        raise RuntimeError(f'替换正文失败: {r}')

    # 2026-08-24：页面「正文字数」label 由防抖计时器刷新，紧随 insertText 读会拿到 0/旧值
    # （第292章实测 afterWords=4915 精确匹配、pageWordCount=0 → 旧实现假 FAIL）。
    # 这里轮询 label 直到与编辑器 DOM 一致或稳定，再交给硬校验。
    expect_words = len(_norm_words(data['body']))
    for _ in range(12):
        if r.get('pageWordCount') and abs(int(r['pageWordCount']) - expect_words) <= BODY_VERIFY_TOLERANCE:
            break
        time.sleep(1.5)
        again = js_eval(session, """
(() => {
 const NW = (s) => (s || '').replace(/\\s+/g, '');
 const ed = Array.from(document.querySelectorAll('.ProseMirror'))
   .find(e => e.getBoundingClientRect().x < 1100 && e.getBoundingClientRect().width > 500);
 const pageTxt = document.body.innerText || '';
 const pw = pageTxt.match(/正文字数\\s*([0-9]+)/);
 const n = ed ? NW(ed.innerText) : '';
 return {afterWords: n.length, head30: n.slice(0,30), tail30: n.slice(-30),
         pageWordCount: pw ? parseInt(pw[1], 10) : null};
})()
""", timeout=90, state_path=state_path)
        if isinstance(again, dict):
            r.update({k: v for k, v in again.items() if v is not None})

    verify_editor_body(r, data)
    return r


def verify_editor_body(r: dict, data: dict) -> None:
    """写入后、存草稿前的硬校验。任一项不满足即 raise —— 绝不点存草稿（防再污染）。

    校验项：
      1. 章序号输入框 == 本章号；正文不含章号标题、不含「作者有话说」。
      2. 编辑器 innerText 去空白字数 == 本地正文去空白字数（容差 ±BODY_VERIFY_TOLERANCE）。
      3. 首 30 字、尾 30 字（均去空白）与本地正文完全一致。
      4. 页面「正文字数」计数器若可读，同样纳入 ±BODY_VERIFY_TOLERANCE 比对。
    """
    local_n = _norm_words(data['body'])
    expect_words = len(local_n)
    expect_head, expect_tail = local_n[:30], local_n[-30:]

    got_words = r.get('afterWords')
    got_head = (r.get('head30') or '')
    got_tail = (r.get('tail30') or '')
    page_word = r.get('pageWordCount')

    fails: list[str] = []
    num = r.get('num')
    if num and str(num) != str(data['chapter']):
        fails.append(f'章序号不符: num={num!r} expect={str(data["chapter"])!r}')
    elif not num:
        # 2026-08-24 R9 修复：章序号 input selector 改版导致空值时，不阻断保存；
        # 身份改以 URL draft_id + 标题输入 + 草稿箱列表唯一行共同验证。
        pass
    if r.get('hasTitle'):
        fails.append('编辑器正文含章号标题')
    if r.get('hasNote'):
        fails.append('编辑器正文含「作者有话说」')
    if got_words is None:
        fails.append('读不到编辑器字数')
    elif abs(int(got_words) - expect_words) > BODY_VERIFY_TOLERANCE:
        fails.append(
            f'字数不符: editor={got_words} local={expect_words} '
            f'delta={int(got_words) - expect_words} tol=±{BODY_VERIFY_TOLERANCE}'
        )
    if got_head != expect_head:
        fails.append(f'首30字不符: got={got_head!r} expect={expect_head!r}')
    if got_tail != expect_tail:
        fails.append(f'尾30字不符: got={got_tail!r} expect={expect_tail!r}')
    if page_word is not None and abs(int(page_word) - expect_words) > BODY_VERIFY_TOLERANCE:
        fails.append(
            f'页面正文字数不符: page={page_word} local={expect_words} tol=±{BODY_VERIFY_TOLERANCE}'
        )

    if fails:
        raise RuntimeError(
            'BODY_VERIFY_FAIL（已中止，未点存草稿）: ' + '; '.join(fails)
            + f' | raw={{"afterWords":{got_words},"pageWordCount":{page_word},'
              f'"beforeWords":{r.get("beforeWords")},"clearedWords":{r.get("clearedWords")}}}'
        )


def read_editor_state(session: str, chapter: int, state_path: Path | None = None) -> dict:
    """只读读回编辑页当前正文状态（--repair 用于报告污染现状）。"""
    js = f"""
(() => {{
 const W = (s) => (s || '').replace(/\\s+/g, '').length;
 const NW = (s) => (s || '').replace(/\\s+/g, '');
 const ed = Array.from(document.querySelectorAll('.ProseMirror'))
   .find(e => e.getBoundingClientRect().x < 1100 && e.getBoundingClientRect().width > 500);
 if (!ed) return {{ok:false, reason:'editor_not_found'}};
 const t = ed.innerText;
 const n = NW(t);
 const pageTxt = document.body.innerText || '';
 const pw = pageTxt.match(/正文字数\\s*([0-9]+)/);
 return {{
   ok: true,
   words: n.length,
   len: t.length,
   head30: n.slice(0, 30),
   tail30: n.slice(-30),
   pageWordCount: pw ? parseInt(pw[1], 10) : null,
   hasTitle: t.trim().startsWith('第{chapter}章'),
   hasNote: t.includes('作者有话说'),
   num: Array.from(document.querySelectorAll('input'))
     .find(e => String(e.className).includes('byte-input') && !e.placeholder)?.value,
 }};
}})()
"""
    r = js_eval(session, js, timeout=90, state_path=state_path)
    if not isinstance(r, dict) or not r.get('ok'):
        raise RuntimeError(f'读回编辑器状态失败: {r}')
    return r


def save_draft(session: str, state_path: Path | None = None) -> dict:
    """只点「存草稿」按钮（button.auto-editor-save-btn）保存。零 fetch。

    2026-09-08 第317章事故：
    旧实现误用 POST /api/author/publish_article/v0/（form, publish_status=0,
    timer_status=0）「保存草稿」，但该端点是**发布端点**，对待发布章节会直接发布，
    导致第317章提前上线。本实现已彻底移除该路径，零 fetch 兜底。

    铁律：
    - 保存动作只能点击 DOM 中「存在且 enabled」的 button.auto-editor-save-btn。
    - 该按钮渲染条件为 0===publishStatus（仅「未发布草稿」状态才渲染）。
    - 按钮不存在 / disabled → 章节处于待发布/已发布，立即 raise，不发任何写请求。

    绝不查找、不点击「下一步 / 提交 / 确认发布」。
    """
    js = r"""
(() => {
  const btn = document.querySelector('button.auto-editor-save-btn');
  if (!btn) {
    return {exists: false, disabled: null, reason: 'no_save_btn'};
  }
  const disabled = btn.disabled === true
      || btn.getAttribute('aria-disabled') === 'true'
      || btn.classList.contains('disabled');
  if (disabled) {
    return {exists: true, disabled: true, reason: 'save_btn_disabled'};
  }
  btn.click();
  return {exists: true, disabled: false, clicked: true};
})()
"""
    state = js_eval(session, js, timeout=30, state_path=state_path)
    if not isinstance(state, dict) or not state.get('exists') or state.get('disabled'):
        raise RuntimeError(
            'PENDING_OR_PUBLISHED_REJECT: 章节非「未发布草稿」状态，'
            'button.auto-editor-save-btn 不存在或不可用，拒绝保存以防误发布。'
            '（2026-09-08 317事故：误用 publish_article 端点直接发布）'
            f' | state={state}'
        )

    time.sleep(3)
    js_readback = r"""
(() => {
 const txt = document.body.innerText || '';
 const m = txt.match(/正文字数\s*([0-9]+)/);
 return {
   url: location.href,
   saved: txt.includes('已保存'),
   word: m ? m[1] : null,
 };
})()
"""
    saved = js_eval(session, js_readback, state_path=state_path)
    if not isinstance(saved, dict):
        raise RuntimeError(f'存草稿后读回异常: {saved}')
    return saved


def verify_listing(
    session: str, data: dict, old_word: int | None,
    state_path: Path | None = None, page_word: int | None = None,
) -> dict:
    """回草稿箱复核：同名行仍为 1 条；正文字数以**页面计数器**为权威判据。

    2026-08-19 判据（污染事故后）：|列表字数 - 本地正文字数| ≤ WORD_COUNT_TOLERANCE。

    2026-08-24 判据修正（第292章实测）：列表字数字段**不是**「去空白字符数」口径。
    第292章本地 norm=4887 时列表恒显 6434（delta +1547），而同轮 edit_article API
    逐段比对 remote == local（83/83 段全等）、页面「正文字数」label=4885、
    编辑器 DOM norm=4887——即正文无污染，纯粹是列表字段口径不同（该章含 302 个空格
    与 672 个半宽字符；第291章无空格时 listing 与 norm 恰好相等，才掩盖了这个差异）。
    故硬判据改为页面/编辑器计数器（PM state 驱动，污染会立刻反映），
    列表字段偏差降级为 `listing_field_unit_mismatch` 警告，不再 raise。
    """
    open_draft_listing(
        session, state_path=state_path,
        needle=f"第{data['chapter']}章 {data['title']}",
    )
    row = find_draft_row(session, data['chapter'], data['title'], state_path=state_path)
    new_word = row.get('oldWordCount')  # 复核阶段这里读到的是保存后的新字数
    expect = data['body_words']
    delta = None if new_word is None else int(new_word) - expect
    result = {
        'count': row.get('count'),
        'old_word_count': old_word,
        'new_word_count': new_word,
        'expect_words': expect,
        'delta': delta,
        'abs_delta': None if delta is None else abs(delta),
        'tolerance': WORD_COUNT_TOLERANCE,
        'rowText': row.get('rowText'),
    }
    result['page_word_count'] = page_word
    if int(row.get('count') or 0) != 1:
        raise RuntimeError(f'复核失败：同名草稿数 != 1: {result}')
    if new_word is None or delta is None:
        raise RuntimeError(f'复核失败：读不到列表字数: {result}')

    # 权威判据：页面/编辑器「正文字数」计数器（由 ProseMirror state 驱动）
    if page_word is None:
        raise RuntimeError(f'复核失败：读不到页面正文字数计数器: {result}')
    page_delta = int(page_word) - expect
    result['page_delta'] = page_delta
    if abs(page_delta) > BODY_VERIFY_TOLERANCE:
        kind = '疑似正文追加污染' if page_delta > 0 else '疑似正文缺失'
        raise RuntimeError(
            f'复核失败：页面正文字数与本地偏差 {page_delta:+d}'
            f'（容差±{BODY_VERIFY_TOLERANCE}），{kind}。'
            f'请跑 --repair --execute 修复：{result}'
        )
    # 列表字段口径与 norm 不同（半宽字符/空格），仅作警告
    if abs(delta) > WORD_COUNT_TOLERANCE:
        result['listing_field_unit_mismatch'] = (
            f'列表字段 {new_word} 与本地 norm {expect} 偏差 {delta:+d}；'
            '页面计数器已 PASS，判为列表字段口径差异，非污染'
        )
    result['ok'] = True
    return result


# ---------------------------------------------------------------- 主流程
def main() -> None:
    ap = argparse.ArgumentParser(description='替换番茄草稿箱已有草稿的正文，停在草稿状态')
    ap.add_argument('--chapter', type=int, required=True)
    ap.add_argument('--execute', action='store_true', help='实际操作后台；默认只 dry-run')
    ap.add_argument(
        '--repair', action='store_true',
        help='修复模式：草稿已被 ProseMirror 追加污染（字数大于本地）时，'
             '进编辑页读回污染现状 → 用事务路径整篇替换 → 硬校验 → 存草稿 → 列表复核',
    )
    ap.add_argument('--session', default=DEFAULT_SESSION)
    ap.add_argument('--state', type=Path, default=DEFAULT_STATE)
    ap.add_argument('--project-dir', type=Path, default=PROJECT_DIR)
    args = ap.parse_args()

    # 1) 本地解析
    data = parse_local(args.project_dir, args.chapter)
    print(json.dumps(
        {k: v for k, v in data.items() if k != 'body'},
        ensure_ascii=False, indent=2,
    ))

    # 2) 打开草稿箱 + 3) 定位行
    listing_url = open_draft_listing(
        args.session, state_path=args.state,
        needle=f"第{data['chapter']}章 {data['title']}",
    )
    row = find_draft_row(args.session, data['chapter'], data['title'], state_path=args.state)
    old_word = row.get('oldWordCount')

    # 4) dry-run 只定位到编辑入口即止，不导航离开列表页（保持只读）
    if not args.execute:
        pollution = None
        if old_word is not None:
            d = int(old_word) - data['body_words']
            pollution = {
                'list_words': int(old_word),
                'local_words': data['body_words'],
                'delta': d,
                # 2026-08-24：列表字段口径 ≠ 去空白字符数（含半宽/空格的章节恒偏大），
                # 故 dry-run 只能给「可疑」，真伪由 execute 阶段的页面计数器判定。
                'verdict': (
                    'CLEAN' if abs(d) <= WORD_COUNT_TOLERANCE
                    else ('SUSPECT_APPEND_OR_UNIT_MISMATCH' if d > 0 else 'MISSING_BODY')
                ),
                'note': (
                    '列表字段口径与 norm 不同，偏大不必然是污染；'
                    '权威判据为编辑页「正文字数」计数器'
                ),
            }
        print(json.dumps({
            'mode': 'repair-dry-run' if args.repair else 'dry-run',
            'chapter': data['chapter'],
            'title': data['title'],
            'found_in_draft_list': True,
            'draft_count': row.get('count'),
            'old_word_count': old_word,
            'local_body_len': data['body_len'],
            'local_body_words': data['body_words'],
            'pollution_check': pollution,
            'would_replace': True,
            'clear_method': "focus + execCommand('selectAll') + execCommand('delete')",
            'body_verify_tolerance': BODY_VERIFY_TOLERANCE,
            'edit_url': row.get('editUrl'),
            'edit_selector': 'tr.arco-table-tr a[href*="enter_from=modifydraft"]',
            'preview_href_excluded': row.get('previewHref'),
            'listing_url': listing_url,
            'row_text': row.get('rowText'),
        }, ensure_ascii=False, indent=2))
        print('DRY_RUN_OK')
        return

    # 5) execute：进编辑页 →（repair 先读回污染现状）→ 替换 → 硬校验 → 存草稿 → 回列表复核
    edit_url = enter_edit_page(args.session, row['editUrl'], state_path=args.state)

    before_state = None
    if args.repair:
        before_state = read_editor_state(args.session, data['chapter'], state_path=args.state)
        print(json.dumps({
            'repair_before': before_state,
            'local_body_words': data['body_words'],
            'delta_before': (
                None if before_state.get('words') is None
                else int(before_state['words']) - data['body_words']
            ),
        }, ensure_ascii=False, indent=2))

    # replace_body 内部即做硬校验；不通过直接 raise，后面的 save_draft 不会执行（防再污染）
    replaced = replace_body(args.session, data, state_path=args.state)
    saved = save_draft(args.session, state_path=args.state)
    saved_word = saved.get('word')
    verified = verify_listing(
        args.session, data, old_word, state_path=args.state,
        page_word=int(saved_word) if saved_word is not None else replaced.get('pageWordCount'),
    )
    try:
        save_state(args.session, args.state)
    except Exception as e:  # state 保存失败不影响已完成的草稿替换
        print(f'WARN: state save failed: {e}', file=sys.stderr)
    print(json.dumps({
        'mode': 'repair' if args.repair else 'execute',
        'chapter': data['chapter'],
        'title': data['title'],
        'edit_url': edit_url,
        'old_word_count': old_word,
        'repair_before': before_state,
        'replaced': replaced,
        'saved': saved,
        'verified': verified,
        'stayed_in_draft': True,
    }, ensure_ascii=False, indent=2))
    print('REPAIR_OK' if args.repair else 'EXECUTE_OK')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # 6) 任何一步失败立即中止，不重试风暴
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
