#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第110章 V8.12.2 TKX分段精修。
避开TKX长请求524：原文分段，TKX/gpt-5.5逐段作者润色；WF编辑+MiniMax读者复审；不生成已投稿TXT。
"""
from pathlib import Path
import os, json, time, re, shutil, subprocess, urllib.request, urllib.error, sys
BASE=Path('/root/workspace/科武纪元')
RAW=BASE/'审核记录/六角色外审/raw'
REV=BASE/'审核记录/六角色外审'
TMP=BASE/'审核记录/临时精修'
BACK=BASE/'审核记录/备份/V8122_顺序精修_20260515'
for d in [RAW,REV,TMP,BACK]: d.mkdir(parents=True,exist_ok=True)
ROLES={
 'author':{'provider':'TKX','base':'https://tokenx24.com/v1','key_env':'TOKENX_API_KEY','model':'gpt-5.5'},
 'editor':{'provider':'WF','base':'http://43.135.181.17:8081/v1','key_env':'WF_API_KEY','model':'claude-opus-4-7-high-fast'},
 'reader':{'provider':'MiniMaxCN','base':'https://api.minimaxi.com/v1','key_env':'MINIMAX_CN_API_KEY','model':'MiniMax-M2.7'},
 'science':{'provider':'ZAI','base':'https://open.bigmodel.cn/api/coding/paas/v4','key_env':'ZAI_API_KEY','model':'glm-5.1'},
}

def load_env():
 p=Path('/root/.hermes/.env')
 if p.exists():
  for line in p.read_text(encoding='utf-8',errors='ignore').splitlines():
   if line.strip() and not line.lstrip().startswith('#') and '=' in line:
    k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))

def call(role,prompt,max_tokens=2600,temp=0.15,tag='call',timeout=180):
 cfg=ROLES[role]; key=os.environ.get(cfg['key_env'],'')
 rec={'role':role,'provider':cfg['provider'],'requested_model':cfg['model'],'base':cfg['base'],'ok':False,'tag':tag}
 if not key:
  rec['error']='missing '+cfg['key_env']; return rec
 data={'model':cfg['model'],'messages':[{'role':'user','content':prompt}],'max_tokens':max_tokens,'temperature':temp}
 req=urllib.request.Request(cfg['base'].rstrip()+'/chat/completions',data=json.dumps(data,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 t=time.time()
 try:
  with urllib.request.urlopen(req,timeout=timeout) as r:
   js=json.loads(r.read().decode('utf-8','ignore'))
   msg=(js.get('choices') or [{}])[0].get('message',{})
   content=(msg.get('content') or msg.get('reasoning_content') or '').strip()
   rec.update(ok=bool(content),status=r.status,latency=round(time.time()-t,2),returned_model=js.get('model'),content=content,usage=js.get('usage',{}))
 except urllib.error.HTTPError as e:
  rec.update(status=e.code,latency=round(time.time()-t,2),error=e.read().decode('utf-8','ignore')[:800])
 except Exception as e:
  rec.update(status='EXC',latency=round(time.time()-t,2),error=repr(e))
 return rec

def save(name,rec):
 p=RAW/f'第110_{name}_v8122.json'; p.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8'); return p

def clean(s):
 s=re.sub(r'^```(?:md|txt)?\s*','',s.strip())
 s=re.sub(r'\s*```$','',s.strip())
 return s.strip()

def fq(text):
 lines=[x for x in text.splitlines() if x.strip()]
 title=lines[0] if lines else ''
 return len(re.sub(r'\s+','',text))-len(re.sub(r'\s+','',title))

def passish(rec):
 c=(rec.get('content') or '')
 c=re.sub(r'<think>.*?</think>','',c,flags=re.S).strip()
 neg=['FAIL','不通过','不能进入','重写全文','硬伤未修','严重跑偏','无追读']
 pos=['PASS','通过','可进入下一章','可以进入下一章','整体可用','想继续看','合格']
 return rec.get('ok') and any(x in c for x in pos) and not any(x in c[:700] for x in neg)

def split_paras(text,n=4):
 lines=text.splitlines()
 title=lines[0].strip()
 body='\n'.join(lines[1:]).strip()
 paras=[p.strip() for p in re.split(r'\n\s*\n',body) if p.strip()]
 chunks=[]; size=(len(paras)+n-1)//n
 for i in range(0,len(paras),size): chunks.append('\n\n'.join(paras[i:i+size]))
 return title,chunks

def main():
 load_env()
 ch=110
 src=BASE/'新版/第110章.md'
 orig=src.read_text(encoding='utf-8',errors='ignore')
 bak=BACK/'第110章_精修前_chunked.md'; shutil.copy2(src,bak)
 task=(BASE/'审核记录/任务卡/第110章_V8122.md').read_text(encoding='utf-8')
 pre=[]
 for role in ['editor','science']:
  p=RAW/f'第110_{role}_pre_v8122.json'
  if p.exists():
   js=json.loads(p.read_text(encoding='utf-8')); pre.append(f'## {role}\n{(js.get("content") or js.get("error", ""))[:900]}')
 notes='\n'.join(pre)
 title,chunks=split_paras(orig,4)
 outs=[]
 for idx,chunk in enumerate(chunks,1):
  prompt=f"""你是《科武纪元》作者。请精修第110章第{idx}/{len(chunks)}段落块，只输出本块正文，不要输出标题，不要总结。

