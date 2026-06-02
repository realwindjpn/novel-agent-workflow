#!/usr/bin/env python3
"""角色联动上下文查询模块——只读，不改正文/索引。

函数:
  build_chapter_role_context(chapter: int) -> dict
  build_role_drift_checklist(chapter: int) -> str
  get_role_context_section(chapter: int) -> str  # 供 author_prompt 注入

数据源:
  - wiki/characters/faction-character-index.md (角色·势力总索引)
  - wiki/plot-threads/ending-hooks-index.md   (章末钩子缺口索引)
  - wiki/plot-threads/foreshadowing-index.md  (伏笔索引)
  - wiki/chapters/chNNN.md                    (章节Wiki)
  - wiki/raw/outline/科武纪元大纲_latest.md    (大纲)

原则:
  - 只读查询，不写任何文件
  - 数据缺失标 ROLE_CONTEXT_INCOMPLETE，不静默 PASS
  - 所有 WARNING 显式输出
"""
from __future__ import annotations
import re
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
CHAR_DIR = BASE / 'wiki/characters'
FACTION_DIR = BASE / 'wiki/factions'
PLOT_DIR = BASE / 'wiki/plot-threads'
CH_DIR = BASE / 'wiki/chapters'
OUTLINE = BASE / 'wiki/raw/outline/科武纪元大纲_latest.md'

FACTION_CHAR_IDX = CHAR_DIR / 'faction-character-index.md'
ENDING_HOOKS_IDX = PLOT_DIR / 'ending-hooks-index.md'
FORESHADOW_IDX = PLOT_DIR / 'foreshadowing-index.md'

# 主角团7人
MAIN_CHARACTERS = ['林星辰', '方宁', '陈思琪', '谢云', '苏雨晴', '赵刚', '李梦瑶']

# ── 工具函数 ─────────────────────────────────────────────

def _read(p: Path) -> str:
    if not p.exists():
        return ''
    return p.read_text(encoding='utf-8', errors='ignore')


def _section(text: str, name: str) -> str:
    m = re.search(rf'## {re.escape(name)}\n(.+?)(?=\n## |\Z)', text, re.S)
    return m.group(1).strip() if m else ''


# ── 从大纲提取章节信息 ─────────────────────────────────

def _parse_outline_chapter(chapter: int) -> dict:
    """从大纲 latest 提取第 chapter 章的标题/锚点/钩子/必打点。"""
    text = _read(OUTLINE)
    if not text:
        return {'title': '', 'anchor': '', 'hook': '', 'must': [], 'warnings': ['OUTLINE_MISSING']}

    # 大纲行格式: | 208 | 第119章 | 第三卷·暗流 | 统一进程 | 描述 | 钩子 | 字数 |
    # 或在 META 区域
    pattern = rf'第{chapter}章\s*[|｜]\s*(.+?)(?:\s*[|｜]|\s*$)'
    for line in text.splitlines():
        if f'第{chapter}章' in line:
            parts = [p.strip() for p in re.split(r'\s*[|｜]\s*', line.strip().strip('|'))]
            if len(parts) >= 2:
                return {
                    'title': parts[2] if len(parts) > 2 else parts[0],
                    'anchor': parts[3] if len(parts) > 3 else '',
                    'hook': parts[4] if len(parts) > 4 else '',
                    'must': [],
                    'warnings': [],
                }
    return {'title': '', 'anchor': '', 'hook': '', 'must': [], 'warnings': ['OUTLINE_CH_NOT_FOUND']}


# ── 从章节Wiki提取KG Entities ─────────────────────────

