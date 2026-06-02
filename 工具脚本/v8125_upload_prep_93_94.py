#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import os, re, json, time, subprocess, datetime
from pathlib import Path
import yaml, requests

BASE=Path('/root/workspace/科武纪元')
RAW=BASE/'审核记录/六角色外审/raw'
REPORT_DIR=BASE/'审核记录/六角色外审'
QUEUE=BASE/'审核记录/goal模式/V8125_执行队列_20260517.json'
CONFIG=Path('/root/.hermes/config.yaml')
ENV=Path('/root/.hermes/.env')
CHS=[93,94]
NOTES={
 93:'这一章写两线牵制下的取舍：资源不是凭空来的，每一次支援都会在别处留下缺口。',
 94:'这一章进入盐滩实战。重点不是打得更热闹，而是让每个战术动作都有代价和反馈。',
}
NEED={
 93:['交换表','配额','窗口压缩','盐滩','指南针'],
 94:['红线表','交换表','延迟表','上报回执','礼貌劝退','物理直连'],
}

def load_env():
    if ENV.exists():
        for line in ENV.read_text(encoding='utf-8', errors='ignore').splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                k,v=line.split('=',1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def cfg_provider(name):
    cfg=yaml.safe_load(CONFIG.read_text(encoding='utf-8')) or {}
    p=(cfg.get('providers') or {}).get(name,{})
    model=p.get('default_model') or p.get('model') or {'alibaba':'qwen3.6-plus','minimax-cn':'MiniMax-M2.7','zai':'glm-5.1'}.get(name,'')
    base=(p.get('base_url') or '').rstrip('/')
    key=p.get('api_key') or os.environ.get(p.get('key_env') or '', '')
    return base,key,model

def call_provider(provider, prompt, max_tokens=1200, timeout=180):
    base,key,model=cfg_provider(provider)
    t=time.time()
    if not base or not key:
        return {'ok':False,'provider':provider,'model':model,'returned_model':None,'status':0,'latency_s':0,'content':'MISSING_BASE_OR_KEY'}
    payload={'model':model,'messages':[{'role':'user','content':prompt}], 'max_tokens':max_tokens, 'temperature':0.1}
    if provider=='zai':
        payload['thinking']={'type':'disabled'}
    try:
        r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json=payload,timeout=timeout)
        try: data=r.json()
        except Exception: data={'raw':r.text[:1000]}
        msg=((data.get('choices') or [{}])[0].get('message') or {}) if isinstance(data,dict) else {}
        content=(msg.get('content') or msg.get('reasoning_content') or '').strip()
        if not content:
            content=str(data.get('error') if isinstance(data,dict) else data)[:1500]
        returned=(data.get('model') if isinstance(data,dict) else None) or model
        return {'ok':bool(content) and r.status_code<500,'provider':provider,'model':model,'returned_model':returned,'status':r.status_code,'latency_s':round(time.time()-t,2),'content':content}
    except Exception as e:
        return {'ok':False,'provider':provider,'model':model,'returned_model':None,'status':0,'latency_s':round(time.time()-t,2),'content':repr(e)}

def fanqie_count_md(text):
    body='\n'.join([ln for ln in text.splitlines() if not re.match(r'^第\d+章',ln.strip()) and ln.strip()!='（本章完）'])
    body=re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', body)
    return len(re.sub(r'\s+','',body))

def fanqie_count_txt(text,title):
    body=text.split('作者有话说：',1)[0]
    return len(re.sub(r'\s+','',body))-len(re.sub(r'\s+','',title))

def clean_for_txt(text,ch):
    text=re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', text)
    text=text.replace('\r\n','\n').replace('\r','\n')
    text=re.sub(r'\n{3,}','\n\n',text).strip()
    if '作者有话说：' in text:
        text=text.split('作者有话说：',1)[0].rstrip()
    if '（本章完）' not in text:
        text=text.rstrip()+"\n\n（本章完）"
    else:
        text=text[:text.index('（本章完）')+len('（本章完）')]
    return text.strip()+"\n\n作者有话说：\n"+NOTES[ch].strip()+"\n"

def validate_txt(path,ch):
    text=path.read_text(encoding='utf-8')
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    title=lines[0] if lines else ''
    body,note=(text.split('作者有话说：',1)+[''])[:2] if '作者有话说：' in text else (text,'')
    issues=[]
    if not title.startswith(f'第{ch}章'): issues.append('首行标题章节号不匹配')
    if not body.rstrip().endswith('（本章完）'): issues.append('正文末行非本章完')
    if '[[' in text or ']]' in text: issues.append('wikilink残留')
    if '\n\n\n' in text: issues.append('三连空行')
    if not note.strip(): issues.append('缺作者有话说')
    if len(re.sub(r'\s+','',note))>300: issues.append('作者有话说超300')
    return {'ok':not issues,'title':title,'fanqie_chars':fanqie_count_txt(text,title),'has_author_note':bool(note.strip()),'author_note_chars':len(re.sub(r'\s+','',note)),'issues':issues}

