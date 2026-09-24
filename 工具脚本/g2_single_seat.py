#!/usr/bin/env python3
"""单席 G2 调用：一次只跑一个席位，立即独立落盘。

背景（2026-09-18 实测）：一次性重跑多席的进程在本机被 OOM 杀掉
（swap 2044/2047 满），已完成席位的输出随进程一起丢失。
改成「一席一进程一文件」，任何一席被杀都不影响其它席已落盘的结果。

用法：
    python3 g2_single_seat.py --seat 编辑/连续性 --bridge-dir ... --out-dir ...
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_g2_council as C  # noqa: E402


def slug(name: str) -> str:
    return name.replace('/', '_').replace(' ', '')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--seat', required=True, help='席名，须与 COUNCIL_SEATS 一致')
    ap.add_argument('--bridge-dir', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--timeout', type=int, default=600)
    args = ap.parse_args()

    match = [s for s in C.COUNCIL_SEATS if s[0] == args.seat]
    if not match:
        print(json.dumps({'status': 'REFUSE', 'reason': f'seat_not_registered:{args.seat}',
                          'known': [s[0] for s in C.COUNCIL_SEATS]}, ensure_ascii=False))
        return 2
    seat, role, provider, model = match[0]

    bridge = Path(args.bridge_dir)
    cards = C.load_bridge_cards(bridge)
    outline = C.load_outline(C.OUTLINE_LATEST)
    prompt = C.build_seat_prompt(seat, role, C.summarize_cards(cards),
                                 C.extract_outline_excerpt(outline))

    res = C.call_hermes_model(provider, model, prompt, timeout=args.timeout)
    verdict = C.parse_verdict(res.get('stdout', ''))

    row = {
        'seat': seat, 'role': role, 'provider': provider, 'model': model,
        'verdict': verdict, 'ok': res['ok'], 'raw': res['stdout'],
        'stderr': res.get('stderr', ''), 'elapsed_sec': res['elapsed_sec'],
        'timeout_used': args.timeout,
        'ts': datetime.now().isoformat(timespec='seconds'),
        'cards_count': len(cards),
        'bridge_dir': str(bridge),
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f'seat_{slug(seat)}.json'
    p.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'SEAT_DONE', 'seat': seat, 'verdict': verdict,
                      'elapsed_sec': res['elapsed_sec'],
                      'raw_len': len(res.get('stdout') or ''), 'path': str(p)},
                     ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
