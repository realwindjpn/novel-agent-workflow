#!/usr/bin/env python3
"""G2融纲会议真多模型脚本。

逐席调用真实模型（hermes chat -P provider -M model -Q -q prompt），
汇总各席意见，生成三态裁决（OUTLINE_PATCH / NOTE_ONLY / NO_PATCH）。

输出：G2_council_decision.md
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path('/root/workspace/科武纪元')
OUTLINE_LATEST = PROJECT / 'wiki/raw/outline/科武纪元大纲_latest.md'
DEFAULT_BRIDGE_DIR = PROJECT / '自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs'
DEFAULT_OUTPUT = PROJECT / '审核记录/G2_council_decision.md'

# 六席定义：(席名, 角色, provider, model)
COUNCIL_SEATS = [
    # 2026-08-29 换席：原六席（aiai137269/aerolink/zai/ds4pro/xiaomi）provider 已失效，
    # 实测五席全部 fallback 到同一模型，等于六席同模造假。
    # 改用 2026-08-27 用户指定白名单八模型，实测 8/8 零 fallback。
    ('主席/结构',     '结构审查', 'custom:sotamodel', 'opus-5'),
    ('编辑/连续性',   '编辑连续性审查', 'custom:anyrouter', 'claude-fable-5'),
    ('科学顾问',     '科学准确性审查', 'astrdark', 'glm-5.2'),
    ('军事制度',     '军事制度审查', 'custom:agentrouter', 'deepseekv4-pro-0813'),
    ('读者视角',     '读者体验审查', 'custom:agentrouter', 'qwen3.8-max'),
    ('海外新鲜度',   '海外素材新鲜度审查', 'grok2api-seeseed1ck', 'grok-4.6'),
]


def load_bridge_cards(bridge_dir: Path) -> list[dict]:
    """读取最新bridge_run的decision_cards.json。"""
    cards_path = bridge_dir / 'decision_cards.json'
    if not cards_path.exists():
        # 尝试找最新bridge_runs子目录
        runs_dir = bridge_dir.parent / 'bridge_runs'
        if runs_dir.exists():
            subdirs = sorted(runs_dir.iterdir(), reverse=True)
            for d in subdirs:
                cp = d / 'decision_cards.json'
                if cp.exists():
                    cards_path = cp
                    break
    if not cards_path.exists():
        return []
    return json.loads(cards_path.read_text(encoding='utf-8'))


def load_disposition_counts(bridge_dir: Path) -> dict:
    """读取disposition_counts.json（若存在）。"""
    for name in ('disposition_counts.json', 'disposition_summary.json'):
        p = bridge_dir / name
        if p.exists():
            return json.loads(p.read_text(encoding='utf-8'))
    return {}


def load_outline(outline_path: Path) -> str:
    """读取大纲latest。"""
    if not outline_path.exists():
        return ''
    return outline_path.read_text(encoding='utf-8')


def call_hermes_model(provider: str, model: str, prompt: str, timeout: int = 180) -> dict:
    """调用 hermes chat -P provider -M model -Q -q prompt，返回结果字典。"""
    cmd = [
        'hermes', 'chat',
        '--provider', provider,
        '-m', model,
        '-Q', '-q', prompt,
    ]
    t0 = time.time()
    try:
        result = subprocess.run(
            cmd, text=True, capture_output=True, timeout=timeout,
        )
        elapsed = round(time.time() - t0, 1)
        return {
            'ok': result.returncode == 0,
            'provider': provider,
            'model': model,
            'stdout': result.stdout.strip()[:4000],
            'stderr': result.stderr.strip()[:500],
            'elapsed_sec': elapsed,
        }
    except subprocess.TimeoutExpired:
        return {
            'ok': False,
            'provider': provider,
            'model': model,
            'stdout': '',
            'stderr': f'TIMEOUT ({timeout}s)',
            'elapsed_sec': timeout,
        }


def build_seat_prompt(seat_name: str, role: str, cards_summary: str, outline_excerpt: str) -> str:
    """为每个席位构建审查提示。"""
    return (
        f"你是G2融纲会议「{seat_name}」席位，角色：{role}。\n\n"
        f"## 本轮素材卡摘要\n{cards_summary}\n\n"
        f"## 大纲当前状态（节选）\n{outline_excerpt[:3000]}\n\n"
        f"请基于你的角色，对本轮素材与大纲的关系给出意见：\n"
        f"1. 是否需要修改大纲备注层？（OUTLINE_PATCH / NOTE_ONLY / NO_PATCH）\n"
        f"2. 具体建议（章号+内容，不超过3条）\n"
        f"3. 风险提示（如有）\n\n"
        f"格式：\n"
        f"VERDICT: OUTLINE_PATCH|NOTE_ONLY|NO_PATCH\n"
        f"SUGGESTIONS:\n- ...\nRISKS:\n- ..."
    )


def summarize_cards(cards: list[dict], max_cards: int = 15) -> str:
    """将decision_cards摘要为文本。"""
    lines = []
    for i, c in enumerate(cards[:max_cards], 1):
        title = c.get('title', '(无标题)')
        src = c.get('source_group', '')
        proj = c.get('mirofish_projection', {})
        reactions = proj.get('force_reactions', [])
        forces = [r.get('force', '') for r in reactions[:3]]
        lines.append(f"{i}. [{src}] {title} → 力量线: {', '.join(forces) if forces else '(无)'}")
    if len(cards) > max_cards:
        lines.append(f"... 共{len(cards)}张卡，已截取前{max_cards}张")
    return '\n'.join(lines)


def extract_outline_excerpt(outline_text: str, max_chars: int = 4000) -> str:
    """提取大纲中当前执行索引+最新摘要部分。"""
    # 取到归档入口之前
    idx = outline_text.find('# 归档入口')
    if idx > 0:
        return outline_text[:idx][:max_chars]
    return outline_text[:max_chars]


def parse_verdict(text: str) -> str:
    """从模型输出中解析裁决。

    空输出或无法解析 → SEAT_FAILED，禁止静默降级为 NO_PATCH。
    2026-08-29 修复：此前 CLI 参数写错（-P/-M 应为 --provider/-m），
    六席全部 argparse 报错退出，脚本把失败当 NO_PATCH 输出，
    导致历史所有 NO_PATCH 裁决均为假信号。
    """
    if not text or not text.strip():
        return 'SEAT_FAILED'
    m = re.search(r'VERDICT:\s*(OUTLINE_PATCH|NOTE_ONLY|NO_PATCH)', text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # fallback: 关键词出现
    t = text.upper()
    if 'OUTLINE_PATCH' in t:
        return 'OUTLINE_PATCH'
    if 'NOTE_ONLY' in t:
        return 'NOTE_ONLY'
    if 'NO_PATCH' in t:
        return 'NO_PATCH'
    return 'SEAT_FAILED'


def aggregate_verdict(verdicts: list[str]) -> str:
    """多数裁决聚合。

    HARD 门禁：过半席位失败 → COUNCIL_FAILED，不得输出可用裁决。
    """
    from collections import Counter
    failed = len([v for v in verdicts if v == 'SEAT_FAILED'])
    if failed * 2 >= len(verdicts):
        return 'COUNCIL_FAILED'
    valid = [v for v in verdicts if v != 'SEAT_FAILED']
    c = Counter(valid)
    most = c.most_common(1)[0]
    return most[0]


def main():
    ap = argparse.ArgumentParser(description='G2融纲会议真多模型脚本')
    ap.add_argument('--bridge-dir', type=Path, default=None,
                    help='bridge_run目录（含decision_cards.json）；默认取最新')
    ap.add_argument('--outline', type=Path, default=OUTLINE_LATEST)
    ap.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument('--dry-run', action='store_true', help='不调用模型，仅输出prompt预览')
    args = ap.parse_args()

    # 1. 加载bridge输出
    bridge_dir = args.bridge_dir or DEFAULT_BRIDGE_DIR
    if not bridge_dir.exists():
        # 尝试找最新子目录
        runs_dir = PROJECT / '自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs'
        if runs_dir.exists():
            subdirs = sorted(
                [d for d in runs_dir.iterdir() if d.is_dir()],
                key=lambda d: d.name, reverse=True,
            )
            for d in subdirs:
                if (d / 'decision_cards.json').exists():
                    bridge_dir = d
                    break

    cards = load_bridge_cards(bridge_dir)
    disp = load_disposition_counts(bridge_dir)
    outline_text = load_outline(args.outline)

    if not cards:
        print('WARNING: 未找到decision_cards.json，使用空素材卡', file=sys.stderr)

    cards_summary = summarize_cards(cards)
    outline_excerpt = extract_outline_excerpt(outline_text)

    # 2. 逐席调用
    results = []
    for seat_name, role, provider, model in COUNCIL_SEATS:
        prompt = build_seat_prompt(seat_name, role, cards_summary, outline_excerpt)
        if args.dry_run:
            print(f'--- {seat_name} ({provider}/{model}) ---')
            print(prompt[:500])
            print('...')
            results.append({
                'seat': seat_name, 'role': role,
                'provider': provider, 'model': model,
                'verdict': 'NO_PATCH', 'raw': '[DRY_RUN]', 'elapsed_sec': 0,
            })
            continue

        print(f'调用 {seat_name} ({provider}/{model})...', file=sys.stderr)
        res = call_hermes_model(provider, model, prompt)
        verdict = parse_verdict(res.get('stdout', ''))
        results.append({
            'seat': seat_name, 'role': role,
            'provider': provider, 'model': model,
            'verdict': verdict,
            'ok': res['ok'],
            'raw': res['stdout'],
            'stderr': res.get('stderr', ''),
            'elapsed_sec': res['elapsed_sec'],
        })

    # 3. 聚合裁决
    verdicts = [r['verdict'] for r in results]
    final_verdict = aggregate_verdict(verdicts)

    # 4. 生成报告
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = [
        f'# G2融纲会议裁决',
        f'',
        f'- 生成时间：{now}',
        f'- bridge目录：`{bridge_dir}`',
        f'- 素材卡数量：{len(cards)}',
        f'- 大纲版本：latest',
        f'',
        f'## 裁决结果',
        f'',
        f'**{final_verdict}**',
        f'',
        f'| 席位 | 角色 | Provider/Model | 裁决 | 耗时(s) |',
        f'|------|------|---------------|------|---------|',
    ]
    for r in results:
        lines.append(
            f"| {r['seat']} | {r['role']} | {r['provider']}/{r['model']} "
            f"| {r['verdict']} | {r['elapsed_sec']} |"
        )
    lines.append('')
    lines.append('## 各席意见详情')
    lines.append('')
    for r in results:
        lines.append(f"### {r['seat']} ({r['provider']}/{r['model']})")
        lines.append(f'- 裁决: {r["verdict"]}')
        lines.append(f'- 耗时: {r["elapsed_sec"]}s')
        lines.append(f'')
        lines.append(f'```')
        lines.append(r.get('raw', '(无输出)'))
        lines.append(f'```')
        lines.append('')

    # disposition_counts
    if disp:
        lines.append('## Disposition Counts')
        lines.append('')
        lines.append('```json')
        lines.append(json.dumps(disp, ensure_ascii=False, indent=2))
        lines.append('```')
        lines.append('')

    # 输出
    report = '\n'.join(lines)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding='utf-8')
    print(f'输出: {args.output}')

    # 同时输出JSON
    json_out = args.output.with_suffix('.json')
    json_out.write_text(json.dumps({
        'generated_at': now,
        'final_verdict': final_verdict,
        'bridge_dir': str(bridge_dir),
        'cards_count': len(cards),
        'seats': results,
        'disposition_counts': disp,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'JSON: {json_out}')


if __name__ == '__main__':
    main()
