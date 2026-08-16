#!/usr/bin/env python3
"""Deterministic regression tests for platform_radar_v2 parser fixes (2026-08-10).

Run:  python3 test_radar_parsers.py
No network, no model calls. Asserts:
- _parse_relative_date recognises "今天" as today
- _parse_relative_date handles "X分钟前"/"几分钟前"
- _parse_relative_date handles "YYYY年MM月DD日"
- is_stale_kol_item: 2025 evidence is NOT DATE_OLD_YEAR in 2026
- is_stale_kol_item: 2023 evidence IS DATE_OLD_YEAR in 2026
"""
from __future__ import annotations
import datetime, sys
from pathlib import Path

sys.path.insert(0, str(Path('/root/workspace/科武纪元/工具脚本').resolve()))
import platform_radar_v2_20260622 as r  # noqa: E402

TODAY = datetime.date.today().isoformat()
errors: list[str] = []


def check(name: str, cond: bool, detail: str = '') -> None:
    if cond:
        print(f'  OK  {name}')
    else:
        errors.append(f'{name}: {detail}')
        print(f'  FAIL {name}: {detail}')


def test_parse_relative_date() -> None:
    print('[_parse_relative_date]')
    check('今天 -> today',
          r._parse_relative_date('今天，智谱在中关村论坛上正式发布 AutoGLM 沉思。') == TODAY,
          f'got={r._parse_relative_date("今天，智谱在中关村论坛上正式发布 AutoGLM 沉思。")!r}')
    check('today (en) -> today',
          r._parse_relative_date('today autoGLM released') == TODAY)
    check('昨天 -> today-1',
          r._parse_relative_date('昨天') == (datetime.date.today() - datetime.timedelta(days=1)).isoformat())
    check('1天前 -> today-1',
          r._parse_relative_date('1天前') == (datetime.date.today() - datetime.timedelta(days=1)).isoformat())
    check('2天前 -> today-2',
          r._parse_relative_date('2天前') == (datetime.date.today() - datetime.timedelta(days=2)).isoformat())
    check('30分钟前 -> today',
          r._parse_relative_date('30分钟前') == TODAY)
    check('几分钟前 -> today',
          r._parse_relative_date('几分钟前') == TODAY)
    check('10秒前 -> today',
          r._parse_relative_date('10秒前') == TODAY)
    check('YYYY年MM月DD日 -> ISO',
          r._parse_relative_date('2025年4月22日') == '2025-04-22')
    check('YYYY.MM.DD -> ISO',
          r._parse_relative_date('2025.04.22') == '2025-04-22')
    check('YYYY-MM-DD -> ISO',
          r._parse_relative_date('2025-04-22') == '2025-04-22')
    check('empty -> empty',
          r._parse_relative_date('') == '')


def test_extract_publication_date_on_autoGLM() -> None:
    print('[extract_publication_date]')
    item = {
        'title': '今天，智谱在中关村论坛上正式发布 AutoGLM 沉思',
        'evidence': '今天，智谱在中关村论坛上正式发布AutoGLM沉思，这一全新智能体具备深度研究能力。',
    }
    pub = r.extract_publication_date(item, today=datetime.date.today())
    check('autoGLM evidence -> TODAY',
          pub == TODAY,
          f'got={pub!r}')


def test_is_stale_kol_item_date_old_year() -> None:
    print('[is_stale_kol_item]')
    today = datetime.date(2026, 8, 10)
    # 2025 content should NOT be DATE_OLD_YEAR in 2026
    stale, tag = r.is_stale_kol_item(
        {'published_at': '', 'title': '', 'evidence': '2025中国载人飞行首发任务临近实施！'},
        today=today,
    )
    check('2025 evidence -> NOT DATE_OLD_YEAR',
          tag != 'DATE_OLD_YEAR',
          f'got={tag!r}')
    # 2023 content should still be DATE_OLD_YEAR
    stale, tag = r.is_stale_kol_item(
        {'published_at': '', 'title': '', 'evidence': '回顾2023年的航天成就'},
        today=today,
    )
    check('2023 evidence -> DATE_OLD_YEAR',
          tag == 'DATE_OLD_YEAR',
          f'got={tag!r}')
    # explicit published_at within 7 days -> fresh
    stale, tag = r.is_stale_kol_item(
        {'published_at': '2026-08-09', 'title': 'x', 'evidence': 'y'},
        today=today,
    )
    check('2026-08-09 -> fresh',
          not stale and tag == '',
          f'got=({stale},{tag!r})')
    # 8 days old is INSIDE the KOL viewpoint window (a commentary piece keeps
    # reference value for months). The old 7/30-day cutoff evicted every dated
    # item, which is the NO_FRESH_DATED defect; assert the window, not a day count.
    stale, tag = r.is_stale_kol_item(
        {'published_at': '2026-08-01', 'title': 'x', 'evidence': 'y'},
        today=today,
    )
    check('2026-08-01 (8d) -> fresh within viewpoint window',
          not stale and tag == '',
          f'got=({stale},{tag!r})')
    # An explicit max_age_days must still cut off exactly where told.
    stale, tag = r.is_stale_kol_item(
        {'published_at': '2026-08-01', 'title': 'x', 'evidence': 'y'},
        max_age_days=7, today=today,
    )
    check('2026-08-01 with max_age_days=7 -> STALE_KOL_ARTICLE',
          stale and tag == 'STALE_KOL_ARTICLE',
          f'got=({stale},{tag!r})')
    # DATE_OLD_YEAR overrides STALE check from evidence years
    stale, tag = r.is_stale_kol_item(
        {'published_at': '2024-01-01', 'title': 'y', 'evidence': '2024年'},
        today=today,
    )
    check('2024 published_at -> STALE_KOL_ARTICLE',
          stale and tag in ('STALE_KOL_ARTICLE', 'DATE_OLD_YEAR'),
          f'got=({stale},{tag!r})')


if __name__ == '__main__':
    test_parse_relative_date()
    test_extract_publication_date_on_autoGLM()
    test_is_stale_kol_item_date_old_year()
    print()
    if errors:
        print(f'FAILURES ({len(errors)}):')
        for e in errors:
            print(' -', e)
        sys.exit(1)
    print(f'ALL {sum(1 for _ in open(__file__)) if False else "tests"} passed.')
