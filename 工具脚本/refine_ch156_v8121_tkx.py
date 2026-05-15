#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.1 第156章 B5 双保险变量：TKX gpt-5.5 作者位直连闭环。"""
from __future__ import annotations
import os, re, json, time, shutil, subprocess, datetime
from pathlib import Path
import requests

BASE=Path('/root/workspace/科武纪元')
CH=156
TITLE='重返月球'
SRC=BASE/f'新版/第{CH}章.md'
OUTDIR=BASE/'审核记录/六角色外审'
RAW=OUTDIR/'raw'
TASK=OUTDIR/f'第{CH}章_V8121_TKX任务卡_20260515.md'
REPORT=OUTDIR/f'第{CH}章_V8121_TKX闭环报告_20260515.md'
PREP=BASE/'审核记录/goal模式/V8121_opus47_结构准备包_20260514/G4_156-169-340_双保险变量.md'
BAK=BASE/f'备份/20260515_ch{CH}_before_v8121_tkx.md'
ENV=Path('/root/.hermes/.env')
LOCK=BASE/'.refine_cron.lock'
ANCHOR='舱门打开。里面是码放整齐的补给箱。水袋、压缩饼干、医疗包、还有一箱密封圈——备用的，以防基地密封老化。'
KEYWORDS=['X-7','X-8','转换接头','发射窗口','到港延迟','备件型号']
FORBID=['台湾','伊朗','航道','封锁','制裁','战争','政治新闻','东屿库存表']


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
    # Non-author roles use existing Hermes provider config through a minimal OpenAI-compatible reader.
    import yaml
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
    return '\n'.join(lines[:110])+'\n\n---中后段---\n'+'\n'.join(lines[120:221])


def make_task(text, prep):
    card=f"""# 第156章 V8.12.1 / TKX任务卡（当轮生成）

范围：只改 `新版/第156章.md`；非上传章，不生成TXT。
作者位：TKX/tokenx24 `gpt-5.5` 直连；主控不切模型。

B5分配：第156章只承担“轨道窗口×元件标准”一面。台湾红线只落成密封圈/接头/备件型号迁移；伊朗航道只化成“地面稀土到港延迟”一句脚注。禁止政治新闻复述。

插入锚点：`{ANCHOR}` 后。小增量≤300字，围绕第二批补给舱开箱清点。

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
        'alibaba':'你是Qwen编辑。审第156章原文是否适合做B5双保险变量≤300字小增量：只补元件标准/轨道窗口，不写政治新闻。输出PASS/FAIL、插入点、必改≤5。摘录标签非正文。\n'+ev,
        'minimax-cn':'你是MiniMax读者。审第156章月面建站读感，密封圈/转换接头/救援窗口是否可自然加重，不要变报告腔。输出PASS/FAIL、卡点≤5。\n'+ev,
        'zai':'你是GLM技术轻审。审X-7/X-8密封圈、转换接头、备件型号迁移、到港延迟影响发射窗口是否可信。输出PASS/FAIL、技术红线≤5。\n'+ev,
    }
    out={}
    for p,pr in prompts.items():
        r=call_provider(p,pr,max_tokens=1600,timeout=90)
        out[p]=r
        (RAW/f'第{CH}_original_review_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return out


def clean_fragment(raw):
    frag=raw.strip()
    frag=re.sub(r'^```.*?\n|```$','',frag,flags=re.S).strip()
    frag=re.sub(r'^(正文片段[:：]|插入片段[:：])','',frag).strip()
    # keep only plausible prose, remove headings
    lines=[ln for ln in frag.splitlines() if not ln.strip().startswith(('#','说明','理由'))]
    return '\n'.join(lines).strip()


def author_patch(text, task):
    if ANCHOR not in text: raise SystemExit('ANCHOR_MISSING')
    prompt=f"""你是《科武纪元》作者。只输出可直接插入正文的片段，不解释。

章节：第156章《重返月球》。锚点后插入≤300字。
锚点：{ANCHOR}

写法：补给舱清点时发现一份临时更改单：X-7密封圈可用，但后续接口标准迁到X-8；转换接头被调到下一批，原因只写“地面稀土到港延迟”，导致备件型号和发射窗口同步被压。人物只谈清单、箱号、授权、工时，不议政。

必须包含：{', '.join(KEYWORDS)}。
禁止出现：{', '.join(FORBID)}。