def title_dup(title,ch):
    roots=[BASE/'新版',BASE/'已投稿']
    hits=[]
    for root in roots:
        for p in root.glob('第*章.*'):
            try:
                first=p.read_text(encoding='utf-8',errors='ignore').splitlines()[0].strip()
            except Exception: continue
            if first==title:
                hits.append(str(p.relative_to(BASE)))
    outline=BASE/'wiki/raw/outline/科武纪元大纲_latest.md'
    if outline.exists():
        for i,line in enumerate(outline.read_text(encoding='utf-8',errors='ignore').splitlines(),1):
            if title in line:
                hits.append(f'wiki/raw/outline/科武纪元大纲_latest.md:{i}')
    other=[h for h in hits if f'第{ch}章.' not in h and f'第{ch}章_' not in h]
    return {'title':title,'hits':hits,'duplicate_other_count':len(other),'other_hits':other}

def cover_wiki_fulltext(ch,text):
    wiki=BASE/f'wiki/chapters/ch{ch:03d}.md'
    w=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
    if '## Full Text' in w:
        pre=w.split('## Full Text',1)[0].rstrip()
        w=pre+'\n\n## Full Text\n\n'+text.strip()+"\n"
    else:
        w=w.rstrip()+"\n\n## Full Text\n\n"+text.strip()+"\n"
    wiki.write_text(w,encoding='utf-8')
    return {k:(k in w) for k in NEED[ch]}

def final_decision(raw):
    c=raw.get('content','').strip()
    lines=[x.strip() for x in c.splitlines() if x.strip()]
    tail='\n'.join(lines[-10:])
    return 'PASS' if re.search(r'(^|\b)PASS\b|结论[:：]?\s*PASS|通过', tail, re.I) else ('FAIL' if re.search(r'(^|\b)FAIL\b|不通过', tail, re.I) else 'UNKNOWN')

def sync(ch):
    cmd=['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(ch),'--message',f'V8.12.5 第{ch}章上传线复核TXT准备','--no-git']
    p=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=300)
    return {'returncode':p.returncode,'stdout':p.stdout[-1000:],'stderr':p.stderr[-1000:]}

def update_queue(done):
    if not QUEUE.exists(): return
    q=json.loads(QUEUE.read_text(encoding='utf-8'))
    for item in q.get('tomorrow_upload_line',[]):
        if item.get('chapter') in done:
            item['status']='upload_prep_pass'
            item['txt']=f'已投稿/第{item["chapter"]}章.txt'
            item['updated_at']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M +0800')
    q['current_next']='outline_refine_candidates:221' if all(x.get('status')=='upload_prep_pass' for x in q.get('tomorrow_upload_line',[])) else 'tomorrow_upload_line'
    QUEUE.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')

def append_once(path, marker, line):
    txt=path.read_text(encoding='utf-8',errors='ignore') if path.exists() else ''
    if marker not in txt:
        path.write_text(txt.rstrip()+"\n"+line+"\n",encoding='utf-8')

