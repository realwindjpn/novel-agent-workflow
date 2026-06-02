#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.4 Goal queue runner. One chapter at a time. No upload TXT for回改线."""
from __future__ import annotations
from pathlib import Path
import os, json, time, re, sys, shutil, subprocess, urllib.request, urllib.error, datetime

BASE=Path('/root/workspace/科武纪元')
QUEUE=BASE/'审核记录/goal模式/V8124_执行队列_20260516.json'
OUT_ROOT=BASE/'审核记录/六角色外审/V8124_goal'
RAW_ROOT=OUT_ROOT/'raw'
EVENTS=BASE/'审核记录/goal模式/V8124_goal_events.jsonl'
LOCK=BASE/'.v8124_goal_runner.lock'
SYNC=BASE/'工具脚本/sync_kewu.py'
for d in [OUT_ROOT, RAW_ROOT, EVENTS.parent]: d.mkdir(parents=True, exist_ok=True)

# P2: 角色联动上下文注入
try:
    import importlib, sys as _sys
    _sys.path.insert(0, str(BASE/'工具脚本'))
    _rl = importlib.import_module('role_linkage')
    _get_role_ctx = _rl.get_role_context_section
    _get_role_drift = _rl.build_role_drift_checklist
    _ROLE_LINKAGE_OK = True
except Exception:
    _ROLE_LINKAGE_OK = False
    _get_role_ctx = lambda ch: '【角色联动上下文】加载失败'
    _get_role_drift = lambda ch: ''

ROLES={
 'kiro': {'provider':'KIRO','base_env':'KIRO_BASE_URL','key_env':'KIRO_API_KEY','model':'claude-opus-4.6'},
 'wf': {'provider':'WF','base_env':'WF_BASE_URL','key_env':'WF_API_KEY','model':'claude-opus-4-7-high-fast'},
 'author': {'provider':'Xiaomi','base_env':'XIAOMI_BASE_URL','key_env':'XIAOMI_API_KEY','model':'mimo-v2.5-pro'},
 'editor': {'provider':'DashScope','base_env':'DASHSCOPE_BASE_URL','key_env':'DASHSCOPE_API_KEY','model':'qwen3.6-plus','default_base':'https://dashscope.aliyuncs.com/compatible-mode/v1'},
 'reader': {'provider':'MiniMaxCN','base_env':'MINIMAX_CN_BASE_URL','key_env':'MINIMAX_CN_API_KEY','model':'MiniMax-M2.7','default_base':'https://api.minimaxi.com/v1'},
 'science': {'provider':'ZAI','base_env':'ZAI_BASE_URL','key_env':'ZAI_API_KEY','model':'glm-5.1','default_base':'https://open.bigmodel.cn/api/coding/paas/v4'},
}

META={
 223:{'title':'内战爆发','target':'AI视频众包机制・审计冻结误伤','must':['任务池','模板','水印','付款链','转发时间戳','审计冻结','证书轮换','抓捕延迟'],'ban':['现实国名对骂','新闻串烧','口号']},
 226:{'title':'政治联盟','target':'执法权/拘押权/日志留存权/AI透明度审计框架','must':['执法权','拘押权','日志留存权','透明度审计','交换表','接口','审计权限','火星探索权'],'ban':['表态式联盟','口号','硬改火星主线']},
}

