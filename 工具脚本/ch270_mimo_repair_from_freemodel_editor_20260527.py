#!/usr/bin/env python3
import json, re, subprocess, time
from datetime import datetime
from pathlib import Path
ROOT=Path('/root/workspace/科武纪元')
OUT=ROOT/'审核记录/六角色外审'
RAW=OUT/'raw/ch270_mimo_repair_v3_from_freemodel_20260527'
RAW.mkdir(parents=True, exist_ok=True)
EVENTS=ROOT/'审核记录/新卷写作队列/events_270_mimo_repair_v3_from_freemodel_20260527.jsonl'
SRC=OUT/'第270章_MiMoPro修订候选_v2_20260527.md'
FREEREP=OUT/'第270章_freemodel_GPT55编辑补审_v2_20260527.md'
CAND=OUT/'第270章_MiMoPro修订候选_v3_20260527.md'
REPORT=OUT/'第270章_MiMoPro修订复审报告_v3_20260527.md'
ROUTES={
 'repair':('xiaomi','mimo-v2.5-pro'),
 'editor':('freemodel','gpt-5.5'),
 'reader':('alibaba','qwen3.6-plus'),
 'advisor':('zai','glm-5.1'),
}
BAD=['微微','意味着','仿佛','像是某种','命运','史诗','灵魂','本段完','omitted','truncated','diff --git','```']
def emit(event,status='RUNNING',msg='',**kw):
 rec={'ts':datetime.now().isoformat(timespec='seconds'),'chapter':270,'event':event,'status':status,'msg':msg}|kw
 EVENTS.parent.mkdir(parents=True, exist_ok=True)
 EVENTS.open('a',encoding='utf-8').write(json.dumps(rec,ensure_ascii=False)+'\n')
def fanqie_count(t):
 lines=t.strip().splitlines(); title=lines[0] if lines else ''
 return len(re.sub(r'\s+','',t))-len(re.sub(r'\s+','',title))
def straight_count(t):
 return t.count('"')+t.count("'")
def run(role,prompt,timeout=1600):
 pvd,model=ROUTES[role]
 emit(role.upper()+'_START',msg=f'{pvd}/{model}')
 st=time.time()
 p=subprocess.run(['hermes','chat','-Q','--provider',pvd,'-m',model,'-q',prompt,'--max-turns','25','--source','kewu-ch270-repair-v3'],cwd='/root/workspace',text=True,capture_output=True,timeout=timeout)
 dur=round(time.time()-st,2)
 out=(p.stdout or '').strip(); err=(p.stderr or '').strip()
 (RAW/f'{role}_stdout.md').write_text(out,encoding='utf-8')
 (RAW/f'{role}_stderr.txt').write_text(err,encoding='utf-8')
 emit(role.upper()+'_DONE' if p.returncode==0 else role.upper()+'_FAIL',status='RUNNING' if p.returncode==0 else 'FAILED',msg=f'exit={p.returncode} dur={dur}',provider=pvd,model=model,duration=dur)
 return p.returncode,out,err,dur,pvd,model
def extract(text):
 m=re.search(r'(第270章[\s\S]+?（本章完）)',text)
 return m.group(1).strip() if m else text.strip()
def verdict(text):
 head=text[:1800]
 if re.search(r'结论[:：]\s*FAIL|\bFAIL\b|不通过|必须回炉',head,re.I): return 'FAIL'
 if re.search(r'结论[:：]\s*PASS|\bPASS\b|通过',head,re.I): return 'PASS'
 return 'UNKNOWN'
emit('INIT',msg='repair freemodel editor fail with mimo-v2.5-pro')
src=SRC.read_text(encoding='utf-8')
frep=FREEREP.read_text(encoding='utf-8')
prompt=f'''你是《科武纪元》作者模型：xiaomi/mimo-v2.5-pro。
任务：按freemodel GPT-5.5编辑补审FAIL项，定点清洁第270章v2候选稿。不得改剧情，不得扩写后续。

硬要求：
1. 删除所有前置验证段、代码噪声、说明文字，只保留小说正文。
2. 全文半角直引号必须为0：不得出现 " 或 '。对话统一使用中文弯引号“”。
3. 保留上一轮已通过修订：三分二十秒震动档、方宁“判断—迟疑—反向确认—执行”承压链、三证据链、章末第四条目的钩子。
4. 清洁正文：无Markdown、无diff、无omitted/truncated、无代码块、无作者说明。末尾保留（本章完）。
5. 番茄口径≥3000。

【freemodel编辑补审报告】
{frep}

【待修v2候选稿】
{src}

只输出修订后的完整正文，从“第270章 第三次校验”开始，到“（本章完）”结束。
'''
code,out,err,dur,pvd,model=run('repair',prompt,timeout=2200)
if code!=0:
 REPORT.write_text(f'# 第270章MiMo修订复审报告v3\n\n结论：REPAIR_FAIL\n\n```text\n{err[-3000:]}\n```\n',encoding='utf-8')
 emit('BLOCKED',status='FAILED',msg='repair model failed',report_path=str(REPORT))
 raise SystemExit(1)
chapter=extract(out)
# deterministic cleanup for obvious model wrappers only
chapter=re.sub(r'^```[a-zA-Z]*\n|\n```$','',chapter.strip())
CAND.write_text(chapter,encoding='utf-8')
fc=fanqie_count(chapter); straight=straight_count(chapter); bans=[b for b in BAD if b in chapter]; bad_end=not chapter.endswith('（本章完）')
machine=(fc>=3000 and straight==0 and not bans and not bad_end)
emit('MACHINE_GATE',status='RUNNING' if machine else 'FAILED',msg='PASS' if machine else 'FAIL',fanqie_count=fc,straight=straight,bans=bans,bad_end=bad_end)
review=f'''复审《科武纪元》第270章MiMo v3修订稿。首行必须写：结论：PASS/FAIL。若FAIL，只列必改≤3。
重点：半角直引号是否为0；是否无前置验证段/代码噪声；是否保留三分二十秒、方宁承压链、三证据链、第四条目的钩子；格式/数值链/人物是否有硬伤。

【修订稿】
{chapter}
'''
_,ed,_,ed_dur,ed_p,ed_m=run('editor','你是编辑。'+review,timeout=1500)
_,rd,_,rd_dur,rd_p,rd_m=run('reader','你是普通追读读者。'+review,timeout=1200)
_,ad,_,ad_dur,ad_p,ad_m=run('advisor','你是科学+军事顾问。'+review,timeout=1200)
ve,vr,va=verdict(ed),verdict(rd),verdict(ad)
final='FULL_LOOP_PASS_CANDIDATE' if machine and ve==vr==va=='PASS' else 'REVIEW_FAIL'
REPORT.write_text(f'''# 第270章 MiMoPro修订复审报告 v3

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
- 半角直引号数：{straight}
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
emit('DONE' if final.endswith('CANDIDATE') else 'REVIEW_FAIL',status=final,msg=final,fanqie_count=fc,straight=straight,report_path=str(REPORT),candidate_path=str(CAND),editor=ve,reader=vr,advisor=va)
print(json.dumps({'final':final,'candidate':str(CAND),'report':str(REPORT),'fanqie_count':fc,'straight':straight,'editor':ve,'reader':vr,'advisor':va},ensure_ascii=False))
