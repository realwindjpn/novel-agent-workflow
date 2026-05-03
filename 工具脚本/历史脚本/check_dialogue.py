#!/usr/bin/env python3
"""Verify dialogue detection accuracy for chapters"""
import re
from pathlib import Path

for ch in [78, 89, 90, 92, 95, 96, 97, 100, 101, 102, 104, 105]:
    fp = Path(f'/workspace/科武纪元/新版/第{ch}章.md')
    if not fp.exists():
        continue
    text = fp.read_text(encoding='utf-8')
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    
    # Try multiple quote patterns
    # Pattern 1: straight double quotes
    d1 = re.findall(r'"[^"]{2,}"', text)
    # Pattern 2: Chinese curly quotes 
    d2 = re.findall(r'\u201c[^\u201d]{2,}\u201d', text)  # "..."
    # Pattern 3: Japanese/Chinese corner brackets
    d3 = re.findall(r'\u300c[^\u300d]{2,}\u300d', text)  # 「...」
    # Pattern 4: any of the above combined
    d4 = re.findall(r'[\u201c\u201d\u300c\u300d"][^\u201d\u300d"]{2,}[\u201d\u300d"]', text)
    # Pattern 5: broadest - match Chinese-style quotes "..." and 「...」
    d5 = re.findall(r'["\u201c][^"\u201d\u300c\u300d]{2,}["\u201d]', text)
    
    print(f'第{ch}章 | {cn_chars}字')
    print(f'  直双引号: {len(d1)}处 {sum(len(d) for d in d1)}字')
    print(f'  中文弯引: {len(d2)}处 {sum(len(d) for d in d2)}字')
    print(f'  角括号:   {len(d3)}处 {sum(len(d) for d in d3)}字')
    print(f'  组合宽:   {len(d4)}处 {sum(len(d) for d in d4)}字')
    print(f'  中英混合: {len(d5)}处 {sum(len(d) for d in d5)}字')
    
    # Best ratio
    all_quotes = d1 + d2 + d3
    total_quote_chars = sum(len(d) for d in all_quotes)
    ratio = total_quote_chars / cn_chars * 100 if cn_chars else 0
    print(f'  → 最佳检测: {len(all_quotes)}处 | 对话比例: {ratio:.1f}%')
    
    if all_quotes:
        samples = [q[:40] for q in all_quotes[:3]]
        print(f'  样例: {samples}')
    print()
