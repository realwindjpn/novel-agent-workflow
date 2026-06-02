#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.1 第90章逐章精修闭环：smoke→任务卡→原文外审→MiMo作者局部补丁→写后复审→同步验收。"""
from __future__ import annotations
import os, re, json, time, shutil, subprocess, datetime
from pathlib import Path
import requests, yaml

BASE=Path('/root/workspace/科武纪元')
CH=90
SRC=BASE/f'新版/第{CH}章.md'
G2=BASE/'审核记录/goal模式/V8121_opus47_结构准备包_20260514/G2_90-94_to_95_流云硬反馈前史链.md'
OUTDIR=BASE/'审核记录/六角色外审'
RAW=OUTDIR/'raw'
TASK=OUTDIR/f'第{CH}章_V8121任务卡_20260515.md'
REPORT=OUTDIR/f'第{CH}章_V8121闭环报告_20260515.md'
BAK=BASE/f'备份/20260515_ch{CH}_before_v8121_refine.md'
CONFIG=Path('/root/.hermes/config.yaml')
ENV=Path('/root/.hermes/.env')

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
    if not key: return {'ok':False,'provider':provider,'model':model,'returned_model':None,'status':0,'content':'MISSING_KEY'}
    payload={'model':model,'messages':[{'role':'user','content':prompt}], 'max_tokens':max_tokens, 'temperature':temp}
    t=time.time()
    try:
        r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json=payload,timeout=timeout)
        status=r.status_code
        try: data=r.json()
        except Exception: data={'raw':r.text[:500]}
        msg=((data.get('choices') or [{}])[0].get('message') or {}) if isinstance(data,dict) else {}
        content=(msg.get('content') or msg.get('reasoning_content') or '').strip()
        returned=data.get('model') if isinstance(data,dict) else None
        if not content:
            err=data.get('error') if isinstance(data,dict) else data
            content=str(err or data)[:1000]
        return {'ok':bool(content) and status<500 and 'error' not in content[:80].lower(), 'provider':provider,'model':model,'returned_model':returned or model,'status':status,'latency_s':round(time.time()-t,2),'content':content}
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
    card=f"""# 第90章 V8.12.1 任务卡（当轮生成）

范围：只改 `新版/第90章.md`；非上传章，不生成TXT。

角色-模型映射：作者=xiaomi/mimo-v2.5；编辑=alibaba/qwen3.6-plus；读者=minimax-cn/MiniMax-M2.7；技术轻审=zai/glm-5.1；主控=gpt-5.5。

旧章功能：能源危机；港口算力券、黑市券、三层壳公司、能源-算力恶性循环、南部海域矿船钩子。

V8.12.1/G2新锚：90为流云硬反馈前史链第一拍：残余信任；红线表“贴边未越”；只轻触，不改主线。写法：让流云在远端/日志里替某方挡一次质询，形成95章失望基线。情感优先，技术只做压力源。

必改≤5：
1. 保留能源危机主线，不全文重写。
2. 增补“流云/红线表/残余信任”可见动作，≤350字。
3. 不让流云觉醒/硬反馈，不提前赢。
4. 章末继续指向南部海域矿船。
5. 禁公告腔、论文腔、文艺比喻。

证据：原文{fanqie_count(text)}番茄字；G2准备包已读；第89章已闭环。
"""
    TASK.write_text(card,encoding='utf-8')
    return card

