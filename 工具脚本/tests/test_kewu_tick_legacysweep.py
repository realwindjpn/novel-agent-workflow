#!/usr/bin/env python3
"""kewu_daily_control_tick 跨日遗留链回收 (legacy sweep v2) 独立测试.

覆盖 (红/绿证据, 全部真实运行, 非静态猜测):
  RED-1  : 备份脚本 (bak.20260908_legacysweep, 旧逻辑) 在真实夹具上运行,
           3 日前 authorB 已验证包不被消费 → ledger 零变化 (旧逻辑只看前一日).
  GREEN-1: 新脚本同夹具运行, 3 日前 authorB PENDING + 真实产物 VERIFIED
           → 被消费, 追加 TRANSITION_ACK authorB + PENDING reviewB, 无 FAIL 噪声.
  GREEN-2: 全部旧包无 PENDING (全闭环 / 无 ledger) 时 tick 零副作用:
           无新增文件, 既有 ledger 行数不变, 无 FAIL, 无 TRANSITION 写入.
  UNIT   : iter_legacy_task_dirs 排序 / 跳过当日 / 跳过无效名 / 跳过超龄.

运行: python3 test_kewu_tick_legacysweep.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SCRIPTS = '/root/.hermes/scripts'
CTRL = Path(SCRIPTS) / 'kewu_daily_control_tick.py'
BAK = Path(SCRIPTS) / 'kewu_daily_control_tick.py.bak.20260908_legacysweep'
PY = sys.executable

# NOW 固定: 今日 = 2026-09-06; 3 日前包 = 20260903; 10 日窗 floor = 08-27
NOW = '2026-09-06T14:05:00+08:00'
TODAY_DIR = '20260906_kewu_selfcycle_daily'
LEGACY_DIR = '20260903_kewu_selfcycle_daily'


def make_env(root: Path) -> dict:
    proj, tasks = root / 'proj', root / 'tasks'
    sub_, new = proj / '已投稿', proj / '新版'
    for p in (sub_, new, tasks):
        p.mkdir(parents=True, exist_ok=True)
    outline = proj / 'outline.md'
    if not outline.exists():
        outline.write_text('\n'.join(
            f'第{i}章 | 第一卷·测试 | 标题{i} | 种子{i} | 伏笔{i} | 3100'
            for i in range(1, 30)), encoding='utf-8')
    env = os.environ.copy()
    env.update({
        'KEWU_DAILY_PROJECT_ROOT': str(proj),
        'KEWU_DAILY_TASK_ROOT': str(tasks),
        'KEWU_DAILY_OUTLINE': str(outline),
        'KEWU_DAILY_SUBMITTED_DIR': str(sub_),
        'KEWU_DAILY_NEWTEXT_DIR': str(new),
        'KEWU_DAILY_NOW': NOW,
        'KEWU_DAILY_ACTION_QUEUE': str(root / 'queue.jsonl'),
        'KEWU_DAILY_EXEC_DB': str(root / 'executions.db'),
        'KEWU_DAILY_DRAFT_LISTING': str(root / 'draft_listing.json'),
        'KEWU_DAILY_STALL_MINUTES': '0',
    })
    # 预建今日包 output, 避免 tick 的 mkdir 造成夹具差异
    (tasks / TODAY_DIR / 'output').mkdir(parents=True, exist_ok=True)
    return env


def ledger_rows(task_dir: Path) -> list[dict]:
    p = task_dir / 'transitions.jsonl'
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()
            if x.strip()]


def write_ledger(task_dir: Path, rows: list[dict]) -> None:
    task_dir.mkdir(parents=True, exist_ok=True)
    with (task_dir / 'transitions.jsonl').open('a', encoding='utf-8') as fh:
        for i, r in enumerate(rows, 1):
            r = dict(r)
            r['seq'] = i
            r.setdefault('ts', f'{NOW}T00:00:00+08:00')
            fh.write(json.dumps(r, ensure_ascii=False) + '\n')


def mk_legacy_authorb_pkg(tasks: Path) -> Path:
    """3 日前包: seed..G4B 全 ACK, authorB PENDING, 真实作者稿已就绪 (VERIFIED 条件齐备)."""
    pkg = tasks / LEGACY_DIR
    (pkg / 'output').mkdir(parents=True, exist_ok=True)
    rows = [
        {'type': 'DAILY_SEED', 'day': '2026-09-03', 'chapters': [317, 318],
         'frontier_source': 'dynamic', 'frontier': 'X',
         'outline_anchors': ['a', 'b']},
        {'type': 'CHAPTER_SLOT', 'slot': 'A', 'chapter': 317},
        {'type': 'CHAPTER_SLOT', 'slot': 'B', 'chapter': 318},
    ]
    for t in ['seed', 'G1', 'G2', 'G3', 'G4A', 'authorA', 'reviewA',
              'closeA', 'G4B']:
        rows.append({'type': 'TRANSITION_ACK', 'transition': t,
                     'day': '2026-09-03'})
    write_ledger(pkg, rows)
    (pkg / 'output' / 'qwen_318_r1.md').write_text(
        '第318章 测试章\n' + '中' * 3100, encoding='utf-8')
    return pkg


def mk_closed_pkg(tasks: Path, day8: str) -> Path:
    """已闭环包: 12 环全 ACK → current_transition 为 None, 不可消费."""
    pkg = tasks / f'{day8}_kewu_selfcycle_daily'
    (pkg / 'output').mkdir(parents=True, exist_ok=True)
    rows = [
        {'type': 'DAILY_SEED', 'day': f'{day8[:4]}-{day8[4:6]}-{day8[6:]}',
         'chapters': [315, 316], 'frontier_source': 'dynamic', 'frontier': 'Y',
         'outline_anchors': ['a', 'b']},
        {'type': 'CHAPTER_SLOT', 'slot': 'A', 'chapter': 315},
        {'type': 'CHAPTER_SLOT', 'slot': 'B', 'chapter': 316},
    ]
    for t in ['seed', 'G1', 'G2', 'G3', 'G4A', 'authorA', 'reviewA',
              'closeA', 'G4B', 'authorB', 'reviewB', 'closeB']:
        rows.append({'type': 'TRANSITION_ACK', 'transition': t,
                     'day': f'{day8[:4]}-{day8[4:6]}-{day8[6:]}'})
    write_ledger(pkg, rows)
    return pkg


def run_tick(script: Path, env: dict) -> tuple[int, str]:
    cp = subprocess.run([PY, str(script)], env=env, text=True,
                        capture_output=True, timeout=180)
    return cp.returncode, (cp.stdout or '').strip()


def snapshot_tree(root: Path) -> dict[str, int]:
    out = {}
    for p in sorted(root.rglob('*')):
        if p.is_file():
            out[str(p.relative_to(root))] = p.stat().st_size
    return out


def red_bak_ignores_legacy() -> dict[str, bool]:
    checks: dict[str, bool] = {}
    # 静态: 备份文件确为旧逻辑 (无 legacy 扫描函数), 防止误用新文件充红证
    src = BAK.read_text(encoding='utf-8')
    checks['red_static_is_old_logic'] = (
        'iter_legacy_task_dirs' not in src
        and 'LEGACY_DAY_CHAIN_CONSUMING' not in src)
    with tempfile.TemporaryDirectory(prefix='kewu-red-') as raw:
        root = Path(raw)
        env = make_env(root)
        legacy = mk_legacy_authorb_pkg(root / 'tasks')
        before = ledger_rows(legacy)
        rc, out = run_tick(BAK, env)
        after = ledger_rows(legacy)
        checks['red_rc_0'] = rc == 0
        checks['red_no_consume_silent'] = out == ''
        checks['red_ledger_unchanged'] = (len(after) == len(before)
                                          and not any(
            r.get('type') == 'TRANSITION_ACK' and r.get('transition') == 'authorB'
            for r in after[len(before):]))
        checks['red_no_fail_written'] = not any(
            r.get('type') == 'TRANSITION_FAIL' for r in after)
    return checks


def green_new_consumes_legacy() -> dict[str, bool]:
    checks: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix='kewu-green-') as raw:
        root = Path(raw)
        env = make_env(root)
        legacy = mk_legacy_authorb_pkg(root / 'tasks')
        before = ledger_rows(legacy)
        n_before = len(before)
        rc, out = run_tick(CTRL, env)
        after = ledger_rows(legacy)
        new_rows = after[n_before:]
        checks['green_rc_0'] = rc == 0
        checks['green_consumed_authorb'] = (
            any(r.get('type') == 'TRANSITION_ACK'
                and r.get('transition') == 'authorB' for r in new_rows))
        checks['green_emitted_consuming'] = (
            'LEGACY_DAY_CHAIN_CONSUMING' in out and 'authorB' in out)
        checks['green_successor_pending_written'] = any(
            r.get('type') == 'TRANSITION_PENDING'
            and r.get('transition') == 'reviewB' for r in new_rows)
        checks['green_no_fail_noise'] = not any(
            r.get('type') == 'TRANSITION_FAIL' for r in after)
        checks['green_ack_after_verify'] = (
            next((r for r in new_rows if r.get('type') == 'TRANSITION_ACK'
                  and r.get('transition') == 'authorB'), None) or {}
        ).get('acked_at', '') >= (next(
            (r for r in new_rows if r.get('type') == 'TRANSITION_ACK'
             and r.get('transition') == 'authorB'), None) or {}
        ).get('verified_at', '')
    return checks


def green_zero_side_effect_when_idle() -> dict[str, bool]:
    checks: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix='kewu-idle-') as raw:
        root = Path(raw)
        env = make_env(root)
        tasks = root / 'tasks'
        mk_closed_pkg(tasks, '20260902')  # 全闭环 → 不可消费
        (tasks / '20260904_kewu_selfcycle_daily' / 'output').mkdir(
            parents=True, exist_ok=True)  # 无 ledger → seed WAITING
        closed = tasks / '20260902_kewu_selfcycle_daily'
        n_closed = len(ledger_rows(closed))
        snap_before = snapshot_tree(tasks)
        rc, out = run_tick(CTRL, env)
        snap_after = snapshot_tree(tasks)
        closed_after = ledger_rows(closed)
        checks['idle_rc_0'] = rc == 0
        checks['idle_silent'] = out == ''
        checks['idle_no_new_files'] = snap_after == snap_before
        checks['idle_no_ledger_growth'] = len(closed_after) == n_closed
        checks['idle_no_fail'] = not any(
            r.get('type') == 'TRANSITION_FAIL' for r in closed_after)
        checks['idle_no_fail_files'] = not any(
            p.name == 'controller_events.jsonl' for p in tasks.rglob('*'))
    return checks


def unit_iter_legacy() -> dict[str, bool]:
    checks: dict[str, bool] = {}
    # 直接加载生产模块 (与生产同一份代码), 调 iter_legacy_task_dirs
    import importlib.util
    spec = importlib.util.spec_from_file_location('ctrl_tick', CTRL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory(prefix='kewu-iter-') as raw:
        root = Path(raw)
        for name in ['20260826_kewu_selfcycle_daily',  # 超龄 (<floor=08-27) 跳过
                     '20260827_kewu_selfcycle_daily',  # =floor 边界保留
                     '20260903_kewu_selfcycle_daily',
                     '20260905_kewu_selfcycle_daily',
                     '20260906_kewu_selfcycle_daily',  # 当日跳过
                     'badname_kewu_selfcycle_daily',   # 无效名跳过
                     '20260907_kewu_selfcycle_daily']:  # 未来跳过
            (root / name).mkdir(exist_ok=True)
        (root / '20260904_kewu_selfcycle_daily').write_text(
            'plain file, not a task dir', encoding='utf-8')
        got = mod.iter_legacy_task_dirs('2026-09-06', task_root=root)
        names = [p.name for p in got]
        checks['unit_sorted_oldest_first'] = names == [
            '20260827_kewu_selfcycle_daily', '20260903_kewu_selfcycle_daily',
            '20260905_kewu_selfcycle_daily']
        checks['unit_plain_file_excluded'] = (
            all(p.is_dir() for p in got)
            and '20260904_kewu_selfcycle_daily' not in names)
        checks['unit_skip_today_invalid_future_stale'] = all(
            n[:8] not in ('20260906', '20260907') and 'badname' not in n
            and n[:8] != '20260826' for n in names)
    return checks


def main() -> int:
    all_checks: dict[str, bool] = {}
    for fn in (red_bak_ignores_legacy, green_new_consumes_legacy,
               green_zero_side_effect_when_idle, unit_iter_legacy):
        all_checks.update(fn())
    ok = all(all_checks.values())
    print(json.dumps({'legacy_sweep_test': 'PASS' if ok else 'FAIL',
                      'checks': all_checks}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())