def _parse_chapter_wiki(chapter: int) -> dict:
    """从 wiki/chapters/chNNN.md 提取出场角色/概念/钩子。"""
    ch_path = CH_DIR / f'ch{chapter:03d}.md'
    text = _read(ch_path)
    if not text:
        return {'entities': [], 'concepts': [], 'ending_hook': '', 'next_hook': '', 'warnings': ['WIKI_CH_MISSING']}

    warnings = []
    # KG Entities
    ent_line = ''
    for ln in text.splitlines():
        if ln.strip().startswith('## KG Entities'):
            # 读取下一行
            idx = text.index(ln) + len(ln)
            rest = text[idx:].strip().splitlines()
            if rest:
                ent_line = rest[0]
            break
    entities = [e.strip() for e in re.split(r'[,，、]', ent_line.lstrip('- ')) if e.strip()] if ent_line else []
    if not entities:
        warnings.append('WIKI_NO_KG_ENTITIES')

    # KG Concepts
    conc_line = ''
    for ln in text.splitlines():
        if ln.strip().startswith('## KG Concepts'):
            idx = text.index(ln) + len(ln)
            rest = text[idx:].strip().splitlines()
            if rest:
                conc_line = rest[0]
            break
    concepts = [c.strip() for c in re.split(r'[,，、]', conc_line.lstrip('- ')) if c.strip()] if conc_line else []

    # Ending Hook / Next Chapter Hook
    ending = _section(text, 'Ending Hook') or _section(text, 'Ending Hook Evidence')
    next_hook = _section(text, 'Next Chapter Hook')

    if not ending:
        warnings.append('NO_ENDING_HOOK')
    if not next_hook:
        warnings.append('NO_NEXT_HOOK')

    return {
        'entities': entities,
        'concepts': concepts,
        'ending_hook': ending[:200],
        'next_hook': next_hook[:200],
        'warnings': warnings,
    }


def _parse_writing_constraints(char_name: str) -> str:
    """从角色页读取 ## 写作约束 段落。"""
    char_path = CHAR_DIR / f'{char_name}.md'
    text = _read(char_path)
    if not text:
        return ''
    sec = _section(text, '写作约束')
    return sec


# ── 从 faction-character-index 提取角色行 ───────────────

def _extract_char_rows(chapter: int, appearing: list[str]) -> list[dict]:
    """从 faction-character-index 提取出场角色的结构化行。"""
    text = _read(FACTION_CHAR_IDX)
    if not text:
        return []
    rows = []
    for ln in text.splitlines():
        if not ln.strip().startswith('|') or '---' in ln or '角色' in ln:
            continue
        cells = [c.strip() for c in ln.strip('|').split('|')]
        if len(cells) < 10:
            continue
        name = cells[0]
        # 匹配出场角色或主角
        if name in appearing or name in MAIN_CHARACTERS:
            rows.append({
                'name': name,
                'camp': cells[1],
                'role_type': cells[2],
                'first_ap': cells[3],
                'coverage': cells[4],
                'chaos': cells[5],
                'func': cells[6],
                'conflict': cells[7],
                'linked_f': cells[8],
                'status': cells[9],
            })
    return rows


# ── 从 foreshadowing-index 提取相关伏笔 ─────────────────

def _extract_foreshadow(chapter: int, entities: list[str]) -> list[dict]:
    """从 foreshadowing-index 提取与当章角色/章节相关的伏笔。"""
    text = _read(FORESHADOW_IDX)
    if not text:
        return []
    relevant = []
    ch_str = str(chapter)
    for ln in text.splitlines():
        if not ln.strip().startswith('| F'):
            continue
        cells = [c.strip() for c in ln.strip('|').split('|')]
        if len(cells) < 4:
            continue
        fid = cells[0]
        status = cells[3] if len(cells) > 3 else ''
        content = cells[2] if len(cells) > 2 else ''
        # 匹配: 伏笔内容含角色名, 或状态桶含当章号
        if any(e in content for e in entities) or ch_str in (cells[1] if len(cells) > 1 else ''):
            relevant.append({'id': fid, 'content': content[:100], 'status': status})
    return relevant


# ── 从 ending-hooks-index 提取当章钩子 ──────────────────

