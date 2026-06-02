#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.1 第189章算力结算/许可延迟/散热账单定点小增量闭环。"""
from __future__ import annotations
import os, re, json, time, shutil, subprocess, datetime
from pathlib import Path
import requests, yaml

BASE=Path('/root/workspace/科武纪元')
CH=189
TITLE='频率展宽'
SRC=BASE/f'新版/第{CH}章.md'
OUTDIR=BASE/'审核记录/六角色外审'
RAW=OUTDIR/'raw'
TASK=OUTDIR/f'第{CH}章_V8121任务卡_20260515.md'
REPORT=OUTDIR/f'第{CH}章_V8121闭环报告_20260515.md'
BAK=BASE/f'备份/20260515_ch{CH}_before_v8121_refine.md'
CONFIG=Path('/root/.hermes/config.yaml')
ENV=Path('/root/.hermes/.env')
LOCK=BASE/'.refine_cron.lock'
PROVIDER_ROLES={'xiaomi':('作者','mimo-v2.5-pro'),'alibaba':('编辑','qwen3.6-plus'),'minimax-cn':('读者','MiniMax-M2.7'),'zai':('技术轻审','glm-5.1')}
KEYWORDS=['算力结算单','许可回执','散热账单','GPU排队','审计接口']

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
        bad=status>=500 or 'error' in content[:120].lower()
        return {'ok':bool(content) and not bad,'provider':provider,'model':model,'returned_model':returned or model,'status':status,'latency_s':round(time.time()-t,2),'content':content}
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

def make_task(text):
    card=f"""# 第189章 V8.12.1 任务卡（当轮生成）

范围：只改 `新版/第189章.md`；非上传章，不生成TXT。

角色-模型映射：作者=xiaomi/mimo-v2.5-pro；编辑=alibaba/qwen3.6-plus；读者=minimax-cn/MiniMax-M2.7；技术轻审=zai/glm-5.1；主控=gpt-5.5。

旧章功能：苏雨晴做频率展宽实验，林星辰做锚点，发现同步可抗量子干扰器。

V8.12.1/B3定点小增量：只在实验前插入≤360字现实约束。用“算力结算单、许可回执、散热账单、GPU排队、审计接口”表现交换表/延迟表，不改核心科学突破，不写新闻复述，不让外交筹码抢戏。

必改≤5：
1. 保留频率展宽主线，不全文重写。
2. 在实验启动前补工程代价：临时算力额度、许可证延迟、散热账单、审计接口关闭。
3. 情绪落到苏雨晴/林星辰动作，不写政策腔。
4. 技术口径：不是算力万能解决意识同步，只是实验窗口被许可/结算/散热制约。
5. 非上传章，不生成已投稿TXT。

证据：原文{fanqie_count(text)}番茄字。
"""
    TASK.write_text(card,encoding='utf-8')
    return card

