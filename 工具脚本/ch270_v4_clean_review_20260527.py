#!/usr/bin/env python3
import json, re, subprocess, time
from datetime import datetime
from pathlib import Path
ROOT=Path('/root/workspace/科武纪元')
OUT=ROOT/'审核记录/六角色外审'
RAW=OUT/'raw/ch270_v4_clean_review_20260527'
RAW.mkdir(parents=True, exist_ok=True)
EVENTS=ROOT/'审核记录/新卷写作队列/events_270_v4_clean_review_20260527.jsonl'
CAND=OUT/'第270章_MiMoPro修订候选_v4_clean_20260527.md'
REPORT=OUT/'第270章_MiMoPro清洁稿复审报告_v4_20260527.md'
ROUTES={'editor':('freemodel','gpt-5.5'),'reader':('alibaba','qwen3.6-plus'),'advisor':('zai','glm-5.1')}
def emit(event,status='RUNNING',msg='',**kw):
 rec={'ts':datetime.now().isoformat(timespec='seconds'),'chapter':270,'event':event,'status':status,'msg':msg}|kw
 EVENTS.parent.mkdir(parents=True, exist_ok=True)
 EVENTS.open('a',encoding='utf-8').write(json.dumps(rec,ensure_ascii=False)+'\n')
def count(t):
 lines=t.strip().splitlines(); title=lines[0] if lines else ''
 return len(re.sub(r'\s+','',t))-len(re.sub(r'\s+','',title))
def verdict(text):
 head=text[:1800]
 if re.search(r'结论[:：]\s*FAIL|\bFAIL\b|不通过|必须回炉',head,re.I): return 'FAIL'
 if re.search(r'结论[:：]\s*PASS|\bPASS\b|通过',head,re.I): return 'PASS'
 return 'UNKNOWN'
def run(role,prompt,timeout=1300):
 pvd,model=ROUTES[role]
 emit(role.upper()+'_START',msg=f'{pvd}/{model}')
 st=time.time()
 p=subprocess.run(['hermes','chat','-Q','--provider',pvd,'-m',model,'-q',prompt,'--max-turns','20','--source','kewu-ch270-v4-clean-review'],cwd='/root/workspace',text=True,capture_output=True,timeout=timeout)
 dur=round(time.time()-st,2)
 out=(p.stdout or '').strip(); err=(p.stderr or '').strip()
 (RAW/f'{role}_stdout.md').write_text(out,encoding='utf-8')
 (RAW/f'{role}_stderr.txt').write_text(err,encoding='utf-8')
 emit(role.upper()+'_DONE' if p.returncode==0 else role.upper()+'_FAIL',status='RUNNING' if p.returncode==0 else 'FAILED',msg=f'exit={p.returncode} dur={dur}',provider=pvd,model=model,duration=dur)
 return out,err,dur,pvd,model,p.returncode
text=CAND.read_text(encoding='utf-8')
fc=count(text); straight=text.count('"')+text.count("'"); bad=[b for b in ['omitted','truncated','```','with open','review diff','/tmp'] if b in text]; end=text.rstrip().endswith('（本章完）')
emit('MACHINE_GATE',status='RUNNING' if fc>=3000 and straight==0 and not bad and end else 'FAILED',msg='PASS' if fc>=3000 and straight==0 and not bad and end else 'FAIL',fanqie_count=fc,straight=straight,bad=bad,end=end)
review=f'''复审《科武纪元》第270章v4清洁稿。首行必须写：结论：PASS/FAIL。若FAIL，只列必改≤3。
重点：半角直引号=0；无前置验证段/代码噪声；保留三分二十秒、方宁承压链、三证据链、第四条目的钩子；格式/数值链/人物无硬伤。

【清洁稿】
{text}
'''
ed,_,ed_dur,ed_p,ed_m,ed_code=run('editor','你是编辑。'+review,timeout=1500)
rd,_,rd_dur,rd_p,rd_m,rd_code=run('reader','你是普通追读读者。'+review,timeout=1200)
ad,_,ad_dur,ad_p,ad_m,ad_code=run('advisor','你是科学+军事顾问。'+review,timeout=1200)
ve,vr,va=verdict(ed),verdict(rd),verdict(ad)
final='FULL_LOOP_PASS_CANDIDATE' if fc>=3000 and straight==0 and not bad and end and ve==vr==va=='PASS' else 'REVIEW_FAIL'
REPORT.write_text(f'''# 第270章 MiMoPro清洁稿复审报告 v4

时间：{datetime.now().isoformat(timespec='seconds')}
结论：{final}
边界：清洁候选稿；未覆盖正式 `新版/第270章.md`；未生成TXT；未上传；未commit。

## 路由
- 清洁：脚本确定性清理 v3（仅剥离噪声与引号规范）
- 编辑：{ed_p}/{ed_m}，duration={ed_dur}s，结论={ve}
- 读者：{rd_p}/{rd_m}，duration={rd_dur}s，结论={vr}
- 科学/军事顾问：{ad_p}/{ad_m}，duration={ad_dur}s，结论={va}

## 机器门禁
- 番茄口径：{fc}
- 半角直引号数：{straight}
- 坏标记：{bad}
- 末尾格式：{'PASS' if end else 'FAIL'}
- 候选稿：`{CAND}`
- raw目录：`{RAW}`

## 编辑复审
{ed}

## 读者复审
{rd}

## 科学/军事顾问复审
{ad}
''',encoding='utf-8')
emit('DONE' if final.endswith('CANDIDATE') else 'REVIEW_FAIL',status=final,msg=final,fanqie_count=fc,straight=straight,report_path=str(REPORT),candidate_path=str(CAND),editor=ve,reader=vr,advisor=va)
print(json.dumps({'final':final,'candidate':str(CAND),'report':str(REPORT),'fanqie_count':fc,'straight':straight,'editor':ve,'reader':vr,'advisor':va},ensure_ascii=False))
