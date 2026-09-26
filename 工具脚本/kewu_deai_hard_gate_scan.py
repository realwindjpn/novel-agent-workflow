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
    'CONSTRAINT_NOT_HARD': re.compile(r'[^，。！？\n]{1,40}是硬(?:性)?约束[，,、]\s*(?:而\s*)?不是建议'),
    'NOT_IS_HARD': re.compile(r'(不是(?!\s*因为)[^。！？\n，；]{0,60}[，。；]\s*是|的是[^。！？\n，；]{0,60}[，。；]\s*不是)'),
    # 叙述层连续否定公式：「不是X，不是Y，就是Z」——同句内出现两个及以上「不是」。
    'NOT_CHAIN_HARD': re.compile(r'不是[^。！？\n]{0,40}，\s*不是[^。！？\n]{0,40}，\s*(?:就是|而是)'),
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
    # 2026-09-09 r9b 新增：拆句公式（句号变体）——「不是X。」后接「而是/这是/是」开头的句子，
    # 同段内跨句号匹配，模型用句号拆行规避「不是…而是/这是」公式闸。placeholder，见 _detect_split_formula。
    'SPLIT_FORMULA_HARD': re.compile(r''),  # placeholder, handled in scan_file
    # 2026-09-03 新增：翻译腔禁词（叙述层）
    'TRANSLATION_TASTE_HARD': re.compile(r'(接住|击穿|锋利|不崩|不爆|打穿|扛住)'),
    # 2026-09-03 新增：过度缩略词
    'OVER_ABBREV_HARD': re.compile(r'(高负|微服|连池)'),
    # 2026-09-03 新增：生造词
    'COINED_TERM_HARD': re.compile(r'(高并发抗性|自解释度|容灾力)'),
    # 2026-09-03 新增：AI味词
    'AI_TASTE_SOFT': re.compile(r'(深入探讨|不仅能.*更能够|值得关注的是|总而言之|综上所述)'),
    # 2026-09-03 新增：中文弯引号 U+201C/U+201D/U+2018/U+2019
    'CURLY_QUOTE_HARD': re.compile(r'[\u201c\u201d\u2018\u2019]'),

    # ── 2026-09-26 人味审计补闸 ─────────────────────────────────────────
    # 缺口来源：kewu_deai_hard_gate_scan.py 原先只有 NOT_BUT/NUM_ENUM/CN_ENUM
    # 等公式类规则，bad_phrases.md 的 13 条禁用词表**从未接入**，导致
    # 第356章 L18「意味着」/ L88「微微」这类明文禁用词扫出 hard_count=0。
    # 「仅写 spec 文件≠生效」——禁用词必须同轮落成机器闸。
    #
    # 口径纪律（2026-09-26 用户定调：按上下文语境判定，不生硬机械判定）：
    # 全库实测 13 条禁用词中 3 条会大面积误伤，硬套原表等于把 255+ 处合法写法判 FAIL。
    #   意味着 109 处——「100%意味着人机完全合一」「这个名字意味着什么？」多为合法推断/角色口语
    #   微微   120+ 处——「微微发白/发颤/发抖/下沉/倾斜/发亮/凸起」全是物理量，可拍可测，
    #                      而 bad_phrases.md 自己的检验句「不能被摄像机拍到就不算合格」恰与之矛盾
    #   缓缓    26 处——「缓缓流动/下降/后移/推入」全是具体慢动作，本就是「替代成具体动作」的示范
    # 故拆为三档：
    #   HARD  —— 语义确定是 AI 腔，无合法小说用法
    #   CONTEXT_SOFT —— 语境相关，配物理/感官谓语放行，配情绪层或裸用才提示
    #   不进闸 —— 合法用法占绝大多数，交审稿席语境判断
    'BANNED_WORD_HARD': re.compile(
        r'(仿佛|宛如|不禁|不由得|某种意义|这不仅是|时代洪流|命运齿轮)'
    ),
    # 微微/缓缓：语境档。下列物理/感官谓语出现时视为「数据落到身体/仪表/延迟」的具体手段，放行。
    # 情绪层名词（眼神/瞳孔/神色/嘴角/呼吸/语调/目光/眉心…）在 微微 前出现，或无谓语跟随时才提示。
    'CONTEXT_ADVERB_SOFT': re.compile(
        r'(微微|缓缓)(?![一-鿿]{0,2}(?:'
        r'发白|发颤|发抖|发烫|发亮|发热|发紧|发麻|发虚|发涩|发红|发青|发胀|发痒|发酸|'
        r'颤动|颤抖|搏动|收紧|蜷着|蜷起|弓起|绷紧|下沉|倾斜|变形|凸起|凹陷|鼓起|'
        r'滑动|打滑|翘起|翻卷|下弯|上浮|明暗|'
        r'流动|下降|上升|后移|前移|推入|抽出|合拢|张开|抬起|落下|移动|漂移|流转|贯通|旋转|摇晃|'
        r'闪动|闪烁|跳动|滚动|推移|晃动|摇摆)'
        r')'
    ),
    # 「不得用引号包裹普通缩写、行业黑话、四字短句或一般性结论」
    # —— DEAI 规范第三节后半句，**长期无机器闸**。第356章 L22「部署」/L28「连带」
    # /L58「逐节点」/L88「部署方」4 处实证违规。
    # 排除对白：引号内带句末标点的是台词，不是「包裹词条」。
    #
    # 口径再收（2026-09-26 实测回归）：初版按 1–6 字全判 HARD，误伤公文原词与术语——
    # 第323章「轨维」（封存流水号前缀）、第324章「待确认」（事由栏）、
    # 第330章「沉肩坠肘」「含胸拔背」（书法术语→战术映射）、第331章「冗余」（图纸标注）。
    # 这些恰是 DEAI 规范要保留的实义引用。现按长度分档：
    #   2–4 字 —— 绝大多数是公文原词/术语/屏幕字段，**降为 SOFT 交审稿席语境判**
    #   5–6 字 —— 已是一般性结论或四字短句，保留 HARD
    'QUOTED_TERM_HARD': re.compile(r'「[^「」\n，。！？、；：]{5,6}」'),
    'QUOTED_TERM_SOFT': re.compile(r'「[^「」\n，。！？、；：]{1,4}」'),
    # 连续同型段（BURSTINESS_FLAT 的局部形态）：placeholder，见 _detect_consec_same_shape。
    # 聚合统计会漏——第356章全章同类微动作段仅占 6%，但 L88/89/90 连续三段同骨架，
    # L96 再把三人动作复述一遍。只看均值/标准差判不出来，必须查连续窗口。
    'CONSEC_SAME_SHAPE_SOFT': re.compile(r''),  # placeholder, handled in scan_file
}

