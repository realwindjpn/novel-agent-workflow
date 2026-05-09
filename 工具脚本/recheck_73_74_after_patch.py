#!/usr/bin/env python3
from pathlib import Path
import json, re, subprocess, datetime
BASE=Path('/root/workspace/科武纪元')
SCRIPT=BASE/'工具脚本/orchestrate_review.py'
RAW=BASE/'审核记录/六角色外审/raw'
RAW.mkdir(parents=True,exist_ok=True)
NEG=['FAIL','REVIEW_NEEDED','必改','硬伤','不宜进入','不能进入','重修','重写','不通过']
POS=['PASS','通过','可上传','可以上传','想继续看','能进入下一章']
def fanqie(text):
    lines=[x for x in text.splitlines() if x.strip()]
    title=lines[0] if lines else ''
    return len(re.sub(r'\s+','',text))-len(re.sub(r'\s+','',title))
def judge(c):
    s=re.sub(r'<think>.*?</think>','',c or '', flags=re.S).strip()
    if any(x in s for x in NEG): return 'FAIL'
    if s.splitlines() and s.splitlines()[0].strip().startswith('PASS'): return 'PASS'
    if any(x in s for x in POS): return 'PASS'
    return 'UNKNOWN'
def ev(ch):
    subprocess.run(['python3',str(BASE/'工具脚本/build_review_evidence.py'),str(ch)],check=True,cwd='/root/workspace')
    txt=(BASE/'审核记录/证据包'/f'第{ch}章_证据包.md').read_text(encoding='utf-8')
    parts=[]
    for marker in ['## 本地预检','## 任务卡摘录','## 尾段行号','## 证据地图：章末钩子','## 证据地图：技术动作','## 证据地图：投稿风险']:
        i=txt.find(marker)
        if i>=0:
            j=txt.find('\n## ', i+4)
            if j<0: j=len(txt)
            parts.append(txt[i:j])
    return '\n\n'.join(parts)[:2600]
def call(role,ch,prompt):
    p=subprocess.run(['python3',str(SCRIPT),'--role',role,'--chapter',str(ch),'--prompt',prompt],capture_output=True,text=True,timeout=260,cwd='/root/workspace')
    try: d=json.loads(p.stdout)
    except Exception: d={'role':role,'ok':False,'content':p.stdout[-1000:]+p.stderr[-1000:]}
    d['judgement']=judge(d.get('content','')) if d.get('ok') else 'FAIL'
    raw=RAW/f'第{ch}_{role}_upload_recheck_after_patch_{int(datetime.datetime.now().timestamp())}.json'
    raw.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    return d, raw
summary=[]
for ch, roles in [(73,[('science','科学顾问','复核已补哈希/矿物指纹/卫星灾备接管箱后，技术硬伤是否清除')]),(74,[('reader','读者','复核已压缩章末论文腔并补动作后，是否顺/爽/想看下一章')])]:
    file=BASE/'新版'/f'第{ch}章.md'
    text=file.read_text(encoding='utf-8')
    lines=[x for x in text.splitlines() if x.strip()]
    evidence=ev(ch)
    fq=fanqie(text)
    res=[]
    for role,zh,focus in roles:
        prompt=f'''角色:{zh}
任务:第{ch}章上传前定向复审。只审核，不改文。
关注:{focus}
硬格式:第一行只写 PASS 或 FAIL。若仍有必改/硬伤/不宜上传，第一行必须 FAIL。第二行起理由≤3条。
本地硬检: 番茄口径{fq}; 首行{lines[0]}; 末行{lines[-1]}
RTK证据包摘录:
{evidence}
'''
        d,raw=call(role,ch,prompt)
        res.append({'role':role,'zh':zh,'ok':d.get('ok'),'provider':d.get('provider'),'model':d.get('model'),'judgement':d.get('judgement'),'raw':str(raw)})
    summary.append({'chapter':ch,'fanqie_count':fq,'title':lines[0],'last':lines[-1],'roles':res})
out=BASE/'审核记录/六角色外审/上传前复审_73_74_修后复审_20260508.json'
out.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
# append records
for item in summary:
    ch=item['chapter']; rec=BASE/'审核记录/六角色外审'/f'第{ch}章.md'
    old=rec.read_text(encoding='utf-8')
    final='PASS' if all(r['ok'] and r['judgement']=='PASS' for r in item['roles']) else 'FAIL'
    block=['','## 上传前定向修后复审（2026-05-08）',f'- 番茄口径字数：{item["fanqie_count"]}',f'- 首行：{item["title"]}',f'- 末行：{item["last"]}']
    for r in item['roles']:
        block.append(f'- {r["zh"]}：{r["provider"]}/{r["model"]} ok={r["ok"]} 结论={r["judgement"]} raw={Path(r["raw"]).name}')
    block+=['', '## 上传前修后结论', final]
    rec.write_text(old.rstrip()+'\n'+'\n'.join(block)+'\n',encoding='utf-8')
print(json.dumps({'summary':summary,'summary_file':str(out)},ensure_ascii=False,indent=2))
