#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G2 缺席席位补位派工（2026-09-26）

2026-09-26 首轮七席会审：bmapi 全链失败、qoder 无输出，两席 SEAT_FAILED。
缺席「结构审查」与「海外素材新鲜度」会偏科，须同族之外补位重派。
两席 prompt 与首轮完全同构（同一素材摘要、同一大纲节选、同一输出格式），
只换 provider/model，保证可比。
"""
import json, re, subprocess, sys, time
from pathlib import Path
import sys as _s; _s.path.insert(0, str(Path(__file__).parent) if 'Path' in dir() else __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from outline_canon import outline_path as _canon_path

ROOT = Path('/root/workspace/科武纪元')
OUT = ROOT / '任务运行态/20260926_kewu_selfcycle_daily/output'
OUT.mkdir(parents=True, exist_ok=True)
BRIDGE = ROOT / '自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/bus_bridge_2026-09-25'

SEATS = [
    ('结构审查补位', '结构审查（主席席替补）', 'custom:sensenova', 'glm-5.2', 400),
    ('海外新鲜度补位', '海外素材新鲜度审查（qoder席替补）', 'agnes-text', 'agnes-3.0-flash', 400),
]


def build_prompt(seat, role):
    cards = json.loads((BRIDGE / 'decision_cards.json').read_text(encoding='utf-8'))
    lines = []
    for i, c in enumerate(cards[:15], 1):
        t = c.get('title', '(无标题)')
        s = c.get('source_group', '')
        proj = c.get('mirofish_projection', {}) or {}
        fr = [r.get('force', '') for r in proj.get('force_reactions', [])][:3]
        lines.append(f"{i}. [{s}] {t} → 力量线: {', '.join(fr) if fr else '(无)'}")
    if len(cards) > 15:
        lines.append(f"... 共{len(cards)}张卡，已截取前15张")
    out = _canon_path()
    outline = out.read_text(encoding='utf-8') if out.exists() else ''
    idx = outline.find('# 归档入口')
    excerpt = (outline[:idx] if idx > 0 else outline)[:3000]
    return (f"你是G2融纲会议「{seat}」席位，角色：{role}。\n\n"
            f"## 本轮素材卡摘要\n" + '\n'.join(lines) + "\n\n"
            f"## 大纲当前状态（节选）\n{excerpt[:3000]}\n\n"
            f"请基于你的角色，对本轮素材与大纲的关系给出意见：\n"
            f"1. 是否需要修改大纲备注层？（OUTLINE_PATCH / NOTE_ONLY / NO_PATCH）\n"
            f"2. 具体建议（章号+内容，不超过3条）\n"
            f"3. 风险提示（如有）\n\n"
            f"格式：\n"
            f"VERDICT: OUTLINE_PATCH|NOTE_ONLY|NO_PATCH\n"
            f"SUGGESTIONS:\n- ...\nRISKS:\n- ...")


def main():
    results = []
    for seat, role, prov, model, to in SEATS:
        p = build_prompt(seat, role)
        (OUT / f'g2_seat_{seat}.prompt.md').write_text(p, encoding='utf-8')
        t0 = time.time()
        try:
            r = subprocess.run(['hermes', 'chat', '--provider', prov, '-m', model, '-Q', '-q', p],
                               capture_output=True, text=True, timeout=to)
            txt = (r.stdout or '').strip()
            err = (r.stderr or '').strip()
            rc = r.returncode
        except subprocess.TimeoutExpired:
            txt, err, rc = '', f'TIMEOUT {to}s', -1
        (OUT / f'g2_seat_{seat}.raw.md').write_text(txt, encoding='utf-8')
        m = re.search(r'VERDICT:\s*(OUTLINE_PATCH|NOTE_ONLY|NO_PATCH)', txt, re.I)
        v = m.group(1).upper() if m else 'SEAT_FAILED'
        results.append({'seat': seat, 'role': role, 'provider': prov, 'model': model,
                        'verdict': v, 'exit': rc, 'len': len(txt),
                        'elapsed': round(time.time() - t0, 1), 'err': err[:200]})
        print(f"{seat}: exit={rc} 裁决={v} {len(txt)}字 {round(time.time()-t0,1)}s", flush=True)
    (OUT / 'g2_substitute_seats.json').write_text(json.dumps(results, ensure_ascii=False, indent=2),
                                                  encoding='utf-8')
    ok = sum(1 for r in results if r['verdict'] != 'SEAT_FAILED')
    print(f'补位完成 {ok}/{len(results)}')


if __name__ == '__main__':
    main()
