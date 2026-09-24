#!/usr/bin/env python3
"""为补偿轮 331/332 跑 G2 融纲四席（跨 family/跨节点），产物落 <task>/output/g2_seats/。

席位（2026-09-16 当轮实测活口，四节点互不相同）：
  主席/结构   custom:rsiai        claude-opus-5
  编辑/连续性 custom:yezi-gemini  gemini-3.6-flash
  读者视角    custom:chun         google/gemma-4-31b-it
  海外新鲜度  nous                ling-3.0-flash-fin:free
"""
from __future__ import annotations
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, '/root/workspace/科武纪元/工具脚本')
TASK = Path('/root/workspace/科武纪元/任务运行态/20260916_kewu_selfcycle_daily_331332')
BRIDGE = TASK / 'bridge_run'
SEATS_DIR = TASK / 'output' / 'g2_seats'
OUTLINE = Path('/root/workspace/科武纪元/wiki/raw/outline/科武纪元大纲_latest.md')

SEATS = [
    ('seat_claude',   '主席/结构审查',   'custom:rsiai',       'claude-opus-5'),
    ('seat_gemini',   '编辑/连续性审查', 'custom:yezi-gemini', 'gemini-3.6-flash'),
    ('seat_gemma',    '读者体验审查',    'custom:chun',        'google/gemma-4-31b-it'),
    ('seat_nous',     '海外素材新鲜度',  'nous',               'ling-3.0-flash-fin:free'),
]


def build_prompt(cards_summary: str, outline_excerpt: str) -> str:
    return f"""你是《科武纪元》G2 融纲会议的独立席位。本次会议审查**今日采集的时事素材**对**全书整体大纲**（主线、世界设定、科学机制、制度冲突、卷间因果、伏笔回收）是否有优化或补充价值。

【硬性口径】
- 你的评估对象是**全书大纲**，不是某两章。不得以「素材与某章无关」为由归档，也不得因素材缺少当前章参数就阻断。
- 对每条素材给出处置：OUTLINE_PATCH（需改大纲）/ CHAPTER_PREP_ONLY（只作下章准备素材）/ NOTE_ONLY（仅备注）/ ARCHIVE_WITH_REASON（归档并给理由）/ NO_PATCH（无需动作）。
- 若建议 OUTLINE_PATCH，必须给出：要改的大纲段落原文、改法、以及与既有卷间因果是否冲突。

【今日素材卡（节选）】
{cards_summary}

【全书大纲（节选）】
{outline_excerpt}

【输出格式（严格遵守，首行必须是 VERDICT）】
VERDICT: OUTLINE_PATCH 或 CHAPTER_PREP_ONLY 或 NOTE_ONLY（三选一，作为总结论）
然后分点给出：主结论理由 / 需要 OUTLINE_PATCH 的条目（如无写「无」）/ 建议随附到下章准备的条目 / 归档且有理由的条目。
"""


def main() -> int:
    import run_g2_council as C  # noqa: E402

    SEATS_DIR.mkdir(parents=True, exist_ok=True)
    cards = C.load_bridge_cards(BRIDGE)
    disp = C.load_disposition_counts(BRIDGE)
    summary = C.summarize_cards(cards, max_cards=15) if hasattr(C, 'summarize_cards') else json.dumps(cards[:15], ensure_ascii=False)
    outline = OUTLINE.read_text(encoding='utf-8')
    excerpt = C.extract_outline_excerpt(outline, 4000) if hasattr(C, 'extract_outline_excerpt') else outline[:4000]
    prompt = build_prompt(summary, excerpt)
    (SEATS_DIR / 'G2_SEAT_PROMPT.md').write_text(prompt, encoding='utf-8')

    results = []
    for seat, role, provider, model in SEATS:
        t0 = time.time()
        cp = subprocess.run(['hermes', 'chat', '--provider', provider, '-m', model, '-Q', '-q', prompt],
                            capture_output=True, text=True, timeout=900)
        out = (cp.stdout or '').strip()
        el = round(time.time() - t0, 1)
        if not out or len(out) < 40:
            (SEATS_DIR / f'{seat}.fail.log').write_text((cp.stderr or '')[-800:], encoding='utf-8')
            results.append({'seat': seat, 'role': role, 'provider': provider, 'model': model,
                            'status': 'FAIL', 'elapsed_sec': el, 'bytes': len(out)})
            print(f'FAIL {seat} {provider}/{model} {el}s', flush=True)
            continue
        p = SEATS_DIR / f'{seat}.md'
        p.write_text(out, encoding='utf-8')
        first = out.splitlines()[0][:80]
        results.append({'seat': seat, 'role': role, 'provider': provider, 'model': model,
                        'status': 'OK', 'elapsed_sec': el, 'bytes': len(out.encode()),
                        'first_line': first, 'path': str(p)})
        print(f'OK {seat} {provider}/{model} {el}s {len(out)}字 | {first}', flush=True)

    (SEATS_DIR / 'seats_result.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    (SEATS_DIR / 'disposition_counts.json').write_text(json.dumps(disp, ensure_ascii=False, indent=2), encoding='utf-8')
    ok = [r for r in results if r['status'] == 'OK']
    print(f'DONE seats_ok={len(ok)}/{len(SEATS)}', flush=True)
    return 0 if len(ok) >= 3 else 1


if __name__ == '__main__':
    raise SystemExit(main())
