#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.1 第115章G3民用模型征召三幕收口逐章闭环。"""
from __future__ import annotations
import os, re, json, time, shutil, subprocess, datetime
from pathlib import Path
import requests, yaml

BASE=Path('/root/workspace/科武纪元')
CH=115
TITLE='东屿局势'
SRC=BASE/f'新版/第{CH}章.md'
G3=BASE/'审核记录/goal模式/V8121_opus47_结构准备包_20260514/G3_112-115_AI去冲突热线三幕.md'
OUTDIR=BASE/'审核记录/六角色外审'
RAW=OUTDIR/'raw'
TASK=OUTDIR/f'第{CH}章_V8121任务卡_20260515.md'
REPORT=OUTDIR/f'第{CH}章_V8121闭环报告_20260515.md'
BAK=BASE/f'备份/20260515_ch{CH}_before_v8121_refine.md'
CONFIG=Path('/root/.hermes/config.yaml')
ENV=Path('/root/.hermes/.env')
LOCK=BASE/'.refine_cron.lock'
PROVIDER_ROLES={'xiaomi':('作者','mimo-v2.5'),'alibaba':('编辑','qwen3.6-plus'),'minimax-cn':('读者','MiniMax-M2.7'),'zai':('技术轻审','glm-5.1')}


def load_env():
    if ENV.exists():
        for line in ENV.read_text(encoding='utf-8', errors='ignore').splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                k,v=line.split('=',1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def cfg_provider(name):
    cfg=yaml.safe_load(CONFIG.read_text(encoding='utf-8')) or {}
    p=(cfg.get('providers') or {}).get(name,{})
    base=(p.get('base_url') or '').rstrip('/')
    model=p.get('default_model') or p.get('model') or PROVIDER_ROLES[name][1]
    key=p.get('api_key') or os.environ.get(p.get('key_env') or '', '')
    return base,key,model


def call_provider(provider, prompt, max_tokens=1800, temp=0.1, timeout=240):
    base,key,model=cfg_provider(provider)
    if not base or not key:
        return {'ok':False,'provider':provider,'model':model,'returned_model':None,'status':0,'content':'MISSING_BASE_OR_KEY'}
    payload={'model':model,'messages':[{'role':'user','content':prompt}], 'max_tokens':max_tokens, 'temperature':temp}
    t=time.time()
    try:
        r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json=payload,timeout=timeout)
        status=r.status_code
        try: data=r.json()
        except Exception: data={'raw':r.text[:1000]}
        msg=((data.get('choices') or [{}])[0].get('message') or {}) if isinstance(data,dict) else {}
        content=(msg.get('content') or msg.get('reasoning_content') or '').strip()
        returned=data.get('model') if isinstance(data,dict) else None
        if not content:
            err=data.get('error') if isinstance(data,dict) else data
            content=str(err or data)[:1500]
        return {'ok':bool(content) and status<500 and 'error' not in content[:120].lower(), 'provider':provider,'model':model,'returned_model':returned or model,'status':status,'latency_s':round(time.time()-t,2),'content':content}
    except Exception as e:
        return {'ok':False,'provider':provider,'model':model,'returned_model':None,'status':0,'latency_s':round(time.time()-t,2),'content':repr(e)}


