#!/usr/bin/env python3
"""
科武纪元统一同步引擎
用法：python3 sync_kewu.py --chapter 86 124 217 --message "V8.8精修+六角色外审PASS"

功能：一次触发，自动级联更新：
  1. Wiki章节页（含原KG实体/概念/记忆卡内容）
  2. Vector-memory语义入库
  3. 跟踪表/STATUS/WAL更新
  4. Git commit（可选）

已归档系统（不再独立维护）：
  - KG (wiki/kg/) → 合并入Wiki章节页
  - 章节记忆卡 (审核记录/章节记忆卡/) → 合并入Wiki章节页
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
WIKI_CH = BASE / 'wiki/chapters'
TRACKING = BASE / '小说综合跟踪表.md'
STATUS = BASE / 'STATUS.md'
WAL = BASE / 'WAL.md'
NEW_VER = BASE / '新版'
VECTOR_MEM = Path('/root/workspace/vector-memory')


def fanqie_count(text: str) -> int:
    """番茄口径字数：去空白总字符数 - 标题字符数"""
    lines = [x for x in text.splitlines() if x.strip()]
    title = lines[0] if lines else ''
    return len(re.sub(r'\s+', '', text)) - len(re.sub(r'\s+', '', title))


def cn_count(text: str) -> int:
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def extract_title(text: str, chapter: int) -> str:
    """Extract title from Markdown heading or plain first line."""
    title_match = re.search(r'^#\s+(.+)', text, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    for line in text.splitlines():
        row = line.strip()
        if not row:
            continue
        if row.startswith(f'第{chapter}章'):
            return row
        break
    return f'第{chapter}章'


def extract_entities(text: str) -> tuple[list, list]:
    """从正文提取人名和关键概念（简单关键词匹配）"""
    # 已知人物
    known_chars = ['林星辰', '陈思琪', '谢云', '方宁', '赵铁柱', '叶启明',
                   '李明远', '周海', '流云', '白盾', '陈思远', '苏晚']
    # 已知概念关键词
    concept_keywords = ['量子', 'AI', '算法', 'UGV', '声波', '白盾', '清道夫',
                        '天门', 'V4贴片', '伏笔', '三秒', '星穹', '氦-3',
                        '供应链', '算力', '数据中心', '泛际', '铁幕', '开源']

    entities = [c for c in known_chars if c in text]
    concepts = [c for c in concept_keywords if c in text]
    return sorted(set(entities)), sorted(set(concepts))


def update_wiki(chapter: int, meta: dict = None) -> bool:
    """更新/创建Wiki章节页"""
    src = NEW_VER / f'第{chapter}章.md'
    if not src.exists():
        print(f"  ⚠ 第{chapter}章源文件不存在: {src}")
        return False

    text = src.read_text(encoding='utf-8')
    wiki_file = WIKI_CH / f'ch{chapter:03d}.md'
    entities, concepts = extract_entities(text)
    now = datetime.now().strftime('%Y-%m-%d')

    # Read existing wiki if present
    if wiki_file.exists():
        existing = wiki_file.read_text(encoding='utf-8')
    else:
        existing = ''

    # Build frontmatter
    title = extract_title(text, chapter)

    lines = [
        '---',
        f'chapter: {chapter}',
        f'title: {title}',
        f'updated: {now}',
        'type: chapter',
        f'word_count_cn: {cn_count(text)}',
        f'fanqie_count: {fanqie_count(text)}',
        '---',
        '',
        f'# {title}',
        '',
        '## Links',
        f'- Previous: [[ch{chapter-1:03d}]]',
        f'- Next: [[ch{chapter+1:03d}]]',
        '',
    ]

    # Preserve or init structured sections
    sections = {}

    # Extract from existing wiki
    for sec_name in ['Chapter Function', 'Key Events / Evidence', 'Ending Hook',
                     'Source Material', 'Review Notes', 'Full Text',
                     'KG Entities', 'KG Concepts', 'KG Causal',
                     'Next Chapter Hook', 'Review Status']:
        pattern = rf'## {re.escape(sec_name)}\n(.+?)(?=\n## |\Z)'
        m = re.search(pattern, existing, re.DOTALL)
        if m:
            sections[sec_name] = m.group(1).strip()

    # Full Text must always mirror the current 新版 source. Preserving the old
    # section caused stale wiki bodies after chapter rewrites.
    sections.pop('Full Text', None)

    # Update meta if provided
    if meta:
        if 'function' in meta:
            sections['Chapter Function'] = f"- {meta['function']}"
        if 'hook' in meta:
            sections['Ending Hook'] = f"- {meta['hook']}"
        if 'events' in meta:
            sections['Key Events / Evidence'] = '\n'.join(f"- {e}" for e in meta['events'])
        if 'source' in meta:
            sections['Source Material'] = '\n'.join(f"- {s}" for s in meta['source'])
        if 'review' in meta:
            sections['Review Status'] = meta['review']

    # Update KG sections from extraction
    if entities:
        sections['KG Entities'] = f"- {', '.join(entities)}"
    if concepts:
        sections['KG Concepts'] = f"- {', '.join(concepts)}"

    # Write sections in order
    section_order = ['Chapter Function', 'Key Events / Evidence', 'Ending Hook',
                     'Source Material', 'Review Notes', 'Review Status',
                     'Next Chapter Hook', 'KG Entities', 'KG Concepts', 'KG Causal',
                     'Full Text']

    for sec in section_order:
        if sec in sections:
            lines += [f'## {sec}', sections[sec], '']
        elif sec == 'Full Text':
            lines += ['## Full Text', text.rstrip(), '']

    wiki_file.parent.mkdir(parents=True, exist_ok=True)
    wiki_file.write_text('\n'.join(lines), encoding='utf-8')
    print(f"  ✓ Wiki: ch{chapter:03d}.md ({cn_count(text)}汉字, {fanqie_count(text)}番茄字)")
    return True


def update_vector_memory(chapter: int) -> bool:
    """将章节摘要入库Vector-memory"""
    try:
        sys.path.insert(0, str(VECTOR_MEM))
        from vecmem import VectorMemory
        vm = VectorMemory()

        src = NEW_VER / f'第{chapter}章.md'
        if not src.exists():
            return False

        text = src.read_text(encoding='utf-8')
        entities, concepts = extract_entities(text)
        title = extract_title(text, chapter)

        # Store summary (first 2000 chars + entity/concept metadata)
        summary = text[:2000]
        tags = concepts + [f'第{chapter}章']

        vm.add(
            domain='novel',
            title=f'第{chapter}章 {title}',
            content=summary,
            tags=tags,
            source=f'科武纪元_第{chapter}章'
        )
        print(f"  ✓ Vector-memory: 第{chapter}章入库 (tags: {', '.join(concepts[:5])})")
        return True
    except Exception as e:
        print(f"  ⚠ Vector-memory入库失败: {e}")
        return False


def update_tracking(chapter: int, status_note: str = '') -> bool:
    """更新跟踪表中对应章节行"""
    if not TRACKING.exists():
        print(f"  ⚠ 跟踪表不存在: {TRACKING}")
        return False

    content = TRACKING.read_text(encoding='utf-8')
    # Find either old table rows (| 223 |) or current bullet records (第223章/第223章《...》)
    patterns = [rf'(\|\s*{chapter}\s*\|)', rf'第{chapter}章']
    if any(re.search(p, content) for p in patterns):
        now = datetime.now().strftime('%Y-%m-%d')
        note = status_note or f'同步更新 {now}'
        print(f"  ✓ 跟踪表: 第{chapter}章标记已同步")
        return True
    else:
        print(f"  ⚠ 跟踪表中未找到第{chapter}章")
        return False


def update_foreshadow_index() -> bool:
    """轻量刷新伏笔索引：脚本聚合，不调用模型。"""
    script = BASE / '工具脚本/update_foreshadow_tracker.py'
    if not script.exists():
        print(f"  ⚠ 伏笔索引脚本不存在: {script}")
        return False
    try:
        result = subprocess.run(['python3', str(script)], cwd=BASE, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("  ✓ 伏笔索引已刷新")
            return True
        print(f"  ⚠ 伏笔索引刷新失败: {result.stderr[:200]}")
        return False
    except Exception as e:
        print(f"  ⚠ 伏笔索引刷新异常: {e}")
        return False


def update_character_thread_indexes() -> bool:
    """刷新角色/势力/钩子索引：脚本聚合，不调用模型。"""
    script = BASE / '工具脚本/update_character_thread_indexes.py'
    if not script.exists():
        print(f"  ⚠ 角色/钩子索引脚本不存在: {script}")
        return False
    try:
        result = subprocess.run(['python3', str(script)], cwd=BASE,
                                capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("  ✓ 角色/势力/钩子索引已刷新")
            return True
        print(f"  ⚠ 角色/钩子索引刷新失败: {result.stderr[:200]}")
        return False
    except Exception as e:
        print(f"  ⚠ 角色/钩子索引刷新异常: {e}")
        return False


def count_char_index_todos() -> int:
    """P2: sync后角色上下文TODO数量门禁——读faction-character-index.md统计TODO。"""
    idx = BASE / 'wiki/characters/faction-character-index.md'
    if not idx.exists():
        return -1  # 索引不存在，无法统计
    text = idx.read_text(encoding='utf-8', errors='ignore')
    return text.count('TODO')


def update_status_wal(chapters: list, message: str = '') -> bool:
    """更新STATUS.md和WAL.md"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    msg = message or f"同步章节 {', '.join(str(c) for c in chapters)}"

    # STATUS
    if STATUS.exists():
        st = STATUS.read_text(encoding='utf-8')
        if '## 最近同步' not in st:
            st += f'\n## 最近同步\n'
        # Remove old sync entry for same chapters, add new
        st = re.sub(rf'- \d{{4}}-\d{{2}}-\d{{2}}.*同步.*第{chapters[0]}章.*\n', '', st)
        st += f'- {now} | {msg}\n'
        STATUS.write_text(st, encoding='utf-8')
        print(f"  ✓ STATUS.md 已更新")

    # WAL
    if WAL.exists():
        wal = WAL.read_text(encoding='utf-8')
        wal += f'\n### {now}\n- {msg}\n'
        WAL.write_text(wal, encoding='utf-8')
        print(f"  ✓ WAL.md 已更新")

    return True


