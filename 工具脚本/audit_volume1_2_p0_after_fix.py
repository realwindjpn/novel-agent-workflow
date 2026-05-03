#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import re, json
ROOT=Path('/root/workspace/科武纪元')
NEW=ROOT/'新版'
OUT=ROOT/'审核记录'/'第一二卷格式修补'/'post_fix_audit.md'

def cn_count(s): return len(re.findall(r'[\u4e00-\u9fff]', s))
def chap(path):
    m=re.search(r'第(\d+)章', path.name)
    return int(m.group(1)) if m else None
def ok_title(line,n): return bool(re.match(rf'^第{n}章(\s+\S+)?$', line.strip()))
issues=[]; rows=[]
for n in range(1,79):
    p=NEW/f'第{n}章.md'
    if not p.exists():
        issues.append((n,'缺文件',str(p))); continue
    text=p.read_text(encoding='utf-8',errors='ignore')
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    first=lines[0] if lines else ''
    last=lines[-1] if lines else ''
    cn=cn_count(text)
    ps=[]
    if not ok_title(first,n): ps.append('标题异常')
    if last!='（本章完）': ps.append('末行异常')
    if re.search(r'^\s*\d+\|', text, re.M): ps.append('行号污染')
    if cn<3000: ps.append('字数<3000')
    if ps: issues.append((n, ','.join(ps), str(p)))
    rows.append((n,cn,first,last,','.join(ps) or 'OK'))
lines=['# 第一二卷 P0 修补后复核','','范围：新版1-78','','|章|字数|首行|末行|状态|','|---:|---:|---|---|---|']
for n,cn,first,last,st in rows:
    lines.append(f'|{n}|{cn}|{first[:30]}|{last}|{st}|')
lines += ['','## 统计',f'- 总章数：78',f'- 仍有问题：{len(issues)}',f'- 其中格式/标题/末行/行号问题：{sum(1 for _,s,_ in issues if any(k in s for k in ["标题异常","末行异常","行号污染"]))}',f'- 字数不足：{sum(1 for _,s,_ in issues if "字数<3000" in s)}']
OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'issues':len(issues),'report':str(OUT),'format_issues':sum(1 for _,s,_ in issues if any(k in s for k in ['标题异常','末行异常','行号污染'])),'short':sum(1 for _,s,_ in issues if '字数<3000' in s)},ensure_ascii=False))
