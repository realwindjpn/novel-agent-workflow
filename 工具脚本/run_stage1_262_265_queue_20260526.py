#!/usr/bin/env python3
import os, re, json, time, subprocess, datetime, pathlib, textwrap

BASE = pathlib.Path('/root/workspace/科武纪元')
QDIR = BASE / '审核记录' / '新卷写作队列'
REVDIR = BASE / '审核记录' / '六角色外审'
RAWDIR = REVDIR / 'raw'
OUTLINE = BASE / 'wiki' / 'raw' / 'outline' / '科武纪元大纲_latest.md'
QUEUE = QDIR / 'queue_262_265_20260526.json'
EVENTS = QDIR / 'events_262_265_20260526.jsonl'
REPORT = QDIR / '阶段一_262_265_执行报告_20260526.md'

BAN = ['仿佛','微微','缓缓','意味着','意识到','不禁','不由得','宛如','这一刻','某种意义上','这不仅是','更是','时代洪流','命运齿轮','淡淡']
CHAPTERS = [262,263,264,265]
AUTHOR_PRIMARY = ('xiaomi','mimo-v2.5-pro')
AUTHOR_FALLBACKS = [('custom:WF','claude-opus-4-7-high-fast'),('zai','glm-5.1'),('alibaba','qwen3.6-plus'),('freemodel','gpt-5.5')]
EDITOR_ROUTES = [('custom:WF','claude-opus-4-7-high-fast'),('alibaba','qwen3.6-plus')]
READER_ROUTES = [('alibaba','qwen3.6-plus'),('zai','glm-5.1'),('freemodel','gpt-5.5')]
ADVISOR_ROUTES = [('zai','glm-5.1'),('freemodel','gpt-5.5')]


def now(): return datetime.datetime.now().isoformat(timespec='seconds')

def loadq():
    if QUEUE.exists(): return json.loads(QUEUE.read_text(encoding='utf-8'))
    return {'stage':'INIT','chapters':[],'current_chapter':None,'current_stage':'','updated_at':now(),'pid':os.getpid(),'event_log':[]}

def saveq(q):
    q['updated_at']=now(); q['pid']=os.getpid()
    QUEUE.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')

def event(ch, ev, status='', msg='', extra=None):
    rec={'ts':now(),'chapter':ch,'event':ev,'status':status,'msg':msg}
    if extra: rec.update(extra)
    with EVENTS.open('a',encoding='utf-8') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    q=loadq(); q.setdefault('event_log',[]).append(rec); q['event_log']=q['event_log'][-80:]
    q['current_chapter']=ch; q['current_stage']=ev
    for c in q.get('chapters',[]):
        if c.get('chapter')==ch:
            c['status']=status or c.get('status','RUNNING'); c['updated_at']=now()
            if extra:
                for k,v in extra.items():
                    if k in c: c[k]=v
    saveq(q)

def chapter_item(ch):
    q=loadq()
    for c in q.get('chapters',[]):
        if c.get('chapter')==ch: return c
    raise RuntimeError('chapter missing')

