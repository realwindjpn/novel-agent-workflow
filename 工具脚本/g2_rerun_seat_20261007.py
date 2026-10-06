#!/usr/bin/env python3
"""补跑单个 G2 席位，可指定大纲与 (provider, model)。

g2_single_seat.py 写死用 OUTLINE_LATEST（非 500 章重建稿）与席位表里的
(provider, model)，补跑失败席时不够用。本脚本显式指定两者。

用法：
    python3 g2_rerun_seat_20261007.py --seat 主席/结构 \
        --provider onefor --model gpt-5.6-terra \
        --outline <500章大纲> --bridge-dir <...> --out <json>
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/workspace/科武纪元/工具脚本')
import run_g2_council as C  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--seat', required=True)
    ap.add_argument('--provider', required=True)
    ap.add_argument('--model', required=True)
    ap.add_argument('--outline', required=True)
    ap.add_argument('--bridge-dir', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--timeout', type=int, default=600)
    a = ap.parse_args()

    roles = {s[0]: s[1] for s in C.COUNCIL_SEATS}
    role = roles.get(a.seat, '审查')

    cards = C.load_bridge_cards(Path(a.bridge_dir))
    outline = Path(a.outline).read_text(encoding='utf-8')
    excerpt = (C.extract_outline_excerpt(outline)
               if hasattr(C, 'extract_outline_excerpt') else outline[:20000])
    prompt = C.build_seat_prompt(a.seat, role, C.summarize_cards(cards), excerpt)

    res = C.call_direct_model(a.provider, a.model, prompt, timeout=a.timeout)
    raw = res.get('stdout') or ''
    row = {
        'seat': a.seat, 'role': role, 'provider': a.provider, 'model': a.model,
        'verdict': C.parse_verdict(raw), 'ok': res['ok'], 'raw': raw,
        'stderr': res.get('stderr', ''), 'elapsed_sec': res['elapsed_sec'],
        'ts': datetime.now().isoformat(timespec='seconds'),
        'cards_count': len(cards), 'bridge_dir': a.bridge_dir,
    }
    p = Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'SEAT_DONE', 'seat': a.seat,
                      'verdict': row['verdict'], 'elapsed_sec': res['elapsed_sec'],
                      'raw_len': len(raw), 'path': str(p)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