def _extract_hooks(chapter: int) -> dict:
    """从 ending-hooks-index 提取当章及前一章的钩子。"""
    text = _read(ENDING_HOOKS_IDX)
    if not text:
        return {'prev_ending': '', 'this_ending': '', 'this_next': '', 'warnings': ['HOOKS_IDX_MISSING']}
    result = {'prev_ending': '', 'this_ending': '', 'this_next': '', 'warnings': []}
    for ln in text.splitlines():
        if not ln.strip().startswith('|'):
            continue
        cells = [c.strip() for c in ln.strip('|').split('|')]
        if len(cells) < 3:
            continue
        try:
            ch_num = int(cells[0])
        except ValueError:
            continue
        if ch_num == chapter - 1:
            result['prev_ending'] = (cells[1] if len(cells) > 1 else '')[:200]
        if ch_num == chapter:
            result['this_ending'] = (cells[1] if len(cells) > 1 else '')[:200]
            result['this_next'] = (cells[2] if len(cells) > 2 else '')[:200]
    if not result['this_ending'] and not result['this_next']:
        result['warnings'].append('CH_HOOKS_NOT_IN_INDEX')
    return result


# ── 构建角色联动上下文（主函数） ────────────────────────

def build_chapter_role_context(chapter: int) -> dict:
    """为指定章节构建角色联动上下文。

    返回:
      {
        'chapter': int,
        'outline': {...},
        'appearing_characters': [...],
        'character_rows': [...],
        'faction_context': [...],
        'foreshadows': [...],
        'hooks': {...},
        'warnings': [...],
        'incomplete': bool,
      }
    """
    warnings = []
    incomplete = False

    # 1. 大纲
    outline = _parse_outline_chapter(chapter)
    warnings.extend(outline.get('warnings', []))

    # 2. 章节Wiki
    wiki = _parse_chapter_wiki(chapter)
    warnings.extend(wiki.get('warnings', []))
    appearing = wiki.get('entities', [])
    if not appearing:
        warnings.append('ROLE_CONTEXT_INCOMPLETE: NO_APPEARING_CHARACTERS')
        incomplete = True

    # 3. 角色索引行
    char_rows = _extract_char_rows(chapter, appearing)
    if not char_rows:
        warnings.append('ROLE_CONTEXT_INCOMPLETE: NO_CHAR_ROWS')
        incomplete = True

    # 检查主角 TODO 状态
    for row in char_rows:
        if row['name'] in MAIN_CHARACTERS:
            if row['func'] == 'TODO':
                warnings.append(f"WARNING: {row['name']} 剧情功能=TODO")
            if row['conflict'] == 'TODO':
                warnings.append(f"WARNING: {row['name']} 冲突关系=TODO")
            if row['linked_f'] == 'TODO':
                warnings.append(f"WARNING: {row['name']} 关联伏笔=TODO")

    # 4. 势力上下文
    faction_chars = set()
    for row in char_rows:
        if row['camp'] not in ('主角团', '', 'UNKNOWN'):
            faction_chars.add(row['camp'])

    faction_context = []
    faction_text = _read(FACTION_CHAR_IDX)
    if faction_text:
        in_faction_section = False
        for ln in faction_text.splitlines():
            if '## B. 势力索引' in ln:
                in_faction_section = True
                continue
            if in_faction_section and ln.startswith('## '):
                break
            if in_faction_section and ln.strip().startswith('|') and '---' not in ln and '势力' not in ln:
                cells = [c.strip() for c in ln.strip('|').split('|')]
                if len(cells) >= 4:
                    fac_name = cells[0]
                    # 主角团相关势力或铁幕联盟（常见对手）
                    if fac_name in faction_chars or fac_name == '铁幕联盟':
                        faction_context.append({
                            'name': fac_name,
                            'position': cells[3][:100] if len(cells) > 3 else '',
                        })

    # 5. 伏笔
    foreshadows = _extract_foreshadow(chapter, appearing)
    # 也搜索主角名
    if not foreshadows:
        foreshadows = _extract_foreshadow(chapter, MAIN_CHARACTERS)
    if not foreshadows:
        warnings.append('WARNING: NO_RELATED_FORESHADOWS')

    # 6. 钩子
    hooks = _extract_hooks(chapter)
    warnings.extend(hooks.get('warnings', []))

    # 7. 禁偏移项（从角色行提取 TODO 项作为禁偏移提醒）
    drift_guards = []
    for row in char_rows:
        if row['name'] in MAIN_CHARACTERS:
            if row['conflict'] != 'TODO' and row['conflict'] != '-':
                drift_guards.append(f"{row['name']} 对抗线: {row['conflict']}")
            if row['func'] != 'TODO' and row['func'] != '-':
                drift_guards.append(f"{row['name']} 剧情功能: {row['func']}")

    # 8. 写作约束
    writing_constraints = {}
    for name in appearing:
        if name in MAIN_CHARACTERS:
            wc = _parse_writing_constraints(name)
            if wc:
                writing_constraints[name] = wc

    if incomplete:
        warnings.insert(0, 'ROLE_CONTEXT_INCOMPLETE')

    return {
        'chapter': chapter,
        'outline': outline,
        'appearing_characters': appearing,
        'character_rows': char_rows,
        'faction_context': faction_context,
        'foreshadows': foreshadows,
        'hooks': hooks,
        'drift_guards': drift_guards,
        'writing_constraints': writing_constraints,
        'warnings': warnings,
        'incomplete': incomplete,
    }


