#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
派稿前置闸门 submit_author_card.py  (2026-10-07)

源起事故：给 371 派扩写卡时，命令写成
    card_selfcheck.py ...; qwen_submit_chapter.py ...
用 `;` 串接 —— 自检 FAIL 了也照样派稿，等于自检形同虚设。
而该卡确实含 2 处破折号（卡内说明文字），属「卡自己命中扫描器」的同一类问题。

本脚本把「先自检、再派稿」固化为单一入口：
  自检非 0 退出 → 拒绝派稿，退出码 2，不启浏览器。

用法：
    python3 工具脚本/submit_author_card.py \
        --card <作者卡> --out <产物路径> \
        --chapter-no 371 --task-marker CH371 \
        [--chapter-url <定点返修URL>] [--take-last] [--min-chars 3400] \
        [--no-os-check] [--timeout 1800] [--log <日志路径>]

说明：
  --chapter-url 存在时走定点返修/续写（不新建会话），并自动加 --take-last。
  --no-os-check 仅用于同一会话的续写卡（OS 首轮已读过）。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
SELFCHECK = BASE / '工具脚本' / 'card_selfcheck.py'
SUBMIT = Path('/root/workspace/工具/web_agents_qwen/scripts/qwen_submit_chapter.py')
PROJECT_NAME = '写作科武纪元小说'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--card', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--chapter-no', required=True)
    ap.add_argument('--task-marker', required=True)
    ap.add_argument('--chapter-url', default=None,
                    help='定点返修/续写：回原会话，不新建')
    ap.add_argument('--take-last', action='store_true')
    ap.add_argument('--min-chars', type=int, default=3400)
    ap.add_argument('--timeout', type=int, default=1800)
    ap.add_argument('--no-os-check', action='store_true')
    ap.add_argument('--log', default=None)
    ap.add_argument('--dry-run', action='store_true', help='只自检不派稿')
    a = ap.parse_args()

    card = Path(a.card)
    if not card.exists():
        print(f'[gate] 卡不存在: {card}', file=sys.stderr)
        return 2

    # ---- 第 1 步：自检（硬闸，不过不许派）----
    sc_cmd = ['/usr/bin/python3', str(SELFCHECK), str(card)]
    if a.no_os_check:
        sc_cmd.append('--no-os-check')
    sc = subprocess.run(sc_cmd, capture_output=True, text=True,
                        cwd=str(BASE))
    print('[gate] selfcheck 输出:', sc.stdout.strip())
    if sc.stderr.strip():
        print('[gate] selfcheck 错误:', sc.stderr.strip(), file=sys.stderr)
    if sc.returncode != 0:
        print(f'[gate] REFUSED：自检未通过（exit={sc.returncode}），拒绝派稿。'
              f'请修卡后重试。', file=sys.stderr)
        return 2

    log = Path(a.log) if a.log else card.parent / f'submit_{card.stem}.log'

    cmd = ['/usr/bin/python3', str(SUBMIT),
           '--prompt-file', str(card),
           '--output', str(Path(a.out)),
           '--chapter-no', str(a.chapter_no),
           '--task-marker', a.task_marker,
           '--project-name', PROJECT_NAME,
           '--require-kb',
           '--min-chars', str(a.min_chars),
           '--timeout', str(a.timeout)]
    if a.chapter_url:
        cmd += ['--chapter-url', a.chapter_url, '--take-last']
    elif a.take_last:
        cmd += ['--take-last']

    if a.dry_run:
        print('[gate] DRY-RUN 命令:', ' '.join(cmd))
        return 0

    print('[gate] 派稿中，日志 →', log)
    with log.open('w', encoding='utf-8') as fh:
        r = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT,
                           cwd=str(BASE), timeout=a.timeout + 120)
    print(f'[gate] 派稿结束 exit={r.returncode}；日志 {log}')
    return r.returncode


if __name__ == '__main__':
    sys.exit(main())
