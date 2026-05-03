#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为已投稿 1-52 生成“改”版候选，不覆盖原文。
输出：/root/workspace/科武纪元/待确认投稿/第N章改.txt
原则：
- 以已投稿原文为底，保留投稿内容。
- 仅做安全格式修补：去BOM/去行号污染/标题标准化/补章末。
- 若新版与已投稿存在明显差异，先不替换正文，只在报告标注需人工审。
"""
from pathlib import Path
import re, json
from datetime import datetime
from difflib import SequenceMatcher
ROOT=Path('/root/workspace/科武纪元')
SUB=ROOT/'已投稿'
NEW=ROOT/'新版'
OUT=ROOT/'待确认投稿'
REPORT_DIR=ROOT/'审核记录'/'第一二卷格式修补'
OUT.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
END='（本章完）'
END_VARIANTS={'本章完','(本章完)','（本章完）','【本章完】'}

def read(p): return p.read_text(encoding='utf-8',errors='ignore') if p.exists() else ''
def cn(s): return len(re.findall(r'[\u4e00-\u9fff]',s))
def norm(s):
    s=s.replace('\ufeff','')
    s=re.sub(r'^\s*\d+\|','',s,flags=re.M)
    s=re.sub(r'^[#＃]+\s*','',s,flags=re.M)
    s=s.replace('（本章完）','').replace('(本章完)','').replace('本章完','').replace('【本章完】','')
    s=re.sub(r'\s+','',s)
    return s
TITLE_RE=re.compile(r'^\s*[#＃]*\s*第\s*([0-9一二三四五六七八九十百千万两]+)\s*章\s*(.*)\s*$')
def title_from_text(s,n):
    lines=[x.strip() for x in s.replace('\ufeff','').splitlines() if x.strip()]
    if not lines: return f'第{n}章'
    raw=re.sub(r'^\s*\d+\|','',lines[0]).strip()
    raw=re.sub(r'^[#＃]+\s*','',raw).strip()
    m=TITLE_RE.match(raw)
    if m:
        t=m.group(2).strip()
        return f'第{n}章 {t}' if t else f'第{n}章'
    # 若新版有标题，优先借用新版标题
    ns=read(NEW/f'第{n}章.md')
    nlines=[x.strip() for x in ns.splitlines() if x.strip()]
    if nlines:
        m2=TITLE_RE.match(nlines[0].strip())
        if m2:
            t=m2.group(2).strip()
            return f'第{n}章 {t}' if t else f'第{n}章'
    return f'第{n}章'
def clean_submitted(s,n):
    old=s
    ops=[]
    s=s.replace('\ufeff','')
    if s!=old: ops.append('去BOM')
    lines=[]; hits=0
    for line in s.splitlines():
        nl=re.sub(r'^\s*\d+\|','',line).rstrip()
        if nl!=line.rstrip(): hits+=1
        lines.append(nl)
    if hits: ops.append(f'去行号污染{hits}处')
    while lines and not lines[0].strip(): lines.pop(0)
    while lines and not lines[-1].strip(): lines.pop()
    title=title_from_text(old,n)
    if lines:
        raw_first=re.sub(r'^\s*\d+\|','',lines[0]).strip().lstrip('\ufeff').strip()
        raw_first=re.sub(r'^[#＃]+\s*','',raw_first).strip()
        if TITLE_RE.match(raw_first):
            if lines[0].strip()!=title:
                ops.append('标准化标题')
            lines[0]=title
        else:
            ops.append('补标题')
            lines.insert(0,title)
    else:
        ops.append('补标题')
        lines=[title]
    # last nonempty
    last_i=None
    for i in range(len(lines)-1,-1,-1):
        if lines[i].strip(): last_i=i; break
    if last_i is None:
        lines.append(END); ops.append('补章末')
    else:
        last=lines[last_i].strip()
        if last in END_VARIANTS:
            if last!=END:
                lines[last_i]=END; ops.append('标准化章末')
        else:
            lines.append(''); lines.append(END); ops.append('补章末')
    text='\n'.join(lines).rstrip()+'\n'
    return text, ops
rows=[]
for n in range(1,53):
    ps=SUB/f'第{n}章.txt'; pn=NEW/f'第{n}章.md'
    sub=read(ps); new=read(pn)
    fixed,ops=clean_submitted(sub,n)
    out=OUT/f'第{n}章改.txt'
    out.write_text(fixed,encoding='utf-8')
    ratio=SequenceMatcher(None,norm(new),norm(sub)).ratio() if (new or sub) else 0
    rows.append({
        'chapter':n,'out':str(out),'ops':ops,'submitted_cn':cn(sub),'fixed_cn':cn(fixed),'new_cn':cn(new),
        'new_sub_similarity':round(ratio,4),'manual_review': bool(ratio<0.985 or abs(cn(new)-cn(sub))>=300)
    })
ts=datetime.now().strftime('%Y%m%d_%H%M%S')
json_path=REPORT_DIR/f'revision_candidates_1_52_{ts}.json'
md_path=REPORT_DIR/f'revision_candidates_1_52_{ts}.md'
json_path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
manual=[r for r in rows if r['manual_review']]
lines=['# 已投稿1-52“改”版候选生成报告','',f'生成时间：{ts}','','## 统计',f'- 生成文件：{len(rows)}',f'- 需人工审差异章：{len(manual)}','','## 明细','|章|输出|已投稿字数|改版字数|新版字数|相似度|操作|需人工审|','|---:|---|---:|---:|---:|---:|---|---|']
for r in rows:
    lines.append(f"|{r['chapter']}|{r['out']}|{r['submitted_cn']}|{r['fixed_cn']}|{r['new_cn']}|{r['new_sub_similarity']}|{','.join(r['ops']) or '无'}|{'是' if r['manual_review'] else '否'}|")
md_path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'generated':len(rows),'manual_review':len(manual),'md':str(md_path),'json':str(json_path),'out_dir':str(OUT)},ensure_ascii=False))
