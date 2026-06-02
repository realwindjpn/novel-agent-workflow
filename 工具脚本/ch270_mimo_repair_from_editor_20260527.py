#!/usr/bin/env python3
import json, re, subprocess, time
from datetime import datetime
from pathlib import Path

ROOT=Path('/root/workspace/科武纪元')
OUT=ROOT/'审核记录/六角色外审'
RAW=OUT/'raw/ch270_mimo_repair_v2_20260527'
RAW.mkdir(parents=True, exist_ok=True)
EVENTS=ROOT/'审核记录/新卷写作队列/events_270_mimo_repair_v2_20260527.jsonl'
SRC=OUT/'第270章_MiMoPro重写候选_20260527.md'
REPORT1=OUT/'第270章_MiMoPro六角色重写报告_20260527.md'
CAND=OUT/'第270章_MiMoPro修订候选_v2_20260527.md'
REPORT=OUT/'第270章_MiMoPro修订复审报告_v2_20260527.md'

ROUTES={
 'repair':('xiaomi','mimo-v2.5-pro'),
 'editor':('custom:WF','claude-opus-4-7-high-fast'),
 'reader':('alibaba','qwen3.6-plus'),
 'advisor':('zai','glm-5.1'),
}
BAD=['微微','意味着','仿佛','像是某种','命运','史诗','灵魂','本段完','omitted','truncated','diff --git']

def emit(event,status='RUNNING',msg='',**kw):
    rec={'ts':datetime.now().isoformat(timespec='seconds'),'chapter':270,'event':event,'status':status,'msg':msg}|kw
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    EVENTS.open('a',encoding='utf-8').write(json.dumps(rec,ensure_ascii=False)+'\n')

def count(t):
    lines=t.strip().splitlines(); title=lines[0] if lines else ''
    return len(re.sub(r'\s+','',t))-len(re.sub(r'\s+','',title))

def run(role,prompt,timeout=1600):
    pvd,model=ROUTES[role]
    emit(role.upper()+'_START',msg=f'{pvd}/{model}')
    t=time.time()
    p=subprocess.run(['hermes','chat','-Q','--provider',pvd,'-m',model,'-q',prompt,'--max-turns','25','--source','kewu-ch270-repair'],cwd='/root/workspace',text=True,capture_output=True,timeout=timeout)
    dur=round(time.time()-t,2)
    out=(p.stdout or '').strip(); err=(p.stderr or '').strip()
    (RAW/f'{role}_stdout.md').write_text(out,encoding='utf-8')
    (RAW/f'{role}_stderr.txt').write_text(err,encoding='utf-8')
    emit(role.upper()+'_DONE' if p.returncode==0 else role.upper()+'_FAIL',status='RUNNING' if p.returncode==0 else 'FAILED',msg=f'exit={p.returncode} dur={dur}',provider=pvd,model=model,duration=dur)
    return p.returncode,out,err,dur,pvd,model

def extract(text):
    m=re.search(r'(第270章[\s\S]+?（本章完）)',text)
    return m.group(1).strip() if m else text.strip()

def verdict(text):
    head=text[:1500]
    if re.search(r'结论[:：]\s*FAIL|\bFAIL\b|不通过|必须回炉',head,re.I): return 'FAIL'
    if re.search(r'结论[:：]\s*PASS|\bPASS\b|通过',head,re.I): return 'PASS'
    return 'UNKNOWN'

emit('INIT',msg='repair editor fail with mimo-v2.5-pro')
old=SRC.read_text(encoding='utf-8')
rep=REPORT1.read_text(encoding='utf-8')

