from pathlib import Path
import re, shutil, json, datetime
root=Path('/root/workspace/科武纪元')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup=root/'审核记录'/'备份'/f'标题同步_133_算力缺口_{stamp}'
backup.mkdir(parents=True, exist_ok=True)
ch=133
title='算力缺口'
changed=[]

def backup_file(p):
    if not p.exists(): return
    dest=backup/p.relative_to(root); dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists(): shutil.copy2(p,dest)

def set_first(p):
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore')
    lines=txt.splitlines(); idx=None
    for i,l in enumerate(lines[:20]):
        if l.strip(): idx=i; break
    if idx is None: return
    old=lines[idx]
    new=f'第{ch}章 {title}'
    if old.lstrip().startswith('#'):
        m=re.match(r'^(#+)\s*', old); hashes=m.group(1) if m else '#'
        new=f'{hashes} 第{ch}章 {title}'
    if old!=new:
        backup_file(p); lines[idx]=new; p.write_text('\n'.join(lines)+'\n', encoding='utf-8')
        changed.append({'file':str(p),'old':old,'new':new})

def update_wiki():
    p=root/'wiki/chapters/ch133.md'
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt
    txt=re.sub(r'(?m)^title:\s*.*$', f'title: {title}', txt, count=1)
    txt=re.sub(r'(?m)^#\s*第?\s*133章.*$', f'# 第133章 {title}', txt, count=1)
    txt=re.sub(r'(## Full Text\s*\n)第\s*133章[^\n]*', r'\1'+f'第133章 {title}', txt, count=1)
    if txt!=old:
        backup_file(p); p.write_text(txt, encoding='utf-8'); changed.append({'file':str(p),'old':'wiki title/fulltext','new':title})

def update_table_file(p):
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt
    lines=[]
    for line in txt.splitlines():
        if re.search(r'第133章\s*\|', line):
            parts=line.split('|')
            if len(parts)>=4:
                parts[3]=' '+title+' '
                line='|'.join(parts)
        lines.append(line)
    txt='\n'.join(lines)+'\n'
    if txt!=old:
        backup_file(p); p.write_text(txt, encoding='utf-8'); changed.append({'file':str(p),'old':'table title','new':title})

def update_tracking(p):
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt
    txt=re.sub(r'(\|\s*第133章\s*\|\s*)[^|\n]+(\|)', rf'\1{title} \2', txt)
    txt=re.sub(r'(\|\s*133\s*\|\s*[^|]+\|\s*)[^|\n]+(\|)', rf'\1{title} \2', txt)
    if txt!=old:
        backup_file(p); p.write_text(txt, encoding='utf-8'); changed.append({'file':str(p),'old':'tracking title','new':title})

for p in sorted((root/'新版').glob('第133章*.md')): set_first(p)
for p in sorted((root/'已投稿').glob('第133章*.txt')): set_first(p)
update_wiki()
for p in [root/'wiki/raw/outline/科武纪元大纲_latest.md', root/'科武纪元大纲 V8_完整版.md']:
    update_table_file(p)
for p in [root/'小说综合跟踪表.md', root/'wiki/raw/chapters/chapter-track.md', root/'新版/chapter-track.md']:
    update_tracking(p)
note=f"\n\n### {stamp} 标题同步：第133章\n- 第133章由《三十EFLOPS》改为《算力缺口》，读者更易理解。\n- 同步范围：新版、已投稿TXT、Wiki、大纲、跟踪表、chapter-track。\n- 未改正文，未触碰番茄后台。\n"
for name in ['STATUS.md','WAL.md']:
    p=root/name
    if p.exists():
        backup_file(p); p.write_text(p.read_text(encoding='utf-8', errors='ignore')+note, encoding='utf-8')
        changed.append({'file':str(p),'old':'append','new':'133 title sync note'})
out=root/'审核记录'/f'标题同步_133_算力缺口_报告_{stamp}.json'
out.write_text(json.dumps({'stamp':stamp,'backup':str(backup),'changed':changed}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'stamp':stamp,'backup':str(backup),'report':str(out),'changed_count':len(changed)}, ensure_ascii=False, indent=2))
