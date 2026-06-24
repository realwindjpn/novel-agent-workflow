from pathlib import Path
import re, json, datetime
root=Path('/root/workspace/科武纪元')
outdir=root/'审核记录'
outdir.mkdir(exist_ok=True)
today=datetime.datetime.now().strftime('%Y%m%d_%H%M')
internal_patterns=[r'第[一二三四五六七八九十0-9]+卷终章', r'卷[一二三四五六七八九十0-9]+终章', r'终章$', r'上传线', r'准备包', r'G[0-9]+', r'OUTLINE', r'PATCH', r'NOTE_ONLY', r'CHAPTER_PREP', r'内部', r'流程']

def norm_title(s):
    s=s.strip().lstrip('\ufeff')
    s=re.sub(r'^#{1,6}\s*','',s).strip()
    s=re.sub(r'^(第\s*[0-9一二三四五六七八九十百]+\s*章\s*[：:、.\-— ]*)','',s).strip()
    s=s.strip('《》「」“”[]【】 ')
    return s

def chapnum(p):
    m=re.search(r'第\s*(\d+)\s*章', p.name)
    if m: return int(m.group(1))
    m=re.search(r'ch(\d+)', p.stem)
    if m: return int(m.group(1))
    return None

sources=[]
for p in sorted((root/'新版').glob('第*章*.md')):
    n=chapnum(p)
    try: lines=p.read_text(encoding='utf-8', errors='ignore').splitlines()
    except Exception: continue
    first=next((x for x in lines if x.strip()), '')
    title=norm_title(first)
    if n and title: sources.append({'source':'新版','chapter':n,'title':title,'raw':first,'path':str(p)})
for p in sorted((root/'已投稿').glob('第*章*.txt')):
    n=chapnum(p)
    try: lines=p.read_text(encoding='utf-8', errors='ignore').splitlines()
    except Exception: continue
    first=next((x for x in lines if x.strip()), '')
    title=norm_title(first)
    if n and title: sources.append({'source':'已投稿','chapter':n,'title':title,'raw':first,'path':str(p)})
for p in sorted((root/'wiki'/'chapters').glob('ch*.md')):
    n=chapnum(p)
    try: txt=p.read_text(encoding='utf-8', errors='ignore')
    except Exception: continue
    title=''
    for line in txt.splitlines()[:80]:
        if line.startswith('title:'):
            title=norm_title(line.split(':',1)[1].strip().strip('"\'')); break
    if not title:
        first=next((x for x in txt.splitlines() if x.strip().startswith('#')), '')
        title=norm_title(first)
    if n and title: sources.append({'source':'wiki','chapter':n,'title':title,'raw':title,'path':str(p)})
outline=root/'wiki'/'raw'/'outline'/'科武纪元大纲_latest.md'
if outline.exists():
    txt=outline.read_text(encoding='utf-8', errors='ignore')
    for i,line in enumerate(txt.splitlines(),1):
        m=re.search(r'第\s*(\d+)\s*章[：:、\s-]*(.+)', line)
        if m:
            n=int(m.group(1)); rest=m.group(2).strip()
            t=re.split(r'[。；;]|\s{2,}|（|\(|【', rest, 1)[0].strip()
            t=norm_title(t)
            if t: sources.append({'source':'大纲','chapter':n,'title':t,'raw':line.strip(),'path':str(outline)+f':{i}'})
track=root/'小说综合跟踪表.md'
if track.exists():
    for i,line in enumerate(track.read_text(encoding='utf-8', errors='ignore').splitlines(),1):
        m=re.search(r'第\s*(\d+)\s*章[^|\n]*[|｜]\s*([^|｜]+)', line)
        if m:
            n=int(m.group(1)); t=norm_title(m.group(2))
            if t and not t.startswith('状态'):
                sources.append({'source':'跟踪表','chapter':n,'title':t,'raw':line.strip(),'path':str(track)+f':{i}'})
by_ch={}
for r in sources: by_ch.setdefault(r['chapter'], []).append(r)
chapter_incons=[]
for ch, rs in sorted(by_ch.items()):
    titles=sorted(set(r['title'] for r in rs))
    if len(titles)>1: chapter_incons.append({'chapter':ch,'titles':titles,'items':rs})
by_title={}; seen=set()
for r in sources:
    key=(r['source'],r['chapter'],r['title'])
    if key in seen: continue
    seen.add(key)
    by_title.setdefault(r['title'], []).append(r)
dups=[]
for title, rs in sorted(by_title.items(), key=lambda kv:(len(set(r['chapter'] for r in kv[1])), kv[0]), reverse=True):
    chs=sorted(set(r['chapter'] for r in rs))
    if len(chs)>1: dups.append({'title':title,'chapters':chs,'items':rs})
internal=[]
for r in sources:
    if any(re.search(pat, r['title'], re.I) or re.search(pat, r['raw'], re.I) for pat in internal_patterns): internal.append(r)
report=[]
report.append('# 科武纪元章节标题全量审计（只读）\n')
report.append(f'- 生成时间：{today}')
report.append(f'- 扫描记录数：{len(sources)}')
report.append(f'- 重复标题组：{len(dups)}')
report.append(f'- 内部流程名命中：{len(internal)}')
report.append(f'- 同章多源标题不一致：{len(chapter_incons)}\n')
report.append('## 一、重复标题组\n')
for d in dups:
    report.append(f'### {d["title"]} → 章节 {", ".join(map(str,d["chapters"]))}')
    for it in d['items'][:20]: report.append(f'- 第{it["chapter"]}章｜{it["source"]}｜`{it["path"]}`｜raw: {it["raw"][:120]}')
    report.append('')
report.append('## 二、内部流程名/不宜外显标题命中\n')
for it in internal: report.append(f'- 第{it["chapter"]}章｜{it["source"]}｜标题：{it["title"]}｜`{it["path"]}`')
report.append('\n## 三、同章多源标题不一致\n')
for c in chapter_incons[:120]:
    report.append(f'### 第{c["chapter"]}章：{c["titles"]}')
    for it in c['items'][:10]: report.append(f'- {it["source"]}: {it["title"]}｜`{it["path"]}`')
    report.append('')
json_path=outdir/f'章节标题问题清单_{today}.json'
md_path=outdir/f'章节标题去重审计_{today}.md'
json_path.write_text(json.dumps({'generated_at':today,'sources_count':len(sources),'duplicates':dups,'internal_name_hits':internal,'chapter_inconsistencies':chapter_incons}, ensure_ascii=False, indent=2), encoding='utf-8')
md_path.write_text('\n'.join(report), encoding='utf-8')
summary={'json':str(json_path),'md':str(md_path),'sources':len(sources),'duplicate_groups':len(dups),'internal_hits':len(internal),'chapter_inconsistencies':len(chapter_incons),'top_duplicates':[(d['title'],d['chapters']) for d in dups[:25]]}
print(json.dumps(summary, ensure_ascii=False, indent=2))