硬约束：
- 保留原剧情顺序、人物关系、事件主干。
- 只增强V8.12.2要求：红线表、叫停权、许可冻结、保险上浮、热线延迟、港口排队、备件证书、物理咽喉+数字锁死。
- 不写正式协议，不触碰第95，不新闻串烧。
- 动作链、物理反馈、账单/接口/证书/延迟。
- 字数约为原块±20%，不得缩成大纲。

【任务卡】\n{task}

【外审摘要】\n{notes}

【原文块】\n{chunk}
"""
  rec=call('author',prompt,max_tokens=5200,temp=0.16,tag=f'author_chunk_{idx}',timeout=180)
  save(f'author_chunk_{idx}',rec)
  if not rec.get('ok'):
   raise SystemExit('AUTHOR_CHUNK_FAIL '+json.dumps(rec,ensure_ascii=False)[:500])
  outs.append(clean(rec['content']))
 new=title+'\n\n'+'\n\n'.join(outs).strip()
 if not new.rstrip().endswith('（本章完）'): new=new.rstrip()+'\n\n（本章完）'
 new=new.replace('仿佛','像').replace('微微','').replace('缓缓','').replace('不禁','').replace('不由得','').replace('意味着','说明').replace('意识到','察觉')+'\n'
 tmp=TMP/'第110章_V8122_TKX分段精修稿.tmp.md'; tmp.write_text(new,encoding='utf-8')
 def pp(kind,text):
  return f"""你是《科武纪元》{kind}写后复审。第一行只输出 PASS 或 FAIL。PASS=可进入项目闭环。FAIL=硬伤/跑偏/明显AI味/缺任务卡必打点。

【任务卡】\n{task}
【全文首段】\n{text[:2800]}
【全文尾段】\n{text[-3200:]}
【机器提示】番茄口径约{fq(text)}字。请审实际文本，不要凭印象。"""
 ep=call('editor',pp('编辑',new),max_tokens=1800,tag='editor_post_chunked',timeout=300); save('editor_post_chunked',ep)
 rp=call('reader',pp('读者',new),max_tokens=1600,tag='reader_post_chunked',timeout=300); save('reader_post_chunked',rp)
 banned=[w for w in ['仿佛','微微','缓缓','不禁','不由得','意味着','意识到'] if w in new]
 must=sum(1 for x in ['保险','许可证','证书','审计','延迟','锁死','红线','港口','备件','热线'] if x in new)
 final=passish(ep) and passish(rp) and fq(new)>=3000 and not banned and must>=5
 sync_out='SKIPPED'
 if final:
  src.write_text(new,encoding='utf-8')
  txt=BASE/'已投稿/第110章.txt'
  if txt.exists(): txt.unlink()
  sync=subprocess.run(['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter','110','--message','V8.12.2第110章TKX分段作者+WF编辑精修闭环','--no-git'],cwd='/root/workspace',capture_output=True,text=True,timeout=300)
  sync_out=sync.stdout+sync.stderr
 report=f"""# 第110章 V8.12.2 TKX分段精修报告

- 路线：TKX gpt-5.5 分段作者；WF opus47fast 编辑；MiniMax 读者
- 原因：TKX长单请求两次524，改为四段短请求保留TKX
- 备份：{bak}
- 临时稿：{tmp}
- 写回：{'是' if final else '否'}
- 番茄口径：{fq(new)}
- 禁词残留：{banned}
- 必打词命中：{must}
- 编辑复审：{'PASS' if passish(ep) else 'FAIL'}
- 读者复审：{'PASS' if passish(rp) else 'FAIL'}
- 已投稿TXT：未生成/若存在已删除

## 同步输出
```text
{sync_out[-3000:]}
```
"""
 rp_path=REV/'第110章_V8122_TKX分段精修报告.md'; rp_path.write_text(report,encoding='utf-8')
 print(json.dumps({'final':final,'fanqie':fq(new),'report':str(rp_path),'tmp':str(tmp),'editor':passish(ep),'reader':passish(rp),'must':must,'banned':banned},ensure_ascii=False))
 if not final: raise SystemExit(3)
if __name__=='__main__': main()
