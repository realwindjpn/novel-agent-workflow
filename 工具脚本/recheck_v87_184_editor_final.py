#!/usr/bin/env python3
import json,re,subprocess,time
from pathlib import Path
from datetime import datetime
BASE=Path('/root/workspace/科武纪元'); ORCH=BASE/'工具脚本/orchestrate_review.py'; EVID=BASE/'工具脚本/build_review_evidence.py'; RAW=BASE/'审核记录/六角色外审/raw'; REC=BASE/'审核记录/六角色外审'
subprocess.run(['python3',str(EVID),'184'],check=False,capture_output=True,text=True)
text=(BASE/'审核记录/证据包/第184章_证据包.md').read_text(encoding='utf-8',errors='ignore')
# include specific fixed lines and full tail to avoid truncation false fail
chapter=(BASE/'新版/第184章.md').read_text(encoding='utf-8',errors='ignore').splitlines()
seg='\n'.join(f'{i}|{chapter[i-1]}' for i in range(161,182))
tail='\n'.join(f'{i}|{chapter[i-1]}' for i in range(max(1,len(chapter)-35),len(chapter)+1))
prompt=f'''只做最终复审，不续写，不改文。
对象:《科武纪元》第184章V8.7修复稿。
此前编辑FAIL两点：1 尾段未完整；2 仍有“死循环”。
现只核对：是否仍有硬伤。第一行只写 PASS 或 FAIL。若仍有硬伤/必改，第一行必须 FAIL。理由≤3条。

## 修复段161-181
{seg}

## 完整尾段
{tail}
'''
rc=subprocess.run(['python3',str(ORCH),'--role','editor','--chapter','184','--prompt',prompt],text=True,capture_output=True,timeout=260)
try: data=json.loads(rc.stdout)
except Exception as e: data={'role':'editor','ok':False,'content':f'parse {e}: {rc.stdout[:500]} {rc.stderr[:200]}'}
ts=datetime.now().strftime('%Y%m%d_%H%M%S')
raw=RAW/f'第184_editor_v87_final_recheck_{ts}.json'; raw.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
s=re.sub(r'<think>.*?</think>','',data.get('content',''),flags=re.S); head=' '.join([x.strip() for x in s.splitlines() if x.strip()][:4]).upper()
ver='FAIL' if any(w in head for w in ['FAIL','硬伤','必改','不通过']) else ('PASS' if any(w in head for w in ['PASS','通过','无硬伤']) else 'UNKNOWN')
rec=REC/'第184章.md'; old=rec.read_text(encoding='utf-8',errors='ignore') if rec.exists() else '# 第184章 六角色外审记录\n'
md=f'''\n## V8.7第184章编辑最终复审 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

|角色|provider/model|ok|结论|raw|
|---|---|---|---|---|
|editor|{data.get('provider','?')}/{data.get('model','?')}|{data.get('ok',False)}|{ver}|{raw}|

## V8.7第184章最终复审结论
{ver}
'''
rec.write_text(old.rstrip()+md,encoding='utf-8')
out={'chapter':184,'final':ver,'raw':str(raw),'record':str(rec),'content':data.get('content','')[:500]}
print(json.dumps(out,ensure_ascii=False,indent=2))
