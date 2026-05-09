#!/usr/bin/env python3
from __future__ import annotations
import json, re, subprocess, sys, time
from pathlib import Path
from datetime import datetime

BASE=Path('/root/workspace/科武纪元')
CHAPTERS=[86,95,184,217,233]
ORCH=BASE/'工具脚本/orchestrate_review.py'
EVID=BASE/'工具脚本/build_review_evidence.py'
RAW=BASE/'审核记录/六角色外审/raw'
REC=BASE/'审核记录/六角色外审'
RAW.mkdir(parents=True,exist_ok=True)
REC.mkdir(parents=True,exist_ok=True)

def sh(cmd, timeout=260):
    p=subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def read(path):
    return Path(path).read_text(encoding='utf-8',errors='ignore')

def strip_think(s):
    s=re.sub(r'<think>.*?</think>','',s,flags=re.S)
    s=re.sub(r'<[^>]+>','',s)
    return s.strip()

def verdict(content):
    s=strip_think(content)
    lines=[x.strip() for x in s.splitlines() if x.strip()]
    head=' '.join(lines[:3]).upper()
    neg=['FAIL','硬伤','必改','不宜进入','不能进入','重写','重大问题','不通过']
    pos=['PASS','通过','可进入','想继续看','继续看下一章']
    if any(x.upper() in head for x in neg): return 'FAIL'
    if any(x.upper() in head for x in pos): return 'PASS'
    return 'UNKNOWN'

def compact_evidence(ch, limit=2600):
    md=BASE/'审核记录/证据包'/f'第{ch}章_证据包.md'
    txt=read(md)
    # tail + maps before head, avoid hook truncation
    parts=[]
    for sec in ['## 本地预检','## 任务卡摘录','## 尾段行号','## 证据地图：章末钩子','## 证据地图：大纲锚点','## 证据地图：技术动作','## 证据地图：军事动作','## 证据地图：投稿风险','## 首段行号']:
        m=re.search(r'(^'+re.escape(sec)+r'.*?)(?=^## |\Z)', txt, flags=re.S|re.M)
        if m: parts.append(m.group(1).strip())
    out='\n\n'.join(parts)
    return out[:limit]

def call_role(role, ch, prompt):
    rc,out,err=sh(['python3',str(ORCH),'--role',role,'--chapter',str(ch),'--prompt',prompt])
    if rc!=0:
        data={'role':role,'chapter':ch,'ok':False,'content':err or out,'rc':rc}
    else:
        try: data=json.loads(out)
        except Exception as e: data={'role':role,'chapter':ch,'ok':False,'content':f'json parse error {e}: {out[:500]}'}
    ts=datetime.now().strftime('%Y%m%d_%H%M%S')
    p=RAW/f'第{ch}_{role}_v87_backfill_{ts}.json'
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return data,p

def make_prompt(role,ch,evidence):
    if role=='editor':
        return f'''只做审核，不续写，不改文。\n角色: 编辑\n对象: 《科武纪元》第{ch}章V8.7增量修改稿\n依据: RTK证据包。重点查结构/大纲对齐/商业节奏/章末钩子/投稿风险。\n第一行只写 PASS 或 FAIL。若有硬伤/必改/不宜进入下一步，第一行必须 FAIL。\n第二行起: 理由≤3条，小修≤3条。\n\n{evidence}'''
    if role=='reader':
        return f'''只做审核，不续写，不改文。\n角色: 普通网文读者\n对象: 《科武纪元》第{ch}章V8.7增量修改稿\n依据: RTK证据包。重点查是否看得懂、顺不顺、AI味、是否想看下一章。\n第一行只写 PASS 或 FAIL。若读不下去/解释腔重/钩子无效，第一行必须 FAIL。\n第二行起: 卡点≤3条，小修≤3条。\n\n{evidence}'''
    if role=='military':
        return f'''只做审核，不续写，不改文。\n角色: 军事顾问\n对象: 《科武纪元》第{ch}章V8.7增量修改稿\n依据: RTK证据包。重点查行动链/装备/组织/冲突可信度。无军事硬点可PASS并说明。\n第一行只写 PASS 或 FAIL。若有战术硬伤/装备不可信，第一行必须 FAIL。\n第二行起: 问题≤3条，改法≤3条。\n\n{evidence}'''
    return f'''只做审核，不续写，不改文。\n角色: 科学顾问\n对象: 《科武纪元》第{ch}章V8.7增量修改稿\n依据: RTK证据包。重点查技术设定/科普可读性/术语是否进入行动。\n第一行只写 PASS 或 FAIL。若有科学硬伤/论文腔，第一行必须 FAIL。\n第二行起: 问题≤3条，改法≤3条。\n\n{evidence}'''

def append_record(ch, results):
    p=REC/f'第{ch}章.md'
    old=p.read_text(encoding='utf-8',errors='ignore') if p.exists() else f'# 第{ch}章 六角色外审记录\n'
    lines=['',f'## V8.7外审补证 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', '', '|角色|provider/model|ok|结论|raw|','|---|---|---|---|---|']
    final='PASS'
    for role,(data,path,v) in results.items():
        pm=f"{data.get('provider','?')}/{data.get('model','?')}"
        ok=str(data.get('ok',False))
        if not data.get('ok') or v!='PASS': final='FAIL'
        lines.append(f'|{role}|{pm}|{ok}|{v}|{path}|')
    lines += ['', f'## V8.7补审结论\n{final}', '']
    p.write_text(old.rstrip()+'\n'+'\n'.join(lines),encoding='utf-8')
    return p, final

def main():
    summary=[]
    roles=['editor','reader','military','science']
    for ch in CHAPTERS:
        print(f'== chapter {ch} evidence ==', flush=True)
        rc,out,err=sh(['python3',str(EVID),str(ch)], timeout=120)
        if rc!=0:
            summary.append({'chapter':ch,'status':'EVID_FAIL','error':err or out}); continue
        evidence=compact_evidence(ch)
        results={}
        for role in roles:
            print(f'-- {ch} {role}', flush=True)
            data,path=call_role(role,ch,make_prompt(role,ch,evidence))
            v=verdict(data.get('content','')) if data.get('ok') else 'FAIL'
            results[role]=(data,path,v)
            time.sleep(1)
        rec,final=append_record(ch,results)
        summary.append({'chapter':ch,'final':final,'record':str(rec),'roles':{r:{'ok':d.get('ok'), 'verdict':v, 'model':d.get('model'), 'raw':str(p)} for r,(d,p,v) in results.items()}})
    out=BASE/'审核记录/V87_MiMoPro_正文修改准备包_20260508/外审补证汇总.json'
    out.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'summary':summary,'summary_file':str(out)},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
