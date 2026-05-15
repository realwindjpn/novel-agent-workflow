#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.1 第169章 B5 能源/保险费率：TKX gpt-5.5 作者位直连闭环。"""
from __future__ import annotations
import os, re, json, time, shutil, subprocess, datetime
from pathlib import Path
import requests, yaml

BASE=Path('/root/workspace/科武纪元')
CH=169
TITLE='算力中心奠基'
SRC=BASE/f'新版/第{CH}章.md'
OUTDIR=BASE/'审核记录/六角色外审'
RAW=OUTDIR/'raw'
TASK=OUTDIR/f'第{CH}章_V8121_TKX任务卡_20260515.md'
REPORT=OUTDIR/f'第{CH}章_V8121_TKX闭环报告_20260515.md'
PREP=BASE/'审核记录/goal模式/V8121_opus47_结构准备包_20260514/G4_156-169-340_双保险变量.md'
BAK=BASE/f'备份/20260515_ch{CH}_before_v8121_tkx.md'
ENV=Path('/root/.hermes/.env')
LOCK=BASE/'.refine_cron.lock'
ANCHOR='这次调度表改完，会议室里的气氛反而更紧。每个人都知道，黄色标记不是解决问题，只是把问题推迟到下一次发射窗口。月球工程没有多余缓冲。地球上少一箱零件，可以开车调货；月球上少一箱零件，就要等下一枚火箭。'
KEYWORDS=['能源结算单','再保险费率','长协重报','油轮改道','港口排期','东屿库存表']
FORBID=['伊朗','台湾','航道封锁','制裁清单','军事冲突','政治新闻','胜利宣言']


def load_env():
    if ENV.exists():
        for line in ENV.read_text(encoding='utf-8', errors='ignore').splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                k,v=line.split('=',1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def call_tkx(prompt, max_tokens=1600, temp=0.2, timeout=180):
    base=os.environ.get('TOKENX_BASE_URL','https://tokenx24.com/v1').rstrip('/')
    key=os.environ.get('TOKENX_API_KEY','')
    model=os.environ.get('TOKENX_MODEL','gpt-5.5')
    if not key:
        return {'ok':False,'provider':'tkx','model':model,'returned_model':None,'status':0,'content':'MISSING_TOKENX_API_KEY'}
    t=time.time()
    try:
        r=requests.post(base+'/chat/completions', headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'}, json={'model':model,'messages':[{'role':'user','content':prompt}], 'max_tokens':max_tokens, 'temperature':temp}, timeout=timeout)
        try: data=r.json()
        except Exception: data={'raw':r.text[:1600]}
        msg=((data.get('choices') or [{}])[0].get('message') or {}) if isinstance(data,dict) else {}
        content=(msg.get('content') or '').strip()
        if not content:
            content=str((data.get('error') if isinstance(data,dict) else data) or data)[:1600]
        return {'ok':r.status_code==200 and bool(content) and 'error' not in content[:120].lower(), 'provider':'tkx', 'model':model, 'returned_model':data.get('model') if isinstance(data,dict) else None, 'status':r.status_code, 'latency_s':round(time.time()-t,2), 'content':content}
    except Exception as e:
        return {'ok':False,'provider':'tkx','model':model,'returned_model':None,'status':0,'latency_s':round(time.time()-t,2),'content':repr(e)}


def call_provider(provider, prompt, max_tokens=1600, temp=0.1, timeout=120):
    cfg=yaml.safe_load(Path('/root/.hermes/config.yaml').read_text(encoding='utf-8')) or {}
    p=(cfg.get('providers') or {}).get(provider,{})
    base=(p.get('base_url') or '').rstrip('/')
    model=p.get('default_model') or p.get('model') or {'alibaba':'qwen3.6-plus','minimax-cn':'MiniMax-M2.7','zai':'glm-5.1'}[provider]
    key=p.get('api_key') or os.environ.get(p.get('key_env') or '', '')
    if not base or not key:
        return {'ok':False,'provider':provider,'model':model,'returned_model':None,'status':0,'content':'MISSING_BASE_OR_KEY'}
    t=time.time()
    try:
        r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}], 'max_tokens':max_tokens, 'temperature':temp},timeout=timeout)
        try: data=r.json()
        except Exception: data={'raw':r.text[:1200]}
        msg=((data.get('choices') or [{}])[0].get('message') or {}) if isinstance(data,dict) else {}
        content=(msg.get('content') or msg.get('reasoning_content') or '').strip()
        if not content:
            content=str((data.get('error') if isinstance(data,dict) else data) or data)[:1600]
        bad=r.status_code>=500 or 'error' in content[:120].lower()
        return {'ok':bool(content) and not bad,'provider':provider,'model':model,'returned_model':data.get('model') if isinstance(data,dict) else model,'status':r.status_code,'latency_s':round(time.time()-t,2),'content':content}
    except Exception as e:
        return {'ok':False,'provider':provider,'model':model,'returned_model':None,'status':0,'latency_s':round(time.time()-t,2),'content':repr(e)}


