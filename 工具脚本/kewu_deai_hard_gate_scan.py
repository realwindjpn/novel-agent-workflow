#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""科武纪元去AI硬闸扫描。

只读扫描正文/TXT/MD，输出命中行号。
硬闸：
- 连续或高密度“不是……而是……”句式
- 叙述层“不是X，是Y”/“不是X。是Y”公式（NOT_IS_HARD）
- 正文说明书式 1/2/3/4、一二三四 枚举
- 报告腔连接词/分层标签

软规则（v2 吸收 Qwen 人味知识库）：
IMPORTANCE_PUFFERY / SHALLOW_SYMBOLISM / NEXT_POINT_ANNOUNCE /
FAKE_CANDOR / UNRAISED_OBJECTION / COLON_REVEAL / DISTANT_NARRATOR /
REPEATED_SUBJECT_OPENING / FRAGMENT_PUNCHLINE

防误伤：完整引号对白行跳过 v2 新增规则；标题行不算 META。

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
    'NOT_BUT_HARD': re.compile(r'(不是[^。！？\n]{0,100}而是|并非[^。！？\n]{0,100}而是|不在于[^。！？\n]{0,100}而在于|不只是[^。！？\n]{0,100}更是|不仅[^。！？\n]{0,100}(还|更)|与其[^。！？\n]{0,100}不如)'),
    'NOT_IS_HARD': re.compile(r'不是[^。！？\n，；]{0,60}[，。；]\s*是'),
    'NUM_ENUM_HARD': re.compile(r'(^|[。！？\n]\s*)\d{1,2}[、.．：:]'),
    'CN_ENUM_HARD': re.compile(r'(^|[。！？\n]\s*)[一二三四五六七八九十][、.．：:]'),
    'META_INFO_HARD': re.compile(r'(下一章|第\d+章|第[一二三四五六七八九十]+章|第\d+卷|第[一二三四五六七八九十]+卷|后续篇章|第二卷后半段)'),
    'COMMAND_OPENING_HARD': re.compile(r'(别急着[^。！？\n]{0,40}先|先别[^。！？\n]{0,40}先|别[^。！？\n]{0,40}先|顺序别反了|别搞反了|记住这句话)'),
    'LECTURE_COLON_HARD': re.compile(r'(我的结论是：|原因很简单：|重点是：|分成三类：|更重要的是：)'),
    'FAKE_INSIGHT_SOFT': re.compile(r'(真正|其实|本质上|说白了|归根结底|更重要的是|这说明|这背后|结果有点出乎意料|核心是|关键是|这意味着)'),
    'VAGUE_REFERENT_SOFT': re.compile(r'(这个东西|这些东西|这件事|这一类|几个方向)'),
    'TENSE_MISMATCH_SOFT': re.compile(r'(我会用|我会先|我接下来会用|下一步我会用)'),
    'VAGUE_COMPARISON_SOFT': re.compile(r'(更适合|更像|更自然|更高级)'),
    'SLOGAN_ENDING_SOFT': re.compile(r'(能力飞轮|上下文燃料|时代分水岭|新的分水岭|作者痕迹|把判断盖住|差距会突然变得很难看|差距会被迅速拉开)'),
    'REPORT_TONE_SOFT': re.compile(r'(公文|汇报|换句话说|分为|层面|维度|路径|机制|首先|其次|最后)'),
    'LAYER_LABEL_SOFT': re.compile(r'(首先|其次|最后|第一|第二|第三|一方面|另一方面|宏观上|中观上|微观上|战略层|战术层|操作层)'),
    'IMPORTANCE_PUFFERY_SOFT': re.compile(r'(标志着|里程碑|划时代|开创性|开启新纪元|不言而喻|毋庸置疑|不可否认)'),
    'SHALLOW_SYMBOLISM_SOFT': re.compile(r'(象征着|折射出|展现了|凸显了|印证了|彰显|诠释了|见证了)'),
    'NEXT_POINT_ANNOUNCE_SOFT': re.compile(r'(接下来|下面我们来看|下面来看|值得注意的是|需要指出|不难发现)'),
    'FAKE_CANDOR_SOFT': re.compile(r'(说实话[？?]|坦白说|不瞒你说|诚实地说)'),
    'UNRAISED_OBJECTION_SOFT': re.compile(r'(也许你会说[^。！？\n]{0,40}但|有人可能认为[^。！？\n]{0,40}然而|尽管有人[^。！？\n]{0,40}但)'),
    'COLON_REVEAL_SOFT': re.compile(r'(答案是：|真相是：|最妙的是：|秘诀在于：)'),
    'DISTANT_NARRATOR_SOFT': re.compile(r'(读者不难发现|众所周知|显而易见|众所周知的事实是)'),
    'REPEATED_SUBJECT_OPENING_SOFT': re.compile(r''),  # placeholder, handled in scan_file
    'FRAGMENT_PUNCHLINE_SOFT': re.compile(r''),  # placeholder, handled in scan_file
}

