#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DEAI 拆句公式硬闸 TDD 测试（r9b）。

新增规则：同段内跨句号「不是…。」后接「而是/这是/是」开头的句子
= SPLIT_FORMULA_HARD。模型用句号拆行规避「不是…而是/这是」公式闸。

与既有 test_kewu_deai_hard_gate_scan.py 同样用 importlib 直载扫描器，
不依赖 sys.path 接线（tests/ 目录无 conftest.py）。
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "kewu_deai_hard_gate_scan.py"
spec = importlib.util.spec_from_file_location("deai_scan_split", MODULE_PATH)
assert spec is not None and spec.loader is not None
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)

SPLIT = "SPLIT_FORMULA_HARD"


def scan_text(text: str):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "第999章.md"
        p.write_text(text, encoding="utf-8")
        return scan.scan_file(p)


class DeaiSplitFormulaTests(unittest.TestCase):
    def hit_types(self, text: str):
        return [h["type"] for h in scan_text(text)["hits"]]

    def test_split_this_is_caught(self):
        """A：拆写「这不是X。这是Y。」必须抓 hard。"""
        r = scan_text("# 第999章 测试\n这不是技术优势。这是规则优势。\n")
        self.assertEqual(r["verdict"], "FAIL_HARD")
        self.assertIn(SPLIT, self.hit_types("# 第999章 测试\n这不是技术优势。这是规则优势。\n"))

    def test_split_er_shi_is_caught(self):
        """B：拆写「这不是X。而是Y。」必须抓 hard。"""
        r = scan_text("# 第999章 测试\n这不是技术优势。而是规则优势。\n")
        self.assertEqual(r["verdict"], "FAIL_HARD")
        self.assertIn(SPLIT, self.hit_types("# 第999章 测试\n这不是技术优势。而是规则优势。\n"))

    def test_split_plain_shi_is_caught(self):
        """拆写「不是X。是Y。」（句号后直接以「是」开头）必须抓 hard。"""
        r = scan_text("# 第999章 测试\n这不是技术优势。是规则优势。\n")
        self.assertEqual(r["verdict"], "FAIL_HARD")
        self.assertIn(SPLIT, self.hit_types("# 第999章 测试\n这不是技术优势。是规则优势。\n"))

    def test_combined_formula_still_caught(self):
        """合写「不是X，而是Y」仍被抓（走既有 NOT_BUT_HARD），且不双计 split。"""
        types = self.hit_types("# 第999章 测试\n这不是技术优势，而是规则优势。\n")
        self.assertIn("NOT_BUT_HARD", types)
        self.assertNotIn(SPLIT, types)

    def test_dialogue_line_exempt(self):
        """对白整行（引号起首）不判拆句公式。"""
        types = self.hit_types('# 第999章 测试\n“这不是问题。这是机会。”\n')
        self.assertNotIn(SPLIT, types)

    def test_dialogue_mixed_line_narration_only(self):
        """混合行：引号内对白被剥，叙述部分无公式则不抓。"""
        types = self.hit_types('# 第999章 测试\n他盯着屏幕说：“这不是问题。这是机会。”\n')
        self.assertNotIn(SPLIT, types)

    def test_normal_narrative_not_caught(self):
        """普通叙述「这不是终点。后面的路还长。」不误抓。"""
        types = self.hit_types("# 第999章 测试\n这不是终点。后面的路还长。\n")
        self.assertNotIn(SPLIT, types)

    def test_not_is_chain_unrelated_not_caught(self):
        """无「而是/这是/是」承接的不成公式，不误抓。"""
        types = self.hit_types("# 第999章 测试\n这不是问题。这不是机会。分工不同罢了。\n")
        self.assertNotIn(SPLIT, types)

    def test_split_formula_pulls_hard_count(self):
        """拆句公式计入 hard_count，触发 FAIL_HARD 闸。"""
        r = scan_text("# 第999章 测试\n这不是技术优势。这是规则优势。\n")
        self.assertGreaterEqual(r["hard_count"], 1)


if __name__ == "__main__":
    unittest.main()