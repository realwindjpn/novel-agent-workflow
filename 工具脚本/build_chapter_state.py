#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
科武纪元·章节状态卡生成器  build_chapter_state.py

产出 wiki/chapters/state/chNNN.json —— 给任务包（G3/G4/审席）用的结构化上下文。

设计原则（kewu-close-loop 技能硬约束）：
- 只保存**可回源**的事实；未知写 null / "PENDING"，**不许臆造**。
- 正文 SHA 改变后必须重建；旧卡不可作为验收依据。
- 提取走确定性规则（正文 grep + 既有 wiki 索引），不用模型猜。

用法:
    python3 工具脚本/build_chapter_state.py --chapter 368
    python3 工具脚本/build_chapter_state.py --chapter 357 358 359
    python3 工具脚本/build_chapter_state.py --range 357 368
    python3 工具脚本/build_chapter_state.py --chapter 368 --dry   # 只打印不落盘
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
NEW = BASE / '新版'
PUB = BASE / '已投稿'
WIKI_CH = BASE / 'wiki' / 'chapters'
STATE_DIR = WIKI_CH / 'state'
OUTLINE_CANON = ('任务运行态/20261003_kewu_selfcycle_daily/output/'
                 '科武纪元大纲V9_500章_重建稿_G2备注版.md')

SCHEMA = 'kewu.chapter-state.v1'


# ---------- 确定性提取 ----------

def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def net_cjk(t: str) -> int:
    return len(re.findall(r'[\u4e00-\u9fff]', t))


def parse_title(body: str):
    """首行『第N章 标题』→ 标题"""
    first = body.strip().split('\n')[0]
    m = re.match(r'^\s*第\d+章\s*(.*)$', first)
    return (m.group(1).strip() if m else first.strip())[:40] or None


# 主要角色名（未在 wiki/characters/ 建页的兜底名单，取自正文既成口径）
EXTRA_NAMES = ['林星辰', '方宁', '韩铮', '谢云', '陈若水', '周棠', '苏雨晴',
               '陈思琪', '老赵', '赵刚', '李梦瑶']


def load_char_names() -> list:
    """wiki/characters/ 的 .md 名 + 兜底名单，去重"""
    d = BASE / 'wiki' / 'characters'
    names = set(EXTRA_NAMES)
    if d.exists():
        names |= {p.stem for p in d.glob('*.md')}
    return sorted(names)


def extract_characters(body: str, names: list) -> list:
    """确定性：角色名在正文中出现即收录，附出现次数。

    先按名单匹配；长名优先（避免「赵刚」被「老赵」漏掉的反向问题由 count 自然处理）。
    """
    hits = []
    for n in sorted(names, key=len, reverse=True):
        c = body.count(n)
        if c > 0:
            hits.append({'name': n, 'mentions': c})
    hits.sort(key=lambda x: -x['mentions'])
    return hits


AUTHOR_NOTE_RE = re.compile(r'^\s*作者有话说\s*[:：]?\s*$')


def strip_tail(body: str) -> str:
    """剥掉文末『（本章完）』『作者有话说：...』——那不是正文钩子。"""
    lines = body.strip().split('\n')
    # 从后往前找到「作者有话说」标记行，截掉它及其后全部
    for i in range(len(lines) - 1, -1, -1):
        if AUTHOR_NOTE_RE.match(lines[i]):
            return '\n'.join(lines[:i])
    return body.strip()


def extract_ending_hook(body: str, max_chars: int = 260):
    """结尾钩子：正文末段末句（剥离作者有话说/本章完）。

    正文是不分行的长段落，按行取会抓到整段；改为按句号断句，
    从末尾回取到 max_chars 为止，保证钩子是「结尾」而非「整章」。
    """
    body = strip_tail(body).strip()
    body = re.sub(r'[（(]本章完[)）]\s*$', '', body).strip()
    if not body:
        return None
    # 取最后一个句号/叹号/问号作为句终点
    last = max(body.rfind('。'), body.rfind('！'), body.rfind('？'),
               body.rfind('”'), body.rfind('"'))
    if last == -1:
        return body[-max_chars:]
    # 从该句终点往前找句子起点，凑够 max_chars
    start = last + 1
    for m in re.finditer(r'[。！？]', body[:last]):
        if last - m.end() <= max_chars:
            start_candidate = m.end()
            if last - start_candidate <= max_chars:
                start = start_candidate
    return body[start:last + 1].strip() or body[-max_chars:]


