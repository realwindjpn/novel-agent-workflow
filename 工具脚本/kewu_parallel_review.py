#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""科武纪元 5席并行审稿脚本（Hermes 原生 CLI + ThreadPoolExecutor）。

设计裁决（2026-08-21，用户定；覆盖 2026-08-20 会议的 C1/C2 部分）：
- 保留 5 席，不合并为 3 席：省的是墙钟时间而非席位数，64席可用池足够分散。
- 一席一 provider（HARD）：primary 与各 rank fallback 均不得撞车，防「假5席」。
- 走 Hermes 原生 CLI，不用裸 HTTP：裸 urllib 会吃 Cloudflare WAF 403=1010 假阴性
  （2026-08-21 实测：裸脚本 11/14 FAIL，Hermes 原生 64/65 PASS）。
- 全文内嵌送审，禁摘要（摘要送审产假 FAIL）。
- launch_child 不用于审稿：其 launcher 只 Popen 不 wait()，子进程完成后变僵尸
  （Zs defunct），主控等死 PID 到超时。产物其实已落盘。
- 超时一次即换异模型族；同席 fallback 必须跨族。

用法：
  python3 kewu_parallel_review.py --chapter 280
  python3 kewu_parallel_review.py --chapter 280 --seats editor,reader
  python3 kewu_parallel_review.py --chapter 280 --body-path /path/to.md

验收产物：审核记录/并行审稿/第N章_YYYYMMDD_HHMMSS.json
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
OUT_DIR = BASE / '审核记录' / '并行审稿'

