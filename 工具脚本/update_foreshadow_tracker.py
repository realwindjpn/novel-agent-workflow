#!/usr/bin/env python3
"""轻量伏笔跟踪器：不调用模型。

来源：
1. 小说综合跟踪表.md 的「伏笔追踪」表
2. wiki/plot-threads/*.md 的主题链文件
3. wiki/chapters/ch*.md 的 Ending Hook / Next Chapter Hook

输出：wiki/plot-threads/foreshadowing-index.md
原则：只做索引与证据定位，不重写剧情，不增加模型负担。
"""
from __future__ import annotations
from pathlib import Path
import re
from datetime import datetime

BASE = Path('/root/workspace/科武纪元')
TRACKING = BASE / '小说综合跟踪表.md'
PLOT_DIR = BASE / 'wiki/plot-threads'
CH_DIR = BASE / 'wiki/chapters'
OUT = PLOT_DIR / 'foreshadowing-index.md'


def clean_cell(s: str) -> str:
    return re.sub(r'\s+', ' ', s.strip())


def parse_tracking_table() -> list[dict]:
    if not TRACKING.exists():
        return []
    text = TRACKING.read_text(encoding='utf-8')
    m = re.search(r'## 四、伏笔追踪\(高优先级\)(.*?)(?=\n---\n|\n## )', text, re.S)
    if not m:
        return []
    rows=[]
    for line in m.group(1).splitlines():
        line=line.strip()
        if not line.startswith('| F'):
            continue
        cells=[clean_cell(x) for x in line.strip('|').split('|')]
        if len(cells) < 5:
            continue
        rows.append({'id':cells[0], 'plant':cells[1], 'content':cells[2], 'status':cells[3], 'payoff':cells[4]})
    return rows


def parse_plot_threads() -> list[dict]:
    items=[]
    if not PLOT_DIR.exists():
        return items
    for p in sorted(PLOT_DIR.glob('*.md')):
        if p.name == OUT.name:
            continue
        text=p.read_text(encoding='utf-8', errors='ignore')
        title=next((ln.strip('# ').strip() for ln in text.splitlines() if ln.startswith('#')), p.stem)
        chain=''
        m=re.search(r'## 核心链\n(.+?)(?=\n## |\Z)', text, re.S)
        if m:
            chain=clean_cell(m.group(1).replace('`',''))[:300]
        elif '伏笔' in text or '线索' in text or 'hook' in text.lower():
            chain=clean_cell(text[:500])
        items.append({'file':p.name, 'title':title, 'chain':chain})
    return items


def section(text: str, name: str) -> str:
    m=re.search(rf'## {re.escape(name)}\n(.+?)(?=\n## |\Z)', text, re.S)
    if not m:
        return ''
    val='\n'.join(x.strip() for x in m.group(1).splitlines() if x.strip())
    if 'TODO' in val:
        return ''
    return clean_cell(val)


def parse_chapter_hooks(limit_latest: int=80) -> list[dict]:
    items=[]
    for p in sorted(CH_DIR.glob('ch*.md')):
        m=re.search(r'ch(\d+)\.md$', p.name)
        if not m:
            continue
        ch=int(m.group(1))
        text=p.read_text(encoding='utf-8', errors='ignore')
        ending=section(text, 'Ending Hook') or section(text, 'Ending Hook Evidence')
        nxt=section(text, 'Next Chapter Hook')
        if ending or nxt:
            items.append({'chapter':ch, 'ending':ending[:220], 'next':nxt[:220]})
    # 全量太长，只保留最新/有价值；早期高优先级仍由表管理
    return items[-limit_latest:]


def status_bucket(s: str, payoff: str) -> str:
    s=s or ''
    payoff=payoff or ''
    if '已回收' in s or re.search(r'\d', payoff) and '待' not in payoff:
        return '已回收/部分回收'
    if '待' in s or '待' in payoff:
        return '待回收'
    if '高价值' in s or '重大' in s:
        return '高优先级'
    return s or '未标注'


def build() -> str:
    now=datetime.now().strftime('%Y-%m-%d %H:%M')
    rows=parse_tracking_table()
    threads=parse_plot_threads()
    hooks=parse_chapter_hooks()
    out=[]
    out += ['# 科武纪元·伏笔跟踪索引', '', f'更新时间：{now}', '',
            '> 轻量索引，不调用模型。主表仍是 `小说综合跟踪表.md`；长链证据放 `wiki/plot-threads/` 与章节 Wiki。', '',
            '## 结论', '',
            '- 伏笔没有消失：高优先级条目仍在 `小说综合跟踪表.md`。',
            '- 但此前只列了8条，且 `sync_kewu.py` 只同步章节 Wiki/Vector/STATUS/WAL，没有自动维护伏笔链。',
            '- 本文件作为统一入口：高优先级伏笔 + 主题链 + 章节钩子证据。', '',
            '## A. 高优先级伏笔（来自综合跟踪表）', '',
            '| ID | 埋设章 | 内容 | 状态桶 | 回收章/去向 |',
            '|---|---:|---|---|---|']
    for r in rows:
        out.append(f"| {r['id']} | {r['plant']} | {r['content']} | {status_bucket(r['status'], r['payoff'])} | {r['payoff']} |")
    if not rows:
        out.append('| - | - | 未解析到伏笔表 | - | - |')
    out += ['', '## B. 主题链文件（来自 wiki/plot-threads）', '', '| 文件 | 标题 | 链路摘要 |', '|---|---|---|']
    for t in threads:
        out.append(f"| `{t['file']}` | {t['title']} | {t['chain'] or '（无核心链摘要）'} |")
    out += ['', '## C. 章节钩子证据（最近章节 Wiki，非TODO）', '', '| 章节 | Ending Hook | Next Chapter Hook |', '|---:|---|---|']
    for h in hooks:
        out.append(f"| {h['chapter']} | {h['ending'] or '-'} | {h['next'] or '-'} |")
    out += ['', '## D. 低负担优化规则', '',
            '1. 不新增常驻模型任务。每次精修/同步后运行本脚本即可。',
            '2. 模型只在具体章节外审时判断“是否回收/是否误埋”；索引生成一律脚本完成。',
            '3. 跟踪表只放高优先级伏笔；普通章节钩子留在章节 Wiki，避免主表膨胀。',
            '4. 每条伏笔只保留五字段：ID、埋设章、内容、状态桶、回收章/去向。',
            '5. 新素材若只是主题，不直接变伏笔；必须能指向章节动作或回收章。', '']
    return '\n'.join(out)


def main():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding='utf-8')
    print(OUT)

if __name__ == '__main__':
    main()
