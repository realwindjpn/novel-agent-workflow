#!/usr/bin/env python3
"""番茄新章节草稿版发布计划生成器

只做本地计划/草稿输入校验，不登录、不提交、不发布。
后续浏览器自动化应停在“保存为草稿”，最终人工点提交。

用法：
  python3 fanqie_new_chapter_draft_plan.py --chapters 73 74 --project-dir /root/workspace/科武纪元
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

PROJECT = Path('/root/workspace/科武纪元')


def fanqie_count(text: str, title: str) -> int:
    return len(re.sub(r'\s+', '', text)) - len(re.sub(r'\s+', '', title))


def split_note(text: str) -> tuple[str, str]:
    marker = '（本章完）'
    idx = text.find(marker)
    if idx < 0:
        return text, ''
    end = idx + len(marker)
    body = text[:end]
    note = text[end:].strip()
    return body, note


def validate_chapter(project_dir: Path, n: int) -> dict:
    path = project_dir / '已投稿' / f'第{n}章.txt'
    if not path.exists():
        return {'chapter': n, 'ok': False, 'error': f'缺文件: {path}'}
    text = path.read_text(encoding='utf-8', errors='ignore')
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = lines[0] if lines else ''
    body, note = split_note(text)
    issues = []
    if not title.startswith(f'第{n}章'):
        issues.append('首行标题章节号不匹配')
    if '（本章完）' not in text:
        issues.append('缺（本章完）')
    if not note:
        issues.append('缺作者有话说；未上传审核稿需加在本章完后')
    elif len(re.sub(r'\s+', '', note)) > 300:
        issues.append('作者有话说超过300字')
    if '[[' in text or ']]' in text:
        issues.append('含wikilink')
    return {
        'chapter': n,
        'ok': not issues,
        'file': str(path),
        'title': title,
        'fanqie_chars': fanqie_count(body, title),
        'has_author_note': bool(note),
        'author_note_chars': len(re.sub(r'\s+', '', note)) if note else 0,
        'issues': issues,
        'automation_boundary': '可自动新建章节/选分卷/填标题编号/粘贴正文/保存草稿；禁止自动发布，最终人工提交。',
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapters', nargs='+', type=int, required=True)
    ap.add_argument('--project-dir', default=str(PROJECT))
    args = ap.parse_args()
    project_dir = Path(args.project_dir)
    rows = [validate_chapter(project_dir, n) for n in args.chapters]
    out_dir = project_dir / '审核记录' / '草稿发布计划'
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = out_dir / f'新章节草稿发布计划_{stamp}.json'
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': all(r.get('ok') for r in rows), 'output': str(out), 'rows': rows}, ensure_ascii=False))


if __name__ == '__main__':
    main()
