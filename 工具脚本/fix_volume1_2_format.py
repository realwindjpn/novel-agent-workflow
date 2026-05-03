#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第一二卷 P0 格式修补脚本。
默认 dry-run，不改正文。

处理项：
1. 去 BOM
2. 去 Markdown 标题符 #
3. 去行号污染：^\d+\| / 形如 1|正文
4. 标准化首行标题：第N章 标题
5. 缺标题则补：第N章
6. 统一章末：（本章完）
7. apply 时先备份到 审核记录/备份/format_fix_时间戳/

用法：
python3 fix_volume1_2_format.py              # dry-run 新版 1-78
python3 fix_volume1_2_format.py --apply      # 修改 新版 1-78
python3 fix_volume1_2_format.py --include-submitted          # dry-run 新版+已投稿
python3 fix_volume1_2_format.py --apply --include-submitted  # 修改 新版+已投稿，慎用
"""
from __future__ import annotations
import argparse, json, re, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path('/root/workspace/科武纪元')
NEW_DIR = ROOT / '新版'
SUB_DIR = ROOT / '已投稿'
OUT_DIR = ROOT / '审核记录' / '第一二卷格式修补'
BAK_ROOT = ROOT / '审核记录' / '备份'
CN_NUM = '零一二三四五六七八九十百千万两'

TITLE_RE = re.compile(r'^\s*[#＃]*\s*第\s*([0-9一二三四五六七八九十百千万两]+)\s*章\s*(.*)\s*$')
LINE_NO_RE = re.compile(r'^\s*\d+\|')
END_VARIANTS = {'本章完', '（本章完）', '(本章完)', '【本章完】'}

def cn_count(s: str) -> int:
    return len(re.findall(r'[\u4e00-\u9fff]', s))

def normalize_title_line(line: str, n: int) -> tuple[str, bool]:
    raw = line.strip().lstrip('\ufeff').strip()
    raw = re.sub(r'^[#＃]+\s*', '', raw).strip()
    m = TITLE_RE.match(raw)
    if not m:
        return f'第{n}章', False
    title = m.group(2).strip()
    if title:
        return f'第{n}章 {title}', True
    return f'第{n}章', True

def strip_line_pollution(text: str) -> tuple[str, int]:
    changed = 0
    out = []
    for line in text.splitlines():
        new = re.sub(r'^\s*\d+\|', '', line)
        if new != line:
            changed += 1
        out.append(new)
    return '\n'.join(out), changed

def clean_text(text: str, n: int, suffix: str) -> tuple[str, dict]:
    original = text
    ops = []
    text = text.replace('\ufeff', '')
    if text != original:
        ops.append('去BOM')
    text, line_no_hits = strip_line_pollution(text)
    if line_no_hits:
        ops.append(f'去行号污染{line_no_hits}处')
    lines = [x.rstrip() for x in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    old_first = lines[0].strip() if lines else ''
    title_line, had_title = normalize_title_line(old_first, n)
    if lines:
        if had_title:
            if lines[0].strip() != title_line:
                ops.append('标准化标题')
            lines[0] = title_line
        else:
            ops.append('补标题')
            lines.insert(0, title_line)
    else:
        ops.append('补空章标题')
        lines = [title_line]

    # 统一章末。已有“本章完”变体则替换为标准；没有则追加。
    last_nonempty_i = None
    for i in range(len(lines)-1, -1, -1):
        if lines[i].strip():
            last_nonempty_i = i
            break
    if last_nonempty_i is None:
        lines.append('（本章完）')
        ops.append('补章末')
    else:
        last = lines[last_nonempty_i].strip()
        if last in END_VARIANTS:
            if last != '（本章完）':
                lines[last_nonempty_i] = '（本章完）'
                ops.append('标准化章末')
        else:
            lines.append('')
            lines.append('（本章完）')
            ops.append('补章末')

    new_text = '\n'.join(lines).rstrip() + '\n'
    info = {
        'changed': new_text != original,
        'ops': ops,
        'old_first': old_first,
        'new_first': lines[0].strip() if lines else '',
        'old_last': next((x.strip() for x in reversed(original.splitlines()) if x.strip()), ''),
        'new_last': next((x.strip() for x in reversed(new_text.splitlines()) if x.strip()), ''),
        'old_cn': cn_count(original),
        'new_cn': cn_count(new_text),
        'path': suffix,
    }
    return new_text, info

def chapter_num(p: Path):
    m = re.search(r'第(\d+)章', p.name)
    return int(m.group(1)) if m else None

def candidate_files(base: Path, lo=1, hi=78):
    files = []
    for ext in ('*.md', '*.txt'):
        for p in base.glob(ext):
            n = chapter_num(p)
            if n is not None and lo <= n <= hi and '备份' not in p.name:
                # 排除明显缩水/候选备份，主文件优先 第N章.md/txt
                if re.fullmatch(rf'第{n}章\.(md|txt)', p.name):
                    files.append((n, p))
    return sorted(files)

def run(apply=False, include_submitted=False):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backup_dir = BAK_ROOT / f'format_fix_{ts}'
    targets = [('新版', NEW_DIR, 1, 78)]
    if include_submitted:
        targets.append(('已投稿', SUB_DIR, 1, 61))
    records = []
    for label, base, lo, hi in targets:
        for n, p in candidate_files(base, lo, hi):
            old = p.read_text(encoding='utf-8', errors='ignore')
            new, info = clean_text(old, n, str(p))
            info.update({'chapter': n, 'scope': label})
            records.append(info)
            if apply and info['changed']:
                rel = p.relative_to(ROOT)
                bak = backup_dir / rel
                bak.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, bak)
                p.write_text(new, encoding='utf-8')
    changed = [r for r in records if r['changed']]
    out_json = OUT_DIR / f'format_fix_dryrun_{ts}.json'
    out_md = OUT_DIR / f'format_fix_dryrun_{ts}.md'
    if apply:
        out_json = OUT_DIR / f'format_fix_apply_{ts}.json'
        out_md = OUT_DIR / f'format_fix_apply_{ts}.md'
    out_json.write_text(json.dumps({'apply': apply, 'include_submitted': include_submitted, 'backup_dir': str(backup_dir) if apply else None, 'total': len(records), 'changed': len(changed), 'records': records}, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = []
    lines.append('# 第一二卷 P0 格式修补报告')
    lines.append('')
    lines.append(f'- 时间：{ts}')
    lines.append(f'- 模式：{"APPLY" if apply else "DRY-RUN"}')
    lines.append(f'- 范围：新版1-78' + (' + 已投稿1-61' if include_submitted else ''))
    lines.append(f'- 扫描文件：{len(records)}')
    lines.append(f'- 需修改：{len(changed)}')
    if apply:
        lines.append(f'- 备份目录：{backup_dir}')
    lines.append('')
    lines.append('|章|范围|操作|旧首行|新首行|旧末行|新末行|')
    lines.append('|---:|---|---|---|---|---|---|')
    for r in changed[:120]:
        def cut(x):
            return (x or '').replace('|','/').replace('\n',' ')[:36]
        lines.append(f"|{r['chapter']}|{r['scope']}|{','.join(r['ops'])}|{cut(r['old_first'])}|{cut(r['new_first'])}|{cut(r['old_last'])}|{cut(r['new_last'])}|")
    if len(changed) > 120:
        lines.append(f'\n> 仅展示前120条，完整见 JSON。')
    out_md.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'apply': apply, 'include_submitted': include_submitted, 'total': len(records), 'changed': len(changed), 'report_md': str(out_md), 'report_json': str(out_json), 'backup_dir': str(backup_dir) if apply else None}, ensure_ascii=False))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--include-submitted', action='store_true')
    args = ap.parse_args()
    run(apply=args.apply, include_submitted=args.include_submitted)