def run(cmd, timeout=120, cwd=str(BASE)):
    t=time.time()
    p=subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    return {'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'duration':round(time.time()-t,2)}

def call_model(provider, model, prompt, timeout=180, max_chars=20000):
    cmd=['hermes','chat','-Q','--provider',provider,'--model',model,'-q',prompt]
    env=os.environ.copy()
    if provider == 'xiaomi':
        # MiMo Pro often needs >120s before stream stays healthy; keep internal read timeout
        # aligned with the stage runner's outer timeout instead of Hermes' 120s default.
        env['HERMES_STREAM_READ_TIMEOUT'] = str(max(150, min(timeout, 240)))
    t=time.time()
    try:
        p=subprocess.run(cmd, cwd=str(BASE), text=True, capture_output=True, timeout=timeout, env=env)
        out=(p.stdout or '').strip()
        err=(p.stderr or '').strip()
        m=re.search(r'session_id:\s*(\S+)', err)
        return {'requested_provider':provider,'requested_model':model,'returned_model':model,'session_id':m.group(1) if m else '', 'duration':round(time.time()-t,2),'exit_code':p.returncode,'stdout':out[:max_chars],'stderr':err[-3000:],'fail_reason':'' if p.returncode==0 else err[-1000:]}
    except subprocess.TimeoutExpired:
        return {'requested_provider':provider,'requested_model':model,'returned_model':'','session_id':'','duration':round(time.time()-t,2),'exit_code':124,'stdout':'','stderr':'TIMEOUT','fail_reason':'TIMEOUT'}

def fanqie_count(text):
    lines=text.splitlines()
    title=lines[0].strip() if lines else ''
    body=''.join(lines[1:])
    return len(re.sub(r'\s+','',body))

def outline_lines():
    txt=OUTLINE.read_text(encoding='utf-8')
    d={}
    for ch in CHAPTERS:
        m=re.search(rf'第{ch}章\s*\|[^\n]+', txt)
        if not m: raise RuntimeError(f'outline missing {ch}')
        d[ch]=m.group(0)
    return d

def read_short(path, limit=9000):
    txt=path.read_text(encoding='utf-8')
    return txt[-limit:]

def clean_body(s):
    s=re.sub(r'```(?:markdown|md)?','',s).replace('```','')
    s=re.sub(r'^\s*第\d+段[:：]\s*','',s.strip())
    s=s.replace('---','')
    return s.strip()

def build_task_card(ch, outline, prev_summary):
    title = re.search(r'第%d章 \| [^|]+ \| ([^|]+)'%ch, outline).group(1).strip()
    card=f"""# 第{ch}章 写前任务卡 20260526

## 大纲行
{outline}

## 承接第261章硬钩
- 真气“逻辑错误残留”必须在262-263兑现：先身体异常/步法偏差，再给代价，不可空置。
- 第二节点与铁幕监测站重叠必须推动外部冲突：监测、封锁、干扰、近距离行动至少出现一项。
- 地火22分钟延迟继续作为信息压力，不得写成地球即时指挥。

## 本章目标
- 标题：第{ch}章 {title}
- 番茄口径：≥3000；3600仅作节奏参考，不作硬上限。
- 正文无 wikilink，无 Markdown 分隔线，首行 `# 第{ch}章 {title}`，末尾 `（本章完）`。
- 技术写法：操作、数据、资源代价、身体反馈先行；禁宏大空话。

## 上章尾部
{prev_summary}

## 分段建议
1. 场景一：承接上章压力，给可见故障/任务。
2. 场景二：人物动作推进技术/冲突。
3. 场景三：铁幕/环境反压，付出代价。
4. 场景四：章末钩子，留下下一章必须处理的问题。
"""
    path=REVDIR / f'第{ch}章_写前任务卡_20260526.md'
    path.write_text(card,encoding='utf-8')
    return title, path, card

def author_segment(ch,title,card,prev_text,seg,total,history):
    context_blob=(prev_text+'\n'+history)[-4500:]
    base=f"""你是《科武纪元》作者位。只输出正文片段，不解释。
章节：# 第{ch}章 {title}
段落：{seg}/{total}
目标：本段600-1000番茄字。动作链、物理反馈、数据、代价。禁止空话。
禁词：{','.join(BAN)}
不得出现 wikilink、Markdown表格、项目符号、作者说明。
本章任务卡：
{card[:3500]}
上文/已写片段：
{context_blob}
输出本段正文。"""
    routes=[AUTHOR_PRIMARY]+AUTHOR_FALLBACKS
    attempts=[]
    for idx,(p,m) in enumerate(routes):
        prompt=base if idx==0 else base+"\n上一作者路由失败或超时。请缩短为650-800字，保持衔接。"
        res=call_model(p,m,prompt,timeout=180 if p!='xiaomi' else 150)
        attempts.append(res)
        if res['exit_code']==0 and len(clean_body(res['stdout']))>350:
            return clean_body(res['stdout']), attempts
    return '', attempts

def review(role, routes, ch, text, card):
    prompt=f"""你是《科武纪元》{role}。审实际正文。
只按以下格式输出：
结论：PASS 或 FAIL
必改项：最多3条；无则写无
理由：≤300字

门禁：大纲对齐；承接261钩子；番茄口径≥3000；禁词0；无wikilink；首行标题；末尾（本章完）；技术/身体/资源代价可见；无AI味。3600只作节奏参考，不作失败条件。
任务卡：
{card[:2500]}
正文：
{text[:18000]}"""
    logs=[]
    for p,m in routes:
        res=call_model(p,m,prompt,timeout=180)
        logs.append(res)
        if res['exit_code']==0 and res['stdout']:
            return res, logs
    return logs[-1], logs

def pass_review(out):
    head='\n'.join(out.splitlines()[:5])
    return 'PASS' in head and 'FAIL' not in head.split('PASS')[0]

def repair(ch,title,text,card,issues,round_no):
    prompt=f"""你是《科武纪元》作者位修稿。只输出完整章节正文。
章节：# 第{ch}章 {title}
依据问题修复，不新增大设定。番茄口径须≥3000；不得为压到3600以下而删有效剧情。
禁词：{','.join(BAN)}
问题：
{issues[:2500]}
任务卡：
{card[:2200]}
原文：
{text[:18000]}"""
    for p,m in [AUTHOR_PRIMARY]+AUTHOR_FALLBACKS:
        res=call_model(p,m,prompt,timeout=220 if p=='xiaomi' else 180)
        if res['exit_code']==0 and fanqie_count(clean_body(res['stdout']))>=2500:
            return normalize_full(ch,title,clean_body(res['stdout'])), res
    return text, res

def normalize_full(ch,title,body):
    body=clean_body(body)
    body=re.sub(r'^#\s*第\d+章[^\n]*\n*','',body).strip()
    body=re.sub(r'（本章完）\s*$','',body).strip()
    paras=[p.strip() for p in re.split(r'\n\s*\n', body) if p.strip()]
    return f"# 第{ch}章 {title}\n\n" + "\n\n".join(paras) + "\n\n（本章完）\n"

def machine_gate(ch,text):
    problems=[]
    if not text.startswith(f'# 第{ch}章 '): problems.append('BAD_TITLE')
    if not text.rstrip().endswith('（本章完）'): problems.append('BAD_END')
    if '[[' in text or ']]' in text: problems.append('WIKILINK')
    hits=[w for w in BAN if w in text]
    if hits: problems.append('BAN:'+','.join(hits))
    cnt=fanqie_count(text)
    if cnt<3000: problems.append(f'COUNT:{cnt}')
    return problems,cnt

def sync_and_commit(ch):
    sync=run(['python3',str(BASE/'工具脚本'/'sync_kewu.py'),'--chapter',str(ch),'--message',f'第{ch}章阶段一写作闭环','--no-git'],timeout=240,cwd='/root/workspace')
    wiki=BASE/'wiki'/'chapters'/f'ch{ch:03d}.md'
    src=BASE/'新版'/f'第{ch}章.md'
    if wiki.exists() and src.exists():
        wt=wiki.read_text(encoding='utf-8')
        st=src.read_text(encoding='utf-8')
        if '## Full Text' in wt and st[:80] not in wt:
            wt=re.sub(r'## Full Text\n.*', '## Full Text\n\n'+st, wt, flags=re.S)
            wiki.write_text(wt,encoding='utf-8')
    files=[str(src),str(wiki),str(REVDIR/f'第{ch}章_写前任务卡_20260526.md'),str(REVDIR/f'第{ch}章_闭环报告_20260526.md'),str(QUEUE),str(EVENTS),str(BASE/'小说综合跟踪表.md'),str(BASE/'STATUS.md'),str(BASE/'WAL.md')]
    files += [str(p) for p in RAWDIR.glob(f'第{ch}章_*')]
    existing=[f for f in files if pathlib.Path(f).exists()]
    add=run(['git','-C',str(BASE),'add','-f','--']+existing,timeout=120,cwd='/root/workspace')
    staged=run(['git','-C',str(BASE),'-c','core.quotePath=false','diff','--cached','--name-only'],timeout=60,cwd='/root/workspace')
    commit=run(['git','-C',str(BASE),'commit','-m',f'write: chapter {ch} stage one'],timeout=180,cwd='/root/workspace')
    sha=''
    if commit['exit_code']==0:
        sha=run(['git','-C',str(BASE),'rev-parse','--short','HEAD'],timeout=30,cwd='/root/workspace')['stdout'].strip()
    return sync, staged['stdout'], commit, sha

def append_status_wal(ch,title,cnt,report_path):
    stamp=now().replace('T',' ')
    s=BASE/'STATUS.md'; w=BASE/'WAL.md'; t=BASE/'小说综合跟踪表.md'
    status_add=f"\n- {stamp} 第{ch}章《{title}》阶段一写作闭环 FULL_LOOP_PASS。番茄口径 {cnt}。报告：`{report_path.relative_to(BASE)}`。非上传章，未TXT/未上传。\n"
    txt=s.read_text(encoding='utf-8')
    txt=txt.replace('## 最近完成\n','## 最近完成\n'+status_add,1)
    s.write_text(txt,encoding='utf-8')
    w.write_text(f"\n## {stamp}｜第{ch}章阶段一写作闭环\n\n- FULL_LOOP_PASS，番茄口径{cnt}。报告：`{report_path.relative_to(BASE)}`。\n- 非上传章，未生成已投稿TXT，未上传番茄。\n"+w.read_text(encoding='utf-8'),encoding='utf-8')
    with t.open('a',encoding='utf-8') as f:
        f.write(f"\n- 第{ch}章《{title}》｜阶段一写作闭环｜FULL_LOOP_PASS｜番茄口径{cnt}｜{stamp}\n")

def process_chapter(ch, outlines):
    event(ch,'START','RUNNING','chapter start')
    prev_path=BASE/'新版'/f'第{ch-1}章.md'
    prev=read_short(prev_path,7000) if prev_path.exists() else ''
    title, card_path, card=build_task_card(ch,outlines[ch],prev[-1800:])
    event(ch,'TASK_CARD','RUNNING',str(card_path),{'report_path':str(card_path)})
    total=4
    parts=[]; model_logs=[]
    history=''
    for seg in range(1,total+1):
        event(ch,f'AUTHOR_SEG_{seg}','RUNNING','author segment')
        part, attempts=author_segment(ch,title,card,prev,seg,total,history)
        model_logs.extend(attempts)
        raw=RAWDIR/f'第{ch}章_mimo_segment_{seg}.md'
        raw.write_text(part or ('FAILED\n'+json.dumps(attempts,ensure_ascii=False,indent=2)),encoding='utf-8')
        if not part:
            raise RuntimeError(f'author segment {seg} failed')
        parts.append(part); history += '\n\n'+part
        item=chapter_item(ch); cached=item.get('cached_segments',[]); cached.append(str(raw)); event(ch,f'AUTHOR_SEG_{seg}_DONE','RUNNING','cached',{'cached_segments':cached})
    full=normalize_full(ch,title,'\n\n'.join(parts))
    src=BASE/'新版'/f'第{ch}章.md'
    src.write_text(full,encoding='utf-8')
    for r in range(2):
        problems,cnt=machine_gate(ch,full)
        if not problems: break
        event(ch,'MACHINE_GATE_REPAIR','RUNNING',';'.join(problems))
        full,res=repair(ch,title,full,card,';'.join(problems),r+1)
        model_logs.append(res); src.write_text(full,encoding='utf-8')
    problems,cnt=machine_gate(ch,full)
    if problems:
        raise RuntimeError('machine gate fail: '+ ';'.join(problems))
    event(ch,'EDITOR_REVIEW','RUNNING','editor review')
    editor, elogs=review('编辑写后复审',EDITOR_ROUTES,ch,full,card); model_logs.extend(elogs)
    event(ch,'READER_REVIEW','RUNNING','reader review')
    reader, rlogs=review('读者写后复审',READER_ROUTES,ch,full,card); model_logs.extend(rlogs)
    event(ch,'ADVISOR_REVIEW','RUNNING','advisor review')
    advisor, alogs=review('科学/军事顾问轻审',ADVISOR_ROUTES,ch,full,card); model_logs.extend(alogs)
    ok=pass_review(editor['stdout']) and pass_review(reader['stdout'])
    if not ok:
        issues='编辑:\n'+editor['stdout']+'\n读者:\n'+reader['stdout']+'\n顾问:\n'+advisor['stdout']
        for rr in range(2):
            event(ch,'AUTHOR_REPAIR','RUNNING',f'round {rr+1}')
            full,res=repair(ch,title,full,card,issues,rr+1); model_logs.append(res); src.write_text(full,encoding='utf-8')
            problems,cnt=machine_gate(ch,full)
            editor,elogs=review('编辑写后复审',EDITOR_ROUTES,ch,full,card); model_logs.extend(elogs)
            reader,rlogs=review('读者写后复审',READER_ROUTES,ch,full,card); model_logs.extend(rlogs)
            advisor,alogs=review('科学/军事顾问轻审',ADVISOR_ROUTES,ch,full,card); model_logs.extend(alogs)
            if not problems and pass_review(editor['stdout']) and pass_review(reader['stdout']):
                ok=True; break
        if not ok:
            raise RuntimeError('review fail: '+issues[:1000])
    report_path=REVDIR/f'第{ch}章_闭环报告_20260526.md'
    routes_md='\n'.join([f"- {x['requested_provider']}/{x['requested_model']} exit={x['exit_code']} dur={x['duration']}s session={x.get('session_id','')} fail={x.get('fail_reason','')}" for x in model_logs])
    report_path.write_text(f"""# 第{ch}章 闭环报告

时间：{now()}
章节：第{ch}章《{title}》
结论：FULL_LOOP_PASS

## 门禁
- 番茄口径：{cnt}
- 禁词：0
- wikilink：0
- 首行/末尾：PASS
- 非上传章：未生成已投稿TXT，未上传番茄

## 模型调用记录
{routes_md}

## 编辑复审
{editor['stdout']}

## 读者复审
{reader['stdout']}

## 顾问轻审
{advisor['stdout']}
""",encoding='utf-8')
    append_status_wal(ch,title,cnt,report_path)
    event(ch,'PROJECT_SYNC','RUNNING','sync/wiki/status/wal/git')
    sync, staged, commit, sha=sync_and_commit(ch)
    item=chapter_item(ch)
    event(ch,'FULL_LOOP_PASS','FULL_LOOP_PASS','chapter completed',{'report_path':str(report_path),'git_commit':sha,'next_action':'continue'})
    return {'chapter':ch,'status':'FULL_LOOP_PASS','title':title,'count':cnt,'report':str(report_path),'commit':sha,'staged':staged,'sync_exit':sync['exit_code'],'commit_exit':commit['exit_code']}

def final_report(results):
    lines=['# 阶段一 262-265 执行报告','',f'时间：{now()}','']
    for r in results:
        lines.append(f"- 第{r.get('chapter')}章：{r.get('status')}｜番茄口径 {r.get('count','')}｜报告 {r.get('report','')}｜commit {r.get('commit','')}")
        if r.get('fail_reason'): lines.append(f"  - 失败：{r['fail_reason']}")
    REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    RAWDIR.mkdir(parents=True,exist_ok=True); QDIR.mkdir(parents=True,exist_ok=True); REVDIR.mkdir(parents=True,exist_ok=True)
    q=loadq(); q['stage']='RUNNING'; q['pid']=os.getpid(); saveq(q)
    event(None,'RUNNER_START','RUNNING','runner pid '+str(os.getpid()))
    outlines=outline_lines(); results=[]
    for ch in CHAPTERS:
        item = next((c for c in loadq().get('chapters', []) if c.get('chapter') == ch), {})
        if item.get('status') == 'FULL_LOOP_PASS':
            event(ch, 'SKIP_DONE', 'FULL_LOOP_PASS', 'already closed; continue next chapter')
            results.append({'chapter': ch, 'status': 'FULL_LOOP_PASS', 'count': item.get('fanqie_count', ''), 'report': item.get('report_path', ''), 'commit': item.get('git_commit', '')})
            final_report(results)
            continue
        try:
            res=process_chapter(ch,outlines); results.append(res); final_report(results)
        except Exception as e:
            msg=str(e)
            event(ch,'FAILED','FAILED',msg,{'fail_reason':msg,'next_action':'主控接管或重派作者/审核模型'})
            results.append({'chapter':ch,'status':'FAILED','fail_reason':msg})
            final_report(results)
            q=loadq(); q['stage']='BLOCKED'; saveq(q)
            return 1
    q=loadq(); q['stage']='DONE'; q['current_stage']='DONE'; saveq(q)
    event(None,'DONE','DONE','all chapters completed')
    final_report(results)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
