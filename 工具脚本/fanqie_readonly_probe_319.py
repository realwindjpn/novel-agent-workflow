#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""番茄第319章草稿箱只读回读探针（2026-09-09 closeout）。

只做读取：枚举草稿箱列表、定位 第319章 代理人真相、抽取编辑页正文/作者说/卷名/字数。
严格禁止任何提交/保存/发布/新建/删除动作。
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
    return { text: txt.slice(0, 200), hrefs: links };
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

EDIT_JS = """
(() => {
  const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
  const eds = Array.from(document.querySelectorAll('.ProseMirror, [contenteditable=true]'));
  const out = { ok: false, url: location.href };
  if (eds.length) {
    let t = eds[0].innerText || '';
    t = t.replace(/暂时没有思路，使用AI续写试试？/g, '').trim();
    const lines = t.split('\\n').map(x => x.trim()).filter(Boolean);
    out.body_head = lines[0] || '';
    out.body_tail = lines.slice(-2).join(' | ');
    out.body_chars = t.length;
    out.body_lines = lines.length;
    out.ok = true;
  } else {
    out.body_head = (document.body.innerText || '').slice(0, 200);
  }
  // 卷名入口多形态
  const vols = [
    document.querySelector('.publish-maintain-volume'),
    document.querySelector('.publish-maintain'),
    document.querySelector('.byte-select-view-value'),
    document.querySelector('.publish-header-volume-wrap'),
  ];
  out.volume = '';
  for (const v of vols) {
    if (v) {
      const t = norm(v.innerText);
      if (t) { out.volume = t; break; }
    }
  }
  // 作者说
  const noteSel = document.querySelector('.author-speak-input-view');
  out.note = noteSel ? norm(noteSel.innerText).slice(0, 200) : '';
  // 标题输入框
  out.title_inputs = Array.from(document.querySelectorAll('input'))
    .map(e => e.value).filter(Boolean).slice(0, 8);
  // 状态/按钮（只读枚举，不点击）
  out.buttons = Array.from(document.querySelectorAll('button, .btn, [class*=button]'))
    .map(b => norm(b.innerText).slice(0, 20)).filter(Boolean).slice(0, 20);
  // word counter
  out.word_counter = norm((document.querySelector('[class*=word-count], .word-count') || {}).innerText || '');
  return out;
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapter', type=int, default=319)
    ap.add_argument('--title', default='代理人真相')
    ap.add_argument('--session', default=DEFAULT_SESSION)
    ap.add_argument('--state', type=Path, default=DEFAULT_STATE)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()

    needle = f'第{a.chapter}章'
    res: dict = {'chapter': a.chapter, 'title': a.title, 'needle': needle,
                 'readonly': True}
    res['draft_list'] = enumerate_list(a.session, DRAFT_URLS, a.state, needle)

    edit_url = None
    for att in res['draft_list']:
        for hit in att.get('hits', []):
            for h in hit.get('hrefs', []):
                if 'modifydraft' in h or 'publish' in h:
                    edit_url = h if h.startswith('http') else 'https://fanqienovel.com' + h
                    break
            if edit_url:
                break
        if edit_url:
            break
    res['edit_url'] = edit_url
    if edit_url:
        res['editor_probe'] = js_eval(a.session, EDIT_JS, state=a.state, timeout=120)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print('WROTE', a.out)


if __name__ == '__main__':
    main()