#!/usr/bin/env python3
"""第335章 R5 拼接：回归大纲口径修正科学席/去AI席 R4 复审 FAIL。

R5 修的是 R4 遗留 + R4 主控代拟数值引入的新错：
  段5 瞳孔潜伏期（11ms 误作绝对值 → 眼间差 + 224/235 绝对基线）
  段6 补接触阻抗链 + 蚀刻去功能区
  段A 走廊三分法 + 能量来源修正（信号是他的、功率是设备的）
  段B 删伪读数体温 + 换重复动作
  段C 压清单腔
  段D 文艺腔给视觉落点
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

TASK = Path('/root/workspace/科武纪元/任务运行态/20260918_kewu_selfcycle_daily')
SRC = TASK / 'output' / 'qwen_335_r4.md'
BATCHES = [
    TASK / 'output' / 'qwen_335_r5_b1.md',
    TASK / 'output' / 'qwen_335_r5_b2.md',
]
DST = TASK / 'output' / 'qwen_335_r5.md'

CJK = re.compile(r'[\u4e00-\u9fff]')
CURLY = re.compile(r'[\u201c\u201d\u2018\u2019]')
BLOCK = re.compile(r'【段\s*([0-9A-D])\s*】')

# key -> (r4 中首句片段, r4 中末句片段)
SEG_BOUNDS = {
    '5': ('医疗技师拿起笔形光源', '备注栏写：待追踪，原因未明。'),
    '6': ('舱内，医疗技师开始逐枚回收电极', '密封取样袋。'),
    # r4 实际结构：走廊对话是 L49-L64 多行块（「十一毫秒。」起，「但陈思琪的档案里会有。」止）
    # 段B 的体温伪读数在 L53 行内，与走廊块重叠 → 一并由段A 覆盖
    'A': ('「十一毫秒。」', '但陈思琪的档案里会有。'),
}

MUST_HAVE = [
    '每秒两千帧',            # 科学#2 采样率
    '二百二十四点三毫秒',    # 科学#1 绝对基线
    '差值十一点二',          # 科学#1 眼间差
    '三毫秒以内',            # 科学#1 正常带参照
    '残差均值零点零八毫秒',  # 科学#2 插值残差
    '四十七千欧',            # 科学#4 阻抗链
    '深部阵列覆盖图',        # 科学#5 分级接口
    '功率是设备的',          # 科学#3 能量来源
    '纯电化学失效',          # 科学#3 三分法
]
MUST_GONE = [
    '采样率每秒五百帧',              # 旧栅格矛盾
    '栅格两毫秒，十一点一卡在两格之间',  # 旧反向论证
    '映射区域：情感抑制区',          # 科学#5 旧蚀刻
    '反向灌入了电极',                # 科学#3 旧因果
    '他的体温在正常范围内',          # 去AI 伪读数
    '所有被动监测数据都在正常区间内',  # 去AI 报告腔
    '不是损伤后的随机偏移',          # 去AI 公式句
]
# 段C 在 r4 中与人物动作同行，只替换句尾读数串，保留前半句
SEG_C_OLD = '呼吸平稳。心率五十九。血氧正常。体温三十六点四度。所有被动监测数据都在正常区间内。'


def parse_blocks(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    marks = [(m.start(), m.end(), m.group(1)) for m in BLOCK.finditer(text)]
    for i, (_s, e, key) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out[key] = text[e:end].strip()
    return out


def build_corridor_block(blocks: dict[str, str]) -> str:
    """把段A（三分法对话）与段B（方宁动作）合成 r4 走廊块的完整替换。

    r4 的走廊块是 L49-L64 连续多行；批二把它拆成 A/B 两段返回，
    其中 B 只是块内一行（原 L53 的体温伪读数行）。这里按 r4 的叙事顺序
    重组：开场读数 → 三分法推演（段A）→ 方宁动作（段B）→ 收束。
    """
    seg_a = blocks['A'].strip().splitlines()
    seg_b = blocks['B'].strip()
    # 段A 末两行是「这句话不进通报」与「所以才不进通报」，方宁动作插在其前
    tail_idx = next((i for i, l in enumerate(seg_a) if '这句话不进通报' in l), len(seg_a))
    head = seg_a[:tail_idx]
    tail = seg_a[tail_idx:]
    out = list(head)
    out.append(seg_b)
    out.extend(tail)
    out.append('「不进。」林星辰说。「但陈思琪的档案里会有。」')
    return '\n'.join(out)


def main() -> int:
    src_text = SRC.read_text(encoding='utf-8')
    blocks: dict[str, str] = {}
    for bp in BATCHES:
        blocks.update(parse_blocks(bp.read_text(encoding='utf-8')))

    if SEG_C_OLD not in src_text:
        print(json.dumps({'status': 'SEG_C_ANCHOR_MISSING'}, ensure_ascii=False))
        return 7
    needed = {'5', '6', 'A', 'B', 'C'}
    missing = [k for k in sorted(needed) if k not in blocks]
    if missing:
        print(json.dumps({'status': 'BLOCK_MISSING', 'missing': missing,
                          'got': sorted(blocks)}, ensure_ascii=False))
        return 2
    # 段A 覆盖整个走廊块，需并入段B
    blocks['A'] = build_corridor_block(blocks)

    lines = src_text.splitlines()
    spans: list[tuple[int, int, str]] = []
    for key, (head, tail) in SEG_BOUNDS.items():
        start = next((i for i, l in enumerate(lines) if head in l), None)
        if start is None:
            print(json.dumps({'status': 'HEAD_NOT_FOUND', 'seg': key,
                              'frag': head}, ensure_ascii=False))
            return 3
        end = next((i + 1 for i in range(start, len(lines)) if tail in lines[i]), None)
        if end is None:
            print(json.dumps({'status': 'TAIL_NOT_FOUND', 'seg': key,
                              'frag': tail}, ensure_ascii=False))
            return 4
        spans.append((start, end, key))

    spans.sort(key=lambda x: x[0])
    for (s1, e1, k1), (s2, _e2, k2) in zip(spans, spans[1:]):
        if e1 > s2:
            print(json.dumps({'status': 'SPAN_OVERLAP', 'a': k1, 'b': k2,
                              'a_end': e1, 'b_start': s2}, ensure_ascii=False))
            return 5

    new_lines = list(lines)
    removed_cjk = 0
    added_cjk = 0
    for start, end, key in sorted(spans, key=lambda x: x[0], reverse=True):
        removed_cjk += len(CJK.findall('\n'.join(lines[start:end])))
        added_cjk += len(CJK.findall(blocks[key]))
        new_lines[start:end] = blocks[key].splitlines()

    text = '\n'.join(new_lines)
    # 段C：行内替换读数串，保留同行人物动作
    seg_c_new = blocks['C'].strip()
    if SEG_C_OLD not in text:
        print(json.dumps({'status': 'SEG_C_LOST_AFTER_SPLICE'}, ensure_ascii=False))
        return 8
    removed_cjk += len(CJK.findall(SEG_C_OLD))
    added_cjk += len(CJK.findall(seg_c_new))
    text = text.replace(SEG_C_OLD, seg_c_new)
    if not text.endswith('\n'):
        text += '\n'

    nonempty = [l for l in text.splitlines() if l.strip()]
    body = '\n'.join(nonempty[1:])
    cjk_new = len(CJK.findall(text))
    cjk_old = len(CJK.findall(src_text))
    expected = cjk_old - removed_cjk + added_cjk

    have_missing = [s for s in MUST_HAVE if s not in text]
    gone_residual = [s for s in MUST_GONE if s in text]

    guards = {
        'first_line_ok': nonempty[0].strip() == '第335章 人机融合',
        'last_line_ok': nonempty[-1].strip() == '（本章完）',
        'cjk_new': cjk_new,
        'cjk_old': cjk_old,
        'cjk_expected': expected,
        'cjk_delta_exact': cjk_new == expected,
        'cjk_ge_3200': cjk_new >= 3200,
        'removed_cjk': removed_cjk,
        'added_cjk': added_cjk,
        'no_block_markers': not BLOCK.search(text),
        'curly_quotes': len(CURLY.findall(text)),
        'half_quotes': text.count('"'),
        'arabic_in_body': len(re.findall(r'\d', body)),
        'markdown_bold': text.count('**'),
        'wikilink': text.count('[['),
        'dash': text.count('——'),
        'formula_ju': len(re.findall(r'不是.{0,20}而是', text)),
        'dup_lines': len(nonempty) - len(set(nonempty)),
        'review_must_have_missing': have_missing,
        'review_must_gone_residual': gone_residual,
    }

    ok = (guards['first_line_ok'] and guards['last_line_ok']
          and guards['cjk_delta_exact'] and guards['cjk_ge_3200']
          and guards['no_block_markers'] and guards['curly_quotes'] == 0
          and guards['half_quotes'] == 0 and guards['arabic_in_body'] == 0
          and guards['markdown_bold'] == 0 and guards['wikilink'] == 0
          and guards['dash'] == 0 and guards['formula_ju'] == 0
          and guards['dup_lines'] == 0 and not have_missing
          and not gone_residual)

    if ok:
        DST.write_text(text, encoding='utf-8')
        guards['sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest()
        guards['path'] = str(DST)

    print(json.dumps({'status': 'SPLICED' if ok else 'SPLICE_GUARD_FAIL',
                      'guards': guards}, ensure_ascii=False, indent=2))
    return 0 if ok else 6


if __name__ == '__main__':
    sys.exit(main())