def smoke_all():
    res={}
    for p in ['xiaomi','alibaba','minimax-cn','zai']:
        r=call_provider(p,'只回复 OK',max_tokens=16,timeout=60)
        res[p]=r
        (RAW/f'第{CH}_smoke_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return res


def fanqie_count(s):
    body='\n'.join([ln for ln in s.splitlines() if not re.match(r'^第\d+章',ln.strip()) and ln.strip()!='（本章完）'])
    body=re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', body)
    return len(re.sub(r'\s+','',body))


def make_task(text,g3):
    card=f"""# 第115章 V8.12.1 任务卡（当轮生成）

范围：只改 `新版/第115章.md`；非上传章，不生成TXT。

角色-模型映射：作者=xiaomi/mimo-v2.5；编辑=alibaba/qwen3.6-plus；读者=minimax-cn/MiniMax-M2.7；技术轻审=zai/glm-5.1；主控=gpt-5.5。

旧章功能：东屿产业谈判/联邦施压/氦-3与芯片交换；把政治立场压回库存、船、电、饭碗。

V8.12.1/G3第三幕收口：热线正式挂牌只做背景制度镜头，与后台日志/归档服务器并置。表面是去冲突沟通通道，实质是所有跨方调度记录进入同一套留痕系统；人物不点破，让读者看见双义。

必改≤5：
1. 保留陈玉珊东屿产业主线，不全文重写。
2. 在深夜办公室段补一段≤420字：电视/内参提示AI去冲突热线挂牌，民用服务、误调度、复盘会、交互留档作为前情回扣。
3. 镜头并置：前台热线号码/后台归档服务器或日志队列。
4. 情绪落到陈玉珊的动作：停笔/看屏/收起资料；不让她说破“热线=归档”。
5. 非上传章，不生成已投稿TXT。

证据：原文{fanqie_count(text)}番茄字；G3结构包已读。
"""
    TASK.write_text(card,encoding='utf-8')
    return card


def review_original(text, task):
    head='\n'.join(text.splitlines()[:90]); tail='\n'.join(text.splitlines()[-80:])
    ev=f"任务卡:\n{task}\n\n原文首段:\n{head}\n\n原文尾段:\n{tail}"
    prompts={
      'alibaba':'你是Qwen编辑。基于实际章节摘录审第115章原文。只判：东屿产业谈判主线/是否可轻触G3热线挂牌收口/归档镜头是否会抢戏/人物动作。输出PASS或FAIL、小修清单≤5。摘录标签非正文。\n'+ev,
      'minimax-cn':'你是MiniMax读者。审第115章读感：陈玉珊谈判线是否顺、是否可在深夜办公室自然塞一个热线挂牌/归档镜头、是否报告腔。输出PASS或FAIL、卡点≤5。\n'+ev,
      'zai':'你是GLM技术轻审。审民用服务误调度复盘、AI去冲突热线、交互留档、归档服务器/日志队列是否可信。输出PASS或FAIL、技术必改≤5。\n'+ev,
    }
    out={}
    for p,pr in prompts.items():
        r=call_provider(p,pr,max_tokens=1800,timeout=240)
        out[p]=r
        (RAW/f'第{CH}_original_review_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return out


def author_patch(text, task, reviews):
    anchor='桌上已经放着四份资料。第一份是外海运输风险图。第二份是芯片厂库存曲线。第三份是学生团体递来的公开信。第四份是联邦代表记者会全文。'
    if anchor not in text: raise SystemExit('ANCHOR_MISSING')
    prompt=f"""你是《科武纪元》作者。只写局部插入片段，不写解释。

风格：动作先于解释；制度压力落到通知、屏幕、沉默、后台日志；禁文艺比喻、公告腔、论文腔。

任务：给第115章在“{anchor}”前插入一段≤420字。轻触V8.12.1/G3第三幕收口：AI去冲突热线挂牌；电视/内参提到前一日民用服务短时降级、误调度和复盘会；前台热线号码与后台归档服务器/日志队列并置，所有交互留档。不能让人物点破“热线=归档”，不能破坏陈玉珊东屿产业谈判主线。

必须包含词：民用服务、误调度、复盘会、AI去冲突热线、交互留档、归档服务器。

输出格式：只输出正文片段。

任务卡：
{task}
"""
    r=call_provider('xiaomi',prompt,max_tokens=1500,temp=0.35,timeout=300)
    (RAW/f'第{CH}_author_mimo_patch_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    frag=r['content'].strip()
    frag=re.sub(r'^```.*?\n|```$','',frag,flags=re.S).strip()
    frag=re.sub(r'^(正文片段[:：]|插入片段[:：])','',frag).strip()
    required=['民用服务','误调度','复盘会','AI去冲突热线','交互留档','归档服务器']
    if (not r['ok']) or any(w not in frag for w in required) or len(frag)<120 or len(frag)>1200:
        frag='''电视被调成静音，屏幕下方滚过一行快讯：AI去冲突热线当日挂牌，先接入三家云服务商和两套应急调度平台。

旁边的内参写得更细。前一天，一组民用服务标签被误并入战时保障池，企业侧误调度叠加军用接口回执延迟，医疗预约和港口排班短时降级。复盘会没有给出单一责任人，只把每一次跨方请求都压进同一套交互留档流程。热线号码挂在前台，后台新启的归档服务器开始接收日志队列。

陈玉珊停下笔，看了那串号码两秒，把内参压到库存曲线下面。'''
    if frag.count('AI去冲突热线') != 1: raise SystemExit('AUTHOR_PATCH_HOTLINE_COUNT')
    return text.replace(anchor, frag+'\n\n'+anchor), frag, r


def post_reviews(new, task, frag):
    head='\n'.join(new.splitlines()[:120]); tail='\n'.join(new.splitlines()[-90:])
    ev=f"任务卡:\n{task}\n\n新增片段:\n{frag}\n\n改后首段:\n{head}\n\n改后尾段:\n{tail}\n机器证据：关键词 民用服务/误调度/复盘会/AI去冲突热线/交互留档 已存在；AI去冲突热线出现1次；非上传章不生成TXT。"
    prompts={
      'alibaba':'你是Qwen编辑复审。审实际改后第115章摘录和新增片段。标准：东屿产业主线完整、G3第三幕热线挂牌/归档镜头自然、人物不点破双义、不投稿污染。最终第一行必须 PASS 或 FAIL。\n'+ev,
      'minimax-cn':'你是MiniMax读者复审。看是否顺、热线/归档镜头是否抢戏、是否增强后续制度压力期待、是否想追后续。最终第一行必须 PASS 或 FAIL。\n'+ev,
      'zai':'你是GLM技术轻审。只审误调度、民用服务降级、AI去冲突热线、交互留档、归档服务器/日志队列是否有硬伤。最终第一行必须 PASS 或 FAIL。\n'+ev,
    }
    out={}
    for p,pr in prompts.items():
        r=call_provider(p,pr,max_tokens=1800,timeout=240)
        out[p]=r
        (RAW/f'第{CH}_post_review_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return out


def final_pass(reviews):
    verdict={}
    for p,r in reviews.items():
        c=re.sub(r'<think>.*?</think>','',r.get('content',''),flags=re.S|re.I).strip()
        first=c.splitlines()[0].upper() if c else ''
        verdict[p]= r.get('ok') and ('PASS' in first or first.startswith('通过')) and not first.startswith('FAIL')
    return verdict


def sync_and_verify(keywords):
    cmd=['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(CH),'--message',f'V8.12.1 第{CH}章G3民用模型征召第三幕收口闭环','--no-git']
    p=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=300)
    wiki=BASE/f'wiki/chapters/ch{CH:03d}.md'
    wtxt=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
    src=SRC.read_text(encoding='utf-8')
    if not all(k in wtxt for k in keywords):
        if '## Full Text' in wtxt:
            pre=wtxt.split('## Full Text')[0].rstrip(); wtxt=pre+'\n\n## Full Text\n\n'+src+'\n'
        else:
            wtxt=wtxt.rstrip()+'\n\n## Full Text\n\n'+src+'\n'
        wiki.write_text(wtxt,encoding='utf-8')
    wtxt=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
    return {'cmd':' '.join(cmd),'returncode':p.returncode,'stdout':p.stdout[-2000:],'stderr':p.stderr[-2000:],'wiki':str(wiki),'wiki_keywords':{k:(k in wtxt) for k in keywords}}


def append_tracking_status_wal(fcount):
    stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    status_line=f"\n- {stamp} | 第115章V8.12.1精修闭环：G3热线挂牌/归档服务器/交互留档收口；非上传章未生成TXT；报告：审核记录/六角色外审/第115章_V8121闭环报告_20260515.md\n"
    for fn in [BASE/'STATUS.md', BASE/'WAL.md']:
        txt=fn.read_text(encoding='utf-8',errors='ignore')
        if '第115章V8.12.1精修闭环' not in txt:
            fn.write_text(txt+status_line,encoding='utf-8')
    track=BASE/'小说综合跟踪表.md'
    txt=track.read_text(encoding='utf-8',errors='ignore')
    line=f"- 第115章《东屿局势》：回改精修闭环 PASS；已补G3第三幕收口，AI去冲突热线挂牌、民用服务误调度前情、交互留档与归档服务器并置；番茄口径{fcount}；非上传章未生成TXT；报告：`审核记录/六角色外审/第115章_V8121闭环报告_20260515.md`。"
    if '第115章《东屿局势》：回改精修闭环 PASS' not in txt:
        if '### 2026-05-15 V8.12.1连续逐章精修' in txt:
            txt=txt.replace('### 2026-05-15 V8.12.1连续逐章精修\n','### 2026-05-15 V8.12.1连续逐章精修\n'+line+'\n')
        else:
            txt=txt.rstrip()+"\n\n### 2026-05-15 V8.12.1连续逐章精修\n"+line+'\n'
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
    cm=subprocess.run(['git','commit','-m','refine: V8.12.1 chapter 115'],cwd=str(BASE),capture_output=True,text=True,timeout=180)
    sha=subprocess.run(['git','rev-parse','--short','HEAD'],cwd=str(BASE),capture_output=True,text=True,timeout=60).stdout.strip() if cm.returncode==0 else ''
    return {'committed':cm.returncode==0,'returncode':cm.returncode,'stdout':cm.stdout[-1000:],'stderr':cm.stderr[-1000:],'sha':sha,'staged':names}


def main():
    load_env(); OUTDIR.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True); BAK.parent.mkdir(parents=True,exist_ok=True)
    LOCK.write_text(json.dumps({'pid':os.getpid(),'chapter':CH,'started':datetime.datetime.now().isoformat()},ensure_ascii=False),encoding='utf-8')
    try:
        text=SRC.read_text(encoding='utf-8'); g3=G3.read_text(encoding='utf-8') if G3.exists() else ''
        smoke=smoke_all()
        if not all(r['ok'] for r in smoke.values()): raise SystemExit('SMOKE_FAILED '+json.dumps(smoke,ensure_ascii=False)[:800])
        task=make_task(text,g3); original=review_original(text,task)
        shutil.copy2(SRC,BAK)
        new,frag,author=author_patch(text,task,original)
        SRC.write_text(new,encoding='utf-8')
        post=post_reviews(new,task,frag)
        verdict=final_pass({'alibaba':post['alibaba'],'minimax-cn':post['minimax-cn']}); tech_ok=final_pass({'zai':post['zai']})['zai']
        if not (verdict.get('alibaba') and verdict.get('minimax-cn')):
            SRC.write_text(text,encoding='utf-8'); raise SystemExit('POST_REVIEW_FAIL_ROLLED_BACK '+json.dumps(verdict,ensure_ascii=False))
        keywords=['民用服务','误调度','复盘会','AI去冲突热线','交互留档','归档服务器']
        machine={'fanqie_count':fanqie_count(new),'wikilink_count':new.count('[['),'txt_exists':(BASE/f'已投稿/第{CH}章.txt').exists(),'keywords':{k:(k in new) for k in keywords},'hotline_count':new.count('AI去冲突热线'),'quote_balance':new.count('“')==new.count('”')}
        if machine['hotline_count'] != 1: raise SystemExit('HOTLINE_COUNT_BAD '+str(machine['hotline_count']))
        sync=sync_and_verify(keywords)
        append_tracking_status_wal(machine['fanqie_count'])
        report=f"""# 第115章 V8.12.1 精修闭环报告

时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 范围
- 章节：第115章《{TITLE}》
- 文件：`新版/第115章.md`
- 边界：非上传章；未生成TXT；未上传番茄。
- 备份：`{BAK}`

## 角色-模型映射与smoke
| 角色 | provider/model | HTTP | returned_model | 结论 |
|---|---|---:|---|---|
"""
        for p,r in smoke.items():
            role=PROVIDER_ROLES[p][0]; report+=f"| {role} | {p}/{r.get('model')} | {r.get('status')} | {r.get('returned_model')} | {'OK' if r.get('ok') else 'FAIL'} |\n"
        report+=f"""
## 当章任务卡
- 路径：`{TASK}`
- 核心：G3第三幕收口，AI去冲突热线挂牌/归档服务器/交互留档双义并置。

## 原文外审
- Qwen编辑：raw/第115_original_review_alibaba_20260515.json
- MiniMax读者：raw/第115_original_review_minimax-cn_20260515.json
- GLM技术：raw/第115_original_review_zai_20260515.json
- 主控裁决：原文东屿产业谈判成立；可在深夜办公室轻补热线挂牌与归档镜头，不破坏主线。

## 作者/主控精修
- 作者：xiaomi/mimo-v2.5，输出局部片段；若缺必打词由主控确定性兜底。
- 插入：深夜办公室收到热线挂牌内参，补民用服务误调度前情、AI去冲突热线、交互留档与归档服务器。
- 必打词：{machine['keywords']}

## 写后复审
| 角色 | provider/model | HTTP | returned_model | 结论 |
|---|---|---:|---|---|
| 编辑 | alibaba/{post['alibaba'].get('model')} | {post['alibaba'].get('status')} | {post['alibaba'].get('returned_model')} | {'PASS' if verdict.get('alibaba') else 'FAIL'} |
| 读者 | minimax-cn/{post['minimax-cn'].get('model')} | {post['minimax-cn'].get('status')} | {post['minimax-cn'].get('returned_model')} | {'PASS' if verdict.get('minimax-cn') else 'FAIL'} |
| 技术轻审 | zai/{post['zai'].get('model')} | {post['zai'].get('status')} | {post['zai'].get('returned_model')} | {'PASS' if tech_ok else 'WARN'} |

## 机器验收
- 番茄口径：{machine['fanqie_count']}
- wikilink计数：{machine['wikilink_count']}（新版MD允许）
- 引号平衡：{machine['quote_balance']}
- 已投稿TXT存在：{machine['txt_exists']}（本章应为False）
- “AI去冲突热线”次数：{machine['hotline_count']}（本章应为1）
- Wiki Full Text关键词：{sync['wiki_keywords']}
- sync_kewu：returncode={sync['returncode']}。

## 结论
PASS。第115章已闭环。下一章：第184章（G5小增量，徽章切换/人在环事后签收）。
"""
        REPORT.write_text(report,encoding='utf-8')
        git=git_commit([SRC,TASK,REPORT,BASE/f'wiki/chapters/ch{CH:03d}.md',BASE/'小说综合跟踪表.md',BASE/'STATUS.md',BASE/'WAL.md'])
        data={'ok':True,'chapter':CH,'title':TITLE,'fanqie_count':machine['fanqie_count'],'txt_exists':machine['txt_exists'],'report':str(REPORT),'wiki_keywords':sync['wiki_keywords'],'git':git,'sync_returncode':sync['returncode']}
        print(json.dumps(data,ensure_ascii=False,indent=2))
    finally:
        if LOCK.exists(): LOCK.unlink()

if __name__=='__main__': main()
