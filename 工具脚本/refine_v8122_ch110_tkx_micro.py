#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第110章 V8.12.2 TKX微分段精修。8段，带重试，避开502/524。"""
from pathlib import Path
import os,json,time,re,shutil,subprocess,urllib.request,urllib.error,sys
BASE=Path('/root/workspace/科武纪元'); RAW=BASE/'审核记录/六角色外审/raw'; REV=BASE/'审核记录/六角色外审'; TMP=BASE/'审核记录/临时精修'; BACK=BASE/'审核记录/备份/V8122_顺序精修_20260515'
for d in [RAW,REV,TMP,BACK]: d.mkdir(parents=True,exist_ok=True)
ROLES={'author':{'provider':'TKX','base':'https://tokenx24.com/v1','key_env':'TOKENX_API_KEY','model':'gpt-5.5'},'editor':{'provider':'WF','base':'http://43.135.181.17:8081/v1','key_env':'WF_API_KEY','model':'claude-opus-4-7-high-fast'},'reader':{'provider':'MiniMaxCN','base':'https://api.minimaxi.com/v1','key_env':'MINIMAX_CN_API_KEY','model':'MiniMax-M2.7'}}
def load_env():
 p=Path('/root/.hermes/.env')
 if p.exists():
  for line in p.read_text(encoding='utf-8',errors='ignore').splitlines():
   if line.strip() and not line.lstrip().startswith('#') and '=' in line:
    k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
