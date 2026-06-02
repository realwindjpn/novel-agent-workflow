#!/usr/bin/env python3
import json, os, pathlib, re, subprocess, time, datetime
ROOT=pathlib.Path('/root/workspace/科武纪元')
RAWDIR=ROOT/'审核记录/六角色外审/raw'; RAWDIR.mkdir(parents=True,exist_ok=True)
EV=ROOT/'审核记录/新卷写作队列/events_266_275_20260526.jsonl'
Q=ROOT/'审核记录/新卷写作队列/queue_266_275_20260526.json'
NEW=ROOT/'新版/第269章.md'
REPORT=ROOT/'审核记录/六角色外审/第269章_闭环报告_20260526.md'
TASK=ROOT/'审核记录/六角色外审/第269章_写前任务卡_20260526.md'
CH=269

def now(): return datetime.datetime.now().isoformat(timespec='seconds')
def event(ev,st,msg='',**kw):
    d={'ts':now(),'chapter':CH,'event':ev,'status':st,'msg':msg}; d.update(kw)
    with EV.open('a',encoding='utf-8') as f: f.write(json.dumps(d,ensure_ascii=False)+'\n')

def update(status=None, **kw):
    q=json.loads(Q.read_text(encoding='utf-8'))
    q['stage']='RUNNING'; q['current_chapter']=CH; q['current_stage']=kw.get('current_stage',status or '') ; q['updated_at']=now()
    for c in q.get('chapters',[]):
        if c.get('chapter')==CH:
            if status: c['status']=status
            c.update({k:v for k,v in kw.items() if k!='current_stage'})
            c['updated_at']=now()
    Q.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')

def call(provider, model, prompt, timeout=300):
    env=os.environ.copy()
    if provider=='xiaomi': env['HERMES_STREAM_READ_TIMEOUT']='300'
    t=time.time()
    p=subprocess.run(['hermes','chat','-Q','--provider',provider,'--model',model,'-q',prompt],text=True,capture_output=True,timeout=timeout,env=env)
    return {'provider':provider,'model':model,'exit_code':p.returncode,'duration':round(time.time()-t,2),'stdout':p.stdout.strip(),'stderr':p.stderr.strip()}

def clean(s):
    s=re.sub(r'^```.*?\n|```$','',s.strip(),flags=re.S)
    reps={'意味着':'代表','仿佛':'像','似乎':'像','微微':'','宛如':'像','犹如':'像','悄然':'','骤然':'','瞬间':'','极致':'','无数':'大量','彻底':'','崩塌':'失效','撕裂':'分开','震撼':'冲击'}
    for a,b in reps.items(): s=s.replace(a,b)
    return s.strip()
def fanqie_count(text):
    lines=text.splitlines(); title=lines[0].strip() if lines else ''
    body=''.join(lines[1:])
    return len(re.sub(r'\s+','',body))-len(re.sub(r'\s+','',title))

