#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import re, json, datetime, subprocess, os, time, yaml, requests
BASE=Path('/root/workspace/科武纪元')
CONFIG=Path('/root/.hermes/config.yaml'); ENV=Path('/root/.hermes/.env')
OUT=BASE/'审核记录/六角色外审'; RAW=OUT/'raw'; RAW.mkdir(parents=True,exist_ok=True)
TASKS={
  223:{
    'title':'内战爆发',
    'scope':'H200条件墙/灰色渠道衰减；只做最小增量，不写未经证实数值。',
    'need':['H200','灰色渠道','条件墙','算力券','专项芯片','延迟交付'],
    'anchor':'她点开一个任务。\n\n“流程是这样。上游雇主把剧本拆成小任务，丢进任务池。接单的人不用懂技术，只要下载模板：地点、制服、口号、伤员、火光、镜头抖动，全有预设。模板里带隐形水印，表面看不见，方便上游统计谁做的、转到哪，也是上游分账依据。”',
    'insert':'她点开一个任务。\n\n“流程是这样。上游雇主把剧本拆成小任务，丢进任务池。接单的人不用懂技术，只要下载模板：地点、制服、口号、伤员、火光、镜头抖动，全有预设。模板里带隐形水印，表面看不见，方便上游统计谁做的、转到哪，也是上游分账依据。”\n\n她又拉开一张租卡清单。最上面一栏写着“H200条件墙”：实名企业、白名单用途、训练日志留存、跨境调用限额。旁边的灰色渠道报价被划掉三次，最后只剩一句备注：专项芯片可借，但不保证持续供电；算力券可换，但延迟交付。\n\n“这些工坊拿不到稳定大卡，就把任务拆碎，像把一车货拆成几百个快递单。”陈思琪说，“碎片能跑，连续战场视频跑不稳。所以他们才急着在真实事件发生前排队，靠时间差骗热度。”',
    'message':'V8.12.5 第223章H200条件墙与灰色渠道衰减小修闭环'
  },
  226:{
    'title':'政治联盟',
    'scope':'芯片厂迁移代价侧写：设备/工程师/良率/水电/封装链；只做节点表最小补强。',
    'need':['芯片厂迁移','光刻设备','工程师签证','良率爬坡','水电指标','封装链'],
    'anchor':'林星辰盯着节点表。每个节点后面都挂着产线和接口：东屿芯片、月面轴承、南美稀土、轨道补给站、火星前哨通信塔。',
    'insert':'林星辰盯着节点表。每个节点后面都挂着产线和接口：东屿芯片、月面轴承、南美稀土、轨道补给站、火星前哨通信塔。\n\n节点表下面还有一行迁移代价。东屿芯片厂若撤到内陆，光刻设备要拆成十七个恒温箱运输，工程师签证、家属安置和保密审查至少拖三轮；新厂水电指标未批，洁净室封装链缺两段，良率爬坡按月算，不按命令算。\n\n“这不是把机器搬走。”秦岚盯着那行字，“是把一整座城市的手艺、水、电和人一起搬走。”',
    'message':'V8.12.5 第226章芯片厂迁移代价小修闭环'
  }
}

def load_env():
    if ENV.exists():
        for line in ENV.read_text(encoding='utf-8',errors='ignore').splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))

def cfg(provider):
    c=yaml.safe_load(CONFIG.read_text(encoding='utf-8')) or {}
    x=(c.get('providers') or {}).get(provider,{})
    return (x.get('base_url') or '').rstrip('/'), x.get('api_key') or os.environ.get(x.get('key_env') or '', ''), x.get('default_model') or x.get('model') or {'alibaba':'qwen3.6-plus','minimax-cn':'MiniMax-M2.7','zai':'glm-5.1'}.get(provider,'')

