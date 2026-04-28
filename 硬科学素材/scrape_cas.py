#!/usr/bin/env python3
"""Scrape latest research from cas.cn for 科武纪元."""
import requests, json, re, time
from pathlib import Path

BASE = Path("/workspace/科武纪元/硬科学素材/中科院官网")
BASE.mkdir(parents=True, exist_ok=True)

KEYWORDS = ["量子", "聚变", "芯片", "AI", "外骨骼", "机器人", "超导", "核聚变", "人造太阳", "FAST", "天眼", "太空", "航天", "能源", "储能", "电池", "材料", "光学", "肌肉", "感知", "基因", "生物", "计算", "算法", "数据", "网络", "通信", "盐穴", "氢", "虚拟宇宙", "阿尔茨海默", "环节动物"]

def is_relevant(title):
    return any(kw in title for kw in KEYWORDS)

# Get research progress page
resp = requests.get("https://www.cas.cn/kyjz/",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
html = resp.text

# Extract links using regex
link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>'
matches = re.findall(link_pattern, html)

relevant = []
for href, text in matches:
    text = text.strip()
    if len(text) > 5 and is_relevant(text):
        if href.startswith("/"):
            href = "https://www.cas.cn" + href
        relevant.append({"title": text, "url": href})
        print("[RELEVANT] " + text[:60])

print("\nFound %d relevant articles from kyjz page" % len(relevant))

# Also check main page
resp2 = requests.get("https://www.cas.cn/",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
html2 = resp2.text
matches2 = re.findall(link_pattern, html2)

for href, text in matches2:
    text = text.strip()
    if len(text) > 8 and is_relevant(text):
        if href.startswith("/"):
            href = "https://www.cas.cn" + href
        title_key = text[:30]
        if not any(title_key == r["title"][:30] for r in relevant):
            relevant.append({"title": text, "url": href})
            print("[MAIN] " + text[:60])

print("\nTotal relevant: %d" % len(relevant))

# Download content
cards = []
for i, article in enumerate(relevant[:8]):
    print("\nDownloading %d: %s" % (i+1, article['title'][:50]))
    try:
        resp3 = requests.get(article['url'],
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=15)
        resp3.encoding = 'utf-8'
        
        # Extract content with regex
        content_match = re.search(r'<div class="TRS_Editor">(.*?)</div>', resp3.text, re.DOTALL)
        if content_match:
            text = re.sub(r'<[^>]+>', '\n', content_match.group(1))
        else:
            paras = re.findall(r'<p[^>]*>(.*?)</p>', resp3.text, re.DOTALL)
            text = '\n'.join(re.sub(r'<[^>]+>', '', p) for p in paras)
        
        text = text.strip()
        if len(text) < 100:
            print("  Too short (%d chars), skipping" % len(text))
            continue
        
        card = {
            "id": "cas_new_%03d" % len(cards),
            "source": "中科院官网",
            "trust": "A",
            "title": article['title'],
            "url": article['url'],
            "content": text[:2000],
            "date": time.strftime("%Y-%m-%d"),
        }
        cards.append(card)
        print("  Saved %d chars" % len(text))
        time.sleep(1)
    except Exception as e:
        print("  Error: %s" % e)

# Save
out_path = BASE / "cas_articles_new_20260426.jsonl"
with open(out_path, "w", encoding="utf-8") as f:
    for c in cards:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print("\nTotal new cards: %d" % len(cards))
print("Saved to: %s" % out_path)

# Save markdown summary
md_path = BASE / "中科院最新科研_20260426.md"
with open(md_path, "w", encoding="utf-8") as f:
    f.write("# 中科院最新科研进展采集\n\n")
    for c in cards:
        f.write("## " + c['title'] + "\n")
        f.write("- 链接: " + c['url'] + "\n")
        f.write("- 内容: " + c['content'][:300] + "...\n\n")
