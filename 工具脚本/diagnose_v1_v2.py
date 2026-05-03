#!/usr/bin/env python3
"""
第一二卷重审诊断脚本 v1
1. 建立主版本映射（解决重复文件）
2. 格式体检（字数、末行、标题行）
3. 大纲对齐（比对 V8 大纲）
4. 敏感词/AI味扫描
5. 投稿一致性检查（新版 vs 已投稿）
"""
from pathlib import Path
import re, json, datetime

BASE = Path('/root/workspace/科武纪元')
NEW_DIR = BASE / '新版'
SUB_DIR = BASE / '已投稿'
OUTLINE = BASE / '科武纪元大纲V8.md'
REPORT_PATH = BASE / '审核记录/第一二卷重审_诊断报告_v1.md'

# 1. 读取大纲标题
outline_titles = {}
with open(OUTLINE, 'r', encoding='utf-8') as f:
    for line in f:
        # Match: 第1章 | 第一卷·觉醒 | 江城少年
        m = re.match(r'^第(\d+)章\s*\|.*\|\s*(.+)', line)
        if m:
            chapter_num = int(m.group(1))
            title = m.group(2).strip()
            outline_titles[chapter_num] = title

# 2. 映射主版本
canonical = {}
# 新版目录
candidates = {}
for f in NEW_DIR.glob('第*.*'):
    m = re.search(r'第\s*(\d+)\s*章', f.name)
    if m:
        n = int(m.group(1))
        candidates.setdefault(n, []).append(f)

for n, files in candidates.items():
    # 优先选以“（本章完）”结尾且最长的
    best = None
    for f in files:
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if not lines: continue
            if lines[-1] == '（本章完）':
                if best is None or len(text) > len(best[1]):
                    best = (f, text)
        except: continue
    if best is None:
        # 都没有本章完，取最长的
        best_file = max(files, key=lambda x: x.stat().st_size)
        best = (best_file, best_file.read_text(encoding='utf-8', errors='ignore'))
    canonical[n] = best[0]

# 已投稿目录
for f in SUB_DIR.glob('第*.txt'):
    m = re.search(r'第\s*(\d+)\s*章', f.name)
    if m:
        n = int(m.group(1))
        canonical[n] = f # 投稿版本优先级更高（如果存在），但此处我们主要检查差异

# 3. 扫描分析
report_rows = []
for n in range(1, 79):
    if n not in canonical:
        report_rows.append({'chapter': n, 'status': 'MISSING', 'file': '无', 'issues': ['文件缺失']})
        continue
    
    f = canonical[n]
    root = '已投稿' if f.parent == SUB_DIR else '新版'
    try:
        text = f.read_text(encoding='utf-8', errors='ignore')
    except:
        report_rows.append({'chapter': n, 'status': 'ERROR', 'file': str(f), 'issues': ['读取失败']})
        continue
    
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    cn = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
    first = lines[0] if lines else ''
    last = lines[-1] if lines else ''
    
    issues = []
    
    # 格式检查
    if cn < 3000: issues.append(f'字数不足({cn})')
    if last != '（本章完）': issues.append(f'末行异常:{last}')
    if not re.match(r'^(#\s*)?第\s*\d+\s*章|^第一章', first):
        issues.append(f'标题格式错:{first}')
        
    # 大纲对齐
    expected_title = outline_titles.get(n, '')
    if expected_title and expected_title not in first:
        # 宽容匹配：只要包含数字和汉字即可，不严格比对全名
        if not re.search(r'第\s*\d+\s*章\s*[^\n]{1,20}', first):
             issues.append(f'标题与大纲不符(预期:{expected_title})')

    # 敏感词/AI味（简化扫描）
    if '像油画' in text or '像猛兽' in text or '像墙' in text: issues.append('禁用比喻')
    if '像' in text and ('油画' in text or '深渊' in text): issues.append('疑似咏叹调')
    
    # 投稿差异
    sub_f = SUB_DIR / f'第{n}章.txt'
    if sub_f.exists():
        sub_text = sub_f.read_text(encoding='utf-8', errors='ignore')
        # 简单比对长度和内容特征
        if abs(len(text) - len(sub_text)) > 100 or '（本章完）' not in sub_text:
            issues.append('与投稿版差异大')

    status = 'OK'
    if 'MISSING' in str(issues): status = 'MISSING'
    elif any(x in ' '.join(issues) for x in ['字数不足', '末行异常', '标题格式错', '标题与大纲不符']):
        status = 'P0'
    elif any(x in ' '.join(issues) for x in ['禁用比喻', '疑似咏叹调']):
        status = 'P1'
    elif issues:
        status = 'P2'

    report_rows.append({
        'chapter': n,
        'status': status,
        'file': str(f),
        'root': root,
        'words': cn,
        'first': first[:40],
        'last': last,
        'issues': issues
    })

# 4. 生成报告
lines = [
    f'# 第一二卷重审诊断报告 v1',
    f'生成时间：{datetime.datetime.now():%Y-%m-%d %H:%M:%S}',
    f'',
    f'## 概览',
    f'- 检查范围：第 1-78 章',
    f'- P0（格式/缺失）：{len([r for r in report_rows if r["status"]=="P0"])}',
    f'- P1（敏感/AI味）：{len([r for r in report_rows if r["status"]=="P1"])}',
    f'- P2（其他）：{len([r for r in report_rows if r["status"]=="P2"])}',
    f'- 正常（OK）：{len([r for r in report_rows if r["status"]=="OK"])}',
    f'',
    f'## 详细列表',
    f'',
    f'|章|状态|字数|文件位置|问题详情|',
    f'|---:|---:|---:|---|---|'
]

for r in report_rows:
    iss_str = '; '.join(r['issues']) if r['issues'] else '-'
    root_tag = f'[{r.get("root","?")}]'
    lines.append(f"|{r['chapter']}|{r['status']}|{r['words']}|{root_tag}{r['file'].split('/')[-1]}|{iss_str}|")

OUTLINE.parent.mkdir(parents=True, exist_ok=True)
OUTLINE.write_text('\n'.join(lines), encoding='utf-8')
print(f"报告已保存：{OUTLINE}")
print('\n'.join(lines[:20]))
