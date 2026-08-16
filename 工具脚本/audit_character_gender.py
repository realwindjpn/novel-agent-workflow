#!/usr/bin/env python3
"""Read-only explicit-gender audit for character knowledge files."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FIELD_PATTERNS = (
    re.compile(r"^(?:gender|sex|性别)\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*\|\s*性别\s*\|\s*([^|]+?)\s*\|\s*$", re.MULTILINE),
    re.compile(r"^\s*[-*]\s*\*\*性别\*\*\s*[：:]\s*(.+?)\s*$", re.MULTILINE),
)


def normalize_gender(value: str) -> str:
    cleaned = value.strip().strip("*`")
    aliases = {"男性": "男", "male": "男", "m": "男", "女性": "女", "female": "女", "f": "女"}
    return aliases.get(cleaned.lower(), cleaned)


def explicit_values(text: str) -> list[str]:
    values: list[str] = []
    for pattern in FIELD_PATTERNS:
        values.extend(normalize_gender(match) for match in pattern.findall(text))
    return sorted(set(values))


def audit(raw_source: Path, character_dir: Path) -> dict:
    pages = []
    character_pages = (page for page in character_dir.glob("*.md") if "index" not in page.stem.lower())
    for page in sorted(character_pages, key=lambda path: path.name):
        values = explicit_values(page.read_text(encoding="utf-8", errors="ignore"))
        pages.append({
            "path": str(page.resolve()),
            "explicit_gender": bool(values),
            "values": values,
            "conflict": len(values) > 1,
        })
    raw_values = explicit_values(raw_source.read_text(encoding="utf-8", errors="ignore"))
    return {
        "policy": "explicit fields only; chapter prose and names are never used to infer gender",
        "raw_source": {
            "path": str(raw_source.resolve()),
            "explicit_gender_field_count": len(raw_values),
            "values": raw_values,
            "missing_explicit_gender_fields": not raw_values,
        },
        "character_pages": pages,
        "summary": {
            "page_count": len(pages),
            "explicit_count": sum(page["explicit_gender"] for page in pages),
            "missing_count": sum(not page["explicit_gender"] for page in pages),
            "conflict_count": sum(page["conflict"] for page in pages),
        },
    }


def render_markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# 人物性别完整性审计",
        "",
        "> 仅检查显式性别字段；不从章节、姓名、称谓或人物描述猜测性别。",
        "",
        "## 汇总",
        f"- 人物页数：{summary['page_count']}",
        f"- 有显式字段：{summary['explicit_count']}",
        f"- 缺项：{summary['missing_count']}",
        f"- 冲突：{summary['conflict_count']}",
        f"- 人物源：{report['raw_source']['path']}",
        f"- 人物源缺显式性别字段：{'是' if report['raw_source']['missing_explicit_gender_fields'] else '否'}",
        "",
        "## 人物页",
        "| 路径 | 显式字段 | 值 | 冲突 |",
        "|---|---|---|---|",
    ]
    for page in report["character_pages"]:
        values = " / ".join(page["values"]) if page["values"] else "缺项"
        lines.append(
            f"| {page['path']} | {'是' if page['explicit_gender'] else '否'} | {values} | {'是' if page['conflict'] else '否'} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="只读人物性别完整性扫描")
    parser.add_argument("--raw", required=True)
    parser.add_argument("--characters", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--md-out", required=True)
    args = parser.parse_args()
    report = audit(Path(args.raw), Path(args.characters))
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
