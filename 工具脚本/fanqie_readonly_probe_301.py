#!/usr/bin/env python3
"""番茄第301章只读核查探针。

只做读取：枚举草稿箱(type=2)与已发布(type=1)列表行、可选搜索框只读定位、
抽取已发布章节编辑页正文用于与本地比对。

严格禁止：任何提交/保存/发布/新建/删除动作。本脚本不含 click 提交类调用，
仅有列表渲染所需的分卷下拉/搜索输入（只读定位），以及编辑页正文读取。
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

PROJECT_DIR = Path('/root/workspace/科武纪元')
BOOK_ID = '7628216044850531352'
BOOK_NAME_ENC = (
    '%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A'
    '%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99'
)
PUBLISHED_URLS = [
    f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}&{BOOK_NAME_ENC}?type=1',
    f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}',
]
DRAFT_URLS = [
    f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}',
    f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}&{BOOK_NAME_ENC}?type=2',
]
DEFAULT_SESSION = 'fanqie'
DEFAULT_STATE = Path('/root/workspace/browser_profiles/fanqie/fanqie_state.json')

WARN = '--state ignored'


def run(cmd: str, timeout: int = 90) -> str:
    p = subprocess.run(cmd, shell=True, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=timeout)
    out = '\n'.join(l for l in p.stdout.splitlines() if WARN not in l)
    if p.returncode != 0:
        raise RuntimeError(f'命令失败({p.returncode}): {cmd}\n{out}')
    return out


def ab(session: str, command: str, state: Path | None = None, timeout: int = 90) -> str:
    st = f'--state {shlex.quote(str(state))} ' if state and state.exists() else ''
    return run(f'agent-browser --session-name {shlex.quote(session)} {st}{command}',
               timeout=timeout)


def js_eval(session: str, js: str, state: Path | None = None, timeout: int = 90):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.js', delete=False) as f:
        f.write(js)
        p = Path(f.name)
    try:
        out = ab(session, f'eval "$(cat {shlex.quote(str(p))})"', state=state, timeout=timeout)
    finally:
        p.unlink(missing_ok=True)
    try:
        v = json.loads(out)
    except Exception:
        return out.strip()
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return v
    return v


ROWS_JS = """
(() => {
  const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
  const rows = Array.from(document.querySelectorAll('tr.arco-table-tr'));
  const out = rows.map(r => {
    const txt = norm(r.innerText);
    const links = Array.from(r.querySelectorAll('a')).map(a => a.getAttribute('href') || '');
    return { text: txt.slice(0, 120), hrefs: links };
  });
  const volSel = document.querySelector('.byte-select-view-value');
  return {
    url: location.href,
    rows: out.length,
    volume: volSel ? norm(volSel.innerText) : '',
    pager: norm((document.querySelector('.arco-pagination') || {}).innerText || ''),
    items: out
  };
})()
"""


def enumerate_list(session: str, urls: list[str], state: Path | None, needle: str):
    attempts = []
    for u in urls:
        try:
            ab(session, f'open {shlex.quote(u)}', state=state, timeout=90)
        except Exception as e:
            attempts.append({'url': u, 'error': str(e)[:300]})
            continue
        time.sleep(3)
        r = js_eval(session, ROWS_JS, state=state)
        if not isinstance(r, dict):
            attempts.append({'url': u, 'raw': str(r)[:300]})
            continue
        hit = [it for it in r.get('items', []) if needle in it.get('text', '')]
        r['hit_count'] = len(hit)
        r['hits'] = hit
        attempts.append(r)
        if hit:
            break
    return attempts


SEARCH_JS = """
(() => {
  const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
  const input = Array.from(document.querySelectorAll('input'))
    .find(e => (e.placeholder || '').includes('搜索章节'));
  if (!input) return { ok: false, reason: 'search_input_not_found', url: location.href };
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, 'value').set;
  setter.call(input, __NEEDLE__);
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
  return { ok: true, url: location.href, typed: __NEEDLE__ };
})()
"""


def search_probe(session: str, url: str, state: Path | None, needle: str):
    ab(session, f'open {shlex.quote(url)}', state=state, timeout=90)
    time.sleep(3)
    r1 = js_eval(session, SEARCH_JS.replace('__NEEDLE__', json.dumps(needle)), state=state)
    time.sleep(3)
    r2 = js_eval(session, ROWS_JS, state=state)
    if isinstance(r2, dict):
        hit = [it for it in r2.get('items', []) if needle in it.get('text', '')]
        r2['hit_count'] = len(hit)
        r2['hits'] = hit
    return {'search': r1, 'result': r2}


BODY_JS = """
(() => {
  const eds = Array.from(document.querySelectorAll('.ProseMirror, [contenteditable=true]'));
  if (!eds.length) return { ok: false, reason: 'editor_not_found', url: location.href,
                            body_head: (document.body.innerText || '').slice(0, 300) };
  const ed = eds[0];
  let t = ed.innerText || '';
  t = t.replace(/暂时没有思路，使用AI续写试试？/g, '');
  const num = Array.from(document.querySelectorAll('input'))
    .map(e => e.value).filter(Boolean).slice(0, 6);
  return { ok: true, url: location.href, chars: t.length, inputs: num, body: t };
})()
"""


def read_body(session: str, url: str, state: Path | None):
    ab(session, f'open {shlex.quote(url)}', state=state, timeout=90)
    time.sleep(4)
    return js_eval(session, BODY_JS, state=state, timeout=120)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapter', type=int, default=301)
    ap.add_argument('--title', default='联合防御')
    ap.add_argument('--session', default=DEFAULT_SESSION)
    ap.add_argument('--state', type=Path, default=DEFAULT_STATE)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--edit-url', default=None,
                    help='已定位到的编辑页 URL，只读抽取正文')
    a = ap.parse_args()

    needle = f'第{a.chapter}章'
    res: dict = {'chapter': a.chapter, 'title': a.title, 'needle': needle,
                 'readonly': True}

    if a.edit_url:
        res['body_probe'] = read_body(a.session, a.edit_url, a.state)
    else:
        res['draft_list'] = enumerate_list(a.session, DRAFT_URLS, a.state, needle)
        res['published_list'] = enumerate_list(a.session, PUBLISHED_URLS, a.state, needle)
        res['published_search'] = search_probe(a.session, PUBLISHED_URLS[0], a.state, needle)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: (v if not isinstance(v, (list, dict)) else '...')
                      for k, v in res.items()}, ensure_ascii=False))
    print('WROTE', a.out)


if __name__ == '__main__':
    main()
