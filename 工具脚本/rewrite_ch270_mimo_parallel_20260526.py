#!/usr/bin/env python3
import concurrent.futures, datetime, json, os, pathlib, re, subprocess, time
ROOT=pathlib.Path('/root/workspace/科武纪元')
RAWDIR=ROOT/'审核记录/六角色外审/raw'; RAWDIR.mkdir(parents=True,exist_ok=True)
EV=ROOT/'审核记录/新卷写作队列/events_266_275_20260526.jsonl'
Q=ROOT/'审核记录/新卷写作队列/queue_266_275_20260526.json'
NEW=ROOT/'新版/第270章.md'
REPORT=ROOT/'审核记录/六角色外审/第270章_闭环报告_20260526.md'
TASK=ROOT/'审核记录/六角色外审/第270章_写前任务卡_20260526.md'
CH=270
BANS=['意味着','仿佛','似乎','微微','宛如','犹如','悄然','骤然','瞬间','极致','无数','彻底','崩塌','撕裂','震撼']
REPS={'意味着':'代表','仿佛':'像','似乎':'像','微微':'','宛如':'像','犹如':'像','悄然':'','骤然':'','瞬间':'','极致':'','无数':'大量','彻底':'','崩塌':'失效','撕裂':'分开','震撼':'冲击'}

def now(): return datetime.datetime.now().isoformat(timespec='seconds')
def event(ev,st,msg='',**kw):
    d={'ts':now(),'chapter':CH,'event':ev,'status':st,'msg':msg}; d.update(kw)
    with EV.open('a',encoding='utf-8') as f: f.write(json.dumps(d,ensure_ascii=False)+'\n')
def update(status=None, **kw):
    q=json.loads(Q.read_text(encoding='utf-8'))
    q['stage']='RUNNING'; q['current_chapter']=CH; q['current_stage']=kw.get('current_stage',status or ''); q['updated_at']=now()
    for c in q.get('chapters',[]):
        if c.get('chapter')==CH:
            if status: c['status']=status
            c.update({k:v for k,v in kw.items() if k!='current_stage'}); c['updated_at']=now()
    Q.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
def call(provider, model, prompt, timeout=480):
    env=os.environ.copy(); env['HERMES_STREAM_READ_TIMEOUT']='420'
    t=time.time()
    p=subprocess.run(['hermes','chat','-Q','--provider',provider,'--model',model,'-q',prompt],text=True,capture_output=True,timeout=timeout,env=env)
    return {'provider':provider,'model':model,'exit_code':p.returncode,'duration':round(time.time()-t,2),'stdout':p.stdout.strip(),'stderr':p.stderr.strip()}
def clean(s):
    s=re.sub(r'^```.*?\n|```$','',s.strip(),flags=re.S)
    for a,b in REPS.items(): s=s.replace(a,b)
    s=re.sub(r'^我逐项.*?全文如下：\s*','',s,flags=re.S)
    s=s.replace('\n---\n','\n')
    return s.strip()
def fanqie_count(text):
    lines=text.splitlines(); title=lines[0].strip() if lines else ''
    body=''.join(lines[1:])
    return len(re.sub(r'\s+','',body))-len(re.sub(r'\s+','',title))