# ── 席位定义 ──────────────────────────────────────────────
# fallbacks: [(provider, model), ...] 按序尝试，第一个出稿即用。
# provider 全部取自 2026-08-21 Hermes 原生全池审计 PASS 名单，延迟优先且跨族。
SEATS = {
    'editor': {
        'role': '编辑席',
        'prompt': (
            "你是《科武纪元》编辑审稿席。审查以下章节全文。\n\n"
            "审查重点：大纲一致性、情节逻辑、人物一致性、节奏控制、章节衔接连续性、"
            "伏笔铺设与回收。\n\n"
            "输出格式：首行只写 PASS 或 PASS_WITH_NOTES 或 FAIL。"
            "若非 PASS，逐条列必改项并引原文片段。\n\n正文：\n{body}"
        ),
        'fallbacks': [
            # 2026-09-18 席位重校：chun/gemma 未过当轮 smoke，换 chun-grok46/grok-4.6。
            ('bmapi', 'gpt-5.6-sol'),
            ('chun-grok46', 'grok-4.6'),
        ],
    },
    'structure': {
        'role': '结构席',
        'prompt': (
            "你是《科武纪元》结构审稿席。审查以下章节全文。\n\n"
            "审查重点：章节结构完整性、场景切换合理性、信息密度分布、"
            "开篇钩子与结尾悬念、段落长度节奏、视角一致性。\n\n"
            "输出格式：首行只写 PASS 或 PASS_WITH_NOTES 或 FAIL。"
            "若非 PASS，逐条列必改项并引原文片段。\n\n正文：\n{body}"
        ),
        'fallbacks': [
            # 2026-09-18 席位重校：yezi-gemini 未过当轮 smoke，agnes 提为 primary。
            ('agnes-text', 'agnes-3.0-flash'),
            ('bytecat', 'glm-5.3'),
        ],
    },
    'science_military': {
        'role': '科学+军事顾问席',
        'prompt': (
            "你是《科武纪元》科学与军事顾问审稿席。审查以下章节全文。\n\n"
            "审查重点：物理机制自洽（信号处理、材料、星际通讯）、军事逻辑与装备可信度、"
            "遗址技术设定一致性、数值量级合理性。\n\n"
            "输出格式：首行只写 PASS 或 PASS_WITH_NOTES 或 FAIL。"
            "若非 PASS，逐条列必改项并引原文片段，给出正确参数或机制。\n\n正文：\n{body}"
        ),
        'fallbacks': [
            # 2026-09-18 席位重校：yezi-gemini 未过当轮 smoke，换 chun-grok46/grok-4.6。
            ('rsiai', 'claude-opus-5'),
            ('chun-grok46', 'grok-4.6'),
        ],
    },
    'reader': {
        'role': '读者席',
        'prompt': (
            "你是《科武纪元》读者审稿席，代表番茄小说普通读者视角。审查以下章节全文。\n\n"
            "审查重点：追读意愿、爽感与悬念、是否有解说腔/降智感、比喻是否过密、"
            "人物是否有魅力。给出追读评分（1-5 分）。\n\n"
            "输出格式：首行只写 PASS 或 PASS_WITH_NOTES 或 FAIL。"
            "次行写「追读评分：N/5」。若非 PASS，逐条列必改项并引原文片段。\n\n正文：\n{body}"
        ),
        'fallbacks': [
            # 2026-09-18 席位重校：yi-hydrogel/GLM-5.2 未过当轮 smoke，换 bytecat/glm-5.3。
            ('bytecat', 'glm-5.3'),
            ('tokeasy', 'deepseek-v4-flash'),
        ],
    },
    'deai': {
        'role': '去AI腔席',
        'prompt': (
            "你是《科武纪元》去AI腔审稿席。审查以下章节全文。\n\n"
            "审查重点（逐项扫描并引原文）：\n"
            "1. 解释腔——叙述者跳出来解释设定或人物动机\n"
            "2. 文艺腔/咏叹调——空洞抒情、无物理落点的比喻\n"
            "3. 清单腔——用排比或编号堆砌信息\n"
            "4. 「不是…而是」公式句\n"
            "5. AI 高频词与过度对称句式\n\n"
            "输出格式：首行只写 PASS 或 PASS_WITH_NOTES 或 FAIL。"
            "若非 PASS，逐条引原文并给改写建议。\n\n正文：\n{body}"
        ),
        'fallbacks': [
            # 2026-09-18 22:05 实测：nous solar-pro4:free 已 404 下架，rsiai 余额耗尽(403)，
            # 换 tokeasy/deepseek-v4-flash（当轮语义 smoke 通过，未与其他席撞 provider）。
            ('tokeasy', 'deepseek-v4-flash'),
            ('bmapi', 'gpt-5.6-sol'),
        ],
    },
}

# 每席每次尝试的超时。实测 2026-08-21：4700 字符全文 + 完整审稿报告，
# 240s 不足（5 席全 NO_OUTPUT，各自 240s primary + 240s fallback = 480s 空转）。
# 同批节点在「只回答OK」的同长度输入下 13-15s 返回，故瓶颈是报告生成而非输入长度。
TIMEOUT_PER_SEAT = 600

VERDICT_TOKENS = ('PASS_WITH_NOTES', 'FAIL', 'PASS')


def parse_verdict(content: str) -> str:
    """Extract the verdict token from model output.

    Order matters: PASS_WITH_NOTES must be matched before PASS.
    Tolerates prefixes like '结论：FAIL'.
    Also handles Hermes review-diff output (┊ review diff wrapper),
    where the actual verdict may sit after the diff header.
    """
    if not content or not content.strip():
        return 'NO_OUTPUT'
    text = content.strip()
    # Hermes review mode wraps output in a git-style diff; scan for verdict token.
    lines = text.splitlines()
    for line in lines[:30]:
        up = line.upper()
        for token in VERDICT_TOKENS:
            if token in up:
                return token
    # If output is a diff but no explicit verdict line, it is still substantive
    # review content — the model chose to annotate via diff rather than prose.
    if any(l.startswith(('┊', '+', '-', '@@', 'diff ', '---', 'a/')) for l in lines[:5]):
        return 'DIFF_FORMAT'
    return 'UNPARSED'


