#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
科武纪元·章节状态机门禁  chapter_state_machine.py

存在理由（2026-10-07 事故）：
    368 已发布，主控无门禁直接改正文，跑 18 轮五审后才发现，浪费一天算力。
    根因：没有机器可判的「这章能不能改」的状态机。

本脚本提供：
    - 状态定义与合法迁移表
    - can_edit(chapter)  -> 可否改写正文（HARD 门禁）
    - transition()       -> 迁移并写状态卡
    - show()             -> 打印当前状态

铁律：
    PUBLISHED 是终态。要改已发布章，必须先 --force-unpublish 显式降级
    （须在 reason 里写明依据），否则任何写操作必须拒绝。

用法:
    python3 工具脚本/chapter_state_machine.py --show 368
    python3 工具脚本/chapter_state_machine.py --can-edit 368       # exit 0=可改, 1=禁改
    python3 工具脚本/chapter_state_machine.py --transition 369 --to DRAFTING
    python3 工具脚本/chapter_state_machine.py --transition 368 --to REVISING \\
        --force-unpublish --reason "用户明确要求按 V9 重写"
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
STATE_DIR = BASE / 'wiki' / 'chapters' / 'state'
SCHEMA = 'kewu.chapter-state.v1'

# ---------- 状态定义 ----------
#
#   PLANNED ──► DRAFTING ──► IN_REVIEW ──► REVIEW_PASS ──► FINALIZED ──► PUBLISHED
#       │            │            │              │              │             │
#       └────────────┴────────────┴──────────────┴──────────────┴─────────────┘
#                              均可 ──► REVISING（回退返修）
#                              PUBLISHED ──► REVISING 需 --force-unpublish
#
S_EDITABLE = {'PLANNED', 'DRAFTING', 'IN_REVIEW', 'REVIEW_PASS', 'FINALIZED', 'REVISING'}
S_TERMINAL = {'PUBLISHED'}

TRANSITIONS = {
    'PLANNED':     {'DRAFTING'},
    'DRAFTING':    {'IN_REVIEW', 'REVISING', 'PLANNED'},
    'IN_REVIEW':   {'REVIEW_PASS', 'REVISING', 'DRAFTING'},
    'REVIEW_PASS': {'FINALIZED', 'REVISING'},
    'FINALIZED':   {'PUBLISHED', 'REVISING'},
    'PUBLISHED':   set(),          # 终态；仅 --force-unpublish 可回 REVISING
    'REVISING':    {'IN_REVIEW', 'DRAFTING', 'FINALIZED'},
}


def state_path(n: int) -> Path:
    return STATE_DIR / f'ch{n:03d}.json'


def load_state(n: int) -> dict:
    p = state_path(n)
    if not p.exists():
        return {'chapter': n, 'status': {'production': 'UNKNOWN'},
                'error': 'STATE_CARD_MISSING'}
    return json.loads(p.read_text(encoding='utf-8'))


def cur_status(n: int) -> str:
    d = load_state(n)
    return (d.get('status') or {}).get('production') or 'UNKNOWN'


def can_edit(n: int) -> tuple:
    """返回 (bool, reason)。HARD：写正文前必调。"""
    s = cur_status(n)
    if s == 'UNKNOWN':
        return (False, f'第{n}章无状态卡，先跑 build_chapter_state.py 生成')
    if s in S_TERMINAL:
        return (False, f'第{n}章={s}（终态）。改稿须先 --force-unpublish 降级并写明依据')
    if s in S_EDITABLE:
        return (True, f'第{n}章={s}，可编辑')
    return (False, f'第{n}章={s}，未识别状态，禁止编辑')


def transition(n: int, to: str, force_unpublish: bool = False,
               reason: str = None, dry: bool = False) -> dict:
    cur = cur_status(n)
    if cur == 'UNKNOWN':
        return {'ok': False, 'error': 'STATE_CARD_MISSING'}

    # 终态豁免
    if cur in S_TERMINAL:
        if not force_unpublish:
            return {'ok': False, 'error': f'{cur} 为终态，需 --force-unpublish'}
        if not reason or len(reason.strip()) < 8:
            return {'ok': False, 'error': '降级须 --reason 写明依据（≥8字）'}
        allowed = {'REVISING'}
    else:
        allowed = TRANSITIONS.get(cur, set())

    if to not in allowed:
        return {'ok': False, 'error': f'{cur} → {to} 非法迁移，允许: {sorted(allowed) or "无"}'}

    p = state_path(n)
    card = json.loads(p.read_text(encoding='utf-8'))
    card.setdefault('status', {})['production'] = to
    card.setdefault('status', {})['updated_at'] = datetime.now().astimezone().isoformat(timespec='seconds')
    card.setdefault('history', []).append({
        'from': cur, 'to': to,
        'at': datetime.now().astimezone().isoformat(timespec='seconds'),
        'reason': reason,
        'forced': bool(force_unpublish),
    })
    if not dry:
        p.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'ok': True, 'from': cur, 'to': to, 'dry': dry}


def show(n: int):
    d = load_state(n)
    if d.get('error'):
        print(d['error']); return
    ok, why = can_edit(n)
    print(f'第{n}章 | {d.get("title")} | 状态 {cur_status(n)}')
    b = d.get('body') or {}
    sha = b.get('sha256')
    print(f'  SHA  {sha[:16] if sha else "—"}  CJK {b.get("net_cjk") or "—"}')
    print(f'  可编辑: {"是" if ok else "否"} —— {why}')
    h = d.get('history') or []
    if h:
        print('  迁移历史:')
        for e in h[-5:]:
            print(f'    {e["from"]} → {e["to"]}  {e["at"][:19]}' + (f'  [{e["reason"]}]' if e.get('reason') else ''))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--show', type=int)
    ap.add_argument('--can-edit', type=int, metavar='CH')
    ap.add_argument('--transition', type=int, metavar='CH')
    ap.add_argument('--to', help='目标状态')
    ap.add_argument('--force-unpublish', action='store_true')
    ap.add_argument('--reason')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()

    if a.show:
        show(a.show); return 0

    if a.can_edit:
        ok, why = can_edit(a.can_edit)
        print(('CAN_EDIT' if ok else 'BLOCKED') + ' | ' + why)
        return 0 if ok else 1

    if a.transition:
        if not a.to:
            ap.error('--transition 需配 --to')
        r = transition(a.transition, a.to, a.force_unpublish, a.reason, a.dry)
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r['ok'] else 1

    ap.error('需 --show / --can-edit / --transition')


if __name__ == '__main__':
    sys.exit(main())