def extract_opening(body: str, n_lines: int = 3):
    """开篇：正文前 N 个非空行（跳过章号标题行）"""
    lines = [l.strip() for l in body.strip().split('\n') if l.strip()]
    if lines and re.match(r'^\s*第\d+章', lines[0]):
        lines = lines[1:]
    return '\n'.join(lines[:n_lines]) or None


def load_outline_row(n: int) -> dict:
    """从 V9 准绳大纲取该章行：卷/标题/情节/暗线/字数"""
    p = BASE / OUTLINE_CANON
    if not p.exists():
        return {}
    for line in p.read_text(encoding='utf-8').split('\n'):
        if re.match(r'^\|\s*%d\s*\|' % n, line):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cells) >= 6:
                return {
                    'volume': cells[1] or None,
                    'title': cells[2] or None,
                    'plot': cells[3] or None,
                    'subtext': cells[4] or None,
                    'target_cjk': int(cells[5]) if cells[5].isdigit() else None,
                }
    return {}


def detect_status(n: int, src: Path) -> tuple:
    """发布态判定：新版正文是已投稿 TXT 的前缀（TXT 带『作者有话说』尾）"""
    pub = PUB / f'第{n}章.txt'
    if not pub.exists():
        return 'DRAFT_SAVED_NOT_PUBLISHED', None, None
    body = src.read_text(encoding='utf-8').rstrip()
    ptxt = pub.read_text(encoding='utf-8')
    if body in ptxt:
        dt = datetime.fromtimestamp(pub.stat().st_mtime).strftime('%Y-%m-%d')
        return 'PUBLISHED', dt, str(pub)
    return 'DRAFT_SAVED_NOT_PUBLISHED', None, None


def grep_index(keyword, index_file: Path, max_hits: int = 6) -> list:
    """从 wiki 索引文件里 grep 含本章号的条目。

    兼容多种写法：第N章 / chNNN / | N |（表格行）/ 裸章号。
    索引文件本身可能滞后（不含新章），此时返回空列表 —— 属实情，不臆造。
    """
    if not index_file.exists():
        return []
    pats = [
        re.compile(r'第%d章' % keyword),
        re.compile(r'ch%03d' % keyword, re.I),
        re.compile(r'\|\s*%d\s*\|' % keyword),
        re.compile(r'(?<![\d])%d(?![\d])' % keyword),
    ]
    out = []
    for line in index_file.read_text(encoding='utf-8').split('\n'):
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        if any(p.search(s) for p in pats):
            out.append(s[:200])
        if len(out) >= max_hits:
            break
    return out


# ---------- 主构建 ----------

def build(n: int, allow_planned: bool = False) -> dict:
    """建卡。

    allow_planned=True 时，无正文也建卡（状态 PLANNED）——新章起点必需，
    否则 chapter_state_machine 会一直 BLOCKED，无法开工。
    """
    src = NEW / f'第{n}章.md'
    if not src.exists():
        if not allow_planned:
            return {'chapter': n, 'error': 'SOURCE_NOT_FOUND', 'path': str(src)}
        return build_planned(n)

    body = src.read_text(encoding='utf-8')
    sha = sha256_file(src)
    status, pub_date, pub_path = detect_status(n, src)
    outline = load_outline_row(n)
    wiki_path = WIKI_CH / f'ch{n:03d}.md'

    card = {
        'schema_version': SCHEMA,
        'generated_at': datetime.now().astimezone().isoformat(timespec='seconds'),
        'chapter': n,
        'title': parse_title(body),
        'volume': outline.get('volume'),

        # --- 正文指纹（SHA 变则卡失效）---
        'body': {
            'path': str(src),
            'sha256': sha,
            'net_cjk': net_cjk(body),
        },

        # --- 状态 ---
        'status': {
            'production': status,
            # 状态机门禁字段：PUBLISHED 为终态，editable=false 即禁止改稿
            'editable': status != 'PUBLISHED',
            'state_machine': 'PUBLISHED 为终态；改稿须先 --force-unpublish 降级',
            'published_at': pub_date,
            'submitted_path': pub_path,
            'wiki_synced': wiki_path.exists(),
            'review': None,          # 无机器证据时不填，禁臆造
        },

        # --- 前后章接口（给下一章衔接）---
        'interface': {
            'prev_chapter': n - 1 if n > 1 else None,
            'next_chapter': n + 1,
            'opening': extract_opening(body),
            'ending_hook': extract_ending_hook(body),
        },

        # --- 内容要素（确定性提取）---
        'content': {
            'characters': extract_characters(body, load_char_names()),
            'outline_plot': outline.get('plot'),
            'outline_subtext': outline.get('subtext'),
            'outline_target_cjk': outline.get('target_cjk'),
        },

        # --- 伏笔/钩子索引回链（可能为空）---
        'threads': {
            'foreshadowing': grep_index(n, BASE / 'wiki' / 'plot-threads' / 'foreshadowing-index.md'),
            'ending_hooks': grep_index(n, BASE / 'wiki' / 'plot-threads' / 'ending-hooks-index.md'),
        },

        # --- 大纲绑定（准绳）---
        'outline_binding': {
            'version': 'V9_G2备注版',
            'path': str(BASE / OUTLINE_CANON),
            'sha256': sha256_file(BASE / OUTLINE_CANON) if (BASE / OUTLINE_CANON).exists() else None,
        },
    }
    return card