WEIGHTS = {
    'NOT_BUT_HARD': 5,
    'CONSTRAINT_NOT_HARD': 5,
    'NOT_IS_HARD': 5,
    'NOT_CHAIN_HARD': 5,
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
    'SPLIT_FORMULA_HARD': 5,
    'TRANSLATION_TASTE_HARD': 5,
    'OVER_ABBREV_HARD': 5,
    'COINED_TERM_HARD': 5,
    'AI_TASTE_SOFT': 2,
    'CURLY_QUOTE_HARD': 3,
    'BANNED_WORD_HARD': 4,
    'CONTEXT_ADVERB_SOFT': 1,
    'QUOTED_TERM_HARD': 3,
    'QUOTED_TERM_SOFT': 1,
    'CONSEC_SAME_SHAPE_SOFT': 2,
}

_DIALOGUE_RE = re.compile(r'^\s*(?:“[^“”\n]*”|「[^「」\n]*」|"[^"\n]*"|\'[^\'\n]*\')\s*$')
_TITLE_RE = re.compile(r'^\s*#?\s*第\d+章\s+\S')

# 只扫叙述层的硬闸：先剥成对引号，引号内台词口语不判硬闸。
_NARRATION_ONLY_HARD = ('CONSTRAINT_NOT_HARD', 'NOT_IS_HARD', 'NOT_CHAIN_HARD')

# 成对引号（中文“”、半角 ""、半角 ''）；未闭合的单侧引号不匹配，故不会吞掉后文。
_PAIRED_QUOTE_RES = (
    re.compile(r'「[^「」\n]*」'),
    re.compile(r'“[^“”\n]*”'),
    re.compile(r'"[^"\n]*"'),
    re.compile(r"'[^'\n]*'"),
)


