# -*- coding: utf-8 -*-
"""科武五审流程 —— 席位固化 + 状态机（2026-10-07 重构）

用户定版流程（2026-10-07）：
1. 每席「一个节点一个模型」，但保留 fallback 链（同模型族内可换号）
2. 五席分别用当前最强的 5 个**不同**模型（异构，跨模型族）
3. 五席并行同审
4. 汇总五席修改意见后**一起**送作者席修改
5. 单席 PASS 后**不再参与后续同审**（只重审未 PASS 的席）—— 效率关键
6. 直到五席全 PASS，再一起做**终审**
7. 终审过关才进闭环写入与上传

与旧实现（kewu_parallel_review.py）的差异：
- 旧：fallbacks 是跨族乱序链，每轮全席重派（r1/r2/r3…），PASS 的席也重跑
- 新：FIVE_SEATS 固化异构五席；state 文件记录每席 PASS 状态；
      重审只派未 PASS 的席；全 PASS 后触发终审阶段

五席选取依据：2026-10-07 hermes_native_full_pool_audit（原生通道，84 测 60 PASS）
按「最强 + 跨族 + 快」选，延迟均 <20s：
  编辑席   artbloom/claude-opus-5-5        10.71s（opus 族最强）
  结构席   jiuuij/grok-4.20-multi-agent-high 11.70s（grok 族）
  科军席   jichuan-dsv4pro/deepseek-v4-pro-0813 11.92s（deepseek 族旗舰）
  读者席   hiyo/gpt-6-luna                 14.63s（gpt-6 族）
  去AI腔席 wechat-glm/GLM-5.2              12.92s（glm 族）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
STATE_DIR = BASE / '任务运行态' / '五审状态'

# ── 角色OS 注入（HARD，2026-10-07）──────────────────────────────────────
# 教训：OS 文件一直存在于 /root/workspace/写作角色OS/，但本脚本零引用，
#       导致 369/370 两章在「裸审」状态下通过全部机器闸与终审 —— 完全未被发现。
#       技能 novel-six-role-cpa-lite 明令「缺角色OS＝任务卡不合格，不得裸写」。
#       见 ../skills  references/role-os-present-but-not-injected-20261007.md
ROLE_OS_DIR = Path('/root/workspace/写作角色OS')

# 各席位必须加载的 OS 文件。缺任一文件 → FileNotFoundError → 中断派工，不降级。
AUTHOR_OS_FILES = [
    'kewu_author_prompt.md',
    'writer_role_core.md',
    'experience_distillation_rules.md',
    'kewu_author_training_index.md',
    'kewu_author_training_examples.md',
    'deai_route_manifest.md',
    'DEAI_WRITING_STYLE_SPEC_20260903.md',
]
SEAT_OS_FILES = {
    'editor':           ['kewu_author_prompt.md', 'DEAI_WRITING_STYLE_SPEC_20260903.md'],
    'structure':        ['writer_role_core.md', 'experience_distillation_rules.md'],
    'science_military': ['experience_distillation_rules.md'],
    'reader':           ['writer_role_core.md', 'DEAI_WRITING_STYLE_SPEC_20260903.md'],
    'deai':             ['deai_route_manifest.md', 'DEAI_WRITING_STYLE_SPEC_20260903.md'],
    # 终审五席同初审角色分工，复用同一批 OS；终审额外强调「只判落实，不复述」
    'final_editor':           ['DEAI_WRITING_STYLE_SPEC_20260903.md'],
    'final_structure':        ['writer_role_core.md'],
    'final_science':          ['experience_distillation_rules.md'],
    'final_reader':           ['writer_role_core.md'],
    'final_deai':             ['deai_route_manifest.md', 'DEAI_WRITING_STYLE_SPEC_20260903.md'],
}


def load_role_os(seat: str, *, max_chars: int = 9000) -> tuple[str, list[str]]:
    """按席位加载角色OS。返回 (文本, 已加载文件名清单)。
    缺文件即抛 FileNotFoundError —— 不降级为空串，不打印警告了事。"""
    files = SEAT_OS_FILES.get(seat)
    if files is None:
        raise KeyError(f'未定义 OS 映射的席位: {seat}')
    chunks, loaded = [], []
    for name in files:
        p = ROLE_OS_DIR / name
        if not p.exists():
            raise FileNotFoundError(
                f'角色OS缺失，拒绝裸审：{p}\n'
                f'席位={seat}；修复或重建 OS 后再派工。'
                f'（教训见 skill kewu-selfcycle-production/'
                f'references/role-os-present-but-not-injected-20261007.md）')
        txt = p.read_text(encoding='utf-8')
        loaded.append(f'{name}({p.stat().st_size}B)')
        if len(txt) > max_chars:      # 上下文保护：OS 全文可能很长
            txt = txt[:max_chars] + f'\n…[{name} 前 {max_chars} 字，已截断]'
        chunks.append(f'### 角色OS片段：{name}\n{txt}')
    return '\n\n'.join(chunks), loaded


def inject_role_os(seat_prompt: str, seat: str) -> tuple[str, list[str]]:
    """把角色OS拼到席位 prompt 前面。prompt 为空或缺文件都会中断。"""
    if not (seat_prompt or '').strip():
        raise ValueError(f'席位 {seat} 的 prompt 为空，疑似未正确取到模板')
    os_text, loaded = load_role_os(seat)
    header = (
        '【角色OS · 必须遵守】以下片段是本席位的角色操作系统，'
        '其优先级高于下方任务描述中的一般措辞。\n\n'
    )
    return header + os_text + '\n\n──────────\n\n' + seat_prompt, loaded

# ── 五席固化：异构、跨族、每席一个节点一个模型 + 同族 fallback ──────────
FIVE_SEATS = {
    'editor': {
        'role': '编辑席',
        'prompt': (
            "你是《科武纪元》编辑审稿席。审查以下章节全文。\n\n"
            "审查重点：大纲一致性、情节逻辑、人物一致性、节奏控制、章节衔接连续性、"
            "伏笔铺设与回收。\n\n"
            "输出格式：首行只写 PASS 或 PASS_WITH_NOTES 或 FAIL。"
            "若非 PASS，逐条列必改项并引原文片段。\n\n正文：\n{body}"
        ),
        'chain': [('artbloom', 'claude-opus-5-5'),
                  ('xlabs-opus47', 'claude-opus-5'),
                  # 2026-10-07 加入：opus-4-8，与 artbloom/xlabs 不同网关，
                  # 防同一节点故障时整条 opus 槽位无可用。仅 Anthropic /v1/messages 端点通
                  # （OpenAI /chat/completions 被 CF WAF 拦 403），api_mode 已配 anthropic_messages。
                  ('justwoker-opus48', 'claude-opus-4-8'),
                  ('openfly', 'claude-opus-4-7')],
    },
    'structure': {
        'role': '结构席',
        'prompt': (
            "你是《科武纪元》结构审稿席。审查以下章节全文。\n\n"
            "审查重点：章节结构完整性、场景切换合理性、信息密度分布、"
            "开篇钩子与结尾悬念、段落长度节奏、视角一致性。\n\n"
            "输出格式：首行只写 PASS 或 PASS_WITH_NOTES 或 FAIL。"
            "若非 PASS，逐条列必改项并引原文片段。\n\n正文：\n{body}"
        ),
        'chain': [('jiuuij', 'grok-4.20-multi-agent-high'),
                  ('grok2api-seeseed1ck', 'grok-4.6'),
                  ('futureppo', 'grok-4.7')],
    },
    'science_military': {
        'role': '科学+军事顾问席',
        'prompt': (
            "你是《科武纪元》科学与军事顾问审稿席。审查以下章节全文。\n\n"
            "审查重点：物理机制自洽（信号处理、材料、星际通讯）、军事逻辑与装备可信度、"
            "遗址技术设定一致性、数值量级合理性。\n\n"
            "输出格式：首行只写 PASS 或 PASS_WITH_NOTES 或 FAIL。"
            "若非 PASS，逐条列必改项并引原文片段，给出正确参数或机制。\n\n正文：\n{body}"
        ),
        'chain': [('jichuan-dsv4pro', 'deepseek-v4-pro-0813'),
                  ('siliconflow', 'deepseek-ai/DeepSeek-V3'),
                  ('fkall-text', 'deepseek-v4-flash')],
    },
    'reader': {
        'role': '读者席',
        'prompt': (
            "你是《科武纪元》读者审稿席，代表番茄小说普通读者视角。审查以下章节全文。\n\n"
            "审查重点：追读意愿、爽感与悬念、是否有解说腔/降智感、比喻是否过密、"
            "人物是否有魅力。给出追读评分（1-5 分）。\n\n"
            "输出格式：首行只写 PASS 或 PASS_WITH_NOTES 或 FAIL。"
            "次行写「追读评分：N/5」。若非 PASS，逐条列必改项并引原文片段。\n\n正文：\n{body}"
        ),
        'chain': [('hiyo', 'gpt-6-luna'),
                  ('piexian', 'gpt-6-astra'),
                  ('rsiai-gpt', 'gpt-6-astra')],
    },
    'deai': {
        'role': '去AI腔席',
        'prompt': (
            "你是《科武纪元》去AI腔审稿席。审查以下章节全文。\n\n"
            "审查重点（逐项扫描并引原文）：\n"
            "1. 解释腔——叙述者跳出来解释设定或人物动机\n"
            "2. 文艺腔/咏叹调——空洞抒情、无物理落点的比喻\n"
            "3. 清单腔——用排比或编号堆砌信息\n"
            "4. 「不是…而是」公式句\n"
            "5. AI 高频词与过度对称句式\n\n"
            "输出格式：首行只写 PASS 或 PASS_WITH_NOTES 或 FAIL。"
            "若非 PASS，逐条引原文并给改写建议。\n\n正文：\n{body}"
        ),
        'chain': [('wechat-glm', 'GLM-5.2'),
                  ('discovery', 'glm-5.3'),
                  ('sensenova', 'glm-5.2')],
    },
}

TIMEOUT_PER_SEAT = 600
VERDICT_TOKENS = ('PASS_WITH_NOTES', 'FAIL', 'PASS')

# ── 终审席：必须与初审五席的模型族不同（2026-10-07 用户采纳优化①）──
# 理由：同一模型审自己刚判过 OK 的稿，等于自我复核，失去终审意义。
# 初审族：opus / grok / deepseek / gpt-6 / glm
# 终审族：sonnet / kimi / qwen / nemotron / minimax  （全部从原生审计 PASS 池取）
FINAL_SEATS = {
    'final_editor': {
        'role': '终审·编辑席',
        'prompt': (
            "你是《科武纪元》终审编辑席。此稿已通过初审五席，现在是终审。\n\n"
            "只做一件事：确认初审提出的修改意见是否已全部落实，且未引入新问题。\n"
            "不许复述初审意见，只判「已落实 / 未落实 / 引入新问题」。\n\n"
            "输出格式：首行只写 PASS 或 FAIL。若 FAIL，逐条列未落实项并引原文。\n\n正文：\n{body}"
        ),
        'chain': [('onyxaxis-sonnet5', 'claude-sonnet-5'),
                  ('openfly', 'claude-opus-4-7')],
    },
    'final_structure': {
        'role': '终审·结构席',
        'prompt': (
            "你是《科武纪元》终审结构席。此稿已通过初审五席，现在是终审。\n\n"
            "只做一件事：确认章节结构完整性（开篇钩子/中段推进/结尾悬念）未被修改破坏。\n"
            "不许复述初审意见。\n\n"
            "输出格式：首行只写 PASS 或 FAIL。若 FAIL，逐条列结构问题并引原文。\n\n正文：\n{body}"
        ),
        # 一个 provider 只出一个模型（2026-10-07 用户铁律）。
        # 主选 1tim/glm-5.2；备选换独立节点 tingfeng/deepseek-v4.1-flash（实测OK 10.9s），
        # 不再由 1tim 同时出 glm 与 deepseek —— 那会让同席位出现同节点双模型。
        # 原：('1tim','kimi-k3')+('773','kimi-k3') → ('1tim','glm-5.2')+('1tim','deepseek-v4.1-flash')
        'chain': [('1tim', 'glm-5.2'), ('tingfeng', 'deepseek-v4.1-flash')],
    },
    'final_science': {
        'role': '终审·科学军事席',
        'prompt': (
            "你是《科武纪元》终审科学与军事席。此稿已通过初审五席，现在是终审。\n\n"
            "只做一件事：确认物理机制与军事逻辑在修改后仍然自洽，数值量级无误。\n"
            "不许复述初审意见。\n\n"
            "输出格式：首行只写 PASS 或 FAIL。若 FAIL，逐条列并给出正确值。\n\n正文：\n{body}"
        ),
        # 一个 provider 只出一个模型（2026-10-07 用户铁律）。
        # 备选原为 773/qwen3.8-max，但 773 已承担 final_deai 两条，
        # 继续复用会让「全部走到第二选」时 773 占 2 席、distinct 掉到 4。
        # 改换独立节点 sunapi-qwen38/qwen3.8-max（实测真通 18.8s，无 fallback）。
        'chain': [('weiyi-qwen', 'qwen3.8-27b'), ('sunapi-qwen38', 'qwen3.8-max')],
    },
    'final_reader': {
        'role': '终审·读者席',
        'prompt': (
            "你是《科武纪元》终审读者席。此稿已通过初审五席，现在是终审。\n\n"
            "只做一件事：以番茄小说读者视角确认改后稿仍值得追读，无解说腔/降智感。\n"
            "给出追读评分（1-5 分）。不许复述初审意见。\n\n"
            "输出格式：首行只写 PASS 或 FAIL。次行写「追读评分：N/5」。\n\n正文：\n{body}"
        ),
        'chain': [('openrouter-nemotron-super', 'nvidia/nemotron-3-super-120b-a12b:free'),
                  ('openrouter', 'nvidia/nemotron-3-ultra-550b-a55b:free')],
    },
    'final_deai': {
        'role': '终审·去AI腔席',
        'prompt': (
            "你是《科武纪元》终审去AI腔席。此稿已通过初审五席，现在是终审。\n\n"
            "只做一件事：确认修改过程中没有新引入 AI 腔（解释腔/文艺腔/清单腔/"
            "「不是…而是」公式句）。只报新增问题，不报已存在的。\n\n"
            "输出格式：首行只写 PASS 或 FAIL。若 FAIL，逐条引原文并给改写建议。\n\n正文：\n{body}"
        ),
        'chain': [('773', 'minimax-agent'), ('773', 'Agents-A1')],
    },
}

# ── 意见聚类（2026-10-07 用户采纳优化②）──
# 五席并行审同一段，多人常指出同一处问题；直接把五份意见丢给作者席
# 会造成重复修改。按「位置 + 类型」聚合成去重清单，作者席一次改完。
ISSUE_TYPES = [
    ('解说腔', r'解说腔|解释腔|叙述者.*解释|跳出来解释'),
    ('文艺腔', r'文艺腔|咏叹调|空洞抒情|抒情.*无.*落点'),
    ('清单腔', r'清单腔|排比堆砌|编号堆砌|罗列'),
    ('公式句', r'不是.{1,20}而是|并非.{1,20}而是'),
    ('节奏', r'节奏|拖沓|推进慢|冗长'),
    ('逻辑', r'逻辑|矛盾|不自洽|前后不一|bug|漏洞'),
    ('人物', r'人物|人设|性格|动机.*不明|OOC'),
    ('伏笔', r'伏笔|铺垫|回收'),
    ('科学', r'物理|机制|参数|数值|量级|不合理'),
    ('军事', r'军事|装备|战术|编制|指挥'),
    ('结尾', r'结尾|收尾|悬念|钩子'),
    ('开篇', r'开篇|开头|入戏|第一句'),
]
_LINE_REF_RE = re.compile(r'(?:第|L|line|行)\s*(\d{1,4})\s*[行线]?|'
                          r'^\s*(\d{1,4})[、.．:：]', re.M)
_QUOTE_RE = re.compile(r'[「『"“""]([^」』"”""]{6,60})[」』"”""]')


def extract_issues(seat: str, content: str) -> list:
    """从一席意见里抽结构化问题：位置（行号或引文）+ 类型。"""
    out = []
    for para in (content or '').split('\n'):
        p = para.strip()
        if not p or len(p) < 8:
            continue
        types = [name for name, pat in ISSUE_TYPES if re.search(pat, p)]
        if not types:
            continue
        locs = []
        for m in _LINE_REF_RE.finditer(p):
            n = m.group(1) or m.group(2)
            if n:
                locs.append('L' + n)
        for m in _QUOTE_RE.finditer(p):
            locs.append('Q:' + m.group(1)[:24])
        out.append({'seat': seat, 'types': types,
                    'locations': locs[:3], 'text': p[:300]})
    return out


def cluster_issues(seat_results: dict) -> dict:
    """按『位置 + 类型』聚合五席意见，产出给作者席的去重清单。"""
    all_issues = []
    for seat, r in seat_results.items():
        if (r.get('verdict') or '') == 'PASS':
            continue
        all_issues += extract_issues(seat, r.get('content') or '')

    buckets = {}
    for it in all_issues:
        keys = it['locations'] or ['GLOBAL']
        for loc in keys:
            for t in it['types']:
                buckets.setdefault((loc, t), []).append(it)

    merged = []
    for (loc, t), items in sorted(buckets.items(),
                                  key=lambda kv: (-len(kv[1]), kv[0][0])):
        merged.append({
            'location': loc, 'type': t, '_items': items,
            'seats': sorted({i['seat'] for i in items}),
            'seat_count': len({i['seat'] for i in items}),
            'evidence': [i['text'][:160] for i in items[:3]],
        })
    # 同一条的多个 location 会拆成多个 key，按「证据文本」再并一次，
    # 避免行号与引文指向同一处却被算作两个问题
    by_text = {}
    for it in merged:
        sig = tuple(sorted(set(i['text'][:80] for i in it['_items'])))
        cur = by_text.get(sig)
        if cur is None:
            by_text[sig] = {'location': it['location'], 'type': it['type'],
                            'items': list(it['_items'])}
        else:
            cur['items'] += it['_items']
            if it['location'] != cur['location'] and not it['location'].startswith('Q:'):
                cur['location'] = (cur['location']
                                   if not cur['location'].startswith('Q:')
                                   else it['location'])
    out = []
    for v in by_text.values():
        seen, uniq = set(), []
        for i in v['items']:
            k = i['text'][:80]
            if k not in seen:
                seen.add(k)
                uniq.append(i)
        out.append({'location': v['location'], 'type': v['type'],
                    'seats': sorted({i['seat'] for i in uniq}),
                    'seat_count': len({i['seat'] for i in uniq}),
                    'evidence': [i['text'][:160] for i in uniq[:3]]})
    out.sort(key=lambda x: (-x['seat_count'], x['location']))
    # merged_count 不应超过独立问题数；去重率按「合并掉的重复条目」计
    n_merged = min(len(out), len(all_issues))
    return {'raw_issue_count': len(all_issues), 'merged_count': n_merged,
            'dedup_ratio': round(1 - n_merged / max(1, len(all_issues)), 2),
            'issues': out}


def parse_verdict(content: str) -> str:
    if not content or not content.strip():
        return 'NO_OUTPUT'
    for line in content.strip().splitlines()[:30]:
        up = line.upper()
        for tok in VERDICT_TOKENS:
            if tok in up:
                return tok
    if any(l.startswith(('┊', '+', '-', '@@', 'diff ')) for l in
           content.strip().splitlines()[:5]):
        return 'DIFF_FORMAT'
    return 'UNPARSED'


def call_seat_model(provider: str, model: str, prompt_file: Path,
                    timeout: int = 280) -> dict:
    """审稿派工 —— 必须走 dispatch_to_model（HARD，2026-08-27 用户裁定）。

    禁用 hermes chat（含 --yolo）：误启即作废产物，不得验收/计席/据此裁决。
    次选是纯 completion 直调，delegate_task 亦禁用于审稿。

    300s 内跑完长审的三要件（缺一即超时）：
      1. 正文不塞 prompt 参数 —— 写进文件，让模型自己 read_file
      2. toolsets=['file'] 且 prompt 写死只读 —— 留读文件、拿掉可触发审批的执行工具
      3. 给输出长度上限（900 字）—— 高能力席不设限会写 3000+ 字顶到超时
    """
    try:
        from hermes_tools import dispatch_to_model  # type: ignore
    except Exception:
        try:
            from hermes import dispatch_to_model  # type: ignore
        except Exception as e:
            return {'ok': False, 'error': 'NO_DISPATCH_API %s' % e,
                    'duration': 0.0}

    inner = (
        '你是一个独立审稿席。第一步用 read_file 读完 %s 全文（内含待审正文），'
        '然后严格按该文件要求的格式输出。\n'
        '只允许 read_file，禁写代码、禁跑命令、禁联网。\n'
        '必须审读正文全文，不得凭摘要或前若干行下判断。\n'
        '全部输出控制在 900 字以内，每项不超两行。'
        % prompt_file
    )
    t0 = time.time()
    try:
        r = dispatch_to_model(provider=provider, model=model,
                              toolsets=['file'], timeout=timeout, prompt=inner)
    except Exception as e:
        return {'ok': False, 'error': 'DISPATCH_EXC %s' % repr(e)[:160],
                'duration': round(time.time() - t0, 1)}
    sec = round(time.time() - t0, 1)
    if isinstance(r, dict):
        content = (r.get('content') or r.get('text')
                   or r.get('stdout') or r.get('response') or '')
        err = r.get('error') or r.get('stderr') or ''
        ok = bool(r.get('ok', True)) and bool(content)
        return {'ok': ok, 'content': content, 'error': err[:200],
                'duration': sec, 'raw_keys': sorted(r.keys())[:8]}
    content = str(r or '')
    return {'ok': bool(content), 'content': content, 'duration': sec}


def run_seat(seat: str, body: str, timeout: int = TIMEOUT_PER_SEAT,
             seat_defs: dict | None = None) -> dict:
    """跑一席，沿同族 fallback 链；第一个出稿即用。"""
    cfg = (seat_defs or FIVE_SEATS)[seat]
    # 要件1：正文写进文件，不让 MCP 传输（塞 prompt 参数是超时的真因）
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    pf = STATE_DIR / f'_prompt_{seat}.md'
    # 角色OS 注入（HARD）：缺 OS 直接中断，不得裸审
    _prompt, role_os_loaded = inject_role_os(cfg['prompt'].format(body=body), seat)
    pf.write_text(_prompt, encoding='utf-8')
    print(f'  [OS] {seat}: ' + ', '.join(role_os_loaded))
    attempts = []
    for provider, model in cfg['chain']:
        r = call_seat_model(provider, model, pf, timeout=min(timeout, 280))
        err = r.get('error') or ''
        # 单席超时不得升级为「通道失效」（HARD）：标可重试，换下一个 provider
        kind = 'UPSTREAM_TIMEOUT_RETRYABLE' if ('TIMEOUT' in err.upper()
                                                or 'timeout' in err.lower()) else ''
        attempts.append({'provider': provider, 'model': model, 'ok': r['ok'],
                         'duration': r['duration'], 'error': err or kind,
                         'kind': kind})
        if r['ok']:
            # 验真（两道）：① 节点未被回落替换 ② 确实读了正文而非凭摘要
            v = verify_real_content(r.get('content') or '', body)
            res = {'seat': seat, 'role': cfg['role'],
                   'verdict': parse_verdict(r['content']),
                   'content': r['content'], 'provider': provider, 'model': model,
                   'duration_sec': r['duration'], 'attempts': attempts,
                   'session_id': r.get('session_id', ''), 'verify': v}
            # 假 PASS：回落到主控自身模型，结论作废，沿链换下一个
            if not v.get('verified'):
                res['verdict'] = 'FAKE_PASS'
                attempts[-1]['error'] = 'FAKE_%s' % v.get('reason', 'UNKNOWN')
                continue
            return res
    return {'seat': seat, 'role': cfg['role'], 'verdict': 'NO_OUTPUT', 'content': '',
            'provider': None, 'model': None,
            'duration_sec': sum(a['duration'] for a in attempts),
            'attempts': attempts, 'error': 'ALL_FALLBACKS_FAILED'}


def verify_real_content(content: str, body: str) -> dict:
    """验真：确认审稿意见确实基于正文，而不是凭摘要/凭空生成。

    dispatch_to_model 在目标节点出错时会回落，回包照常、exit 0 —— 假 PASS。
    模型若没真读正文，意见里不会出现正文中的具体片段。
    判据：意见中引用的原文片段，必须能在正文里找到。
    """
    if not content or len(content.strip()) < 40:
        return {'verified': False, 'reason': 'EMPTY_OR_TOO_SHORT',
                'quote_hits': 0, 'quote_total': 0, 'line_refs': 0,
                'body_word_hits': 0}
    # 从意见里抽引号内容，回正文里找
    # 正文与模型引文常是同一句的不同写法（中文数字「零点八」vs 阿拉伯「0.8」、
    # 省略号 vs ……、异体引号），字面全等会漏判，故做归一化后再比对
    def norm(s: str) -> str:
        s = s.replace('……', '').replace('...', '').replace('…', '')
        s = re.sub(r'[\s，。、；：！？,.;:!?「」『』""\'"“”（）()《》]', '', s)
        cn = '零一二三四五六七八九'
        s = re.sub(r'\d+', lambda m: ''.join(
            cn[int(d)] if d.isdigit() else d for d in m.group(0)), s)
        return s

    nbody = norm(body)
    qs = [m.group(1) for m in _QUOTE_RE.finditer(content)]
    qs += [m.group(1) for m in re.finditer(r'"([^"]{6,60})"', content)]
    qs += [m.group(1) for m in re.finditer(r"([一-鿿0-9．.\s]{8,40})[，。；]", content)]
    qs = [q.strip() for q in qs if len(q.strip()) >= 6]
    hit = 0
    for q in qs:
        nq = norm(q)
        if len(nq) < 6:
            continue
        if nq[:10] in nbody or nq[:8] in nbody or nq[:6] in nbody:
            hit += 1
    # 抽行号/段号引用
    line_refs = len([m for m in _LINE_REF_RE.finditer(content)])
    # 兜底：意见里出现正文的实体词（人名/术语）也算读过
    probes = [w for w in re.findall(r'[一-鿿]{3,6}', body) if w not in
              ('林星辰', '陈思琪')]
    uniq_probes = list(dict.fromkeys(probes))[:80]
    body_words = sum(1 for w in uniq_probes if w in norm(content))
    ok = (hit >= 1) or (line_refs >= 1 and body_words >= 3) or body_words >= 6
    return {'verified': ok, 'quote_hits': hit, 'quote_total': len(qs),
            'line_refs': line_refs, 'body_word_hits': body_words,
            'reason': '' if ok else 'NO_EVIDENCE_FROM_BODY'}


def verify_real_node(session_id: str, expect_provider: str,
                     expect_model: str) -> dict:
    """派工验真（2026-10-03 用户纠偏铁律，勿省）。

    dispatch_to_model / hermes chat 在目标节点报错时会**回落到会话自身模型**，
    回包照常落 stdout、exit_code 仍为 0 —— 这是「假 PASS」。
    第366章五审实测 5 次假 PASS（discovery/glm-5.3 连续2次、agentrouter、
    jichuan、onyxaxis），只看 stdout 会让带假证据的稿子定稿。

    判据：Turn ended 前**最后一条** API call 的 model/provider
    （带 toolsets 时 #1 只是读文件，不能看第一条）。
    见 provider=nous 或 model 不符 → 该席结论作废。
    """
    if not session_id:
        return {'verified': False, 'reason': 'NO_SESSION_ID'}
    roots = [Path(os.path.expanduser('~/.hermes/cache/terminal-output')),
             Path(os.path.expanduser('~/.hermes/cache/delegation')),
             Path(os.path.expanduser('~/.hermes/sessions')),
             Path(os.path.expanduser('~/.hermes/cron'))]
    txt, found = '', ''
    # 先按 session_id 精确定位
    for root in roots:
        if not root.exists():
            continue
        try:
            for f in root.rglob('*'):
                if not f.is_file() or f.suffix not in ('.log', '.jsonl', '.txt'):
                    continue
                if session_id not in f.name and session_id not in str(f.parent):
                    continue
                try:
                    txt = f.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    continue
                if 'API call' in txt:
                    found = str(f)
                    break
        except Exception:
            continue
        if found:
            break
    # 兜底：找最近修改且含该 session_id 的文件
    if not txt:
        cands = []
        for root in roots:
            if not root.exists():
                continue
            try:
                cands += [f for f in root.rglob('*.log') if f.is_file()]
            except Exception:
                pass
        cands.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        for f in cands[:60]:
            try:
                t = f.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            if session_id in t and 'API call' in t:
                txt, found = t, str(f)
                break
    if not txt:
        return {'verified': False, 'reason': 'NO_SESSION_LOG', 'session_id': session_id,
                'looked': found or 'searched terminal-output/delegation/sessions/cron'}
    lines = [l for l in txt.split('\n')
             if '"API call' in l or 'API call #' in l or 'api_call' in l.lower()]
    last = lines[-1] if lines else ''
    low = last.lower()
    hits_model = expect_model.lower().split('/')[-1][:12] in low
    hits_prov = expect_provider.lower().split(':')[-1] in low
    fell_back = ('provider=nous' in low.replace(' ', '')
                 or '"provider": "nous"' in last
                 or 'nous' in low and 'nousresearch' not in low)
    verified = bool(last) and (hits_model or hits_prov) and not fell_back
    return {'verified': verified, 'session_id': session_id,
            'last_call': last[:220], 'fell_back': fell_back,
            'reason': '' if verified else ('FALLBACK_TO_SELF' if fell_back
                                           else 'MODEL_MISMATCH')}


def load_state(chapter: int) -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    p = STATE_DIR / f'ch{chapter}_five_review_state.json'
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    return {'chapter': chapter, 'seats': {}, 'round': 0,
            'final_review': None, 'history': []}


def save_state(chapter: int, st: dict) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    p = STATE_DIR / f'ch{chapter}_five_review_state.json'
    p.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding='utf-8')
    return p


def verify_independence(results: dict) -> dict:
    used = {}
    for seat, r in results.items():
        prov = r.get('provider')
        if not prov or not (r.get('content') or '').strip():
            continue
        used.setdefault(prov, []).append(seat)
    collapsed = sorted(p for p, s in used.items() if len(s) > 1)
    rep = {'independent': bool(used) and not collapsed,
           'collapsed_providers': collapsed,
           'provider_to_seats': {p: sorted(s) for p, s in sorted(used.items())},
           'distinct_providers': len(used)}
    if not used:
        rep['reason'] = 'NO_EFFECTIVE_SEAT'
    elif collapsed:
        rep['reason'] = 'PROVIDER_COLLAPSE'
    return rep


def cmd_prepare(a) -> int:
    """只组装任务包（prompt 文件），不调用模型 —— 由主控并行发 dispatch_to_model。"""
    body_path = Path(a.body) if a.body else None
    if not body_path or not body_path.exists():
        for cand in (BASE / '新版' / f'第{a.chapter}章.md',
                     BASE / '正文' / f'第{a.chapter}章.md'):
            if cand.exists():
                body_path = cand
                break
    if not body_path or not body_path.exists():
        print(json.dumps({'ok': False, 'reason': 'BODY_NOT_FOUND'}, ensure_ascii=False))
        return 2
    body = body_path.read_text(encoding='utf-8')
    defs = FINAL_SEATS if a.final else FIVE_SEATS
    st = load_state(a.chapter)
    if a.final:
        todo = [s for s in defs
                if not st.get('final_review') or
                st['final_review'].get(s, {}).get('verdict') != 'PASS']
    else:
        todo = [s for s in defs
                if st['seats'].get(s, {}).get('verdict') != 'PASS']
    import hashlib
    prebind = {
        'sha256': hashlib.sha256(body.encode()).hexdigest(),
        'cjk': len(re.findall(r'[一-鿿]', body)),
        'first_line': body.strip().split('\n')[0][:40],
        'last_line': body.strip().split('\n')[-1][:20],
        'lines': len(body.strip().split('\n')),
        'chars': len(body),
    }
    PREBIND_TXT = (
        '\n【本轮预绑定事实（主控已算好，审席不得自行重算、'
        '也不得以"无法计算 SHA"为由判 FAIL）】\n'
        f"正文 SHA256 = {prebind['sha256'][:32]}…\n"
        f"净 CJK = {prebind['cjk']} ｜ 总字符 = {prebind['chars']} ｜ 行数 = {prebind['lines']}\n"
        f"首行 = {prebind['first_line']}\n"
        f"尾行 = {prebind['last_line']}\n"
        '审席只按内联正文与以上事实审读。\n'
    )
    out = {'chapter': a.chapter, 'stage': 'FINAL' if a.final else 'REVIEW',
           'body_path': str(body_path), 'body_chars': len(body),
           'prebind': prebind, 'seats': {}}
    for s in todo:
        cfg = defs[s]
        pf = STATE_DIR / f'_prompt_{s}.md'
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        _full, _loaded = inject_role_os(
            cfg['prompt'].format(body=body) + PREBIND_TXT, s)
        pf.write_text(_full, encoding='utf-8')
        print(f'  [OS] {s}: ' + ', '.join(_loaded))
        out['seats'][s] = {
            'role': cfg['role'], 'prompt_file': str(pf),
            'chain': cfg['chain'],
            'dispatch_call': {
                'provider': cfg['chain'][0][0], 'model': cfg['chain'][0][1],
                'toolsets': ['file'], 'timeout': 280,
                'prompt': ('你是一个独立审稿席。第一步用 read_file 读完 %s 全文'
                           '（内含待审正文），然后严格按该文件要求的格式输出。\n'
                           '只允许 read_file，禁写代码、禁跑命令、禁联网。\n'
                           '必须审读正文全文，不得凭摘要或前若干行下判断。\n'
                           '全部输出控制在 900 字以内，每项不超两行。' % pf),
            },
        }
    out['skipped_passed'] = [s for s in defs if s not in todo]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_apply(a) -> int:
    """把主控拿到的 dispatch 回包写回状态机并判 PASS/FAIL。"""
    body_path = Path(a.body) if a.body else None
    if not body_path or not body_path.exists():
        for cand in (BASE / '新版' / f'第{a.chapter}章.md',
                     BASE / '正文' / f'第{a.chapter}章.md'):
            if cand.exists():
                body_path = cand
                break
    body = body_path.read_text(encoding='utf-8') if body_path else ''
    import hashlib
    body_sha = hashlib.sha256(body.encode()).hexdigest() if body else ''
    payload = json.loads(Path(a.file).read_text(encoding='utf-8'))
    st = load_state(a.chapter)
    defs = FINAL_SEATS if a.final else FIVE_SEATS
    store_key = 'final_review' if a.final else 'seats'
    if a.final and st.get('final_review') is None:
        st['final_review'] = {}
    st['round'] += 1
    res = {}
    for seat, item in payload.items():
        content = item.get('content') or item.get('text') or ''
        prov = item.get('provider') or (defs.get(seat, {}).get('chain') or [('', '')])[0][0]
        model = item.get('model') or (defs.get(seat, {}).get('chain') or [('', '')])[0][1]
        v = verify_real_content(content, body) if body else {'verified': False,
                                                             'reason': 'NO_BODY'}
        verdict = parse_verdict(content) if content else 'NO_OUTPUT'
        if not v.get('verified'):
            verdict = 'FAKE_PASS'
        res[seat] = {'seat': seat, 'role': defs.get(seat, {}).get('role', ''),
                     'provider': prov, 'model': model, 'verdict': verdict,
                     'content': content, 'verify': v, 'body_sha': body_sha,
                     'round': st['round'],
                     'ts': datetime.now().isoformat(timespec='seconds')}
        st[store_key][seat] = res[seat]
    st['history'].append({'round': st['round'],
                          'stage': 'FINAL' if a.final else 'REVIEW',
                          'body_sha': body_sha, 'ran': sorted(res),
                          'verdicts': {s: r['verdict'] for s, r in res.items()}})
    p = save_state(a.chapter, st)
    cluster = None
    if not a.final:
        cluster = cluster_issues(st['seats'])
        cp = STATE_DIR / f'ch{a.chapter}_author_fix_list.json'
        cp.write_text(json.dumps(cluster, ensure_ascii=False, indent=2), encoding='utf-8')
        cluster['path'] = str(cp)
    tot = defs
    passed = [s for s in tot if st[store_key].get(s, {}).get('verdict') == 'PASS']
    out = {'ok': True, 'chapter': a.chapter,
           'stage': 'FINAL' if a.final else 'REVIEW', 'round': st['round'],
           'verdicts': {s: r['verdict'] for s, r in res.items()},
           'passed': sorted(passed), 'all_pass': len(passed) == len(tot),
           'state': str(p)}
    if cluster:
        out['author_fix_list'] = {'raw': cluster['raw_issue_count'],
                                  'merged': cluster['merged_count'],
                                  'dedup_ratio': cluster['dedup_ratio'],
                                  'path': cluster.get('path')}
    ind = verify_independence(res)
    out['independence'] = ind
    if a.final:
        out['next'] = ('终审全 PASS → 闭环写入与上传' if out['all_pass']
                       else '终审未过 → 汇总送作者席')
    else:
        out['next'] = ('五席全 PASS → prepare --final（换另一批模型）'
                       if out['all_pass'] else
                       '按 author_fix_list 送作者席一次改完 → 重跑 prepare')
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('prepare', help='组装任务包（不调模型，主控并行派发）')
    p.add_argument('--chapter', type=int, required=True)
    p.add_argument('--body', default='')
    p.add_argument('--final', action='store_true')
    p.set_defaults(fn=cmd_prepare)

    p = sub.add_parser('apply', help='回写 dispatch 回包并判 PASS/FAIL')
    p.add_argument('--chapter', type=int, required=True)
    p.add_argument('--body', default='')
    p.add_argument('--file', required=True, help='{seat:{content,provider,model}}')
    p.add_argument('--final', action='store_true')
    p.set_defaults(fn=cmd_apply)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == '__main__':
    raise SystemExit(main())
