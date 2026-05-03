#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import re, json, hashlib
from difflib import SequenceMatcher
from datetime import datetime
ROOT=Path('/root/workspace/科武纪元')
NEW=ROOT/'新版'
SUB=ROOT/'已投稿'
OUT=ROOT/'审核记录'/'第一二卷格式修补'
OUT.mkdir(parents=True, exist_ok=True)

def read(p):
    return p.read_text(encoding='utf-8',errors='ignore') if p.exists() else ''
def norm(s):
    s=s.replace('\ufeff','')
    s=re.sub(r'^\s*\d+\|','',s,flags=re.M)
    s=re.sub(r'^[#＃]+\s*','',s,flags=re.M)
    s=s.replace('（本章完）','').replace('(本章完)','').replace('本章完','').replace('【本章完】','')
    s=re.sub(r'\s+','',s)
    return s
def cn(s): return len(re.findall(r'[\u4e00-\u9fff]',s))
def first_last(s):
    lines=[x.strip() for x in s.splitlines() if x.strip()]
    return (lines[0] if lines else '', lines[-1] if lines else '')
rows=[]
for n in range(1,62):
    pn=NEW/f'第{n}章.md'; ps=SUB/f'第{n}章.txt'
    tn=read(pn); ts=read(ps)
    nn,ns=norm(tn),norm(ts)
    ratio=SequenceMatcher(None, nn, ns).ratio() if nn or ns else 0
    fn,ln=first_last(tn); fs,ls=first_last(ts)
    delta=cn(tn)-cn(ts)
    status=[]
    if not ps.exists(): status.append('已投稿缺文件')
    if not pn.exists(): status.append('新版缺文件')
    if abs(delta)>=300: status.append('字数差>=300')
    if ratio<0.985: status.append('内容差异明显')
    if fs!=fn: status.append('首行不同')
    if ls!='（本章完）': status.append('已投稿末行异常')
    if re.search(r'^\s*\d+\|',ts,re.M): status.append('已投稿行号污染')
    rows.append({
        'chapter':n,'new_file':str(pn),'submitted_file':str(ps),
        'new_cn':cn(tn),'submitted_cn':cn(ts),'delta_new_minus_sub':delta,
        'similarity':round(ratio,4),'new_first':fn,'sub_first':fs,'new_last':ln,'sub_last':ls,
        'status':status or ['基本一致']
    })
summary={
    'total':61,
    'major_diff':sum(1 for r in rows if '内容差异明显' in r['status'] or '字数差>=300' in r['status']),
    'line_pollution':sum(1 for r in rows if '已投稿行号污染' in r['status']),
    'bad_end':sum(1 for r in rows if '已投稿末行异常' in r['status']),
    'short_submitted':sum(1 for r in rows if r['submitted_cn']<3000),
    'missing_submitted':sum(1 for r in rows if '已投稿缺文件' in r['status']),
}
ts=datetime.now().strftime('%Y%m%d_%H%M%S')
json_path=OUT/f'submitted_vs_new_1_61_{ts}.json'
md_path=OUT/f'submitted_vs_new_1_61_{ts}.md'
json_path.write_text(json.dumps({'summary':summary,'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 已投稿 vs 新版 差异表（1-61）','',f'生成时间：{ts}','','## 统计']
for k,v in summary.items(): lines.append(f'- {k}: {v}')
lines += ['','## 差异明细','', '|章|新版字数|已投稿字数|差值|相似度|状态|新版首行|已投稿首行|已投稿末行|','|---:|---:|---:|---:|---:|---|---|---|---|']
for r in rows:
    st=','.join(r['status'])
    def cut(x): return (x or '').replace('|','/').replace('\n',' ')[:32]
    lines.append(f"|{r['chapter']}|{r['new_cn']}|{r['submitted_cn']}|{r['delta_new_minus_sub']}|{r['similarity']}|{st}|{cut(r['new_first'])}|{cut(r['sub_first'])}|{cut(r['sub_last'])}|")
md_path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'summary':summary,'md':str(md_path),'json':str(json_path)},ensure_ascii=False))
