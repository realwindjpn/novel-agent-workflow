#!/usr/bin/env python3
"""核查林星辰人称代词在已投稿章节与新稿中的一致性。

方法：取「林星辰」出现位置之后 60 字窗口，统计首个出现的 他/她。
"""
import glob
import os
import re

TARGET = '林星辰'


def scan(path: str):
    t = open(path, encoding='utf-8').read()
    male = female = 0
    for m in re.finditer(TARGET, t):
        window = t[m.end():m.end() + 60]
        # 找窗口内第一个第三人称单数代词
        hit = re.search(r'[他她]', window)
        if not hit:
            continue
        if hit.group() == '他':
            male += 1
        else:
            female += 1
    return male, female, t.count(TARGET)


rows = []
for c in range(250, 261):
    for pat in (f'已投稿/第{c}章.txt', f'新版/第{c}章.md'):
        if os.path.exists(pat):
            male, female, total = scan(pat)
            rows.append((pat, total, male, female))

print(f"{'file':<26} {'林星辰':>6} {'他':>5} {'她':>5}  判定")
for path, total, male, female in rows:
    if male and female:
        verdict = 'MIXED(冲突)'
    elif male:
        verdict = '男'
    elif female:
        verdict = '女'
    else:
        verdict = '无代词'
    print(f"{path:<26} {total:>6} {male:>5} {female:>5}  {verdict}")
