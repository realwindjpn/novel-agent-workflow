#!/usr/bin/env python3
"""P0 上游修复聚焦测试（2026-09-01）。

覆盖两个结构根因：
  A. supplement → evaluate 入账（补充采集不再是影子产物）
  B. coverage sweep 按域持久游标（跨进程重启不归零）

隔离原则：所有素材总线 / 游标 / streak 状态都写进 tmpdir，
永不触碰 /root/workspace/素材总线/kewu/material_cards.jsonl 与生产游标。

直接运行：python3 test_p0_upstream_repair_20260901.py
"""
from __future__ import annotations

import importlib.util
import json
import py_compile
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent          # 工具脚本/
RADAR = SCRIPT_DIR / 'platform_radar_v2_20260622.py'
SIDECAR = Path('/root/.hermes/scripts/kewu_platform_radar_sensenova_sidecar.py')
WATCHLIST = Path('/root/workspace/科武纪元/学习记录/平台号观点雷达/platform_watchlist.json')
REAL_BUS = Path('/root/workspace/素材总线/kewu/material_cards.jsonl')

PASS_COUNT = 0
FAIL_COUNT = 0
METRICS: dict = {}


def ok(label: str):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f'  PASS  {label}')


def fail(label: str, detail: str = ''):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f'  FAIL  {label}: {detail}')


def check(label: str, cond: bool, detail: str = ''):
    ok(label) if cond else fail(label, detail)


def section(title: str):
    print(f'\n=== {title} ===')


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f'cannot load {path}'
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ══════════════════════════════════════════
section('0. py_compile 两脚本')
# ══════════════════════════════════════════
for script in (RADAR, SIDECAR):
    try:
        py_compile.compile(str(script), doraise=True)
        ok(f'py_compile {script.name}')
    except Exception as exc:  # pragma: no cover - 编译失败即整轮无意义
        fail(f'py_compile {script.name}', str(exc))
        raise SystemExit(1)

radar = load_module('radar_p0', RADAR)
sidecar = load_module('sidecar_p0', SIDECAR)
REAL_BUS_BEFORE = sidecar.bus_line_count(REAL_BUS)
METRICS['real_bus_lines_before'] = REAL_BUS_BEFORE


# ══════════════════════════════════════════
# A. supplement → evaluate 入账
# ══════════════════════════════════════════
def make_run_dir(tmp: Path, mainline_urls: list[str], returncode_ok: bool = True) -> Path:
    """造一个最小 run 目录：discovery + mirofish 卡，卡数即主线新增。"""
    out = tmp / 'run'
    out.mkdir(parents=True, exist_ok=True)
    stats = {
        'sidecar_health': 'HEALTHY',
        'queried_domains': 9, 'queried_accounts': 9, 'domains_with_results': 9,
        'body_fetched': max(1, len(mainline_urls)), 'excerpt_only': 0, 'skipped_non_article': 0,
        'hotspot_recall': {
            'fresh_dated_count': 1, 'date_unknown_ratio': 0.0,
            'ai_science_hotspot_count': 1, 'dynamic_entity_count': 1,
        },
    }
    (out / 'platform_discovery.json').write_text(
        json.dumps({'items': [], 'stats': stats}, ensure_ascii=False), encoding='utf-8')
    (out / 'platform_mirofish_feed_package.json').write_text(
        json.dumps({'total_cards': len(mainline_urls),
                    'cards': [{'url': u} for u in mainline_urls]}, ensure_ascii=False),
        encoding='utf-8')
    return out


