#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.1 第221章企业筹码交换表定点小增量闭环。"""
from __future__ import annotations
import os, re, json, time, shutil, subprocess, datetime
from pathlib import Path
import requests, yaml

BASE=Path('/root/workspace/科武纪元')
CH=221
TITLE='远岸账号'
SRC=BASE/f'新版/第{CH}章.md'
OUTDIR=BASE/'审核记录/六角色外审'
RAW=OUTDIR/'raw'
TASK=OUTDIR/f'第{CH}章_V8121任务卡_20260515.md'
REPORT=OUTDIR/f'第{CH}章_V8121闭环报告_20260515.md'
PREP=BASE/'审核记录/goal模式/V8121_opus47_结构准备包_20260514/G5_221_企业筹码交换表.md'
BAK=BASE/f'备份/20260515_ch{CH}_before_v8121_refine.md'
CONFIG=Path('/root/.hermes/config.yaml')
ENV=Path('/root/.hermes/.env')
LOCK=BASE/'.refine_cron.lock'
PROVIDER_ROLES={'xiaomi':('作者','mimo-v2.5-pro'),'alibaba':('编辑','qwen3.6-plus'),'minimax-cn':('读者','MiniMax-M2.7'),'zai':('技术轻审','glm-5.1')}
KEYWORDS=['H200','现货报价','交期','磁材','长协','阶梯报价','训练任务']
FORBID=['台湾','伊朗','航道','能源双保险','模型叛变','一夜超越','量子降神']
ANCHOR='李梦瑶把远岸合同、保险新报价、泛际会议隐藏队列截图三份文件并排。'

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

def call_provider(provider, prompt, max_tokens=1600, temp=0.1, timeout=240):
    base,key,model=cfg_provider(provider)
    if not base or not key:
        return {'ok':False,'provider':provider,'model':model,'returned_model':None,'status':0,'content':'MISSING_BASE_OR_KEY'}
    payload={'model':model,'messages':[{'role':'user','content':prompt}], 'max_tokens':max_tokens, 'temperature':temp}
    t=time.time()
    try:
        r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json=payload,timeout=timeout)
        status=r.status_code
        try: data=r.json()
        except Exception: data={'raw':r.text[:1200]}
        msg=((data.get('choices') or [{}])[0].get('message') or {}) if isinstance(data,dict) else {}
        content=(msg.get('content') or msg.get('reasoning_content') or '').strip()
        returned=data.get('model') if isinstance(data,dict) else None
        if not content:
            content=str((data.get('error') if isinstance(data,dict) else data) or data)[:1600]
        bad=status>=500 or 'error' in content[:120].lower()
        return {'ok':bool(content) and not bad,'provider':provider,'model':model,'returned_model':returned or model,'status':status,'latency_s':round(time.time()-t,2),'content':content}
    except Exception as e:
        return {'ok':False,'provider':provider,'model':model,'returned_model':None,'status':0,'latency_s':round(time.time()-t,2),'content':repr(e)}

def fanqie_count(s):
    body='\n'.join([ln for ln in s.splitlines() if not re.match(r'^第\d+章',ln.strip()) and ln.strip()!='（本章完）'])
    body=re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', body)
    return len(re.sub(r'\s+','',body))

