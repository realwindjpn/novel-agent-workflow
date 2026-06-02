#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并发跑 V8.12.1 章节精修；模型审核不降级。
- 并发：run_refine_chapter_v4.py 140/141/142
- 串行收束：删除非上传 TXT、sync_kewu --no-git、Wiki Full Text 复核
"""
from __future__ import annotations
import json, subprocess, time, os, re
from pathlib import Path
from datetime import datetime

BASE = Path('/root/workspace/科武纪元')
SCRIPT = BASE / '工具脚本' / 'run_refine_chapter_v4.py'
SYNC = BASE / '工具脚本' / 'sync_kewu.py'
CHAPTERS = [140, 141, 142]
RUN_DIR = BASE / '审核记录' / '并发精修' / ('batch_140_142_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
RUN_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY = RUN_DIR / 'summary.json'


def fanqie_count(p: Path) -> int:
    txt = p.read_text(encoding='utf-8', errors='ignore')
    lines = txt.splitlines()
    title = lines[0] if lines else ''
    return len(''.join(txt.split())) - len(''.join(title.split()))


def report_pass(ch: int) -> bool:
    rep = BASE / '审核记录' / '六角色外审' / f'第{ch}章.md'
    if not rep.exists():
        return False
    txt = rep.read_text(encoding='utf-8', errors='ignore')
    gates = ['编辑写后：PASS', '读者写后：PASS', 'RTK编辑门禁：PASS', 'RTK读者门禁：PASS', '最终结论\nPASS']
    return all(g in txt for g in gates)


def verify_wiki(ch: int) -> bool:
    src = BASE / '新版' / f'第{ch}章.md'
    wiki = BASE / 'wiki' / 'chapters' / f'ch{ch:03d}.md'
    if not src.exists() or not wiki.exists():
        return False
    s = src.read_text(encoding='utf-8', errors='ignore')
    w = wiki.read_text(encoding='utf-8', errors='ignore')
    src_lines = [x.strip() for x in s.splitlines() if x.strip()]
    if not src_lines:
        return False
    title = src_lines[0]
    tail = src_lines[-1]
    return title in w and tail in w and '## Full Text' in w


def run_sync(ch: int) -> tuple[int, str]:
    cmd = ['python3', str(SYNC), '--chapter', str(ch), '--message', f'V8.12.1 第{ch}章并发精修闭环', '--no-git']
    r = subprocess.run(cmd, cwd='/root/workspace', text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    (RUN_DIR / f'ch{ch}_sync.log').write_text(r.stdout, encoding='utf-8')
    return r.returncode, r.stdout[-1200:]


def main():
    started = datetime.now().isoformat(timespec='seconds')
    procs = {}
    for ch in CHAPTERS:
        log = open(RUN_DIR / f'ch{ch}_v4.log', 'w', encoding='utf-8')
        p = subprocess.Popen(['python3', str(SCRIPT), str(ch)], cwd='/root/workspace', stdout=log, stderr=subprocess.STDOUT, text=True)
        procs[ch] = (p, log)
        time.sleep(2)  # 避免同时抢初始化/日志

    result = {'started': started, 'run_dir': str(RUN_DIR), 'chapters': {}}
    # 等三章作者/外审链路跑完
    for ch, (p, log) in procs.items():
        rc = p.wait()
        log.close()
        result['chapters'][str(ch)] = {'v4_exit': rc, 'v4_log': str(RUN_DIR / f'ch{ch}_v4.log')}
        SUMMARY.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    # 串行收束，防止 STATUS/WAL/Wiki 写冲突
    for ch in CHAPTERS:
        item = result['chapters'][str(ch)]
        item['report_pass'] = report_pass(ch)
        item['source_exists'] = (BASE / '新版' / f'第{ch}章.md').exists()
        if item['source_exists']:
            item['fanqie_count'] = fanqie_count(BASE / '新版' / f'第{ch}章.md')
        # 非上传章，不保留已投稿TXT
        txt = BASE / '已投稿' / f'第{ch}章.txt'
        if txt.exists():
            txt.unlink()
            item['upload_txt_removed'] = True
        else:
            item['upload_txt_removed'] = False
        if item['v4_exit'] == 0 and item['report_pass']:
            code, out = run_sync(ch)
            item['sync_exit'] = code
            item['sync_tail'] = out
            item['wiki_fulltext_ok'] = verify_wiki(ch)
        else:
            item['sync_exit'] = None
            item['wiki_fulltext_ok'] = False
        SUMMARY.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    result['finished'] = datetime.now().isoformat(timespec='seconds')
    SUMMARY.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
