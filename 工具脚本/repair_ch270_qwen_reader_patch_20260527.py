#!/usr/bin/env python3
import datetime,json,os,pathlib,re,subprocess,time
ROOT=pathlib.Path('/root/workspace/科武纪元')
RAWDIR=ROOT/'审核记录/六角色外审/raw'; RAWDIR.mkdir(parents=True,exist_ok=True)
EV=ROOT/'审核记录/新卷写作队列/events_266_275_20260526.jsonl'
Q=ROOT/'审核记录/新卷写作队列/queue_266_275_20260526.json'
NEW=ROOT/'新版/第270章.md'
REPORT=ROOT/'审核记录/六角色外审/第270章_闭环报告_20260526.md'
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
def call(p,m,prompt,timeout=360):
 env=os.environ.copy(); env['HERMES_STREAM_READ_TIMEOUT']='420'
 t=time.time(); r=subprocess.run(['hermes','chat','-Q','--provider',p,'--model',m,'-q',prompt],text=True,capture_output=True,timeout=timeout,env=env)
 return {'provider':p,'model':m,'exit_code':r.returncode,'duration':round(time.time()-t,2),'stdout':r.stdout.strip(),'stderr':r.stderr.strip()}
def clean(s):
 s=re.sub(r'^```.*?\n|```$','',s.strip(),flags=re.S)
 s=re.sub(r'^.*?全文如下[:：]\s*','',s,flags=re.S)
 s=s.replace('\n---\n','\n')
 for a,b in REPS.items(): s=s.replace(a,b)
 return s.strip()
def cnt(t):
 lines=t.splitlines(); title=lines[0] if lines else ''
 return len(re.sub(r'\s+','', ''.join(lines[1:])))-len(re.sub(r'\s+','',title))
def passp(r):
 s=r.get('stdout',''); head=s.split('结论',1)[-1][:50]
 return r.get('exit_code')==0 and 'PASS' in s and 'FAIL' not in head

