#!/usr/bin/env python3
"""只重跑 G2 会议里 SEAT_FAILED(TIMEOUT) 的席位，合并回原 council JSON。

背景（2026-09-18 实测）：run_g2_council.call_hermes_model 硬编码 timeout=180s，
长 prompt 下 bytecat/glm-5.3、bmapi/gpt-5.6-sol、agnes-text/agnes-3.0-flash 三席
均 180s 超时零输出，而当轮语义 smoke 全部 PASS —— 属超时上限过窄，非节点故障。

本脚本不改已成功席位的产物，只补跑失败席，超时放宽到 --timeout（默认 600s）。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_g2_council as C  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--council-json', required=True)
    ap.add_argument('--bridge-dir', required=True)
    ap.add_argument('--timeout', type=int, default=600)
    args = ap.parse_args()

    cj = Path(args.council_json)
    d = json.loads(cj.read_text(encoding='utf-8'))
    seats = d.get('seats') or []

    bridge = Path(args.bridge_dir)
    cards = C.load_bridge_cards(bridge)
    outline = C.load_outline(C.OUTLINE_LATEST)
    cards_summary = C.summarize_cards(cards)
    outline_excerpt = C.extract_outline_excerpt(outline)

    retried = []
    for s in seats:
        if str(s.get('verdict')) != 'SEAT_FAILED':
            continue
        seat, role = s.get('seat'), s.get('role')
        provider, model = s.get('provider'), s.get('model')
        prompt = C.build_seat_prompt(seat, role, cards_summary, outline_excerpt)
        print(f'重跑 {seat} ({provider}/{model}) timeout={args.timeout}s...',
              file=sys.stderr, flush=True)
        res = C.call_hermes_model(provider, model, prompt, timeout=args.timeout)
        verdict = C.parse_verdict(res.get('stdout', ''))
        s['verdict'] = verdict
        s['ok'] = res['ok']
        s['raw'] = res['stdout']
        s['stderr'] = res.get('stderr', '')
        s['elapsed_sec'] = res['elapsed_sec']
        s['retried_with_timeout'] = args.timeout
        retried.append({'seat': seat, 'verdict': verdict,
                        'elapsed_sec': res['elapsed_sec'],
                        'raw_len': len(res.get('stdout') or '')})

    d['seats'] = seats
    d['final_verdict'] = C.aggregate_verdict([str(s.get('verdict')) for s in seats])
    d['retry_round'] = {
        'ts': datetime.now().isoformat(timespec='seconds'),
        'timeout': args.timeout,
        'retried': retried,
        'reason': 'SEAT_TIMEOUT_180S_TOO_TIGHT_FOR_LONG_PROMPT',
    }
    cj.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'RETRY_DONE', 'final_verdict': d['final_verdict'],
                      'retried': retried}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
