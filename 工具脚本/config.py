#!/usr/bin/env python3
"""Project configuration for novel agent workflow scripts.

All paths are resolved relative to PROJECT_DIR which can be set via:
1. --project-dir CLI argument (preferred)
2. PROJECT_DIR environment variable
3. Default: /root/workspace/科武纪元

Usage:
    from config import ProjectConfig
    cfg = ProjectConfig(project_dir="/path/to/project")
    print(cfg.base, cfg.new_dir, cfg.outline)
"""
import argparse
import os
from pathlib import Path


DEFAULT_PROJECT_DIR = os.environ.get(
    'PROJECT_DIR',
    '/root/workspace/科武纪元'
)


class ProjectConfig:
    """Centralized project paths and settings."""

    def __init__(self, project_dir: str = None):
        self.base = Path(project_dir or DEFAULT_PROJECT_DIR)
        # Core directories
        self.new_dir = self.base / '新版'
        self.submitted_dir = self.base / '已投稿'
        self.draft_dir = self.base / '待确认投稿'
        self.kb_dir = self.base / '知识库'
        self.wiki_dir = self.base / 'wiki'
        self.review_dir = self.base / '审核记录'
        self.tools_dir = self.base / '工具脚本'
        self.rag_dir = self.base / 'rag_kb' / 'science'
        self.outline = self.base / '科武纪元大纲 V8_完整版.md'

        # Sub-directories under review
        self.evidence_dir = self.review_dir / '证据包'
        self.task_dir = self.review_dir / '任务卡'
        self.memory_dir = self.review_dir / '章节记忆卡'
        self.wal_dir = self.review_dir / 'WAL'
        self.context_dir = self.review_dir / '上下文包'
        self.review_record_dir = self.review_dir / '六角色外审'
        self.raw_dir = self.review_record_dir / 'raw'

        # RAG paths
        self.rag_cards = self.rag_dir / 'cards' / 'science_cards.jsonl'
        self.rag_index = self.rag_dir / 'index' / 'semantic_vectors.npy'

    def chapter_file(self, ch: int, submitted: bool = False) -> Path:
        """Get chapter file path. Prefers MD, falls back to TXT."""
        md = self.new_dir / f'第{ch}章.md'
        if md.exists():
            return md
        txt = self.submitted_dir / f'第{ch}章.txt'
        if txt.exists():
            return txt
        return md

    def draft_file(self, ch: int) -> Path:
        return self.draft_dir / f'第{ch}章改.txt'

    def wiki_chapter(self, ch: int) -> Path:
        return self.wiki_dir / 'chapters' / f'ch{ch:03d}.md'

    def evidence_file(self, ch: int) -> Path:
        return self.evidence_dir / f'第{ch}章_证据包.md'

    def task_card(self, ch: int) -> Path:
        return self.task_dir / f'第{ch}章.md'

    def memory_card(self, ch: int) -> Path:
        return self.memory_dir / f'第{ch}章.md'

    def review_file(self, ch: int) -> Path:
        return self.review_record_dir / f'第{ch}章.md'

    def context_file(self, ch: int) -> Path:
        return self.context_dir / f'第{ch:03d}章_context.md'

    def raw_review(self, ch: int, role: str, suffix: str) -> Path:
        return self.raw_dir / f'第{ch}_{role}_{suffix}.json'


def add_project_arg(parser: argparse.ArgumentParser) -> None:
    """Add --project-dir argument to an ArgumentParser."""
    parser.add_argument(
        '--project-dir',
        default=DEFAULT_PROJECT_DIR,
        help='Path to novel project directory (default: %(default)s)'
    )


def get_config(args: argparse.Namespace = None) -> ProjectConfig:
    """Get ProjectConfig from parsed args or environment."""
    if args and hasattr(args, 'project_dir'):
        return ProjectConfig(args.project_dir)
    return ProjectConfig()
