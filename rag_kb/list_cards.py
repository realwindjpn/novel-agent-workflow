#!/usr/bin/env python3
"""Generate RAG knowledge base inventory."""
import json
from pathlib import Path

CARDS_PATH = Path("/workspace/科武纪元/rag_kb/science/cards/science_cards.jsonl")

cards = []
with open(CARDS_PATH) as f:
    for line in f:
        cards.append(json.loads(line.strip()))

trusted = [c for c in cards if c["trust"] in ("A", "B")]

# Group by source
by_source = {}
for c in trusted:
    src = c["source"]
    if src not in by_source:
        by_source[src] = []
    by_source[src].append(c)

lines = ["# 科武纪元 RAG 知识库索引\n"]
lines.append(f"总计 {len(cards)} 条素材，可信 {len(trusted)} 条（A/B），噪声 {len(cards)-len(trusted)} 条（C/D）\n")

for src, items in sorted(by_source.items()):
    lines.append(f"\n## {src} ({len(items)}条)")
    for c in items:
        domains = ", ".join(d for d in c.get("domains", []) if d)
        title = c["title"]
        if len(title) > 80:
            title = title[:77] + "..."
        lines.append(f"- [{c['trust']}] `{c['id']}` {title}")
        if domains:
            lines.append(f"  - 领域: {domains}")

# Domain summary
print('\n'.join(lines))