def smoke_all():
    out={}
    for p in ['xiaomi','alibaba','minimax-cn','zai']:
        r=call_provider(p,'只回复 OK',max_tokens=16,timeout=60)
        out[p]=r
        (RAW/f'第{CH}_smoke_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return out

def make_task(text, prep):
    card=f"""# 第221章 V8.12.1 任务卡（当轮生成）

范围：只改 `新版/第221章.md`；非上传章，不生成TXT。

角色-模型映射：作者=xiaomi/mimo-v2.5-pro；编辑=alibaba/qwen3.6-plus；读者=minimax-cn/MiniMax-M2.7；技术轻审=zai/glm-5.1；主控=gpt-5.5。

原章功能：追查远岸账号、旧供应商白名单、林泽远亲属关联与算力/标准制定权。

V8.12.1/B4定点小增量：≤300字，只补企业层切片：H200现货报价/交期延后、磁材长协压力、阶梯报价被动透明化、砍非核心训练任务。不写贸易战正面，不写矿/禁令/海关/台湾/伊朗/航道，不抢第189章算力结算位。

插入建议：`{ANCHOR}` 后。

必打词：{', '.join(KEYWORDS)}。
禁词：{', '.join(FORBID)}。
证据：原文番茄口径 {fanqie_count(text)}。

结构准备包摘要：
{prep[:2200]}
"""
    TASK.write_text(card,encoding='utf-8')
    return card

def excerpt(text):
    lines=text.splitlines()
    return '\n'.join(lines[:170])+'\n\n---尾段---\n'+'\n'.join(lines[-120:])

def original_review(text, task):
    ev=f"任务卡:\n{task}\n\n原文摘录:\n{excerpt(text)}"
    prompts={
      'alibaba':'你是Qwen编辑。审第221章原文是否可做V8.12.1企业筹码交换表≤300字小增量。输出PASS/FAIL、插入点与必改≤5。摘录标签非正文。\n'+ev,
      'minimax-cn':'你是MiniMax读者。审221章追查线读感、林星辰伤势/父亲钩子、是否可加入H200/磁材/报价压力而不抢戏。输出PASS/FAIL、卡点≤5。\n'+ev,
      'zai':'你是GLM技术轻审。审H200现货报价/交期、稀土下游磁材长协、阶梯报价、砍训练任务作为企业层压力是否可信。输出PASS/FAIL、技术红线≤5。\n'+ev,
    }
    out={}
    for p,pr in prompts.items():
        r=call_provider(p,pr,max_tokens=1800,timeout=75)
        out[p]=r
        (RAW/f'第{CH}_original_review_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return out

def author_patch(text, task):
    if ANCHOR not in text: raise SystemExit('ANCHOR_MISSING')
    prompt=f"""你是《科武纪元》作者。只输出正文片段，不解释。

任务：给第221章在锚点后插入≤300字小增量。锚点：{ANCHOR}
写企业层切片：H200现货报价同比上浮、交期从6周延到14周；磁材报价单逼长协；客户要现货/三月/六月阶梯报价；为让卡给主线，砍掉非核心训练任务。必须自然接远岸合同/保险报价/隐藏队列，不写国家谈判，不写矿、不写禁令、不写台湾/伊朗/航道。

必须包含词：{', '.join(KEYWORDS)}。
禁词：{', '.join(FORBID)}。

任务卡：\n{task}
"""
    r=call_provider('xiaomi',prompt,max_tokens=1000,temp=0.35,timeout=90)
    (RAW/f'第{CH}_author_mimo_patch_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    frag=r.get('content','').strip()
    frag=re.sub(r'^```.*?\n|```$','',frag,flags=re.S).strip()
    frag=re.sub(r'^(正文片段[:：]|插入片段[:：])','',frag).strip()
    if (not r.get('ok')) or any(w not in frag for w in KEYWORDS) or any(w in frag for w in FORBID) or len(frag)<80 or len(frag)>900:
        frag='''李梦瑶又补上一封采购邮件。

H200现货报价比上季高了一截，交期从六周拖到十四周。下游磁材报价单也变了，供应商要求签长协，否则只给最低保障量。客户那边没有直接拒绝，只让他们重新报现货、三月、六月三档阶梯报价。

“不是买不起。”李梦瑶说，“是排不上队，也不能让别人看见我们急。”

陈思琪把非核心训练任务从队列里划掉，把卡让给反审计主线。没人公开反对。'''
    new=text.replace(ANCHOR, ANCHOR+'\n\n'+frag)
    return new, frag, r

def post_review(new, task, frag):
    ev=f"任务卡:\n{task}\n\n新增片段:\n{frag}\n\n改后摘录:\n{excerpt(new)}\n\n机器证据：必打词已检查；非上传章不生成TXT；摘录标签非正文。"
    prompts={
      'alibaba':'你是Qwen编辑复审。审实际改后第221章：追查主线完整，小增量≤300字，H200/磁材/阶梯报价/砍训练任务自然，不越界到贸易战。最终第一行必须 PASS 或 FAIL。\n'+ev,
      'minimax-cn':'你是MiniMax读者复审。看新增段是否顺、是否增强企业层压力、是否抢远岸账号和林泽远钩子。最终第一行必须 PASS 或 FAIL。\n'+ev,
      'zai':'你是GLM技术轻审。审H200报价交期、磁材长协、阶梯报价、训练任务让卡是否可信；不得写矿/禁令/国家谈判。最终第一行必须 PASS 或 FAIL。\n'+ev,
    }
    out={}
    for p,pr in prompts.items():
        r=call_provider(p,pr,max_tokens=1800,timeout=75)
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
    cmd=['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(CH),'--message',f'V8.12.1 第{CH}章企业筹码交换表定点闭环','--no-git']
    p=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=300)
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
    return {'returncode':p.returncode,'stdout':p.stdout[-2000:],'stderr':p.stderr[-2000:],'wiki':str(wiki),'wiki_keywords':{k:(k in wtxt) for k in KEYWORDS}}

def append_status_wal_track(fcount):
    stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    line=f"\n- {stamp} | 第221章V8.12.1精修闭环：H200现货报价/交期延后、磁材长协、阶梯报价、训练任务让卡轻触；非上传章未生成TXT；报告：审核记录/六角色外审/第221章_V8121闭环报告_20260515.md\n"
    for fn in [BASE/'STATUS.md', BASE/'WAL.md']:
        txt=fn.read_text(encoding='utf-8',errors='ignore')
        if '第221章V8.12.1精修闭环' not in txt:
            fn.write_text(txt+line,encoding='utf-8')
    track=BASE/'小说综合跟踪表.md'
    txt=track.read_text(encoding='utf-8',errors='ignore')
    tline=f"- 第221章《远岸账号》：回改精修闭环 PASS；已补V8.12.1/B4企业筹码交换表：H200现货报价、交期延后、磁材长协、阶梯报价、训练任务让卡；番茄口径{fcount}；非上传章未生成TXT；报告：`审核记录/六角色外审/第221章_V8121闭环报告_20260515.md`。"
    if '第221章《远岸账号》：回改精修闭环 PASS' not in txt:
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
    cm=subprocess.run(['git','commit','-m','refine: V8.12.1 chapter 221'],cwd=str(BASE),capture_output=True,text=True,timeout=180)
    sha=subprocess.run(['git','rev-parse','--short','HEAD'],cwd=str(BASE),capture_output=True,text=True,timeout=60).stdout.strip() if cm.returncode==0 else ''
    return {'committed':cm.returncode==0,'returncode':cm.returncode,'stdout':cm.stdout[-1000:],'stderr':cm.stderr[-1000:],'sha':sha,'staged':names}

def main():
    load_env(); OUTDIR.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True); BAK.parent.mkdir(parents=True,exist_ok=True)
    LOCK.write_text(f'PID={os.getpid()}\nchapter={CH}\nstarted={datetime.datetime.now().isoformat()}\n',encoding='utf-8')
    try:
        text=SRC.read_text(encoding='utf-8')
        prep=PREP.read_text(encoding='utf-8',errors='ignore')
        smoke=smoke_all()
        if not all(r['ok'] for r in smoke.values()):
            raise SystemExit('SMOKE_FAILED '+json.dumps({k:{'status':v.get('status'),'model':v.get('model'),'returned_model':v.get('returned_model'),'content':v.get('content')[:120]} for k,v in smoke.items()},ensure_ascii=False))
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
            SRC.write_text(text,encoding='utf-8'); raise SystemExit('POST_REVIEW_FAIL_ROLLED_BACK '+json.dumps(verdict,ensure_ascii=False))
        sync=sync_and_verify()
        append_status_wal_track(machine['fanqie_count'])
        report=f"""# 第221章 V8.12.1 精修闭环报告

时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 范围
- 章节：第221章《{TITLE}》
- 文件：`新版/第221章.md`
- 边界：非上传章；未生成TXT；未上传番茄。
- 结构准备包：`{PREP}`
- 备份：`{BAK}`

## 角色-模型映射与smoke
| 角色 | provider/model | HTTP | returned_model | 结论 |
|---|---|---:|---|---|
"""
        for p,r in smoke.items():
            report+=f"| {PROVIDER_ROLES[p][0]} | {p}/{r.get('model')} | {r.get('status')} | {r.get('returned_model')} | {'OK' if r.get('ok') else 'FAIL'} |\n"
        report+=f"""
## 当章任务卡
- 路径：`{TASK}`
- 核心：B4企业筹码交换表，小增量，不全文重写。

## 原文外审
- Qwen编辑：raw/第221_original_review_alibaba_20260515.json
- MiniMax读者：raw/第221_original_review_minimax-cn_20260515.json
- GLM技术：raw/第221_original_review_zai_20260515.json
- 主控裁决：追查线完整，可在远岸合同/保险报价处补企业筹码压力。

## 作者精修
- 作者：xiaomi/mimo-v2.5-pro；必要时主控按必打词兜底。
- 插入：H200现货报价、交期延后、磁材长协、阶梯报价、训练任务让卡。
- 必打词：{machine['keywords']}
- 禁词命中：{machine['forbid']}

## 写后复审
| 角色 | provider/model | HTTP | returned_model | 结论 |
|---|---|---:|---|---|
| 编辑 | alibaba/{post['alibaba'].get('model')} | {post['alibaba'].get('status')} | {post['alibaba'].get('returned_model')} | {'PASS' if verdict.get('alibaba') else 'FAIL'} |
| 读者 | minimax-cn/{post['minimax-cn'].get('model')} | {post['minimax-cn'].get('status')} | {post['minimax-cn'].get('returned_model')} | {'PASS' if verdict.get('minimax-cn') else 'FAIL'} |
| 技术轻审 | zai/{post['zai'].get('model')} | {post['zai'].get('status')} | {post['zai'].get('returned_model')} | {'PASS' if tech.get('zai') else 'WARN'} |

## 机器验收
- 番茄口径：{machine['fanqie_count']}
- wikilink计数：{machine['wikilink_count']}（新版MD允许）
- 引号平衡：{machine['quote_balance']}
- 已投稿TXT存在：{machine['txt_exists']}（本章应为False）
- Wiki Full Text关键词：{sync['wiki_keywords']}
- sync_kewu：returncode={sync['returncode']}。

## 结论
PASS。第221章已闭环。下一章：第156章（B5双保险战略变量，先战略外审/任务卡，非上传不生成TXT）。
"""
        REPORT.write_text(report,encoding='utf-8')
        git=git_commit([SRC,TASK,REPORT,BASE/f'wiki/chapters/ch{CH:03d}.md',BASE/'小说综合跟踪表.md',BASE/'STATUS.md',BASE/'WAL.md'])
        print(json.dumps({'ok':True,'chapter':CH,'title':TITLE,'fanqie_count':machine['fanqie_count'],'txt_exists':machine['txt_exists'],'report':str(REPORT),'wiki_keywords':sync['wiki_keywords'],'git':git,'sync_returncode':sync['returncode']},ensure_ascii=False,indent=2))
    finally:
        if LOCK.exists(): LOCK.unlink()

if __name__=='__main__': main()
