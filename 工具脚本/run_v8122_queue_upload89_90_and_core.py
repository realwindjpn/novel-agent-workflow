#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.2 + 明日上传线队列。
优先上传前精修 89/90；再跑 V8.12.2 回改核心 221/189/223/226。
作者位：TKX gpt-5.5（run_refine_chapter_v4 直连）。
项目级 sync 串行；上传线保留已投稿TXT，回改线删除已投稿TXT。
"""
from pathlib import Path
import subprocess, json, os, re, time
BASE=Path('/root/workspace/科武纪元')
REPORT=BASE/'审核记录/队列汇总/V8122_上传89_90_核心队列_20260515.json'
REPORT.parent.mkdir(parents=True,exist_ok=True)
queue=[
 {'ch':89,'kind':'upload','note':'明日上传前精修'},
 {'ch':90,'kind':'upload','note':'明日上传前精修'},
 {'ch':221,'kind':'core','note':'V8.12.2中大改：共管/交换表'},
 {'ch':189,'kind':'core','note':'V8.12.2中大改：方舟协议现实账单'},
 {'ch':223,'kind':'core','note':'V8.12.2中改：AI视频众包黑产机制'},
 {'ch':226,'kind':'core','note':'V8.12.2中改：政治联盟/审计框架'},
]

def fanqie_count(text):
 lines=[x for x in text.splitlines() if x.strip()]
 title=lines[0] if lines else ''
 return len(re.sub(r'\s+','',text))-len(re.sub(r'\s+','',title))

def add_author_note(ch):
 txt=BASE/'已投稿'/f'第{ch}章.txt'
 if not txt.exists(): return {'ok':False,'reason':'txt_missing'}
 s=txt.read_text(encoding='utf-8')
 if '作者有话说：' in s:
  body,note=s.split('作者有话说：',1)
  if len(note.strip())<=300 and note.strip(): return {'ok':True,'reason':'exists','note_len':len(note.strip())}
 note=f'本章把冲突落到具体城市现场：道路、能源、算力和人的选择。相关技术与社会影响均为小说化处理，现实中仍以安全、合规与公共利益为前提。'
 s=s.rstrip()+f'\n\n作者有话说：\n{note}\n'
 txt.write_text(s,encoding='utf-8')
 return {'ok':True,'reason':'added','note_len':len(note)}

def run_ch(ch,kind):
 env=os.environ.copy(); env['KEWU_AUTHOR_ROUTE']='tkx'
 cmd=['python3',str(BASE/'工具脚本/run_refine_chapter_v4.py'),str(ch)]
 t=time.time()
 p=subprocess.run(cmd,cwd='/root/workspace',env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900)
 out=p.stdout[-6000:]
 rec={'ch':ch,'kind':kind,'returncode':p.returncode,'seconds':round(time.time()-t,1),'stdout_tail':out}
 # parse last json line if any
 for line in reversed(p.stdout.splitlines()):
  line=line.strip()
  if line.startswith('{') and line.endswith('}'):
   try: rec['script_json']=json.loads(line); break
   except Exception: pass
 src=BASE/'新版'/f'第{ch}章.md'
 if src.exists():
  text=src.read_text(encoding='utf-8',errors='ignore')
  rec['fanqie']=fanqie_count(text); rec['title']=next((x for x in text.splitlines() if x.strip()),'')
 # project sync no git, after PASS only
 review=BASE/'审核记录/六角色外审'/f'第{ch}章.md'
 final_pass=review.exists() and '## 最终结论\nPASS' in review.read_text(encoding='utf-8',errors='ignore')
 rec['pass']=bool(final_pass)
 if final_pass:
  if kind=='core':
   txt=BASE/'已投稿'/f'第{ch}章.txt'
   if txt.exists():
    txt.unlink(); rec['upload_txt']='deleted_non_upload'
  else:
   rec['author_note']=add_author_note(ch)
   rec['upload_txt']='kept_for_upload'
  sp=subprocess.run(['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(ch),'--message',f'第{ch}章TKX作者上传/回改精修闭环','--no-git'],cwd='/root/workspace',text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
  rec['sync_returncode']=sp.returncode; rec['sync_tail']=sp.stdout[-2500:]
 return rec

def main():
 results=[]
 for item in queue:
  ch=item['ch']
  src=BASE/'新版'/f'第{ch}章.md'
  if not src.exists():
   results.append({**item,'pass':False,'skip':'source_missing'}); continue
  try:
   rec=run_ch(ch,item['kind']); rec.update(item)
  except subprocess.TimeoutExpired as e:
   rec={**item,'pass':False,'error':'timeout','stdout_tail':(e.stdout or '')[-3000:] if isinstance(e.stdout,str) else ''}
  except Exception as e:
   rec={**item,'pass':False,'error':repr(e)}
  results.append(rec)
  REPORT.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
  if not rec.get('pass'):
   break
 REPORT.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'report':str(REPORT),'results':[{k:r.get(k) for k in ['ch','kind','pass','fanqie','returncode','seconds','error','skip']} for r in results]},ensure_ascii=False))
 if not all(r.get('pass') for r in results): raise SystemExit(3)
if __name__=='__main__': main()
