#!/usr/bin/env python3
"""第335章 初产作者任务卡打包器（确定性）。

按 qwen-web-longform-pipeline 的打包纪律：
  - 所有约束从 G3_PREP_335.json 原文读取，不手抄
  - 硬闸清单显式写引号制式（防弯引号整片回潮）
  - 禁词只写判据类别，不逐字列举（防作者照抄成硬命中）
  - 打包后读回自验：字节数、关键锚点、禁项自查
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

TASK = Path('/root/workspace/科武纪元/任务运行态/20260918_kewu_selfcycle_daily')
G3 = TASK / 'output' / 'G3_PREP_335.json'
OUT = Path('/root/workspace/科武纪元/任务运行态/20260918_kewu_selfcycle_daily/output/AUTHOR_PROMPT_335.md')

# 科武官方硬闸扫描器禁用词表（自检用，不写进卡）
SCANNER_HARD = re.compile(r'接住|击穿|锋利|不崩|不爆|打穿|扛住')
CURLY = re.compile(r'[\u201c\u201d\u2018\u2019]')


def main() -> int:
    d = json.loads(G3.read_text(encoding='utf-8'))
    ch = d['chapter']
    title = d['title']
    volume = d['volume']
    hg = d['hard_gates']
    locked = d['locked_constraints']
    entry = d['entry_interface']
    plot = d['plot_seed']
    fore = d['foreshadow']
    cjk_min = hg['cjk_min']
    prev_ch = d.get('prev_chapter')

    parts = []
    parts.append(f'# 任务：创作《科武纪元》第{ch}章《{title}》正文')
    parts.append('')
    parts.append(f'卷属：{volume}')
    parts.append(f'净中文硬线：{cjk_min} 起（唯一硬线，无业务上限）。'
                 f'大纲目标 {d.get("target_chars")} 仅参考，不据此判超长。')
    parts.append('')

    parts.append('## 一、本章剧情种子（大纲权威，不得改写走向）')
    parts.append('')
    parts.append(plot)
    parts.append('')

    parts.append('## 二、本章须埋的伏笔（两条都要落进正文，写成可观测的物证）')
    parts.append('')
    for i, f in enumerate([x for x in fore.split('；') if x.strip()], 1):
        parts.append(f'{i}. {f.strip()}')
    parts.append('')

    parts.append(f'## 三、与第{prev_ch}章的衔接（上章结尾原文，本章须自然接上）')
    parts.append('')
    for line in entry:
        parts.append(f'- {line}')
    parts.append('')
    parts.append(f'衔接要求：本章开篇承接上述场景，不得重述上章已写过的动作，'
                 f'不得让上章未完成的评估凭空消失。')
    parts.append('')

    parts.append('## 四、锁定约束（canon，逐条硬性，违反即整章作废）')
    parts.append('')
    for i, c in enumerate(locked, 1):
        parts.append(f'{i}. {c}')
    parts.append('')

    parts.append('## 五、格式硬闸（机器扫描，逐项必过）')
    parts.append('')
    parts.append(f'- 首行必须精确等于：{hg["first_line"]}')
    parts.append(f'- 末行必须精确等于：{hg["last_line"]}')
    parts.append(f'- 净中文（仅计汉字）≥ {cjk_min}')
    parts.append('- 数字一律中文数字。正文禁阿拉伯数字（仅首行标题的章号例外）。')
    parts.append('- 对话引号一律用直角引号「」。禁用弯引号（全角弯双引号与弯单引号一律禁），'
                 '禁用半角双引号。需要再引一层时直接去掉内层引号写词，不加任何替代引号。')
    parts.append('- 禁破折号、禁 markdown 加粗、禁 wikilink、禁裸章号引用、禁代码块。')
    parts.append('')

    parts.append('## 六、写法要求（本项目「人味」口径）')
    parts.append('')
    parts.append('必须做到：')
    parts.append('- 物理反馈优先：仪表读数、体感、手部动作、现场声响、身体代价，'
                 '让读者从可观测现象推出结论。')
    parts.append('- 科学机制落到工程量：延迟预算、误差边界、置信度回读、散热与功率代价，'
                 '不写超越物理极限的效果。')
    parts.append('- 制度约束具名：谁签字、谁担责、谁看日志、通报延迟、权限移交，'
                 '写成留痕动作而非抽象伦理。')
    parts.append('- 人物潜台词：动机与阵营关系由选择、代价、隐瞒显出，不由旁白替读者总结。')
    parts.append('- 章末留钩子：给出可追索的新问题或新后果，不写议论升华。')
    parts.append('')
    parts.append('必须避免（按判据自查，不按词表）：')
    parts.append('- 空泛咏叹与文艺比喻堆叠：形容词叠加而无可观测指向的句子一律删。')
    parts.append('- 解释腔：替读者总结含义、复述刚写过的结论。')
    parts.append('- 清单腔：把流程写成条目罗列、字段罗列、编号规则罗列。')
    parts.append('- 否定—肯定对举的公式句式（含用句号拆成两句的变体）。')
    parts.append('- 节奏均匀：相邻段落字数不得长期接近，须有长短句剧烈交替，'
                 '至少出现若干十字以内的短句。')
    parts.append('- 角色口吻趋同：不同人物的说话方式须可区分。')
    parts.append('')

    parts.append('## 七、输出格式')
    parts.append('')
    parts.append('直接输出正文全文，不要任何前言、说明、修改清单、自评或格式说明。')
    parts.append(f'首行「{hg["first_line"]}」，末行「{hg["last_line"]}」。')
    parts.append('')

    text = '\n'.join(parts) + '\n'

    # 自检：卡本身不得命中扫描器禁用词，不得含弯引号示例
    hard_hits = SCANNER_HARD.findall(text)
    if hard_hits:
        print(json.dumps({'status': 'CARD_SELFCHECK_FAIL',
                          'reason': 'card_contains_scanner_hard_words',
                          'hits': sorted(set(hard_hits))}, ensure_ascii=False))
        return 2

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding='utf-8')

    # 读回自验
    back = OUT.read_text(encoding='utf-8')
    checks = {
        'bytes': len(back.encode('utf-8')),
        'first_line_anchor_present': hg['first_line'] in back,
        'last_line_anchor_present': hg['last_line'] in back,
        'cjk_min_stated': str(cjk_min) in back,
        'locked_count': len(locked),
        'entry_lines': len(entry),
        'no_scanner_hard_words': not SCANNER_HARD.search(back),
        'no_curly_quote_example': not CURLY.search(back),
        'sha256': hashlib.sha256(back.encode('utf-8')).hexdigest(),
    }
    ok = (checks['first_line_anchor_present'] and checks['last_line_anchor_present']
          and checks['no_scanner_hard_words'] and checks['no_curly_quote_example']
          and checks['bytes'] > 2000)
    print(json.dumps({'status': 'PACKED' if ok else 'PACKAGING_FAIL',
                      'path': str(OUT), 'checks': checks},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 3


if __name__ == '__main__':
    sys.exit(main())