def build_planned(n: int) -> dict:
    """无正文建卡：状态 PLANNED，内容要素取自 V9 大纲，正文字段留 null。"""
    outline = load_outline_row(n)
    return {
        'schema_version': SCHEMA,
        'generated_at': datetime.now().astimezone().isoformat(timespec='seconds'),
        'chapter': n,
        'title': outline.get('title'),
        'volume': outline.get('volume'),
        'body': {'path': None, 'sha256': None, 'net_cjk': None},
        'status': {
            'production': 'PLANNED',
            'editable': True,
            'state_machine': '新章起点，无正文；写稿后重建状态卡',
            'published_at': None,
            'submitted_path': None,
            'wiki_synced': False,
            'review': None,
        },
        'interface': {
            'prev_chapter': n - 1 if n > 1 else None,
            'next_chapter': n + 1,
            'opening': None,
            'ending_hook': None,
        },
        'content': {
            'characters': [],
            'outline_plot': outline.get('plot'),
            'outline_subtext': outline.get('subtext'),
            'outline_target_cjk': outline.get('target_cjk'),
        },
        'threads': {'foreshadowing': [], 'ending_hooks': []},
        'outline_binding': {
            'version': 'V9_G2备注版',
            'path': str(BASE / OUTLINE_CANON),
            'sha256': sha256_file(BASE / OUTLINE_CANON) if (BASE / OUTLINE_CANON).exists() else None,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapter', '-c', nargs='+', type=int)
    ap.add_argument('--range', nargs=2, type=int, metavar=('START', 'END'))
    ap.add_argument('--dry', action='store_true', help='只打印不落盘')
    ap.add_argument('--allow-planned', action='store_true',
                    help='无正文也建卡（状态 PLANNED，新章起点）')
    a = ap.parse_args()

    chapters = a.chapter or []
    if a.range:
        chapters += list(range(a.range[0], a.range[1] + 1))
    chapters = sorted(set(chapters))
    if not chapters:
        ap.error('需 --chapter 或 --range')

    if not a.dry:
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    ok = err = 0
    for n in chapters:
        card = build(n, allow_planned=a.allow_planned)
        if card.get('error'):
            print(f'第{n}章: {card["error"]}')
            err += 1
            continue
        out = STATE_DIR / f'ch{n:03d}.json'
        if not a.dry:
            out.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding='utf-8')
        c = card['content']
        print(f'第{n}章 | {card["title"]} | CJK {card["body"]["net_cjk"]} | '
              f'{card["status"]["production"]} | 角色 {len(c["characters"])} | '
              f'伏笔 {len(card["threads"]["foreshadowing"])} | '
              f'钩子 {len(card["threads"]["ending_hooks"])}'
              + (' [DRY]' if a.dry else ''))
        ok += 1

    print(f'\n生成 {ok} 张，失败 {err} 张')
    if not a.dry and ok:
        print('输出目录:', STATE_DIR)


if __name__ == '__main__':
    sys.exit(main())
