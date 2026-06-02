#!/usr/bin/env python3
"""Generate 已投稿TXT for ch122."""
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
cand = (BASE / '新版/第122章.md').read_text()

author_note = '\n\n作者有话说：AI无人机置信度压制为电子战核心手段，通过污染多源感知数据降低决策可靠性，非简单信号干扰。量子增强抗干扰模式为独立高灵敏度感知链路。商船进入干扰叠合区的时间距离经科学复审校正。'
txt = cand.rstrip() + author_note + '\n'

out = BASE / '已投稿/第122章.txt'
out.write_text(txt)

content = ''.join(l.strip() for l in txt.split('\n'))
title = txt.split('\n')[0].strip()
wc = len(content) - len(title)
print(f'TXT: {out}')
print(f'WordCount: {wc}')
print(f'wikilink: {txt.count("[[")}')
print(f'has_author_note: {"作者有话说" in txt}')