# ── 生成可注入 author_prompt 的文本切片 ─────────────────

def get_role_context_section(chapter: int) -> str:
    """生成【角色联动上下文】文本，供 author_prompt 注入。"""
    ctx = build_chapter_role_context(chapter)
    lines = ['【角色联动上下文】']

    # 出场角色
    if ctx['appearing_characters']:
        lines.append(f"- 出场角色: {', '.join(ctx['appearing_characters'])}")
    else:
        lines.append('- 出场角色: [数据缺失]')

    # 角色行（主角）
    main_rows = [r for r in ctx['character_rows'] if r['name'] in MAIN_CHARACTERS]
    if main_rows:
        lines.append('- 角色状态:')
        for r in main_rows:
            parts = [r['name']]
            if r['func'] != 'TODO' and r['func'] != '-':
                parts.append(f"功能={r['func']}")
            if r['conflict'] != 'TODO' and r['conflict'] != '-':
                parts.append(f"对抗={r['conflict']}")
            if r['linked_f'] != 'TODO' and r['linked_f'] != '-':
                parts.append(f"伏笔={r['linked_f']}")
            lines.append(f"  {'｜'.join(parts)}")

    # 势力
    if ctx['faction_context']:
        lines.append('- 势力代表:')
        for f in ctx['faction_context']:
            lines.append(f"  {f['name']}: {f['position']}")

    # 对抗线缺口
    gap_lines = [l for l in _read(FACTION_CHAR_IDX).splitlines()
                 if '## C. 对抗线缺口' in l]
    in_gap = False
    for ln in _read(FACTION_CHAR_IDX).splitlines():
        if '## C. 对抗线缺口' in ln:
            in_gap = True
            continue
        if in_gap and ln.startswith('## '):
            break
        if in_gap and ln.strip().startswith('|') and '---' not in ln and '对抗线' not in ln:
            cells = [c.strip() for c in ln.strip('|').split('|')]
            if cells and any(c in (cells[0] if cells else '') for c in ctx['appearing_characters']):
                lines.append(f"- 对抗线缺口: {cells[0]} ({cells[2] if len(cells) > 2 else ''})")

    # 伏笔
    if ctx['foreshadows']:
        lines.append('- 关联伏笔:')
        for f in ctx['foreshadows']:
            lines.append(f"  {f['id']}: {f['content']} [{f['status']}]")

    # 钩子
    h = ctx['hooks']
    if h.get('prev_ending'):
        lines.append(f"- 上章Ending Hook: {h['prev_ending']}")
    if h.get('this_next'):
        lines.append(f"- 本章Next Hook: {h['this_next']}")

    # 禁偏移项
    if ctx['drift_guards']:
        lines.append('- 禁偏移项:')
        for g in ctx['drift_guards']:
            lines.append(f"  {g}")

    # 写作约束
    wc = ctx.get('writing_constraints', {})
    if wc:
        lines.append('- 写作约束:')
        for cname, ctext in wc.items():
            lines.append(f"  【{cname}】")
            for cl in ctext.splitlines():
                cl = cl.strip()
                if cl:
                    lines.append(f"    {cl}")

    # WARNING
    if ctx['warnings']:
        lines.append('- ⚠ WARNING:')
        for w in ctx['warnings']:
            lines.append(f"  {w}")

    return '\n'.join(lines)


