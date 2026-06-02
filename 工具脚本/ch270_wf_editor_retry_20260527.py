#!/usr/bin/env python3
import json, re, subprocess, time
from datetime import datetime
from pathlib import Path
ROOT=Path('/root/workspace/科武纪元')
OUT=ROOT/'审核记录/六角色外审'
RAW=OUT/'raw/ch270_wf_editor_retry_20260527'
RAW.mkdir(parents=True, exist_ok=True)
EVENTS=ROOT/'审核记录/新卷写作队列/events_270_wf_editor_retry_20260527.jsonl'
CAND=OUT/'第270章_MiMoPro修订候选_v2_20260527.md'
REPORT=OUT/'第270章_WF编辑补审_v2_20260527.md'

def emit(event,status='RUNNING',msg='',**kw):
    rec={'ts':datetime.now().isoformat(timespec='seconds'),'chapter':270,'event':event,'status':status,'msg':msg}|kw
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    EVENTS.open('a',encoding='utf-8').write(json.dumps(rec,ensure_ascii=False)+'\n')

def verdict(text):
    head=text[:1800]
    if re.search(r'结论[:：]\s*FAIL|\bFAIL\b|不通过|必须回炉',head,re.I): return 'FAIL'
    if re.search(r'结论[:：]\s*PASS|\bPASS\b|通过',head,re.I): return 'PASS'
    return 'UNKNOWN'

chapter=CAND.read_text(encoding='utf-8')
prompt=f'''你是《科武纪元》WF编辑复审。只审第270章MiMo修订候选。
首行必须写：结论：PASS 或 结论：FAIL。
若FAIL，只列必改≤3。

复审重点：
1. 全文引号是否统一为中文弯引号。
2. 震动链是否补齐3分20秒，不再从4分40跳到2分40。
3. 方宁是否有三档制冷承压动作，不再只是报数机。
4. 数值链/人线/格式是否仍有硬伤。

【正文】
{chapter}
'''
emit('WF_EDITOR_RETRY_START',msg='custom:WF/claude-opus-4-7-high-fast')
t=time.time()
p=subprocess.run(['hermes','chat','-Q','--provider','custom:WF','-m','claude-opus-4-7-high-fast','-q',prompt,'--max-turns','20','--source','kewu-ch270-wf-editor-retry'],cwd='/root/workspace',text=True,capture_output=True,timeout=1400)
dur=round(time.time()-t,2)
out=(p.stdout or '').strip(); err=(p.stderr or '').strip()
(RAW/'editor_stdout.md').write_text(out,encoding='utf-8')
(RAW/'editor_stderr.txt').write_text(err,encoding='utf-8')
v=verdict(out) if p.returncode==0 else 'ERROR'
status='PASS' if v=='PASS' else ('FAILED' if v in ('FAIL','ERROR') else 'UNKNOWN')
REPORT.write_text(f'''# 第270章 WF编辑补审 v2

时间：{datetime.now().isoformat(timespec='seconds')}
路由：custom:WF / claude-opus-4-7-high-fast
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
emit('WF_EDITOR_RETRY_DONE',status=status,msg=f'editor={v}',duration=dur,report_path=str(REPORT))
print(json.dumps({'editor':v,'report':str(REPORT),'duration':dur,'exit_code':p.returncode},ensure_ascii=False))
