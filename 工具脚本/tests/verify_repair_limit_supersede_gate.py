#!/usr/bin/env python3
"""独立机器闸：验证 REPAIR_LIMIT 在合法/非法新产物下的解锁语义。

四项断言：
  A 三轮未过 → REPAIR_LIMIT 写入且后续 tick 静默（原止损不被削弱）
  B 锁死后放入「非法」G3 产物（错章号）→ 仍不解锁、不 ACK、无 supersede 事件
  C 锁死后放入「合法」G3 产物 → 写 REPAIR_LIMIT_SUPERSEDED，再 ACK 并推后继
  D 锁死状态下不得自动执行 builder（止损优先于 auto-run）
全程隔离临时项目，不碰生产任务包/正文/草稿箱/cron。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path('/root/.hermes/scripts')
TICK = SCRIPTS / 'kewu_daily_control_tick.py'
SEED = SCRIPTS / 'kewu_daily_seed.py'
BUILDER = SCRIPTS / 'kewu_daily_g3_builder.py'
PY = sys.executable

A, B, FRONTIER = 421, 422, 420
ROWS = {
    418: '第418章 | 第九卷·验卷 | 旧甲 | 旧甲事件。 | 旧甲伏笔。 | 3210',
    419: '第419章 | 第九卷·验卷 | 旧乙 | 旧乙事件。 | 旧乙伏笔。 | 3220',
    420: '第420章 | 第九卷·验卷 | 前沿 | 前沿事件。 | 前沿伏笔。 | 3230',
    421: '第421章 | 第九卷·验卷 | 甲章 | 甲章主体事件。 | 甲章伏笔。 | 3240',
    422: '第422章 | 第九卷·验卷 | 乙章 | 乙章主体事件。 | 乙章伏笔。 | 3250',
    423: '第423章 | 第九卷·验卷 | 后丙 | 后丙事件。 | 后丙伏笔。 | 3270',
}
PREV = '\n'.join([f'第{FRONTIER}章 前沿'] + [f'前沿第{i}段，给出读数与签批链。' for i in range(1, 11)] + ['（本章完）'])


def build_fixture(root: Path) -> dict:
    proj, tasks = root / 'proj', root / 'tasks'
    sub, new = proj / '已投稿', proj / '新版'
    for d in (sub, new, tasks):
        d.mkdir(parents=True, exist_ok=True)
    for i in range(1, FRONTIER + 1):
        (sub / f'第{i}章.txt').write_text('正文' * 600, encoding='utf-8')
    (new / f'第{FRONTIER}章.md').write_text(PREV + '\n', encoding='utf-8')
    outline = proj / 'outline.md'
    outline.write_text('\n'.join(ROWS[c] for c in sorted(ROWS)) + '\n', encoding='utf-8')
    task = tasks / '20260906_kewu_selfcycle_daily'
    out = task / 'output'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'G1_material_match.json').write_text(json.dumps({
        'verdict': 'ALLOW_G2', 'target_chapters': [A, B], 'total_cards': 12,
    }, ensure_ascii=False), encoding='utf-8')
    (out / 'G2_verdict.json').write_text(json.dumps({
        'verdict': 'NOTE_LAYER', 'final_verdict': 'NOTE_LAYER',
        'target_chapters': [A, B], 'outline_patch_allowed': False,
        'material_summary': {'bridged_cards': 12},
        'note_layer_points': [
            {'seat': '军事制度', 'point': f'{A}章：授权链须留可审计记录；BLOCKING_FOR_G3。'},
            {'seat': '读者视角', 'point': f'第{B}章 → 不注入今日素材。'},
        ],
    }, ensure_ascii=False), encoding='utf-8')
    env = os.environ.copy()
    env.update({
        'KEWU_DAILY_PROJECT_ROOT': str(proj), 'KEWU_DAILY_TASK_ROOT': str(tasks),
        'KEWU_DAILY_OUTLINE': str(outline), 'KEWU_DAILY_SUBMITTED_DIR': str(sub),
        'KEWU_DAILY_NEWTEXT_DIR': str(new),
        'KEWU_DAILY_DRAFT_LISTING': str(root / 'draft.json'),
        'KEWU_DAILY_ACTION_QUEUE': str(root / 'queue.jsonl'),
        'KEWU_DAILY_EXEC_DB': str(root / 'exec.db'),
        'KEWU_DAILY_NOW': '2026-09-06T20:05:00+08:00',
        'KEWU_DAILY_STALL_MINUTES': '0',
    })
    return {'task': task, 'out': out, 'env': env, 'root': root}


def run_tick(env) -> tuple[int, str]:
    cp = subprocess.run([PY, str(TICK)], env=env, text=True, capture_output=True, timeout=180)
    return cp.returncode, (cp.stdout or '').strip()


def ledger(task: Path) -> list[dict]:
    p = task / 'transitions.jsonl'
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]


def acks(task: Path) -> list[str]:
    return [r['transition'] for r in ledger(task) if r.get('type') == 'TRANSITION_ACK']


def types_for(task: Path, transition: str) -> list[str]:
    return [r.get('type') for r in ledger(task) if r.get('transition') == transition]


def drive_to_g3_repair_limit(fx: dict) -> None:
    """禁用 builder 制造真实三轮止损：把 AUTO_BUILDERS 指向不存在的脚本。"""
    env = dict(fx['env'])
    env['KEWU_DAILY_G3_BUILDER'] = str(fx['root'] / 'no_such_builder.py')
    subprocess.run([PY, str(SEED)], env=env, check=True, capture_output=True, timeout=60)
    for _ in range(8):
        run_tick(env)
        rows = ledger(fx['task'])
        if any(r.get('type') == 'REPAIR_LIMIT' and r.get('transition') == 'G3' for r in rows):
            return
    raise AssertionError('未能造出 G3 REPAIR_LIMIT')


def legal_prep(fx: dict) -> None:
    cp = subprocess.run([PY, str(BUILDER), '--task-dir', str(fx['task']),
                         '--chapters', str(A), str(B)],
                        env=fx['env'], text=True, capture_output=True, timeout=180)
    assert cp.returncode == 0, (cp.stdout, cp.stderr[-400:])


def main() -> int:
    checks: dict[str, bool] = {}

    # ── A/B/D: 锁死 + 非法产物 ──
    with tempfile.TemporaryDirectory(prefix='g3-sup-illegal-') as raw:
        fx = build_fixture(Path(raw))
        drive_to_g3_repair_limit(fx)
        checks['A_repair_limit_reached'] = 'REPAIR_LIMIT' in types_for(fx['task'], 'G3')
        checks['A_g3_not_acked'] = 'G3' not in acks(fx['task'])

        # 锁死后一次 tick 必须静默，且不得自动跑 builder（无新 AUTO_BUILD 行）
        before_auto = sum(1 for t in types_for(fx['task'], 'G3') if t == 'TRANSITION_AUTO_BUILD')
        rc, out = run_tick(fx['env'])
        after_auto = sum(1 for t in types_for(fx['task'], 'G3') if t == 'TRANSITION_AUTO_BUILD')
        checks['A_locked_tick_silent'] = rc == 0 and out == ''
        checks['D_no_autorun_while_locked'] = after_auto == before_auto

        # 非法产物：正确文件名，错章号
        legal_prep(fx)
        bad = json.loads((fx['out'] / f'G3_PREP_{B}.json').read_text(encoding='utf-8'))
        bad['chapter'] = 999
        (fx['out'] / f'G3_PREP_{B}.json').write_text(
            json.dumps(bad, ensure_ascii=False), encoding='utf-8')
        rc, out = run_tick(fx['env'])
        types = types_for(fx['task'], 'G3')
        checks['B_illegal_no_supersede'] = 'REPAIR_LIMIT_SUPERSEDED' not in types
        checks['B_illegal_no_ack'] = 'G3' not in acks(fx['task'])
        checks['B_illegal_tick_silent'] = out == ''

    # ── C: 锁死 + 合法产物 → 显式解锁后 ACK ──
    with tempfile.TemporaryDirectory(prefix='g3-sup-legal-') as raw:
        fx = build_fixture(Path(raw))
        drive_to_g3_repair_limit(fx)
        legal_prep(fx)
        rc, out = run_tick(fx['env'])
        rows = ledger(fx['task'])
        types = types_for(fx['task'], 'G3')
        sup = [r for r in rows if r.get('type') == 'REPAIR_LIMIT_SUPERSEDED']
        ack = [r for r in rows if r.get('type') == 'TRANSITION_ACK' and r.get('transition') == 'G3']
        pend = [r['transition'] for r in rows if r.get('type') == 'TRANSITION_PENDING']
        checks['C_supersede_written'] = len(sup) == 1 and sup[0].get('transition') == 'G3'
        checks['C_supersede_has_evidence'] = bool(sup) and sup[0].get('evidence') == 'RE_VERIFIED_ARTIFACT'
        checks['C_supersede_before_ack'] = bool(sup and ack) and sup[0]['seq'] < ack[0]['seq']
        checks['C_g3_acked'] = 'G3' in acks(fx['task'])
        checks['C_next_is_g4a'] = pend[-1] == 'G4A'
        checks['C_emitted_resume'] = 'REPAIR_LIMIT_SUPERSEDED' in out
        # 再 tick 一次不得重复写 supersede（幂等）
        run_tick(fx['env'])
        again = [r for r in ledger(fx['task']) if r.get('type') == 'REPAIR_LIMIT_SUPERSEDED']
        checks['C_supersede_not_duplicated'] = len(again) == 1

    ok = all(checks.values())
    print(json.dumps({'repair_limit_supersede_gate': 'PASS' if ok else 'FAIL',
                      'checks': checks}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
