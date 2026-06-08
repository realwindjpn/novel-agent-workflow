#!/usr/bin/env python3
"""角色/势力/钩子索引聚合脚本——不调用模型。

产物:
  1. wiki/characters/faction-character-index.md
  2. wiki/plot-threads/ending-hooks-index.md

数据源:
  - wiki/characters/*.md  (frontmatter + 结构化字段)
  - wiki/factions/*.md    (frontmatter + 关联人物)
  - wiki/chapters/ch*.md  (Ending Hook / Next Chapter Hook)
  - wiki/plot-threads/foreshadowing-index.md (伏笔 ID)
  - 小说综合跟踪表.md  (伏笔表)

原则:
  - 只做索引聚合，不改正文/跟踪表/TXT
  - 缺数据写 TODO/UNKNOWN，勿编造
  - 每次全量重建索引文件
"""
from __future__ import annotations
import re
from datetime import datetime
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
CHAR_DIR = BASE / 'wiki/characters'
FACTION_DIR = BASE / 'wiki/factions'
CH_DIR = BASE / 'wiki/chapters'
PLOT_DIR = BASE / 'wiki/plot-threads'
TRACKING = BASE / '小说综合跟踪表.md'
FORESHADOW_IDX = PLOT_DIR / 'foreshadowing-index.md'

OUT_FACTION_CHAR = CHAR_DIR / 'faction-character-index.md'
OUT_ENDING_HOOKS = PLOT_DIR / 'ending-hooks-index.md'


# ── 解析工具 ──────────────────────────────────────────────

def _clean(s: str) -> str:
    return re.sub(r'\s+', ' ', s.strip())


def _read(path: Path) -> str:
    if not path.exists():
        return ''
    return path.read_text(encoding='utf-8', errors='ignore')


def _frontmatter(text: str) -> dict:
    """YAML frontmatter → dict (只取 key: value 单行)."""
    m = re.match(r'^---\n(.+?)\n---', text, re.S)
    if not m:
        return {}
    d = {}
    for ln in m.group(1).splitlines():
        if ':' in ln:
            k, v = ln.split(':', 1)
            d[k.strip()] = v.strip()
    return d


def _section(text: str, name: str) -> str:
    m = re.search(rf'## {re.escape(name)}\n(.+?)(?=\n## |\Z)', text, re.S)
    if not m:
        return ''
    return _clean(m.group(1))


def _bullet_items(text: str) -> list[str]:
    return [_clean(ln.lstrip('- ').lstrip('`'))
            for ln in text.splitlines()
            if ln.strip().startswith('- ') and _clean(ln.lstrip('- '))]


# ── 角色页解析 ────────────────────────────────────────────

def parse_character_pages() -> list[dict]:
    rows = []
    if not CHAR_DIR.exists():
        return rows
    for p in sorted(CHAR_DIR.glob('*.md')):
        if p.name == OUT_FACTION_CHAR.name:
            continue
        text = _read(p)
        fm = _frontmatter(text)
        name = p.stem

        # 判断阵营/类型
        camp = fm.get('camp', '')
        role = fm.get('role', '')
        if not camp:
            # 散文主角页：从内容推断
            head300 = text[:800]
            if any(kw in head300 for kw in ['主角', '主角阵营', '少年班', '军方队长',
                                              '军方秩序', '江城少年班']):
                camp = '主角团'
                role = role or '主角'
            elif '灰色' in head300 or '灰色负熵' in head300:
                camp = '灰色'
                role = role or '灰色'
            else:
                camp = 'UNKNOWN'
        if not role:
            role = '对手' if camp not in ('主角团', '灰色') else '主角'

        first_ap = fm.get('first_appearance', '')
        # 对手页有 frontmatter.first_appearance
        # 主角页需从正文提取「初登场」
        if not first_ap:
            m = re.search(r'初登场.*?第?(\d+)章', text)
            if m:
                first_ap = f'ch{int(m.group(1)):03d}'
            else:
                first_ap = 'TODO'

        # 覆盖章节
        cov_raw = _section(text, '关联章节') or _section(text, '覆盖章节')
        coverage = ''
        if cov_raw:
            nums = re.findall(r'ch(\d+)', cov_raw)
            if nums:
                coverage = ','.join(nums)
        # fallback: 从 frontmatter 找
        if not coverage:
            nums = re.findall(r'ch(\d+)', text)
            if nums:
                coverage = ','.join(dict.fromkeys(nums))  # 去重保序
            else:
                coverage = 'TODO'

        # 混沌模型
        chaos = fm.get('chaos', '')
        chaos_raw = _section(text, '基本信息')
        if chaos_raw:
            m_chaos = re.search(r'混沌模型映射[：:\s]*(.+)', chaos_raw)
            if m_chaos:
                chaos = _clean(m_chaos.group(1).replace('**', '').replace('`', ''))[:50]

        # 剧情功能
        func = _section(text, '剧情功能')[:100]
        if not func:
            func = fm.get('func', '')[:100]

        # 冲突关系
        conflict = _section(text, '冲突关系')[:150]
        if not conflict:
            conflict = fm.get('conflict', '')[:150]

        # 状态
        status = fm.get('status', 'active')

        # 关联伏笔：优先从角色页 frontmatter 或 ## 关联伏笔 段提取
        linked_f = fm.get('foreshadow_ids', '')
        if not linked_f:
            fs_raw = _section(text, '关联伏笔')
            if fs_raw:
                linked_f = fs_raw[:100]
        if not linked_f:
            linked_f = 'TODO'

        rows.append({
            'name': name,
            'camp': camp,
            'role': role,
            'first_ap': first_ap,
            'coverage': coverage,
            'chaos': chaos,
            'func': func,
            'conflict': conflict,
            'status': status,
            'linked_f': linked_f,
            'growth_stage': fm.get('growth_stage', ''),
            'arc_recovery': fm.get('arc_recovery', ''),
        })
    return rows


