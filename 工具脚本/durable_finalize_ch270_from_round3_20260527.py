#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, pathlib, re, subprocess, datetime, os, time
ROOT=pathlib.Path('/root/workspace/科武纪元')
EV=ROOT/'审核记录/新卷写作队列/events_266_275_20260526.jsonl'
Q=ROOT/'审核记录/新卷写作队列/queue_266_275_20260526.json'
RAWDIR=ROOT/'审核记录/六角色外审/raw'
NEW=ROOT/'新版/第270章.md'
REPORT=ROOT/'审核记录/六角色外审/第270章_闭环报告_20260526.md'
BANS=['意味着','仿佛','似乎','微微','宛如','犹如','悄然','骤然','瞬间','极致','无数','彻底','崩塌','撕裂','震撼']
def now(): return datetime.datetime.now().isoformat(timespec='seconds')
def event(ev,st,msg='',**kw):
 rec={'ts':now(),'chapter':270,'event':ev,'status':st,'msg':msg}; rec.update(kw)
 with EV.open('a',encoding='utf-8') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
def update(status,**kw):
 q=json.loads(Q.read_text(encoding='utf-8')); q['stage']='RUNNING'; q['current_chapter']=270; q['current_stage']=status; q['updated_at']=now()
 for c in q.get('chapters',[]):
  if c.get('chapter')==270:
   c['status']=status; c.update(kw); c['updated_at']=now()
 Q.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
def call(p,m,prompt,timeout=360):
 env=os.environ.copy(); env['HERMES_STREAM_READ_TIMEOUT']='420'; t=time.time()
 r=subprocess.run(['hermes','chat','-Q','--provider',p,'--model',m,'-q',prompt],text=True,capture_output=True,timeout=timeout,env=env,cwd=str(ROOT))
 return {'provider':p,'model':m,'exit_code':r.returncode,'duration':round(time.time()-t,2),'stdout':r.stdout.strip(),'stderr':r.stderr.strip()}
def cnt(t):
 lines=t.splitlines(); title=lines[0] if lines else ''
 return len(re.sub(r'\s+','', ''.join(lines[1:])))-len(re.sub(r'\s+','',title))
def passp(r):
 s=r.get('stdout',''); head=s.split('结论',1)[-1][:60]
 return r.get('exit_code')==0 and 'PASS' in s and 'FAIL' not in head