def write_bus(path: Path, urls: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as fh:
        for u in urls:
            fh.write(json.dumps({'url': u, 'title': 'x'}, ensure_ascii=False) + '\n')
    return sidecar.bus_line_count(path)


def eval_case(tmp: Path, mainline: list[str], supplement_urls: list[str],
              supplement_stats: dict, bus_seed: list[str] | None = None,
              streak_name: str = 'streak.json') -> dict:
    """隔离回放一轮：主线卡 + 补充线写入隔离总线 → evaluate_run 入账。"""
    bus = tmp / 'bus.jsonl'
    if bus_seed:
        write_bus(bus, bus_seed)
    out = make_run_dir(tmp, mainline)
    bus_before = sidecar.bus_line_count(bus)
    write_bus(bus, supplement_urls)          # 模拟补充采集器直写素材总线
    return sidecar.evaluate_run(
        out, 0, sidecar.now(), '', '',
        supplement_stats=supplement_stats, bus_lines_before=bus_before,
        bus_path=bus, zero_streak_path=tmp / streak_name,
    )


OK_WEIBO = {'weibo': {'exit': 0, 'stdout_tail': '入库卡 3'}}
OK_BOTH = {'weibo': {'exit': 0, 'stdout_tail': '入库卡 2'},
           'redfox': {'exit': 0, 'stdout_tail': '入库卡 1'}}
REDFOX_ZERO_BALANCE = {'redfox': {'exit': 1, 'stdout_tail': '{"code":3201,"msg":"积分余额不足"}'}}

section('A1. 主0补N → evaluate 计 N')
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    ev = eval_case(tmp, [], ['https://a.com/1', 'https://a.com/2', 'https://a.com/3'], OK_WEIBO)
    sup = ev.get('supplement') or {}
    check('supplement 已入账', ev['policy']['supplement_accounted_in_evaluate'] is True)
    check('主线新增 0', sup.get('mainline_new_cards') == 0, str(sup.get('mainline_new_cards')))
    check('补充新增 3', sup.get('supplement_new_cards') == 3, str(sup.get('supplement_new_cards')))
    check('总新增 3（不再是影子产物）', ev.get('total_new_cards_unique') == 3,
          str(ev.get('total_new_cards_unique')))
    check('总线增量口径 3', sup.get('bus_delta') == 3, str(sup.get('bus_delta')))
    check('自报卡数与总线一致', sup.get('reported_vs_bus_mismatch') is False)
    check('来源字段清楚', all(c.get('source', '').startswith('supplement:') for c in sup['channels']))
    # 主线 mirofish 0 卡是真实的发现层退化，补充线补位不得把它洗白成 DONE；
    # 状态照旧走既有健康门禁（PARTIAL_DISCOVERY_ONLY），但补充线必须已入账可见。
    check('主线退化仍标 PARTIAL（补充线不洗白主线）',
          ev['status'] == 'KOL_RADAR_SIDECAR_PARTIAL_DISCOVERY_ONLY', ev['status'])
    check('PARTIAL 下补充线仍可见', ev.get('total_new_cards_unique') == 3
          and isinstance(ev.get('supplement'), dict))
    check('MIROFISH_CARDS_ZERO 仍如实报告', 'MIROFISH_CARDS_ZERO' in ev['cache_health_reasons'],
          str(ev['cache_health_reasons']))
    METRICS['A1_total_new'] = ev.get('total_new_cards_unique')
    METRICS['A1_status'] = ev['status']

section('A2. 主N补M → 分别记账，总数 N+M')
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    ev = eval_case(tmp, ['https://main.com/1', 'https://main.com/2'],
                   ['https://sup.com/1'], OK_BOTH)
    sup = ev['supplement']
    check('主线 2', sup['mainline_new_cards'] == 2, str(sup['mainline_new_cards']))
    check('补充 1', sup['supplement_new_cards'] == 1, str(sup['supplement_new_cards']))
    check('总新增 3', ev['total_new_cards_unique'] == 3, str(ev['total_new_cards_unique']))
    check('无降级通道', sup['degraded_channels'] == [], str(sup['degraded_channels']))
    METRICS['A2_total_new'] = ev['total_new_cards_unique']

section('A3. 防双计：补充线重复主线 URL 只算一次')
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    # 补充线 3 条，其中 2 条是主线同一 URL 的变体（scheme/www/斜杠/大小写/query）
    ev = eval_case(
        tmp,
        ['https://main.com/a', 'https://main.com/b'],
        ['http://www.main.com/a/', 'HTTPS://MAIN.COM/b?utm_source=x', 'https://sup.com/new'],
        OK_WEIBO,
    )
    sup = ev['supplement']
    check('识别到 2 条重叠', sup['overlap_with_mainline'] == 2, str(sup['overlap_with_mainline']))
    check('总新增 3 而非 5（交集只减一次）', ev['total_new_cards_unique'] == 3,
          str(ev['total_new_cards_unique']))
    check('主线2+补充3-重叠2', sup['mainline_new_cards'] + sup['supplement_new_cards']
          - sup['overlap_with_mainline'] == ev['total_new_cards_unique'])
    METRICS['A3_overlap'] = sup['overlap_with_mainline']

section('A4. RedFox 余额0 → DEGRADED_BALANCE_ZERO，不是「成功0条」')
row = sidecar.classify_supplement_channel('redfox', REDFOX_ZERO_BALANCE['redfox'])
check('归类 DEGRADED_BALANCE_ZERO', row['outcome'] == 'DEGRADED_BALANCE_ZERO', row['outcome'])
check('标记 degraded', row['degraded'] is True)
check('不是 NO_RESULTS/OK', row['outcome'] not in ('NO_RESULTS', 'OK'))
row_ok_zero = sidecar.classify_supplement_channel('weibo', {'exit': 0, 'stdout_tail': '入库卡 0'})
check('真·成功0条仍为 NO_RESULTS', row_ok_zero['outcome'] == 'NO_RESULTS', row_ok_zero['outcome'])
check('成功0条不算降级', row_ok_zero['degraded'] is False)
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    ev = eval_case(tmp, ['https://main.com/1'], [], REDFOX_ZERO_BALANCE)
    check('降级通道进事件', ev['supplement']['degraded_channels'] == ['redfox'],
          str(ev['supplement']['degraded_channels']))
    METRICS['A4_outcome'] = row['outcome']

section('A5. 连续两轮总新增0 → 只告警一次')
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    streak = tmp / 'streak.json'
    statuses = []
    for round_no in range(4):
        bus = tmp / 'bus.jsonl'
        out = make_run_dir(tmp, [])
        ev = sidecar.evaluate_run(
            out, 0, sidecar.now(), '', '',
            supplement_stats=REDFOX_ZERO_BALANCE, bus_lines_before=sidecar.bus_line_count(bus),
            bus_path=bus, zero_streak_path=streak)
        statuses.append((ev['status'], ev['zero_new_streak']['streak'],
                         bool(ev['zero_new_streak']['alert'])))
    alerts = [s for s in statuses if s[2]]
    check('第1轮不告警（未到阈值）', statuses[0][2] is False, str(statuses[0]))
    check('第2轮告警一次', statuses[1][2] is True, str(statuses[1]))
    check('告警轮状态为 NEED_CONTROLLER',
          statuses[1][0] == 'KOL_RADAR_SIDECAR_NO_NEW_CARDS_FAIL_NEED_CONTROLLER', statuses[1][0])
    check('第3、4轮不再刷屏', statuses[2][2] is False and statuses[3][2] is False, str(statuses[2:]))
    check('四轮共告警 1 次', len(alerts) == 1, str(len(alerts)))
    check('streak 持续累加到 4', statuses[3][1] == 4, str(statuses[3][1]))
    # 恢复：一轮有新增即清零，之后再连续两轮0可再次告警
    bus = tmp / 'bus.jsonl'
    out = make_run_dir(tmp, [])
    before = sidecar.bus_line_count(bus)
    write_bus(bus, ['https://recover.com/1'])
    ev_recover = sidecar.evaluate_run(out, 0, sidecar.now(), '', '',
                                      supplement_stats=OK_WEIBO, bus_lines_before=before,
                                      bus_path=bus, zero_streak_path=streak)
    check('有新增即 streak 清零', ev_recover['zero_new_streak']['streak'] == 0,
          str(ev_recover['zero_new_streak']))
    METRICS['A5_alerts_in_4_zero_rounds'] = len(alerts)

section('A6. 隔离性：真实素材总线未被测试写入')
check('真实总线行数未变', sidecar.bus_line_count(REAL_BUS) == REAL_BUS_BEFORE,
      f'{REAL_BUS_BEFORE} -> {sidecar.bus_line_count(REAL_BUS)}')


# ══════════════════════════════════════════
# B. coverage sweep 按域持久游标
# ══════════════════════════════════════════
def load_accounts() -> list[dict]:
    watch = json.loads(WATCHLIST.read_text(encoding='utf-8'))
    rows = []
    for dom in watch['domains']:
        for acc in dom['accounts']:
            flat = dict(acc)
            flat['domain_id'] = dom['domain_id']
            flat['domain_name'] = dom['domain_name']
            rows.append(flat)
    return rows


ACCOUNTS = load_accounts()
DOMAIN_IDS = sorted({a['domain_id'] for a in ACCOUNTS})

section('B0. watchlist 基线 48 账号槽 / 9 域')
check('账号槽 48', len(ACCOUNTS) == 48, str(len(ACCOUNTS)))
check('域数 9', len(DOMAIN_IDS) == 9, str(len(DOMAIN_IDS)))
METRICS['watchlist_account_slots'] = len(ACCOUNTS)
METRICS['watchlist_domains'] = len(DOMAIN_IDS)
METRICS['watchlist_unique_names'] = len({a['name'] for a in ACCOUNTS})

section('B1. 连续6轮：每轮九域覆盖，账号并集 ≥40')
cursor: dict = {}
union_slots: set[tuple[str, str]] = set()
per_domain: dict[str, set[str]] = {}
rounds_domains = []
for round_no in range(6):
    plan = radar.build_account_query_plan(ACCOUNTS, coverage_sweep=True,
                                          max_queries=9, cursor_state=cursor)
    picks = [(acc['domain_id'], acc['name']) for acc, _, _ in plan]
    rounds_domains.append(len({d for d, _ in picks}))
    for dom, name in picks:
        union_slots.add((dom, name))
        per_domain.setdefault(dom, set()).add(name)
    check(f'第{round_no + 1}轮 9 条计划', len(plan) == 9, str(len(plan)))
    check(f'第{round_no + 1}轮覆盖 9 域', len({d for d, _ in picks}) == 9, str(rounds_domains[-1]))
check(f'6 轮账号并集 {len(union_slots)} ≥ 40', len(union_slots) >= 40, str(len(union_slots)))
low = {d: sorted(v) for d, v in per_domain.items() if len(v) < 2}
check('每域 ≥2 个不同账号', not low, str(low))
check('不是固定 9/48（并集远超单轮）', len(union_slots) > 9, str(len(union_slots)))
METRICS['B1_union_account_slots_6_rounds'] = len(union_slots)
METRICS['B1_unique_names_6_rounds'] = len({n for _, n in union_slots})
METRICS['B1_per_domain_distinct'] = {d: len(v) for d, v in sorted(per_domain.items())}
METRICS['B1_max_queries'] = 9

section('B2. 进程重载后游标继续（不归零）')
with tempfile.TemporaryDirectory() as td:
    path = Path(td) / 'cursor.json'
    cur1: dict = {}
    plan1 = radar.build_account_query_plan(ACCOUNTS, coverage_sweep=True,
                                           max_queries=9, cursor_state=cur1)
    check('落盘成功', radar.save_coverage_cursor(path, cur1) is True)
    check('落盘文件存在', path.exists())
    # 模拟进程重启：全新 dict 从磁盘读回
    cur2 = radar.load_coverage_cursor(path)
    check('读回游标等于落盘游标', cur2 == cur1, f'{cur2} != {cur1}')
    check('游标非全零', any(v > 0 for v in cur2.values()), str(cur2))
    plan2 = radar.build_account_query_plan(ACCOUNTS, coverage_sweep=True,
                                          max_queries=9, cursor_state=cur2)
    names1 = [acc['name'] for acc, _, _ in plan1]
    names2 = [acc['name'] for acc, _, _ in plan2]
    check('重启后账号集不同于上一轮', names1 != names2, f'{names1} == {names2}')
    slots1 = {(a['domain_id'], a['name']) for a, _, _ in plan1}
    slots2 = {(a['domain_id'], a['name']) for a, _, _ in plan2}
    check('重启后槽位无一重复', not (slots1 & slots2), str(slots1 & slots2))
    check('重启后仍覆盖 9 域', len({a['domain_id'] for a, _, _ in plan2}) == 9)
    # 原子写：无残留 tmp
    leftovers = [p.name for p in Path(td).iterdir() if '.tmp.' in p.name]
    check('原子写无残留 tmp 文件', not leftovers, str(leftovers))
    METRICS['B2_cursor_after_reload'] = dict(sorted(cur2.items()))

section('B3. state 损坏 → 回退默认，不崩生产')
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    cases = {
        'truncated.json': '{"domains": {"ai": 3',
        'wrong_type.json': '[1,2,3]',
        'bad_values.json': '{"domains": {"ai": "x", "space": null, "_meta": 9, "energy": -4}}',
        'empty.json': '',
        'binary.json': '\x00\x01\x02',
    }
    for name, body in cases.items():
        p = tmp / name
        p.write_text(body, encoding='utf-8', errors='ignore')
        try:
            cur = radar.load_coverage_cursor(p)
            crashed = False
        except Exception as exc:
            cur, crashed = None, exc
        check(f'损坏 state 不抛异常 [{name}]', crashed is False, str(crashed))
        if crashed is False:
            check(f'回退为可用游标 [{name}]', isinstance(cur, dict))
            check(f'无负值/非法键 [{name}]',
                  all(isinstance(k, str) and not k.startswith('_') and isinstance(v, int) and v >= 0
                      for k, v in (cur or {}).items()), str(cur))
            plan = radar.build_account_query_plan(ACCOUNTS, coverage_sweep=True,
                                                  max_queries=9, cursor_state=dict(cur or {}))
            check(f'损坏后仍能出 9 条计划 [{name}]', len(plan) == 9, str(len(plan)))
    check('缺失文件回退空游标', radar.load_coverage_cursor(tmp / 'nope.json') == {})
    # 越界 offset 取模有界
    huge = {d: 10 ** 6 for d in DOMAIN_IDS}
    plan = radar.build_account_query_plan(ACCOUNTS, coverage_sweep=True,
                                          max_queries=9, cursor_state=huge)
    check('越界 offset 取模仍出 9 条', len(plan) == 9, str(len(plan)))
    check('越界 offset 前推后有界',
          all(0 <= v < 48 for v in huge.values()), str(huge))

section('B4. 普通非 coverage 模式行为不变')
plan_plain_a = radar.build_account_query_plan(ACCOUNTS, coverage_sweep=False, max_queries=0)
plan_plain_b = radar.build_account_query_plan(ACCOUNTS, coverage_sweep=False, max_queries=0,
                                              cursor_state={d: 3 for d in DOMAIN_IDS})
check('非 coverage 模式无视游标（结果逐项一致）',
      [(a['name'], r, n) for a, r, n in plan_plain_a] == [(a['name'], r, n) for a, r, n in plan_plain_b],
      f'{len(plan_plain_a)} vs {len(plan_plain_b)}')
cur_untouched = {d: 3 for d in DOMAIN_IDS}
radar.build_account_query_plan(ACCOUNTS, coverage_sweep=False, max_queries=5,
                              cursor_state=cur_untouched)
check('非 coverage 模式不改写游标', cur_untouched == {d: 3 for d in DOMAIN_IDS}, str(cur_untouched))
plan_limited = radar.build_account_query_plan(ACCOUNTS, coverage_sweep=False, max_queries=5)
check('非 coverage max_queries 截断仍生效', len(plan_limited) == 5, str(len(plan_limited)))
check('非 coverage 首条仍是 watchlist 首账号',
      plan_plain_a[0][0]['name'] == ACCOUNTS[0]['name'],
      f"{plan_plain_a[0][0]['name']} vs {ACCOUNTS[0]['name']}")
METRICS['B4_plain_plan_len'] = len(plan_plain_a)

section('B5. advance_cursor=False → 只读预览，不推进')
cur_ro = {d: 1 for d in DOMAIN_IDS}
snapshot = dict(cur_ro)
radar.build_account_query_plan(ACCOUNTS, coverage_sweep=True, max_queries=9,
                              cursor_state=cur_ro, advance_cursor=False)
check('只读模式游标不变', cur_ro == snapshot, str(cur_ro))

section('B6. 未把 max_queries 冒充成修复')
src = SIDECAR.read_text(encoding='utf-8')
check("sidecar 仍用 --max-queries 9", "'--max-queries', '9'" in src)
check('sidecar 未改成 18', "'--max-queries', '18'" not in src)


# ══════════════════════════════════════════
print(f'\n{"=" * 46}')
print(f'PASS={PASS_COUNT}  FAIL={FAIL_COUNT}')
print('metrics=' + json.dumps(METRICS, ensure_ascii=False, sort_keys=True))
print('=' * 46)
raise SystemExit(1 if FAIL_COUNT else 0)