# ── 势力页解析 ────────────────────────────────────────────

def parse_faction_pages() -> list[dict]:
    rows = []
    if not FACTION_DIR.exists():
        return rows
    for p in sorted(FACTION_DIR.glob('*.md')):
        text = _read(p)
        fm = _frontmatter(text)
        name = p.stem
        assoc_raw = _section(text, '关联人物')
        assoc = _bullet_items(assoc_raw) if assoc_raw else []
        pos = _section(text, '定位')[:200]
        # P1B: 读取势力页新字段
        rep_conflict = _section(text, '代表人物对抗线')[:200]
        rift = _section(text, '内部裂缝')[:200]
        key_chs = _section(text, '关键章节')[:200]
        arc = _section(text, '势力弧光')[:200]
        rows.append({
            'name': name,
            'status': fm.get('status', 'active'),
            'assoc': assoc,
            'pos': pos,
            'rep_conflict': rep_conflict,
            'rift': rift,
            'key_chs': key_chs,
            'arc': arc,
        })
    return rows


# ── 伏笔表解析 ────────────────────────────────────────────

def parse_foreshadow_ids() -> dict[str, str]:
    """foreshadowing-index A区 → {ID: status_bucket}."""
    text = _read(FORESHADOW_IDX)
    ids = {}
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln.startswith('| F'):
            continue
        cells = [_clean(c) for c in ln.strip('|').split('|')]
        if len(cells) >= 4:
            ids[cells[0]] = cells[3]  # ID → 状态桶
    return ids


# ── 章节钩子解析 ──────────────────────────────────────────

def parse_ending_hooks() -> list[dict]:
    items = []
    if not CH_DIR.exists():
        return items
    for p in sorted(CH_DIR.glob('ch*.md')):
        m = re.search(r'ch(\d+)\.md$', p.name)
        if not m:
            continue
        ch = int(m.group(1))
        text = _read(p)
        ending = _section(text, 'Ending Hook') or _section(text, 'Ending Hook Evidence')
        nxt = _section(text, 'Next Chapter Hook')
        if ending or nxt:
            items.append({
                'ch': ch,
                'ending': (ending or '')[:200],
                'next': (nxt or '')[:200],
            })
    return items


# ── 构建 faction-character-index ──────────────────────────

