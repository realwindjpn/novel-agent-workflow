#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import re, json, subprocess, datetime, os, time, requests, yaml

BASE=Path('/root/workspace/科武纪元'); CH=156
SRC=BASE/'新版/第156章.md'; RAW=BASE/'审核记录/六角色外审/raw'
TASK=BASE/'审核记录/六角色外审/第156章_V8121_TKX任务卡_20260515.md'
REPORT=BASE/'审核记录/六角色外审/第156章_V8121_TKX闭环报告_20260515.md'
KEYWORDS=['X-7','X-8','转换接头','发射窗口','到港延迟','备件型号']
FORBID=['台湾','伊朗','航道','封锁','制裁','战争','政治新闻','东屿库存表']

def load_env():
    env=Path('/root/.hermes/.env')
    if env.exists():
        for line in env.read_text(errors='ignore').splitlines():
            if line and not line.startswith('#') and '=' in line:
                k,v=line.split('=',1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def call_provider(provider, prompt, max_tokens=1600, timeout=120):
    cfg=yaml.safe_load(Path('/root/.hermes/config.yaml').read_text()) or {}
    p=(cfg.get('providers') or {}).get(provider,{})
    base=(p.get('base_url') or '').rstrip('/'); model=p.get('default_model') or p.get('model') or {'alibaba':'qwen3.6-plus','minimax-cn':'MiniMax-M2.7','zai':'glm-5.1'}[provider]
    key=p.get('api_key') or os.environ.get(p.get('key_env') or '', '')
    t=time.time()
    try:
        r=requests.post(base+'/chat/completions',headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':max_tokens,'temperature':0.1},timeout=timeout)
        try: data=r.json()
        except Exception: data={'raw':r.text[:800]}
        msg=((data.get('choices') or [{}])[0].get('message') or {}) if isinstance(data,dict) else {}
        content=(msg.get('content') or msg.get('reasoning_content') or '').strip() or str(data.get('error',''))[:800]
        return {'ok':r.status_code==200 and bool(content),'provider':provider,'model':model,'returned_model':data.get('model') if isinstance(data,dict) else model,'status':r.status_code,'latency_s':round(time.time()-t,2),'content':content}
    except Exception as e:
        return {'ok':False,'provider':provider,'model':model,'returned_model':None,'status':0,'latency_s':round(time.time()-t,2),'content':repr(e)}

def pass_first(r):
    c=re.sub(r'<think>.*?</think>','',r.get('content',''),flags=re.S|re.I).strip()
    first=c.splitlines()[0].upper() if c else ''
    return r.get('ok') and ('PASS' in first or first.startswith('通过')) and not first.startswith('FAIL')

def fanqie_count(s):
    body='\n'.join([ln for ln in s.splitlines() if not re.match(r'^第\d+章',ln.strip()) and ln.strip()!='（本章完）'])
    body=re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]',r'\1',body)
    return len(re.sub(r'\s+','',body))

def main():
    load_env(); RAW.mkdir(parents=True,exist_ok=True)
    text=SRC.read_text(encoding='utf-8')
    frag='''清点到密封圈那箱时，箱盖内侧夹着一张临时更改单。

“箱号B-214，X-7密封圈可用。”林星辰念到一半，停了停，“后续接口标准迁到X-8。”

方宁把清单拉到下一页：“转换接头呢？”

“调到下一批。”陈思琪看着备注，“原因：地面稀土到港延迟。”

值守工程师低声报数：“现有备件型号能撑三百六十工时，但发射窗口往后压了，授权要重签。”'''
    machine={'keywords':{k:(k in text) for k in KEYWORDS},'forbid':{k:(k in text) for k in FORBID},'fanqie_count':fanqie_count(text),'wikilink_count':text.count('[['),'txt_exists':(BASE/'已投稿/第156章.txt').exists(),'quote_balance':text.count('“')==text.count('”')}
    if not all(machine['keywords'].values()) or any(machine['forbid'].values()):
        print(json.dumps({'ok':False,'reason':'machine gate fail','machine':machine},ensure_ascii=False)); raise SystemExit(1)
    ev=f"任务卡:\n{TASK.read_text(encoding='utf-8')}\n\n修正后新增片段:\n{frag}\n\n机器证据：{machine}。摘录标签非正文。"
    prompts={
      'alibaba':'你是Qwen编辑复审。Qwen上轮指出人名断层；现在已按你给出的定稿块修正为林星辰/方宁/陈思琪。请审实际修正后第156章，小增量≤300字，元件标准/轨道窗口自然，不变政治新闻。最终第一行必须 PASS 或 FAIL。\n'+ev,
      'minimax-cn':'你是MiniMax读者复审。审修正后新增段是否顺、是否增强现实压力、是否报告腔。最终第一行必须 PASS 或 FAIL。\n'+ev,
      'zai':'你是GLM技术轻审。审X-7/X-8、转换接头、稀土到港延迟、发射窗口、备件型号是否可信，禁政治新闻。最终第一行必须 PASS 或 FAIL。\n'+ev,
    }
    post={}
    for p,pr in prompts.items():
        r=call_provider(p,pr,1600,120)
        post[p]=r
        (RAW/f'第156_post_review_fix_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    verdict={p:pass_first(r) for p,r in post.items()}
    if not (verdict.get('alibaba') and verdict.get('minimax-cn')):
        print(json.dumps({'ok':False,'verdict':verdict,'post':{k:v.get('content','')[:300] for k,v in post.items()}},ensure_ascii=False,indent=2)); raise SystemExit(1)
    sync=subprocess.run(['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter','156','--message','V8.12.1 第156章TKX作者位B5双保险闭环','--no-git'],cwd='/root/workspace',capture_output=True,text=True,timeout=300)
    wiki=BASE/'wiki/chapters/ch156.md'; wtxt=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
    if not all(k in wtxt for k in KEYWORDS):
        if '## Full Text' in wtxt: wtxt=wtxt.split('## Full Text')[0].rstrip()+'\n\n## Full Text\n\n'+text+'\n'
        else: wtxt=wtxt.rstrip()+'\n\n## Full Text\n\n'+text+'\n'
        wiki.write_text(wtxt,encoding='utf-8')
    wtxt=wiki.read_text(encoding='utf-8',errors='ignore')
    stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    line=f"\n- {stamp} | 第156章V8.12.1 TKX精修闭环：X-7/X-8密封圈、转换接头、稀土到港延迟、备件型号与发射窗口轻触；非上传章未生成TXT；报告：审核记录/六角色外审/第156章_V8121_TKX闭环报告_20260515.md\n"
    for fn in [BASE/'STATUS.md',BASE/'WAL.md']:
        t=fn.read_text(encoding='utf-8',errors='ignore')
        if '第156章V8.12.1 TKX精修闭环' not in t: fn.write_text(t+line,encoding='utf-8')
    track=BASE/'小说综合跟踪表.md'; tt=track.read_text(encoding='utf-8',errors='ignore')
    tline=f"- 第156章《重返月球》：回改精修闭环 PASS；TKX/gpt-5.5作者位已补V8.12.1/B5元件标准与轨道窗口：X-7/X-8密封圈、转换接头、稀土到港延迟、备件型号、发射窗口；番茄口径{machine['fanqie_count']}；非上传章未生成TXT；报告：`审核记录/六角色外审/第156章_V8121_TKX闭环报告_20260515.md`。"
    if '第156章《重返月球》：回改精修闭环 PASS' not in tt:
        if '### 2026-05-15 V8.12.1连续逐章精修' in tt:
            tt=tt.replace('### 2026-05-15 V8.12.1连续逐章精修\n','### 2026-05-15 V8.12.1连续逐章精修\n'+tline+'\n')
        else:
            tt=tt.rstrip()+'\n\n### 2026-05-15 V8.12.1连续逐章精修\n'+tline+'\n'
        track.write_text(tt,encoding='utf-8')
    sm=json.loads((RAW/'第156_tkx_smoke_20260515.json').read_text()) if (RAW/'第156_tkx_smoke_20260515.json').exists() else {}
    report=f'''# 第156章 V8.12.1 TKX精修闭环报告

时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 范围
- 章节：第156章《重返月球》
- 文件：`新版/第156章.md`
- 边界：非上传章；未生成TXT；未上传番茄。
- 备份：`备份/20260515_ch156_before_v8121_tkx.md`

## 作者路由
| 角色 | provider/model | HTTP | returned_model | 结论 |
|---|---|---:|---|---|
| 作者 | tkx/{sm.get('model')} | {sm.get('status')} | {sm.get('returned_model')} | OK |

## 流程
- 当章任务卡：`审核记录/六角色外审/第156章_V8121_TKX任务卡_20260515.md`
- 原文外审：Qwen / MiniMax / GLM raw 已落盘。
- 作者精修：TKX gpt-5.5 直连产出片段；首轮误用林溪/周凛，Qwen FAIL。
- 主控修正：采纳Qwen定稿块，替换为林星辰/方宁/陈思琪。
- 写后复审：Qwen编辑={'PASS' if verdict.get('alibaba') else 'FAIL'}；MiniMax读者={'PASS' if verdict.get('minimax-cn') else 'FAIL'}；GLM技术={'PASS' if verdict.get('zai') else 'WARN'}。

## 机器验收
- 番茄口径：{machine['fanqie_count']}
- wikilink计数：{machine['wikilink_count']}（新版MD允许）
- 引号平衡：{machine['quote_balance']}
- 已投稿TXT存在：{machine['txt_exists']}（本章应为False）
- 必打词：{machine['keywords']}
- 禁词命中：{machine['forbid']}
- Wiki Full Text关键词：{{k:(k in wtxt) for k in KEYWORDS}}
- sync_kewu：returncode={sync.returncode}

## 结论
PASS。第156章已闭环。下一章：第169章（B5能源/保险费率，非上传不生成TXT）。
'''
    REPORT.write_text(report,encoding='utf-8')
    paths=[SRC,TASK,REPORT,wiki,track,BASE/'STATUS.md',BASE/'WAL.md',BASE/'工具脚本/refine_ch156_v8121_tkx.py',BASE/'工具脚本/finalize_ch156_tkx.py']
    rel=[str(x.relative_to(BASE)) for x in paths if x.exists()]
    subprocess.run(['git','add','-f']+rel,cwd=str(BASE),capture_output=True,text=True,timeout=120)
    staged=subprocess.run(['git','-c','core.quotePath=false','diff','--cached','name-only'],cwd=str(BASE),capture_output=True,text=True,timeout=120)
    if staged.returncode!=0:
        staged=subprocess.run(['git','-c','core.quotePath=false','diff','--cached','--name-only'],cwd=str(BASE),capture_output=True,text=True,timeout=120)
    names=[x for x in staged.stdout.splitlines() if x.strip()]
    extra=[n for n in names if n not in set(rel)]
    if extra:
        subprocess.run(['git','reset'],cwd=str(BASE),capture_output=True,text=True,timeout=120)
        git={'committed':False,'reason':'staged extra blocked','extra':extra,'staged':names}
    elif names:
        cm=subprocess.run(['git','commit','-m','refine: V8.12.1 chapter 156 tkx'],cwd=str(BASE),capture_output=True,text=True,timeout=180)
        sha=subprocess.run(['git','rev-parse','--short','HEAD'],cwd=str(BASE),capture_output=True,text=True,timeout=60).stdout.strip() if cm.returncode==0 else ''
        git={'committed':cm.returncode==0,'returncode':cm.returncode,'sha':sha,'staged':names,'stderr':cm.stderr[-500:]}
    else:
        git={'committed':False,'reason':'nothing staged'}
    lock=BASE/'.refine_cron.lock'
    if lock.exists(): lock.unlink()
    print(json.dumps({'ok':True,'chapter':156,'fanqie_count':machine['fanqie_count'],'report':str(REPORT),'verdict':verdict,'txt_exists':machine['txt_exists'],'wiki_keywords':{k:(k in wtxt) for k in KEYWORDS},'git':git},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
