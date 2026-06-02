#!/usr/bin/env python3
import datetime,json,os,pathlib,re,subprocess,time
ROOT=pathlib.Path('/root/workspace/科武纪元')
RAWDIR=ROOT/'审核记录/六角色外审/raw'; RAWDIR.mkdir(parents=True,exist_ok=True)
EV=ROOT/'审核记录/新卷写作队列/events_266_275_20260526.jsonl'
Q=ROOT/'审核记录/新卷写作队列/queue_266_275_20260526.json'
NEW=ROOT/'新版/第270章.md'
REPORT=ROOT/'审核记录/六角色外审/第270章_闭环报告_20260526.md'
TASK=ROOT/'审核记录/六角色外审/第270章_写前任务卡_20260526.md'
CH=270
BANS=['意味着','仿佛','似乎','微微','宛如','犹如','悄然','骤然','瞬间','极致','无数','彻底','崩塌','撕裂','震撼']
REPS={'意味着':'代表','仿佛':'像','似乎':'像','微微':'','宛如':'像','犹如':'像','悄然':'','骤然':'','瞬间':'','极致':'','无数':'大量','彻底':'','崩塌':'失效','撕裂':'分开','震撼':'冲击'}
def now(): return datetime.datetime.now().isoformat(timespec='seconds')
def event(ev,st,msg='',**kw):
 d={'ts':now(),'chapter':CH,'event':ev,'status':st,'msg':msg}; d.update(kw)
 with EV.open('a',encoding='utf-8') as f:f.write(json.dumps(d,ensure_ascii=False)+'\n')
def update(status=None,**kw):
 q=json.loads(Q.read_text(encoding='utf-8'))
 q['stage']='RUNNING'; q['current_chapter']=CH; q['current_stage']=kw.get('current_stage',status or ''); q['updated_at']=now()
 for c in q.get('chapters',[]):
  if c.get('chapter')==CH:
   if status:c['status']=status
   c.update({k:v for k,v in kw.items() if k!='current_stage'}); c['updated_at']=now()
 Q.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
def call(p,m,prompt,timeout=420):
 env=os.environ.copy(); env['HERMES_STREAM_READ_TIMEOUT']='420'
 t=time.time(); r=subprocess.run(['hermes','chat','-Q','--provider',p,'--model',m,'-q',prompt],text=True,capture_output=True,timeout=timeout,env=env)
 return {'provider':p,'model':m,'exit_code':r.returncode,'duration':round(time.time()-t,2),'stdout':r.stdout.strip(),'stderr':r.stderr.strip()}
def clean(s):
 s=re.sub(r'^```.*?\n|```$','',s.strip(),flags=re.S)
 s=re.sub(r'^我(已|来|将).*?全文如下[:：]\s*','',s,flags=re.S)
 s=s.replace('\n---\n','\n')
 for a,b in REPS.items():s=s.replace(a,b)
 return s.strip()
def cnt(t):
 lines=t.splitlines(); title=lines[0] if lines else ''
 return len(re.sub(r'\s+','', ''.join(lines[1:])))-len(re.sub(r'\s+','',title))
def passp(r):
 s=r.get('stdout',''); head=s.split('结论',1)[-1][:40]
 return r.get('exit_code')==0 and 'PASS' in s and 'FAIL' not in head

