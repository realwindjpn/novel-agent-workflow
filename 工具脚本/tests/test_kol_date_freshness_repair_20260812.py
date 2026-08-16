#!/usr/bin/env python3
"""Focused deterministic tests for 2026-08-12 KOL date/freshness repair.

Covers TASK.md required cases:
  1. 2025 PLATFORM_SIGNAL stays in-window under approved policy window
  2. 2023 PLATFORM_SIGNAL remains stale
  3. Numeric platform identifiers never become dates
  4. Aggregator URL classified without invented date
  5. Budget-truncated WeChat does not use run timestamp as publication date

TASK2 (domain-scorer eligibility layer):
  6. Dated in-window platform-commentary item is NOT archived as STALE_NEWS
     (viewpoint signals skip the 14/180-day news-staleness rule).
  7. News-staleness rule stays intact for non-commentary source groups
     (primary-fact cards are not weakened).
  8. No-Dyson-match platform-commentary behavior is explicit: scorer reports
     NO_DYSON_TREE_MATCH, the radar gate archives eligible policies with that
     reason, and legacy archive_reason residue is cleared on any other outcome.
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPT_DIR))
import platform_radar_v2_20260622 as radar  # noqa: E402
import kewu_domain_scorer as scorer  # noqa: E402

TODAY = datetime.date(2026, 8, 12)
PASS = 0
FAIL = 0


def ok(label: str) -> None:
    global PASS
    PASS += 1
    print(f'  PASS  {label}')


def fail(label: str, detail: str = '') -> None:
    global FAIL
    FAIL += 1
    print(f'  FAIL  {label}: {detail}')


def test_2025_platform_signal_in_window() -> None:
    item = {
        'published_at': '2025-11-20',
        'material_policy': 'PLATFORM_SIGNAL',
        'title': '量子位观点',
        'evidence': '',
    }
    stale, tag = radar.is_stale_kol_item(item, today=TODAY)
    if not stale and tag == '':
        ok('2025 PLATFORM_SIGNAL stays in-window')
    else:
        fail('2025 PLATFORM_SIGNAL stays in-window', f'stale={stale} tag={tag!r}')


def test_2023_platform_signal_stale() -> None:
    item = {
        'published_at': '2023-12-07',
        'material_policy': 'PLATFORM_SIGNAL',
        'title': '旧稿',
        'evidence': '',
    }
    stale, tag = radar.is_stale_kol_item(item, today=TODAY)
    if stale and tag in ('STALE_KOL_ARTICLE', 'DATE_OLD_YEAR'):
        ok('2023 PLATFORM_SIGNAL remains stale')
    else:
        fail('2023 PLATFORM_SIGNAL remains stale', f'stale={stale} tag={tag!r}')


def test_numeric_platform_ids_never_dates() -> None:
    cases = [
        {'url': 'https://weibo.com/1893892941/Qqh07ciz4', 'title': '微博帖'},
        {'created_at': '1893892941'},
        {'created_at': '1793892941'},
        {'url': 'https://space.bilibili.com/1234567890/article/251231.html', 'title': 'x'},
    ]
    for payload in cases:
        got = radar.extract_publication_date(payload, today=TODAY)
        if got == '':
            ok(f'numeric id not date: {payload}')
        else:
            fail('numeric id became date', f'payload={payload} got={got!r}')


def test_aggregator_url_no_invented_date() -> None:
    url = 'https://weibo.com/a/hot/5cc504ffe041aa95_0.html?type=grab'
    if not radar.is_aggregator_url(url):
        fail('aggregator classified', 'is_aggregator_url=False')
        return
    ok('aggregator URL recognized')
    pub = radar.extract_publication_date(
        {'url': url, 'title': '#长征十二号乙运载火箭首飞成功#_微博', 'evidence': ''},
        today=TODAY,
    )
    if pub == '':
        ok('aggregator has no invented date')
    else:
        fail('aggregator invented date', f'got={pub!r}')
    tag = radar.date_unknown_failure_tag({'url': url, 'body_status': 'excerpt_only'})
    if tag == radar.AGGREGATOR_FAILURE_TAG and not radar.is_date_unknown_tag(tag):
        ok('aggregator tag is WEIBO_AGGREGATOR_PAGE (not DATE_UNKNOWN*)')
    else:
        fail('aggregator tag', f'got={tag!r}')


def test_budget_truncated_wechat_no_run_timestamp() -> None:
    run_ts = '2026-08-12T13:18:00'
    item = {
        'platform': 'wechat',
        'url': 'https://mp.weixin.qq.com/s/uakKFD59KplMnvWIZnx7vw',
        'body_status': 'truncated_by_budget',
        'published_at': '',
        'title': '川东液化签约',
        'evidence': '',
        'created_at_of_run': run_ts,
        'collected_at': run_ts,
    }
    # Metadata inaccessible → must stay empty (never fall back to run time).
    with mock.patch.object(radar, 'fetch_publication_date', return_value=''):
        meta = radar.backfill_platform_metadata_date(item, timeout=1)
    if meta != '':
        fail('wechat meta empty on fetch miss', f'got={meta!r}')
        return
    ok('wechat truncated: no meta when fetch empty')
    pub = radar.extract_publication_date(item, today=TODAY)
    if pub == '' and pub != run_ts[:10]:
        ok('wechat truncated: extract does not use run timestamp')
    else:
        fail('wechat truncated used run timestamp', f'got={pub!r}')
    # When platform metadata IS present, accept it (still not run time).
    with mock.patch.object(radar, 'fetch_publication_date', return_value='2026-07-01'):
        meta2 = radar.backfill_platform_metadata_date(item, timeout=1)
    if meta2 == '2026-07-01' and meta2 != run_ts[:10]:
        ok('wechat truncated: explicit platform metadata accepted')
    else:
        fail('wechat truncated meta accept', f'got={meta2!r}')


def _days_ago_iso(days: int) -> str:
    return (datetime.date.today() - datetime.timedelta(days=days)).isoformat()


# 200 days: outside the 180-day domestic news window, inside the 365-day
# PLATFORM_SIGNAL viewpoint window — the exact band Task 2 repairs.
NEWS_STALE_BUT_VIEWPOINT_FRESH = _days_ago_iso(200)

QUANTUM_TITLE = '量子计算产业化的三点观察'
QUANTUM_BODY = (
    '量子计算、量子纠错与量子网络的工程化路线图正在收敛，'
    '产业动员能力决定谁先跨过容错阈值。' * 4
)


def test_platform_commentary_dated_in_window_not_stale_news() -> None:
    # Degradation layer: commentary group must skip the news-staleness rule.
    degrade, reason = scorer.classify_noise_degradation(
        QUANTUM_TITLE,
        QUANTUM_BODY,
        'https://mp.weixin.qq.com/s/task2fixture',
        NEWS_STALE_BUT_VIEWPOINT_FRESH,
        'wechat_platform_commentary',
    )
    if not degrade and reason == '':
        ok('commentary dated in-window: no STALE_NEWS at degradation layer')
    else:
        fail('commentary dated in-window: no STALE_NEWS', f'degrade={degrade} reason={reason!r}')
        return
    # Full scorer path (same item shape the radar feeds): stays scorable,
    # Dyson gate passes on relevance, no archive reason.
    res = scorer.score_and_classify_item({
        'title': QUANTUM_TITLE,
        'summary': QUANTUM_BODY,
        'url': 'https://mp.weixin.qq.com/s/task2fixture',
        'source_group_key': 'wechat_platform_commentary',
        'source_role': 'secondary',
        'published_at': NEWS_STALE_BUT_VIEWPOINT_FRESH,
    })
    if res.get('noise_flag') or res.get('archive_reason') == 'STALE_NEWS':
        fail('commentary scorer path not STALE_NEWS', f"archive_reason={res.get('archive_reason')!r}")
        return
    if not res.get('dyson_tree_matches'):
        fail('commentary scorer path dyson match', 'expected quantum node match')
        return
    ok('commentary scorer path: scored + dyson match, archive_reason empty')
    # Radar gate: eligible policy with a match stays eligible, and any legacy
    # archive_reason residue from a replayed sidecar is cleared.
    it = {
        'material_policy': 'PLATFORM_SIGNAL',
        'dyson_tree_matches': res['dyson_tree_matches'],
        'archive_reason': 'NO_DYSON_TREE_MATCH',
    }
    radar.apply_dyson_archive_gate(it, res)
    if it['material_policy'] == 'PLATFORM_SIGNAL' and 'archive_reason' not in it:
        ok('radar gate keeps dated in-window commentary eligible')
    else:
        fail('radar gate keeps eligible', f'it={it!r}')


def test_news_staleness_rule_intact_for_non_commentary() -> None:
    # Same 200-day-old date on a non-commentary source group must still be
    # archived as STALE_NEWS: the carve-out must not weaken primary-fact cards.
    degrade, reason = scorer.classify_noise_degradation(
        QUANTUM_TITLE,
        QUANTUM_BODY,
        'https://example.gov.cn/news/task2fixture',
        NEWS_STALE_BUT_VIEWPOINT_FRESH,
        'domestic_official',
    )
    if degrade and reason == 'STALE_NEWS':
        ok('non-commentary source group still archived as STALE_NEWS')
    else:
        fail('non-commentary STALE_NEWS intact', f'degrade={degrade} reason={reason!r}')


def test_no_dyson_match_commentary_archive_explicit() -> None:
    # Off-domain commentary (travel/hospitality brief) matches no Dyson node:
    # archived by the relevance gate with the explicit NO_DYSON_TREE_MATCH
    # reason — not by news staleness, even though it carries a fresh date.
    res = scorer.score_and_classify_item({
        'title': '一周商旅动态 | 曹操出行全面进军企业商旅市场；三亚湾voco酒店开业',
        'summary': '企业商旅市场动态，酒店开业与出行平台扩张。' * 6,
        'url': 'https://mp.weixin.qq.com/s/task2fixture2',
        'source_group_key': 'wechat_platform_commentary',
        'source_role': 'secondary',
        'published_at': _days_ago_iso(30),
    })
    if res.get('archive_reason') == 'STALE_NEWS':
        fail('no-dyson commentary not STALE_NEWS', 'staleness rule leaked into commentary')
        return
    if (
        res.get('dyson_tree_matches') == []
        and res.get('archive_reason') == 'NO_DYSON_TREE_MATCH'
        and res.get('dyson_gate_status') == 'ARCHIVE_NO_DYSON_TREE_MATCH'
    ):
        ok('no-dyson commentary: scorer reason explicit (NO_DYSON_TREE_MATCH)')
    else:
        fail(
            'no-dyson commentary scorer contract',
            f"matches={res.get('dyson_tree_matches')} reason={res.get('archive_reason')!r} gate={res.get('dyson_gate_status')!r}",
        )
        return
    # Radar gate: eligible policy + no match → ARCHIVE_WITH_REASON + reason.
    it = {'material_policy': 'DISCOVERY_ONLY', 'dyson_tree_matches': []}
    radar.apply_dyson_archive_gate(it, res)
    if it.get('material_policy') == 'ARCHIVE_WITH_REASON' and it.get('archive_reason') == 'NO_DYSON_TREE_MATCH':
        ok('radar gate archives no-dyson commentary with explicit reason')
    else:
        fail('radar gate archives no-dyson commentary', f'it={it!r}')
        return
    # Legacy residue: replayed sidecar item re-gated to NOISE (e.g. DATE_OLD_YEAR)
    # must not keep a contradicting archive_reason.
    stale_it = {
        'material_policy': 'NOISE',
        'failure_tag': 'DATE_OLD_YEAR',
        'dyson_tree_matches': [],
        'archive_reason': 'NO_DYSON_TREE_MATCH',
    }
    radar.apply_dyson_archive_gate(stale_it, res)
    if stale_it.get('material_policy') == 'NOISE' and 'archive_reason' not in stale_it:
        ok('legacy archive_reason cleared when re-gate is not an archive decision')
    else:
        fail('legacy archive_reason cleared', f'it={stale_it!r}')


if __name__ == '__main__':
    print('=== kol date/freshness repair 20260812 ===')
    test_2025_platform_signal_in_window()
    test_2023_platform_signal_stale()
    test_numeric_platform_ids_never_dates()
    test_aggregator_url_no_invented_date()
    test_budget_truncated_wechat_no_run_timestamp()
    test_platform_commentary_dated_in_window_not_stale_news()
    test_news_staleness_rule_intact_for_non_commentary()
    test_no_dyson_match_commentary_archive_explicit()
    print(f'\nPASS={PASS} FAIL={FAIL}')
    sys.exit(1 if FAIL else 0)