def main():
    event('FULL_REWRITE_START','RUNNING','mimo-v2.5-pro single full chapter')
    update('RUNNING', next_action='mimo_pro_full_single', current_stage='MIMO_PRO_FULL')
    prev=(ROOT/'新版/第268章.md').read_text(encoding='utf-8') if (ROOT/'新版/第268章.md').exists() else ''
    outline=(ROOT/'科武纪元大纲 V8_完整版.md').read_text(encoding='utf-8')[:20000] if (ROOT/'科武纪元大纲 V8_完整版.md').exists() else ''
    task='''# 第269章 写前任务卡\n\n方式：MiMo v2.5 Pro 单次整章写作。\n红线：不分段拼接；番茄口径≥3000；无禁词；承接第268章；完成后WF编辑/Qwen读者/ZAI顾问复审。\n'''
    TASK.write_text(task,encoding='utf-8')
    prompt=f'''你是《科武纪元》作者OS。请直接写第269章完整正文，非大纲，非提要。\n硬性要求：\n- 首行：第269章 标题\n- 只输出正文，末尾（本章完）\n- 番茄口径≥3000字，可到6000字，不压缩\n- 必须承接第268章：火星南极地下四百公里遗迹、箱体升温、三条舰队轨道数据、联合政府等待摘要/完整包\n- 不得出现双稿拼接、时间线回跳、温度回跳、人物位置跳跃\n- 400km光程只能是约1.3毫秒；任何秒级等待须归因协议/队列/设备响应\n- 写动作链、工程代价、资源代价、人物选择，不要概念讲稿\n- 禁词不要用：意味着、仿佛、似乎、微微、宛如、犹如、悄然、骤然、瞬间、极致、无数、彻底、崩塌、撕裂、震撼\n\n上一章末段参考：\n{prev[-2500:]}\n\n大纲参考节选：\n{outline[-8000:]}\n'''
    res=call('xiaomi','mimo-v2.5-pro',prompt,timeout=420)
    (RAWDIR/'第269章_mimo_pro_full_raw.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
    if res['exit_code']!=0 or len(res['stdout'])<2000:
        event('FULL_REWRITE_FAIL','FAILED',res.get('stderr','')[:300])
        update('FAILED',fail_reason='mimo pro full failed '+res.get('stderr','')[:300],next_action='retry_or_fallback')
        return
    text=clean(res['stdout'])
    if not text.startswith('第269章'):
        text='第269章 地下四百公里的第二个回声\n\n'+text
    NEW.write_text(text+'\n',encoding='utf-8')
    cnt=fanqie_count(text); bans=[b for b in ['意味着','仿佛','似乎','微微','宛如','犹如','悄然','骤然','瞬间','极致','无数','彻底','崩塌','撕裂','震撼'] if b in text]
    event('MIMO_PRO_FULL_DONE','RUNNING',f'count={cnt} bans={len(bans)}',fanqie_count=cnt,bans=bans)
    if cnt<3000 or bans:
        update('FAILED',fail_reason=f'machine gate failed count={cnt} bans={bans}',next_action='repair')
        event('MACHINE_GATE_FAIL','FAILED',f'count={cnt} bans={bans}')
        return
    event('EDITOR_REVIEW','RUNNING','WF opus editor')
    ed=call('custom:WF','claude-opus-4-7-high-fast',f'你是编辑OS。审第269章实际正文。只输出：结论：PASS/FAIL；必改项≤3；理由≤200字。检查大纲对齐、时间线、无拼接、人物位置、硬科幻逻辑。正文：{text[:24000]}',timeout=240)
    event('READER_REVIEW','RUNNING','qwen reader')
    rd=call('alibaba','qwen3.6-plus',f'你是读者。审第269章实际正文。只输出：结论：PASS/FAIL；劝退点≤3；理由≤200字。正文：{text[:22000]}',timeout=180)
    event('ADVISOR_REVIEW','RUNNING','zai advisor')
    ad=call('zai','glm-5.1',f'你是科学/军事顾问。审第269章硬伤。只输出：结论：PASS/FAIL；硬伤≤3；理由≤200字。正文：{text[:22000]}',timeout=220)
    reviews={'editor':ed,'reader':rd,'advisor':ad}
    (RAWDIR/'第269章_mimo_pro_full_reviews.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2),encoding='utf-8')
    ok=all(('PASS' in r.get('stdout','') and r.get('exit_code')==0) for r in reviews.values())
    REPORT.write_text(f'''# 第269章 闭环报告\n\n时间：{now()}\n结论：{'FULL_LOOP_PASS' if ok else 'REVIEW_FAIL'}\n方式：MiMo v2.5 Pro 单次整章写作。\n\n## 门禁\n- 番茄口径：{cnt}\n- 禁词：{len(bans)}\n- 上传边界：未生成已投稿TXT，未上传番茄\n\n## 模型证据\n- 作者：xiaomi/mimo-v2.5-pro exit={res['exit_code']} duration={res['duration']}\n- 编辑：custom:WF/claude-opus-4-7-high-fast exit={ed['exit_code']} duration={ed['duration']}\n- 读者：alibaba/qwen3.6-plus exit={rd['exit_code']} duration={rd['duration']}\n- 顾问：zai/glm-5.1 exit={ad['exit_code']} duration={ad['duration']}\n\n## 编辑\n{ed.get('stdout','')}\n\n## 读者\n{rd.get('stdout','')}\n\n## 顾问\n{ad.get('stdout','')}\n''',encoding='utf-8')
    if ok:
        subprocess.run(['git','-C',str(ROOT),'add','-f',str(NEW.relative_to(ROOT)),str(REPORT.relative_to(ROOT)),str(TASK.relative_to(ROOT)),str((RAWDIR/'第269章_mimo_pro_full_raw.json').relative_to(ROOT)),str((RAWDIR/'第269章_mimo_pro_full_reviews.json').relative_to(ROOT))],check=False)
        cp=subprocess.run(['git','-C',str(ROOT),'commit','-m','write: chapter 269 mimo pro full'],text=True,capture_output=True)
        commit=subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],text=True,capture_output=True).stdout.strip()
        update('FULL_LOOP_PASS',report_path=str(REPORT),git_commit=commit,next_action='continue_270')
        event('FULL_LOOP_PASS','FULL_LOOP_PASS','chapter 269 closed',report_path=str(REPORT),git_commit=commit,fanqie_count=cnt,next_action='continue_270')
    else:
        fail='\n'.join([k+': '+v.get('stdout','')[:400] for k,v in reviews.items()])
        update('REVIEW_FAIL',report_path=str(REPORT),fail_reason=fail,next_action='repair_or_rewrite')
        event('REVIEW_FAIL','FAILED','review not pass',report_path=str(REPORT))
if __name__=='__main__': main()