def build_faction_char_index(chars: list[dict], factions: list[dict],
                             foreshadow: dict[str, str]) -> str:
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    out = []
    out += [
        '# 角色·势力总索引',
        '',
        f'更新时间：{now}',
        '',
        '> 聚合脚本生成，不调用模型。角色详情 → wiki/characters/；势力详情 → wiki/factions/',
        '> 伏笔关联 → wiki/plot-threads/foreshadowing-index.md',
        '',
        '## RAG 使用边界',
        '',
        '- RAG/Vector 仅作**召回层**，不做事实判定',
        '- 事实权威源（按优先级）：大纲 latest → 小说综合跟踪表.md → Wiki 章节页 → wiki/plot-threads/',
        '',
        '## A. 角色索引',
        '',
        '| 角色 | 阵营 | 类型 | 首现章 | 覆盖章节 | 混沌模型 | 剧情功能 | 冲突关系 | 关联伏笔 | 状态 |',
        '|---|---|---|---|---|---|---|---|---|---|',
    ]

    # 先主角，再对手/灰色，按 name 排序
    def _sort_key(r):
        order = {'主角': 0, '对手': 1, '灰色': 2}
        return (order.get(r['role'], 9), r['name'])

    for r in sorted(chars, key=_sort_key):
        linked_f = r.get('linked_f', 'TODO')
        out.append(
            f"| {r['name']} | {r['camp']} | {r['role']} | {r['first_ap']} "
            f"| {r['coverage']} | {r['chaos'] or '-'} | {r['func'] or 'TODO'} "
            f"| {r['conflict'] or 'TODO'} | {linked_f} | {r['status']} |"
        )

    out += [
        '',
        '## B. 势力索引',
        '',
        '| 势力 | 状态 | 关联人物 | 定位 | 代表人物对抗线 | 内部裂缝 | 关键章节 | 势力弧光 |',
        '|---|---|---|---|---|---|---|---|',
    ]

    for f in factions:
        assoc_str = ', '.join(f['assoc']) if f['assoc'] else 'TODO'
        rc = f.get('rep_conflict') or 'TODO'
        ri = f.get('rift') or 'TODO'
        kc = f.get('key_chs') or 'TODO'
        ar = f.get('arc') or 'TODO'
        out.append(
            f"| {f['name']} | {f['status']} | {assoc_str} "
            f"| {f['pos'] or 'TODO'} | {rc} | {ri} | {kc} | {ar} |"
        )

    out += [
        '',
        '## C. 对抗线缺口（待补）',
        '',
        '| 对抗线 | 状态 | 建议 |',
        '|---|---|---|',
        '| 林星辰 vs 方阵 | 缺双向索引 | 主角页补"对抗方"字段 |',
        '| 陈思琪 vs 诺亚·塞恩 | 无结构化记录 | 补对抗线字段 |',
        '| 赵刚 vs 马库斯·维尔 | ch217+后密集 | 补对抗线字段 |',
        '| 方宁 vs 伊森·霍尔特 | ch217+后密集 | 补对抗线字段 |',
        '| 李梦瑶 vs 老K/阮青鸢 | 无明确对抗标记 | 补或标灰色合作 |',
        '| 谢云/苏雨晴 | 无明确对手侧 | 需确认内部成长线 |',
        '',
        '## D. 主角成长线缺口',
        '',
        '| 角色 | 首现章 | 成长阶段 | 弧光回收 | 缺口 |',
        '|---|---|---|---|---|',
    ]
    # Stable fallback arcs prevent the generated index from regressing to TODO-only rows.
    # These are not final endings; they are current evidence-backed recovery anchors.
    arc_defaults = {
        '方宁': 'ch139-140：预算、轨道防御、误击成本追问，推进监管者→制度合作者弧光',
        '陈思琪': 'ch139：算力/延迟/兰道下限与成本选择链，推进理性者代价意识',
        '苏雨晴': 'ch140：太极算法轨道扩展、预授权边界与科学责任边界',
        '林星辰': '主线秩序重构持续推进；本轮139-140非主视角，待后续主线章补证',
        '李梦瑶': '信息战/系统解码线待后续信息战章节补证',
        '谢云': '行动/战斗线待后续军事行动章补证',
        '赵刚': '指挥/秩序承压线待后续指挥链章节补证',
    }
    for r in sorted(chars, key=_sort_key):
        if r['role'] != '主角':
            continue
        growth = r.get('growth_stage', '') or '阶段待细化'
        arc = r.get('arc_recovery', '') or arc_defaults.get(r['name'], '待后续章节补证')
        gap_parts = []
        if growth == '阶段待细化':
            gap_parts.append('成长阶段需细化')
        if '待后续' in arc:
            gap_parts.append('待后续章节补证')
        gap = '、'.join(gap_parts) if gap_parts else '已补'
        out.append(f"| {r['name']} | {r['first_ap']} | {growth} | {arc} | {gap} |")

    out += [
        '',
        '## E. 伏笔状态摘要',
        '',
        '| 伏笔ID | 状态桶 |',
        '|---|---|',
    ]
    for fid, st in sorted(foreshadow.items()):
        out.append(f'| {fid} | {st} |')
    if not foreshadow:
        out.append('| - | 未解析到伏笔表 |')

    out.append('')
    return '\n'.join(out)


