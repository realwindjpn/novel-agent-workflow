#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import re,json
ROOT=Path('/root/workspace/科武纪元')
DIR=ROOT/'待确认投稿'
REPORT=ROOT/'审核记录'/'第一二卷格式修补'/'revision_candidates_1_52_audit.md'
def cn(s): return len(re.findall(r'[\u4e00-\u9fff]',s))
def ok_title(first,n): return bool(re.match(rf'^第{n}章(\s+\S+)?$', first.strip()))
rows=[]; bad=[]
for n in range(1,53):
    p=DIR/f'第{n}章改.txt'
    text=p.read_text(encoding='utf-8',errors='ignore') if p.exists() else ''
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    first=lines[0] if lines else ''
    last=lines[-1] if lines else ''
    issues=[]
    if not p.exists(): issues.append('缺文件')
    if not ok_title(first,n): issues.append('标题异常')
    if last!='（本章完）': issues.append('末行异常')
    if re.search(r'^\s*\d+\|',text,re.M): issues.append('行号污染')
    if cn(text)<3000: issues.append('字数<3000')
    if issues: bad.append((n,issues))
    rows.append((n,cn(text),first,last,','.join(issues) or 'OK'))
lines=['# 1-52 改版候选复核','','|章|字数|首行|末行|状态|','|---:|---:|---|---|---|']
for r in rows:
    lines.append(f'|{r[0]}|{r[1]}|{r[2][:32]}|{r[3]}|{r[4]}|')
lines += ['','## 统计',f'- 总数：52',f'- 有问题：{len(bad)}',f'- 格式问题：{sum(1 for _,xs in bad if any(x in xs for x in ["标题异常","末行异常","行号污染","缺文件"]))}',f'- 字数不足：{sum(1 for _,xs in bad if "字数<3000" in xs)}']
REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'bad':len(bad),'report':str(REPORT)},ensure_ascii=False))