def main():
 event('TARGETED_FINALIZE_START','RUNNING','WF targeted final repair on round3')
 text=NEW.read_text(encoding='utf-8')
 report=REPORT.read_text(encoding='utf-8')
 prompt=f'''你是《科武纪元》编辑修订位。请基于第270章现稿做“最小修订”，直接输出完整正文。
不得解释，不得diff，不得省略。
必须保留首行：第270章 第三次校验；末尾：（本章完）。
番茄口径≥3000，禁词勿用：{','.join(BANS)}。

只修以下失败点：
1. 传输时间线：删掉/改掉“加起来不到一个小时”等余量矛盾句。统一为：37%→43%后剩约41-45分钟，封装读件还需20分钟，总余量很紧，不能说宽裕。
2. 温差二档缺失：补明确二档读数：二档四千瓦，箱壁38.4/中心39.2或39.3，温差0.8；三档后温差0.9/1.0。不要凭空归纳。
3. 震动外推：把“指数模型确定”改成“四样本粗估，下一档落在4:40附近，再下一档可能跳到3:20”，避免跳档矛盾。
4. 读感：合并重复的毫秒报数，不要反复“一点三下行/二点六上行”；给赵大山一句实质判断；林星辰在两小时窗口处给一个身体反馈。
5. 保留三份证据：签名同源、语法应答、主动握手。

当前失败报告：
{report[-3500:]}

现稿：
{text}
'''
 res=call('custom:WF','claude-opus-4-7-high-fast',prompt,420)
 (RAWDIR/'第270章_durable_targeted_finalize_raw.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
 if res['exit_code']!=0 or len(res['stdout'])<2500:
  event('TARGETED_FINALIZE_FAIL','FAILED',res.get('stderr','')[:300]); update('FAILED',fail_reason='targeted finalize failed',next_action='manual'); return
 out=res['stdout'].strip()
 out=re.sub(r'^```.*?\n|```$','',out,flags=re.S).strip()
 if not out.startswith('第270章'): out='第270章 第三次校验\n\n'+out
 NEW.write_text(out+'\n',encoding='utf-8')
 n=cnt(out); hits=[b for b in BANS if b in out]
 if n<3000 or hits or '（本章完）' not in out[-100:]:
  event('MACHINE_GATE','FAILED',f'count={n} bans={hits} end={"（本章完）" in out[-100:]}',fanqie_count=n,fail_reason='machine gate final'); update('FAILED',fanqie_count=n,fail_reason='machine gate final',next_action='manual'); return
 reviews={
  'editor':call('custom:WF','claude-opus-4-7-high-fast',f'审第270章最终稿。只输出：结论：PASS/FAIL；必改项≤3；理由≤180字。正文：{out[:24000]}',260),
  'reader':call('alibaba','qwen3.6-plus',f'读者审第270章最终稿。只输出：结论：PASS/FAIL；劝退点≤3；理由≤180字。正文：{out[:22000]}',220),
  'advisor':call('zai','glm-5.1',f'顾问审第270章最终稿硬伤。只输出：结论：PASS/FAIL；硬伤≤3；理由≤180字。正文：{out[:22000]}',260)
 }
 (RAWDIR/'第270章_durable_targeted_finalize_reviews.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2),encoding='utf-8')
 ok=all(passp(v) for v in reviews.values())
 REPORT.write_text(f'''# 第270章 闭环报告

时间：{now()}
结论：{'FULL_LOOP_PASS' if ok else 'REVIEW_FAIL'}
方式：durable runner BLOCKED后，WF最小修订；WF/Qwen/ZAI复审。

## 门禁
- 番茄口径：{n}
- 禁词：{len(hits)}
- 上传边界：未生成已投稿TXT，未上传番茄

## 模型证据
- 修订：custom:WF/claude-opus-4-7-high-fast exit={res['exit_code']} duration={res['duration']}
- 编辑：{reviews['editor']['provider']}/{reviews['editor']['model']} exit={reviews['editor']['exit_code']} duration={reviews['editor']['duration']}
- 读者：{reviews['reader']['provider']}/{reviews['reader']['model']} exit={reviews['reader']['exit_code']} duration={reviews['reader']['duration']}
- 顾问：{reviews['advisor']['provider']}/{reviews['advisor']['model']} exit={reviews['advisor']['exit_code']} duration={reviews['advisor']['duration']}

## 编辑
{reviews['editor']['stdout']}

## 读者
{reviews['reader']['stdout']}

## 顾问
{reviews['advisor']['stdout']}
''',encoding='utf-8')
 if ok:
  subprocess.run(['python3',str(ROOT/'工具脚本/sync_kewu.py'),'--chapter','270','--message','第270章闭环','--no-git'],cwd='/root/workspace',text=True,capture_output=True,timeout=240)
  files=[NEW,REPORT,RAWDIR/'第270章_durable_targeted_finalize_raw.json',RAWDIR/'第270章_durable_targeted_finalize_reviews.json',Q,EV]
  subprocess.run(['git','-C',str(ROOT),'add','-f','--']+[str(p.relative_to(ROOT)) for p in files if p.exists()],text=True,capture_output=True,timeout=120)
  subprocess.run(['git','-C',str(ROOT),'commit','-m','write: chapter 270 durable finalized'],text=True,capture_output=True,timeout=180)
  sha=subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],text=True,capture_output=True).stdout.strip()
  event('FULL_LOOP_PASS','FULL_LOOP_PASS','chapter 270 closed',report_path=str(REPORT),git_commit=sha,fanqie_count=n,next_action='continue_271')
  update('FULL_LOOP_PASS',report_path=str(REPORT),git_commit=sha,fanqie_count=n,next_action='continue_271')
 else:
  fail='\n'.join(k+': '+v['stdout'][:300] for k,v in reviews.items())
  event('REVIEW_FAIL','FAILED','targeted finalize review fail',report_path=str(REPORT),fail_reason=fail,fanqie_count=n)
  update('FAILED',report_path=str(REPORT),fail_reason=fail,fanqie_count=n,next_action='manual')
if __name__=='__main__': main()
