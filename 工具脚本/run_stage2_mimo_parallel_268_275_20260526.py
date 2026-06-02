#!/usr/bin/env python3
import os, re, json, time, pathlib, datetime, subprocess, concurrent.futures
BASE=pathlib.Path('/root/workspace/科武纪元')
QDIR=BASE/'审核记录/新卷写作队列'; REVDIR=BASE/'审核记录/六角色外审'; RAWDIR=REVDIR/'raw'
OUTLINE=BASE/'wiki/raw/outline/科武纪元大纲_latest.md'
QUEUE=QDIR/'queue_266_275_20260526.json'; EVENTS=QDIR/'events_266_275_20260526.jsonl'; REPORT=QDIR/'阶段二_266_275_执行报告_20260526.md'
BAN=['仿佛','微微','缓缓','意味着','意识到','不禁','不由得','宛如','这一刻','某种意义上','这不仅是','更是','时代洪流','命运齿轮','淡淡']
CHAPTERS=list(range(268,276))
SEG_HINTS={1:'开场承接上章，明确当前压力/场景/目标，给身体代价和可见任务。',2:'推进技术解密/冲突升级，给数据链、操作链、人物选择。',3:'外部反压/资源代价/制度或军事压力，必须有动作和后果。',4:'收束本章功能，留下下一章钩子，末段只写正文，不写本章完。'}

def now(): return datetime.datetime.now().isoformat(timespec='seconds')
def loadq(): return json.loads(QUEUE.read_text(encoding='utf-8')) if QUEUE.exists() else {'stage':'INIT','chapters':[]}
def saveq(q): q['updated_at']=now(); q['pid']=os.getpid(); QUEUE.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
def event(ch,ev,status='',msg='',extra=None):
    rec={'ts':now(),'chapter':ch,'event':ev,'status':status,'msg':msg}
    if extra: rec.update(extra)
    with EVENTS.open('a',encoding='utf-8') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    q=loadq(); q.setdefault('event_log',[]).append(rec); q['event_log']=q['event_log'][-100:]; q['current_chapter']=ch; q['current_stage']=ev
    for c in q.get('chapters',[]):
        if c.get('chapter')==ch:
            c['status']=status or c.get('status','RUNNING'); c['updated_at']=now()
            if extra:
                for k,v in extra.items():
                    if k in c: c[k]=v
    saveq(q)

def call_model(provider,model,prompt,timeout=180,max_chars=22000):
    cmd=['hermes','chat','-Q','--provider',provider,'--model',model,'-q',prompt]
    env=os.environ.copy()
    if provider=='xiaomi': env['HERMES_STREAM_READ_TIMEOUT']=str(max(180,min(timeout,240)))
    t=time.time()
    try:
        p=subprocess.run(cmd,cwd=str(BASE),text=True,capture_output=True,timeout=timeout,env=env)
        err=(p.stderr or '').strip(); m=re.search(r'session_id:\s*(\S+)',err)
        return {'requested_provider':provider,'requested_model':model,'session_id':m.group(1) if m else '', 'duration':round(time.time()-t,2),'exit_code':p.returncode,'stdout':(p.stdout or '').strip()[:max_chars],'stderr':err[-2000:],'fail_reason':'' if p.returncode==0 else err[-1000:]}
    except subprocess.TimeoutExpired:
        return {'requested_provider':provider,'requested_model':model,'session_id':'','duration':round(time.time()-t,2),'exit_code':124,'stdout':'','stderr':'TIMEOUT','fail_reason':'TIMEOUT'}

def clean(s):
    s=re.sub(r'```(?:markdown|md)?','',s).replace('```','').strip()
    s=re.sub(r'^\s*第\d+段[:：]\s*','',s)
    s=re.sub(r'^#\s*第\d+章[^\n]*\n*','',s).strip()
    s=re.sub(r'（本章完）\s*$','',s).strip()
    s=s.replace('（本段完）','')
    # strip common prompt echoes
    for marker in ['## 分段建议','上文/已写片段：','输出本段正文。','正文：']:
        if marker in s:
            s=s.split(marker)[0].strip()
    repl={'意味着':'代表','仿佛':'像','微微':'','缓缓':'','意识到':'判断出','不禁':'','不由得':'','宛如':'像','这一刻':'此时','某种意义上':'','这不仅是':'这是','更是':'也是','时代洪流':'局势','命运齿轮':'局面','淡淡':''}
    for a,b in repl.items(): s=s.replace(a,b)
    return s.strip()

def count(text): return len(re.sub(r'\s+','', ''.join(text.splitlines()[1:])))
def gate(ch,text):
    probs=[]
    if not text.startswith(f'# 第{ch}章 '): probs.append('BAD_TITLE')
    if not text.rstrip().endswith('（本章完）'): probs.append('BAD_END')
    if '[[' in text or ']]' in text: probs.append('WIKILINK')
    hits=[w for w in BAN if w in text]
    if hits: probs.append('BAN:'+','.join(hits))
    for bad in ['任务卡','分段建议','正文：','输出本段正文','本段完']:
        if bad in text: probs.append('META:'+bad)
    c=count(text)
    if c<3000: probs.append(f'COUNT:{c}')
    return probs,c

