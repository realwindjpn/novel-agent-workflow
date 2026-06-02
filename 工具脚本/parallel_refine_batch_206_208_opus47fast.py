#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并发跑 V8.12.1 第206-208章；作者位强制 WF opus47fast。"""
from __future__ import annotations
import json, subprocess, time, os, re, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

BASE=Path('/root/workspace/科武纪元')
SCRIPT=BASE/'工具脚本/run_refine_chapter_v4.py'
SYNC=BASE/'工具脚本/sync_kewu.py'
CHAPTERS=[206,207,208]
RUN_DIR=BASE/'审核记录/并发精修'/('batch_206_208_opus47fast_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
RUN_DIR.mkdir(parents=True,exist_ok=True)
SUMMARY=RUN_DIR/'summary.json'
WF_MODEL='claude-opus-4-7-high-fast'

def load_env():
    env=Path('/root/.hermes/.env')
    if env.exists():
        for line in env.read_text(errors='ignore').splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))

def wf_smoke():
    load_env(); base=os.environ.get('WF_BASE_URL','').rstrip('/'); key=os.environ.get('WF_API_KEY','')
    if not base or not key: return {'ok':False,'reason':'WF env missing','requested_model':WF_MODEL}
    payload={'model':WF_MODEL,'messages':[{'role':'user','content':'只回复OK'}],'max_tokens':8,'temperature':0}
    req=urllib.request.Request(base+'/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    t=time.time()
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            js=json.loads(r.read().decode('utf-8','ignore'))
            return {'ok':True,'status':r.status,'latency':round(time.time()-t,2),'requested_model':WF_MODEL,'returned_model':js.get('model'),'content':js.get('choices',[{}])[0].get('message',{}).get('content')}
    except urllib.error.HTTPError as e:
        return {'ok':False,'status':e.code,'latency':round(time.time()-t,2),'requested_model':WF_MODEL,'error_body':e.read().decode('utf-8','ignore')[:500]}
    except Exception as e:
        return {'ok':False,'status':'EXC','latency':round(time.time()-t,2),'requested_model':WF_MODEL,'error':repr(e)}

def meta_present(ch:int)->bool:
    return re.search(rf'\n\s*{ch}:\s*\(',SCRIPT.read_text(encoding='utf-8',errors='ignore')) is not None

def fanqie_count(p:Path)->int:
    txt=p.read_text(encoding='utf-8',errors='ignore'); lines=txt.splitlines(); title=lines[0] if lines else ''
    return len(''.join(txt.split()))-len(''.join(title.split()))

def report_pass(ch:int)->bool:
    rep=BASE/'审核记录/六角色外审'/f'第{ch}章.md'
    if not rep.exists(): return False
    txt=rep.read_text(encoding='utf-8',errors='ignore')
    return all(g in txt for g in ['编辑写后：PASS','读者写后：PASS','RTK编辑门禁：PASS','RTK读者门禁：PASS','最终结论\nPASS'])

def verify_wiki(ch:int)->bool:
    src=BASE/'新版'/f'第{ch}章.md'; wiki=BASE/'wiki/chapters'/f'ch{ch:03d}.md'
    if not src.exists() or not wiki.exists(): return False
    s=src.read_text(encoding='utf-8',errors='ignore'); w=wiki.read_text(encoding='utf-8',errors='ignore')
    lines=[x.strip() for x in s.splitlines() if x.strip()]
    return bool(lines) and lines[0] in w and lines[-1] in w and '## Full Text' in w

def run_sync(ch:int):
    cmd=['python3',str(SYNC),'--chapter',str(ch),'--message',f'V8.12.1 第{ch}章 opus47fast作者位精修闭环','--no-git']
    r=subprocess.run(cmd,cwd='/root/workspace',text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
    (RUN_DIR/f'ch{ch}_sync.log').write_text(r.stdout,encoding='utf-8')
    return r.returncode,r.stdout[-1200:]

def main():
    smoke=wf_smoke()
    result={'started':datetime.now().isoformat(timespec='seconds'),'run_dir':str(RUN_DIR),'wf_smoke':smoke,'author_route':'opus47fast','meta_check':{},'chapters':{}}
    for ch in CHAPTERS:
        p=BASE/'新版'/f'第{ch}章.md'
        result['meta_check'][str(ch)]={'meta_present':meta_present(ch),'source_exists':p.exists(),'fanqie_before':fanqie_count(p) if p.exists() else None}
    SUMMARY.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    if not smoke.get('ok'): raise SystemExit('WF opus47fast smoke failed')
    bad=[ch for ch in CHAPTERS if not result['meta_check'][str(ch)]['meta_present'] or not result['meta_check'][str(ch)]['source_exists']]
    if bad: raise SystemExit('meta/source missing: '+','.join(map(str,bad)))
    env=os.environ.copy(); env['KEWU_AUTHOR_ROUTE']='opus47fast'; load_env(); env.update({k:os.environ[k] for k in ['WF_BASE_URL','WF_API_KEY'] if k in os.environ})
    procs={}
    for ch in CHAPTERS:
        log=open(RUN_DIR/f'ch{ch}_v4.log','w',encoding='utf-8')
        p=subprocess.Popen(['python3',str(SCRIPT),str(ch)],cwd='/root/workspace',stdout=log,stderr=subprocess.STDOUT,text=True,env=env)
        procs[ch]=(p,log); time.sleep(2)
    for ch,(p,log) in procs.items():
        rc=p.wait(); log.close(); result['chapters'][str(ch)]={'v4_exit':rc,'v4_log':str(RUN_DIR/f'ch{ch}_v4.log')}; SUMMARY.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    for ch in CHAPTERS:
        item=result['chapters'][str(ch)]; src=BASE/'新版'/f'第{ch}章.md'
        item['report_pass']=report_pass(ch); item['source_exists']=src.exists(); item['fanqie_count']=fanqie_count(src) if src.exists() else None
        txt=BASE/'已投稿'/f'第{ch}章.txt'; item['upload_txt_removed']=False
        if txt.exists(): txt.unlink(); item['upload_txt_removed']=True
        if item['v4_exit']==0 and item['report_pass']:
            code,out=run_sync(ch); item['sync_exit']=code; item['sync_tail']=out; item['wiki_fulltext_ok']=verify_wiki(ch)
        else:
            item['sync_exit']=None; item['wiki_fulltext_ok']=False
        SUMMARY.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    result['finished']=datetime.now().isoformat(timespec='seconds'); SUMMARY.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
