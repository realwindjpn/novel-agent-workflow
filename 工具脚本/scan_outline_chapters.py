#!/usr/bin/env python3
"""大纲章节自动扫描：对比大纲 vs 新版 vs 已投稿，分类输出。"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE = Path("/workspace/科武纪元")
OUTLINE_PATH = BASE / "wiki" / "raw" / "outline" / "科武纪元大纲_latest.md"
NEW_DIR = BASE / "新版"
UPLOAD_DIR = BASE / "已投稿"

# 正则：匹配"第N章"或表格行"| N |"
RE_CH_NUM = re.compile(r'第(\d+)章')
RE_TABLE_NUM = re.compile(r'\|\s*(\d{1,3})\s*\|')


def extract_outline_chapters(path: Path) -> set[int]:
    """从大纲提取所有章号。"""
    text = path.read_text(encoding="utf-8")
    nums: set[int] = set()
    for m in RE_CH_NUM.finditer(text):
        nums.add(int(m.group(1)))
    for m in RE_TABLE_NUM.finditer(text):
        n = int(m.group(1))
        # 表格数字行：章号通常 ≥2，过滤掉纯等级/数值行
        if n >= 1:
            nums.add(n)
    return nums


def extract_dir_chapters(d: Path, ext: str) -> set[int]:
    """从目录提取已写/已投稿章号。ext=".md" 或 ".txt"。"""
    nums: set[int] = set()
    if not d.is_dir():
        return nums
    for f in d.iterdir():
        if not f.name.endswith(ext):
            continue
        m = RE_CH_NUM.search(f.name)
        if m:
            nums.add(int(m.group(1)))
    return nums


def main() -> None:
    ap = argparse.ArgumentParser(description="大纲章节自动扫描")
    ap.add_argument("--output", "-o", help="输出JSON文件路径")
    args = ap.parse_args()

    if not OUTLINE_PATH.exists():
        print(f"[ERROR] 大纲不存在: {OUTLINE_PATH}", file=sys.stderr)
        sys.exit(1)

    outline = extract_outline_chapters(OUTLINE_PATH)
    written = extract_dir_chapters(NEW_DIR, ".md")
    uploaded = extract_dir_chapters(UPLOAD_DIR, ".txt")

    needs_write = sorted(outline - written)
    needs_upload = sorted(written - uploaded)
    done = sorted(written & uploaded)

    result = {
        "outline_count": len(outline),
        "written_count": len(written),
        "uploaded_count": len(uploaded),
        "NEEDS_NEW_WRITE": needs_write,
        "NEEDS_UPLOAD": needs_upload,
        "UPLOADED": done,
    }

    # 终端摘要
    print(f"大纲章数: {len(outline)} | 已写: {len(written)} | 已投稿: {len(done)}")
    print(f"  需新写: {len(needs_write)}  需上传: {len(needs_upload)}  已完成: {len(done)}")
    if needs_write:
        print(f"  需新写(前10): {needs_write[:10]}")
    if needs_upload:
        print(f"  需上传(前10): {needs_upload[:10]}")

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON已写: {out}")


if __name__ == "__main__":
    main()
