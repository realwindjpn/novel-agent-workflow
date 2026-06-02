#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess,json,os,re,time
BASE=Path('/root/workspace/科武纪元')
REPORT=BASE/'审核记录/队列汇总/V8122_核心续跑_221_189_223_226_20260516.json'
REPORT.parent.mkdir(parents=True,exist_ok=True)
queue=[221,189,223,226]

def fanqie_count(text):
 lines=[x for x in text.splitlines() if x.strip()]
 title=lines[0] if lines else ''
 return len(re.sub(r'\s+','',text))-len(re.sub(r'\s+','',title))

def run_ch(ch):
 env=os.environ.copy(); env['KEWU_AUTHOR_ROUTE']='tkx'
 t=time.time()
 p=subprocess.run(['python3',str(BASE/'工具脚本/run_refine_chapter_v4.py'),str(ch)],cwd='/root/workspace',env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900)
 rec={'ch':ch,'kind':'core','returncode':p.returncode,'seconds':round(time.time()-t,1),'stdout_tail':p.stdout[-6000:]}
 for line in reversed(p.stdout.splitlines()):
  line=line.strip()
  if line.startswith('{') and line.endswith('}'):
   try: rec['script_json']=json.loads(line); break
   except Exception: pass
 src=BASE/'新版'/f'第{ch}章.md'
 if src.exists():
  text=src.read_text(encoding='utf-8',errors='ignore')
  rec['fanqie']=fanqie_count(text); rec['title']=next((x for x in text.splitlines() if x.strip()),'')
 review=BASE/'审核记录/六角色外审'/f'第{ch}章.md'
 final=review.exists() and '## 最终结论\nPASS' in review.read_text(encoding='utf-8',errors='ignore')
 rec['pass']=bool(final)
 if final:
  txt=BASE/'已投稿'/f'第{ch}章.txt'
  if txt.exists(): txt.unlink(); rec['upload_txt']='deleted_non_upload'
  sp=subprocess.run(['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(ch),'--message',f'V8.12.2第{ch}章TKX作者核心回改闭环','--no-git'],cwd='/root/workspace',text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
  rec['sync_returncode']=sp.returncode; rec['sync_tail']=sp.stdout[-2500:]
 return rec

def main():
 results=[]
 for ch in queue:
  try: rec=run_ch(ch)
  except subprocess.TimeoutExpired as e: rec={'ch':ch,'kind':'core','pass':False,'error':'timeout','stdout_tail':(e.stdout or '')[-3000:] if isinstance(e.stdout,str) else ''}
  except Exception as e: rec={'ch':ch,'kind':'core','pass':False,'error':repr(e)}
  results.append(rec); REPORT.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
  if not rec.get('pass'): break
 print(json.dumps({'report':str(REPORT),'results':[{k:r.get(k) for k in ['ch','pass','fanqie','returncode','seconds','error']} for r in results]},ensure_ascii=False))
 if not all(r.get('pass') for r in results): raise SystemExit(3)
if __name__=='__main__': main()