def main():
 event('QWEN_READER_PATCH_START','RUNNING','qwen repairs its reader fail')
 update('RUNNING',current_stage='QWEN_READER_PATCH',next_action='qwen_patch_then_reviews')
 text=NEW.read_text(encoding='utf-8')
 report=REPORT.read_text(encoding='utf-8') if REPORT.exists() else ''
 prompt=f'''你是《科武纪元》读者修订编辑。请在不重写整章、不破坏硬科幻数值链的前提下，修订第270章全文并直接输出修后完整正文。

必须解决这些FAIL点：
1. 数据密度过高：保留关键数值，但删/合并重复报数，让人物动作和压力有缓冲。
2. “只读广播不应……”同类前提只保留1-2处，不要反复说。
3. 给赵大山一处实质判断，不只是动作。
4. 东方舰指挥层/联合政府压力补一处简短博弈或代价，不要只靠通报推动。
5. 删除结尾刻意断奏，结尾改为动作/屏幕终态。
6. 修正顾问轻微硬伤：40.0°C后，30分钟/2小时外推用同一斜率口径；可改成“按当前斜率三十分钟约41.5，若制冷与散热拖低平均斜率，两小时约44；若继续加速会更高”。
7. 补上校验-六-A最终摘要生成/发送动作，闭合第三份证据。

不得改坏：
- 震动链：7min→6min→5:30→5:15→4:40→3:20
- 传输链：11→19→24→30→37→43，且速率解释保留
- 温度链：38.9→39.0→39.1→39.3→39.5→39.8→40.0；温差0.7→0.8→0.9→1.0
- 番茄口径≥3000，禁词不用：{','.join(BANS)}
- 首行：第270章 第三次校验；末尾：（本章完）
- 不输出解释，只输出正文。

失败报告：
{report}

原文：
{text}
'''
 res=call('alibaba','qwen3.6-plus',prompt,timeout=420)
 (RAWDIR/'第270章_qwen_reader_patch_raw.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
 if res['exit_code']!=0 or len(res['stdout'])<2500:
  event('QWEN_READER_PATCH_FAIL','FAILED',res.get('stderr','')[:300]); update('FAILED',fail_reason='qwen patch failed '+res.get('stderr','')[:300],next_action='manual_route'); return
 new=clean(res['stdout'])
 if not new.startswith('第270章'): new='第270章 第三次校验\n\n'+new
 NEW.write_text(new+'\n',encoding='utf-8')
 n=cnt(new); bans=[b for b in BANS if b in new]
 event('QWEN_READER_PATCH_DONE','RUNNING',f'count={n} bans={len(bans)}',fanqie_count=n,bans=bans)
 if n<3000 or bans:
  event('MACHINE_GATE_FAIL','FAILED',f'count={n} bans={bans}'); update('FAILED',fail_reason=f'patch machine gate count={n} bans={bans}',next_action='retry'); return
 ed=call('custom:WF','claude-opus-4-7-high-fast',f'你是编辑OS。审第270章修后正文。只输出：结论：PASS/FAIL；必改项≤3；理由≤200字。重点查温度/传输/震动连续性、拼接、人物压力是否补足。正文：{new[:24000]}',260)
 rd=call('alibaba','qwen3.6-plus',f'你是读者。审第270章修后正文。只输出：结论：PASS/FAIL；劝退点≤3；理由≤200字。正文：{new[:22000]}',220)
 ad=call('zai','glm-5.1',f'你是科学/军事顾问。审第270章修后正文硬伤。只输出：结论：PASS/FAIL；硬伤≤3；理由≤220字。正文：{new[:22000]}',260)
 reviews={'editor':ed,'reader':rd,'advisor':ad}
 (RAWDIR/'第270章_qwen_reader_patch_reviews.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2),encoding='utf-8')
 ok=all(passp(r) for r in reviews.values())
 REPORT.write_text(f'''# 第270章 闭环报告

时间：{now()}
结论：{'FULL_LOOP_PASS' if ok else 'REVIEW_FAIL'}
方式：WF Opus整章稿 → Qwen读者修订 → WF/Qwen/ZAI复审。

## 门禁
- 番茄口径：{n}
- 禁词：{len(bans)}
- 上传边界：未生成已投稿TXT，未上传番茄

## 模型证据
- 修订：alibaba/qwen3.6-plus exit={res['exit_code']} duration={res['duration']}
- 编辑：custom:WF/claude-opus-4-7-high-fast exit={ed['exit_code']} duration={ed['duration']}
- 读者：alibaba/qwen3.6-plus exit={rd['exit_code']} duration={rd['duration']}
- 顾问：zai/glm-5.1 exit={ad['exit_code']} duration={ad['duration']}

## 编辑
{ed.get('stdout','')}

## 读者
{rd.get('stdout','')}

## 顾问
{ad.get('stdout','')}
''',encoding='utf-8')
 if ok:
  files=[NEW,REPORT,RAWDIR/'第270章_qwen_reader_patch_raw.json',RAWDIR/'第270章_qwen_reader_patch_reviews.json']
  subprocess.run(['git','-C',str(ROOT),'add','-f']+[str(p.relative_to(ROOT)) for p in files],check=False)
  subprocess.run(['git','-C',str(ROOT),'commit','-m','write: chapter 270 qwen reader patch'],text=True,capture_output=True)
  commit=subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],text=True,capture_output=True).stdout.strip()
  update('FULL_LOOP_PASS',report_path=str(REPORT),git_commit=commit,next_action='continue_271')
  event('FULL_LOOP_PASS','FULL_LOOP_PASS','chapter 270 closed after qwen patch',report_path=str(REPORT),git_commit=commit,fanqie_count=n,next_action='continue_271')
 else:
  fail='\n'.join(k+': '+v.get('stdout','')[:400] for k,v in reviews.items())
  update('REVIEW_FAIL',report_path=str(REPORT),fail_reason=fail,next_action='targeted_repair')
  event('REVIEW_FAIL','FAILED','qwen patch review fail',report_path=str(REPORT),fanqie_count=n)
if __name__=='__main__': main()
