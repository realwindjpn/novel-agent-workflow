#!/usr/bin/env python3
"""DEAI确定性扫描前置门禁。

读取候选稿（--chapter N 或 --file path），
调用 kewu_deai_hard_gate_scan.py 扫描，
non_pass>0 则阻断输出FAIL+行号+模式，
non_pass==0 输出 DEAI_GATE_PASS。

用法：
  python3 run_deai_gate_before_review.py --chapter 163
  python3 run_deai_gate_before_review.py --file /path/to/file.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT = Path('/root/workspace/科武纪元')
NEW_VER_DIR = PROJECT / '新版'
UPLOAD_DIR = PROJECT / '已投稿'

# 导入扫描模块
sys.path.insert(0, str(PROJECT / '工具脚本'))
from kewu_deai_hard_gate_scan import scan_file, WEIGHTS
from humanity_precard import default_card_path, validate_card


def resolve_file(chapter: int | None, file_path: str | None) -> Path:
    """根据章号或文件路径解析候选稿。"""
    if file_path:
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f'文件不存在: {p}')
        return p
    if chapter is not None:
        # 优先新版/
        p = NEW_VER_DIR / f'第{chapter}章.md'
        if p.exists():
            return p
        # 回退已投稿/
        p = UPLOAD_DIR / f'第{chapter}章.txt'
        if p.exists():
            return p
        raise FileNotFoundError(f'第{chapter}章 未在新版/或已投稿/中找到')
    raise ValueError('必须指定 --chapter 或 --file')


def main():
    ap = argparse.ArgumentParser(description='DEAI确定性扫描前置门禁')
    ap.add_argument('--chapter', type=int, default=None, help='章号')
    ap.add_argument('--file', type=str, default=None, help='直接指定文件路径')
    ap.add_argument('--humanity-card', type=str, default=None, help='人味前置卡 JSON；默认候选同目录同名 .humanity.json')
    args = ap.parse_args()

    target = resolve_file(args.chapter, args.file)
    humanity_card = Path(args.humanity_card) if args.humanity_card else default_card_path(target)
    humanity = validate_card(humanity_card, target)
    if humanity['status'] != 'PASS':
        print('HUMANITY_PRECARD_BLOCKED')
        print(f'card: {humanity_card}')
        for error in humanity['errors']:
            print(f'  - {error}')
        return 2
    result = scan_file(target)

    verdict = result['verdict']
    hits = result.get('hits', [])
    hard_hits = [h for h in hits if h['type'].endswith('_HARD')]
    hard_count = len(hard_hits)
    score = result.get('score', 0)

    if hard_count > 0 or verdict == 'FAIL_HARD':
        # 阻断
        print('DEAI_GATE_FAIL')
        print(f'verdict: {verdict}')
        print(f'hard_count: {hard_count}')
        print(f'score: {score}')
        print(f'file: {target}')
        print()
        print('命中模式:')
        for h in hard_hits:
            print(f'  行{h["line"]}: [{h["type"]}] {h["text"][:120]}')
        # 也输出软风险
        soft_hits = [h for h in hits if not h['type'].endswith('_HARD')]
        if soft_hits:
            print(f'\n软风险({len(soft_hits)}条):')
            for h in soft_hits[:10]:
                print(f'  行{h["line"]}: [{h["type"]}] {h["text"][:120]}')
        sys.exit(1)
    else:
        print('DEAI_GATE_PASS')
        print(f'verdict: {verdict}')
        print(f'score: {score}')
        print(f'file: {target}')
        sys.exit(0)


if __name__ == '__main__':
    raise SystemExit(main())
