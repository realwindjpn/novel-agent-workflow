#!/usr/bin/env python3
import json, pathlib, re, subprocess, time, datetime, os
ROOT=pathlib.Path('/root/workspace/科武纪元')
NEW=ROOT/'新版/第270章.md'
REPORT=ROOT/'审核记录/六角色外审/第270章_闭环报告_20260526.md'
RAWDIR=ROOT/'审核记录/六角色外审/raw'; RAWDIR.mkdir(parents=True,exist_ok=True)
EV=ROOT/'审核记录/新卷写作队列/events_266_275_20260526.jsonl'
Q=ROOT/'审核记录/新卷写作队列/queue_266_275_20260526.json'
CH=270
BANS=['意味着','仿佛','似乎','微微','宛如','犹如','悄然','骤然','瞬间','极致','无数','彻底','崩塌','撕裂','震撼']
def now(): return datetime.datetime.now().isoformat(timespec='seconds')
def event(ev,st,msg='',**kw):
 d={'ts':now(),'chapter':CH,'event':ev,'status':st,'msg':msg}; d.update(kw)
 with EV.open('a',encoding='utf-8') as f:f.write(json.dumps(d,ensure_ascii=False)+'\n')
def call(p,m,prompt,timeout=300):
 env=os.environ.copy();
 if p=='xiaomi': env['HERMES_STREAM_READ_TIMEOUT']='300'
 t=time.time(); r=subprocess.run(['hermes','chat','-Q','--provider',p,'--model',m,'-q',prompt],text=True,capture_output=True,timeout=timeout,env=env)
 return {'provider':p,'model':m,'exit_code':r.returncode,'duration':round(time.time()-t,2),'stdout':r.stdout.strip(),'stderr':r.stderr.strip()}
def clean(s):
 s=re.sub(r'^```.*?\n|```$','',s.strip(),flags=re.S)
 for a,b in {'意味着':'代表','仿佛':'像','似乎':'像','微微':'','宛如':'像','犹如':'像','悄然':'','骤然':'','瞬间':'','极致':'','无数':'大量','彻底':'','崩塌':'失效','撕裂':'分开','震撼':'冲击'}.items(): s=s.replace(a,b)
 return s.strip()
def count(t):
 lines=t.splitlines(); title=lines[0] if lines else ''; return len(re.sub(r'\s+','', ''.join(lines[1:])))-len(re.sub(r'\s+','',title))
