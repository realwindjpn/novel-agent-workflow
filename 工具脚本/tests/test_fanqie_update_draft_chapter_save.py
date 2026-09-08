#!/usr/bin/env python3
"""离线单测：fanqie_update_draft_chapter.save_draft 零 fetch 防误发布门禁。

mock js_eval / time.sleep，不碰网络、不开浏览器、不调任何真实接口。
覆盖（2026-09-08 第317章事故拆弹任务书）：
- 按钮存在且 enabled → 点击成功，返回存后读回 dict
- 按钮不存在 → RuntimeError PENDING_OR_PUBLISHED_REJECT（含 2026-09-08 317事故 溯源），
  且不再发起任何后续请求
- 按钮 disabled（disabled 属性 / aria-disabled / class）→ 同上拒绝
- 源码零 fetch( 调用；publish_article 仅存于 docstring/注释，不构成写路径（零 fetch 兜底）
- replace_body 的 adapter.view.dispatch 主路径与 execCommand fallback 必须保留（防回归）
"""
import ast
import importlib.util
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "fanqie_update_draft_chapter.py"
spec = importlib.util.spec_from_file_location("fanqie_save_disarm", MODULE_PATH)
assert spec is not None and spec.loader is not None
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

SRC = MODULE_PATH.read_text(encoding="utf-8")
_TREE = ast.parse(SRC)


def _publish_lines():
    return [ln for ln in SRC.splitlines() if "publish_article" in ln]


def _fake_js_eval(script_calls, returns):
    """返回 (fake_func, calls)。calls 累积 (js, timeout)；returns 逐次弹出。"""
    calls = []

    def fake(session, js, timeout=60, state_path=None):
        calls.append((js, timeout, state_path))
        return returns.pop(0) if returns else None

    script_calls.append(calls)
    return fake


class SaveDraftGateTests(unittest.TestCase):
    def setUp(self):
        self.calls_holder: list = []
        self.sleep_patch = mock.patch.object(m.time, "sleep")
        self.sleep_patch.start()
        self.addCleanup(self.sleep_patch.stop)

    def _patch_js_eval(self, returns):
        fake = _fake_js_eval(self.calls_holder, returns)
        patcher = mock.patch.object(m, "js_eval", fake)
        patcher.start()
        self.addCleanup(patcher.stop)

    # ---------------- 场景：按钮存在且可用 → 点击成功 ----------------
    def test_btn_present_click_success(self):
        self._patch_js_eval([
            {"exists": True, "disabled": False, "clicked": True},
            {"saved": True, "word": "3000", "url": "https://fanqie/edit/123"},
        ])
        out = m.save_draft("sess")
        self.assertIsInstance(out, dict)
        self.assertTrue(out["saved"])
        self.assertEqual(out["word"], "3000")
        # 恰好两次 js_eval：查按钮+click、存后读回；中间无任何写请求
        calls = self.calls_holder[0]
        self.assertEqual(len(calls), 2)
        first_js = calls[0][0]
        self.assertIn("auto-editor-save-btn", first_js)
        self.assertIn("btn.click()", first_js)
        # 点击路径的 JS 不允许出现任何 fetch 字样
        self.assertNotIn("fetch", first_js)
        self.assertNotIn("publish_article", first_js)

    # ---------------- 场景：按钮不存在 → 立即拒绝，零写请求 ----------------
    def test_btn_missing_rejects_and_no_requests_after(self):
        self._patch_js_eval([
            {"exists": False, "disabled": None, "reason": "no_save_btn"},
        ])
        with self.assertRaises(RuntimeError) as ctx:
            m.save_draft("sess")
        msg = str(ctx.exception)
        self.assertIn("PENDING_OR_PUBLISHED_REJECT", msg)
        self.assertIn("2026-09-08", msg)
        self.assertIn("317", msg)
        self.assertIn("publish_article", msg)
        # 拒绝后不再有任何第二次调用（读回/写请求都不应发生）
        self.assertEqual(len(self.calls_holder[0]), 1)

    # ---------------- 场景：按钮 disabled → 同上拒绝 ----------------
    def test_btn_disabled_rejects(self):
        for disabled_state in (
            {"exists": True, "disabled": True, "reason": "save_btn_disabled"},
        ):
            self.calls_holder.clear()
            self._patch_js_eval([disabled_state])
            with self.assertRaises(RuntimeError) as ctx:
                m.save_draft("sess")
            self.assertIn("PENDING_OR_PUBLISHED_REJECT", str(ctx.exception))
            self.assertEqual(len(self.calls_holder[0]), 1)

    def test_js_missing_and_disabled_return_paths(self):
        # 源码 JS 层面对「不存在 / disabled」返回明确标记，供 Python 侧拒绝
        self.assertIn("no_save_btn", SRC)
        self.assertIn("save_btn_disabled", SRC)
        self.assertIn("aria-disabled", SRC)

    # ---------------- 源码级：零 fetch 兜底 ----------------
    def test_source_zero_fetch_call(self):
        # 整个脚本不允许出现任何 fetch( 调用 —— 零 fetch 兜底，不只是 publish_article
        self.assertNotIn("fetch(", SRC)
        self.assertNotIn("fetch (", SRC)
        self.assertNotIn("fetch(", SRC.replace(" ", ""))

    def test_no_fetch_call_node_in_ast(self):
        # ast 层面同样不得存在 fetch(...) 调用节点（覆盖 fetch 与 ( 间有换行的写法）
        for node in ast.walk(_TREE):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id == "fetch":
                self.fail(f"发现 fetch 调用节点: {ast.unparse(node)}")

    def test_publish_article_never_in_any_fetch_context(self):
        # 事故记录必须保留（docstring/注释/错误消息文本均可，供追溯），
        # 但 publish_article 绝不允许与 fetch 共现于任何一行/任一调用路径
        lines = _publish_lines()
        self.assertTrue(lines, "publish_article 事故记录应保留供追溯")
        for ln in lines:
            self.assertNotIn("fetch", ln, f"publish_article 与 fetch 共现: {ln!r}")

    # ---------------- 防回归：replace_body 新主路径必须保留 ----------------
    def test_replace_body_keeps_adapter_dispatch_and_fallback(self):
        self.assertIn("adapter.view.dispatch", SRC)
        self.assertIn("view.dispatch(tr)", SRC)
        # execCommand fallback 保留（adapter 不可用时回退）
        self.assertIn("execCommand('selectAll')", SRC)
        self.assertIn("execCommand('insertText'", SRC)
        # 代码路径禁止 innerHTML 直写（275章污染根因）；
        # docstring/JS 字符串属文本，不作为判据 —— 以 ast.Attribute 精确判定
        inner_html_nodes = [
            ast.unparse(n) for n in ast.walk(_TREE)
            if isinstance(n, ast.Attribute) and n.attr == "innerHTML"
        ]
        self.assertEqual([], inner_html_nodes)

    # ---------------- 防回归：主流程仍按 替换→存草稿→复核 顺序 ----------------
    def test_main_flow_keeps_replace_then_save(self):
        self.assertIn("replaced = replace_body(args.session, data, state_path=args.state)", SRC)
        self.assertIn("saved = save_draft(args.session, state_path=args.state)", SRC)
        self.assertIn("verified = verify_listing(", SRC)
        self.assertIn("stayed_in_draft", SRC)


if __name__ == "__main__":
    unittest.main()