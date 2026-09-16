#!/usr/bin/env python3
"""场景 D 回归：G2 缺失产物连续三次后必须 REPAIR_LIMIT，第四 tick 静默。

该测试只运行控制器内置 self-test；内置场景 D 使用 tempfile 夹具，
不会访问生产任务包、正文、草稿箱、cron 或模型配置。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CTRL = Path('/root/.hermes/scripts/kewu_daily_control_tick.py')
PY = sys.executable
REQUIRED = {
    'repair_limit_after_3',
    'repair_limit_stops',
    'repair_limit_queued_escalation',
    'no_ack_without_artifact',
    'queue_row_has_ownership',
    'queue_row_has_expected_artifact',
    'queue_next_transition_is_successor',
    'task_inbox_dual_write',
    'pending_row_has_ownership',
}


def main() -> int:
    cp = subprocess.run([PY, str(CTRL), '--self-test'], text=True,
                        capture_output=True, timeout=240)
    if cp.returncode != 0:
        print(json.dumps({
            'scenario_d_regression': 'FAIL',
            'reason': 'controller self-test did not complete',
            'returncode': cp.returncode,
            'stdout': cp.stdout,
            'stderr': cp.stderr,
        }, ensure_ascii=False, indent=2))
        return 1
    try:
        result = json.loads(cp.stdout)
    except json.JSONDecodeError as exc:
        print(json.dumps({
            'scenario_d_regression': 'FAIL',
            'reason': f'invalid self-test JSON: {exc}',
            'stdout': cp.stdout,
            'stderr': cp.stderr,
        }, ensure_ascii=False, indent=2))
        return 1
    checks = result.get('checks', {})
    missing = sorted(REQUIRED - set(checks))
    failed = sorted(name for name in REQUIRED if checks.get(name) is not True)
    ok = result.get('control_tick_self_test') == 'PASS' and not missing and not failed
    print(json.dumps({
        'scenario_d_regression': 'PASS' if ok else 'FAIL',
        'self_test_verdict': result.get('control_tick_self_test'),
        'missing_checks': missing,
        'failed_checks': failed,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