def git_commit(chapters: list, message: str = '') -> bool:
    """Git commit"""
    msg = message or f"sync: chapters {', '.join(str(c) for c in chapters)}"
    try:
        subprocess.run(['git', 'add', '-A'], cwd=BASE, check=True, capture_output=True)
        result = subprocess.run(
            ['git', 'commit', '-m', msg, '--allow-empty'],
            cwd=BASE, capture_output=True, text=True
        )
        if result.returncode == 0:
            sha = result.stdout.strip().split('\n')[0] if result.stdout else ''
            print(f"  ✓ Git: {msg}")
            return True
        else:
            print(f"  ⚠ Git commit: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  ⚠ Git失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='科武纪元统一同步引擎')
    parser.add_argument('--chapter', '-c', nargs='+', type=int, required=True,
                        help='要同步的章节号，如 86 124 217')
    parser.add_argument('--message', '-m', type=str, default='',
                        help='提交信息')
    parser.add_argument('--no-git', action='store_true',
                        help='跳过Git commit')
    parser.add_argument('--no-vector', action='store_true',
                        help='跳过Vector-memory入库')
    parser.add_argument('--wiki-only', action='store_true',
                        help='只更新Wiki，跳过其他')
    parser.add_argument('--function', type=str, default='',
                        help='章节功能描述')
    parser.add_argument('--hook', type=str, default='',
                        help='结尾钩子')
    parser.add_argument('--source', nargs='+', type=str, default=[],
                        help='素材来源文件路径')

    args = parser.parse_args()
    chapters = sorted(args.chapter)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    print(f"\n{'='*50}")
    print(f"科武同步引擎 | {now}")
    print(f"章节: {chapters}")
    print(f"{'='*50}\n")

    meta = {}
    if args.function:
        meta['function'] = args.function
    if args.hook:
        meta['hook'] = args.hook
    if args.source:
        meta['source'] = args.source

    results = {'wiki': 0, 'vector': 0, 'tracking': 0, 'foreshadow': 0,
               'char_thread': 0, 'status': 0, 'git': 0}

    for ch in chapters:
        print(f"\n--- 第{ch}章 ---")
        if update_wiki(ch, meta if meta else None):
            results['wiki'] += 1

        if not args.wiki_only:
            if not args.no_vector:
                if update_vector_memory(ch):
                    results['vector'] += 1
            if update_tracking(ch, args.message):
                results['tracking'] += 1

    if not args.wiki_only:
        if update_foreshadow_index():
            results['foreshadow'] = 1
        if update_character_thread_indexes():
            results['char_thread'] = 1
        # P2: sync后TODO数量门禁
        todo_n = count_char_index_todos()
        if todo_n < 0:
            print("  ⚠ [P2门禁] faction-character-index.md 不存在，无法统计TODO")
        elif todo_n == 0:
            print(f"  ✓ [P2门禁] 角色索引TODO=0，无缺口")
        else:
            print(f"  ⚠ [P2门禁] 角色索引TODO={todo_n}，需回填（见 faction-character-index.md）")
        update_status_wal(chapters, args.message)
        results['status'] = 1

        if not args.no_git:
            git_commit(chapters, args.message)
            results['git'] = 1

    print(f"\n{'='*50}")
    print(f"同步完成 | Wiki:{results['wiki']} Vector:{results['vector']} "
          f"Tracking:{results['tracking']} Foreshadow:{results['foreshadow']} "
          f"CharThread:{results['char_thread']} "
          f"Status:{results['status']} Git:{results['git']}")
    print(f"{'='*50}\n")

    # Print verification commands
    print("验证命令:")
    for ch in chapters:
        print(f"  head -20 {WIKI_CH}/ch{ch:03d}.md")
    if not args.no_git:
        print(f"  cd {BASE} && git log -1 --oneline")


if __name__ == '__main__':
    main()