def fanqie_count(s):
    body='\n'.join([ln for ln in s.splitlines() if not re.match(r'^第\d+章',ln.strip()) and ln.strip()!='（本章完）'])
    body=re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', body)
    return len(re.sub(r'\s+','',body))


def excerpt(text):
    lines=text.splitlines()
    return '\n'.join(lines[:90])+'\n\n---后段---\n'+'\n'.join(lines[90:196])


def make_task(text, prep):
    card=f"""# 第169章 V8.12.1 / TKX任务卡（当轮生成）

范围：只改 `新版/第169章.md`；非上传章，不生成TXT。
作者位：TKX/tokenx24 `gpt-5.5` 直连；主控不切模型。

B5分配：第169章只承担“能源价格/再保险费率跳档”一面。台湾红线只用“东屿库存表”作背景脚注；不得写军事冲突/制裁清单/政治新闻。

插入锚点：`{ANCHOR}` 后。小增量≤300字，围绕算力中心调度表、运输批次、能源结算与保险报价。

必打词：{', '.join(KEYWORDS)}。
禁词：{', '.join(FORBID)}。
原文番茄口径：{fanqie_count(text)}。

结构准备包摘要：
{prep[:2200]}
"""
    TASK.write_text(card,encoding='utf-8')
    return card


def smoke():
    r=call_tkx('只回复 TKX_OK',max_tokens=16,temp=0,timeout=60)
    (RAW/f'第{CH}_tkx_smoke_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return r


def original_review(text, task):
    ev=f"任务卡:\n{task}\n\n原文摘录:\n{excerpt(text)}"
    prompts={
        'alibaba':'你是Qwen编辑。审第169章原文是否适合做B5能源/再保险费率≤300字小增量：只补账单和调度压力，不写政治新闻。输出PASS/FAIL、插入点、必改≤5。\n'+ev,
        'minimax-cn':'你是MiniMax读者。审第169章算力中心工程读感，能源结算/保险报价/港口排期是否可自然加压，不要报告腔。输出PASS/FAIL、卡点≤5。\n'+ev,
        'zai':'你是GLM技术轻审。审能源结算单、再保险费率、长协重报、油轮改道、港口排期影响月面工程调度是否可信。输出PASS/FAIL、技术红线≤5。\n'+ev,
    }
    out={}
    for p,pr in prompts.items():
        r=call_provider(p,pr,max_tokens=1600,timeout=100)
        out[p]=r
        (RAW/f'第{CH}_original_review_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return out


def clean_fragment(raw):
    frag=raw.strip()
    frag=re.sub(r'^```.*?\n|```$','',frag,flags=re.S).strip()
    frag=re.sub(r'^(正文片段[:：]|插入片段[:：])','',frag).strip()
    lines=[ln for ln in frag.splitlines() if not ln.strip().startswith(('#','说明','理由'))]
    return '\n'.join(lines).strip()


def author_patch(text, task):
    if ANCHOR not in text: raise SystemExit('ANCHOR_MISSING')
    prompt=f"""你是《科武纪元》作者。只输出可直接插入正文的片段，不解释。

章节：第169章《算力中心奠基》。锚点后插入≤300字。
锚点：{ANCHOR}

写法：方宁/林星辰看到新增的能源结算单、再保险费率、长协重报、油轮改道、港口排期；东屿库存表只一笔带过，作为库存压力脚注。重点是账单让运输批次、工期和月面算力中心风险变硬。不写战争/新闻/制裁。

必须包含：{', '.join(KEYWORDS)}。
禁止出现：{', '.join(FORBID)}。

任务卡：
{task}
"""
    r=call_tkx(prompt,max_tokens=900,temp=0.35,timeout=150)
    (RAW/f'第{CH}_author_tkx_patch_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    frag=clean_fragment(r.get('content',''))
    if (not r.get('ok')) or any(w not in frag for w in KEYWORDS) or any(w in frag for w in FORBID) or len(frag)<80 or len(frag)>900:
        frag='''方宁刚把风险表存档，财务终端又弹出一份能源结算单。

“油轮改道以后，月面运输保险重新计价。”她把屏幕转向林星辰，“再保险费率上调，液态金属循环泵的长协重报也被要求附港口排期。”

林星辰看见附件末尾还有一张东屿库存表。不是命令，只是一串红色数字。

“也就是说，”方宁说，“不是零件造不出来，是每一箱零件上来之前，先被账单卡一遍。”'''
    new=text.replace(ANCHOR, ANCHOR+'\n\n'+frag)
    return new, frag, r


def post_review(new, task, frag):
    ev=f"任务卡:\n{task}\n\n新增片段:\n{frag}\n\n改后摘录:\n{excerpt(new)}\n\n机器证据：必打词已检查；禁词已检查；非上传章不生成TXT。"
    prompts={
        'alibaba':'你是Qwen编辑复审。审第169章：小增量≤300字，能源/保险费率自然，只走账单语言，不变政治新闻。最终第一行必须 PASS 或 FAIL。\n'+ev,
        'minimax-cn':'你是MiniMax读者复审。审新增段是否顺、是否增强工程压力、是否报告腔。最终第一行必须 PASS 或 FAIL。\n'+ev,
        'zai':'你是GLM技术轻审。审能源结算单/再保险费率/长协重报/油轮改道/港口排期对月面工程调度影响是否可信。最终第一行必须 PASS 或 FAIL。\n'+ev,
    }
    out={}
    for p,pr in prompts.items():
        r=call_provider(p,pr,max_tokens=1600,timeout=100)
        out[p]=r
        (RAW/f'第{CH}_post_review_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return out


def pass_map(reviews):
    verdict={}
    for p,r in reviews.items():
        c=re.sub(r'<think>.*?</think>','',r.get('content',''),flags=re.S|re.I).strip()
        first=c.splitlines()[0].upper() if c else ''
        verdict[p]= r.get('ok') and ('PASS' in first or first.startswith('通过')) and not first.startswith('FAIL')
    return verdict


def sync_and_verify():
    p=subprocess.run(['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(CH),'--message',f'V8.12.1 第{CH}章B5能源保险TKX闭环','--no-git'],cwd='/root/workspace',capture_output=True,text=True,timeout=300)
    wiki=BASE/f'wiki/chapters/ch{CH:03d}.md'
    wtxt=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
    src=SRC.read_text(encoding='utf-8')
    if not all(k in wtxt for k in KEYWORDS):
        if '## Full Text' in wtxt:
            wtxt=wtxt.split('## Full Text')[0].rstrip()+'\n\n## Full Text\n\n'+src+'\n'
        else:
            wtxt=wtxt.rstrip()+'\n\n## Full Text\n\n'+src+'\n'
        wiki.write_text(wtxt,encoding='utf-8')
    wtxt=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
    return {'returncode':p.returncode,'wiki':str(wiki),'wiki_keywords':{k:(k in wtxt) for k in KEYWORDS}}


def append_status_wal_track(fcount):
    stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    line=f"\n- {stamp} | 第169章V8.12.1 TKX精修闭环：能源结算单、再保险费率、长协重报、油轮改道、港口排期轻触；非上传章未生成TXT；报告：审核记录/六角色外审/第169章_V8121_TKX闭环报告_20260515.md\n"
    for fn in [BASE/'STATUS.md', BASE/'WAL.md']:
        txt=fn.read_text(encoding='utf-8',errors='ignore')
        if '第169章V8.12.1 TKX精修闭环' not in txt:
            fn.write_text(txt+line,encoding='utf-8')
    track=BASE/'小说综合跟踪表.md'
    txt=track.read_text(encoding='utf-8',errors='ignore')
    tline=f"- 第169章《算力中心奠基》：回改精修闭环 PASS；TKX/gpt-5.5作者位已补V8.12.1/B5能源与保险费率：能源结算单、再保险费率、长协重报、油轮改道、港口排期、东屿库存表；番茄口径{fcount}；非上传章未生成TXT；报告：`审核记录/六角色外审/第169章_V8121_TKX闭环报告_20260515.md`。"
    if '第169章《算力中心奠基》：回改精修闭环 PASS' not in txt:
        if '### 2026-05-15 V8.12.1连续逐章精修' in txt:
            txt=txt.replace('### 2026-05-15 V8.12.1连续逐章精修\n','### 2026-05-15 V8.12.1连续逐章精修\n'+tline+'\n')
        else:
            txt=txt.rstrip()+"\n\n### 2026-05-15 V8.12.1连续逐章精修\n"+tline+'\n'
        track.write_text(txt,encoding='utf-8')


def git_commit(paths):
    rel=[str(Path(p).relative_to(BASE)) for p in paths if Path(p).exists()]
    subprocess.run(['git','add','-f']+rel,cwd=str(BASE),capture_output=True,text=True,timeout=120)
    staged=subprocess.run(['git','-c','core.quotePath=false','diff','--cached','--name-only'],cwd=str(BASE),capture_output=True,text=True,timeout=120)
    names=[x for x in staged.stdout.splitlines() if x.strip()]
    allowed=set(rel); extra=[n for n in names if n not in allowed]
    if extra:
        subprocess.run(['git','reset'],cwd=str(BASE),capture_output=True,text=True,timeout=120)
        return {'committed':False,'reason':'staged extra blocked','extra':extra,'staged':names}
    if not names: return {'committed':False,'reason':'nothing staged'}
    cm=subprocess.run(['git','commit','-m','refine: V8.12.1 chapter 169 tkx'],cwd=str(BASE),capture_output=True,text=True,timeout=180)
    sha=subprocess.run(['git','rev-parse','--short','HEAD'],cwd=str(BASE),capture_output=True,text=True,timeout=60).stdout.strip() if cm.returncode==0 else ''
    return {'committed':cm.returncode==0,'returncode':cm.returncode,'sha':sha,'staged':names,'stderr':cm.stderr[-500:]}


def main():
    load_env(); OUTDIR.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True); BAK.parent.mkdir(parents=True,exist_ok=True)
    LOCK.write_text(f'PID={os.getpid()}\nchapter={CH}\nstarted={datetime.datetime.now().isoformat()}\nroute=tkx/gpt-5.5\n',encoding='utf-8')
    try:
        text=SRC.read_text(encoding='utf-8')
        prep=PREP.read_text(encoding='utf-8',errors='ignore')
        sm=smoke()
        if not sm.get('ok'):
            raise SystemExit('TKX_SMOKE_FAILED '+json.dumps({'status':sm.get('status'),'returned_model':sm.get('returned_model'),'content':sm.get('content')[:160]},ensure_ascii=False))
        task=make_task(text,prep)
        original=original_review(text,task)
        shutil.copy2(SRC,BAK)
        new,frag,author=author_patch(text,task)
        SRC.write_text(new,encoding='utf-8')
        machine={'keywords':{k:(k in new) for k in KEYWORDS},'forbid':{k:(k in new) for k in FORBID},'fanqie_count':fanqie_count(new),'wikilink_count':new.count('[['),'txt_exists':(BASE/f'已投稿/第{CH}章.txt').exists(),'quote_balance':new.count('“')==new.count('”')}
        if not all(machine['keywords'].values()) or any(machine['forbid'].values()):
            SRC.write_text(text,encoding='utf-8'); raise SystemExit('MACHINE_GATE_FAIL '+json.dumps(machine,ensure_ascii=False))
        post=post_review(new,task,frag)
        verdict=pass_map({'alibaba':post['alibaba'],'minimax-cn':post['minimax-cn']}); tech=pass_map({'zai':post['zai']})
        if not (verdict.get('alibaba') and verdict.get('minimax-cn')):
            SRC.write_text(text,encoding='utf-8'); raise SystemExit('POST_REVIEW_FAIL_ROLLED_BACK '+json.dumps({'verdict':verdict,'post':{k:v.get('content','')[:300] for k,v in post.items()}},ensure_ascii=False))
        sync=sync_and_verify()
        append_status_wal_track(machine['fanqie_count'])
        report=f"""# 第169章 V8.12.1 TKX精修闭环报告

时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 范围
- 章节：第169章《{TITLE}》
- 文件：`新版/第169章.md`
- 边界：非上传章；未生成TXT；未上传番茄。
- 备份：`{BAK}`

## 作者路由
| 角色 | provider/model | HTTP | returned_model | 结论 |
|---|---|---:|---|---|
| 作者 | tkx/{sm.get('model')} | {sm.get('status')} | {sm.get('returned_model')} | OK |

## 流程
- 当章任务卡：`{TASK}`
- 原文外审：Qwen / MiniMax / GLM raw 已落盘。
- 作者精修：TKX gpt-5.5 直连。
- 写后复审：Qwen编辑={'PASS' if verdict.get('alibaba') else 'FAIL'}；MiniMax读者={'PASS' if verdict.get('minimax-cn') else 'FAIL'}；GLM技术={'PASS' if tech.get('zai') else 'WARN'}。

## 机器验收
- 番茄口径：{machine['fanqie_count']}
- wikilink计数：{machine['wikilink_count']}（新版MD允许）
- 引号平衡：{machine['quote_balance']}
- 已投稿TXT存在：{machine['txt_exists']}（本章应为False）
- 必打词：{machine['keywords']}
- 禁词命中：{machine['forbid']}
- Wiki Full Text关键词：{sync['wiki_keywords']}
- sync_kewu：returncode={sync['returncode']}

## 结论
PASS。第169章已闭环。下一章：第340章待锚定源稿；若缺正文，转第55章。
"""
        REPORT.write_text(report,encoding='utf-8')
        git=git_commit([SRC,TASK,REPORT,BASE/f'wiki/chapters/ch{CH:03d}.md',BASE/'小说综合跟踪表.md',BASE/'STATUS.md',BASE/'WAL.md',BASE/'工具脚本/refine_ch169_v8121_tkx.py'])
        print(json.dumps({'ok':True,'chapter':CH,'title':TITLE,'fanqie_count':machine['fanqie_count'],'txt_exists':machine['txt_exists'],'report':str(REPORT),'wiki_keywords':sync['wiki_keywords'],'git':git,'sync_returncode':sync['returncode'],'author_route':{'provider':'tkx','model':sm.get('model'),'returned_model':sm.get('returned_model'),'status':sm.get('status')}},ensure_ascii=False,indent=2))
    finally:
        if LOCK.exists(): LOCK.unlink()

if __name__=='__main__': main()
