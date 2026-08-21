#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TDD tests for kewu_parallel_review.py — 5席并行审稿不变量。

设计裁决（2026-08-21，用户定）：
- 保留 5 席（不合并为3席）：编辑/结构/科学军事/读者/去AI
- 每席独立 provider（一席一 provider，HARD 条文）
- 走 Hermes 原生 CLI（裸 HTTP 直连吃 Cloudflare WAF 403=1010）
- 全文内嵌送审（摘要送审产假 FAIL）

跑法: python3 test_kewu_parallel_review.py
"""
from __future__ import annotations
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import kewu_parallel_review as M

POOL_AUDIT = Path('/root/workspace/任务运行态/20260821_kewu_selfcycle_optimize/output/pool_audit_20260821.json')


def verified_providers() -> set[str]:
    """Providers that actually PASSed the Hermes-native audit."""
    data = json.loads(POOL_AUDIT.read_text(encoding='utf-8'))
    return {r['provider'] for r in data['results'] if r['classification'] == 'PASS'}


class TestSeatRoster(unittest.TestCase):
    """席位名册不变量。"""

    def test_five_seats_exactly(self):
        """必须恰好 5 席 —— 用户 2026-08-21 定：保留5席不合并。"""
        self.assertEqual(len(M.SEATS), 5,
                         f'expected 5 seats, got {len(M.SEATS)}: {list(M.SEATS)}')

    def test_required_seat_names(self):
        """五审必须覆盖：编辑/结构/科学军事/读者/去AI。"""
        required = {'editor', 'structure', 'science_military', 'reader', 'deai'}
        self.assertEqual(set(M.SEATS.keys()), required)

    def test_每席都有角色描述和prompt(self):
        for name, cfg in M.SEATS.items():
            self.assertTrue(cfg.get('role'), f'{name} missing role')
            self.assertTrue(cfg.get('prompt'), f'{name} missing prompt')
            self.assertIn('{body}', cfg['prompt'],
                          f'{name} prompt must embed full body via {{body}}')


class TestProviderIndependence(unittest.TestCase):
    """一席一 provider —— 防「假5席」。"""

    def test_primary_providers_all_distinct(self):
        """5 席主 provider 必须互不相同。"""
        primaries = [cfg['fallbacks'][0][0] for cfg in M.SEATS.values()]
        dupes = {p for p in primaries if primaries.count(p) > 1}
        self.assertFalse(dupes, f'duplicate primary providers: {dupes}')

    def test_no_shared_provider_across_any_fallback_rank(self):
        """同 rank 的 fallback 也不得撞车（否则超时后会汇合成一席）。"""
        max_rank = max(len(cfg['fallbacks']) for cfg in M.SEATS.values())
        for rank in range(max_rank):
            at_rank = [cfg['fallbacks'][rank][0]
                       for cfg in M.SEATS.values() if len(cfg['fallbacks']) > rank]
            dupes = {p for p in at_rank if at_rank.count(p) > 1}
            self.assertFalse(dupes, f'rank {rank} duplicate providers: {dupes}')

    def test_每席至少两个fallback(self):
        for name, cfg in M.SEATS.items():
            self.assertGreaterEqual(len(cfg['fallbacks']), 2,
                                    f'{name} needs >=2 fallbacks for 异故障域切换')

    def test_fallback_跨模型族(self):
        """同席的 primary 与 backup 须跨模型族（异故障域）。"""
        def family(model: str) -> str:
            m = model.lower()
            for key in ('opus', 'gpt-5.6', 'gpt-5.5', 'grok', 'glm', 'deepseek', 'gemini'):
                if key in m:
                    return key
            return m
        for name, cfg in M.SEATS.items():
            fams = [family(fb[1]) for fb in cfg['fallbacks']]
            self.assertGreater(len(set(fams)), 1,
                               f'{name} fallbacks share model family {fams}')


class TestProvidersAreVerified(unittest.TestCase):
    """所有 provider 必须在实测 PASS 名单内 —— 禁未验证节点。"""

    @classmethod
    def setUpClass(cls):
        if not POOL_AUDIT.exists():
            raise unittest.SkipTest(f'pool audit missing: {POOL_AUDIT}')
        cls.verified = verified_providers()

    def test_every_provider_in_verified_pool(self):
        bad = []
        for name, cfg in M.SEATS.items():
            for prov, model in cfg['fallbacks']:
                if prov not in self.verified:
                    bad.append(f'{name}->{prov}')
        self.assertFalse(bad, f'unverified providers: {bad}')


class TestTransportIsHermesNative(unittest.TestCase):
    """必须走 Hermes 原生 CLI，不得裸 HTTP。"""

    def test_no_raw_http_client(self):
        src = Path(M.__file__).read_text(encoding='utf-8')
        for banned in ('urllib.request.urlopen', 'requests.post', 'http.client'):
            self.assertNotIn(banned, src,
                             f'raw HTTP {banned} hits Cloudflare WAF 403=1010; use hermes CLI')

    def test_run_seat_invokes_hermes_cli(self):
        src = Path(M.__file__).read_text(encoding='utf-8')
        self.assertIn('hermes', src)
        self.assertIn('subprocess', src)


class TestFullTextEmbedding(unittest.TestCase):
    """全文内嵌，禁摘要送审。"""

    def test_no_truncation_of_body(self):
        src = Path(M.__file__).read_text(encoding='utf-8')
        self.assertNotIn('body[:', src, 'body must not be truncated (摘要送审产假FAIL)')
        self.assertNotIn('summary', src.lower().replace('summarize_results', ''),
                         'no summarization of body allowed')


class TestVerdictParsing(unittest.TestCase):
    """裁决解析行为。"""

    def test_parse_verdict_pass(self):
        self.assertEqual(M.parse_verdict('PASS\n无必改项'), 'PASS')

    def test_parse_verdict_fail(self):
        self.assertEqual(M.parse_verdict('FAIL\n1. 第三段解释腔'), 'FAIL')

    def test_parse_verdict_pass_with_notes(self):
        self.assertEqual(M.parse_verdict('PASS_WITH_NOTES\n建议压缩'), 'PASS_WITH_NOTES')

    def test_parse_verdict_diff_format(self):
        """Hermes review mode wraps output as git diff; no explicit verdict line."""
        content = "┊ review diff\na/file.txt → b/file.txt\n@@ -0,0 +1,94 @@\n+第280章\n+正文..."
        self.assertEqual(M.parse_verdict(content), 'DIFF_FORMAT')

    def test_parse_verdict_verdict_inside_diff(self):
        """If a verdict token sits within the diff header, still extract it."""
        content = "┊ review diff\nFAIL\n+改动内容..."
        self.assertEqual(M.parse_verdict(content), 'FAIL')

    def test_parse_verdict_empty_is_timeout(self):
        self.assertEqual(M.parse_verdict(''), 'NO_OUTPUT')

    def test_parse_verdict_prefix_tolerant(self):
        """模型可能加前缀，须容错。"""
        self.assertEqual(M.parse_verdict('结论：FAIL\n...'), 'FAIL')


class TestIndependenceReport(unittest.TestCase):
    """产物须自报独立性，防假5席蒙混过关。"""

    def test_verify_independence_detects_collapse(self):
        results = {
            'editor': {'provider': 'A', 'verdict': 'PASS', 'content': 'PASS ok'},
            'structure': {'provider': 'A', 'verdict': 'PASS', 'content': 'PASS ok'},
            'science_military': {'provider': 'B', 'verdict': 'PASS', 'content': 'PASS ok'},
            'reader': {'provider': 'C', 'verdict': 'PASS', 'content': 'PASS ok'},
            'deai': {'provider': 'D', 'verdict': 'PASS', 'content': 'PASS ok'},
        }
        rep = M.verify_independence(results)
        self.assertFalse(rep['independent'])
        self.assertIn('A', rep['collapsed_providers'])
        self.assertEqual(rep['distinct_providers'], 4)

    def test_verify_independence_all_distinct(self):
        results = {
            f'seat{i}': {'provider': p, 'verdict': 'PASS', 'content': 'PASS ok'}
            for i, p in enumerate('ABCDE')
        }
        rep = M.verify_independence(results)
        self.assertTrue(rep['independent'])
        self.assertEqual(rep['collapsed_providers'], [])
        self.assertEqual(rep['distinct_providers'], 5)

    def test_verify_independence_ignores_failed_seats(self):
        """未出稿的席位不算独立性冲突。"""
        results = {
            'editor': {'provider': None, 'verdict': 'NO_OUTPUT', 'content': ''},
            'structure': {'provider': 'B', 'verdict': 'PASS', 'content': 'PASS ok'},
        }
        rep = M.verify_independence(results)
        self.assertTrue(rep['independent'])

    def test_zero_seats_is_not_independent(self):
        """全席无产出不得报 independent=True —— 防「0席也算PASS」假绿。

        实测 2026-08-21：5 席全 NO_OUTPUT 时旧实现输出
        「独立性: PASS (0 个不同 provider)」，会被误读为审稿通过。
        """
        results = {
            f'seat{i}': {'provider': None, 'verdict': 'NO_OUTPUT', 'content': ''}
            for i in range(5)
        }
        rep = M.verify_independence(results)
        self.assertFalse(rep['independent'])
        self.assertEqual(rep['distinct_providers'], 0)
        self.assertEqual(rep.get('reason'), 'NO_EFFECTIVE_SEAT')

    def test_single_seat_is_independent_but_flagged(self):
        """只有 1 席出稿：独立性无冲突，但须标注有效席不足。"""
        results = {
            'editor': {'provider': 'A', 'verdict': 'PASS', 'content': 'PASS ok'},
            'reader': {'provider': None, 'verdict': 'NO_OUTPUT', 'content': ''},
        }
        rep = M.verify_independence(results)
        self.assertTrue(rep['independent'])
        self.assertEqual(rep['distinct_providers'], 1)

    def test_empty_content_not_counted_as_seat(self):
        """provider 有值但 content 空 —— 不得算作有效席（防假绿）。"""
        results = {
            'editor': {'provider': 'A', 'verdict': 'NO_OUTPUT', 'content': ''},
            'structure': {'provider': 'A', 'verdict': 'PASS', 'content': 'PASS ok'},
        }
        rep = M.verify_independence(results)
        self.assertTrue(rep['independent'])
        self.assertEqual(rep['distinct_providers'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