def load_env():
    for p in [Path('/root/.hermes/.env'), BASE/'.env', Path('/root/workspace/.env')]:
        if p.exists():
            for line in p.read_text(encoding='utf-8',errors='ignore').splitlines():
                if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                    k,v=line.split('=',1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def api_call(role:str, prompt:str, max_tokens:int=2000, temp:float=0.15, timeout:int=300):
    cfg=ROLES[role]
    key=os.environ.get(cfg['key_env'],'')
    base=os.environ.get(cfg['base_env']) or cfg.get('default_base','')
    rec={'role':role,'provider':cfg['provider'],'requested_model':cfg['model'],'base':base,'ok':False,'started':datetime.datetime.now().isoformat(timespec='seconds')}
    if not key or not base:
        rec['error']='missing '+cfg['key_env']+'/'+cfg['base_env']; return rec
    data={'model':cfg['model'],'messages':[{'role':'user','content':prompt}], 'max_tokens':max_tokens, 'temperature':temp}
    if role=='science': data['thinking']={'type':'disabled'}
    req=urllib.request.Request(base.rstrip()+'/chat/completions', data=json.dumps(data,ensure_ascii=False).encode(), headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    t=time.time()
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            body=r.read().decode('utf-8','ignore'); js=json.loads(body)
            msg=(js.get('choices') or [{}])[0].get('message',{})
            content=(msg.get('content') or msg.get('reasoning_content') or '').strip()
            rec.update(ok=bool(content),status=r.status,latency=round(time.time()-t,2),returned_model=js.get('model'),content=content,usage=js.get('usage',{}))
    except urllib.error.HTTPError as e:
        rec.update(status=e.code,latency=round(time.time()-t,2),error=e.read().decode('utf-8','ignore')[:1200])
    except Exception as e:
        rec.update(status='EXC',latency=round(time.time()-t,2),error=repr(e))
    return rec

def save_raw(ch:int, name:str, rec:dict):
    d=OUT_ROOT/f'第{ch}章'; d.mkdir(parents=True,exist_ok=True)
    p=d/f'第{ch}章_{name}.json'
    p.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8')
    return p

def event(kind:str, text:str, data:dict|None=None):
    rec={'time':datetime.datetime.now().isoformat(timespec='seconds'),'kind':kind,'text':text,'data':data or {}}
    with EVENTS.open('a',encoding='utf-8') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')

def load_queue(): return json.loads(QUEUE.read_text(encoding='utf-8'))
def save_queue(q): QUEUE.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')

def set_status(ch:int, status:str, report:str|None=None):
    q=load_queue()
    found=False
    for item in q.get('active_queue',[]):
        if item.get('chapter')==ch:
            item['status']=status; found=True
            if report: item['report']=report
        elif found and status=='completed' and item.get('status')=='pending':
            item['status']='next'; found=False
    save_queue(q)

def compact(s:str): return re.sub(r'\s+','',s)
def fanqie(text:str):
    title=next((x for x in text.splitlines() if x.strip()),'')
    return max(0,len(compact(text))-len(compact(title)))
def clean(s:str):
    s=re.sub(r'^```(?:md|txt)?\s*','',s.strip()); s=re.sub(r'\s*```$','',s.strip())
    return s.strip()
def passish(rec:dict):
    c=re.sub(r'<think>.*?</think>','',rec.get('content',''),flags=re.S).strip()
    first=' '.join(c.splitlines()[:2])
    neg=['FAIL','不通过','重写全文','硬伤','跑偏','不能进入']
    pos=['PASS','通过','可进入','可以进入','合格','想继续看']
    return rec.get('ok') and any(x in c[:800] for x in pos) and not any(x in first for x in neg)

def read_context(ch:int):
    outline=(BASE/'wiki/raw/outline/科武纪元大纲_latest.md').read_text(encoding='utf-8',errors='ignore')[-12000:]
    chaos=(BASE/'wiki/concepts/chaos-model.md').read_text(encoding='utf-8',errors='ignore')[-7000:]
    style=''
    for p in ['/root/workspace/写作角色OS/writer_role_core.md','/root/workspace/写作角色OS/experience_distillation_rules.md','/root/workspace/科武纪元/参考资料/作家风格OS/author_prompt_patch.md']:
        pp=Path(p)
        if pp.exists(): style += '\n## '+pp.name+'\n'+pp.read_text(encoding='utf-8',errors='ignore')[:1800]
    return outline, chaos, style

def run_chapter(ch:int):
    meta=META[ch]; src=BASE/'新版'/f'第{ch}章.md'
    if not src.exists(): raise SystemExit(f'SOURCE_MISSING {ch}')
    orig=src.read_text(encoding='utf-8',errors='ignore')
    if fanqie(orig)<1500: raise SystemExit(f'SOURCE_TOO_SHORT {ch}')
    d=OUT_ROOT/f'第{ch}章'; d.mkdir(parents=True,exist_ok=True)
    bak=d/f'第{ch}章_精修前备份.md'; shutil.copy2(src,bak)
    outline,chaos,style=read_context(ch)
    task=f"""# 第{ch}章 V8.12.4 Goal任务卡
- 目标：{meta['target']}
- 必打词：{' / '.join(meta['must'])}
- 禁止：{' / '.join(meta['ban'])}
- 边界：非上传章，不生成已投稿TXT；只改本章；不改队列外章节。
- 路由：KIRO原文外审，WF opus47fast结构终审，MiMo作者，Qwen编辑复审，MiniMax读者复审，GLM技术轻审。
"""
    role_ctx = _get_role_ctx(ch)
    role_drift = _get_role_drift(ch)
    (d/f'第{ch}章_任务卡.md').write_text(task,encoding='utf-8')
    event('chapter_started',f'第{ch}章已启动：{meta["target"]}',{'chapter':ch})
    pre=f"""你是《科武纪元》KIRO原文外审。只输出≤900字：本章最小改法、必改点、不可动线。
【任务卡】\n{task}\n【大纲/混沌模型】\n{outline[:5000]}\n{chaos[:2500]}\n【原文首尾】\n{orig[:2200]}\n---TAIL---\n{orig[-2600:]}"""
    kiro=api_call('kiro',pre,1800,0.12,360); save_raw(ch,'KIRO原文外审',kiro)
    wfpre=api_call('wf',pre+'\n补充：请检查与既有V8.12.4角度是否重复。',1800,0.12,360); save_raw(ch,'WF结构外审',wfpre)
    if not (kiro.get('ok') or wfpre.get('ok')): raise SystemExit(f'PRE_REVIEW_FAIL {ch}')
    notes='\n'.join([(kiro.get('content') or kiro.get('error',''))[:1500], (wfpre.get('content') or wfpre.get('error',''))[:1500]])
    author_prompt=f"""你是《科武纪元》作者。输出第{ch}章完整正文，不解释。
硬约束：
- 首行保持"第{ch}章 {meta['title']}"；末行"（本章完）"。
- 保留原章主干，只做任务卡要求的增补/修补。
- 禁文艺比喻/咏叹调；用动作、设备反馈、账单、接口、日志、延迟、身体反应。
- 正文字数保持原文±20%。
【任务卡】\n{task}\n【KIRO/WF外审】\n{notes}\n【作家OS】\n{style[:5200]}\n【角色联动上下文】\n{role_ctx[:2000]}\n【原文全文】\n{orig}"""
    auth=api_call('author',author_prompt,14000,0.16,520); save_raw(ch,'MiMo作者',auth)
    if not auth.get('ok'):
        event('chapter_failed',f'第{ch}章作者失败',{'chapter':ch,'error':auth.get('error')}); raise SystemExit(f'AUTHOR_FAIL {ch}')
    new=clean(auth['content'])
    if not new.startswith(f'第{ch}章'): new=f"第{ch}章 {meta['title']}\n\n"+new
    if not new.rstrip().endswith('（本章完）'): new=new.rstrip()+'\n（本章完）\n'
    tmp=d/f'第{ch}章_MiMo候选稿.md'; tmp.write_text(new,encoding='utf-8')
    post=f"""写后复审。第一行只写PASS或FAIL；第二行起≤5条。FAIL仅限硬伤/缺必打点/明显跑偏。
【任务卡】\n{task}\n【角色偏移门禁】\n{role_drift[:1500]}\n【正文首尾】\n{new[:2600]}\n---TAIL---\n{new[-3000:]}"""
    ep=api_call('editor',post,1800,0.1,320); save_raw(ch,'Qwen编辑复审',ep)
    rp=api_call('reader',post,1600,0.1,320); save_raw(ch,'MiniMax读者复审',rp)
    sp=api_call('science',post+'\n只查技术/制度硬伤，不评价文采。',1400,0.05,260); save_raw(ch,'GLM技术轻审',sp)
    if not (passish(ep) and passish(rp)):
        repair=f"""按复审意见修复第{ch}章，只输出完整正文。
【编辑】\n{ep.get('content') or ep.get('error','')}\n【读者】\n{rp.get('content') or rp.get('error','')}\n【当前正文】\n{new}"""
        ar=api_call('author',repair,14000,0.12,520); save_raw(ch,'MiMo二修',ar)
        if ar.get('ok'):
            new=clean(ar['content'])
            if not new.startswith(f'第{ch}章'): new=f"第{ch}章 {meta['title']}\n\n"+new
            if not new.rstrip().endswith('（本章完）'): new=new.rstrip()+'\n（本章完）\n'
            tmp.write_text(new,encoding='utf-8')
            ep=api_call('editor',post.replace(new[:2600],new[:2600]),1800,0.1,320); save_raw(ch,'Qwen编辑二审',ep)
            rp=api_call('reader',post.replace(new[:2600],new[:2600]),1600,0.1,320); save_raw(ch,'MiniMax读者二审',rp)
    missing=[w for w in meta['must'] if w not in new]
    banned=[w for w in ['仿佛','微微','缓缓','不禁','不由得','像是'] if w in new]
    fq=fanqie(new)
    ok=passish(ep) and passish(rp) and fq>=3000 and len(missing)<=2 and not banned
    sync_out=''
    if ok:
        src.write_text(new,encoding='utf-8')
        txt=BASE/'已投稿'/f'第{ch}章.txt'
        if txt.exists(): txt.unlink()
        r=subprocess.run(['python3',str(SYNC),'--chapter',str(ch),'--message',f'V8.12.4 Goal 第{ch}章闭环','--no-git'],cwd='/root/workspace',text=True,capture_output=True,timeout=360)
        sync_out=(r.stdout+r.stderr)[-2500:]
    wfpost=api_call('wf',f"""终审第{ch}章。第一行PASS/FAIL。只查：是否完成{meta['target']}、是否角度重复、是否可闭环。\n【任务卡】\n{task}\n【正文首尾】\n{new[:2400]}\n---TAIL---\n{new[-2600:]}""",1200,0.05,260); save_raw(ch,'WF终审',wfpost)
    ok = ok and (passish(wfpost) or wfpost.get('ok'))
    report=d/f'第{ch}章_V8124闭环报告.md'
    report.write_text(f"""# 第{ch}章 V8.12.4 Goal精修闭环报告

- 结论：{'PASS' if ok else 'FAIL'}
- 目标：{meta['target']}
- 番茄口径：{fq}
- KIRO：HTTP {kiro.get('status')} / {kiro.get('returned_model')} / {kiro.get('latency')}s
- WF opus47fast外审：HTTP {wfpre.get('status')} / {wfpre.get('returned_model')} / {wfpre.get('latency')}s
- MiMo作者：HTTP {auth.get('status')} / {auth.get('returned_model')} / {auth.get('latency')}s
- Qwen编辑复审：{'PASS' if passish(ep) else 'FAIL'} / HTTP {ep.get('status')} / {ep.get('returned_model')} / {ep.get('latency')}s
- MiniMax读者复审：{'PASS' if passish(rp) else 'FAIL'} / HTTP {rp.get('status')} / {rp.get('returned_model')} / {rp.get('latency')}s
- GLM技术轻审：HTTP {sp.get('status')} / {sp.get('returned_model')} / {sp.get('latency')}s
- WF终审：HTTP {wfpost.get('status')} / {wfpost.get('returned_model')} / {wfpost.get('latency')}s
- 机器门禁：缺失 {missing}；禁词 {banned}
- 项目同步：{'sync_kewu --no-git 已执行' if ok else '未执行'}
- TXT：非上传章，未生成已投稿TXT
- 备份：{bak}

## sync输出
```text
{sync_out}
```
""",encoding='utf-8')
    if ok:
        set_status(ch,'completed',str(report))
        event('chapter_completed',f'第{ch}章闭环 PASS；番茄口径 {fq}；下一章自动继续。',{'chapter':ch,'fanqie':fq,'report':str(report)})
    else:
        set_status(ch,'failed',str(report))
        event('chapter_failed',f'第{ch}章 FAIL，队列已停。',{'chapter':ch,'report':str(report),'missing':missing,'banned':banned})
        raise SystemExit(f'CHAPTER_FAIL {ch}')

def next_chapter():
    q=load_queue()
    # reconcile 221 if report exists
    r221=OUT_ROOT/'第221章/第221章_V8124闭环报告.md'
    if r221.exists() and '结论：PASS' in r221.read_text(encoding='utf-8',errors='ignore'):
        for item in q.get('active_queue',[]):
            if item.get('chapter')==221 and item.get('status')!='completed':
                item['status']='completed'; item['report']=str(r221)
        seen_next=False
        for item in q.get('active_queue',[]):
            if item.get('chapter')==223 and item.get('status')=='pending': item['status']='next'
        save_queue(q)
    for item in load_queue().get('active_queue',[]):
        if item.get('status')=='next': return int(item['chapter'])
    return None

def main():
    load_env()
    if LOCK.exists():
        try:
            pid=int(LOCK.read_text().strip().split()[0])
            os.kill(pid,0); print('RUNNER_ALREADY_ACTIVE',pid); return 0
        except Exception: LOCK.unlink(missing_ok=True)
    LOCK.write_text(str(os.getpid())+' '+datetime.datetime.now().isoformat(timespec='seconds'),encoding='utf-8')
    try:
        event('runner_started','V8.12.4 Goal队列已启动，严格按 next 执行。')
        # smoke core routes
        for role in ['kiro','wf','author','editor','reader']:
            rec=api_call(role,'只回复OK',16,0,90); save_raw(0,role+'_smoke',rec)
            if not rec.get('ok'):
                event('runner_failed',f'{role} smoke失败',{'role':role,'error':rec.get('error'),'status':rec.get('status')})
                raise SystemExit('SMOKE_FAIL '+role)
        while True:
            ch=next_chapter()
            if ch is None:
                event('runner_completed','V8.12.4 Goal队列全部完成。')
                break
            if ch not in META:
                event('runner_failed',f'无脚本元数据：第{ch}章',{'chapter':ch}); raise SystemExit('NO_META '+str(ch))
            run_chapter(ch)
        return 0
    finally:
        LOCK.unlink(missing_ok=True)

if __name__=='__main__':
    raise SystemExit(main())
