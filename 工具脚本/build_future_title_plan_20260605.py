from pathlib import Path
import re,json,datetime
root=Path('/root/workspace/科武纪元')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M')

def norm(s):
    s=s.strip().lstrip('\ufeff')
    s=re.sub(r'^#{1,6}\s*','',s).strip()
    s=re.sub(r'^第\s*\d+\s*章\s*[：:、.\-— ]*','',s).strip()
    return s.strip('《》「」“”[]【】 ')

def chnum(p):
    m=re.search(r'第\s*(\d+)\s*章',p.name)
    return int(m.group(1)) if m else None

# freeze written/uploaded titles from 新版 actual body + 已投稿.
freeze={}
for folder,kind in [('已投稿','uploaded'),('新版','written')]:
    for p in sorted((root/folder).glob('第*章*.txt' if folder=='已投稿' else '第*章*.md')):
        ch=chnum(p)
        if not ch: continue
        txt=p.read_text(encoding='utf-8',errors='ignore')
        lines=[x for x in txt.splitlines() if x.strip()]
        if not lines: continue
        # consider real written if length sufficient or uploaded
        if folder=='新版' and len(txt)<1500: continue
        title=norm(lines[0])
        if title:
            freeze.setdefault(ch, {'chapter':ch,'titles':{},'paths':[]})
            freeze[ch]['titles'][kind]=title
            freeze[ch]['paths'].append(str(p))
freeze_title_to_ch={}
for ch,info in freeze.items():
    # prefer uploaded title then written title
    t=info['titles'].get('uploaded') or info['titles'].get('written')
    if t: freeze_title_to_ch.setdefault(t,[]).append(ch)
# parse latest outline up to 500
outline=root/'wiki/raw/outline/科武纪元大纲_latest.md'
outline_items=[]
for i,line in enumerate(outline.read_text(encoding='utf-8',errors='ignore').splitlines(),1):
    m=re.search(r'第\s*(\d+)\s*章\s*\|',line)
    if not m: continue
    ch=int(m.group(1))
    if ch>500: continue
    parts=line.split('|')
    title=''
    if len(parts)>=4: title=norm(parts[3])
    else:
        m2=re.search(r'第\s*\d+\s*章[：:、\s-]+([^|｜（(【。；;\n]+)',line)
        title=norm(m2.group(1)) if m2 else ''
    if title:
        status='frozen_written' if ch in freeze else 'future_outline_only'
        outline_items.append({'chapter':ch,'title':title,'line':i,'raw':line,'status':status})
# conflicts: future title collides with frozen titles or earlier outline title
seen_outline={}
conflicts=[]
internal_pats=[r'第[一二三四五六七八九十0-9]+卷终章',r'卷[一二三四五六七八九十0-9]+终章',r'终章$',r'上传线',r'准备包',r'G[0-9]+',r'内部',r'流程']
for item in outline_items:
    ch=item['chapter']; t=item['title']
    if item['status']=='future_outline_only':
        if t in freeze_title_to_ch:
            conflicts.append({'type':'future_vs_frozen','chapter':ch,'title':t,'collides_with':freeze_title_to_ch[t],'line':item['line'],'raw':item['raw']})
        if t in seen_outline:
            prev=[x for x in seen_outline[t] if x<ch]
            if prev:
                conflicts.append({'type':'future_vs_outline_earlier','chapter':ch,'title':t,'collides_with':prev,'line':item['line'],'raw':item['raw']})
        if any(re.search(p,t,re.I) for p in internal_pats):
            conflicts.append({'type':'future_internal_name','chapter':ch,'title':t,'collides_with':[],'line':item['line'],'raw':item['raw']})
    seen_outline.setdefault(t,[]).append(ch)
# frozen duplicates only record, do not change
frozen_duplicates=[]
for t,chs in sorted(freeze_title_to_ch.items()):
    if len(chs)>1: frozen_duplicates.append({'title':t,'chapters':chs,'action':'record_only_do_not_change_written'})
# write json/md
outdir=root/'审核记录'
freeze_path=outdir/f'章节标题冻结库_{stamp}.json'
plan_json=outdir/f'500章大纲未来标题冲突_{stamp}.json'
md_path=outdir/f'500章大纲标题去重方案_{stamp}.md'
freeze_path.write_text(json.dumps({'generated_at':stamp,'freeze':list(freeze.values()),'title_to_chapters':freeze_title_to_ch,'frozen_duplicates':frozen_duplicates},ensure_ascii=False,indent=2),encoding='utf-8')
plan_json.write_text(json.dumps({'generated_at':stamp,'outline_count':len(outline_items),'future_conflicts':conflicts,'frozen_duplicates_record_only':frozen_duplicates},ensure_ascii=False,indent=2),encoding='utf-8')
md=[]
md.append(f'# 500章大纲标题去重方案（只读）\n')
md.append(f'- 生成时间：{stamp}')
md.append(f'- 冻结章节数：{len(freeze)}')
md.append(f'- 大纲≤500章条目：{len(outline_items)}')
md.append(f'- 未来章冲突/内部名：{len(conflicts)}')
md.append(f'- 已写/已上传重复仅记录：{len(frozen_duplicates)}\n')
md.append('## 冻结库重复（只记录，不改已写）\n')
for d in frozen_duplicates:
    md.append(f'- 「{d["title"]}」：章节 {d["chapters"]}｜动作：{d["action"]}')
md.append('\n## 未来章需改名候选\n')
for c in conflicts:
    md.append(f'### 第{c["chapter"]}章｜{c["title"]}｜{c["type"]}')
    md.append(f'- 撞名/关联：{c["collides_with"]}')
    md.append(f'- 大纲行：{c["line"]}')
    md.append(f'- 原文：{c["raw"]}')
    md.append('- 建议新标题：待模型拟定\n')
md_path.write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'freeze':str(freeze_path),'plan_json':str(plan_json),'plan_md':str(md_path),'freeze_count':len(freeze),'future_conflicts':len(conflicts),'frozen_duplicates':len(frozen_duplicates)},ensure_ascii=False,indent=2))
