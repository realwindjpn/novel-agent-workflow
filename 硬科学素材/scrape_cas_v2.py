#!/usr/bin/env python3
"""Scrape cas.cn article content with improved extraction."""
import requests, json, re, time
from pathlib import Path

BASE = Path("/workspace/科武纪元/硬科学素材/中科院官网")

# Read the new articles list
cards = []
with open(BASE / "cas_articles_new_20260426.jsonl") as f:
    for line in f:
        cards.append(json.loads(line.strip()))

# Re-fetch each article with better content extraction
for card in cards:
    print("Re-fetching: %s" % card["title"][:50])
    try:
        resp = requests.get(card["url"],
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=15)
        resp.encoding = 'utf-8'
        html = resp.text
        
        # Strategy 1: Find the article body div
        # CAS articles typically have content in a specific div
        patterns = [
            r'<div class="TRS_Editor"[^>]*>(.*?)</div>\s*<!--',
            r'<div class="TRS_Editor"[^>]*>(.*?)</div>\s*<div',
            r'<div id="zoom"[^>]*>(.*?)</div>',
            r'<div class="article-content"[^>]*>(.*?)</div>',
            r'<div class="content"[^>]*>(.*?)</div>',
        ]
        
        content = None
        for pat in patterns:
            m = re.search(pat, html, re.DOTALL)
            if m:
                content = m.group(1)
                break
        
        if not content:
            # Strategy 2: Find content between known markers
            # Look for first real paragraph after title/author/date
            body_start = re.search(r'<div class="TRS_Editor">', html, re.DOTALL)
            if body_start:
                # Get everything from TRS_Editor to the next div or end
                rest = html[body_start.end():]
                # Find end of content (next major div or footer)
                end_markers = [
                    '<!--', '</div>', '<div class="page"', 
                    '<div class="related"', '<script'
                ]
                end_pos = len(rest)
                for marker in end_markers:
                    pos = rest.find(marker)
                    if pos > 100 and pos < end_pos:
                        end_pos = pos
                content = rest[:end_pos]
        
        if content:
            # Clean HTML tags
            text = re.sub(r'<[^>]+>', '\n', content)
            # Clean whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            # Remove header noise (职责, 方针 etc.)
            filtered = []
            skip = True
            for line in lines:
                if len(line) > 20 and ('主要职责' not in line and '贯彻落实' not in line):
                    skip = False
                if not skip:
                    filtered.append(line)
            text = '\n'.join(filtered)
            
            if len(text) > 200:
                card["content"] = text[:2000]
                print("  Extracted %d chars" % len(text))
                print("  Preview: %s" % text[:80])
            else:
                print("  Content too short after filtering (%d)" % len(text))
        else:
            print("  No content found")
        time.sleep(0.5)
    except Exception as e:
        print("  Error: %s" % e)

# Save updated cards
with open(BASE / "cas_articles_new_20260426.jsonl", "w", encoding="utf-8") as f:
    for c in cards:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print("\nDone. Updated %d cards" % len(cards))
