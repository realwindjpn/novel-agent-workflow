#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""6 章措辞级返修派工卡（2026-09-26）

背景：kewu_deai_hard_gate_scan.py 新增五条闸后，基线 PASS 被翻成 FAIL_HARD 的文件共 11 个
（.md/.txt 各一），对应 6 章：205/316/324/325/340/350。基线全库 PASS=174 → 语境版 160。

本轮返修范围**严格限定为 7 处硬命中**，不是整章重写：
  - 4 处「仿佛」文艺比喻（第205 L30、第316 L8、第340 L44、第350 L21/L25）——bad_phrases 明令删除
  - 1 处「这不仅是…更是…」公式句（第213 之外的那处在第350 L21 邻近；实际命中见下表）
  - 2 处「」包裹长词组（第324 L49「箱底夹层有异」6字、第325 L12「月衡字通报」5字）——5-6字已是一般性结论

写死约束（防三类返工）：
1. 每处只改该处，**同行其余文字逐字不动**——包括数值、专名、单据名、代码、时间。
2. 不得改变情节、人物立场、逻辑链、动作反馈。
3. 不得引入新禁用词。改后自行 grep 确认。
4. 改后净 CJK 与原行差异应 < 30 字（措辞级），若超过说明改过头，须回退重做。

模型：cn:hy4-preview（WorkBuddy 张老师，Qwen 席）。跨族核验另派。
"""
import json, re, subprocess, sys, hashlib
from pathlib import Path

CH = Path('/root/workspace/科武纪元')
OUT = CH / '任务运行态' / '20260925_kewu_selfcycle_daily' / 'output' / 'revision_6ch'
OUT.mkdir(parents=True, exist_ok=True)

# 逐处精确定位（章, 行, 原行全文, 命中类型, 改法要求）
TARGETS = [
    (205, 30, 'BANNED_WORD_HARD', '「仿佛意识被抽离了躯壳」——比喻写意识离体。改法：直接写身体感受与认知缺口的物理表现，不要"像被抽离"这类喻体。'),
    (316,  8, 'BANNED_WORD_HARD', '「仿佛什么都没发生过」——比喻收尾。改法：直接写指示灯已回绿、无人处置，让"什么都没发生"由事实本身承担，不加"仿佛"。'),
    (324, 49, 'QUOTED_TERM_HARD', '「箱底夹层有异」5-6字结论式引号包裹。改法：这是入库单上的字段名，属公文原词，改为不加引号的直接引述或叙述转述（例：她把图片放大，盯着入库单上那行字——箱底夹层有异。拇指悬在屏幕上方，没有滑动）。字段内容本身必须逐字保留。'),
    (325, 12, 'QUOTED_TERM_HARD', '「月衡字通报」5字公文名被引号包裹。改法：按公文引用惯例改为书名号《》或直接叙述不加引号。通报名"月衡字通报"与回执编号"衡字第八十三号"逐字保留。'),
    (340, 44, 'BANNED_WORD_HARD', '「仿佛整艘飞船都在经历一场高烧」——比喻。改法：改写为铆钉金属悲鸣的实际声响特征与管壁温差的可见反馈，不使用"像发烧"喻体。'),
    (350, 21, 'BANNED_WORD_HARD', '「仿佛它从一开始就是这么定的」——比喻收尾。改法：改为由排版事实承担（数字是黑色的，字体和正文一致，和上下两行没有区别），去掉"仿佛"。'),
    (350, 25, 'BANNED_WORD_HARD', '「仿佛那阵振动与它无关」——比喻。改法：改为直接陈述观测事实（漂移幅度没有变化，维持在布朗区间内），让"与它无关"由数值本身承担。'),
]

BANNED = ['仿佛', '宛如', '微微', '缓缓', '意味着', '意识到', '不禁', '不由得',
          '这一刻', '某种意义上', '这不仅是', '时代洪流', '命运齿轮', '—']


def build_card(ch, ln, typ, req):
    path = CH / f'新版/第{ch}章.md'
    lines = path.read_text(encoding='utf-8').splitlines()
    orig = lines[ln - 1]
    cjk = len(re.findall(r'[一-鿿]', orig))
    return f"""【返修卡 · 第{ch}章 第{ln}行 · {typ}】

要改的行（原文，逐字）：
{orig}

这一行现在的 CJK 字符数：{cjk}

改法要求：
{req}

硬约束（违反即作废）：
1. **只改这一行**。同章其他行一个字都不许动。
2. 同行内的数字、专名、单据名、代号、文件名、时间、坐标逐字保留。
   第325章特别注意："月衡字通报""衡字第八十三号""零点零四个兆帕""传感器零漂，非泄漏""三号线公路以东十一公里"全是剧情数据，一个字不能改。
3. 不得改变情节、人物立场、动作顺序、逻辑因果。
4. 改后这一行不得出现以下任一词：{'、'.join(BANNED)}
5. 改后净 CJK 与 {cjk} 的差值绝对值 < 30。若超过 30，说明改过头了，请回退重写。
6. 不要加解释、不要加"修改说明"、不要输出任何前后缀。

输出格式（严格）：
只输出改好后的这一整行正文，不要行号，不要引号包裹整行，不要任何其他内容。
"""


def main():
    cards = []
    for ch, ln, typ, req in TARGETS:
        card = build_card(ch, ln, typ, req)
        p = OUT / f'card_{ch}_{ln}.md'
        p.write_text(card, encoding='utf-8')
        cards.append({'ch': ch, 'line': ln, 'type': typ, 'card': str(p),
                      'sha_before': hashlib.sha256((CH / f'新版/第{ch}章.md').read_bytes()).hexdigest()[:16]})
    (OUT / 'manifest.json').write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'已生成 {len(cards)} 张返修卡 → {OUT}')
    for c in cards:
        print(f"  第{c['ch']}章 L{c['line']} {c['type']}")


if __name__ == '__main__':
    main()
