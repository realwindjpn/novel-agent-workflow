#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "kewu_deai_hard_gate_scan.py"
spec = importlib.util.spec_from_file_location("deai_scan", MODULE_PATH)
assert spec is not None and spec.loader is not None
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)


def scan_text(text: str):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "第999章.md"
        p.write_text(text, encoding="utf-8")
        return scan.scan_file(p)


class DeaiHardGateTests(unittest.TestCase):
    def hit_types(self, text: str):
        return [h["type"] for h in scan_text(text)["hits"]]

    def test_not_x_is_y_narration_is_hard(self):
        r = scan_text("# 第999章 测试\n他要的不是答案，是权限。\n")
        self.assertEqual(r["verdict"], "FAIL_HARD")
        self.assertIn("NOT_IS_HARD", [h["type"] for h in r["hits"]])

    def test_dialogue_not_x_is_y_is_exempt(self):
        r = scan_text('# 第999章 测试\n"这不是撤退，是换位。"\n')
        self.assertEqual(r["hard_count"], 0)

    def test_extended_soft_patterns(self):
        cases = {
            "IMPORTANCE_PUFFERY_SOFT": "这标志着一个划时代的里程碑。",
            "SHALLOW_SYMBOLISM_SOFT": "这象征着合作，也彰显了决心。",
            "NEXT_POINT_ANNOUNCE_SOFT": "接下来，我们来看结果。",
            "FAKE_CANDOR_SOFT": "坦白说，这很难。",
            "UNRAISED_OBJECTION_SOFT": "也许你会说时间不够，但事实相反。",
            "COLON_REVEAL_SOFT": "真相是：节点早已断开。",
            "DISTANT_NARRATOR_SOFT": "读者不难发现，他没有回头。",
        }
        for typ, line in cases.items():
            with self.subTest(typ=typ):
                self.assertIn(typ, self.hit_types(f"# 第999章 测试\n{line}\n"))

    def test_repeated_subject_opening_soft(self):
        text = "# 第999章 测试\n方宁按下开关。方宁看向屏幕。方宁关掉频道。\n"
        self.assertIn("REPEATED_SUBJECT_OPENING_SOFT", self.hit_types(text))

    def test_fragment_punchline_soft(self):
        text = "# 第999章 测试\n没有偏好。没有先验。没有乡愁。\n"
        self.assertIn("FRAGMENT_PUNCHLINE_SOFT", self.hit_types(text))

    def test_existing_clean_dialogue_stays_pass(self):
        text = '# 第999章 测试\n林星辰按下开关。屏幕跳到十九。\n"这不是撤退，是换位。"\n'
        r = scan_text(text)
        self.assertEqual(r["verdict"], "PASS")
        self.assertEqual(r["hard_count"], 0)

    def test_normal_prose_not_hit_by_placeholder_rules(self):
        """普通正文/标题不应命中占位正则 REPEATED_SUBJECT_OPENING_SOFT /
        FRAGMENT_PUNCHLINE_SOFT（修复 r'' 空正则误报的回归测试）。"""
        text = "# 第999章 测试\n方宁走到窗前。屏幕亮了起来。外面的天色渐渐暗了下去。\n"
        hits = self.hit_types(text)
        self.assertNotIn("REPEATED_SUBJECT_OPENING_SOFT", hits)
        self.assertNotIn("FRAGMENT_PUNCHLINE_SOFT", hits)

    def test_title_line_not_hit_by_placeholder_rules(self):
        """纯标题行不应命中占位规则。"""
        text = "# 第999章 暗流\n方宁看了一眼数据。\n"
        hits = self.hit_types(text)
        self.assertNotIn("REPEATED_SUBJECT_OPENING_SOFT", hits)
        self.assertNotIn("FRAGMENT_PUNCHLINE_SOFT", hits)

    def test_three_sentence_repeated_subject_still_hits(self):
        """三句同主语起句仍应命中 REPEATED_SUBJECT_OPENING_SOFT。"""
        text = "# 第999章 测试\n方宁按下开关。方宁看向屏幕。方宁关掉频道。\n"
        self.assertIn("REPEATED_SUBJECT_OPENING_SOFT", self.hit_types(text))

    def test_three_short_fragments_still_hit(self):
        """三个等长短句排比仍应命中 FRAGMENT_PUNCHLINE_SOFT。"""
        text = "# 第999章 测试\n没有偏好。没有先验。没有乡愁。\n"
        self.assertIn("FRAGMENT_PUNCHLINE_SOFT", self.hit_types(text))

    # ---- 混合行（叙述 + 对白同一行）NOT_IS_HARD 只扫叙述层 ----

    def test_strip_paired_quotes_helper(self):
        """helper 移除中文“”、半角 ""、半角 '' 成对引号内容；单侧引号不吞后文。"""
        self.assertEqual(scan.strip_paired_quotes("他点头，“不是撤退，是换位。”走开。"), "他点头，走开。")
        self.assertEqual(scan.strip_paired_quotes('他点头，"不是撤退，是换位。"走开。'), "他点头，走开。")
        self.assertEqual(scan.strip_paired_quotes("他点头，'不是撤退，是换位。'走开。"), "他点头，走开。")
        # 未闭合引号保持原样，不得把后文吞掉。
        self.assertEqual(scan.strip_paired_quotes("他说“不是撤退，是换位。"), "他说“不是撤退，是换位。")

    def test_mixed_line_dialogue_not_is_exempt_cn_quotes(self):
        """混合行：中文引号内台词的「不是X，是Y」不判硬闸。"""
        r = scan_text("# 第999章 测试\n他点了下头，“这不是撤退，是换位。”随后关掉频道。\n")
        self.assertNotIn("NOT_IS_HARD", [h["type"] for h in r["hits"]])
        self.assertEqual(r["hard_count"], 0)
        self.assertNotEqual(r["verdict"], "FAIL_HARD")

    def test_mixed_line_dialogue_not_is_exempt_halfwidth_quotes(self):
        """混合行：半角双引号与单引号内台词同样豁免。"""
        for line in (
            '他点了下头，"这不是撤退，是换位。"随后关掉频道。',
            "他点了下头，'这不是撤退，是换位。'随后关掉频道。",
        ):
            with self.subTest(line=line):
                r = scan_text(f"# 第999章 测试\n{line}\n")
                self.assertNotIn("NOT_IS_HARD", [h["type"] for h in r["hits"]])
                self.assertEqual(r["hard_count"], 0)

    def test_mixed_line_narration_outside_quotes_still_hard(self):
        """同为混合行：引号外叙述层出现「不是X，是Y」仍须 FAIL_HARD。"""
        r = scan_text("# 第999章 测试\n他要的不是答案，是权限。“交给我。”\n")
        self.assertIn("NOT_IS_HARD", [h["type"] for h in r["hits"]])
        self.assertEqual(r["verdict"], "FAIL_HARD")

    def test_mixed_line_narration_hard_with_halfwidth_dialogue(self):
        """半角引号混合行同理：叙述层命中仍判硬闸。"""
        r = scan_text('# 第999章 测试\n他要的不是答案，是权限。"交给我。"\n')
        self.assertIn("NOT_IS_HARD", [h["type"] for h in r["hits"]])
        self.assertEqual(r["verdict"], "FAIL_HARD")


if __name__ == "__main__":
    unittest.main()
