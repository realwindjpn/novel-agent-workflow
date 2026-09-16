#!/usr/bin/env python3
"""一次性脚本：拆掉 fanqie_update_draft_chapter.py 的发布地雷（save_draft 零 fetch）。"""
from pathlib import Path

p = Path('/root/workspace/科武纪元/工具脚本/fanqie_update_draft_chapter.py')
text = p.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)

start = end = None
for i, ln in enumerate(lines):
    if ln.startswith('def save_draft('):
        start = i
    if ln.startswith('def verify_listing('):
        end = i
        break
assert start is not None and end is not None, (start, end)

new_save = r'''def save_draft(session: str, state_path: Path | None = None) -> dict:
    """只点「存草稿」按钮（button.auto-editor-save-btn）保存。零 fetch。

    2026-09-08 第317章事故：
    旧实现误用 POST /api/author/publish_article/v0/（form, publish_status=0,
    timer_status=0）「保存草稿」，但该端点是**发布端点**，对待发布章节会直接发布，
    导致第317章提前上线。本实现已彻底移除该路径，零 fetch 兜底。

    铁律：
    - 保存动作只能点击 DOM 中「存在且 enabled」的 button.auto-editor-save-btn。
    - 该按钮渲染条件为 0===publishStatus（仅「未发布草稿」状态才渲染）。
    - 按钮不存在 / disabled → 章节处于待发布/已发布，立即 raise，不发任何写请求。

    绝不查找、不点击「下一步 / 提交 / 确认发布」。
    """
    js = r"""
(() => {
  const btn = document.querySelector('button.auto-editor-save-btn');
  if (!btn) {
    return {exists: false, disabled: null, reason: 'no_save_btn'};
  }
  const disabled = btn.disabled === true
      || btn.getAttribute('aria-disabled') === 'true'
      || btn.classList.contains('disabled');
  if (disabled) {
    return {exists: true, disabled: true, reason: 'save_btn_disabled'};
  }
  btn.click();
  return {exists: true, disabled: false, clicked: true};
})()
"""
    state = js_eval(session, js, timeout=30, state_path=state_path)
    if not isinstance(state, dict) or not state.get('exists') or state.get('disabled'):
        raise RuntimeError(
            'PENDING_OR_PUBLISHED_REJECT: 章节非「未发布草稿」状态，'
            'button.auto-editor-save-btn 不存在或不可用，拒绝保存以防误发布。'
            '（2026-09-08 317事故：误用 publish_article 端点直接发布）'
            f' | state={state}'
        )

    time.sleep(3)
    js_readback = r"""
(() => {
 const txt = document.body.innerText || '';
 const m = txt.match(/正文字数\s*([0-9]+)/);
 return {
   url: location.href,
   saved: txt.includes('已保存'),
   word: m ? m[1] : null,
 };
})()
"""
    saved = js_eval(session, js_readback, state_path=state_path)
    if not isinstance(saved, dict):
        raise RuntimeError(f'存草稿后读回异常: {saved}')
    return saved


'''

new_lines = lines[:start] + [new_save] + lines[end:]
text2 = ''.join(new_lines)

old_doc = '    adapter.getHTML() 返回编辑器 HTML，供 save_draft 的 API 调用使用。\n'
new_doc = '    adapter.getHTML() 返回编辑器 HTML（仅诊断/读回用，不用于任何写请求）。\n'
assert old_doc in text2, 'docstring anchor missing'
text2 = text2.replace(old_doc, new_doc)

old_call = '    saved = save_draft(args.session, data, state_path=args.state)\n'
new_call = '    saved = save_draft(args.session, state_path=args.state)\n'
assert old_call in text2, 'main call anchor missing'
text2 = text2.replace(old_call, new_call)

p.write_text(text2, encoding='utf-8')

print('=== 残留扫描（应全为 0）===')
for needle in ['publish_article', 'fetch(', 'publish_status', 'timer_status']:
    print(f'SCAN {needle!r}: {text2.count(needle)} 处')
print('REJECT 串存在:', 'PENDING_OR_PUBLISHED_REJECT' in text2)
print('存草稿按钮选择器存在:', 'button.auto-editor-save-btn' in text2)
print('总行数:', len(text2.splitlines()))
print('OK')
