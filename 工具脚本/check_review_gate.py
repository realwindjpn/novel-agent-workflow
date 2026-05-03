#!/usr/bin/env python3
"""科武纪元第五卷六角色外审门禁检查。

用法：
  python3 check_review_gate.py --chapter 226
  python3 check_review_gate.py --next 226   # 检查能否开始写226：要求225 PASS
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
REVIEW_DIR = BASE / '审核记录' / '六角色外审'
CARD_DIR = BASE / '审核记录' / '章节记忆卡'
WAL_DIR = BASE / '审核记录' / 'WAL'
INDEX = REVIEW_DIR / 'index.md'

# 支持跨行和加粗
PASS_PAT = re.compile(r'(最终结论|复审结论|结论|主控裁决)[:：\s]*\*?(\*?\s*PASS|通过|小修后通过|小修后 PASS)', re.I | re.M)
BLOCK_PAT = re.compile(r'(REVIEW_NEEDED|FAIL|不通过|不得进入|不允许进入|禁止进入|继续修订|重写|严重偏离|严重断裂)', re.I)


def chapter_file(ch: int) -> Path:
    return REVIEW_DIR / f'第{ch:03d}章.md'


def read(ch: int) -> str:
    p = chapter_file(ch)
    if not p.exists():
        raise SystemExit(f'NO_REVIEW_RECORD 第{ch}章 缺审核记录: {p}')
    return p.read_text(encoding='utf-8', errors='ignore')


def final_section(text: str) -> str:
    # 只看最后一次最终/复审/门禁结论，避免早期 FAIL/REVIEW_NEEDED 污染最终结果。
    markers = [
        '## 复审结论',
        '## 最终结论',
        '# 门禁通过',
        '# 第224章 最终门禁补录',
        '# 第225章 小修补录',
    ]
    # 不再匹配 '# 第'，防止匹配到文件标题导致扫描全文。
    pos = max([text.rfind(m) for m in markers] + [-1])
    return text[pos:] if pos >= 0 else text[-1200:]


def status(ch: int) -> tuple[str, str]:
    text = read(ch)
    tail = final_section(text)
    has_pass = bool(PASS_PAT.search(tail))
    has_block = bool(BLOCK_PAT.search(tail)) and not re.search(r'(已patch完成|最终结论:\s*PASS|最终结论: PASS|最终结论\s*PASS|小修后通过)', tail)
    if has_pass and not has_block:
        return 'PASS', tail.strip()[-500:]
    return 'BLOCKED', tail.strip()[-500:]


def ensure_can_start(ch: int) -> None:
    prev = ch - 1
    st, detail = status(prev)
    if st != 'PASS':
        raise SystemExit(f'GATE_BLOCKED 不能开始第{ch}章：第{prev}章未PASS\n{detail}')
    print(f'GATE_OK 可开始第{ch}章：第{prev}章 PASS')


def rebuild_index() -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(REVIEW_DIR.glob('第*章.md')):
        m = re.search(r'第(\d+)章', p.name)
        if not m:
            continue
        ch = int(m.group(1))
        st, _ = status(ch)
        card = CARD_DIR / f'第{ch:03d}章.md'
        wal = WAL_DIR / f'第{ch:03d}.md'
        rows.append((ch, st, p, card.exists(), wal.exists()))
    lines = ['# 科武纪元第五卷六角色外审门禁表', '', '| 章 | 状态 | 审核记录 | 记忆卡 | WAL |', '|---:|---|---|---|---|']
    for ch, st, p, has_card, has_wal in rows:
        lines.append(f'| {ch} | {st} | `{p}` | {"✓" if has_card else "缺"} | {"✓" if has_wal else "缺"} |')
    if rows:
        passed = [ch for ch, st, *_ in rows if st == 'PASS']
        next_ch = (max(passed) + 1) if passed else rows[0][0]
        lines += ['', f'当前可推进章：第{next_ch}章（需先确认第{next_ch-1}章 PASS）']
    INDEX.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(INDEX)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapter', type=int)
    ap.add_argument('--next', type=int)
    ap.add_argument('--rebuild-index', action='store_true')
    args = ap.parse_args()
    if args.next:
        ensure_can_start(args.next)
    if args.chapter:
        st, detail = status(args.chapter)
        print(f'第{args.chapter}章 {st}\n{detail}')
    if args.rebuild_index:
        rebuild_index()

if __name__ == '__main__':
    main()