def strip_paired_quotes(text: str) -> str:
    """以等长换行占位掩盖所有成对引号及其内容，只留叙述层文字。

    用于 NOT_IS_HARD：对白里的「不是X，是Y」是正常口语，
    只有引号外的叙述层才该判硬闸。混合行（叙述+对白同一行）因此不再误扫。
    """
    out = text
    for pat in _PAIRED_QUOTE_RES:
        out = pat.sub(lambda match: '\n' * len(match.group(0)), out)
    return out


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
            if typ in ('REPEATED_SUBJECT_OPENING_SOFT', 'FRAGMENT_PUNCHLINE_SOFT', 'SPLIT_FORMULA_HARD', 'CONSEC_SAME_SHAPE_SOFT'):
                continue
            # 语境档副词闸：对白整行豁免——角色口语里的「微微/缓缓」是正常表达。
            if is_dialogue and typ == 'CONTEXT_ADVERB_SOFT':
                continue
            # 标题行“第X章 标题”/“# 第X章 标题”是合法格式，不算章节元信息。
            if typ == 'META_INFO_HARD' and is_title:
                continue
            # 完整对白行豁免新增的人味软/硬模式（NOT_IS_HARD 与 9 项 SOFT）+ CURLY_QUOTE_HARD。
            if is_dialogue and (typ in _NARRATION_ONLY_HARD or typ.endswith('_SOFT') or typ == 'CURLY_QUOTE_HARD'):
                continue
            # 叙述层专用硬闸只扫引号外：先剥掉所有成对引号内容，避免混合行
            #（叙述 + 对白同一行）里的台词口语被判硬闸。
            # CURLY_QUOTE_HARD 同样只扫引号外（对白里的引号不算违规）。
            target = strip_paired_quotes(line) if typ in _NARRATION_ONLY_HARD or typ == 'CURLY_QUOTE_HARD' else line
            # 「X是硬约束，不是建议」有专属类型，不重复记作通用 NOT_IS_HARD。
            if typ == 'NOT_IS_HARD' and PATTERNS['CONSTRAINT_NOT_HARD'].search(target):
                continue
            # 「不是X，不是Y，就是Z」有专属连续否定类型，不重复记作通用 NOT_IS_HARD。
            if typ == 'NOT_IS_HARD' and PATTERNS['NOT_CHAIN_HARD'].search(target):
                continue
            if pat.search(target):
                hits.append({'line': i, 'type': typ, 'text': stripped[:260]})

    # 跨行检测：连续同主语开头（≥3 句）
    _detect_repeated_subject_opening(lines, hits)
    # 跨行检测：碎片式打点（≥3 个等长短句排比）
    _detect_fragment_punchline(lines, hits)
    # 拆句公式（句号变体）：「不是X。」后接「而是/这是/是」开头
    _detect_split_formula(lines, hits)
    # 连续同型微动作段（BURSTINESS_FLAT 局部形态，均值法漏检）
    _detect_consec_same_shape(lines, hits)

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
# 拆句公式预筛（r9b）：「不是…。」后 20 字内以「而是/这是/是」开头的句首。
# 仅第一道闸（防无效行空转）；是否真实命中由 _detect_split_formula 按相邻句起始做字面二次校验，
# 防「不是X。这堆东西是Y。」这类句2中间含「是」的假阳性。
_SPLIT_FORMULA_RE = re.compile(r'不是[^。！？\n]{0,100}[。！？!?]\s*[^。！？\n]{0,20}?(?:而是|这是|是)')
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


def _detect_split_formula(lines: list[str], hits: list[dict]) -> None:
    """同段内跨句号「不是…。」后接「而是/这是/是」开头 = SPLIT_FORMULA_HARD。

    模型用句号拆行规避「不是…而是/这是」公式闸，属真漏洞，须按叙述层补抓。
    - 对白整行（_DIALOGUE_RE）自然排除：strip_paired_quotes 后整行变空占位，无句子可配。
    - 混合行引号内台词被剥，只留叙述层判断（与 NOT_IS_HARD 同一叙事规则）。
    - 字面二次校验：含「不是」句与其后紧邻句以 而是/这是/是 起首，防跨段假阳性。
    - 单句（逗号合写式「不是X，而是Y」）无跨句关系，交给既有 NOT_BUT_HARD。
    """
    for idx, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s or _TITLE_RE.match(s):
            continue
        target = strip_paired_quotes(s)
        if not _SPLIT_FORMULA_RE.search(target):
            continue
        parts = [p.strip() for p in _SENT_SPLIT_RE.split(target) if p.strip()]
        for a, b in zip(parts, parts[1:]):
            if '不是' in a and (b.startswith('而是') or b.startswith('这是') or b.startswith('是')):
                hits.append({
                    'line': idx,
                    'type': 'SPLIT_FORMULA_HARD',
                    'text': s[:260],
                })
                break


