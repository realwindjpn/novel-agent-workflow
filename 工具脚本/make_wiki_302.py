#!/usr/bin/env python3
"""建 302 wiki 章节页，格式照抄 ch301.md；并补 ch301 的 Next 链有效性。"""
import pathlib
import re

ROOT = pathlib.Path('/root/workspace/科武纪元')
WIKI = ROOT / 'wiki' / 'chapters'
body = (ROOT / '已投稿' / '第302章.txt').read_text(encoding='utf-8').strip()

cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
fanqie = len(re.sub(r'\s', '', body))

# 实体/概念从正文抽（出场人物 + 关键建制词）
PEOPLE = ['方宁', '林星辰', '陈思琪', '韩铮', '周棠', '苏雨晴', '马库斯·维尔']
CONCEPTS = ['泛际', '戴森球', '宪章', '监督委员会', '联邦', '算力', '铁幕']
ents = [p for p in PEOPLE if p in body]
cons = [c for c in CONCEPTS if c in body]

page = """---
chapter: 302
title: 第302章 戴森共识
updated: 2026-08-28
type: chapter
word_count_cn: {cjk}
fanqie_count: {fanqie}
---

# 第302章 戴森共识

## Links
- Previous: [[ch301]]
- Next: [[ch303]]

## KG Entities
- {ents}

## KG Concepts
- {cons}

## Full Text
{body}
""".format(cjk=cjk, fanqie=fanqie, ents=', '.join(ents),
           cons=', '.join(cons), body=body)

out = WIKI / 'ch302.md'
out.write_text(page, encoding='utf-8')
print('wrote', out, out.stat().st_size, 'B')

back = out.read_text(encoding='utf-8')
print('回读校验: 正文完整 %s | Prev链 %s | 字数字段 %s' % (
    body in back, '[[ch301]]' in back, ('word_count_cn: %d' % cjk) in back))
print('KG Entities:', ', '.join(ents))
print('KG Concepts:', ', '.join(cons))

# ch301 的 Next 已指向 ch302，核一下
p301 = WIKI / 'ch301.md'
t301 = p301.read_text(encoding='utf-8')
print('\nch301 Next 指向 ch302:', '[[ch302]]' in t301)