def call_hermes(provider: str, model: str, prompt: str, timeout: int) -> dict:
    """Invoke one seat through the Hermes native CLI.

    Hermes native is mandatory: raw HTTP to these endpoints returns
    Cloudflare 403=1010 for non-browser UAs, producing false negatives.
    """
    cmd = ['hermes', 'chat', '--provider', provider, '-m', model, '-Q', '-q', prompt]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or '').strip()
        err = (p.stderr or '').strip()
        if p.returncode == 0 and out:
            return {'ok': True, 'content': out, 'duration': round(time.time() - t0, 1)}
        return {
            'ok': False,
            'error': f'rc={p.returncode} stderr={err[:200]}' if err else f'rc={p.returncode} empty stdout',
            'duration': round(time.time() - t0, 1),
        }
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': f'TIMEOUT after {timeout}s', 'duration': round(time.time() - t0, 1)}
    except Exception as exc:  # noqa: BLE001 - report any launcher fault verbatim
        return {'ok': False, 'error': repr(exc)[:200], 'duration': round(time.time() - t0, 1)}


def run_seat(seat_name: str, seat_cfg: dict, body: str, timeout: int = TIMEOUT_PER_SEAT) -> dict:
    """Run one review seat, walking its cross-family fallback chain."""
    prompt = seat_cfg['prompt'].format(body=body)
    attempts: list[dict] = []
    for provider, model in seat_cfg['fallbacks']:
        res = call_hermes(provider, model, prompt, timeout)
        attempts.append({'provider': provider, 'model': model,
                         'ok': res['ok'], 'duration': res['duration'],
                         'error': res.get('error', '')})
        if res['ok']:
            return {
                'seat': seat_name,
                'role': seat_cfg['role'],
                'verdict': parse_verdict(res['content']),
                'content': res['content'],
                'provider': provider,
                'model': model,
                'duration_sec': res['duration'],
                'attempts': attempts,
            }
    return {
        'seat': seat_name,
        'role': seat_cfg['role'],
        'verdict': 'NO_OUTPUT',
        'content': '',
        'provider': None,
        'model': None,
        'duration_sec': sum(a['duration'] for a in attempts),
        'attempts': attempts,
        'error': 'ALL_FALLBACKS_FAILED',
    }


def verify_independence(results: dict) -> dict:
    """Assert one-seat-one-provider on the seats that actually produced output.

    Seats with no output are excluded: a missing seat is a coverage gap, not an
    independence violation. Collapsed providers mean the review is a 假N席.
    """
    used: dict[str, list[str]] = {}
    for seat, r in results.items():
        prov = r.get('provider')
        if not prov or not (r.get('content') or '').strip():
            continue
        used.setdefault(prov, []).append(seat)
    collapsed = sorted(p for p, seats in used.items() if len(seats) > 1)
    report = {
        'independent': bool(used) and not collapsed,
        'collapsed_providers': collapsed,
        'provider_to_seats': {p: sorted(s) for p, s in sorted(used.items())},
        'distinct_providers': len(used),
    }
    # Zero effective seats must never read as PASS: an all-timeout run once
    # printed 「独立性: PASS (0 个不同 provider)」, which invites a false green.
    if not used:
        report['reason'] = 'NO_EFFECTIVE_SEAT'
    elif collapsed:
        report['reason'] = 'PROVIDER_COLLAPSE'
    return report


def resolve_body_path(chapter: int, explicit: str | None) -> Path | None:
    """Find the chapter body. Explicit path wins; otherwise probe known layouts."""
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    for cand in (
        BASE / '新版' / f'第{chapter}章.md',
        BASE / '正文' / f'第{chapter}章.md',
        BASE / '新版' / f'第{chapter}章.txt',
    ):
        if cand.exists():
            return cand
    hits = sorted(BASE.rglob(f'第{chapter}章.md'))
    return hits[0] if hits else None