WEIGHTS = {
    'NOT_BUT_HARD': 5,
    'NOT_IS_HARD': 5,
    'NUM_ENUM_HARD': 5,
    'CN_ENUM_HARD': 5,
    'META_INFO_HARD': 9,
    'COMMAND_OPENING_HARD': 5,
    'LECTURE_COLON_HARD': 5,
    'FAKE_INSIGHT_SOFT': 2,
    'VAGUE_REFERENT_SOFT': 1,
    'TENSE_MISMATCH_SOFT': 2,
    'VAGUE_COMPARISON_SOFT': 1,
    'SLOGAN_ENDING_SOFT': 2,
    'REPORT_TONE_SOFT': 2,
    'LAYER_LABEL_SOFT': 1,
    'IMPORTANCE_PUFFERY_SOFT': 2,
    'SHALLOW_SYMBOLISM_SOFT': 2,
    'NEXT_POINT_ANNOUNCE_SOFT': 2,
    'FAKE_CANDOR_SOFT': 2,
    'UNRAISED_OBJECTION_SOFT': 2,
    'COLON_REVEAL_SOFT': 2,
    'DISTANT_NARRATOR_SOFT': 2,
    'REPEATED_SUBJECT_OPENING_SOFT': 2,
    'FRAGMENT_PUNCHLINE_SOFT': 2,
}

_DIALOGUE_RE = re.compile(r'^\s*[“”"\'].*[”"\']\s*$')
_TITLE_RE = re.compile(r'^\s*#?\s*第\d+章\s+\S')


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
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        stripped = line.strip()
        is_title = bool(_TITLE_RE.match(stripped))
        is_dialogue = bool(_DIALOGUE_RE.match(stripped))
        for typ, pat in PATTERNS.items():
            # 跨行/跨句检测键由专用函数添加，主循环必须跳过——
            # 其正则为占位 r''，search 对任意非空行无条件命中，会导致分数通胀。
            if typ in ('REPEATED_SUBJECT_OPENING_SOFT', 'FRAGMENT_PUNCHLINE_SOFT'):
                continue
            # 标题行“第X章 标题”/“# 第X章 标题”是合法格式，不算章节元信息。
            if typ == 'META_INFO_HARD' and is_title:
                continue
            # 完整对白行豁免新增的人味软/硬模式（NOT_IS_HARD 与 9 项 SOFT）。
            if is_dialogue and (typ == 'NOT_IS_HARD' or typ.endswith('_SOFT')):
                continue
            if pat.search(line):
                hits.append({'line': i, 'type': typ, 'text': stripped[:260]})

    # 跨行检测：连续同主语开头（≥3 句）
    _detect_repeated_subject_opening(lines, hits)
    # 跨行检测：碎片式打点（≥3 个等长短句排比）
    _detect_fragment_punchline(lines, hits)

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