def call(role,prompt,max_tokens=2800,temp=0.15,tag='call',timeout=150):
 cfg=ROLES[role]; key=os.environ.get(cfg['key_env'],''); rec={'role':role,'provider':cfg['provider'],'requested_model':cfg['model'],'base':cfg['base'],'ok':False,'tag':tag}
 if not key: rec['error']='missing '+cfg['key_env']; return rec
 data={'model':cfg['model'],'messages':[{'role':'user','content':prompt}],'max_tokens':max_tokens,'temperature':temp}
 req=urllib.request.Request(cfg['base'].rstrip()+'/chat/completions',data=json.dumps(data,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 t=time.time()
 try:
  with urllib.request.urlopen(req,timeout=timeout) as r:
   js=json.loads(r.read().decode('utf-8','ignore')); msg=(js.get('choices') or [{}])[0].get('message',{}); content=(msg.get('content') or msg.get('reasoning_content') or '').strip()
   rec.update(ok=bool(content),status=r.status,latency=round(time.time()-t,2),returned_model=js.get('model'),content=content,usage=js.get('usage',{}))
 except urllib.error.HTTPError as e: rec.update(status=e.code,latency=round(time.time()-t,2),error=e.read().decode('utf-8','ignore')[:800])
 except Exception as e: rec.update(status='EXC',latency=round(time.time()-t,2),error=repr(e))
 return rec
def save(name,rec):
 p=RAW/f'第110_{name}_v8122.json'; p.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8'); return p
def load_ok(name):
 p=RAW/f'第110_{name}_v8122.json'
 if p.exists():
  try:
   js=json.loads(p.read_text(encoding='utf-8'))
   if js.get('ok') and js.get('content'): return js['content'].strip()
  except Exception: pass
 return None
def clean(s):
 return re.sub(r'\s*```$','',re.sub(r'^```(?:md|txt)?\s*','',s.strip())).strip()
def fq(text):
 lines=[x for x in text.splitlines() if x.strip()]; title=lines[0] if lines else ''
 return len(re.sub(r'\s+','',text))-len(re.sub(r'\s+','',title))
def passish(rec):
 c=re.sub(r'<think>.*?</think>','',rec.get('content') or '',flags=re.S).strip()
 first=next((x.strip() for x in c.splitlines() if x.strip()), '')
 neg=['FAIL','不通过','不能进入','重写全文','硬伤未修','严重跑偏','无追读']
 pos=['PASS','通过','可进入下一章','可以进入下一章','整体可用','想继续看','合格']
 if first.startswith('PASS'):
  return bool(rec.get('ok'))
 if first.startswith('FAIL'):
  return False
 return rec.get('ok') and any(x in c for x in pos) and not any(x in c[:500] for x in neg)
def split(text,n=8):
 lines=text.splitlines(); title=lines[0].strip(); body='\n'.join(lines[1:]).strip(); paras=[p.strip() for p in re.split(r'\n\s*\n',body) if p.strip()]
 size=(len(paras)+n-1)//n; return title,['\n\n'.join(paras[i:i+size]) for i in range(0,len(paras),size)]
def main():
 load_env(); src=BASE/'新版/第110章.md'; orig=src.read_text(encoding='utf-8',errors='ignore'); shutil.copy2(src,BACK/'第110章_精修前_micro.md')
 task=(BASE/'审核记录/任务卡/第110章_V8122.md').read_text(encoding='utf-8')
 title,chunks=split(orig,8); outs=[]
 for i,chunk in enumerate(chunks,1):
  tag=f'author_micro_{i}'; cached=load_ok(tag)
  if cached: outs.append(clean(cached)); continue
  prompt=f"""你是《科武纪元》作者。精修第110章第{i}/{len(chunks)}小段。只输出本小段正文，不要标题/说明。
硬约束：保留原剧情顺序；只增强红线表、叫停权、许可冻结、保险上浮、热线延迟、港口排队、备件证书、物理咽喉+数字锁死；不写正式协议；不触碰第95；字数为原段±20%。
【任务卡】\n{task}
【原文小段】\n{chunk}"""
  rec=None
  for attempt in range(1,4):
   rec=call('author',prompt,max_tokens=3200,temp=0.14,tag=f'{tag}_try{attempt}',timeout=140); save(tag,rec)
   if rec.get('ok'): break
   time.sleep(8*attempt)
  if not rec or not rec.get('ok'): raise SystemExit('AUTHOR_MICRO_FAIL '+json.dumps(rec,ensure_ascii=False)[:500])
  outs.append(clean(rec['content']))
 new=title+'\n\n'+'\n\n'.join(outs).strip()
 if not new.rstrip().endswith('（本章完）'): new=new.rstrip()+'\n\n（本章完）'
 for a,b in {'仿佛':'像','微微':'','缓缓':'','不禁':'','不由得':'','意味着':'说明','意识到':'察觉'}.items(): new=new.replace(a,b)
 new=new+'\n'; tmp=TMP/'第110章_V8122_TKX微分段精修稿.tmp.md'; tmp.write_text(new,encoding='utf-8')
 def pp(kind): return f"""你是《科武纪元》{kind}写后复审。第一行只输出 PASS 或 FAIL。PASS=可进入项目闭环；FAIL=硬伤/跑偏/AI味/缺任务卡必打点。\n【任务卡】\n{task}\n【首段】\n{new[:2800]}\n【尾段】\n{new[-3200:]}\n番茄口径约{fq(new)}字。"""
 ep=call('editor',pp('编辑'),max_tokens=1800,tag='editor_post_micro',timeout=300); save('editor_post_micro',ep)
 rp=call('reader',pp('读者'),max_tokens=1600,tag='reader_post_micro',timeout=300); save('reader_post_micro',rp)
 banned=[w for w in ['仿佛','微微','缓缓','不禁','不由得','意味着','意识到'] if w in new]; must=sum(1 for x in ['保险','许可证','证书','审计','延迟','锁死','红线','港口','备件','热线'] if x in new)
 final=passish(ep) and passish(rp) and fq(new)>=3000 and not banned and must>=5; sync_out='SKIPPED'
 if final:
  src.write_text(new,encoding='utf-8'); txt=BASE/'已投稿/第110章.txt'
  if txt.exists(): txt.unlink()
  sync=subprocess.run(['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter','110','--message','V8.12.2第110章TKX微分段作者+WF编辑精修闭环','--no-git'],cwd='/root/workspace',capture_output=True,text=True,timeout=300); sync_out=sync.stdout+sync.stderr
 report=f"""# 第110章 V8.12.2 TKX微分段精修报告\n\n- 路线：TKX gpt-5.5 微分段作者；WF opus47fast 编辑；MiniMax 读者\n- 分段：{len(chunks)}段，单段失败最多重试3次\n- 写回：{'是' if final else '否'}\n- 番茄口径：{fq(new)}\n- 禁词残留：{banned}\n- 必打词命中：{must}\n- 编辑复审：{'PASS' if passish(ep) else 'FAIL'}\n- 读者复审：{'PASS' if passish(rp) else 'FAIL'}\n- 临时稿：{tmp}\n\n## 同步输出\n```text\n{sync_out[-3000:]}\n```\n"""
 rp_path=REV/'第110章_V8122_TKX微分段精修报告.md'; rp_path.write_text(report,encoding='utf-8')
 print(json.dumps({'final':final,'fanqie':fq(new),'report':str(rp_path),'editor':passish(ep),'reader':passish(rp),'must':must,'banned':banned},ensure_ascii=False))
 if not final: raise SystemExit(3)
if __name__=='__main__': main()