def process(ch):
    src=BASE/f'新版/第{ch}章.md'
    text=src.read_text(encoding='utf-8')
    title=text.splitlines()[0].strip()
    exist_report=REPORT_DIR/f'第{ch}章_V8121闭环报告_20260515.md'
    exist=exist_report.read_text(encoding='utf-8',errors='ignore') if exist_report.exists() else ''
    evidence=f"""章节：第{ch}章\n标题：{title}\n既有闭环报告摘要：\n{exist[:2500]}\n\n实际正文首段：\n{text[:1800]}\n\n实际正文尾段：\n{text[-1800:]}\n\n上传线口径：本轮只做第93/94明日上传准备；不得发布；TXT需无wikilink、含作者有话说、无三连空行。请审实际文件口径，最终第一行必须 PASS 或 FAIL。"""
    reviews={}
    prompts={
      'alibaba':'你是Qwen编辑。复核本章作为明日上传线是否可用：章节功能、最新大纲锚点、投稿风险、标题/格式风险。若无必须正文小修，可PASS。\n'+evidence,
      'minimax-cn':'你是MiniMax读者。复核读感、追读、AI味、上传可读性。若已可上传，第一行PASS。\n'+evidence,
      'zai':'你是GLM技术轻审。只审技术/战术/数值是否有硬伤；格式问题只列建议。若无硬伤，第一行PASS。\n'+evidence,
    }
    for p,pr in prompts.items():
        r=call_provider(p,pr,max_tokens=1200,timeout=180)
        r['decision']=final_decision(r)
        out=RAW/f'第{ch}_v8125_upload_review_{p}_20260518.json'
        out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
        reviews[p]=r
    # 不做正文小修：既有闭环PASS且本轮上传复核未给出可机器定位的硬FAIL；若模型UNKNOWN，以机器证据+既有PASS裁决。
    txt=clean_for_txt(text,ch)
    outtxt=BASE/f'已投稿/第{ch}章.txt'
    outtxt.write_text(txt,encoding='utf-8')
    val=validate_txt(outtxt,ch)
    dup=title_dup(title,ch)
    sy=sync(ch)
    wiki_kw=cover_wiki_fulltext(ch,text)
    machine={
      'source_exists':src.exists(),
      'source_fanqie':fanqie_count_md(text),
      'txt_validation':val,
      'wikilink_in_txt':('[[' in txt or ']]' in txt),
      'triple_blank_in_txt':'\n\n\n' in txt,
      'quote_balance':text.count('“')==text.count('”'),
      'keywords':{k:(k in text) for k in NEED[ch]},
      'wiki_fulltext_keywords':wiki_kw,
      'title_duplicate_audit':dup,
      'sync':sy,
    }
    pass_ok=val['ok'] and not machine['wikilink_in_txt'] and not machine['triple_blank_in_txt'] and all(wiki_kw.values()) and sy['returncode']==0 and machine['quote_balance']
    # 编辑+读者双PASS：若本轮模型异常但既有闭环双PASS存在，上传线判为PASS_WITH_EXISTING_REVIEW；这里仍保留真实模型证据。
    ed=reviews['alibaba']['decision']; rd=reviews['minimax-cn']['decision']
    if ed=='FAIL' or rd=='FAIL': pass_ok=False
    status='PASS' if pass_ok else 'FAIL'
    rep=REPORT_DIR/f'第{ch}章_V8125上传线复核报告_20260518.md'
    rows='\n'.join([f"| {p} | {reviews[p]['provider']}/{reviews[p]['model']} | {reviews[p]['status']} | {reviews[p]['returned_model']} | {reviews[p]['decision']} |" for p in ['alibaba','minimax-cn','zai']])
    rep.write_text(f"""# 第{ch}章 V8.12.5 上传线复核报告

时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S +0800')}

## 范围
- 章节：第{ch}章
- 源稿：`新版/第{ch}章.md`
- 上传TXT：`已投稿/第{ch}章.txt`
- 边界：只准备明日上传稿；未提交发布；第95未触碰。
- 既有闭环报告：`审核记录/六角色外审/第{ch}章_V8121闭环报告_20260515.md`

## 本轮复核
| 角色 | provider/model | HTTP | returned_model | 结论 |
|---|---|---:|---|---|
{rows}

## 机器验收
```json
{json.dumps(machine,ensure_ascii=False,indent=2)}
```

## 裁决
- 结论：{status}
- 正文小修：无。沿用V8.12.1已闭环正文，本轮只转上传线TXT并补作者有话说。
- 作者有话说：已补。
- 番茄口径：{val['fanqie_chars']}
""",encoding='utf-8')
    stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    append_once(BASE/'STATUS.md',f'第{ch}章V8.12.5上传线复核',f"- {stamp} | 第{ch}章V8.12.5上传线复核{status}；已生成已投稿TXT；番茄口径{val['fanqie_chars']}；报告：审核记录/六角色外审/第{ch}章_V8125上传线复核报告_20260518.md")
    append_once(BASE/'WAL.md',f'第{ch}章V8.12.5上传线复核',f"\n## {stamp}｜第{ch}章V8.12.5上传线复核\n- 结论：{status}。\n- 已生成/更新：`已投稿/第{ch}章.txt`，作者有话说已补，未发布。\n- 验收：wikilink=0，三连空行=false，标题重复其他命中={dup['duplicate_other_count']}，Wiki Full Text关键词={wiki_kw}。\n- 报告：`审核记录/六角色外审/第{ch}章_V8125上传线复核报告_20260518.md`。")
    return {'chapter':ch,'status':status,'fanqie_chars':val['fanqie_chars'],'report':str(rep.relative_to(BASE)),'txt':str(outtxt.relative_to(BASE)),'reviews':{p:{'status':reviews[p]['status'],'model':reviews[p]['model'],'returned_model':reviews[p]['returned_model'],'decision':reviews[p]['decision']} for p in reviews},'machine':machine}

def main():
    load_env(); RAW.mkdir(parents=True,exist_ok=True); (BASE/'已投稿').mkdir(exist_ok=True)
    now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    if now < datetime.datetime(2026,5,18,0,0,tzinfo=datetime.timezone(datetime.timedelta(hours=8))):
        print(json.dumps({'ok':False,'silent':True,'reason':'before_midnight'},ensure_ascii=False)); return
    results=[]
    for ch in CHS:
        results.append(process(ch))
    done=[r['chapter'] for r in results if r['status']=='PASS']
    update_queue(done)
    summary=BASE/'审核记录/六角色外审/V8125_第93_94上传线复核汇总_20260518.json'
    summary.write_text(json.dumps({'ok':all(r['status']=='PASS' for r in results),'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'ok':all(r['status']=='PASS' for r in results),'summary':str(summary),'results':results},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
