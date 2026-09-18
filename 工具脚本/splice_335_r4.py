#!/usr/bin/env python3
"""第335章 R4 五席审稿返修拼接（四批合并）。

R4 被拆成四批投递（13.6KB 整卡撞输入上限导致假成功，见 pitfall）：
  b1 = 段1-4, b3 = 段5-6, b4 = 段7-8（b2 整批回 57 字符判空，已弃）

每段在 r3 中按「首句片段 + 末句片段」定位整段边界后整体替换。
拼接后守卫：首末行、净 CJK、标记残留、引号、阿拉伯数字、重复行，
外加审稿点逐条回归断言（新数值在、旧数值无）。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

TASK = Path('/root/workspace/科武纪元/任务运行态/20260918_kewu_selfcycle_daily')
SRC = TASK / 'output' / 'qwen_335_r3.md'
BATCHES = [
    TASK / 'output' / 'qwen_335_r4_b1.md',
    TASK / 'output' / 'qwen_335_r4_b3.md',
    TASK / 'output' / 'qwen_335_r4_b4.md',
]
DST = TASK / 'output' / 'qwen_335_r4.md'

CJK = re.compile(r'[\u4e00-\u9fff]')
CURLY = re.compile(r'[\u201c\u201d\u2018\u2019]')
BLOCK = re.compile(r'【段\s*([1-8])\s*】')

# 每段在 r3 中的边界：(首句片段, 末句片段)
SEG_BOUNDS = {
    1: ('陈思琪的手指在代谢面板上划了一下', '骨缝发出一声很轻的响。'),
    2: ('苏雨晴用拇指按住谢云耳后乳突骨的下缘', '继续往下一枚走。'),
    3: ('屏幕上的波形突然安静了', '然后他落回去。'),
    # 段4 在 r3 中跨两段（L36 动作段 + L38 气音段），末句取 r3 原文而非改写后文本
    4: ('谢云的嘴唇动了一下。喉结上提', '辨不出元音的共振。'),
    5: ('医疗技师拿起笔形光源', '备注栏写：待追踪，原因未明。'),
    6: ('舱内，医疗技师开始逐枚回收电极', '密封取样袋里。'),
    # 段7 在 r3 中是 L61 单行；末句锚点不可用「插进外套口袋」（L6 也含该串）
    7: ('但他没有说话。不是不想说。', '那条调度链路，断了。'),
    8: ('方宁从口袋里拿出手持终端', '谢云没有告诉她任何一个数字代表什么感受。'),
}

# 审稿点回归：改后必须出现 / 必须消失
MUST_HAVE = [
    '七十二爬到八十一毫米汞柱',   # 科学#1 灌注压量级
    '残余肾清除率',                # 科学#2 判据
    '十一点二毫秒',                # 科学#3 非零方差
    '标准差零点三毫秒',            # 科学#3
    '红外瞳孔计',                  # 科学#4 装备
    '每秒五百帧',                  # 科学#4
    '导电膏碳化沉积',              # 科学#5 能量级
    '浅二度',                      # 科学#5 皮肤链
    '第三号电极，第三触点',        # 编辑 编号一致
]
MUST_GONE = [
    '四十二毫米汞柱',              # 旧休克级数值
    '肌酐清除率',                  # 旧误用判据
    '标准差为零',                  # 旧零方差
    '落在结构性偏移的判定区间内',  # 去AI 旧盖章
    '不是不想说',                  # 去AI 旧公式句
    '声带在，气息在，舌头在',      # 去AI 旧排比
    '金属再凝固的毛刺',            # 科学#5 旧熔融
    '所有数字都在。',              # 去AI 旧对称收束
    '像砂纸擦过木头',              # 去AI 重复比喻
    '在容许带内',                  # 去AI 判定式句尾
    '清除率与灌注压均维持在代偿量程内',  # 旧报告腔
    '灰色文件袋',                  # 读者 旧后勤冗段
]


def parse_blocks(text: str) -> dict[int, str]:
    out: dict[int, str] = {}
    marks = [(m.start(), m.end(), int(m.group(1))) for m in BLOCK.finditer(text)]
    for i, (_s, e, num) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out[num] = text[e:end].strip()
    return out


def main() -> int:
    src_text = SRC.read_text(encoding='utf-8')
    blocks: dict[int, str] = {}
    for bp in BATCHES:
        blocks.update(parse_blocks(bp.read_text(encoding='utf-8')))

    missing = [n for n in range(1, 9) if n not in blocks]
    if missing:
        print(json.dumps({'status': 'BLOCK_MISSING', 'missing': missing,
                          'got': sorted(blocks)}, ensure_ascii=False))
        return 2

    lines = src_text.splitlines()
    spans: list[tuple[int, int, int]] = []
    for num, (head, tail) in SEG_BOUNDS.items():
        start = next((i for i, l in enumerate(lines) if head in l), None)
        if start is None:
            print(json.dumps({'status': 'HEAD_NOT_FOUND', 'seg': num,
                              'frag': head}, ensure_ascii=False))
            return 3
        end = next((i + 1 for i in range(start, len(lines)) if tail in lines[i]), None)
        if end is None:
            print(json.dumps({'status': 'TAIL_NOT_FOUND', 'seg': num,
                              'frag': tail}, ensure_ascii=False))
            return 4
        spans.append((start, end, num))

    # 区间不得重叠
    spans.sort(key=lambda x: x[0])
    for (s1, e1, n1), (s2, _e2, n2) in zip(spans, spans[1:]):
        if e1 > s2:
            print(json.dumps({'status': 'SPAN_OVERLAP', 'a': n1, 'b': n2,
                              'a_end': e1, 'b_start': s2}, ensure_ascii=False))
            return 5

    new_lines = list(lines)
    removed_cjk = 0
    added_cjk = 0
    for start, end, num in sorted(spans, key=lambda x: x[0], reverse=True):
        removed_cjk += len(CJK.findall('\n'.join(lines[start:end])))
        added_cjk += len(CJK.findall(blocks[num]))
        new_lines[start:end] = blocks[num].splitlines()

    text = '\n'.join(new_lines)
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
        'zaine_count': text.count('在容许带内') + text.count('量程内')
                       + text.count('判定区间内') + text.count('正常区间内')
                       + text.count('正常范围内'),
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