def main():
 event('WF_AUTHOR_REWRITE_START','RUNNING','WF opus writes, MiMo edits')
 update('RUNNING',current_stage='WF_AUTHOR_REWRITE',next_action='wf_author_mimo_editor')
 prev=(ROOT/'新版/第269章.md').read_text(encoding='utf-8') if (ROOT/'新版/第269章.md').exists() else ''
 outline=(ROOT/'科武纪元大纲 V8_完整版.md').read_text(encoding='utf-8')[:30000] if (ROOT/'科武纪元大纲 V8_完整版.md').exists() else ''
 bfail=(ROOT/'审核记录/六角色外审/第270章_闭环报告_20260526.md').read_text(encoding='utf-8') if (ROOT/'审核记录/六角色外审/第270章_闭环报告_20260526.md').exists() else ''
 crev=(RAWDIR/'第270章_mimo_parallel_C_reviews.json').read_text(encoding='utf-8') if (RAWDIR/'第270章_mimo_parallel_C_reviews.json').exists() else ''
 TASK.write_text('# 第270章 写前任务卡\n\n方式：WF Opus整章重写；MiMo v2.5 Pro当编辑；Qwen读者；ZAI顾问。\n红线：番茄口径≥3000；禁词0；温度/传输/震动连续；不拼接；不上传番茄。\n',encoding='utf-8')
 prompt=f'''你是《科武纪元》作者OS，用 WF Opus 写第270章完整正文。
只输出正文，不要解释。

首行：第270章 第三次校验
末尾：（本章完）
番茄口径：4200-6200字，必须≥3000。

必须修正前稿失败点：
- 温度连续：38.9→39.0→39.1→39.3→39.5→39.8须有时间/速率过渡，不得跳。
- 传输进度连续：11%后到19%、24%、30/31%、37%、43%须对账时间/剩余时间，不得突变无解释。
- 震动间隔连续：7min→6min→5:30→5:15→4:40→3:20，若引用某档，正文先出现该档。
- 功率递增时，中心-外壳温差不得恒定，可0.7→0.8→0.9。

承接第269章：五节点、索引签名异常、拓扑同构孵化舱、箱体升温、三条舰队轨道数据、联合政府决策压力。
本章只推进第三次校验：让异常变成可验证证据；不要提前解谜。
400km光程≈1.3ms；秒级等待归因协议/队列/设备响应。
写动作链、设备反馈、资源代价、决策压力；勿咏叹调。
禁词勿用：{','.join(BANS)}

上一章末段：
{prev[-3500:]}

大纲节选：
{outline[-10000:]}

前稿失败证据：
{bfail[-2500:]}
{crev[-2200:]}
'''
 author=call('custom:WF','claude-opus-4-7-high-fast',prompt,timeout=520)
 (RAWDIR/'第270章_wf_author_raw.json').write_text(json.dumps(author,ensure_ascii=False,indent=2),encoding='utf-8')
 if author['exit_code']!=0 or len(author['stdout'])<2500:
  event('WF_AUTHOR_FAIL','FAILED',author.get('stderr','')[:300]); update('FAILED',fail_reason='WF author failed '+author.get('stderr','')[:300],next_action='retry_wf_or_fix_c'); return
 text=clean(author['stdout'])
 if not text.startswith('第270章'): text='第270章 第三次校验\n\n'+text
 NEW.write_text(text+'\n',encoding='utf-8')
 n=cnt(text); bans=[b for b in BANS if b in text]
 event('WF_AUTHOR_DONE','RUNNING',f'count={n} bans={len(bans)}',fanqie_count=n,bans=bans)
 if n<3000 or bans:
  event('MACHINE_GATE_FAIL','FAILED',f'count={n} bans={bans}'); update('FAILED',fail_reason=f'WF machine gate count={n} bans={bans}',next_action='deterministic_clean_or_retry'); return
 mimo=call('xiaomi','mimo-v2.5-pro',f'你是编辑OS。审第270章WF稿。只输出：结论：PASS/FAIL；必改项≤3；理由≤220字。重点查温度/传输/震动连续性、是否拼接、硬科幻对账。正文：{text[:24000]}',timeout=360)
 qwen=call('alibaba','qwen3.6-plus',f'你是读者。审第270章WF稿。只输出：结论：PASS/FAIL；劝退点≤3；理由≤200字。正文：{text[:22000]}',timeout=220)
 zai=call('zai','glm-5.1',f'你是科学/军事顾问。审第270章WF稿硬伤。只输出：结论：PASS/FAIL；硬伤≤3；理由≤220字。正文：{text[:22000]}',timeout=260)
 reviews={'mimo_editor':mimo,'reader':qwen,'advisor':zai}
 (RAWDIR/'第270章_wf_author_mimo_editor_reviews.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2),encoding='utf-8')
 ok=all(passp(r) for r in reviews.values())
 REPORT.write_text(f'''# 第270章 闭环报告

时间：{now()}
结论：{'FULL_LOOP_PASS' if ok else 'REVIEW_FAIL'}
方式：WF Opus整章重写；MiMo v2.5 Pro编辑；Qwen读者；ZAI顾问。

## 门禁
- 番茄口径：{n}
- 禁词：{len(bans)}
- 上传边界：未生成已投稿TXT，未上传番茄

## 模型证据
- 作者：custom:WF/claude-opus-4-7-high-fast exit={author['exit_code']} duration={author['duration']}
- 编辑：xiaomi/mimo-v2.5-pro exit={mimo['exit_code']} duration={mimo['duration']}
- 读者：alibaba/qwen3.6-plus exit={qwen['exit_code']} duration={qwen['duration']}
- 顾问：zai/glm-5.1 exit={zai['exit_code']} duration={zai['duration']}

## MiMo编辑
{mimo.get('stdout','')}

## 读者
{qwen.get('stdout','')}

## 顾问
{zai.get('stdout','')}
''',encoding='utf-8')
 if ok:
  files=[NEW,REPORT,TASK,RAWDIR/'第270章_wf_author_raw.json',RAWDIR/'第270章_wf_author_mimo_editor_reviews.json']
  subprocess.run(['git','-C',str(ROOT),'add','-f']+[str(p.relative_to(ROOT)) for p in files],check=False)
  subprocess.run(['git','-C',str(ROOT),'commit','-m','write: chapter 270 wf author mimo editor'],text=True,capture_output=True)
  commit=subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],text=True,capture_output=True).stdout.strip()
  update('FULL_LOOP_PASS',report_path=str(REPORT),git_commit=commit,next_action='continue_271')
  event('FULL_LOOP_PASS','FULL_LOOP_PASS','chapter 270 closed by WF author',report_path=str(REPORT),git_commit=commit,fanqie_count=n,next_action='continue_271')
 else:
  fail='\n'.join(k+': '+v.get('stdout','')[:400] for k,v in reviews.items())
  update('REVIEW_FAIL',report_path=str(REPORT),fail_reason=fail,next_action='repair_wf稿_or_retry')
  event('REVIEW_FAIL','FAILED','WF author review fail',report_path=str(REPORT),fanqie_count=n)
if __name__=='__main__': main()