# 句子切分：只按 。！？（含半角 !?）切，不切 '.'，避免 3.5 这类小数被拆断。
_SENT_SPLIT_RE = re.compile(r'[。！？!?]+')
# 代词主语精确匹配，长词在前，避免「他们」被截成「他」。
_PRONOUN_SUBJECTS = ('他们', '她们', '它们', '我们', '他', '她', '它', '我')
# 名字主语候选：取行首连续汉字（最多 6 字），后续用公共前缀收敛出真正主语。
_LEAD_CJK_RE = re.compile(r'^[\u4e00-\u9fff]{1,6}')
_MIN_NAME_PREFIX = 2


def _sentence_subject(part: str) -> tuple[str, str] | None:
    """抽取句首主语键。

    返回 ('pron', 代词) 或 ('name', 行首汉字串)；无汉字/仅 1 字非代词返回 None。
    name 分支不做贪婪定长切分——定长切分会把「方宁按下」「方宁看向」判成不同主语，
    真正的主语由 _detect_repeated_subject_opening 用公共前缀收敛（≥2 字算同主语）。
    """
    for p in _PRONOUN_SUBJECTS:
        if part.startswith(p):
            return ('pron', p)
    m = _LEAD_CJK_RE.match(part)
    if not m:
        return None
    lead = m.group(0)
    if len(lead) < _MIN_NAME_PREFIX:
        return None
    return ('name', lead)


def _common_prefix(a: str, b: str) -> str:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return a[:n]


def _detect_repeated_subject_opening(lines: list[str], hits: list[dict]) -> None:
    """连续 ≥3 句同一主语起句时标记 REPEATED_SUBJECT_OPENING_SOFT。

    同一行多句与跨行连续都算；主语不同（公共前缀 <2 字）或出现无主语句即断链，
    故「方宁走到窗前。屏幕亮了起来。外面的天色暗了下去。」这类三不同主语不误报。
    """
    # None 作为断链哨兵，保证无主语句能打断连续计数。
    seq: list[tuple[int, tuple[str, str]] | None] = []
    for idx, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s or _TITLE_RE.match(s) or _DIALOGUE_RE.match(s):
            continue
        for part in _SENT_SPLIT_RE.split(s):
            part = part.strip()
            if not part:
                continue
            subj = _sentence_subject(part)
            seq.append((idx, subj) if subj else None)

    run_kind: str | None = None
    run_token = ''
    run_start = 0
    run_count = 0
    for item in seq:
        if item is None:
            run_kind, run_token, run_count = None, '', 0
            continue
        ln, (kind, token) = item
        same = False
        merged = token
        if run_count and kind == run_kind:
            if kind == 'pron':
                same = token == run_token
                merged = token
            else:
                merged = _common_prefix(run_token, token)
                same = len(merged) >= _MIN_NAME_PREFIX
        if same:
            run_token = merged
            run_count += 1
        else:
            run_kind, run_token, run_count, run_start = kind, token, 1, ln
        if run_count >= 3:
            hits.append({
                'line': run_start,
                'type': 'REPEATED_SUBJECT_OPENING_SOFT',
                'text': f'连续同主语「{run_token}」起句 {run_count} 句',
            })
            return


def _detect_fragment_punchline(lines: list[str], hits: list[dict]) -> None:
    """≥3 个等长短句排比（无信息增量）时标记 FRAGMENT_PUNCHLINE_SOFT。"""
    frags: list[tuple[int, str]] = []
    for idx, raw in enumerate(lines, 1):
        s = raw.strip().rstrip('。.！!？?')
        # 短句碎片：≤12 字，无主谓完整结构（不含“了/着/过”动词尾的判断）
        if 2 <= len(s) <= 12 and not _TITLE_RE.match(s) and not _DIALOGUE_RE.match(s):
            frags.append((idx, s))
    # 在同一行内查找（如“没有偏好。没有先验。没有乡愁。”）
    for idx, raw in enumerate(lines, 1):
        parts = re.split(r'[。.！!？?]', raw.strip())
        short = [p.strip() for p in parts if 2 <= len(p.strip()) <= 12]
        if len(short) >= 3 and len({len(p) for p in short}) == 1:
            hits.append({
                'line': idx,
                'type': 'FRAGMENT_PUNCHLINE_SOFT',
                'text': raw.strip()[:260],
            })
            return


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
