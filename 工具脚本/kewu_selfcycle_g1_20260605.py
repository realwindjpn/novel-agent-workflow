import json, os, re, glob, datetime
from collections import Counter
base='/root/workspace/科武纪元'
aud=base+'/审核记录'
outdir=aud+'/自循环体系会议_20260605'
os.makedirs(outdir, exist_ok=True)
paths=[
 aud+'/mirofish_weekly_supplemental_decision_cards_20260605.json',
 aud+'/mirofish_quantum_recollection_decision_card_20260605.json',
 aud+'/mirofish_second_feed_decision_cards_20260605.json'
]
allcards=[]
for p in paths:
    if os.path.exists(p):
        txt=open(p,'r',encoding='utf-8').read()
        try:
            data=json.loads(txt)
        except Exception:
            data=[]
        if isinstance(data, dict):
            for k in ['cards','decision_cards','items','data']:
                if isinstance(data.get(k), list):
                    data=data[k]
                    break
            else:
                data=[data]
        if isinstance(data, list):
            for c in data:
                if isinstance(c, dict):
                    c['_source_file']=p
                    allcards.append(c)

def pick(c,*keys):
    for k in keys:
        v=c.get(k)
        if v not in (None,'',[]): return v
    return ''

def disp(c):
    blob=json.dumps(c,ensure_ascii=False)
    for tag in ['OUTLINE_PATCH','CHAPTER_PREP_ONLY','ARCHIVE_WITH_REASON','NEED_SOURCE_UPGRADE','NO_ACTION']:
        if tag in blob: return tag
    s=str(pick(c,'decision','status','disposition','action','route','裁决','处置'))
    return s or 'UNKNOWN'

rows=[]
for i,c in enumerate(allcards,1):
    title=pick(c,'title','material_title','素材','主题','name','card_title') or f'card_{i}'
    decision=disp(c)
    src=pick(c,'source_url','url','source','来源')
    chapter=pick(c,'chapter','target_chapter','章节','mapping','小说映射','kewu_mapping')
    rows.append({'id':i,'title':str(title),'decision':decision,'chapter':str(chapter),'url':str(src),'source_file':c['_source_file']})
seen=set(); ded=[]
for r in rows:
    key=(r['title'],r['decision'],r['url'])
    if key not in seen:
        seen.add(key); ded.append(r)
rows=ded
cnt=Counter(r['decision'] for r in rows)
nums=[]
for p in glob.glob(base+'/已投稿/第*.txt'):
    m=re.search(r'第(\d+)章', os.path.basename(p))
    if m: nums.append(int(m.group(1)))
maxn=max(nums) if nums else None
upload=[maxn+1,maxn+2] if maxn else []
chapinfo=[]
for n in upload:
    md=base+f'/新版/第{n}章.md'
    exists=os.path.exists(md)
    chars=None; title=''
    if exists:
        txt=open(md,'r',encoding='utf-8',errors='ignore').read()
        lines=[x.strip() for x in txt.splitlines() if x.strip()]
        title=lines[0] if lines else ''
        plain=re.sub(r'\s+','',txt)
        titlechars=len(re.sub(r'\s+','',title))
        chars=len(plain)-titlechars
    chapinfo.append({'chapter':n,'path':md,'exists':exists,'title':title,'fanqie_chars':chars})
md=[]
md.append('# 2026-06-05 MiroFish→科武自循环 G1 处置表\n\n')
md.append('## 结论\n\n')
md.append(f'- 合并决策卡：{len(rows)} 张\n')
md.append(f'- 处置统计：{dict(cnt)}\n')
md.append(f'- 已投稿最大章：第{maxn}章\n')
if upload:
    md.append(f'- 今日上传线锁定：第{upload[0]}章、第{upload[1]}章\n')
else:
    md.append('- 今日上传线锁定：失败\n')
md.append('\n## 上传线源稿门禁\n\n')
md.append('|章|源稿|标题|番茄口径|\n|---|---|---|---|\n')
for ci in chapinfo:
    md.append(f"|{ci['chapter']}|{'PASS' if ci['exists'] else 'MISSING'}|{ci['title']}|{ci['fanqie_chars']}|\n")
md.append('\n## MiroFish三态处置\n\n')
md.append('|ID|素材|处置|章节/映射|URL|\n|---|---|---|---|---|\n')
for r in rows:
    md.append(f"|{r['id']}|{r['title'][:80]}|{r['decision']}|{r['chapter'][:80]}|{r['url'][:80]}|\n")
report=''.join(md)
open(outdir+'/G1_mirofish_disposition_20260605.md','w',encoding='utf-8').write(report)
state={
 'date':'2026-06-05',
 'status':'G1_DONE_G2_READY',
 'current_phase':'G1',
 'upload_line':upload,
 'max_submitted_chapter':maxn,
 'decision_counts':dict(cnt),
 'cards_total':len(rows),
 'artifacts':{'g1_disposition':outdir+'/G1_mirofish_disposition_20260605.md'},
 'next_action':'start_G2_multimodel_council',
}
open(outdir+'/selfcycle_state.json','w',encoding='utf-8').write(json.dumps(state,ensure_ascii=False,indent=2))
inbox='/root/workspace/agent_inbox/kewu_selfcycle_20260605.jsonl'
os.makedirs(os.path.dirname(inbox), exist_ok=True)
with open(inbox,'a',encoding='utf-8') as f:
    f.write(json.dumps({'ts':datetime.datetime.now().isoformat(),'event':'G1_DONE_G2_READY','state_path':outdir+'/selfcycle_state.json','report_path':outdir+'/G1_mirofish_disposition_20260605.md'},ensure_ascii=False)+'\n')
print(json.dumps({'status':'G1_DONE_G2_READY','rows':len(rows),'counts':dict(cnt),'upload':upload,'report':outdir+'/G1_mirofish_disposition_20260605.md'},ensure_ascii=False,indent=2))