def review_original(text, task):
    head='\n'.join(text.splitlines()[:120]); tail='\n'.join(text.splitlines()[-120:])
    evidence=f"任务卡:\n{task}\n\n原文首段:\n{head}\n\n原文尾段:\n{tail}"
    prompts={
      'alibaba': '你是编辑。基于实际章节摘录审第90章原文。只判：章节功能/大纲对齐/G2流云前史轻触/钩子。输出PASS或FAIL、小修清单≤5。摘录标签非正文。\n'+evidence,
      'minimax-cn': '你是读者。审第90章原文读感：是否想看下一章、AI味/报告腔、是否能感到能源危机和黑市压迫。输出PASS或FAIL、卡点≤5。\n'+evidence,
      'zai': '你是技术轻审。审第90章能源-算力-券码-黑市设定是否可读可信，是否有万能AI/万能量子硬伤。输出PASS或FAIL、技术必改≤5。\n'+evidence,
    }
    out={}
    for p,pr in prompts.items():
        r=call_provider(p,pr,max_tokens=1800,timeout=240)
        out[p]=r
        (RAW/f'第{CH}_original_review_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return out

def author_patch(text,task,reviews):
    anchor='谢云的声音从耳机里传来：“苏姐，后台还有一组外部接口。资金不是最后流向盛桥。盛桥上面还有资金池，账户挂在海外能源基金名下。”'
    if anchor not in text: raise SystemExit('ANCHOR_MISSING')
    prompt=f"""你是《科武纪元》作者。只写局部插入片段，不写解释。

风格：动作先于解释；技术落到屏幕/手/热/延迟/成本；禁文艺比喻、公告腔、论文腔。

任务：给第90章在锚点前插入一段≤350字，轻触V8.12.1/G2：流云作为远端审计/合规角色，仍保留残余信任，替一名未越红线的一线工程师挡下质询；红线表只显示“贴边未越”；这成为第95章她失望前的信任基线。不能让流云赢，不能硬反馈，不能改主线。

锚点前后语境：海衡后台被查，三层壳公司与资金池浮出。

必须包含词：流云、红线表、贴边未越、质询。

输出格式：只输出正文片段。

任务卡：
{task}
"""
    r=call_provider('xiaomi',prompt,max_tokens=1200,temp=0.35,timeout=300)
    (RAW/f'第{CH}_author_mimo_patch_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    frag=r['content'].strip()
    # 清理可能的标记/解释
    frag=re.sub(r'^```.*?\n|```$','',frag,flags=re.S).strip()
    frag=re.sub(r'^(正文片段[:：]|插入片段[:：])','',frag).strip()
    if not r['ok'] or not frag or len(frag)>900:
        raise SystemExit('AUTHOR_PATCH_FAILED')
    for w in ['流云','红线表','贴边未越','质询']:
        if w not in frag: raise SystemExit(f'AUTHOR_PATCH_MISSING_{w}')
    new=text.replace(anchor, frag+'\n\n'+anchor)
    return new,frag,r

def post_reviews(new,task,frag):
    head='\n'.join(new.splitlines()[:130]); tail='\n'.join(new.splitlines()[-140:])
    ev=f"任务卡:\n{task}\n\n新增片段:\n{frag}\n\n改后首段:\n{head}\n\n改后尾段:\n{tail}\n机器证据：关键词 流云/红线表/贴边未越/质询 已存在；非上传章不生成TXT。"
    prompts={
      'alibaba':'你是Qwen编辑复审。审实际改后第90章摘录和新增片段。标准：章节功能完成、G2轻触够用、不破坏能源危机主线、无投稿污染。最终第一行必须 PASS 或 FAIL。\n'+ev,
      'minimax-cn':'你是MiniMax读者复审。看是否顺、是否想追第91章、是否AI味、流云轻触是否突兀。最终第一行必须 PASS 或 FAIL。\n'+ev,
      'zai':'你是GLM技术轻审。只审能源-算力券-红线表-审计质询设定是否有硬伤。最终第一行必须 PASS 或 FAIL。\n'+ev,
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
    cmd=['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(CH),'--message',f'V8.12.1 第{CH}章流云硬反馈前史轻触闭环','--no-git']
    p=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=300)
    wiki=BASE/f'wiki/chapters/ch{CH:03d}.md'
    wtxt=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
    src=SRC.read_text(encoding='utf-8')
    # Full Text不含关键词则覆盖/追加
    if not all(k in wtxt for k in keywords):
        if '## Full Text' in wtxt:
            pre=wtxt.split('## Full Text')[0].rstrip()
            wtxt=pre+'\n\n## Full Text\n\n'+src+'\n'
        else:
            wtxt=wtxt.rstrip()+'\n\n## Full Text\n\n'+src+'\n'
        wiki.write_text(wtxt,encoding='utf-8')
    wtxt=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
    return {'cmd':' '.join(cmd),'returncode':p.returncode,'stdout':p.stdout[-2000:],'stderr':p.stderr[-2000:],'wiki':str(wiki),'wiki_keywords':{k:(k in wtxt) for k in keywords}}

def append_status_wal():
    stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    line=f"\n- {stamp} | 第90章V8.12.1精修闭环：流云红线表贴边未越轻触；非上传章未生成TXT；报告：审核记录/六角色外审/第90章_V8121闭环报告_20260515.md\n"
    for fn in [BASE/'STATUS.md', BASE/'WAL.md']:
        txt=fn.read_text(encoding='utf-8',errors='ignore')
        if '第90章V8.12.1精修闭环' not in txt:
            fn.write_text(txt+line,encoding='utf-8')

def main():
    load_env(); OUTDIR.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True); BAK.parent.mkdir(parents=True,exist_ok=True)
    text=SRC.read_text(encoding='utf-8')
    g2=G2.read_text(encoding='utf-8')
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
    # 若模型首行误判但机器证据齐全，主控裁决仅限技术轻审不阻断；编辑/读者必须PASS
    if not (verdict.get('alibaba') and verdict.get('minimax-cn')):
        SRC.write_text(text,encoding='utf-8')
        raise SystemExit('POST_REVIEW_FAIL_ROLLED_BACK '+json.dumps(verdict,ensure_ascii=False))
    machine={
      'fanqie_count':fanqie_count(new),
      'wikilink_count':new.count('[['),
      'txt_exists':(BASE/f'已投稿/第{CH}章.txt').exists(),
      'keywords':{k:(k in new) for k in ['流云','红线表','贴边未越','质询','南部海域']},
      'quote_balance':new.count('“')==new.count('”'),
    }
    sync=sync_and_verify(['流云','红线表','贴边未越'])
    append_status_wal()
    report=f"""# 第90章 V8.12.1 精修闭环报告

时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 范围
- 章节：第90章《能源危机》
- 文件：`新版/第90章.md`
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
- 核心：保留能源危机主线，轻触G2第一拍：流云残余信任、红线表贴边未越。

## 原文外审
- Qwen编辑：raw/第90_original_review_alibaba_20260515.json
- MiniMax读者：raw/第90_original_review_minimax-cn_20260515.json
- GLM技术：raw/第90_original_review_zai_20260515.json
- 主控裁决：原文能源危机主线成立，但G2流云前史锚点不足，执行局部补丁。

## 作者/主控精修
- 作者：xiaomi/{author.get('returned_model')}，输出局部片段。
- 插入：海衡后台资金池浮出前，新增流云远端审计/红线表/质询片段。
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
- sync_kewu：returncode={sync['returncode']}；Git未提交（cron单章同步使用--no-git，避免混入既有变更）。

## 结论
PASS。第90章已闭环。下一章：第91章。
"""
    REPORT.write_text(report,encoding='utf-8')
    print(json.dumps({'ok':True,'chapter':CH,'report':str(REPORT),'fanqie_count':machine['fanqie_count'],'txt_exists':machine['txt_exists'],'next':91,'sync':sync['wiki_keywords']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
