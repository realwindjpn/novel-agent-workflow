#!/usr/bin/env python3
"""第335章 R2 补段拼接（确定性，主控可直做）。

按 qwen-web-longform-pipeline 拼接纪律：
  - 锚点必须是源稿整行，投卡前已在源稿验 count==1
  - 拼接后守卫：首末行、净 CJK 下限、标记残留 0、弯引号 0、半角引号 0、
    正文阿拉伯数字 0、重复句 0
  - CJK 增量须等于补段净汉字数减去被替换句汉字数
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

TASK = Path('/root/workspace/科武纪元/任务运行态/20260918_kewu_selfcycle_daily')
SRC = TASK / 'output' / 'qwen_335_r1.md'
SUP = TASK / 'output' / 'qwen_335_supplement_r2.md'
DST = TASK / 'output' / 'qwen_335_r2.md'

CJK = re.compile(r'[\u4e00-\u9fff]')
CURLY = re.compile(r'[\u201c\u201d\u2018\u2019]')
BLOCK = re.compile(r'【(补|改)\s*([1-9])\s*】')

# 锚点：源稿整行（补段插在该行之后）
ANCHORS = {
    '补1': '「峰值到了。」她说。声音很平。「代偿效率百分之五十四。比预估低六个百分点，但肾脏灌注压稳住了。」',
    '补2': '谢云没立刻回答。他看着苏雨晴把第四枚电极贴上他的颞骨乳突后方，冰凉的金属片压住皮肤，他吸了口气。',
    '补3': '他的目光没有焦点。持续了大约两秒，然后瞳孔收缩，视线落在舱顶环形灯上。他张嘴。喉结动了一下。没有声音出来。',
    '补4': '方宁点了一下头，转身继续走。他的脚步声在走廊里渐渐变远。',
}
REPLACE_SRC = '没有表情。不是痛苦，不是平静。是空。像一面被擦干净的屏幕，什么数据都还没写上去。'


def parse_blocks(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    marks = [(m.start(), m.end(), f'{m.group(1)}{m.group(2)}') for m in BLOCK.finditer(text)]
    for i, (_s, e, key) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out[key] = text[e:end].strip()
    return out


def main() -> int:
    src = SRC.read_text(encoding='utf-8')
    sup = SUP.read_text(encoding='utf-8')
    blocks = parse_blocks(sup)

    missing = [k for k in (*ANCHORS, '改1') if k not in blocks]
    if missing:
        print(json.dumps({'status': 'BLOCK_MISSING', 'missing': missing,
                          'got': sorted(blocks)}, ensure_ascii=False))
        return 2

    lines = src.splitlines()
    # 锚点唯一性预检
    for key, anchor in ANCHORS.items():
        n = lines.count(anchor)
        if n != 1:
            print(json.dumps({'status': 'ANCHOR_FAIL', 'block': key, 'count': n,
                              'anchor': anchor[:50]}, ensure_ascii=False))
            return 3
    if src.count(REPLACE_SRC) != 1:
        print(json.dumps({'status': 'ANCHOR_FAIL', 'block': '改1',
                          'count': src.count(REPLACE_SRC)}, ensure_ascii=False))
        return 3

    # 插入补段
    out_lines: list[str] = []
    inserted: list[str] = []
    for line in lines:
        out_lines.append(line)
        for key, anchor in ANCHORS.items():
            if line == anchor:
                out_lines.append(blocks[key])
                inserted.append(key)
    if sorted(inserted) != sorted(ANCHORS):
        print(json.dumps({'status': 'INSERT_MISMATCH', 'inserted': inserted},
                         ensure_ascii=False))
        return 4

    text = '\n'.join(out_lines)
    # 改写句替换
    text = text.replace(REPLACE_SRC, blocks['改1'])
    if not text.endswith('\n'):
        text += '\n'

    nonempty = [l for l in text.splitlines() if l.strip()]
    cjk_new = len(CJK.findall(text))
    cjk_old = len(CJK.findall(src))
    sup_cjk = sum(len(CJK.findall(blocks[k])) for k in ANCHORS)
    repl_delta = len(CJK.findall(blocks['改1'])) - len(CJK.findall(REPLACE_SRC))
    expected = cjk_old + sup_cjk + repl_delta

    body = '\n'.join(nonempty[1:])
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
        'old_replaced_gone': REPLACE_SRC not in text,
        'new_replace_present': blocks['改1'] in text,
        'dup_lines': len(nonempty) - len(set(nonempty)),
    }
    ok = (guards['first_line_ok'] and guards['last_line_ok']
          and guards['cjk_delta_exact'] and guards['cjk_ge_3200']
          and guards['no_block_markers'] and guards['curly_quotes'] == 0
          and guards['half_quotes'] == 0 and guards['arabic_in_body'] == 0
          and guards['markdown_bold'] == 0 and guards['wikilink'] == 0
          and guards['dash'] == 0 and guards['formula_ju'] == 0
          and guards['old_replaced_gone'] and guards['new_replace_present']
          and guards['dup_lines'] == 0)

    if ok:
        DST.write_text(text, encoding='utf-8')
        guards['sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest()
        guards['path'] = str(DST)
    print(json.dumps({'status': 'SPLICED' if ok else 'SPLICE_GUARD_FAIL',
                      'guards': guards}, ensure_ascii=False, indent=2))
    return 0 if ok else 5


if __name__ == '__main__':
    sys.exit(main())
