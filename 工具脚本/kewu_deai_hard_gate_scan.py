#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""科武纪元去AI硬闸扫描。

只读扫描正文/TXT/MD，输出命中行号。
硬闸：
- 连续或高密度“不是……而是……”句式
- 正文说明书式 1/2/3/4、一二三四 枚举
- 报告腔连接词/分层标签

默认不改文。
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

PROJECT = Path('/root/workspace/科武纪元')
DEFAULT_DIRS = [PROJECT / '已投稿', PROJECT / '新版']

PATTERNS = {
    'NOT_BUT_HARD': re.compile(r'不是[^。！？\n]{0,100}而是'),
    'NUM_ENUM_HARD': re.compile(r'(^|[。！？\n]\s*)\d{1,2}[、.．：:]'),
    'CN_ENUM_HARD': re.compile(r'(^|[。！？\n]\s*)[一二三四五六七八九十][、.．：:]'),
    'META_INFO_HARD': re.compile(r'(下一章|第\d+章|第[一二三四五六七八九十]+章|第\d+卷|第[一二三四五六七八九十]+卷|后续篇章|第二卷后半段)'),
    'REPORT_TONE_SOFT': re.compile(r'(公文|汇报|本质上|换句话说|这意味着|分为|层面|维度|路径|机制|核心是|更重要的是|首先|其次|最后)'),
    'LAYER_LABEL_SOFT': re.compile(r'(首先|其次|最后|第一|第二|第三|一方面|另一方面|核心是|本质是|意味着|换句话说|更重要的是)'),
}

WEIGHTS = {
    'NOT_BUT_HARD': 5,
    'NUM_ENUM_HARD': 5,
    'CN_ENUM_HARD': 5,
    'META_INFO_HARD': 9,
    'REPORT_TONE_SOFT': 2,
    'LAYER_LABEL_SOFT': 1,
}


def iter_files(paths: list[Path]):
    for root in paths:
        if root.is_file():
            yield root
        elif root.exists():
            for p in sorted(root.glob('第*章.*')):
                if p.suffix.lower() in {'.txt', '.md'}:
                    yield p


def chapter_no(path: Path) -> int:
    m = re.search(r'第(\d+)章', path.name)
    return int(m.group(1)) if m else 999999


def scan_file(path: Path) -> dict:
    text = path.read_text(encoding='utf-8-sig', errors='replace')
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        for typ, pat in PATTERNS.items():
            # 标题行“第X章 标题”是合法格式，不算章节元信息。
            if typ == 'META_INFO_HARD' and i == 1 and re.match(r'^第\d+章\s+', line.strip()):
                continue
            if pat.search(line):
                hits.append({'line': i, 'type': typ, 'text': line.strip()[:260]})
    score = sum(WEIGHTS.get(h['type'], 1) for h in hits)
    hard_hits = [h for h in hits if h['type'].endswith('_HARD')]
    verdict = 'PASS'
    if hard_hits:
        verdict = 'FAIL_HARD'
    elif score >= 20:
        verdict = 'WARN_DENSE_SOFT'
    return {
        'path': str(path),
        'chapter': chapter_no(path),
        'verdict': verdict,
        'score': score,
        'hit_count': len(hits),
        'hard_count': len(hard_hits),
        'hits': hits,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='*', help='文件或目录；默认扫描 已投稿/ 与 新版/')
    ap.add_argument('--start', type=int)
    ap.add_argument('--end', type=int)
    ap.add_argument('--outdir', default=str(PROJECT / '审核记录' / '去AI硬闸扫描'))
    args = ap.parse_args()

    roots = [Path(p) for p in args.paths] if args.paths else DEFAULT_DIRS
    records = []
    for p in iter_files(roots):
        ch = chapter_no(p)
        if args.start and ch < args.start:
            continue
        if args.end and ch > args.end:
            continue
        records.append(scan_file(p))
    records.sort(key=lambda r: (r['chapter'], r['path']))

    outdir = Path(args.outdir) / datetime.now().strftime('%Y%m%d_%H%M%S')
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / 'deai_hard_gate_scan.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')

    lines = ['# 科武纪元去AI硬闸扫描', '', f'- 生成时间：{datetime.now().isoformat(timespec="seconds")}', '- 规则：NOT_BUT/NUM_ENUM/CN_ENUM 为硬闸；LAYER_LABEL 为软风险。', '']
    fail = [r for r in records if r['verdict'] != 'PASS']
    lines.append(f'- 扫描文件：{len(records)}')
    lines.append(f'- 非PASS：{len(fail)}')
    lines.append('')
    lines.append('|章|结论|硬闸|分数|文件|')
    lines.append('|---:|---|---:|---:|---|')
    for r in fail:
        lines.append(f"|{r['chapter']}|{r['verdict']}|{r['hard_count']}|{r['score']}|{r['path']}|")
    lines.append('')
    lines.append('## 命中证据')
    for r in fail:
        lines.append(f"\n### 第{r['chapter']}章 — {r['verdict']} — {r['path']}")
        lines.append('|行号|类型|证据|')
        lines.append('|---:|---|---|')
        for h in r['hits'][:120]:
            lines.append(f"|{h['line']}|{h['type']}|{h['text'].replace('|','｜')}|")
        if len(r['hits']) > 120:
            lines.append(f"|...|...|余 {len(r['hits'])-120} 条略|")
    (outdir / 'deai_hard_gate_scan.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'outdir': str(outdir), 'files': len(records), 'non_pass': len(fail)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
