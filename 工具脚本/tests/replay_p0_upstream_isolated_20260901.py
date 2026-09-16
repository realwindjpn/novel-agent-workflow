#!/usr/bin/env python3
"""端到端隔离回放（2026-09-01 P0）。

与聚焦测试的区别：这里真的 fork 子进程跑采集器 CLI，验证
  1. 游标文件跨进程 6 轮持续推进（不归零、不重复账号槽）
  2. 补充采集器 → evaluate_run 的 supplement 入账在整链上成立（主0补N→计N）
全程写隔离 tmpdir，真实素材总线与生产游标行数/内容必须零变化。

用法：python3 replay_p0_upstream_isolated_20260901.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
RADAR = SCRIPT_DIR / 'platform_radar_v2_20260622.py'
SIDECAR = Path('/root/.hermes/scripts/kewu_platform_radar_sensenova_sidecar.py')
REAL_BUS = Path('/root/workspace/素材总线/kewu/material_cards.jsonl')
PROD_CURSOR = Path('/root/workspace/科武纪元/学习记录/平台号观点雷达/kol_coverage_cursor.json')

RESULT: dict = {'checks': [], 'metrics': {}}


def check(label: str, cond: bool, detail: str = ''):
    RESULT['checks'].append({'label': label, 'pass': bool(cond), 'detail': detail})
    print(f'  {"PASS" if cond else "FAIL"}  {label}' + (f': {detail}' if detail and not cond else ''))


def digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except Exception:
        return 'ABSENT'


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sidecar = load('sidecar_replay', SIDECAR)
BUS_BEFORE = sidecar.bus_line_count(REAL_BUS)
BUS_SHA_BEFORE = digest(REAL_BUS)
PROD_CURSOR_SHA_BEFORE = digest(PROD_CURSOR)

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)

    # ── 1. 跨进程 6 轮游标推进（真 subprocess，--dry-run-mirofish 免联网后段）──
    print('\n=== 1. 跨进程 6 轮 coverage 游标推进 ===')
    cursor_path = tmp / 'replay_cursor.json'
    rounds: list[dict] = []
    for round_no in range(6):
        out_dir = tmp / f'run{round_no}'
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable, str(RADAR), '--coverage-sweep', '--max-queries', '9',
            '--coverage-cursor', str(cursor_path), '--out-dir', str(out_dir),
            '--timeout-sec', '2', '--max-runtime-sec', '20',
            '--dry-run-mirofish', '--disable-social-cdp',
        ]
        proc = subprocess.run(cmd, cwd='/root/workspace', capture_output=True,
                              text=True, timeout=300)
        line = next((ln for ln in proc.stdout.splitlines()
                     if ln.startswith('[coverage_cursor]')), '')
        after = json.loads(cursor_path.read_text(encoding='utf-8')).get('domains', {})
        discovery = json.loads((out_dir / 'platform_discovery.json').read_text(encoding='utf-8'))
        stats = discovery.get('stats', {})
        planned = stats.get('query_plan_accounts') or stats.get('queried_accounts')
        rounds.append({
            'round': round_no, 'rc': proc.returncode,
            'cursor_after': after,
            'queried_accounts': stats.get('queried_accounts'),
            'queried_domains': stats.get('queried_domains'),
            'account_names': sorted(stats.get('queried_account_names') or []),
            'cursor_log': line[:200],
        })
        check(f'第{round_no + 1}轮 exit 0', proc.returncode == 0,
              proc.stderr[-300:])
        check(f'第{round_no + 1}轮打印游标 before/after', bool(line), proc.stdout[-200:])

    cursors = [r['cursor_after'] for r in rounds]
    check('每轮游标都落盘', all(isinstance(c, dict) and c for c in cursors), str(cursors[:2]))
    check('游标跨进程发生推进（相邻轮不同）',
          any(cursors[i] != cursors[i + 1] for i in range(len(cursors) - 1)), str(cursors))
    check('第6轮游标非全零（未归零）', any(int(v) > 0 for v in cursors[-1].values()), str(cursors[-1]))

    # 回放带运行预算截断，单轮实查条数可能少于 9，所以这里的不变量不是「并集≥40」
    # （那条在聚焦测试的 plan 层验），而是「并集必须大于任一单轮」——旧行为下每轮
    # 固定同一批 index0 账号，并集恒等于单轮，这条会 FAIL。
    name_sets = [set(r['account_names']) for r in rounds if r['account_names']]
    if name_sets:
        union = set().union(*name_sets)
        max_single = max(len(s) for s in name_sets)
        check(f'6 轮实查账号并集 {len(union)} > 单轮最大 {max_single}（旧行为下相等）',
              len(union) > max_single, str(sorted(union)))
        check('相邻轮实查账号不完全相同',
              any(name_sets[i] != name_sets[i + 1] for i in range(len(name_sets) - 1)),
              str([sorted(s) for s in name_sets]))
        RESULT['metrics']['replay_union_queried_names'] = len(union)
        RESULT['metrics']['replay_max_single_round_names'] = max_single
        RESULT['metrics']['replay_union_list'] = sorted(union)
    RESULT['metrics']['replay_rounds'] = rounds

    # ── 2. 主0补N → evaluate 计 N（隔离总线）──
    print('\n=== 2. 主0补N → evaluate 入账 N（隔离总线）===')
    iso_bus = tmp / 'iso_bus.jsonl'
    iso_bus.parent.mkdir(parents=True, exist_ok=True)
    iso_bus.write_text('', encoding='utf-8')
    run_dir = tmp / 'acct_run'
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / 'platform_discovery.json').write_text(json.dumps({
        'items': [], 'stats': {
            'sidecar_health': 'HEALTHY', 'queried_domains': 9, 'queried_accounts': 9,
            'domains_with_results': 9, 'body_fetched': 4, 'excerpt_only': 0,
            'skipped_non_article': 0,
            'hotspot_recall': {'fresh_dated_count': 1, 'date_unknown_ratio': 0.0,
                               'ai_science_hotspot_count': 1, 'dynamic_entity_count': 1},
        }}, ensure_ascii=False), encoding='utf-8')
    (run_dir / 'platform_mirofish_feed_package.json').write_text(
        json.dumps({'total_cards': 0, 'cards': []}, ensure_ascii=False), encoding='utf-8')

    bus_before_iso = sidecar.bus_line_count(iso_bus)
    with iso_bus.open('a', encoding='utf-8') as fh:
        for i in range(4):
            fh.write(json.dumps({'url': f'https://replay.example/{i}'}, ensure_ascii=False) + '\n')
    event = sidecar.evaluate_run(
        run_dir, 0, sidecar.now(), '', '',
        supplement_stats={'weibo': {'exit': 0, 'stdout_tail': '入库卡 4'}},
        bus_lines_before=bus_before_iso, bus_path=iso_bus,
        zero_streak_path=tmp / 'iso_streak.json')
    sup = event.get('supplement') or {}
    check('supplement 显式入账', event['policy']['supplement_accounted_in_evaluate'] is True)
    check('主线 0', sup.get('mainline_new_cards') == 0, str(sup.get('mainline_new_cards')))
    check('补充 4', sup.get('supplement_new_cards') == 4, str(sup.get('supplement_new_cards')))
    check('总新增 4（主0补N计N）', event.get('total_new_cards_unique') == 4,
          str(event.get('total_new_cards_unique')))
    check('bus 增量 4', sup.get('bus_delta') == 4, str(sup.get('bus_delta')))
    RESULT['metrics']['replay_total_new_cards'] = event.get('total_new_cards_unique')
    RESULT['metrics']['replay_event_status'] = event['status']

# ── 3. 隔离性 ──
print('\n=== 3. 隔离性：未写真实素材总线 / 生产游标 ===')
check('真实总线行数未变', sidecar.bus_line_count(REAL_BUS) == BUS_BEFORE,
      f'{BUS_BEFORE} -> {sidecar.bus_line_count(REAL_BUS)}')
check('真实总线 sha 未变', digest(REAL_BUS) == BUS_SHA_BEFORE)
check('生产游标 sha 未变', digest(PROD_CURSOR) == PROD_CURSOR_SHA_BEFORE,
      f'{PROD_CURSOR_SHA_BEFORE} -> {digest(PROD_CURSOR)}')
RESULT['metrics']['real_bus_lines'] = BUS_BEFORE
RESULT['metrics']['real_bus_sha16'] = BUS_SHA_BEFORE
RESULT['metrics']['prod_cursor_sha16'] = PROD_CURSOR_SHA_BEFORE

failed = [c['label'] for c in RESULT['checks'] if not c['pass']]
RESULT['pass'] = sum(1 for c in RESULT['checks'] if c['pass'])
RESULT['fail'] = len(failed)
print('\n' + '=' * 46)
print(f'REPLAY PASS={RESULT["pass"]} FAIL={RESULT["fail"]}')
print('metrics=' + json.dumps(RESULT['metrics'], ensure_ascii=False, sort_keys=True)[:1200])
out = Path(__file__).resolve().parent / 'replay_p0_upstream_20260901_result.json'
out.write_text(json.dumps(RESULT, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'result_json={out}')
print('=' * 46)
raise SystemExit(1 if failed else 0)