def make_prompt(prev, outline, variant):
    focus={
      'A':'主打工程动作链：设备、箱体、温度、协议队列、三条舰队轨道数据。',
      'B':'主打人物选择链：林星辰、方宁、联合政府代表、舰队指挥员各自付出代价。',
      'C':'主打硬科幻校验链：400km光程1.3毫秒；秒级等待归因协议/设备/队列；温度单调。'
    }[variant]
    return f'''你是《科武纪元》作者OS。请重写第270章完整正文。不是提纲，不是修订说明。

硬要求：
- 首行必须是：第270章 第三次校验
- 只输出正文，末尾写（本章完）
- 番茄口径≥3600字，目标4200-6200字；不得低于3000
- 承接第269章：五节点、索引签名异常、拓扑同构孵化舱、箱体升温、三条舰队轨道数据、联合政府决策压力
- 本章只推进“第三次校验”：发现第二个回声/异常的可验证证据，留下第271章处理空间
- 不提前解决全部谜题，不引入新大设定
- 不得双稿拼接、不得自我说明、不得出现“我逐项检查后”等元话语
- 400km光程只能约1.3毫秒；秒级等待只能来自协议、队列、设备响应
- 温度线单调，不得回跳；人物位置不得跳跃
- 写物理反馈、屏幕数值、设备噪声、手部动作、决策代价
- 禁词勿用：{','.join(BANS)}
- 本版本侧重：{focus}

上一章末段：
{prev[-3500:]}

大纲参考节选：
{outline[-10000:]}
'''
def candidate(variant, prev, outline):
    prompt=make_prompt(prev,outline,variant)
    res=call('xiaomi','mimo-v2.5-pro',prompt,timeout=600)
    text=clean(res.get('stdout','')) if res.get('exit_code')==0 else ''
    if text and not text.startswith('第270章'):
        text='第270章 第三次校验\n\n'+text
    cnt=fanqie_count(text) if text else 0
    bans=[b for b in BANS if b in text]
    out={'variant':variant,'result':res,'text':text,'fanqie_count':cnt,'bans':bans,'ok':res.get('exit_code')==0 and cnt>=3000 and not bans and len(text)>2500}
    (RAWDIR/f'第270章_mimo_parallel_{variant}.json').write_text(json.dumps({k:v for k,v in out.items() if k!='text'}|{'text_preview':text[:2000]},ensure_ascii=False,indent=2),encoding='utf-8')
    (RAWDIR/f'第270章_mimo_parallel_{variant}.md').write_text(text+'\n',encoding='utf-8')
    event('MIMO_PARALLEL_CANDIDATE_DONE','RUNNING',f'{variant} count={cnt} bans={len(bans)} ok={out["ok"]}',variant=variant,fanqie_count=cnt,bans=bans,ok=out['ok'])
    return out

