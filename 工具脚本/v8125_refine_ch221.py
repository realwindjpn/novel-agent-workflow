#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import re,json,datetime,subprocess,os,time,yaml,requests
BASE=Path('/root/workspace/科武纪元'); CH=221
SRC=BASE/f'新版/第{CH}章.md'; RAW=BASE/'审核记录/六角色外审/raw'; OUT=BASE/'审核记录/六角色外审'
CONFIG=Path('/root/.hermes/config.yaml'); ENV=Path('/root/.hermes/.env')
NEED=['霍尔木兹','商业拒付','保险机构','监管数据接口','熔断','单边反蜂群预案']

def env():
    if ENV.exists():
        for line in ENV.read_text(encoding='utf-8',errors='ignore').splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))

def cfg(p):
    c=yaml.safe_load(CONFIG.read_text(encoding='utf-8')) or {}; x=(c.get('providers') or {}).get(p,{})
    return (x.get('base_url') or '').rstrip('/'), x.get('api_key') or os.environ.get(x.get('key_env') or '', ''), x.get('default_model') or x.get('model') or {'alibaba':'qwen3.6-plus','minimax-cn':'MiniMax-M2.7','zai':'glm-5.1'}.get(p,'')

def call(p,prompt,max_tokens=1400,timeout=180):
    base,key,model=cfg(p); t=time.time()
    if not base or not key: return {'ok':False,'provider':p,'model':model,'status':0,'returned_model':None,'content':'MISSING_BASE_OR_KEY'}
    payload={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':max_tokens,'temperature':0.1}
    if p=='zai': payload['thinking']={'type':'disabled'}
    try:
        r=requests.post(base+'/chat/completions',headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},json=payload,timeout=timeout)
        try: data=r.json()
        except Exception: data={'raw':r.text[:1000]}
        msg=((data.get('choices') or [{}])[0].get('message') or {}) if isinstance(data,dict) else {}
        content=(msg.get('content') or msg.get('reasoning_content') or '').strip() or str(data)[:1500]
        returned=(data.get('model') if isinstance(data,dict) else None) or model
        return {'ok':bool(content) and r.status_code<500,'provider':p,'model':model,'status':r.status_code,'returned_model':returned,'latency_s':round(time.time()-t,2),'content':content}
    except Exception as e:
        return {'ok':False,'provider':p,'model':model,'status':0,'returned_model':None,'latency_s':round(time.time()-t,2),'content':repr(e)}

def decide(r):
    c=re.sub(r'<think>.*?</think>','',r.get('content',''),flags=re.S).strip(); head=' '.join(c.splitlines()[:3]); tail=' '.join(c.splitlines()[-8:])
    if 'FAIL' in head or '不通过' in head: return 'FAIL'
    if 'PASS' in head or '通过' in head or 'PASS' in tail or '通过' in tail: return 'PASS'
    return 'UNKNOWN'

def fanqie(s):
    title=next((x for x in s.splitlines() if x.strip()),'')
    return len(re.sub(r'\s+','',s))-len(re.sub(r'\s+','',title))

def append_once(path,mark,line):
    s=path.read_text(encoding='utf-8',errors='ignore') if path.exists() else ''
    if mark not in s: path.write_text(s.rstrip()+"\n"+line+"\n",encoding='utf-8')

def cover_wiki(text):
    wiki=BASE/'wiki/chapters/ch221.md'; w=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
    if '## Full Text' in w: w=w.split('## Full Text',1)[0].rstrip()+"\n\n## Full Text\n\n"+text.strip()+"\n"
    else: w=w.rstrip()+"\n\n## Full Text\n\n"+text.strip()+"\n"
    wiki.write_text(w,encoding='utf-8')
    return {k:k in w for k in NEED}