def outline_map():
    txt=OUTLINE.read_text(encoding='utf-8'); d={}
    for ch in CHAPTERS:
        m=re.search(rf'第{ch}章\s*\|[^\n]+',txt)
        if not m: raise RuntimeError(f'outline missing {ch}')
        d[ch]=m.group(0)
    return d

def title_from(outline,ch):
    m=re.search(rf'第{ch}章 \| [^|]+ \| ([^|]+)', outline)
    return m.group(1).strip() if m else f'第{ch}章'

def build_card(ch,outline,prev):
    title=title_from(outline,ch)
    card=f'''# 第{ch}章 写前任务卡 20260526

## 大纲行
{outline}

## 目标
- 标题：第{ch}章 {title}
- 番茄口径≥3000；3600仅作节奏参考，不作硬上限。
- 正文无wikilink/Markdown/草稿标记，首行标题，末尾（本章完）。
- 每段须含动作链、数据/物理反馈、资源代价。

## 上章尾部
{prev[-1800:]}
'''
    p=REVDIR/f'第{ch}章_写前任务卡_20260526.md'; p.write_text(card,encoding='utf-8')
    return title,card,p

def gen_seg(ch,title,card,prev,seg):
    prompt=f'''你是《科武纪元》MiMo作者分身{seg}。只输出正文片段，不解释。
章节：# 第{ch}章 {title}
段落：{seg}/4
本段任务：{SEG_HINTS[seg]}
目标：750-1100番茄字。不得写本章完/本段完/任务卡/说明。
禁词：{','.join(BAN)}
章节任务卡：
{card[:2600]}
上章尾部：
{prev[-1200:]}
只输出本段正文。'''
    res=call_model('xiaomi','mimo-v2.5-pro',prompt,timeout=180)
    part=clean(res['stdout']) if res['exit_code']==0 else ''
    raw=RAWDIR/f'第{ch}章_mimo_parallel_segment_{seg}.md'
    raw.write_text((part if part else 'FAILED\n'+json.dumps(res,ensure_ascii=False,indent=2)),encoding='utf-8')
    return seg,part,res,str(raw)

def review(role,provider,model,ch,text,card):
    prompt=f'''你是《科武纪元》{role}。只看实际正文，输出：结论：PASS/FAIL；必改项≤3；理由≤200字。3600不是上限。
门禁：大纲对齐、番茄≥3000、禁词0、无wikilink、无草稿标记、首行标题、末尾（本章完）、技术/身体/资源代价可见。
任务卡：{card[:1500]}
正文：{text[:18000]}'''
    return call_model(provider,model,prompt,timeout=180)

def is_pass(out):
    head='\n'.join(out.splitlines()[:6])
    return 'PASS' in head and 'FAIL' not in head.split('PASS')[0]

