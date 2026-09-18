#!/usr/bin/env python3
"""第336章 R2 拼接：补三段 + 改五句。"""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

TASK = Path('/root/workspace/科武纪元/任务运行态/20260918_kewu_selfcycle_daily')
SRC = TASK / 'output' / 'qwen_336_r1.md'
SUP = TASK / 'output' / 'qwen_336_r2_supplement.md'
DST = TASK / 'output' / 'qwen_336_r2.md'

CJK = re.compile(r'[\u4e00-\u9fff]')
CURLY = re.compile(r'[\u201c\u201d\u2018\u2019]')
BLOCK = re.compile(r'【(补|改)\s*([1-9])\s*】')

ANCHORS = {
    '补1': '她点开详情。',
    '补2': '然后停住。',
    '补3': '直到我们真的崩溃。」',
}
# 改写句的原文（精确匹配后替换）
REPLACEMENTS = {
    '改1': ('不是因为紧张。是因为连续工作十八个小时后的肌肉疲劳。',
            '连续工作十八个小时带来的肌肉疲劳让她的指尖不受控制地微颤。'),
    '改2': ('不是医疗系统的告警。是情报分析组的优先级中断请求。',
            '屏幕中央弹出一个红色提示框。上面显示着情报分析组的优先级中断请求。'),
    '改3': ('不能等。', ''),  # 删除
    '改4': ('训练有素的大脑在自动识别模式。',
            '她的目光沿着波形的上升沿快速扫过每一个极值点。'),
    '改5': ('距离她说的四十分钟还有十一分钟。',
            '距离她说的四十分钟还有十一分钟。'),  # 阿拉伯→中文，原文已是中文
}


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

    # Check补段
    missing = [k for k in (*ANCHORS, '改1','改2','改3','改4','改5') if k not in blocks]
    if missing:
        print(json.dumps({'status': 'BLOCK_MISSING', 'missing': missing}, ensure_ascii=False))
        return 2

    lines = src.splitlines()
    # 验证补段锚点唯一
    for key, anchor in ANCHORS.items():
        n = sum(1 for l in lines if anchor in l)
        if n != 1:
            print(json.dumps({'status': 'ANCHOR_FAIL', 'block': key, 'count': n,
                              'anchor': anchor[:40]}, ensure_ascii=False))
            return 3

    # 插入补段
    out_lines: list[str] = []
    inserted: list[str] = []
    for line in lines:
        out_lines.append(line)
        for key, anchor in ANCHORS.items():
            if anchor in line:
                out_lines.append(blocks[key])
                inserted.append(key)
    if sorted(inserted) != sorted(ANCHORS):
        print(json.dumps({'status': 'INSERT_MISMATCH', 'inserted': inserted}, ensure_ascii=False))
        return 4

    text = '\n'.join(out_lines)

    # 改写句替换
    for key, (old, new) in REPLACEMENTS.items():
        replacement = blocks[key].strip()
        if key == '改3' and replacement == '（删除此句）':
            replacement = ''
        if old == new:
            # 改5: 阿拉伯数字→中文，原文已是中文，跳过
            continue
        if old not in text:
            print(json.dumps({'status': 'REPLACE_NOT_FOUND', 'block': key,
                              'old': old[:40]}, ensure_ascii=False))
            return 5
        text = text.replace(old, replacement)

    # Fix R1 遗留的阿拉伯数字
    text = text.replace('第320章', '第三百二十章')
    # Fix 改5: 原文已是中文数字，但替换句与原文相同导致重复——跳过已处理
    # 去重：如果补段末句与原文下句重复，删掉重复行
    dedup_lines = text.splitlines()
    seen = set()
    out_dedup = []
    for l in dedup_lines:
        if l.strip() and l in seen:
            continue
        if l.strip():
            seen.add(l)
        out_dedup.append(l)
    text = '\n'.join(out_dedup)

    if not text.endswith('\n'):
        text += '\n'

    nonempty = [l for l in text.splitlines() if l.strip()]
    body = '\n'.join(nonempty[1:])
    cjk_new = len(CJK.findall(text))
    cjk_old = len(CJK.findall(src))

    guards = {
        'first_line_ok': nonempty[0].strip() == '第336章 外星真相',
        'last_line_ok': nonempty[-1].strip() == '（本章完）',
        'cjk_new': cjk_new,
        'cjk_old': cjk_old,
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
    }

    ok = (guards['first_line_ok'] and guards['last_line_ok']
          and guards['cjk_ge_3200'] and guards['no_block_markers']
          and guards['curly_quotes'] == 0 and guards['half_quotes'] == 0
          and guards['arabic_in_body'] == 0 and guards['markdown_bold'] == 0
          and guards['wikilink'] == 0 and guards['dash'] == 0
          and guards['formula_ju'] == 0 and guards['dup_lines'] == 0)

    if ok:
        DST.write_text(text, encoding='utf-8')
        guards['sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest()
        guards['path'] = str(DST)

    print(json.dumps({'status': 'SPLICED' if ok else 'SPLICE_GUARD_FAIL',
                      'guards': guards}, ensure_ascii=False, indent=2))
    return 0 if ok else 6


if __name__ == '__main__':
    sys.exit(main())