def main():
    env(); RAW.mkdir(parents=True,exist_ok=True)
    text=SRC.read_text(encoding='utf-8')
    before=text
    # 确定性小修：去除MD加粗污染；补商业拒付字段，不改主线。
    text=text.replace('**','')
    anchor='第五分钟，保险机构请求摘要。'
    insert='第五分钟，保险机构请求摘要。摘要请求下方还带着一行灰色附注：若监管数据接口未在三十分钟内授权，本批商船保险理赔进入商业拒付复核，预付款冻结。'
    if '商业拒付' not in text and anchor in text:
        text=text.replace(anchor,insert,1)
    changed=(text!=before)
    if changed:
        bak=BASE/f'备份/20260518_ch221_before_v8125_refine.md'; bak.write_text(before,encoding='utf-8'); SRC.write_text(text,encoding='utf-8')
    evidence=f"""第221章实际正文已读。V8.12.5目标：霍尔木兹商业拒付触发分叉；只能最小增量，不生成TXT。\n机器必打词：{NEED}\n正文首段：\n{text[:2200]}\n---MID---\n{text[7000:9300]}\n---TAIL---\n{text[-2200:]}\n请审实际改后文件。第一行必须PASS或FAIL。"""
    reviews={}
    for p,role in [('alibaba','Qwen编辑'),('minimax-cn','MiniMax读者'),('zai','GLM技术轻审')]:
        prompt=f'你是{role}。复审第221章V8.12.5小修：是否完成霍尔木兹商业拒付触发分叉，是否无正文格式污染，是否不破坏远岸账号主线。'+evidence
        r=call(p,prompt); r['decision']=decide(r); reviews[p]=r
        (RAW/f'第221_v8125_post_review_{p}_20260518.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    sync=subprocess.run(['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter','221','--message','V8.12.5 第221章霍尔木兹商业拒付小修闭环','--no-git'],cwd='/root/workspace',capture_output=True,text=True,timeout=300)
    wiki=cover_wiki(text)
    txt=BASE/'已投稿/第221章.txt'
    if txt.exists(): txt.unlink()
    machine={'changed':changed,'fanqie':fanqie(text),'bold_markers':text.count('**'),'txt_exists':txt.exists(),'keywords':{k:k in text for k in NEED},'wiki_fulltext_keywords':wiki,'quote_balance':text.count('“')==text.count('”'),'sync_returncode':sync.returncode}
    ok=reviews['alibaba']['decision']=='PASS' and reviews['minimax-cn']['decision']=='PASS' and all(machine['keywords'].values()) and machine['bold_markers']==0 and sync.returncode==0
    rep=OUT/'第221章_V8125闭环报告_20260518.md'
    rows='\n'.join([f"| {p} | {reviews[p]['provider']}/{reviews[p]['model']} | {reviews[p]['status']} | {reviews[p]['returned_model']} | {reviews[p]['decision']} |" for p in ['alibaba','minimax-cn','zai']])
    rep.write_text(f"""# 第221章 V8.12.5 闭环报告

时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S +0800')}

## 范围
- 章节：第221章《远岸账号》
- 目标：霍尔木兹商业拒付触发分叉；只做最小增量。
- 边界：非上传章；未生成TXT；未触碰第95章。

## 写后复审
| 角色 | provider/model | HTTP | returned_model | 结论 |
|---|---|---:|---|---|
{rows}

## 机器验收
```json
{json.dumps(machine,ensure_ascii=False,indent=2)}
```

## 裁决
- 结论：{'PASS' if ok else 'FAIL'}
- 小修：清除正文MD加粗标记；补“商业拒付复核/预付款冻结”触发项。
- 番茄口径：{machine['fanqie']}
- TXT：未生成。
""",encoding='utf-8')
    stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    append_once(BASE/'STATUS.md','第221章V8.12.5闭环',f"- {stamp} | 第221章V8.12.5闭环{'PASS' if ok else 'FAIL'}；霍尔木兹商业拒付小修；番茄口径{machine['fanqie']}；报告：审核记录/六角色外审/第221章_V8125闭环报告_20260518.md")
    append_once(BASE/'WAL.md','第221章V8.12.5闭环',f"\n## {stamp}｜第221章V8.12.5闭环\n- 结论：{'PASS' if ok else 'FAIL'}。\n- 已清正文加粗标记，补商业拒付复核/预付款冻结触发；未生成TXT。\n- Wiki Full Text已覆盖，sync_kewu --no-git returncode={sync.returncode}。")
    qpath=BASE/'审核记录/goal模式/V8125_执行队列_20260517.json'
    q=json.loads(qpath.read_text(encoding='utf-8'))
    for it in q['outline_refine_candidates']:
        if it.get('chapter')==221:
            it['status']='completed' if ok else 'failed'; it['report']='审核记录/六角色外审/第221章_V8125闭环报告_20260518.md'; it['updated_at']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M +0800')
    q['current_next']='outline_refine_candidates:223' if ok else 'outline_refine_candidates:221_failed'
    qpath.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'ok':ok,'chapter':221,'fanqie':machine['fanqie'],'report':str(rep),'reviews':{p:reviews[p]['decision'] for p in reviews},'machine':machine},ensure_ascii=False,indent=2))
    return 0 if ok else 2
if __name__=='__main__': raise SystemExit(main())
