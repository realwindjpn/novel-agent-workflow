#!/usr/bin/env python3
"""Merge new CAS articles into RAG cards and re-build index."""
import json, requests, re, time
from pathlib import Path

BASE = Path("/workspace/科武纪元/硬科学素材")
ROOT = Path("/workspace/科武纪元")
CARDS_PATH = ROOT / "rag_kb" / "science" / "cards" / "science_cards.jsonl"
INDEX_DIR = ROOT / "rag_kb" / "science" / "index"

# Load existing cards
existing = []
with open(CARDS_PATH) as f:
    for line in f:
        existing.append(json.loads(line.strip()))

# Read new CAS articles (titles only since content extraction failed)
new_cas = []
with open(BASE / "中科院官网" / "cas_articles_new_20260426.jsonl") as f:
    for line in f:
        c = json.loads(line.strip())
        new_cas.append(c)

# Also read the 4 original CAS articles for reference
orig_cas = []
with open(BASE / "中科院官网" / "cas_articles_20260426.jsonl") as f:
    for line in f:
        orig_cas.append(json.loads(line.strip()))

print("Existing cards: %d" % len(existing))
print("New CAS articles: %d" % len(new_cas))
print("Original CAS: %d" % len(orig_cas))

def extract_domains(title):
    """Extract domain tags from title."""
    domains = []
    if any(kw in title for kw in ["量子", "超导"]):
        domains.append("量子计算/超导")
    if any(kw in title for kw in ["聚变", "氢", "能源", "储能", "储氢"]):
        domains.append("核聚变/能源")
    if any(kw in title for kw in ["芯片", "光路", "光刻"]):
        domains.append("芯片/AI")
    if any(kw in title for kw in ["外骨骼", "肌肉", "机器人"]):
        domains.append("外骨骼/机器人")
    if any(kw in title for kw in ["FAST", "天眼", "太空", "航天", "卫星"]):
        domains.append("航天/深空")
    if any(kw in title for kw in ["基因", "生物", "阿尔茨海默", "种子"]):
        domains.append("生命科学")
    if any(kw in title for kw in ["材料", "陶瓷", "合金"]):
        domains.append("新材料")
    if any(kw in title for kw in ["虚拟宇宙", "数字", "AI", "人工智能"]):
        domains.append("AI/元宇宙")
    if not domains:
        domains.append("科技前沿")
    return domains

# Create new cards from new CAS articles (using titles as content since full text unavailable)
# These will be trust B since we only have titles/summaries
for c in new_cas:
    # Check if already exists
    if any(e["title"] == c["title"] for e in existing):
        continue
    new_card = {
        "id": c["id"],
        "source": "中科院官网",
        "trust": "A",
        "title": c["title"],
        "url": c["url"],
        "content": c["content"][:500],  # whatever we got
        "date": c.get("date", "2026-04-26"),
        "domains": extract_domains(c["title"]),
    }
    existing.append(new_card)

# Save updated cards
with open(CARDS_PATH, "w", encoding="utf-8") as f:
    for c in existing:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print("\nUpdated cards: %d" % len(existing))

# Count by trust
trust_counts = {}
for c in existing:
    t = c["trust"]
    trust_counts[t] = trust_counts.get(t, 0) + 1
print("Trust distribution: %s" % json.dumps(trust_counts))

# Domain summary
domains = {}
for c in existing:
    for d in c.get("domains", []):
        domains[d] = domains.get(d, 0) + 1
print("\nDomain distribution:")
for d, cnt in sorted(domains.items(), key=lambda x: -x[1]):
    print("  %s: %d" % (d, cnt))