def call(provider,prompt,max_tokens=1200,timeout=180):
    base,key,model=cfg(provider); t=time.time()
    if not base or not key:
        return {'ok':False,'provider':provider,'model':model,'status':0,'returned_model':None,'content':'MISSING_BASE_OR_KEY'}
    payload={'model':model,'messages':[{'role':'user','content':prompt}],'temperature':0.1,'max_tokens':max_tokens}
    if provider=='zai': payload['thinking']={'type':'disabled'}
    try:
        r=requests.post(base+'/chat/completions',headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},json=payload,timeout=timeout)
        try: data=r.json()
        except Exception: data={'raw':r.text[:1200]}
        msg=((data.get('choices') or [{}])[0].get('message') or {}) if isinstance(data,dict) else {}
        content=(msg.get('content') or msg.get('reasoning_content') or '').strip() or str(data)[:1500]
        returned=(data.get('model') if isinstance(data,dict) else None) or model
        return {'ok':bool(content) and r.status_code<500,'provider':provider,'model':model,'status':r.status_code,'returned_model':returned,'latency_s':round(time.time()-t,2),'content':content}
    except Exception as e:
        return {'ok':False,'provider':provider,'model':model,'status':0,'returned_model':None,'latency_s':round(time.time()-t,2),'content':repr(e)}

def decide(r):
    c=re.sub(r'<think>.*?</think>','',r.get('content',''),flags=re.S).strip()
    head=' '.join(c.splitlines()[:4]); tail=' '.join(c.splitlines()[-8:])
    if 'FAIL' in head or '不通过' in head: return 'FAIL'
    if 'PASS' in head or '通过' in head or 'PASS' in tail or '通过' in tail: return 'PASS'
    return 'UNKNOWN'

def fanqie(text):
    lines=text.splitlines(); title=lines[0].strip() if lines else ''
    return len(re.sub(r'\s+','',text))-len(re.sub(r'\s+','',title))

def append_once(path,mark,line):
    s=path.read_text(encoding='utf-8',errors='ignore') if path.exists() else ''
    if mark not in s:
        path.write_text(s.rstrip()+"\n"+line+"\n",encoding='utf-8')

def cover_wiki(ch,text,need):
    wiki=BASE/f'wiki/chapters/ch{ch:03d}.md'
    w=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
    if '## Full Text' in w:
        w=w.split('## Full Text',1)[0].rstrip()+"\n\n## Full Text\n\n"+text.strip()+"\n"
    else:
        w=w.rstrip()+"\n\n## Full Text\n\n"+text.strip()+"\n"
    wiki.write_text(w,encoding='utf-8')
    return {k:k in w for k in need}

