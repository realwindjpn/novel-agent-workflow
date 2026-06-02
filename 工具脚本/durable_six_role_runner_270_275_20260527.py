#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Durable six-role queue runner for ch270-275.
Runs outside chat turn. Main controller only monitors EVENTS/QUEUE.
"""
import os, re, json, time, pathlib, subprocess, datetime, traceback

BASE=pathlib.Path('/root/workspace/科武纪元')
QDIR=BASE/'审核记录/新卷写作队列'
REVDIR=BASE/'审核记录/六角色外审'
RAWDIR=REVDIR/'raw'
QUEUE=QDIR/'queue_266_275_20260526.json'
EVENTS=QDIR/'events_266_275_20260526.jsonl'
RUNLOG=QDIR/'durable_runner_270_275_20260527.log'
OUTLINE_CAND=[BASE/'wiki/raw/outline/科武纪元大纲_latest.md', BASE/'科武纪元大纲 V8_完整版.md']
CHAPTERS=list(range(270,276))
BANS=['意味着','仿佛','似乎','微微','宛如','犹如','悄然','骤然','瞬间','极致','无数','彻底','崩塌','撕裂','震撼','缓缓','不禁','不由得','这一刻','更是','这不仅是','某种意义上']
REPL={'意味着':'代表','仿佛':'像','似乎':'像','微微':'','宛如':'像','犹如':'像','悄然':'','骤然':'','瞬间':'','极致':'','无数':'大量','彻底':'','崩塌':'失效','撕裂':'分开','震撼':'冲击','缓缓':'','不禁':'','不由得':'','这一刻':'此时','更是':'也是','这不仅是':'这是','某种意义上':''}
AUTHOR_PRIMARY=('xiaomi','mimo-v2.5-pro')
WF=('custom:WF','claude-opus-4-7-high-fast')
QWEN=('alibaba','qwen3.6-plus')
ZAI=('zai','glm-5.1')
FALLBACKS=[WF,ZAI,QWEN,('freemodel','gpt-5.5')]

def now(): return datetime.datetime.now().isoformat(timespec='seconds')
def log(s):
    RUNLOG.parent.mkdir(parents=True,exist_ok=True)
    with RUNLOG.open('a',encoding='utf-8') as f: f.write(f'[{now()}] {s}\n')
def loadq(): return json.loads(QUEUE.read_text(encoding='utf-8'))
def saveq(q):
    q['updated_at']=now(); q['pid']=os.getpid(); QUEUE.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
def event(ch, ev, status='RUNNING', msg='', **kw):
    rec={'ts':now(),'chapter':ch,'event':ev,'status':status,'msg':msg}; rec.update(kw)
    with EVENTS.open('a',encoding='utf-8') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    q=loadq(); q['stage']='RUNNING' if status not in ('FAILED','BLOCKED','DONE') else q.get('stage','RUNNING')
    q['current_chapter']=ch; q['current_stage']=ev; q.setdefault('event_log',[]).append(rec); q['event_log']=q['event_log'][-80:]
    for c in q.get('chapters',[]):
        if c.get('chapter')==ch:
            c['status']=status; c['updated_at']=now()
            for k,v in kw.items():
                if k in ('report_path','git_commit','fail_reason','next_action','fanqie_count','cached_segments'): c[k]=v
    saveq(q)

def call(provider,model,prompt,timeout=520,max_chars=70000):
    env=os.environ.copy(); env['HERMES_STREAM_READ_TIMEOUT']=str(min(timeout,480))
    cmd=['hermes','chat','-Q','--provider',provider,'--model',model,'-q',prompt]
    t=time.time()
    try:
        p=subprocess.run(cmd,cwd=str(BASE),text=True,capture_output=True,timeout=timeout,env=env)
        err=(p.stderr or '').strip(); out=(p.stdout or '').strip()
        sid=re.search(r'session_id:\s*(\S+)',err)
        return {'provider':provider,'model':model,'exit_code':p.returncode,'duration':round(time.time()-t,2),'stdout':out[:max_chars],'stderr':err[-4000:],'session_id':sid.group(1) if sid else ''}
    except subprocess.TimeoutExpired:
        return {'provider':provider,'model':model,'exit_code':124,'duration':round(time.time()-t,2),'stdout':'','stderr':'TIMEOUT','session_id':''}

def clean(s):
    s=re.sub(r'^```.*?\n|```$','',s.strip(),flags=re.S)
    s=re.sub(r'^我(已|来|将).*?全文如下[:：]\s*','',s,flags=re.S)
    s=s.replace('\n---\n','\n')
    for a,b in REPL.items(): s=s.replace(a,b)
    return s.strip()
def fanqie_count(t):
    lines=t.splitlines(); title=lines[0] if lines else ''
    return len(re.sub(r'\s+','', ''.join(lines[1:])))-len(re.sub(r'\s+','',title))
def gate(ch,text):
    probs=[]; n=fanqie_count(text); hits=[b for b in BANS if b in text]
    if n<3000: probs.append(f'COUNT:{n}')
    if hits: probs.append('BANS:'+','.join(hits))
    if not text.startswith(f'第{ch}章'): probs.append('BAD_TITLE')
    if '（本章完）' not in text[-80:]: probs.append('BAD_END')
    if '...' in text or '…' in text or '[truncated]' in text or '\\...' in text: probs.append('TRUNCATION_MARK')
    return probs,n,hits

def passp(r):
    s=r.get('stdout',''); head=s.split('结论',1)[-1][:60]
    return r.get('exit_code')==0 and 'PASS' in s and 'FAIL' not in head

def outline_text():
    for p in OUTLINE_CAND:
        if p.exists(): return p.read_text(encoding='utf-8')
    return ''
def outline_line(ch, outline):
    m=re.search(rf'第{ch}章\s*[|｜][^\n]+',outline)
    return m.group(0) if m else ''
def title_from_line(ch,line):
    if line:
        parts=re.split(r'[|｜]',line)
        if len(parts)>=3: return parts[2].strip()
    return '未定题'

def build_prompt_new(ch, outline, prev):
    line=outline_line(ch,outline); title=title_from_line(ch,line)
    return title, f'''你是《科武纪元》作者OS。请写第{ch}章完整正文。只输出正文，不要解释。
首行：第{ch}章 {title}
末尾：（本章完）
番茄口径4200-6200字，必须≥3000。
承接上一章，不重置人物位置/技术状态。
写动作链、工程代价、资源代价、身体反馈、数据读数；勿概念讲稿。
禁词勿用：{','.join(BANS)}
大纲行：{line}
上一章末段：
{prev[-4500:]}
大纲节选：
{outline[-10000:]}
'''

def repair_prompt(ch,text,report,mode):
    return f'''你是《科武纪元》{mode}修订模型。请修订第{ch}章全文，只输出修后完整正文，不解释。
硬要求：首行“第{ch}章 ...”；末尾“（本章完）”；番茄口径≥3000；禁词勿用：{','.join(BANS)}。
不要截断，不要省略，不要写“...”。
只修失败点，不重置已通过的数值链/人物位置/章末钩子。
失败报告：
{report[-5000:]}
原文：
{text}
'''

def write_task_card(ch, title, mode):
    p=REVDIR/f'第{ch}章_写前任务卡_20260526.md'
    p.write_text(f'# 第{ch}章 写前任务卡\n\n方式：durable六角色runner。模式：{mode}\n红线：番茄口径≥3000；禁词0；不拼接；不上传番茄；PASS后续下一章。\n',encoding='utf-8')
    return p

def review_all(ch,text):
    event(ch,'EDITOR_REVIEW','RUNNING','WF editor')
    ed=call(*WF,f'你是编辑OS。审第{ch}章实际正文。只输出：结论：PASS/FAIL；必改项≤3；理由≤220字。重点查大纲对齐、时间线、拼接/截断、人物压力、数值连续。正文：{text[:26000]}',timeout=300)
    event(ch,'READER_REVIEW','RUNNING','Qwen reader')
    rd=call(*QWEN,f'你是读者。审第{ch}章实际正文。只输出：结论：PASS/FAIL；劝退点≤3；理由≤220字。正文：{text[:24000]}',timeout=260)
    event(ch,'ADVISOR_REVIEW','RUNNING','ZAI advisor')
    ad=call(*ZAI,f'你是科学/军事顾问。审第{ch}章硬伤。只输出：结论：PASS/FAIL；硬伤≤3；理由≤240字。正文：{text[:24000]}',timeout=320)
    return {'editor':ed,'reader':rd,'advisor':ad}

def choose_repair_route(reviews):
    if not passp(reviews.get('reader',{})): return QWEN,'读者'
    if not passp(reviews.get('advisor',{})): return ZAI,'顾问'
    return WF,'编辑'

def sync_commit(ch, files):
    subprocess.run(['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(ch),'--message',f'第{ch}章durable六角色闭环','--no-git'],cwd='/root/workspace',text=True,capture_output=True,timeout=240)
    src=BASE/'新版'/f'第{ch}章.md'; wiki=BASE/'wiki/chapters'/f'ch{ch:03d}.md'
    files=list(files)+[src,wiki,QUEUE,EVENTS,BASE/'STATUS.md',BASE/'WAL.md',BASE/'小说综合跟踪表.md']
    existing=[str(p) for p in files if pathlib.Path(p).exists()]
    subprocess.run(['git','-C',str(BASE),'add','-f','--']+existing,text=True,capture_output=True,timeout=120)
    subprocess.run(['git','-C',str(BASE),'commit','-m',f'write: chapter {ch} durable six-role'],text=True,capture_output=True,timeout=180)
    sha=subprocess.run(['git','-C',str(BASE),'rev-parse','--short','HEAD'],text=True,capture_output=True,timeout=30).stdout.strip()
    return sha

def process_chapter(ch, outline):
    src=BASE/'新版'/f'第{ch}章.md'; report=REVDIR/f'第{ch}章_闭环报告_20260526.md'
    prev=(BASE/'新版'/f'第{ch-1}章.md').read_text(encoding='utf-8') if (BASE/'新版'/f'第{ch-1}章.md').exists() else ''
    line=outline_line(ch,outline); title=title_from_line(ch,line) or '第三次校验'
    card=write_task_card(ch,title,'repair-existing' if src.exists() and ch==270 else 'new-full')
    event(ch,'START','RUNNING','durable chapter start')
    if src.exists() and ch==270 and report.exists() and 'REVIEW_FAIL' in report.read_text(encoding='utf-8'):
        text=src.read_text(encoding='utf-8')
        prompt=repair_prompt(ch,text,report.read_text(encoding='utf-8'),'WF编辑')
        route=WF; mode='wf_repair_existing'
    else:
        title,prompt=build_prompt_new(ch,outline,prev); route=AUTHOR_PRIMARY; mode='mimo_new_full'
    model_logs=[]
    for round_no in range(1,5):
        event(ch,'AUTHOR_OR_REPAIR','RUNNING',f'{mode} round {round_no}',next_action='model_call')
        res=call(*route,prompt,timeout=620 if route[0]=='xiaomi' else 520)
        model_logs.append({'stage':mode,'round':round_no,**res})
        (RAWDIR/f'第{ch}章_durable_{mode}_round{round_no}.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
        if res['exit_code']!=0 or len(res.get('stdout',''))<2500:
            route=FALLBACKS[min(round_no-1,len(FALLBACKS)-1)]; mode='fallback_author'; prompt=prompt+'\n上一轮失败/过短。请完整输出正文，勿截断。'; continue
        text=clean(res['stdout'])
        if not text.startswith(f'第{ch}章'):
            text=f'第{ch}章 {title}\n\n'+text
        src.write_text(text+'\n',encoding='utf-8')
        probs,n,hits=gate(ch,text)
        event(ch,'MACHINE_GATE','RUNNING' if not probs else 'FAILED', ';'.join(probs) or 'PASS', fanqie_count=n, fail_reason=';'.join(probs), next_action='review' if not probs else 'repair')
        if probs:
            route=AUTHOR_PRIMARY; mode='machine_repair'; prompt=repair_prompt(ch,text,'机器门禁失败：'+';'.join(probs),'作者位'); continue
        reviews=review_all(ch,text)
        (RAWDIR/f'第{ch}章_durable_reviews_round{round_no}.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2),encoding='utf-8')
        ok=all(passp(v) for v in reviews.values())
        report.write_text(f'''# 第{ch}章 闭环报告

时间：{now()}
结论：{'FULL_LOOP_PASS' if ok else 'REVIEW_FAIL'}
方式：durable六角色runner｜{mode}｜round {round_no}

## 门禁
- 番茄口径：{n}
- 禁词：{len(hits)}
- 上传边界：未生成已投稿TXT，未上传番茄

## 模型记录
{json.dumps(model_logs,ensure_ascii=False,indent=2)[:12000]}

## 编辑
{reviews['editor']['stdout']}

## 读者
{reviews['reader']['stdout']}

## 顾问
{reviews['advisor']['stdout']}
''',encoding='utf-8')
        if ok:
            sha=sync_commit(ch,[report,card]+list(RAWDIR.glob(f'第{ch}章_durable_*')))
            event(ch,'FULL_LOOP_PASS','FULL_LOOP_PASS','chapter closed',report_path=str(report),git_commit=sha,fanqie_count=n,next_action=f'continue_{ch+1}')
            return True
        route,role=choose_repair_route(reviews); mode=f'{role}_repair'
        issues='\n'.join([k+': '+v.get('stdout','') for k,v in reviews.items()])
        prompt=repair_prompt(ch,text,issues,role)
        event(ch,'REPAIR_QUEUED','RUNNING',f'{role} repairs review fail',fail_reason=issues[:1000],next_action='repair_round')
    event(ch,'BLOCKED','FAILED','max repair rounds exceeded',report_path=str(report),fail_reason='max repair rounds exceeded',next_action='主控查raw/report后接管')
    q=loadq(); q['stage']='BLOCKED'; saveq(q)
    return False

def main():
    QDIR.mkdir(parents=True,exist_ok=True); REVDIR.mkdir(parents=True,exist_ok=True); RAWDIR.mkdir(parents=True,exist_ok=True)
    q=loadq(); q['stage']='RUNNING'; q['pid']=os.getpid(); q['current_stage']='DURABLE_RUNNER_START'; saveq(q)
    event(None,'DURABLE_RUNNER_START','RUNNING',f'pid {os.getpid()}')
    outline=outline_text()
    for ch in CHAPTERS:
        item=next((c for c in loadq().get('chapters',[]) if c.get('chapter')==ch),{})
        if item.get('status')=='FULL_LOOP_PASS':
            event(ch,'SKIP_DONE','FULL_LOOP_PASS','already closed'); continue
        ok=process_chapter(ch,outline)
        if not ok: return 1
    q=loadq(); q['stage']='DONE'; q['current_stage']='DONE'; saveq(q)
    event(None,'DONE','DONE','270-275 complete')
    return 0
if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as e:
        log(traceback.format_exc())
        try:
            q=loadq(); q['stage']='BLOCKED'; q['current_stage']='RUNNER_EXCEPTION'; q['fail_reason']=str(e); saveq(q)
            event(None,'RUNNER_EXCEPTION','FAILED',str(e))
        except Exception: pass
        raise
