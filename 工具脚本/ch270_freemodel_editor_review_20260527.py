#!/usr/bin/env python3
import json, re, subprocess, time
from datetime import datetime
from pathlib import Path
ROOT=Path('/root/workspace/科武纪元')
OUT=ROOT/'审核记录/六角色外审'
RAW=OUT/'raw/ch270_freemodel_editor_review_20260527'
RAW.mkdir(parents=True, exist_ok=True)
EVENTS=ROOT/'审核记录/新卷写作队列/events_270_freemodel_editor_review_20260527.jsonl'
CAND=OUT/'第270章_MiMoPro修订候选_v2_20260527.md'
REPORT=OUT/'第270章_freemodel_GPT55编辑补审_v2_20260527.md'

def emit(event,status='RUNNING',msg='',**kw):
 rec={'ts':datetime.now().isoformat(timespec='seconds'),'chapter':270,'event':event,'status':status,'msg':msg}|kw
 EVENTS.parent.mkdir(parents=True, exist_ok=True)
 EVENTS.open('a',encoding='utf-8').write(json.dumps(rec,ensure_ascii=False)+'\n')

def verdict(text):
 head=text[:2000]
 if re.search(r'结论[:：]\s*FAIL|\bFAIL\b|不通过|必须回炉',head,re.I): return 'FAIL'
 if re.search(r'结论[:：]\s*PASS|\bPASS\b|通过',head,re.I): return 'PASS'
 return 'UNKNOWN'
chapter=CAND.read_text(encoding='utf-8')
prompt=f'''你是《科武纪元》第270章编辑复审，模型路线 freemodel/gpt-5.5。
首行必须写：结论：PASS 或 结论：FAIL。
若FAIL，只列必改≤3，不写长篇建议。

复审目标：验证MiMo按上一轮WF编辑必改后是否可通过。
必查：
1. 全文引号统一为中文弯引号，无半角直引号污染。
2. 震动链补齐3分20秒，不再从4分40秒跳到2分40秒。
3. 方宁三档制冷处有“判断—迟疑—反向确认—执行”的承压动作，不只是报数机。
4. 数值链、人物压力、三证据链、章末钩子、格式无硬伤。

【正文】
{chapter}
'''
emit('FREEMODEL_EDITOR_START',msg='freemodel/gpt-5.5')
t=time.time()
p=subprocess.run(['hermes','chat','-Q','--provider','freemodel','-m','gpt-5.5','-q',prompt,'--max-turns','20','--source','kewu-ch270-freemodel-editor'],cwd='/root/workspace',text=True,capture_output=True,timeout=1600)
dur=round(time.time()-t,2)
out=(p.stdout or '').strip(); err=(p.stderr or '').strip()
(RAW/'editor_stdout.md').write_text(out,encoding='utf-8')
(RAW/'editor_stderr.txt').write_text(err,encoding='utf-8')
v=verdict(out) if p.returncode==0 else 'ERROR'
status='PASS' if v=='PASS' else ('FAILED' if v in ('FAIL','ERROR') else 'UNKNOWN')
REPORT.write_text(f'''# 第270章 freemodel GPT-5.5 编辑补审 v2

时间：{datetime.now().isoformat(timespec='seconds')}
路由：freemodel / gpt-5.5
exit_code：{p.returncode}
duration：{dur}s
结论：{v}
候选稿：`{CAND}`
raw：`{RAW}`

## stdout
{out}

## stderr
```text
{err}
```
''',encoding='utf-8')
emit('FREEMODEL_EDITOR_DONE',status=status,msg=f'editor={v}',duration=dur,report_path=str(REPORT))
print(json.dumps({'editor':v,'report':str(REPORT),'duration':dur,'exit_code':p.returncode},ensure_ascii=False))
