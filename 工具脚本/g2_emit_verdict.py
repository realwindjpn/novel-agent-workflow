#!/usr/bin/env python3
"""把 run_g2_council 的会议 JSON 转成 dispatcher 期望的 output/G2_verdict.json。

dispatcher._v_g2 硬要求：verdict 非空、target_chapters 为严格连号双章、g3_gate == 'ALLOW'。
本脚本只做确定性转换 + 门禁映射，不代替任何席位裁决。

映射规则（对齐 kewu-selfcycle-model-roster P0）：
  OUTLINE_PATCH / NOTE_ONLY / CHAPTER_PREP_ONLY / NO_PATCH → g3_gate=ALLOW
  COUNCIL_FAILED / SEAT_FAILED / 过半席失败            → g3_gate=BLOCK（写盘但不放行）
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

CST = timezone(timedelta(hours=8))
ALLOW_VERDICTS = {'OUTLINE_PATCH', 'NOTE_ONLY', 'CHAPTER_PREP_ONLY', 'NO_PATCH'}


def latest_seed_chapters(task_dir: Path) -> list[int]:
    led = task_dir / 'transitions.jsonl'
    last: list[int] = []
    if not led.exists():
        return last
    for line in led.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get('type') == 'DAILY_SEED':
            chs = [int(c) for c in (row.get('chapters') or [])]
            if len(chs) == 2:
                last = chs
    return last


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--task-dir', required=True)
    ap.add_argument('--council-json', required=True,
                    help='run_g2_council.py 输出的 *.json')
    args = ap.parse_args()

    task = Path(args.task_dir)
    council_path = Path(args.council_json)
    council = json.loads(council_path.read_text(encoding='utf-8'))

    chapters = latest_seed_chapters(task)
    if len(chapters) != 2 or chapters[1] != chapters[0] + 1:
        print(json.dumps({'status': 'REFUSE', 'reason': f'seed_chapters_invalid:{chapters}'},
                         ensure_ascii=False))
        return 2

    seats = council.get('seats') or []
    final = str(council.get('final_verdict') or '')
    failed = [s for s in seats if str(s.get('verdict')) == 'SEAT_FAILED']
    live = [s for s in seats if str(s.get('verdict')) != 'SEAT_FAILED']

    if final in ALLOW_VERDICTS and len(live) > len(failed):
        gate = 'ALLOW'
    else:
        gate = 'BLOCK'

    out = {
        'verdict': final or 'COUNCIL_FAILED',
        'g3_gate': gate,
        'target_chapters': chapters,
        'generated_at': datetime.now(CST).isoformat(timespec='seconds'),
        'council_json': str(council_path),
        'council_sha256': hashlib.sha256(council_path.read_bytes()).hexdigest(),
        'cards_count': council.get('cards_count'),
        'bridge_dir': council.get('bridge_dir'),
        'seats': [
            {
                'seat': s.get('seat'),
                'role': s.get('role'),
                'provider': s.get('provider'),
                'model': s.get('model'),
                'verdict': s.get('verdict'),
                'elapsed_sec': s.get('elapsed_sec'),
                'raw_len': len(str(s.get('raw') or '')),
            }
            for s in seats
        ],
        'seat_stats': {
            'total': len(seats),
            'live': len(live),
            'failed': len(failed),
        },
        'gate_owner': 'g2_emit_verdict.py',
        'note': ('确定性转换：裁决由 run_g2_council 六席产出，本脚本只做门禁映射与 SHA 绑定。'),
    }

    out_dir = task / 'output'
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / 'G2_verdict.json'
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'G2_VERDICT_WRITTEN', 'path': str(p),
                      'verdict': out['verdict'], 'g3_gate': gate,
                      'target_chapters': chapters,
                      'seat_stats': out['seat_stats']}, ensure_ascii=False))
    return 0 if gate == 'ALLOW' else 3


if __name__ == '__main__':
    raise SystemExit(main())
