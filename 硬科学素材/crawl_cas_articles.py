#!/usr/bin/env python3
"""Use crawl4ai-skill to scrape CAS research articles for 科武纪元."""
import re, subprocess, json, time, os
from pathlib import Path

OUT_DIR = Path("/workspace/科武纪元/硬科学素材/中科院官网/new_cas_crawl4ai")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read the crawled homepage
with open("/tmp/cas_kyjz.md") as f:
    content = f.read()

# Keywords for filtering
KEYWORDS = ["量子", "聚变", "芯片", "AI", "外骨骼", "机器人", "超导", "核聚变", "人造太阳", "FAST", "天眼", "太空", "航天", "能源", "储能", "电池", "材料", "光学", "肌肉", "感知", "基因", "生物", "计算", "算法", "数据", "网络", "通信", "盐穴", "氢", "虚拟宇宙", "阿尔茨海默", "环节动物"]

# Extract links
link_pattern = r'\[([^\]]+)\]\(([^)]+?\.shtml)'
matches = re.findall(link_pattern, content)

base = "https://www.cas.cn"
articles = []
for title, url in matches:
    if any(kw in title for kw in KEYWORDS):
        if url.startswith("../../"):
            # Convert relative path to absolute
            url = url.replace("../../syky/", base + "/syky/")
            url = url.replace("../../cg/zh/", base + "/cg/zh/")
        elif url.startswith("/"):
            url = base + url
        elif url.startswith("http"):
            pass
        else:
            continue
        articles.append({"title": title, "url": url})
        print("[MATCH] %s" % title[:50])
        print("  URL: %s" % url)
        print()

print("Total relevant: %d" % len(articles))

# Crawl each article using crawl4ai-skill
cards = []
for i, article in enumerate(articles[:10]):
    print("\n=== Crawling %d/%d: %s ===" % (i+1, len(articles), article["title"][:40]))
    out_file = OUT_DIR / ("article_%03d.md" % i)
    
    cmd = ["crawl4ai-skill", "crawl", article["url"], "--format", "fit_markdown", "-o", str(out_file), "--timeout", "30"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    if out_file.exists() and out_file.stat().st_size > 200:
        text = out_file.read_text(encoding="utf-8")
        # Check if we got meaningful content (not just navigation)
        if len(text) > 300 and "主要职责" not in text[:500]:
            card = {
                "id": "cas_crawl4ai_%03d" % len(cards),
                "source": "中科院官网",
                "trust": "A",
                "title": article["title"],
                "url": article["url"],
                "content": text[:2000],
                "content_len": len(text),
                "date": time.strftime("%Y-%m-%d"),
            }
            cards.append(card)
            print("  OK: %d chars extracted" % len(text))
        else:
            print("  Content too short or navigation noise (%d chars)" % len(text))
    else:
        print("  FAILED: no output or empty file")
    
    time.sleep(2)  # rate limit

# Save results
out_path = OUT_DIR / "cas_crawled_cards.jsonl"
with open(out_path, "w", encoding="utf-8") as f:
    for c in cards:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print("\n=== Summary ===")
print("Successfully crawled: %d articles" % len(cards))
print("Saved to: %s" % out_path)

# Show first article preview
if cards:
    print("\nFirst article preview:")
    print(cards[0]["content"][:500])