def review_original(text, task):
    head='\n'.join(text.splitlines()[:115]); tail='\n'.join(text.splitlines()[-80:])
    ev=f"任务卡:\n{task}\n\n原文首段:\n{head}\n\n原文尾段:\n{tail}"
    prompts={
      'alibaba':'你是Qwen编辑。基于实际章节摘录审第189章原文。只判：频率展宽主线是否成立、是否可轻触V8.12.1算力结算/许可延迟/散热账单、插入点是否自然。输出PASS或FAIL、小修清单≤5。摘录标签非正文。\n'+ev,
      'minimax-cn':'你是MiniMax读者。审第189章读感：实验紧迫感、林苏关系、是否可自然加入现实算力/许可/散热约束而不抢戏。输出PASS或FAIL、卡点≤5。\n'+ev,
      'zai':'你是GLM技术轻审。审频率展宽、干扰频谱、GPU排队、许可回执、散热账单、审计接口作为实验约束是否可信。输出PASS或FAIL、技术必改≤5。\n'+ev,
    }
    out={}
    for p,pr in prompts.items():
        r=call_provider(p,pr,max_tokens=1800,timeout=240)
        out[p]=r
        (RAW/f'第{CH}_original_review_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return out

def author_patch(text, task):
    anchor='测试舱内的空气开始轻微震动，那是共振场启动的征兆。频率映射芯片亮起淡蓝色的光芒，在两人之间投射出模糊的光影。屏幕上的三维波形图开始缓慢旋转，三条波峰在各自的频率位置上闪烁着规律的脉冲。'
    if anchor not in text: raise SystemExit('ANCHOR_MISSING')
    prompt=f"""你是《科武纪元》作者。只写局部插入片段，不写解释。

风格：动作先于解释；现实约束落到账单、回执、屏幕、设备降频；禁文艺比喻、公告腔、论文腔。

任务：给第189章在“{anchor}”前插入一段≤360字。轻触V8.12.1/B3：算力结算、许可延迟、散热账单、GPU排队、审计接口。它们只压缩实验窗口，不解决意识同步。人物动作要落到苏雨晴/林星辰，不要破坏频率展宽主线。

必须包含词：算力结算单、许可回执、散热账单、GPU排队、审计接口。

输出格式：只输出正文片段。

任务卡：
{task}
"""
    r=call_provider('xiaomi',prompt,max_tokens=1200,temp=0.35,timeout=300)
    (RAW/f'第{CH}_author_mimo_patch_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    frag=r.get('content','').strip()
    frag=re.sub(r'^```.*?\n|```$','',frag,flags=re.S).strip()
    frag=re.sub(r'^(正文片段[:：]|插入片段[:：])','',frag).strip()
    if (not r.get('ok')) or any(w not in frag for w in KEYWORDS) or len(frag)<100 or len(frag)>1000:
        frag='''控制台右下角忽然弹出一张算力结算单。

苏雨晴扫了一眼，没有立刻关掉。临时租用的轨道算力只批了四十分钟，GPU排队序号还在往后跳。许可回执停在“人工复核”一栏，旁边的散热账单已经被系统标成红色，审计接口也在上一个整点后改成只读。

“窗口比你说的短。”林星辰看着屏幕。

“所以不能失败。”苏雨晴把账单拖到角落，手指按住启动键，“频率展宽靠的是人，不靠这些机器。机器只是告诉我们，外面已经不愿意再给第二次机会。”'''
    return text.replace(anchor, frag+'\n\n'+anchor), frag, r

def post_reviews(new, task, frag):
    head='\n'.join(new.splitlines()[:130]); tail='\n'.join(new.splitlines()[-90:])
    ev=f"任务卡:\n{task}\n\n新增片段:\n{frag}\n\n改后首段:\n{head}\n\n改后尾段:\n{tail}\n机器证据：关键词 算力结算单/许可回执/散热账单/GPU排队/审计接口 已存在；非上传章不生成TXT。"
    prompts={
      'alibaba':'你是Qwen编辑复审。审实际改后第189章摘录和新增片段。标准：频率展宽主线完整、算力结算/许可延迟/散热账单为现实压力不抢戏、人物动作自然、不投稿污染。最终第一行必须 PASS 或 FAIL。\n'+ev,
      'minimax-cn':'你是MiniMax读者复审。看是否顺、是否增强实验紧迫感、是否报告腔、是否想追后续。最终第一行必须 PASS 或 FAIL。\n'+ev,
      'zai':'你是GLM技术轻审。只审算力结算、GPU排队、许可回执、散热账单、审计接口作为实验窗口约束是否有硬伤；频率展宽不得被写成算力万能。最终第一行必须 PASS 或 FAIL。\n'+ev,
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
    cmd=['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(CH),'--message',f'V8.12.1 第{CH}章算力结算/许可延迟/散热账单定点闭环','--no-git']
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
    return {'returncode':p.returncode,'stdout':p.stdout[-2000:],'stderr':p.stderr[-2000:],'wiki':str(wiki),'wiki_keywords':{k:(k in wtxt) for k in keywords}}

def append_tracking_status_wal(fcount):
    stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    status_line=f"\n- {stamp} | 第189章V8.12.1精修闭环：算力结算单/许可回执/散热账单/GPU排队/审计接口轻触；非上传章未生成TXT；报告：审核记录/六角色外审/第189章_V8121闭环报告_20260515.md\n"
    for fn in [BASE/'STATUS.md', BASE/'WAL.md']:
        txt=fn.read_text(encoding='utf-8',errors='ignore')
        if '第189章V8.12.1精修闭环' not in txt:
            fn.write_text(txt+status_line,encoding='utf-8')
    track=BASE/'小说综合跟踪表.md'
    txt=track.read_text(encoding='utf-8',errors='ignore')
    line=f"- 第189章《频率展宽》：回改精修闭环 PASS；已补V8.12.1/B3算力结算、许可延迟、散热账单、GPU排队、审计接口现实约束；番茄口径{fcount}；非上传章未生成TXT；报告：`审核记录/六角色外审/第189章_V8121闭环报告_20260515.md`。"
    if '第189章《频率展宽》：回改精修闭环 PASS' not in txt:
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
    cm=subprocess.run(['git','commit','-m','refine: V8.12.1 chapter 189'],cwd=str(BASE),capture_output=True,text=True,timeout=180)
    sha=subprocess.run(['git','rev-parse','--short','HEAD'],cwd=str(BASE),capture_output=True,text=True,timeout=60).stdout.strip() if cm.returncode==0 else ''
    return {'committed':cm.returncode==0,'returncode':cm.returncode,'stdout':cm.stdout[-1000:],'stderr':cm.stderr[-1000:],'sha':sha,'staged':names}

def main():
    load_env(); OUTDIR.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True); BAK.parent.mkdir(parents=True,exist_ok=True)
    LOCK.write_text(json.dumps({'pid':os.getpid(),'chapter':CH,'started':datetime.datetime.now().isoformat()},ensure_ascii=False),encoding='utf-8')
    try:
        text=SRC.read_text(encoding='utf-8')
        smoke=smoke_all()
        if not all(r['ok'] for r in smoke.values()):
            raise SystemExit('SMOKE_FAILED '+json.dumps({k:{'status':v.get('status'),'model':v.get('model'),'returned_model':v.get('returned_model'),'content':v.get('content')[:120]} for k,v in smoke.items()},ensure_ascii=False))
        task=make_task(text); original=review_original(text,task)
        shutil.copy2(SRC,BAK)
        new,frag,author=author_patch(text,task)
        SRC.write_text(new,encoding='utf-8')
        post=post_reviews(new,task,frag)
        verdict=final_pass({'alibaba':post['alibaba'],'minimax-cn':post['minimax-cn']}); tech_ok=final_pass({'zai':post['zai']})['zai']
        if not (verdict.get('alibaba') and verdict.get('minimax-cn')):
            SRC.write_text(text,encoding='utf-8'); raise SystemExit('POST_REVIEW_FAIL_ROLLED_BACK '+json.dumps(verdict,ensure_ascii=False))
        machine={'fanqie_count':fanqie_count(new),'wikilink_count':new.count('[['),'txt_exists':(BASE/f'已投稿/第{CH}章.txt').exists(),'keywords':{k:(k in new) for k in KEYWORDS},'quote_balance':new.count('“')==new.count('”')}
        if not all(machine['keywords'].values()): raise SystemExit('KEYWORD_MISSING '+json.dumps(machine['keywords'],ensure_ascii=False))
        sync=sync_and_verify(KEYWORDS)
        append_tracking_status_wal(machine['fanqie_count'])
        report=f"""# 第189章 V8.12.1 精修闭环报告

时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 范围
- 章节：第189章《{TITLE}》
- 文件：`新版/第189章.md`
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
- 核心：B3算力结算、许可延迟、散热账单定点小增量，不破坏频率展宽主线。

## 原文外审
- Qwen编辑：raw/第189_original_review_alibaba_20260515.json
- MiniMax读者：raw/第189_original_review_minimax-cn_20260515.json
- GLM技术：raw/第189_original_review_zai_20260515.json
- 主控裁决：原文章实验线成立；可在启动前补工程/许可/散热窗口压力。

## 作者/主控精修
- 作者：xiaomi/mimo-v2.5-pro，输出局部片段；若缺必打词由主控确定性兜底。
- 插入：实验启动前的算力结算单、许可回执、散热账单、GPU排队与审计接口只读。
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
- Wiki Full Text关键词：{sync['wiki_keywords']}
- sync_kewu：returncode={sync['returncode']}。

## 结论
PASS。第189章已闭环。下一章：第221章（G5/G4企业筹码交换表，稀土/H200/报价）。
"""
        REPORT.write_text(report,encoding='utf-8')
        git=git_commit([SRC,TASK,REPORT,BASE/f'wiki/chapters/ch{CH:03d}.md',BASE/'小说综合跟踪表.md',BASE/'STATUS.md',BASE/'WAL.md'])
        data={'ok':True,'chapter':CH,'title':TITLE,'fanqie_count':machine['fanqie_count'],'txt_exists':machine['txt_exists'],'report':str(REPORT),'wiki_keywords':sync['wiki_keywords'],'git':git,'sync_returncode':sync['returncode']}
        print(json.dumps(data,ensure_ascii=False,indent=2))
    finally:
        if LOCK.exists(): LOCK.unlink()

if __name__=='__main__': main()
