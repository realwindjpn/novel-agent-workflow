#!/usr/bin/env python3
"""第259章代词修正：林星辰为男性（wiki/characters/林星辰.md L29「性别 | 男」）。

本章女性角色：谢云、陈思琪 —— 她们的「她」必须保留。
本章男性角色：林星辰、方宁、赵大山、老周。

判定采用显式行号白名单，不用启发式。
逐行核对第259章.md 全文后得出：指代林星辰的「她/她的」所在行为
L7, L12, L15, L18(无), L22, L26(她转身), L30, L31, L35, L37, L38, L45, L49, L54, L56, L60, L61。

其中：
- L19「她沉默了几秒」→ 谢云，保留。
- L45「谢云递过来一支葡萄糖注射液，她没接」→ 她=林星辰，改。
- L53「他看了一眼林星辰」→ 方宁，本就是「他」，不动。
"""
import re
import shutil
from pathlib import Path

PATH = Path('/root/workspace/科武纪元/新版/第259章.md')

# 指代林星辰、需要把「她」改成「他」的行号（1-indexed）
LINXINGCHEN_LINES = {7, 12, 15, 22, 26, 30, 31, 35, 37, 38, 45, 49, 54, 56, 60, 61}

# 明确保留（女性角色）的行号
FEMALE_KEEP_LINES = {19}


def main() -> None:
    text = PATH.read_text(encoding='utf-8')
    lines = text.split('\n')

    backup = PATH.with_suffix('.md.bak_pronoun')
    shutil.copy2(PATH, backup)

    changes = []
    for idx, line in enumerate(lines, start=1):
        if idx in FEMALE_KEEP_LINES:
            continue
        if idx not in LINXINGCHEN_LINES:
            continue
        if '她' not in line:
            continue
        new_line = line.replace('她', '他')
        if new_line != line:
            # 记录改动片段用于人工复核
            for m in re.finditer('她', line):
                s = max(0, m.start() - 12)
                e = min(len(line), m.end() + 12)
                changes.append((idx, line[s:e]))
            lines[idx - 1] = new_line

    PATH.write_text('\n'.join(lines), encoding='utf-8')

    print(f'backup   : {backup}')
    print(f'changed  : {len(changes)} occurrences')
    for idx, frag in changes:
        print(f'  L{idx}: ...{frag}...')

    # 复核：全文残留「她」
    after = PATH.read_text(encoding='utf-8')
    remain = []
    for idx, line in enumerate(after.split('\n'), start=1):
        for m in re.finditer('她', line):
            s = max(0, m.start() - 14)
            e = min(len(line), m.end() + 14)
            remain.append((idx, line[s:e]))
    print(f'\nremaining 她: {len(remain)}')
    for idx, frag in remain:
        print(f'  L{idx}: ...{frag}...')


if __name__ == '__main__':
    main()
