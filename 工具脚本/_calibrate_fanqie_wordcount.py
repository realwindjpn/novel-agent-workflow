#!/usr/bin/env python3
"""校准番茄字数口径：用已知番茄回读值反推统计规则。

已知样本：
- 错稿第259章.txt → 番茄列表显示 4891 字
- 第253章 → 番茄列表显示 3709 字
- 第254章 → 番茄列表显示 4312 字
"""
import re
import os

SAMPLES = [
    ('/root/workspace/科武纪元/备份/20260812_101551_ch259_wrong_europa/第259章.txt', 4891),
    ('/root/workspace/科武纪元/已投稿/第253章.txt', 3709),
    ('/root/workspace/科武纪元/已投稿/第254章.txt', 4312),
]


def strip_author_note(t: str) -> str:
    """番茄正文字数不含「作者有话说」段。"""
    for marker in ('作者有话说', '作者说：', '作者的话'):
        idx = t.find(marker)
        if idx != -1:
            return t[:idx]
    return t


def variants(raw: str):
    body = strip_author_note(raw)
    return {
        'cjk_only_full': len(re.findall(r'[\u4e00-\u9fff]', raw)),
        'cjk_only_body': len(re.findall(r'[\u4e00-\u9fff]', body)),
        'nonspace_body': len(re.sub(r'\s', '', body)),
        'nonspace_full': len(re.sub(r'\s', '', raw)),
        'total_body': len(body),
        'total_full': len(raw),
    }


print(f"{'sample':<12} {'fanqie':>7} | " + ' '.join(f'{k:>16}' for k in
      ['cjk_only_full', 'cjk_only_body', 'nonspace_body', 'nonspace_full', 'total_body', 'total_full']))

score = {}
for path, expect in SAMPLES:
    if not os.path.exists(path):
        print(f"MISSING: {path}")
        continue
    raw = open(path, encoding='utf-8').read()
    v = variants(raw)
    name = os.path.basename(path).replace('.txt', '')
    row = ' '.join(f'{v[k]:>16}' for k in
                   ['cjk_only_full', 'cjk_only_body', 'nonspace_body', 'nonspace_full', 'total_body', 'total_full'])
    print(f"{name:<12} {expect:>7} | {row}")
    for k, val in v.items():
        score.setdefault(k, []).append(abs(val - expect))

print()
print("平均绝对误差（越小越接近番茄口径）：")
for k, errs in sorted(score.items(), key=lambda x: sum(x[1]) / len(x[1])):
    print(f"  {k:<16} {sum(errs)/len(errs):>8.1f}")
