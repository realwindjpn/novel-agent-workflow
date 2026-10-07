#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
科武纪元·大纲准绳单一解析入口  outline_canon.py

存在理由（2026-10-07）：
    20+ 个脚本各自硬编码不同大纲路径（V8 / latest / V8.6 / V8.md），
    导致同一批任务里混用版本。本模块是**唯一**取大纲的地方。

铁律：
    所有脚本一律 `from outline_canon import outline_path, outline_text, outline_row`
    不得再自行拼大纲路径。

用法:
    from outline_canon import outline_path, outline_text, outline_row, CANON_VERSION
    p = outline_path()          # Path
    t = outline_text()          # 全文
    r = outline_row(368)        # {'volume','title','plot','subtext','target_cjk'}
"""
import re
import sys
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
REL = ('任务运行态/20261003_kewu_selfcycle_daily/output/'
       '科武纪元大纲V9_500章_重建稿_G2备注版.md')

CANON_VERSION = 'V9_G2备注版'
CANON_MTIME = '2026-10-07 01:23'

# 已知的非准绳路径（用于 lint 扫描，命中即报警）
NON_CANON_PATTERNS = [
    r'科武纪元大纲\s*V8',
    r'科武纪元大纲V8',
    r'wiki/raw/outline/科武纪元大纲_latest\.md',
    r'科武纪元大纲V9_500章_修订稿\.md',
    r'科武纪元大纲V9_500章_重建稿\.md(?!_G2)',
]


def outline_path() -> Path:
    p = BASE / REL
    if not p.exists():
        raise FileNotFoundError(
            f'大纲准绳缺失: {p}\n准绳应为 {CANON_VERSION}（{CANON_MTIME}）')
    return p


def outline_text() -> str:
    return outline_path().read_text(encoding='utf-8')


def outline_row(chapter: int) -> dict:
    """取该章大纲行：卷/标题/情节/暗线/目标字数。无则 {}。"""
    for line in outline_text().split('\n'):
        if re.match(r'^\|\s*%d\s*\|' % chapter, line):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cells) >= 6:
                return {
                    'chapter': chapter,
                    'volume': cells[1] or None,
                    'title': cells[2] or None,
                    'plot': cells[3] or None,
                    'subtext': cells[4] or None,
                    'target_cjk': int(cells[5]) if cells[5].isdigit() else None,
                }
    return {}


def lint_scripts() -> list:
    """扫描 工具脚本/*.py，报出仍硬编码非准绳大纲的脚本。"""
    import re as _re
    pats = [_re.compile(p) for p in NON_CANON_PATTERNS]
    out = []
    d = BASE / '工具脚本'
    for f in sorted(d.glob('*.py')):
        if f.name in ('outline_canon.py',):
            continue
        try:
            t = f.read_text(encoding='utf-8')
        except Exception:
            continue
        for i, line in enumerate(t.split('\n'), 1):
            s = line.strip()
            if s.startswith('#'):
                continue
            if any(p.search(s) for p in pats):
                out.append((f.name, i, s[:110]))
    return out


if __name__ == '__main__':
    if '--lint' in sys.argv:
        hits = lint_scripts()
        print(f'仍硬编码非准绳大纲的脚本: {len(hits)} 处')
        for name, ln, s in hits[:40]:
            print(f'  {name}:{ln}  {s}')
        sys.exit(0)
    print('准绳:', outline_path())
    print('版本:', CANON_VERSION, '|', CANON_MTIME)
    r = outline_row(368)
    print('第368章:', r.get('title'), '|', r.get('volume'), '|', r.get('target_cjk'))
