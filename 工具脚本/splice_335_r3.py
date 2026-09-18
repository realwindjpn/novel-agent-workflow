#!/usr/bin/env python3
"""第335章 R3 返修拼接：用 fix_r3 四段替换 r2 中对应段落。

策略：按【段N】标记提取 fix_r3 的四段，替换 r2 中从该段首句到该段末句的整段。
用首尾锚点精确定位，拼接后跑全部硬闸。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

TASK = Path('/root/workspace/科武纪元/任务运行态/20260918_kewu_selfcycle_daily')
SRC = TASK / 'output' / 'qwen_335_r2.md'
FIX = TASK / 'output' / 'qwen_335_fix_r3.md'
DST = TASK / 'output' / 'qwen_335_r3.md'

CJK = re.compile(r'[\u4e00-\u9fff]')
CURLY = re.compile(r'[\u201c\u201d\u2018\u2019]')
BLOCK = re.compile(r'【段\s*([1-9])\s*】')

# 每段的首句（用于在 r2 中找到段落起点）
SEG_STARTS = {
    1: '陈思琪的手指在代谢面板上划了一下',
    2: '屏幕上的波形突然安静了',
    3: '他又动了一下嘴唇',
    4: '陈思琪把四组数据并排投在舱外主屏上',
}
# 每段的末句（用于确定段落终点）
SEG_ENDS = {
    1: '骨缝发出一声很轻的响。',
    2: '然后他落回去。',
    3: '也辨不出元音的共振。',  # fix_r3 新末句
    4: '备注栏写：待追踪，原因未明。',
}


def parse_blocks(text: str) -> dict[int, str]:
    out: dict[int, str] = {}
    marks = [(m.start(), m.end(), int(m.group(1))) for m in BLOCK.finditer(text)]
    for i, (_s, e, num) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out[num] = text[e:end].strip()
    return out


def find_segment(text: str, start_frag: str, end_frag: str) -> tuple[int, int] | None:
    """Find a segment by its start fragment and end fragment.
    Returns (start_idx, end_idx) where end_idx is after the end fragment's line.
    """
    lines = text.splitlines()
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if start_idx is None and start_frag in line:
            start_idx = i
        if start_idx is not None and end_frag in line:
            end_idx = i + 1
            break
    if start_idx is not None and end_idx is not None:
        return (start_idx, end_idx)
    return None


def main() -> int:
    src_text = SRC.read_text(encoding='utf-8')
    fix_text = FIX.read_text(encoding='utf-8')
    blocks = parse_blocks(fix_text)

    missing = [n for n in (1, 2, 3, 4) if n not in blocks]
    if missing:
        print(json.dumps({'status': 'BLOCK_MISSING', 'missing': missing}, ensure_ascii=False))
        return 2

    lines = src_text.splitlines()
    # For each segment, find start and end in r2
    # But we need to handle r2's old content for segments 1,2,3,4
    # r2 has the same segment starts but different ends for seg 3 (old end was different)
    
    # Build the replacement map
    replacements: list[tuple[int, int, str]] = []
    for num in (1, 2, 3, 4):
        start_frag = SEG_STARTS[num]
        # For the end, use the r2 text to find where each segment ends
        # seg 1 ends with '骨缝发出一声很轻的响。'
        # seg 2 ends with '然后他落回去。'
        # seg 3 in r2 ends with '是气流经过声门时声带没有闭合的杂音。' (old)
        # seg 4 ends with '备注栏写：待追踪，原因未明。'
        
        # Find start line
        start_idx = None
        for i, line in enumerate(lines):
            if start_frag in line:
                start_idx = i
                break
        if start_idx is None:
            print(json.dumps({'status': 'START_NOT_FOUND', 'seg': num,
                              'frag': start_frag}, ensure_ascii=False))
            return 3
        
        # Find end line: search forward from start for the end fragment
        # For r2, the old seg 3 end was different, so we need to use old ends
        OLD_ENDS = {
            1: '骨缝发出一声很轻的响。',
            2: '然后他落回去。',
            3: '是气流经过声门时声带没有闭合的杂音。',  # r2 old end
            4: '备注栏写：待追踪，原因未明。',
        }
        end_frag = OLD_ENDS[num]
        end_idx = None
        for i in range(start_idx, len(lines)):
            if end_frag in lines[i]:
                end_idx = i + 1
                break
        if end_idx is None:
            print(json.dumps({'status': 'END_NOT_FOUND', 'seg': num,
                              'frag': end_frag}, ensure_ascii=False))
            return 4
        
        replacements.append((start_idx, end_idx, blocks[num]))
    
    # Apply replacements in reverse order to preserve indices
    replacements.sort(key=lambda x: x[0], reverse=True)
    new_lines = list(lines)
    for start_idx, end_idx, replacement in replacements:
        new_lines[start_idx:end_idx] = replacement.splitlines()
    
    text = '\n'.join(new_lines)
    if not text.endswith('\n'):
        text += '\n'
    
    # Guards
    nonempty = [l for l in text.splitlines() if l.strip()]
    body = '\n'.join(nonempty[1:])
    cjk_new = len(CJK.findall(text))
    cjk_old = len(CJK.findall(src_text))
    
    # Expected: old CJK - removed CJK + added CJK
    removed_cjk = 0
    added_cjk = 0
    for start_idx, end_idx, replacement in replacements:
        old_seg = '\n'.join(lines[start_idx:end_idx])
        removed_cjk += len(CJK.findall(old_seg))
        added_cjk += len(CJK.findall(replacement))
    expected = cjk_old - removed_cjk + added_cjk
    
    guards = {
        'first_line_ok': nonempty[0].strip() == '第335章 人机融合',
        'last_line_ok': nonempty[-1].strip() == '（本章完）',
        'cjk_new': cjk_new,
        'cjk_old': cjk_old,
        'cjk_expected': expected,
        'cjk_delta_exact': cjk_new == expected,
        'cjk_ge_3200': cjk_new >= 3200,
        'no_block_markers': not BLOCK.search(text),
        'curly_quotes': len(CURLY.findall(text)),
        'half_quotes': text.count('"'),
        'arabic_in_body': len(re.findall(r'\d', body)),
        'markdown_bold': text.count('**'),
        'wikilink': text.count('[['),
        'dash': text.count('——'),
        'formula_ju': len(re.findall(r'不是.{0,20}而是', text)),
        'dup_lines': len(nonempty) - len(set(nonempty)),
        'removed_cjk': removed_cjk,
        'added_cjk': added_cjk,
    }
    
    # Check for residual old patterns
    old_patterns = [
        '不是消失，是频率',
        '不是词。是气流',
        '不是波动，不是噪声。是恒定',
        '接住代谢负担',
    ]
    guards['old_patterns_gone'] = all(p not in text for p in old_patterns)
    
    ok = (guards['first_line_ok'] and guards['last_line_ok']
          and guards['cjk_delta_exact'] and guards['cjk_ge_3200']
          and guards['no_block_markers'] and guards['curly_quotes'] == 0
          and guards['half_quotes'] == 0 and guards['arabic_in_body'] == 0
          and guards['markdown_bold'] == 0 and guards['wikilink'] == 0
          and guards['dash'] == 0 and guards['formula_ju'] == 0
          and guards['dup_lines'] == 0 and guards['old_patterns_gone'])
    
    if ok:
        DST.write_text(text, encoding='utf-8')
        guards['sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest()
        guards['path'] = str(DST)
    
    print(json.dumps({'status': 'SPLICED' if ok else 'SPLICE_GUARD_FAIL',
                      'guards': guards}, ensure_ascii=False, indent=2))
    return 0 if ok else 5


if __name__ == '__main__':
    sys.exit(main())