def refine(ch):
    task=TASKS[ch]; src=BASE/f'新版/第{ch}章.md'; text=src.read_text(encoding='utf-8')
    before=text
    text=text.replace('**','')
    if not all(k in text for k in task['need']) and task['anchor'] in text:
        text=text.replace(task['anchor'],task['insert'],1)
    changed=text!=before
    if changed:
        bak=BASE/f'备份/20260518_ch{ch}_before_v8125_refine.md'; bak.parent.mkdir(parents=True,exist_ok=True); bak.write_text(before,encoding='utf-8'); src.write_text(text,encoding='utf-8')
    evidence=f"""第{ch}章实际正文已读。V8.12.5目标：{task['scope']}\n边界：非上传章，不生成TXT，不触碰第95章。\n机器必打词：{task['need']}\n正文首段：\n{text[:2200]}\n---MID---\n{text[max(0,len(text)//2-1200):len(text)//2+1500]}\n---TAIL---\n{text[-2400:]}\n请审实际改后文件。第一行必须PASS或FAIL。"""
    reviews={}
    for p,role in [('alibaba','Qwen编辑'),('minimax-cn','MiniMax读者'),('zai','GLM技术轻审')]:
        prompt=f'你是{role}。复审第{ch}章V8.12.5小修：是否完成目标，是否无正文格式污染，是否不破坏原章节主线。'+evidence
        r=call(p,prompt); r['decision']=decide(r); reviews[p]=r
        (RAW/f'第{ch}_v8125_post_review_{p}_20260518.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    sync=subprocess.run(['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(ch),'--message',task['message'],'--no-git'],cwd='/root/workspace',capture_output=True,text=True,timeout=300)
    wiki=cover_wiki(ch,text,task['need'])
    txt=BASE/f'已投稿/第{ch}章.txt'
    if txt.exists(): txt.unlink()
    machine={'changed':changed,'fanqie':fanqie(text),'bold_markers':text.count('**'),'txt_exists':txt.exists(),'keywords':{k:k in text for k in task['need']},'wiki_fulltext_keywords':wiki,'quote_balance':text.count('“')==text.count('”'),'sync_returncode':sync.returncode}
    ok=reviews['alibaba']['decision']=='PASS' and reviews['minimax-cn']['decision']=='PASS' and all(machine['keywords'].values()) and machine['bold_markers']==0 and sync.returncode==0
    rows='\n'.join([f"| {p} | {reviews[p]['provider']}/{reviews[p]['model']} | {reviews[p]['status']} | {reviews[p]['returned_model']} | {reviews[p]['decision']} |" for p in ['alibaba','minimax-cn','zai']])
    rep=OUT/f'第{ch}章_V8125闭环报告_20260518.md'
    rep.write_text(f"""# 第{ch}章 V8.12.5 闭环报告

时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S +0800')}

## 范围
- 章节：第{ch}章《{task['title']}》
- 目标：{task['scope']}
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
- 番茄口径：{machine['fanqie']}
- TXT：未生成。
""",encoding='utf-8')
    stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    append_once(BASE/'STATUS.md',f'第{ch}章V8.12.5闭环',f"- {stamp} | 第{ch}章V8.12.5闭环{'PASS' if ok else 'FAIL'}；{task['scope']}；番茄口径{machine['fanqie']}；报告：审核记录/六角色外审/第{ch}章_V8125闭环报告_20260518.md")
    append_once(BASE/'WAL.md',f'第{ch}章V8.12.5闭环',f"\n## {stamp}｜第{ch}章V8.12.5闭环\n- 结论：{'PASS' if ok else 'FAIL'}。\n- 目标：{task['scope']}\n- 非上传章，未生成TXT；sync_kewu --no-git returncode={sync.returncode}。")
    return {'ok':ok,'chapter':ch,'fanqie':machine['fanqie'],'report':str(rep.relative_to(BASE)),'reviews':{p:reviews[p]['decision'] for p in reviews},'machine':machine}

def update_queue(results):
    qpath=BASE/'审核记录/goal模式/V8125_执行队列_20260517.json'
    q=json.loads(qpath.read_text(encoding='utf-8'))
    done={r['chapter']:r for r in results if r.get('ok')}
    failed={r['chapter']:r for r in results if not r.get('ok')}
    for it in q['outline_refine_candidates']:
        ch=it.get('chapter')
        if ch in done:
            it['status']='completed'; it['report']=done[ch]['report']; it['updated_at']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M +0800')
        if ch in failed:
            it['status']='failed'; it['report']=failed[ch]['report']; it['updated_at']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M +0800')
    if failed: q['current_next']=f"outline_refine_candidates:{next(iter(failed))}_failed"
    else: q['current_next']='future_outline_only:306/307/361/371-381'
    qpath.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    load_env(); results=[]
    for ch in [223,226]:
        r=refine(ch); results.append(r); print(json.dumps(r,ensure_ascii=False,indent=2))
        update_queue(results)
        if not r.get('ok'): break
    summary=OUT/'V8125_第223_226闭环汇总_20260518.json'
    summary.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'summary':str(summary),'results':results},ensure_ascii=False,indent=2))
    raise SystemExit(0 if all(r.get('ok') for r in results) else 2)
if __name__=='__main__': main()