def update(status, **kw):
 q=json.loads(Q.read_text(encoding='utf-8'))
 q['stage']='RUNNING'; q['current_chapter']=CH; q['current_stage']=status; q['updated_at']=now()
 for c in q.get('chapters',[]):
  if c.get('chapter')==CH:
   c['status']=status; c.update(kw); c['updated_at']=now()
 Q.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
 old=NEW.read_text(encoding='utf-8') if NEW.exists() else ''
 event('EXPAND_REPAIR_START','RUNNING','count below 3000; expand with mimo pro')
 update('RUNNING',next_action='expand_to_3000')
 prompt=f'''你是《科武纪元》作者OS。第270章当前番茄口径仅2836，低于3000。请在不破坏原结构、不重写整章的前提下，把正文扩展到3300-4200字，直接输出修后完整正文。
要求：
- 保留现有标题和主线。
- 只新增必要场景细节：三条舰队等待链路、联合政府决策压力、箱体温度/震动、设备代价、人员动作。
- 不新增大设定，不把第271章内容提前。
- 禁词不得出现：{','.join(BANS)}。
- 保持温度线单调、光程常识正确、无拼接。
正文：
{old}
'''
 res=call('xiaomi','mimo-v2.5-pro',prompt,timeout=420)
 (RAWDIR/'第270章_mimo_pro_expand_raw.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
 if res['exit_code']!=0 or len(res['stdout'])<2000:
  update('FAILED',fail_reason='expand failed '+res.get('stderr','')[:300]); event('EXPAND_FAIL','FAILED',res.get('stderr','')[:300]); return
 text=clean(res['stdout'])
 if not text.startswith('第270章'): text='第270章 第三次校验\n\n'+text
 NEW.write_text(text+'\n',encoding='utf-8')
 cnt=count(text); bans=[b for b in BANS if b in text]
 event('EXPAND_DONE','RUNNING',f'count={cnt} bans={len(bans)}',fanqie_count=cnt,bans=bans)
 if cnt<3000 or bans:
  update('FAILED',fail_reason=f'after expand count={cnt} bans={bans}'); event('MACHINE_GATE_FAIL','FAILED',f'count={cnt} bans={bans}'); return
 ed=call('custom:WF','claude-opus-4-7-high-fast',f'编辑OS审第270章修后正文。只输出：结论：PASS/FAIL；必改项≤3；理由≤200字。检查大纲对齐、时间线、无拼接、字数达标。正文：{text[:24000]}',timeout=240)
 rd=call('alibaba','qwen3.6-plus',f'读者审第270章修后正文。只输出：结论：PASS/FAIL；劝退点≤3；理由≤200字。正文：{text[:22000]}',timeout=180)
 ad=call('zai','glm-5.1',f'科学/军事顾问审第270章修后正文。只输出：结论：PASS/FAIL；硬伤≤3；理由≤200字。正文：{text[:22000]}',timeout=220)
 reviews={'editor':ed,'reader':rd,'advisor':ad}
 (RAWDIR/'第270章_mimo_pro_expand_reviews.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2),encoding='utf-8')
 ok=all(r['exit_code']==0 and 'PASS' in r['stdout'] and 'FAIL' not in r['stdout'].split('结论',1)[-1][:20] for r in reviews.values())
 REPORT.write_text(f'''# 第270章 闭环报告

时间：{now()}
结论：{'FULL_LOOP_PASS' if ok else 'REVIEW_FAIL'}
方式：MiMo v2.5 Pro 单次整章 → MiMo Pro扩写补足字数。

## 门禁
- 番茄口径：{cnt}
- 禁词：{len(bans)}
- 上传边界：未生成已投稿TXT，未上传番茄

## 模型证据
- 扩写：xiaomi/mimo-v2.5-pro exit={res['exit_code']} duration={res['duration']}
- 编辑：custom:WF/claude-opus-4-7-high-fast exit={ed['exit_code']} duration={ed['duration']}
- 读者：alibaba/qwen3.6-plus exit={rd['exit_code']} duration={rd['duration']}
- 顾问：zai/glm-5.1 exit={ad['exit_code']} duration={ad['duration']}

## 编辑
{ed['stdout']}

## 读者
{rd['stdout']}

## 顾问
{ad['stdout']}
''',encoding='utf-8')
 if ok:
  subprocess.run(['git','-C',str(ROOT),'add','-f','新版/第270章.md',str(REPORT.relative_to(ROOT)),str((RAWDIR/'第270章_mimo_pro_full_raw.json').relative_to(ROOT)),str((RAWDIR/'第270章_mimo_pro_expand_raw.json').relative_to(ROOT)),str((RAWDIR/'第270章_mimo_pro_expand_reviews.json').relative_to(ROOT))],check=False)
  subprocess.run(['git','-C',str(ROOT),'commit','-m','write: chapter 270 mimo pro full'],text=True,capture_output=True)
  commit=subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],text=True,capture_output=True).stdout.strip()
  update('FULL_LOOP_PASS',report_path=str(REPORT),git_commit=commit,next_action='continue_271')
  event('FULL_LOOP_PASS','FULL_LOOP_PASS','chapter 270 closed',report_path=str(REPORT),git_commit=commit,fanqie_count=cnt,next_action='continue_271')
 else:
  fail='\n'.join(k+': '+v['stdout'][:300] for k,v in reviews.items())
  update('REVIEW_FAIL',report_path=str(REPORT),fail_reason=fail,next_action='repair_again')
  event('REVIEW_FAIL','FAILED','review not pass',report_path=str(REPORT))
if __name__=='__main__': main()
