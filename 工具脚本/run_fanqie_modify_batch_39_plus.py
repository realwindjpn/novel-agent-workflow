#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path

CHAPTERS = [39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,55,68]
BASE = Path('/root/workspace/科武纪元')
LOG_DIR = BASE / '审核记录' / '番茄旧章批量修改_20260510_从39'
LOG_DIR.mkdir(parents=True, exist_ok=True)
SCRIPT = BASE / '工具脚本' / 'fanqie_modify_uploaded_chapter.py'
summary=[]

for ch in CHAPTERS:
    item={'chapter': ch, 'status': 'started'}
    log_path = LOG_DIR / f'第{ch}章.log'
    cmd = ['python3', str(SCRIPT), '--chapter', str(ch), '--session', 'fanqie', '--execute']
    t0=time.time()
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=360)
    out=p.stdout
    log_path.write_text(out, encoding='utf-8')
    item['seconds']=round(time.time()-t0,1)
    item['log']=str(log_path)
    item['exit_code']=p.returncode
    if p.returncode != 0:
        item['status']='failed'
        item['tail']='\n'.join(out.splitlines()[-30:])
        summary.append(item)
        break
    # parse last JSON block loosely
    item['status']='submitted'
    if '修改审核中' in out:
        item['verify']='修改审核中'
    elif '已发布' in out:
        item['verify']='已发布/快速过审'
    else:
        item['verify']='unknown_check_log'
    if '超过上传发布字数限制' in out or ('字数限制' in out and 'RuntimeError' in out):
        item['status']='limit_stop'
        summary.append(item)
        break
    summary.append(item)
    print(json.dumps({'chapter': ch, 'status': item['status'], 'verify': item['verify'], 'seconds': item['seconds']}, ensure_ascii=False), flush=True)
    time.sleep(1.5)

summary_path=LOG_DIR/'summary.json'
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
md=[]
md.append('# 番茄旧章批量修改记录｜从第39章继续')
md.append('')
md.append(f'- 日志目录：`{LOG_DIR}`')
md.append('')
md.append('|章|状态|复核|耗时|日志|')
md.append('|---:|---|---|---:|---|')
for it in summary:
    md.append(f"|{it['chapter']}|{it.get('status','')}|{it.get('verify','')}|{it.get('seconds','')}|`{it.get('log','')}`|")
if summary and summary[-1].get('status')=='failed':
    md.append('')
    md.append('## 停止原因')
    md.append('```text')
    md.append(summary[-1].get('tail',''))
    md.append('```')
md_path=LOG_DIR/'summary.md'
md_path.write_text('\n'.join(md), encoding='utf-8')
print(json.dumps({'summary': str(summary_path), 'report': str(md_path), 'last': summary[-1] if summary else None}, ensure_ascii=False, indent=2))
if summary and summary[-1].get('status')=='failed':
    sys.exit(1)