# ── 生成复审门禁检查项 ─────────────────────────────────

def build_role_drift_checklist(chapter: int) -> str:
    """生成角色偏移复审门禁，供编辑/读者复审 prompt 注入。"""
    ctx = build_chapter_role_context(chapter)
    lines = [
        '【角色偏移门禁检查】',
        '请逐项检查并输出 ROLE_DRIFT_PASS 或 ROLE_DRIFT_FAIL:',
        '',
    ]

    # 检查项1: 出场角色是否在索引中有记录
    indexed = {r['name'] for r in ctx['character_rows']}
    for c in ctx['appearing_characters']:
        if c in indexed:
            lines.append(f'✓ {c} 在 faction-character-index 中有记录')
        else:
            lines.append(f'✗ {c} 不在 faction-character-index 中 → 可能偏移')

    # 检查项2: 角色行为是否违反写作约束
    lines.append('')
    lines.append('请检查角色行为是否违反以下约束:')
    for r in ctx['character_rows']:
        if r['name'] in MAIN_CHARACTERS and r['func'] != 'TODO':
            lines.append(f'- {r["name"]}: 剧情功能={r["func"]}')

    # 检查项3: 对抗线是否推进
    if ctx['drift_guards']:
        lines.append('')
        lines.append('对抗线检查:')
        for g in ctx['drift_guards']:
            lines.append(f'- {g}')

    # 检查项4: 伏笔是否推进
    if ctx['foreshadows']:
        lines.append('')
        lines.append('伏笔推进检查:')
        for f in ctx['foreshadows']:
            lines.append(f'- {f["id"]}: {f["content"]} [{f["status"]}] — 是否在本章有推进?')

    # 检查项5: 章末钩子
    h = ctx['hooks']
    if h.get('this_next'):
        lines.append('')
        lines.append(f'章末钩子检查: {h["this_next"]}')

    lines.append('')
    lines.append('输出格式:')
    lines.append('ROLE_DRIFT_PASS 或 ROLE_DRIFT_FAIL')
    lines.append('FAIL时列: 偏离角色页/势力页/伏笔ID + 具体证据')

    return '\n'.join(lines)


# ── CLI 测试入口 ─────────────────────────────────────────

if __name__ == '__main__':
    import sys, json
    ch = int(sys.argv[1]) if len(sys.argv) > 1 else 119
    ctx = build_chapter_role_context(ch)
    print(f'=== Chapter {ch} Role Context ===')
    print(f'Appearing: {ctx["appearing_characters"]}')
    print(f'Character rows: {len(ctx["character_rows"])}')
    print(f'Factions: {len(ctx["faction_context"])}')
    print(f'Foreshadows: {len(ctx["foreshadows"])}')
    print(f'Drift guards: {len(ctx["drift_guards"])}')
    print(f'Incomplete: {ctx["incomplete"]}')
    print(f'Warnings ({len(ctx["warnings"])}):')
    for w in ctx['warnings']:
        print(f'  {w}')
    print()
    print('--- Author Prompt Section ---')
    print(get_role_context_section(ch))
    print()
    print('--- Drift Checklist ---')
    print(build_role_drift_checklist(ch))
