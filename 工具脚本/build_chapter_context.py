#!/usr/bin/env python3
"""科武纪元章节上下文压缩器。

目标：减少 token、降低幻觉。
只输出当前章需要的最小上下文包：
- 前置门禁状态
- 上一章记忆卡
- 当前章WAL目标（若有）
- 大纲锚点
- 最近章节首尾摘录

用法：
  python3 build_chapter_context.py --chapter 228
  python3 build_chapter_context.py --chapter 228 --write
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
NEW = BASE / '新版'
OUTLINE = BASE / '科武纪元大纲V8.md'
REVIEW = BASE / '审核记录' / '六角色外审'
CARD = BASE / '审核记录' / '章节记忆卡'
WAL = BASE / '审核记录' / 'WAL'
CTX = BASE / '审核记录' / '上下文包'
GATE = BASE / '工具脚本' / 'check_review_gate.py'


def read(p: Path, limit: int | None = None) -> str:
    if not p.exists():
        return ''
    s = p.read_text(encoding='utf-8', errors='ignore')
    return s[:limit] if limit else s


def cn_count(s: str) -> int:
    return sum(1 for c in s if '\u4e00' <= c <= '\u9fff')


def excerpt_chapter(ch: int, head: int = 900, tail: int = 900) -> str:
    p = NEW / f'第{ch}章.md'
    if not p.exists():
        p = NEW / f'第{ch:03d}章.md'
    if not p.exists():
        return f'第{ch}章文件不存在'
    s = p.read_text(encoding='utf-8', errors='ignore')
    non = [x for x in s.splitlines() if x.strip()]
    first = non[0] if non else ''
    last = non[-1] if non else ''
    return f'''文件: {p}
标题: {first}
字数: {cn_count(s)}
末行: {last}
首段摘录:
{s[:head]}

末段摘录:
{s[-tail:]}
'''


def outline_anchor(ch: int) -> str:
    s = read(OUTLINE)
    if not s:
        return '大纲缺失'
    # 只截 V8 第五卷表，避免命中过往 V7 备份造成上下文污染。
    m = re.search(r'## 第五卷·归途[\s\S]*?(?=\n---\n|\n## V7|\Z)', s)
    block = m.group(0) if m else s
    keep = []
    for line in block.splitlines():
        if any(x in line for x in [
            '223-233', '234-244', '245-250', '251', '252', '253', '254-258',
            '第五卷', '章号 | 功能'
        ]):
            keep.append(line)
    if 223 <= ch <= 233:
        focus = '当前章属 223-233：供应链保卫/东屿产线。稳住东屿产线和南天门认证供应链，避免金融-舆论连锁挤兑。'
    elif 234 <= ch <= 244:
        focus = '当前章属 234-244：归途坐标暗线。火星坐标只做暗线推进，不抢地球危机主线。'
    elif 245 <= ch <= 250:
        focus = '当前章属 245-250：铁幕反扑。合法程序、资本、媒体、代理人多线施压。'
    elif 254 <= ch <= 258:
        focus = '当前章属 254-258：卷尾收束。回收地球危机，明确第六卷火星/深空方向。'
    else:
        focus = '当前章属第五卷弹性/过渡区：地球危机主线优先，火星/归途只做暗线。'
    return focus + '\n' + '\n'.join(keep[:12])


def gate_status(ch: int) -> str:
    # 不调用子进程，直接读 index 简化
    idx = read(REVIEW / 'index.md')
    prev = ch - 1
    if f'| {prev} | PASS ' in idx:
        return f'GATE_OK: 第{prev}章 PASS，可准备第{ch}章。'
    return f'GATE_UNKNOWN_OR_BLOCKED: 请先运行 check_review_gate.py --next {ch}。'


def budget_note(text: str) -> str:
    chars = len(text)
    est_tokens = max(1, chars // 2)
    level = 'OK' if chars <= 12000 else 'TOO_LARGE'
    return f'字符数: {chars}；粗略token估算: {est_tokens}；状态: {level}。若超过12KB，优先删早期摘录，保留门禁/上一章记忆卡/大纲锚点/末尾摘录。'


def build(ch: int) -> str:
    prev = ch - 1
    prev2 = ch - 2
    parts = []
    parts.append(f'# 第{ch}章最小上下文包')
    parts.append('')
    parts.append('## 预算规则')
    parts.append('目标≤12KB；信息优先级：门禁 > 上一章记忆卡 > 大纲锚点 > 上章末尾 > 前章简摘。')
    parts.append('')
    parts.append('## 0. 门禁')
    parts.append(gate_status(ch))
    parts.append('开始写作前仍需执行：')
    parts.append(f'`python3 {GATE} --next {ch}`')
    parts.append('')
    parts.append('## 1. 大纲锚点')
    parts.append(outline_anchor(ch))
    parts.append('')
    parts.append('## 2. 上一章记忆卡')
    parts.append(read(CARD / f'第{prev:03d}章.md') or read(CARD / f'第{prev}章.md') or '缺上一章记忆卡')
    parts.append('')
    parts.append('## 3. 前两章简摘')
    parts.append(excerpt_chapter(prev2, 500, 500))
    parts.append(excerpt_chapter(prev, 700, 900))
    parts.append('')
    parts.append('## 4. 当前章WAL草案')
    wal = read(WAL / f'第{ch:03d}.md') or read(WAL / f'第{ch}.md')
    parts.append(wal if wal else '暂无。写作前需新建 WAL：目标/大纲锚点/允许/禁止/验收。')
    parts.append('')
    parts.append('## 5. 审稿输入规则')
    parts.append('- 给外部角色只发：摘要 + 大纲锚点 + 首尾摘录 + 高风险段。')
    parts.append('- 每个角色输入≤1800中文；输出≤500中文。')
    parts.append('- 禁止整章/整卷无差别塞入。')
    parts.append('- 若需要全文，只在本地脚本中统计，不发给模型。')
    body = '\n'.join(parts).strip() + '\n'
    body = body.replace('## 预算规则\n目标≤12KB；信息优先级：门禁 > 上一章记忆卡 > 大纲锚点 > 上章末尾 > 前章简摘。', '## 预算规则\n目标≤12KB；信息优先级：门禁 > 上一章记忆卡 > 大纲锚点 > 上章末尾 > 前章简摘。\n' + budget_note(body))
    return body


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapter', type=int, required=True)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    out = build(args.chapter)
    if args.write:
        CTX.mkdir(parents=True, exist_ok=True)
        p = CTX / f'第{args.chapter:03d}章_context.md'
        p.write_text(out, encoding='utf-8')
        print(p)
    else:
        print(out)

if __name__ == '__main__':
    main()
