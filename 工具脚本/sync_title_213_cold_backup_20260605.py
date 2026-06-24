from pathlib import Path
import re, shutil, json, datetime
root=Path('/root/workspace/科武纪元')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup=root/'审核记录'/'备份'/f'标题同步_213_冷备机_{stamp}'
backup.mkdir(parents=True, exist_ok=True)
ch=213; title='冷备机'; changed=[]

def backup_file(p):
    if not p.exists(): return
    dest=backup/p.relative_to(root); dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists(): shutil.copy2(p,dest)

def set_first(p):
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore'); lines=txt.splitlines(); idx=None
    for i,l in enumerate(lines[:20]):
        if l.strip(): idx=i; break
    if idx is None: return
    old=lines[idx]
    new=f'第{ch}章 {title}'
    if old.lstrip().startswith('#'):
        m=re.match(r'^(#+)\s*', old); hashes=m.group(1) if m else '#'; new=f'{hashes} 第{ch}章 {title}'
    if old!=new:
        backup_file(p); lines[idx]=new; p.write_text('\n'.join(lines)+'\n', encoding='utf-8'); changed.append({'file':str(p),'old':old,'new':new})

def update_wiki():
    p=root/'wiki/chapters/ch213.md'
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt
    txt=re.sub(r'(?m)^title:\s*.*$', f'title: {title}', txt, count=1)
    txt=re.sub(r'(?m)^#\s*第?\s*213章.*$', f'# 第213章 {title}', txt, count=1)
    txt=re.sub(r'(## Full Text\s*\n)第\s*213章[^\n]*', r'\1'+f'第213章 {title}', txt, count=1)
    if txt!=old:
        backup_file(p); p.write_text(txt, encoding='utf-8'); changed.append({'file':str(p),'old':'wiki title/fulltext','new':title})

def update_table_file(p):
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt; lines=[]
    for line in txt.splitlines():
        if re.search(r'第213章\s*\|', line):
            parts=line.split('|')
            if len(parts)>=4:
                parts[3]=' '+title+' '; line='|'.join(parts)
        lines.append(line)
    txt='\n'.join(lines)+'\n'
    if txt!=old:
        backup_file(p); p.write_text(txt, encoding='utf-8'); changed.append({'file':str(p),'old':'table title','new':title})

def update_tracking(p):
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt
    txt=re.sub(r'(\|\s*第213章\s*\|\s*)[^|\n]+(\|)', rf'\1{title} \2', txt)
    txt=re.sub(r'(\|\s*213\s*\|\s*[^|]+\|\s*)[^|\n]+(\|)', rf'\1{title} \2', txt)
    if txt!=old:
        backup_file(p); p.write_text(txt, encoding='utf-8'); changed.append({'file':str(p),'old':'tracking title','new':title})

for p in sorted((root/'新版').glob('第213章*.md')): set_first(p)
for p in sorted((root/'已投稿').glob('第213章*.txt')): set_first(p)
update_wiki()
update_table_file(root/'wiki/raw/outline/科武纪元大纲_latest.md')
update_table_file(root/'科武纪元大纲 V8_完整版.md')
update_tracking(root/'小说综合跟踪表.md')
update_tracking(root/'wiki/raw/chapters/chapter-track.md')
update_tracking(root/'新版/chapter-track.md')
note=f"\n\n### {stamp} 标题同步：213\n- 第213章由《内部签名》改为《冷备机》。\n- 依据：正文核心转折为冷备机回包、账号接管与样本流转权限线索。\n- 仅改标题字段；未改正文段落；未触碰番茄后台。\n"
for name in ['STATUS.md','WAL.md']:
    p=root/name
    if p.exists():
        backup_file(p); p.write_text(p.read_text(encoding='utf-8', errors='ignore')+note, encoding='utf-8'); changed.append({'file':str(p),'old':'append','new':'213 title note'})
out=root/'审核记录'/f'标题同步_213_冷备机_报告_{stamp}.json'
out.write_text(json.dumps({'stamp':stamp,'backup':str(backup),'changed':changed}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'stamp':stamp,'backup':str(backup),'report':str(out),'changed_count':len(changed)}, ensure_ascii=False, indent=2))