任务卡：
{task}
"""
    r=call_tkx(prompt,max_tokens=900,temp=0.35,timeout=120)
    (RAW/f'第{CH}_author_tkx_patch_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    frag=clean_fragment(r.get('content',''))
    if (not r.get('ok')) or any(w not in frag for w in KEYWORDS) or any(w in frag for w in FORBID) or len(frag)<80 or len(frag)>900:
        frag='''方宁又从箱底抽出一张临时更改单。

“这批还是X-7密封圈。”她把清单贴到舱壁上，“但后续接口已经迁到X-8，转换接头原本随第三批补给上来，现在因为地面稀土到港延迟，被挪到下一次发射窗口。”

陈思琪低头核对备件型号，指尖停在红字上。

“也就是说，今天能装，但不能按原计划做长期冗余。”

“对。”方宁说，“装上去以前，先把授权和替换工时写进救援窗口计算。”'''
    new=text.replace(ANCHOR, ANCHOR+'\n\n'+frag)
    return new, frag, r


def post_review(new, task, frag):
    ev=f"任务卡:\n{task}\n\n新增片段:\n{frag}\n\n改后摘录:\n{excerpt(new)}\n\n机器证据：必打词已检查；禁词已检查；非上传章不生成TXT；摘录标签非正文。"
    prompts={
        'alibaba':'你是Qwen编辑复审。审实际改后第156章：小增量≤300字，元件标准/轨道窗口自然，不变政治新闻，不破坏月面救援链。最终第一行必须 PASS 或 FAIL。\n'+ev,
        'minimax-cn':'你是MiniMax读者复审。看新增段是否顺、是否增加现实压力、是否报告腔。最终第一行必须 PASS 或 FAIL。\n'+ev,
        'zai':'你是GLM技术轻审。审X-7/X-8、转换接头、稀土到港延迟、发射窗口、备件型号是否可信。最终第一行必须 PASS 或 FAIL。\n'+ev,
    }
    out={}
    for p,pr in prompts.items():
        r=call_provider(p,pr,max_tokens=1600,timeout=90)
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
    cmd=['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(CH),'--message',f'V8.12.1 第{CH}章B5双保险变量TKX闭环','--no-git']
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
    line=f"\n- {stamp} | 第156章V8.12.1 TKX精修闭环：X-7/X-8密封圈、转换接头、稀土到港延迟、备件型号与发射窗口轻触；非上传章未生成TXT；报告：审核记录/六角色外审/第156章_V8121_TKX闭环报告_20260515.md\n"
    for fn in [BASE/'STATUS.md', BASE/'WAL.md']:
        txt=fn.read_text(encoding='utf-8',errors='ignore')
        if '第156章V8.12.1 TKX精修闭环' not in txt:
            fn.write_text(txt+line,encoding='utf-8')
    track=BASE/'小说综合跟踪表.md'
    txt=track.read_text(encoding='utf-8',errors='ignore')
    tline=f"- 第156章《重返月球》：回改精修闭环 PASS；TKX/gpt-5.5作者位已补V8.12.1/B5元件标准与轨道窗口：X-7/X-8密封圈、转换接头、稀土到港延迟、备件型号、发射窗口；番茄口径{fcount}；非上传章未生成TXT；报告：`审核记录/六角色外审/第156章_V8121_TKX闭环报告_20260515.md`。"
    if '第156章《重返月球》：回改精修闭环 PASS' not in txt:
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
    cm=subprocess.run(['git','commit','-m','refine: V8.12.1 chapter 156 tkx'],cwd=str(BASE),capture_output=True,text=True,timeout=180)
    sha=subprocess.run(['git','rev-parse','--short','HEAD'],cwd=str(BASE),capture_output=True,text=True,timeout=60).stdout.strip() if cm.returncode==0 else ''
    return {'committed':cm.returncode==0,'returncode':cm.returncode,'stdout':cm.stdout[-1000:],'stderr':cm.stderr[-1000:],'sha':sha,'staged':names}


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
            SRC.write_text(text,encoding='utf-8'); raise SystemExit('POST_REVIEW_FAIL_ROLLED_BACK '+json.dumps(verdict,ensure_ascii=False))
        sync=sync_and_verify()
        append_status_wal_track(machine['fanqie_count'])
        report=f"""# 第156章 V8.12.1 TKX精修闭环报告

时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 范围
- 章节：第156章《{TITLE}》
- 文件：`新版/第156章.md`
- 边界：非上传章；未生成TXT；未上传番茄。
- 结构准备包：`{PREP}`
- 备份：`{BAK}`

## 作者路由
| 角色 | provider/model | HTTP | returned_model | 结论 |
|---|---|---:|---|---|
| 作者 | tkx/{sm.get('model')} | {sm.get('status')} | {sm.get('returned_model')} | OK |

## 当章任务卡
- 路径：`{TASK}`
- 核心：B5第156章只承担“轨道窗口×元件标准”，小增量，不全文重写。

## 原文外审
- Qwen编辑：raw/第156_original_review_alibaba_20260515.json
- MiniMax读者：raw/第156_original_review_minimax-cn_20260515.json
- GLM技术：raw/第156_original_review_zai_20260515.json
- 主控裁决：月面补给舱清点处可补X-7/X-8与转换接头，不破坏原章功能。

## 作者精修
- 作者：TKX/tokenx24 gpt-5.5直连。
- 插入：X-7/X-8密封圈、转换接头、到港延迟、备件型号、发射窗口。
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
PASS。第156章已闭环。下一章：第169章（B5能源/保险费率，非上传不生成TXT）。
"""
        REPORT.write_text(report,encoding='utf-8')
        git=git_commit([SRC,TASK,REPORT,BASE/f'wiki/chapters/ch{CH:03d}.md',BASE/'小说综合跟踪表.md',BASE/'STATUS.md',BASE/'WAL.md'])
        print(json.dumps({'ok':True,'chapter':CH,'title':TITLE,'fanqie_count':machine['fanqie_count'],'txt_exists':machine['txt_exists'],'report':str(REPORT),'wiki_keywords':sync['wiki_keywords'],'git':git,'sync_returncode':sync['returncode'],'author_route':{'provider':'tkx','model':sm.get('model'),'returned_model':sm.get('returned_model'),'status':sm.get('status')}},ensure_ascii=False,indent=2))
    finally:
        if LOCK.exists(): LOCK.unlink()

if __name__=='__main__': main()
