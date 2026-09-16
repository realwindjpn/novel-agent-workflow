#!/usr/bin/env python3
"""Regression tests — coverage 口径拆分 / round-robin cohort 可见性 /
微信空 slug 候选跳过 / 游标不错位 / 旧产物回放（2026-09-05 A2）.

根因（审计误读）:
  stats['coverage_pct'] = accounts_with_results / configured_accounts,
  最新轮 2/48 = 4%。它是「产出率」，不是「查询覆盖率」。同一轮
  queried_accounts=9/48 属 coverage_sweep 按域游标轮转的设计值，
  但 summary 里只有一个 coverage_pct，审计据此读成「只查了 9 个账号且覆盖 4%」。

本文件锁死四件事：
  1. query_coverage_pct = queried_accounts/configured_accounts；
     yield_coverage_pct = accounts_with_results/configured_accounts；
     coverage_pct 保留为 yield 的兼容别名，分母口径显式写出。
  2. summary/stats 输出 round_robin_cohort：本轮各域取了哪些账号 + 游标 before/after。
  3. 微信候选层遇空 slug（https://mp.weixin.qq.com/s/）拒绝该候选并继续后续路由
     （collect_web → anysearch → ddgs），畸形 URL 不得占掉该账号本轮候选名额；
     错误标签区分 MALFORMED_URL_SKIPPED_CONTINUED / MALFORMED_URL_DROPPED_NO_ALTERNATIVE。
  4. 候选跳过不推进/不错位按域持久游标；回放 sidecar_20260905_1921 旧产物不崩。

Run: python3 -m pytest test_radar_coverage_fields.py -v
No network for the unit tests (routes are monkeypatched); the replay test runs the
script in deterministic post-segment mode (no live discovery) on a temp copy.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path('/root/workspace/科武纪元/工具脚本')
SCRIPT = SCRIPT_DIR / 'platform_radar_v2_20260622.py'
OLD_RUN = Path('/root/workspace/科武纪元/学习记录/平台号观点雷达/runs/sidecar_20260905_1921')

sys.path.insert(0, str(SCRIPT_DIR.resolve()))
import platform_radar_v2_20260622 as r  # noqa: E402


# ── helpers ────────────────────────────────────────────────────────────────
def _acc(name: str, domain: str, platform: str = '微信公众号') -> dict:
    return {
        'name': name,
        'keywords': ['脑机接口', '芯片'],
        'platform_candidates': [platform],
        'domain_id': domain,
        'domain_name': domain + '域',
    }


BARE_SLUG = 'https://mp.weixin.qq.com/s/'
GOOD_WECHAT = 'https://mp.weixin.qq.com/s/AbCdEf123456xyz'
GOOD_WECHAT_2 = 'https://mp.weixin.qq.com/s/ZzYyXx987654abc'


# ══════════════════════════════════════════════════════════════════════════
# 1. coverage 口径与分母
# ══════════════════════════════════════════════════════════════════════════
def test_coverage_fields_two_rates_and_denominators():
    f = r.compute_coverage_fields(configured_accounts=48, queried_accounts=9,
                                  accounts_with_results=2)
    # 查询覆盖率：本轮实际发出查询的账号 / 配置账号
    assert f['query_coverage_pct'] == 19, f
    assert f['queried_accounts'] == 9 and f['configured_accounts'] == 48
    # 产出率：有结果的账号 / 配置账号（旧 coverage_pct 就是这一个）
    assert f['yield_coverage_pct'] == 4, f
    assert f['accounts_with_results'] == 2
    # 兼容：coverage_pct 必须仍等于 yield，不得被悄悄改成 query
    assert f['coverage_pct'] == f['yield_coverage_pct'] == 4
    # 口径必须写在产物里，让审计不用猜
    sem = f['coverage_semantics']
    assert sem['query_coverage_pct'] == 'queried_accounts/configured_accounts'
    assert sem['yield_coverage_pct'] == 'accounts_with_results/configured_accounts'
    assert 'yield_coverage_pct' in sem['coverage_pct']


def test_coverage_fields_zero_denominator_safe():
    f = r.compute_coverage_fields(0, 0, 0)
    assert f['query_coverage_pct'] == 0 and f['yield_coverage_pct'] == 0
    assert f['coverage_pct'] == 0


def test_coverage_fields_full_sweep():
    f = r.compute_coverage_fields(48, 48, 48)
    assert f['query_coverage_pct'] == 100 and f['yield_coverage_pct'] == 100


def test_coverage_fields_reproduce_sidecar_20260905_1921():
    """旧产物的真实数字：9 查询 / 48 配置 / 2 产出 → 19% 查询覆盖、4% 产出。"""
    doc = json.loads((OLD_RUN / 'platform_discovery.json').read_text(encoding='utf-8'))
    st = doc['stats']
    f = r.compute_coverage_fields(st['configured_accounts'], st['queried_accounts'],
                                  st['accounts_with_results'])
    assert (f['query_coverage_pct'], f['yield_coverage_pct']) == (19, 4)
    assert f['coverage_pct'] == st['coverage_pct'] == 4


# ══════════════════════════════════════════════════════════════════════════
# 2. round_robin_cohort：9/48 不再被读成缺查
# ══════════════════════════════════════════════════════════════════════════
def test_round_robin_cohort_lists_picked_accounts_and_cursor():
    accounts = [_acc('A1', 'ai'), _acc('A2', 'ai'), _acc('A3', 'ai'),
                _acc('S1', 'space'), _acc('S2', 'space')]
    domain_map = {'ai': ['A1', 'A2', 'A3'], 'space': ['S1', 'S2']}
    cursor = {'ai': 1, 'space': 0}
    before = dict(cursor)
    plan = r.build_account_query_plan(accounts, coverage_sweep=True, max_queries=2,
                                      cursor_state=cursor)
    cohort = r.build_round_robin_cohort(plan, domain_map, before, cursor)
    rows = {row['domain_id']: row for row in cohort['domains']}
    # cursor=1 → ai 域本轮从 A2 起取
    assert rows['ai']['picked_accounts'] == ['A2']
    assert rows['ai']['cursor_before'] == 1 and rows['ai']['cursor_after'] == 2
    assert rows['ai']['domain_accounts'] == 3
    assert rows['space']['picked_accounts'] == ['S1']
    assert rows['space']['cursor_before'] == 0 and rows['space']['cursor_after'] == 1
    assert cohort['queried_accounts'] == 2
    assert cohort['configured_accounts'] == 5


def test_round_robin_cohort_marks_domains_not_sampled_this_round():
    accounts = [_acc('A1', 'ai'), _acc('S1', 'space')]
    domain_map = {'ai': ['A1'], 'space': ['S1']}
    cursor = {'ai': 0, 'space': 0}
    before = dict(cursor)
    plan = r.build_account_query_plan(accounts, coverage_sweep=True, max_queries=1,
                                      cursor_state=cursor)
    cohort = r.build_round_robin_cohort(plan, domain_map, before, cursor)
    rows = {row['domain_id']: row for row in cohort['domains']}
    assert rows['ai']['picked_accounts'] == ['A1']
    assert rows['space']['picked_accounts'] == []
    assert rows['space']['sampled_this_round'] is False


def test_round_robin_cohort_summary_lines_explain_9_of_48():
    accounts = [_acc(f'A{i}', 'ai') for i in range(1, 6)]
    domain_map = {'ai': [a['name'] for a in accounts]}
    cursor = {'ai': 3}
    before = dict(cursor)
    plan = r.build_account_query_plan(accounts, coverage_sweep=True, max_queries=1,
                                      cursor_state=cursor)
    cohort = r.build_round_robin_cohort(plan, domain_map, before, cursor)
    lines = r.render_round_robin_cohort_md(cohort)
    text = '\n'.join(lines)
    assert 'round_robin_cohort' in text or 'round-robin' in text.lower()
    assert 'A4' in text            # cursor=3 → 第 4 个账号
    assert 'cursor_before' in text and 'cursor_after' in text


# ══════════════════════════════════════════════════════════════════════════
# 3. 空 slug 候选：拒绝并继续后续候选/fallback
# ══════════════════════════════════════════════════════════════════════════
def test_is_malformed_article_url_catches_bare_slug():
    assert r.is_malformed_article_url(BARE_SLUG) is True
    assert r.is_malformed_article_url(GOOD_WECHAT) is False


def test_wechat_bare_slug_skipped_then_anysearch_candidate_used(monkeypatch):
    """collect_web 只回空 slug 时，必须继续拿到 anysearch 的可用候选。"""
    monkeypatch.setattr(r, 'discover_collect_web_search',
                        lambda *a, **k: [{'title': '空壳', 'url': BARE_SLUG, 'body': ''}])
    monkeypatch.setattr(r, 'discover_anysearch',
                        lambda *a, **k: [{'title': '真文章', 'url': GOOD_WECHAT, 'body': 'x' * 200}])
    monkeypatch.setattr(r, 'discover_ddgs', lambda *a, **k: [])
    diag: dict = {}
    hits = r.discover_for_account(_acc('脑机接口社区', 'frontier_tech'), 'wechat', 5, diag=diag)
    urls = [h['url'] for h in hits]
    assert GOOD_WECHAT in urls, urls
    assert BARE_SLUG not in urls, '空 slug 不得进入候选'
    assert diag['malformed_skipped'], diag
    assert diag['malformed_skipped'][0]['url'] == BARE_SLUG
    assert diag['malformed_skipped'][0]['route'] == 'collect_web_wechat_search'
    assert r.malformed_error_label(diag, hits) == 'MALFORMED_URL_SKIPPED_CONTINUED'


def test_wechat_bare_slug_does_not_eat_candidate_slot(monkeypatch):
    """limit_per_platform=1 时，空 slug 不得占掉唯一名额。"""
    monkeypatch.setattr(r, 'discover_collect_web_search',
                        lambda *a, **k: [{'title': '空壳', 'url': BARE_SLUG, 'body': ''}])
    monkeypatch.setattr(r, 'discover_anysearch',
                        lambda *a, **k: [{'title': '真文章', 'url': GOOD_WECHAT_2, 'body': 'y' * 200}])
    monkeypatch.setattr(r, 'discover_ddgs', lambda *a, **k: [])
    hits = r.discover_for_account(_acc('出口管制合规研究', 'geopolitics'), 'wechat', 5,
                                  limit_per_platform=1)
    assert [h['url'] for h in hits] == [GOOD_WECHAT_2]


def test_wechat_bare_slug_falls_through_to_ddgs(monkeypatch):
    """collect_web/anysearch 全空 slug → ddgs fallback 必须仍被触发。"""
    monkeypatch.setattr(r, 'discover_collect_web_search',
                        lambda *a, **k: [{'title': 'a', 'url': BARE_SLUG, 'body': ''}])
    monkeypatch.setattr(r, 'discover_anysearch',
                        lambda *a, **k: [{'title': 'b', 'url': BARE_SLUG, 'body': ''}])
    called = {'n': 0}

    def _ddgs(*a, **k):
        called['n'] += 1
        return [{'title': 'c', 'url': GOOD_WECHAT, 'body': 'z' * 200}]

    monkeypatch.setattr(r, 'discover_ddgs', _ddgs)
    diag: dict = {}
    hits = r.discover_for_account(_acc('脑机接口社区', 'frontier_tech'), 'wechat', 5, diag=diag)
    assert called['n'] == 1, 'ddgs fallback 必须因畸形候选被清空而触发'
    assert [h['url'] for h in hits] == [GOOD_WECHAT]
    assert r.malformed_error_label(diag, hits) == 'MALFORMED_URL_SKIPPED_CONTINUED'


def test_wechat_all_candidates_malformed_labels_no_alternative(monkeypatch):
    monkeypatch.setattr(r, 'discover_collect_web_search',
                        lambda *a, **k: [{'title': 'a', 'url': BARE_SLUG, 'body': ''}])
    monkeypatch.setattr(r, 'discover_anysearch', lambda *a, **k: [])
    monkeypatch.setattr(r, 'discover_ddgs', lambda *a, **k: [])
    diag: dict = {}
    hits = r.discover_for_account(_acc('出口管制合规研究', 'geopolitics'), 'wechat', 5, diag=diag)
    assert hits == []
    assert len(diag['malformed_skipped']) == 1
    assert r.malformed_error_label(diag, hits) == 'MALFORMED_URL_DROPPED_NO_ALTERNATIVE'
    assert diag['routes_tried'] and 'anysearch' in diag['routes_tried']


def test_malformed_error_label_none_when_clean():
    assert r.malformed_error_label({}, [{'url': GOOD_WECHAT}]) == ''
    assert r.malformed_error_label({'malformed_skipped': []}, []) == ''


# ══════════════════════════════════════════════════════════════════════════
# 4. 游标不因跳过而错位
# ══════════════════════════════════════════════════════════════════════════
def test_cursor_advance_independent_of_candidate_quality():
    """畸形候选的跳过发生在候选层，绝不能改变本轮 plan 或游标推进量。"""
    accounts = [_acc(f'F{i}', 'frontier_tech') for i in range(1, 5)] + \
               [_acc(f'G{i}', 'geopolitics') for i in range(1, 4)]
    c1 = {'frontier_tech': 3, 'geopolitics': 3}
    c2 = dict(c1)
    p1 = r.build_account_query_plan(accounts, coverage_sweep=True, max_queries=2, cursor_state=c1)
    p2 = r.build_account_query_plan(accounts, coverage_sweep=True, max_queries=2, cursor_state=c2)
    assert [a['name'] for a, _, _ in p1] == [a['name'] for a, _, _ in p2]
    assert c1 == c2
    # 取模有界：frontier_tech 4 个账号，offset 3 → 取 F4 后回到 0
    assert c1['frontier_tech'] == 0
    assert c1['geopolitics'] == 1  # 3 个账号，offset 3%3=0 → 取 G1 → 1


def test_cursor_roundtrip_covers_all_accounts_over_rounds(tmp_path):
    accounts = [_acc(f'A{i}', 'ai') for i in range(1, 5)]
    path = tmp_path / 'cursor.json'
    seen: list[str] = []
    for _ in range(4):
        state = r.load_coverage_cursor(path)
        plan = r.build_account_query_plan(accounts, coverage_sweep=True, max_queries=1,
                                          cursor_state=state)
        seen.append(plan[0][0]['name'])
        assert r.save_coverage_cursor(path, state) is True
    assert seen == ['A1', 'A2', 'A3', 'A4']


# ══════════════════════════════════════════════════════════════════════════
# 5. social CDP：保持禁用但必须给出不可用原因
# ══════════════════════════════════════════════════════════════════════════
def test_social_cdp_disabled_by_flag_reports_reason():
    rep = r.social_cdp_disabled_report()
    assert rep['status'] == 'DISABLED_BY_FLAG'
    assert rep['not_available_reason']
    assert 'login' in rep['not_available_reason'].lower() or '登录' in rep['not_available_reason']
    assert rep.get('reenable_hint')


def test_social_cdp_env_disabled_probe_reports_reason(monkeypatch):
    monkeypatch.setenv('KEWU_DISABLE_SOCIAL_CDP', '1')
    rep = r.probe_social_cdp()
    assert rep['status'] == 'CDP_DISABLED_BY_CONFIG'
    assert rep['not_available_reason']


# ══════════════════════════════════════════════════════════════════════════
# 6. 回放旧产物（确定性 post-segment，不发查询）
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.skipif(not (OLD_RUN / 'platform_discovery.json').exists(),
                    reason='sidecar_20260905_1921 产物不在本机')
def test_replay_sidecar_20260905_1921(tmp_path):
    out = tmp_path / 'replay'
    out.mkdir()
    shutil.copy(OLD_RUN / 'platform_discovery.json', out / 'platform_discovery.json')
    proc = subprocess.run(
        [sys.executable, str(SCRIPT),
         '--discovery-json', str(out / 'platform_discovery.json'),
         '--out-dir', str(out), '--dry-run-mirofish',
         '--disable-social-cdp', '--no-coverage-cursor'],
        capture_output=True, text=True, timeout=600,
        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
    )
    assert proc.returncode == 0, proc.stderr[-3000:]
    doc = json.loads((out / 'platform_discovery.json').read_text(encoding='utf-8'))
    st = doc['stats']
    # 新字段必须出现，且旧字段口径不变
    assert st['yield_coverage_pct'] == st['coverage_pct'] == 4
    assert st['query_coverage_pct'] == 0  # post-segment 不发查询 → 查询覆盖 0，与产出率分开
    assert st['coverage_semantics']['query_coverage_pct'] == 'queried_accounts/configured_accounts'
    assert st['social_cdp_not_available_reason']
    summary = (out / 'radar_v2_summary.md').read_text(encoding='utf-8')
    assert 'query_coverage_pct' in summary and 'yield_coverage_pct' in summary
    assert 'round_robin_cohort' in summary
    assert 'social_cdp_not_available_reason' in summary
    # 回放绝不能推进/写坏游标
    assert st['coverage_cursor_after'] == {}