def main():
    event('MIMO_PARALLEL_REWRITE_START','RUNNING','3 x mimo-v2.5-pro full rewrite')
    update('RUNNING',current_stage='MIMO_PARALLEL_REWRITE',next_action='3_mimo_candidates')
    prev=(ROOT/'新版/第269章.md').read_text(encoding='utf-8') if (ROOT/'新版/第269章.md').exists() else ''
    outline=(ROOT/'科武纪元大纲 V8_完整版.md').read_text(encoding='utf-8')[:30000] if (ROOT/'科武纪元大纲 V8_完整版.md').exists() else ''
    TASK.write_text('# 第270章 写前任务卡\n\n方式：3路 MiMo v2.5 Pro 并发整章重写，机器门禁选优，WF/Qwen/ZAI复审。\n红线：番茄口径≥3000；禁词0；不拼接；不上传番茄。\n',encoding='utf-8')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futs=[ex.submit(candidate,v,prev,outline) for v in ['A','B','C']]
        cands=[f.result() for f in concurrent.futures.as_completed(futs)]
    okc=[c for c in cands if c['ok']]
    if not okc:
        event('MACHINE_GATE_FAIL','FAILED','no parallel candidate passed',candidates=[{'v':c['variant'],'count':c['fanqie_count'],'bans':c['bans'],'exit':c['result']['exit_code']} for c in cands])
        update('FAILED',fail_reason='no mimo parallel candidate passed',next_action='retry_parallel_or_fallback')
        return
    best=sorted(okc,key=lambda c:(c['fanqie_count'], c['variant']),reverse=True)[0]
    text=best['text']
    NEW.write_text(text+'\n',encoding='utf-8')
    event('MIMO_PARALLEL_SELECTED','RUNNING',f'selected={best["variant"]} count={best["fanqie_count"]}',variant=best['variant'],fanqie_count=best['fanqie_count'])
    ed=call('custom:WF','claude-opus-4-7-high-fast',f'你是编辑OS。审第270章实际正文。只输出：结论：PASS/FAIL；必改项≤3；理由≤200字。检查大纲对齐、时间线、无拼接、人物位置、硬科幻逻辑。正文：{text[:24000]}',timeout=300)
    rd=call('alibaba','qwen3.6-plus',f'你是读者。审第270章实际正文。只输出：结论：PASS/FAIL；劝退点≤3；理由≤200字。正文：{text[:22000]}',timeout=220)
    ad=call('zai','glm-5.1',f'你是科学/军事顾问。审第270章硬伤。只输出：结论：PASS/FAIL；硬伤≤3；理由≤200字。正文：{text[:22000]}',timeout=260)
    reviews={'editor':ed,'reader':rd,'advisor':ad}
    (RAWDIR/'第270章_mimo_parallel_reviews.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2),encoding='utf-8')
    def passp(r):
        s=r.get('stdout',''); head=s.split('结论',1)[-1][:30]
        return r.get('exit_code')==0 and 'PASS' in s and 'FAIL' not in head
    review_ok=all(passp(r) for r in reviews.values())
    REPORT.write_text(f'''# 第270章 闭环报告

时间：{now()}
结论：{'FULL_LOOP_PASS' if review_ok else 'REVIEW_FAIL'}
方式：3路 MiMo v2.5 Pro 并发整章重写；选中候选 {best['variant']}。

## 门禁
- 番茄口径：{best['fanqie_count']}
- 禁词：{len(best['bans'])}
- 上传边界：未生成已投稿TXT，未上传番茄

## 候选
{json.dumps([{'variant':c['variant'],'count':c['fanqie_count'],'bans':len(c['bans']),'exit':c['result']['exit_code'],'duration':c['result']['duration'],'ok':c['ok']} for c in sorted(cands,key=lambda x:x['variant'])],ensure_ascii=False,indent=2)}

## 模型证据
- 作者：3 x xiaomi/mimo-v2.5-pro
- 编辑：custom:WF/claude-opus-4-7-high-fast exit={ed['exit_code']} duration={ed['duration']}
- 读者：alibaba/qwen3.6-plus exit={rd['exit_code']} duration={rd['duration']}
- 顾问：zai/glm-5.1 exit={ad['exit_code']} duration={ad['duration']}

## 编辑
{ed.get('stdout','')}

## 读者
{rd.get('stdout','')}

## 顾问
{ad.get('stdout','')}
''',encoding='utf-8')
    if review_ok:
        files=[NEW,REPORT,TASK,RAWDIR/'第270章_mimo_parallel_reviews.json']
        files += [RAWDIR/f'第270章_mimo_parallel_{v}.json' for v in ['A','B','C']]
        files += [RAWDIR/f'第270章_mimo_parallel_{v}.md' for v in ['A','B','C']]
        subprocess.run(['git','-C',str(ROOT),'add','-f']+[str(p.relative_to(ROOT)) for p in files],check=False)
        cp=subprocess.run(['git','-C',str(ROOT),'commit','-m','write: chapter 270 mimo parallel rewrite'],text=True,capture_output=True)
        commit=subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],text=True,capture_output=True).stdout.strip()
        update('FULL_LOOP_PASS',report_path=str(REPORT),git_commit=commit,next_action='continue_271')
        event('FULL_LOOP_PASS','FULL_LOOP_PASS','chapter 270 closed by parallel mimo',report_path=str(REPORT),git_commit=commit,fanqie_count=best['fanqie_count'],variant=best['variant'],next_action='continue_271')
    else:
        fail='\n'.join(k+': '+v.get('stdout','')[:400] for k,v in reviews.items())
        update('REVIEW_FAIL',report_path=str(REPORT),fail_reason=fail,next_action='repair_or_retry_parallel')
        event('REVIEW_FAIL','FAILED','parallel selected candidate review fail',report_path=str(REPORT),variant=best['variant'])
if __name__=='__main__': main()