# 「某人+微动作+否定/重复+回到静止」段的形态指纹。
# 用于抓 BURSTINESS_FLAT 的**局部**形态：连续 3 段同骨架、动作趋同。
# 刻意不统计全章均值/标准差——第356章实证：全章同类段仅 6%（聚合达标），
# 但 L88/L89/L90 连续三段同骨架、L96 复述三人动作，均值法完全判不出。
_MICROACT_VERB = re.compile(r'(合拢|压住|按住|按在|压在|停在|收回来|翻过来|翻过去|敲|点了一下|端起|放下|没接话|没有抬头)')
_MICROACT_NEG = re.compile(r'(没有|又|还|再|仍|依旧)')
_CJK_ONLY = re.compile(r'[\u4e00-\u9fff]')
# 母题豁免：同一意象 ≥3 次且每次有变奏不算过度对称（依 C 席审计第4条打架）。
# 豁免口径落在「动作动词各不相同」上——全用同一动词才算真同型。
_MICROACT_MAXLEN = 60  # 超过此长度的段落不是「微动作段」


def _detect_consec_same_shape(lines: list[str], hits: list[dict]) -> None:
    """连续同型段检测（BURSTINESS_FLAT 局部形态）。

    连续 3 个有效叙述段均命中「微动作+否定」形态、且三段的微动作动词互不相同
    （说明是同一骨架换道具，正是第356章 L88/89/90 的形态）→ 记一次软命中，
    标在窗口末段行号上。

    标题行、对白整行、被引号剥空后无实质内容的行一律跳过。
    """
    cands: list[tuple[int, str, set[str]]] = []
    for idx, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s or _TITLE_RE.match(s) or _DIALOGUE_RE.match(s):
            continue
        cjk = len(_CJK_ONLY.findall(s))
        if cjk == 0 or cjk > _MICROACT_MAXLEN:
            continue
        if not (_MICROACT_VERB.search(s) and _MICROACT_NEG.search(s)):
            continue
        cands.append((idx, s, set(_MICROACT_VERB.findall(s))))

    for i in range(len(cands) - 2):
        win = cands[i:i + 3]
        verbs: set[str] = set()
        for _, _, v in win:
            verbs |= v
        # 三段同骨架 + 动词各异 = 换道具式重复；若三段动词完全相同则是母题变奏，豁免。
        if len(win) == 3 and len(verbs) >= 3:
            last = win[-1]
            hits.append({
                'line': last[0],
                'type': 'CONSEC_SAME_SHAPE_SOFT',
                'text': (f"连续3段同型微动作段 L{win[0][0]}/L{win[1][0]}/L{last[0]}："
                         f"动作{'/'.join(sorted(verbs))}｜末段 {last[1][:120]}"),
            })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='*', help='文件或目录；默认扫描 已投稿/ 与 新版/')
    ap.add_argument('--start', type=int)
    ap.add_argument('--end', type=int)
    ap.add_argument('--outdir', default=str(PROJECT / '审核记录' / '去AI硬闸扫描'))
    # 2026-09-26 补：基线回归用。停用当日新增的三条闸，用于回答
    # 「新增闸把多少原本 PASS 的文件推成 FAIL」——没有基线就报命中数等于瞎报。
    ap.add_argument('--disable-new', action='store_true',
                    help='停用 2026-09-26 新增的五条闸（BANNED_WORD_HARD / CONTEXT_ADVERB_SOFT / '
                         'QUOTED_TERM_HARD / QUOTED_TERM_SOFT / CONSEC_SAME_SHAPE_SOFT）')
    args = ap.parse_args()
    if args.disable_new:
        for k in ('BANNED_WORD_HARD', 'CONTEXT_ADVERB_SOFT', 'QUOTED_TERM_HARD',
                  'QUOTED_TERM_SOFT', 'CONSEC_SAME_SHAPE_SOFT'):
            PATTERNS.pop(k, None)
            WEIGHTS.pop(k, None)
        global _detect_consec_same_shape
        _detect_consec_same_shape = lambda lines, hits: None  # noqa: E731

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