def process_chapter(ch,outlines):
    event(ch,'START','RUNNING','chapter start')
    prev_path=BASE/'新版'/f'第{ch-1}章.md'; prev=prev_path.read_text(encoding='utf-8') if prev_path.exists() else ''
    title,card,card_path=build_card(ch,outlines[ch],prev); event(ch,'TASK_CARD','RUNNING',str(card_path),{'report_path':str(card_path)})
    event(ch,'MIMO_PARALLEL_START','RUNNING','4 mimo segments concurrently')
    logs=[]; parts=['']*4; raws=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futs=[ex.submit(gen_seg,ch,title,card,prev,i) for i in range(1,5)]
        for fut in concurrent.futures.as_completed(futs):
            seg,part,res,raw=fut.result(); logs.append(res); raws.append(raw)
            if not part or len(part)<300: raise RuntimeError(f'segment {seg} failed')
            parts[seg-1]=part; event(ch,f'MIMO_SEG_{seg}_DONE','RUNNING','cached',{'cached_segments':raws[:]})
    full=f"# 第{ch}章 {title}\n\n"+'\n\n'.join(parts)+'\n\n（本章完）\n'
    full=clean(full); full=f"# 第{ch}章 {title}\n\n"+re.sub(r'^#\s*第\d+章[^\n]*\n*','',full).strip()+"\n\n（本章完）\n"
    src=BASE/'新版'/f'第{ch}章.md'; src.write_text(full,encoding='utf-8')
    probs,c=gate(ch,full)
    if probs: raise RuntimeError('machine gate fail: '+';'.join(probs))
    event(ch,'EDITOR_REVIEW','RUNNING','qwen editor')
    ed=review('编辑复审','alibaba','qwen3.6-plus',ch,full,card); logs.append(ed)
    event(ch,'READER_REVIEW','RUNNING','qwen reader')
    rd=review('读者复审','alibaba','qwen3.6-plus',ch,full,card); logs.append(rd)
    event(ch,'ADVISOR_REVIEW','RUNNING','zai advisor')
    adv=review('科学/军事顾问','zai','glm-5.1',ch,full,card); logs.append(adv)
    if not (is_pass(ed['stdout']) and is_pass(rd['stdout'])):
        raise RuntimeError('review fail: 编辑:\n'+ed['stdout']+'\n读者:\n'+rd['stdout']+'\n顾问:\n'+adv['stdout'])
    report=REVDIR/f'第{ch}章_闭环报告_20260526.md'
    routes='\n'.join(f"- {x['requested_provider']}/{x['requested_model']} exit={x['exit_code']} dur={x['duration']} session={x.get('session_id','')} fail={x.get('fail_reason','')}" for x in logs)
    report.write_text(f'''# 第{ch}章 闭环报告

时间：{now()}
章节：第{ch}章《{title}》
结论：FULL_LOOP_PASS

## 门禁
- 番茄口径：{c}
- 禁词：0
- wikilink：0
- 草稿标记：0
- 首行/末尾：PASS
- 非上传章：未生成已投稿TXT，未上传番茄

## 模型调用记录
{routes}

## 编辑复审
{ed['stdout']}

## 读者复审
{rd['stdout']}

## 顾问轻审
{adv['stdout']}
''',encoding='utf-8')
    sync=subprocess.run(['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(ch),'--message',f'第{ch}章阶段二MiMo并行写作闭环','--no-git'],cwd='/root/workspace',text=True,capture_output=True,timeout=240)
    wiki=BASE/'wiki/chapters'/f'ch{ch:03d}.md'
    if wiki.exists():
        wt=wiki.read_text(encoding='utf-8')
        if '## Full Text' in wt and full[:80] not in wt:
            wiki.write_text(re.sub(r'## Full Text\n.*','## Full Text\n\n'+full,wt,flags=re.S),encoding='utf-8')
    # status/wal minimal append
    stamp=now().replace('T',' ')
    for f,txt in [(BASE/'STATUS.md',f"\n- {stamp} 第{ch}章《{title}》阶段二MiMo并行闭环 FULL_LOOP_PASS。番茄口径 {c}。报告：`{report.relative_to(BASE)}`。\n"),(BASE/'WAL.md',f"\n## {stamp}｜第{ch}章阶段二MiMo并行闭环\n\n- FULL_LOOP_PASS，番茄口径{c}。报告：`{report.relative_to(BASE)}`。\n")]:
        old=f.read_text(encoding='utf-8') if f.exists() else ''
        f.write_text(txt+old,encoding='utf-8')
    files=[str(src),str(wiki),str(card_path),str(report),str(QUEUE),str(EVENTS),str(BASE/'STATUS.md'),str(BASE/'WAL.md')]+raws
    existing=[x for x in files if pathlib.Path(x).exists()]
    subprocess.run(['git','-C',str(BASE),'add','-f','--']+existing,cwd='/root/workspace',timeout=120)
    commit=subprocess.run(['git','-C',str(BASE),'commit','-m',f'write: chapter {ch} stage two mimo parallel'],cwd='/root/workspace',text=True,capture_output=True,timeout=180)
    sha=''
    if commit.returncode==0:
        sha=subprocess.run(['git','-C',str(BASE),'rev-parse','--short','HEAD'],cwd='/root/workspace',text=True,capture_output=True,timeout=30).stdout.strip()
    event(ch,'FULL_LOOP_PASS','FULL_LOOP_PASS','chapter completed',{'report_path':str(report),'git_commit':sha,'fanqie_count':c,'next_action':'continue'})
    return {'chapter':ch,'status':'FULL_LOOP_PASS','count':c,'report':str(report),'commit':sha}

def main():
    RAWDIR.mkdir(parents=True,exist_ok=True); QDIR.mkdir(parents=True,exist_ok=True); REVDIR.mkdir(parents=True,exist_ok=True)
    q=loadq(); q['stage']='RUNNING'; q['pid']=os.getpid(); saveq(q); event(None,'RUNNER_START','RUNNING','parallel runner pid '+str(os.getpid()))
    outlines=outline_map(); results=[]
    for ch in CHAPTERS:
        item=next((c for c in loadq().get('chapters',[]) if c.get('chapter')==ch),{})
        if item.get('status')=='FULL_LOOP_PASS':
            event(ch,'SKIP_DONE','FULL_LOOP_PASS','already closed; continue next chapter'); continue
        try:
            results.append(process_chapter(ch,outlines))
        except Exception as e:
            msg=str(e); event(ch,'FAILED','FAILED',msg,{'fail_reason':msg,'next_action':'controller_takeover_or_retry_mimo_parallel'}); q=loadq(); q['stage']='BLOCKED'; saveq(q); return 1
    q=loadq(); q['stage']='DONE'; q['current_stage']='DONE'; saveq(q); event(None,'DONE','DONE','stage2 complete'); return 0
if __name__=='__main__': raise SystemExit(main())
