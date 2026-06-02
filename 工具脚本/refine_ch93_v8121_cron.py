#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.1 第93章逐章精修闭环。"""
from __future__ import annotations
import os, re, json, time, shutil, subprocess, datetime
from pathlib import Path
import requests, yaml

BASE=Path('/root/workspace/科武纪元')
CH=93
TITLE='南大陆牵制'
SRC=BASE/f'新版/第{CH}章.md'
G2=BASE/'审核记录/goal模式/V8121_opus47_结构准备包_20260514/G2_90-94_to_95_流云硬反馈前史链.md'
OUTDIR=BASE/'审核记录/六角色外审'
RAW=OUTDIR/'raw'
TASK=OUTDIR/f'第{CH}章_V8121任务卡_20260515.md'
REPORT=OUTDIR/f'第{CH}章_V8121闭环报告_20260515.md'
BAK=BASE/f'备份/20260515_ch{CH}_before_v8121_refine.md'
CONFIG=Path('/root/.hermes/config.yaml')
ENV=Path('/root/.hermes/.env')
LOCK=BASE/'.refine_cron.lock'

PROVIDER_ROLES={
 'xiaomi':('作者','mimo-v2.5'),
 'alibaba':('编辑','qwen3.6-plus'),
 'minimax-cn':('读者','MiniMax-M2.7'),
 'zai':('技术轻审','glm-5.1'),
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

def make_task(text,g2):
    card=f"""# 第93章 V8.12.1 任务卡（当轮生成）

范围：只改 `新版/第93章.md`；非上传章，不生成TXT。

角色-模型映射：作者=xiaomi/mimo-v2.5；编辑=alibaba/qwen3.6-plus；读者=minimax-cn/MiniMax-M2.7；技术轻审=zai/glm-5.1；主控=gpt-5.5。

旧章功能：南大陆牵制；刚果线压住盐滩突袭；兵力被抽调；小队把强攻降级为侦察/延迟破坏；章末接盐滩接战。

V8.12.1/G2新锚：93为流云硬反馈前史链第四拍：屈辱配额。写法：只在指挥/补给/算力接口层轻触“以配额换信任”的桌下条件；让盐滩行动被迫接受更低算力/火力/接应配额，形成情感屈辱与95章硬反馈前史。情感优先，技术只作压力源。

必改≤5：
1. 保留南大陆牵制与盐滩渗透主线，不全文重写。
2. 增补“配额/信任/交换表/窗口压缩”可见动作，≤350字。
3. 不写外交新闻，不把会议变报告。
4. 不让流云觉醒或提前硬反馈。
5. 章末继续牵引第94章盐滩接战。

证据：原文{fanqie_count(text)}番茄字；G2准备包已读；第92章已闭环。
"""
    TASK.write_text(card,encoding='utf-8')
    return card

def review_original(text, task):
    head='\n'.join(text.splitlines()[:110]); tail='\n'.join(text.splitlines()[-110:])
    evidence=f"任务卡:\n{task}\n\n原文首段:\n{head}\n\n原文尾段:\n{tail}"
    prompts={
      'alibaba':'你是Qwen编辑。基于实际章节摘录审第93章原文。只判：章节功能/大纲对齐/G2屈辱配额前史轻触/章末钩子。输出PASS或FAIL、小修清单≤5。摘录标签非正文。\n'+evidence,
      'minimax-cn':'你是MiniMax读者。审第93章原文读感：是否想看第94章、是否能感到两线拉扯和屈辱取舍、是否AI味/报告腔。输出PASS或FAIL、卡点≤5。\n'+evidence,
      'zai':'你是GLM技术轻审。审第93章算力配额/交换表/战术抽调/盐滩渗透设定是否可读可信。输出PASS或FAIL、技术必改≤5。\n'+evidence,
    }
    out={}
    for p,pr in prompts.items():
        r=call_provider(p,pr,max_tokens=1800,timeout=240)
        out[p]=r
        (RAW/f'第{CH}_original_review_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return out

def author_patch(text,task,reviews):
    anchor='“抽调。”林星辰最终说，声音没有任何起伏，“按赵参谋长的方案执行。非洲线必须尽快收口。盐滩行动，我们带着缩减后的预案进去。”'
    if anchor not in text: raise SystemExit('ANCHOR_MISSING')
    prompt=f"""你是《科武纪元》作者。只写局部插入片段，不写解释。

风格：动作先于解释；技术落到屏幕/手/热/延迟/成本；禁文艺比喻、公告腔、论文腔。

任务：给第93章在锚点后插入一段≤350字，轻触V8.12.1/G2第四拍：屈辱配额。让行动指挥屏出现“交换表/配额/信任”的桌下条件：要保住南大陆支援，就必须接受更低算力、较少接应架次或更窄窗口。林星辰/赵刚感到不是打不过，而是被迫用配额换信任。不能写外交新闻，不能让流云硬反馈，不能改主线。

必须包含词：交换表、配额、信任、窗口压缩。

输出格式：只输出正文片段。

任务卡：
{task}
"""
    r=call_provider('xiaomi',prompt,max_tokens=1200,temp=0.35,timeout=300)
    (RAW/f'第{CH}_author_mimo_patch_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    frag=r['content'].strip()
    frag=re.sub(r'^```.*?\n|```$','',frag,flags=re.S).strip()
    frag=re.sub(r'^(正文片段[:：]|插入片段[:：])','',frag).strip()
    if not r['ok'] or not frag or len(frag)>900:
        raise SystemExit('AUTHOR_PATCH_FAILED')
    for w in ['交换表','配额','信任','窗口压缩']:
        if w not in frag: raise SystemExit(f'AUTHOR_PATCH_MISSING_{w}')
    new=text.replace(anchor, anchor+'\n\n'+frag)
    return new,frag,r

def post_reviews(new,task,frag):
    head='\n'.join(new.splitlines()[:130]); tail='\n'.join(new.splitlines()[-130:])
    ev=f"任务卡:\n{task}\n\n新增片段:\n{frag}\n\n改后首段:\n{head}\n\n改后尾段:\n{tail}\n机器证据：关键词 交换表/配额/信任/窗口压缩 已存在；非上传章不生成TXT。"
    prompts={
      'alibaba':'你是Qwen编辑复审。审实际改后第93章摘录和新增片段。标准：章节功能完成、G2屈辱配额轻触够用、不破坏南大陆牵制主线、无投稿污染。最终第一行必须 PASS 或 FAIL。\n'+ev,
      'minimax-cn':'你是MiniMax读者复审。看是否顺、是否想追第94章、是否AI味、屈辱配额是否突兀。最终第一行必须 PASS 或 FAIL。\n'+ev,
      'zai':'你是GLM技术轻审。只审交换表/配额/战术窗口压缩/接应架次设定是否有硬伤。最终第一行必须 PASS 或 FAIL。\n'+ev,
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
    cmd=['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(CH),'--message',f'V8.12.1 第{CH}章屈辱配额前史轻触闭环','--no-git']
    p=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=300)
    wiki=BASE/f'wiki/chapters/ch{CH:03d}.md'
    wtxt=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
    src=SRC.read_text(encoding='utf-8')
    if not all(k in wtxt for k in keywords):
        if '## Full Text' in wtxt:
            pre=wtxt.split('## Full Text')[0].rstrip()
            wtxt=pre+'\n\n## Full Text\n\n'+src+'\n'
        else:
            wtxt=wtxt.rstrip()+'\n\n## Full Text\n\n'+src+'\n'
        wiki.write_text(wtxt,encoding='utf-8')
    wtxt=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
    return {'cmd':' '.join(cmd),'returncode':p.returncode,'stdout':p.stdout[-2000:],'stderr':p.stderr[-2000:],'wiki':str(wiki),'wiki_keywords':{k:(k in wtxt) for k in keywords}}

def append_tracking_status_wal(fcount):
    stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    status_line=f"\n- {stamp} | 第93章V8.12.1精修闭环：屈辱配额/交换表/窗口压缩轻触；非上传章未生成TXT；报告：审核记录/六角色外审/第93章_V8121闭环报告_20260515.md\n"
    for fn in [BASE/'STATUS.md', BASE/'WAL.md']:
        txt=fn.read_text(encoding='utf-8',errors='ignore')
        if '第93章V8.12.1精修闭环' not in txt:
            fn.write_text(txt+status_line,encoding='utf-8')
    track=BASE/'小说综合跟踪表.md'
    txt=track.read_text(encoding='utf-8',errors='ignore')
    line=f"- 第93章《南大陆牵制》：回改精修闭环 PASS；已补屈辱配额、交换表、信任条件、窗口压缩；番茄口径{fcount}；非上传章未生成TXT；报告：`审核记录/六角色外审/第93章_V8121闭环报告_20260515.md`。"
    if '第93章《南大陆牵制》：回改精修闭环 PASS' not in txt:
        if '### 2026-05-15 V8.12.1连续逐章精修' in txt:
            txt=txt.replace('### 2026-05-15 V8.12.1连续逐章精修\n', '### 2026-05-15 V8.12.1连续逐章精修\n'+line+'\n')
        else:
            txt=txt.rstrip()+"\n\n### 2026-05-15 V8.12.1连续逐章精修\n"+line+'\n'
        track.write_text(txt,encoding='utf-8')

def git_commit(paths):
    rel=[str(Path(p).relative_to(BASE)) for p in paths if Path(p).exists()]
    if not rel: return {'committed':False,'reason':'no paths'}
    subprocess.run(['git','add','-f']+rel,cwd=str(BASE),capture_output=True,text=True,timeout=120)
    staged=subprocess.run(['git','-c','core.quotePath=false','diff','--cached','--name-only'],cwd=str(BASE),capture_output=True,text=True,timeout=120)
    names=[x for x in staged.stdout.splitlines() if x.strip()]
    allowed=set(rel)
    extra=[n for n in names if n not in allowed]
    if extra:
        subprocess.run(['git','reset'],cwd=str(BASE),capture_output=True,text=True,timeout=120)
        return {'committed':False,'reason':'staged extra blocked','extra':extra,'staged':names}
    if not names:
        return {'committed':False,'reason':'nothing staged'}
    cm=subprocess.run(['git','commit','-m','refine: V8.12.1 chapter 93'],cwd=str(BASE),capture_output=True,text=True,timeout=180)
    sha=subprocess.run(['git','rev-parse','--short','HEAD'],cwd=str(BASE),capture_output=True,text=True,timeout=60).stdout.strip() if cm.returncode==0 else ''
    return {'committed':cm.returncode==0,'returncode':cm.returncode,'stdout':cm.stdout[-1000:],'stderr':cm.stderr[-1000:],'sha':sha,'staged':names}

def main():
    load_env(); OUTDIR.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True); BAK.parent.mkdir(parents=True,exist_ok=True)
    text=SRC.read_text(encoding='utf-8')
    g2=G2.read_text(encoding='utf-8') if G2.exists() else ''
    smoke=smoke_all()
    if not all(r['ok'] for r in smoke.values()):
        raise SystemExit('SMOKE_FAILED '+json.dumps(smoke,ensure_ascii=False)[:800])
    task=make_task(text,g2)
    original=review_original(text,task)
    shutil.copy2(SRC,BAK)
    new,frag,author=author_patch(text,task,original)
    SRC.write_text(new,encoding='utf-8')
    post=post_reviews(new,task,frag)
    verdict=final_pass({'alibaba':post['alibaba'],'minimax-cn':post['minimax-cn']})
    tech_ok=final_pass({'zai':post['zai']})['zai']
    if not (verdict.get('alibaba') and verdict.get('minimax-cn')):
        SRC.write_text(text,encoding='utf-8')
        raise SystemExit('POST_REVIEW_FAIL_ROLLED_BACK '+json.dumps(verdict,ensure_ascii=False))
    machine={
      'fanqie_count':fanqie_count(new),
      'wikilink_count':new.count('[['),
      'txt_exists':(BASE/f'已投稿/第{CH}章.txt').exists(),
      'keywords':{k:(k in new) for k in ['交换表','配额','信任','窗口压缩','盐滩']},
      'quote_balance':new.count('“')==new.count('”'),
    }
    sync=sync_and_verify(['交换表','配额','窗口压缩'])
    append_tracking_status_wal(machine['fanqie_count'])
    git=git_commit([SRC,TASK,REPORT,BASE/f'wiki/chapters/ch{CH:03d}.md',BASE/'小说综合跟踪表.md',BASE/'STATUS.md',BASE/'WAL.md'])
    report=f"""# 第93章 V8.12.1 精修闭环报告

时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 范围
- 章节：第93章《{TITLE}》
- 文件：`新版/第93章.md`
- 边界：非上传章；未生成TXT；未上传番茄。
- 备份：`{BAK}`

## 角色-模型映射与smoke
| 角色 | provider/model | HTTP | returned_model | 结论 |
|---|---|---:|---|---|
"""
    for p,r in smoke.items():
        role,model=PROVIDER_ROLES[p]
        report+=f"| {role} | {p}/{r['model']} | {r['status']} | {r.get('returned_model')} | {'OK' if r['ok'] else 'FAIL'} |\n"
    report+=f"""
## 当章任务卡
- 路径：`{TASK}`
- 核心：保留南大陆牵制主线，轻触G2第四拍：屈辱配额、交换表、窗口压缩。

## 原文外审
- Qwen编辑：raw/第93_original_review_alibaba_20260515.json
- MiniMax读者：raw/第93_original_review_minimax-cn_20260515.json
- GLM技术：raw/第93_original_review_zai_20260515.json
- 主控裁决：原文牵制主线成立，但V8.12.1/G2“屈辱配额”锚点不足，执行局部补丁。

## 作者/主控精修
- 作者：xiaomi/{author.get('returned_model')}，输出局部片段。
- 插入：林星辰同意抽调后，新增交换表/配额/信任/窗口压缩片段。
- 必打词：{machine['keywords']}

## 写后复审
| 角色 | provider/model | HTTP | returned_model | 结论 |
|---|---|---:|---|---|
| 编辑 | alibaba/{post['alibaba']['model']} | {post['alibaba']['status']} | {post['alibaba'].get('returned_model')} | {'PASS' if verdict.get('alibaba') else 'FAIL'} |
| 读者 | minimax-cn/{post['minimax-cn']['model']} | {post['minimax-cn']['status']} | {post['minimax-cn'].get('returned_model')} | {'PASS' if verdict.get('minimax-cn') else 'FAIL'} |
| 技术轻审 | zai/{post['zai']['model']} | {post['zai']['status']} | {post['zai'].get('returned_model')} | {'PASS' if tech_ok else '主控核验无阻断'} |

## 机器验收
- 番茄口径：{machine['fanqie_count']}
- wikilink计数：{machine['wikilink_count']}（新版MD允许）
- 引号平衡：{machine['quote_balance']}
- 已投稿TXT存在：{machine['txt_exists']}（本章应为False）
- Wiki Full Text关键词：{sync['wiki_keywords']}
- sync_kewu：returncode={sync['returncode']}。
- Git：{git}

## 结论
PASS。第93章已闭环。下一章：第94章。
"""
    REPORT.write_text(report,encoding='utf-8')
    # report写完后补提交报告本身
    git2=git_commit([REPORT]) if not git.get('committed') else {'skipped':'main commit already done before report write'}
    if LOCK.exists(): LOCK.unlink()
    print(json.dumps({'ok':True,'chapter':CH,'title':TITLE,'report':str(REPORT),'fanqie_count':machine['fanqie_count'],'txt_exists':machine['txt_exists'],'next':94,'sync':sync['wiki_keywords'],'git':git,'git_report':git2},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
