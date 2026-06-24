#!/usr/bin/env python3
"""Ensure Fanqie upload TXT mirrors are complete before draft upload.

Checks/fixes:
- 已投稿/第N章.txt exists, or generate from 新版/第N章.md with --write
- first non-empty line is 第N章 <title>
- upload body ends with （本章完） before 作者有话说
- 作者有话说 exists, non-empty, <=300 chars, and not duplicated in body
- no wikilink / markdown heading / triple blank lines

Default is read-only check. Use --write to fix/generate with backups.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
NEW = BASE / '新版'
TXT = BASE / '已投稿'
BACKUP_ROOT = BASE / '审核记录' / '上传TXT完备门禁'

DEFAULT_NOTE = '本章技术要点与创作意图待补充。'


def clean_md_to_txt(md: str) -> str:
    s = md.replace('\r\n', '\n').replace('\r', '\n')
    s = re.sub(r'^---\n[\s\S]*?\n---\n', '', s, count=1)
    s = re.sub(r'^#\s*', '', s, flags=re.M)
    s = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', s)
    s = re.sub(r'`([^`]+)`', r'\1', s)
    s = normalize_author_note_marker(s)
    s = re.sub(r'\*\*(.*?)\*\*', r'\1', s)
    return s.strip() + '\n'


def normalize_author_note_marker(s: str) -> str:
    """Normalize common Markdown author-note headings to Fanqie marker."""
    s = re.sub(r'^\s*[-—]{3,}\s*$', '', s, flags=re.M)
    s = re.sub(r'^\s*\*\*\s*作者有话说\s*\*\*\s*$', '作者有话说：', s, flags=re.M)
    s = re.sub(r'^\s*#+\s*作者有话说\s*$', '作者有话说：', s, flags=re.M)
    s = re.sub(r'^\s*作者有话说\s*$', '作者有话说：', s, flags=re.M)
    return s


def split_txt(s: str) -> tuple[str, str]:
    if '作者有话说：' in s:
        body, note = s.split('作者有话说：', 1)
        return body.rstrip(), re.sub(r'^(作者有话说[:：]\s*)+', '', note.strip()).strip()
    return s.rstrip(), ''


def fanqie_count_body(body: str) -> int:
    lines = [x for x in body.splitlines() if x.strip()]
    title = lines[0] if lines else ''
    return len(re.sub(r'\s+', '', body)) - len(re.sub(r'\s+', '', title))


def normalize_body(ch: int, body: str) -> str:
    lines = [x.rstrip() for x in body.replace('\r\n', '\n').replace('\r', '\n').splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        raise ValueError('empty_body')
    first = lines[0].strip()
    if first.startswith('#'):
        first = re.sub(r'^#+\s*', '', first)
        lines[0] = first
    if not first.startswith(f'第{ch}章'):
        raise ValueError(f'bad_title_line:{first!r}')
    # Remove accidental trailing duplicated author marker from body.
    joined = '\n'.join(lines).rstrip()
    joined = re.sub(r'\n{3,}', '\n\n', joined)
    if not joined.rstrip().endswith('（本章完）'):
        joined = joined.rstrip() + '\n\n（本章完）'
    return joined.rstrip()


def check_one(ch: int, write: bool, note_text: str | None, backup_dir: Path) -> dict:
    txt_path = TXT / f'第{ch}章.txt'
    source = 'existing_txt'
    changed = False
    generated = False
    if txt_path.exists():
        original = txt_path.read_text(encoding='utf-8')
    else:
        md_path = NEW / f'第{ch}章.md'
        if not md_path.exists():
            return {'chapter': ch, 'ok': False, 'issues': ['missing_txt_and_source'], 'path': str(txt_path)}
        original = clean_md_to_txt(md_path.read_text(encoding='utf-8'))
        source = str(md_path)
        generated = True
        changed = True

    issues: list[str] = []
    try:
        body, note = split_txt(original)
        body2 = normalize_body(ch, body)
    except Exception as e:
        return {'chapter': ch, 'ok': False, 'issues': [str(e)], 'path': str(txt_path), 'source': source}

    if body2 != body.rstrip():
        changed = True

    if '作者有话说' in body2:
        issues.append('body_contains_author_note')
    if '[[' in body2 or ']]' in body2:
        issues.append('wikilink_residue')
    if re.search(r'^#', body2, flags=re.M):
        issues.append('markdown_heading_residue')
    if re.search(r'\n\s*\n\s*\n', body2):
        issues.append('triple_blank')

    if not note.strip():
        note = (note_text or DEFAULT_NOTE).strip()
        changed = True
        if not note_text:
            issues.append('note_uses_default')
    note = re.sub(r'^(作者有话说[:：]\\s*)+', '', note.strip()).strip()
    if len(note) > 300:
        issues.append(f'note_too_long:{len(note)}')
    if not note:
        issues.append('missing_note')

    final = body2 + '\n\n作者有话说：\n' + note + '\n'
    # Re-check final shape.
    if not body2.rstrip().endswith('（本章完）'):
        issues.append('body_not_end_with_done')
    if '作者有话说：' not in final:
        issues.append('missing_note_marker')

    ok = not issues
    if write and changed and ok:
        backup_dir.mkdir(parents=True, exist_ok=True)
        if txt_path.exists():
            shutil.copy2(txt_path, backup_dir / txt_path.name)
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        txt_path.write_text(final, encoding='utf-8')

    return {
        'chapter': ch,
        'ok': ok,
        'changed': changed,
        'written': bool(write and changed and ok),
        'generated': generated,
        'path': str(txt_path),
        'source': source,
        'fanqie_body_chars': fanqie_count_body(body2),
        'note_len': len(note),
        'issues': issues,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapter', type=int, nargs='+', required=True)
    ap.add_argument('--write', action='store_true', help='apply fixes/generate missing TXT')
    ap.add_argument('--note', default=None, help='note text to use when missing; <=300 chars')
    ap.add_argument('--report', default=None)
    args = ap.parse_args()
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = BACKUP_ROOT / f'backup_{stamp}'
    results = [check_one(ch, args.write, args.note, backup_dir) for ch in args.chapter]
    out = {'write': args.write, 'backup_dir': str(backup_dir) if args.write else None, 'results': results}
    text = json.dumps(out, ensure_ascii=False, indent=2)
    print(text)
    if args.report:
        Path(args.report).write_text(text + '\n', encoding='utf-8')
    return 0 if all(r.get('ok') for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
