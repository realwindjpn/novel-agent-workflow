#!/usr/bin/env python3
"""Generate 已投稿TXT for ch121 from candidate draft."""
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
cand = (BASE / '审核记录/自循环体系会议_20260530/ch121_author_refined_mimo.md').read_text()

author_note = '\n\n作者有话说：航道外十二海里线替代原北纬30度线，贴合东屿实际地理与无人机航程。武者电磁场定位为谐振触发预充能脉冲，非人体直接供能。量子磁传感阵列用于陀螺仪精确定位。'
txt = cand.rstrip() + author_note + '\n'

out = BASE / '已投稿/第121章.txt'
out.write_text(txt)

content = ''.join(l.strip() for l in txt.split('\n'))
title = txt.split('\n')[0].strip()
wc = len(content) - len(title)
print(f'TXT: {out}')
print(f'WordCount: {wc}')
print(f'wikilink: {txt.count("[[")}')
print(f'has_author_note: {"作者有话说" in txt}')