repair_prompt=f'''你是《科武纪元》作者模型：xiaomi/mimo-v2.5-pro。
任务：只根据编辑必改项，定点修订第270章候选稿。不要重写成另一版，不要扩展后续剧情。

硬要求：
1. 统一全章引号为中文全角弯引号“”。
2. 补齐震动数值链缺口：在摘要推送/签发/站起前后，明确补上“三分二十秒”一档，震级递增合理（如0.62），不得直接从4分40跳到2分40。
3. 加强方宁承压：三档制冷前让方宁出现“判断—迟疑—反向确认”的动作，例如机柜报警、她抬头问“开吗”，林星辰确认“开”。不要让她只报数。
4. 保留原稿优点：三证据链、数值链、章末“要求第四条——目的”钩子。
5. 清洁正文：无Markdown、无wikilink、无本段完、无diff/omitted/truncated。末尾保留（本章完）。
6. 番茄口径≥3000。

【编辑FAIL报告】
{rep[:6500]}

【待修候选稿】
{old}

只输出修订后的完整正文，从“第270章 第三次校验”开始，到“（本章完）”结束。
'''
code,out,err,dur,pvd,model=run('repair',repair_prompt,timeout=2200)
if code!=0:
    REPORT.write_text(f'# 第270章MiMo修订复审报告v2\n\n结论：REPAIR_FAIL\n\n{pvd}/{model}\n\n```\n{err[-2000:]}\n```\n',encoding='utf-8')
    emit('BLOCKED',status='FAILED',msg='repair model failed',report_path=str(REPORT))
    raise SystemExit(1)
chapter=extract(out)
CAND.write_text(chapter,encoding='utf-8')
fc=count(chapter); bans=[b for b in BAD if b in chapter]; bad_end=not chapter.endswith('（本章完）')
emit('MACHINE_GATE',status='RUNNING' if fc>=3000 and not bans and not bad_end else 'FAILED',msg='PASS' if fc>=3000 and not bans and not bad_end else 'FAIL',fanqie_count=fc,bans=bans,bad_end=bad_end)

review_base=f'''复审《科武纪元》第270章MiMo修订稿。首行必须写：结论：PASS/FAIL。若FAIL，只列必改≤3。
复审重点：原编辑三必改是否解决：引号统一、3分20秒震动缺口、方宁三档制冷承压动作。另查数值链、人物、人味、格式。

【修订稿】
{chapter}
'''
_,ed,_,ed_dur,ed_p,ed_m=run('editor','你是WF编辑。'+review_base,timeout=1400)
_,rd,_,rd_dur,rd_p,rd_m=run('reader','你是普通追读读者。'+review_base,timeout=1200)
_,ad,_,ad_dur,ad_p,ad_m=run('advisor','你是科学+军事顾问。'+review_base,timeout=1200)
ve,vr,va=verdict(ed),verdict(rd),verdict(ad)
final='FULL_LOOP_PASS_CANDIDATE' if fc>=3000 and not bans and not bad_end and ve==vr==va=='PASS' else 'REVIEW_FAIL'
REPORT.write_text(f'''# 第270章 MiMoPro修订复审报告 v2

时间：{datetime.now().isoformat(timespec='seconds')}
结论：{final}
边界：已生成修订候选；未覆盖正式 `新版/第270章.md`；未生成TXT；未上传；未commit。

## 路由
- 修订作者：{pvd}/{model}，duration={dur}s
- 编辑：{ed_p}/{ed_m}，duration={ed_dur}s，结论={ve}
- 读者：{rd_p}/{rd_m}，duration={rd_dur}s，结论={vr}
- 科学/军事顾问：{ad_p}/{ad_m}，duration={ad_dur}s，结论={va}

## 机器门禁
- 番茄口径：{fc}
- 禁词/坏标记：{bans}
- 末尾格式：{'PASS' if not bad_end else 'FAIL'}
- 修订稿：`{CAND}`
- raw目录：`{RAW}`

## 编辑复审
{ed}

## 读者复审
{rd}

## 科学/军事顾问复审
{ad}
''',encoding='utf-8')
emit('DONE' if final.endswith('CANDIDATE') else 'REVIEW_FAIL',status=final,msg=final,fanqie_count=fc,report_path=str(REPORT),candidate_path=str(CAND),editor=ve,reader=vr,advisor=va)
print(json.dumps({'final':final,'candidate':str(CAND),'report':str(REPORT),'fanqie_count':fc,'editor':ve,'reader':vr,'advisor':va},ensure_ascii=False))