def main() -> int:
    ap = argparse.ArgumentParser(description='科武 5席并行审稿（Hermes 原生）')
    ap.add_argument('--chapter', type=int, required=True, help='章节号')
    ap.add_argument('--seats', default='all',
                    help='席位: all 或逗号分隔 ' + '|'.join(SEATS))
    ap.add_argument('--timeout', type=int, default=TIMEOUT_PER_SEAT, help='每席每次尝试超时秒数')
    ap.add_argument('--body-path', default=None, help='显式指定正文路径')
    args = ap.parse_args()

    body_path = resolve_body_path(args.chapter, args.body_path)
    if not body_path:
        print(json.dumps({'error': f'CHAPTER_NOT_FOUND: 第{args.chapter}章'}, ensure_ascii=False))
        return 2
    body = body_path.read_text(encoding='utf-8').strip()
    cjk = len(re.sub(r'[^\u4e00-\u9fff]', '', body))
    print(f'章节 {args.chapter}: {cjk} 净中文, {len(body)} 字符')
    print(f'正文: {body_path}')

    if args.seats == 'all':
        seat_names = list(SEATS)
    else:
        seat_names = [s.strip() for s in args.seats.split(',') if s.strip() in SEATS]
    if not seat_names:
        print(json.dumps({'error': f'NO_VALID_SEATS: {args.seats}'}, ensure_ascii=False))
        return 2

    print(f'并行派发 {len(seat_names)} 席: {", ".join(seat_names)}')
    t0 = time.time()
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=len(seat_names)) as pool:
        futures = {pool.submit(run_seat, n, SEATS[n], body, args.timeout): n
                   for n in seat_names}
        for fut in as_completed(futures):
            seat = futures[fut]
            try:
                r = fut.result()
            except Exception as exc:  # noqa: BLE001
                r = {'seat': seat, 'role': SEATS[seat]['role'], 'verdict': 'ERROR',
                     'content': '', 'provider': None, 'model': None,
                     'duration_sec': 0, 'attempts': [], 'error': repr(exc)[:200]}
            results[seat] = r
            mark = '✓' if r['verdict'].startswith('PASS') else '✗'
            print(f'  {mark} {seat:18} {r["verdict"]:16} '
                  f'[{r.get("provider") or "NONE"}/{r.get("model") or "-"}] '
                  f'{r["duration_sec"]}s')

    wall = round(time.time() - t0, 1)
    indep = verify_independence(results)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = OUT_DIR / f'第{args.chapter}章_{ts}.json'
    out_path.write_text(json.dumps({
        'chapter': args.chapter,
        'body_path': str(body_path),
        'cjk_chars': cjk,
        'timestamp': ts,
        'wall_sec': wall,
        'seats_requested': seat_names,
        'independence': indep,
        'results': results,
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    counts: dict[str, int] = {}
    for r in results.values():
        counts[r['verdict']] = counts.get(r['verdict'], 0) + 1
    print(f'\n墙钟 {wall}s（串行约需 {sum(r["duration_sec"] for r in results.values()):.0f}s）')
    print(f'裁决: {counts}')
    effective = indep['distinct_providers']
    if indep['independent']:
        indep_line = f'PASS（{effective}/{len(seat_names)} 席出稿，provider 全独立）'
    else:
        indep_line = f'FAIL [{indep.get("reason", "?")}]（{effective} 个有效 provider）'
    print(f'独立性: {indep_line}')
    if indep['collapsed_providers']:
        print(f'  撞车 provider: {indep["collapsed_providers"]}')

    missing = [s for s in seat_names if not (results.get(s, {}).get('content') or '').strip()]
    if missing:
        print(f'未出稿席位: {missing} —— 审稿不完整，不得据此判稿')
    print(f'产物: {out_path}')
    # Non-zero exit when the review is not usable, so callers cannot mistake
    # an all-timeout run for a clean pass.
    return 0 if (indep['independent'] and not missing) else 1


if __name__ == '__main__':
    raise SystemExit(main())