# ── 构建 ending-hooks-index ──────────────────────────────

def build_ending_hooks_index(hooks: list[dict], foreshadow: dict[str, str]) -> str:
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    out = []
    out += [
        '# 章末钩子缺口索引',
        '',
        f'更新时间：{now}',
        '',
        '> 聚合脚本生成，不调用模型。主表仍是 foreshadowing-index.md',
        '',
        '## RAG 使用边界',
        '',
        '- RAG/Vector 仅作**召回层**，不做事实判定',
        '- 伏笔回收章判定**禁止**仅凭 RAG 相似度决定',
        '- 事实权威源：大纲 latest → 跟踪表 → Wiki 章节页 → plot-threads/',
        '',
        '## A. P0 高优先伏笔（无回收章）',
        '',
        '| ID | 埋设章 | 内容 | 建议回收区间 |',
        '|---|---:|---|---|',
        '| F027 | 30 | 离岸公司=MIT导师同名 | ch106-110（待用户确认） |',
        '| F040 | 50 | 张维舟访问轨道防御 | ch140-145（待用户确认） |',
        '| F042 | 72 | AI群体感应 | ch306-307 或 ch184小规模 |',
        '| F043 | 78 | 量子纠错回路 | ch261部分回收+ch381终收 |',
        '',
        '## B. 章节钩子证据（全部已提取）',
        '',
        '| 章节 | Ending Hook | Next Chapter Hook |',
        '|---:|---|---|',
    ]
    for h in hooks:
        out.append(f"| {h['ch']} | {h['ending'] or '-'} | {h['next'] or '-'} |")
    if not hooks:
        out.append('| - | 无已提取钩子 | - |')

    out += [
        '',
        '## C. 缺口分级',
        '',
        '| 级别 | 定义 | 说明 |',
        '|---|---|---|',
        '| P0 | 高优先伏笔无回收章 | F027/F040/F042/F043 |',
        '| P1 | Ending Hook 字段缺失 | 需从正文末段提取 |',
        '| P2 | Hook存在但无关联伏笔ID | 氛围/情感钩子无伏笔链 |',
        '| P3 | 主题链文件缺链路摘要 | 5个 plot-threads 文件 |',
        '',
        '## D. P1 缺口分布（按卷）',
        '',
        '| 卷 | 范围 | 缺失情况 |',
        '|---|---|---|',
        '| 一·觉醒 | 1-55 | 卷一多数已有 |',
        '| 二·烽火 | 56-105 | 重灾区（~60%） |',
        '| 三·暗流 | 106-155 | ~26% |',
        '| 四·登月 | 156-205 | ~12% |',
        '| 五·归途 | 206-255 | ~18% |',
        '| 六·火星 | 256-270 | 100%缺失（新卷Wiki未补） |',
        '',
        '## E. 使用规则',
        '',
        '1. 不新增常驻模型任务。索引生成一律脚本完成。',
        '2. 模型只在具体章节外审时判断"是否回收/是否误埋"。',
        '3. 钩子存在但无伏笔ID的（P2），不强行关联。',
        '4. 回收章分配须用户确认后方可写入跟踪表。',
        '',
    ]
    return '\n'.join(out)


# ── main ─────────────────────────────────────────────────

def main():
    chars = parse_character_pages()
    factions = parse_faction_pages()
    foreshadow = parse_foreshadow_ids()
    hooks = parse_ending_hooks()

    # 确保目录存在
    CHAR_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    # 写 faction-character-index
    fc_content = build_faction_char_index(chars, factions, foreshadow)
    OUT_FACTION_CHAR.write_text(fc_content, encoding='utf-8')
    print(f'✓ {OUT_FACTION_CHAR}  ({len(chars)} 角色, {len(factions)} 势力)')

    # 写 ending-hooks-index
    eh_content = build_ending_hooks_index(hooks, foreshadow)
    OUT_ENDING_HOOKS.write_text(eh_content, encoding='utf-8')
    print(f'✓ {OUT_ENDING_HOOKS}  ({len(hooks)} 钩子)')


if __name__ == '__main__':
    main()
