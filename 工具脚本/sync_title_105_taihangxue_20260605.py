from pathlib import Path
import re, shutil, json, datetime
root=Path('/root/workspace/科武纪元')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup=root/'审核记录'/'备份'/f'标题同步_105_太行雪_{stamp}'
backup.mkdir(parents=True, exist_ok=True)
ch=105; title='太行雪'; changed=[]

def backup_file(p):
    if not p.exists(): return
    dest=backup/p.relative_to(root); dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists(): shutil.copy2(p,dest)

def set_first(p):
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8',errors='ignore'); lines=txt.splitlines(); idx=None
    for i,l in enumerate(lines[:20]):
        if l.strip(): idx=i; break
    if idx is None: return
    old=lines[idx]; new=f'第{ch}章 {title}'
    if old.lstrip().startswith('#'):
        m=re.match(r'^(#+)\s*', old); new=f'{m.group(1) if m else "#"} 第{ch}章 {title}'
    if old!=new:
        backup_file(p); lines[idx]=new; p.write_text('\n'.join(lines)+'\n',encoding='utf-8'); changed.append(str(p))
for pat in ['第105章*.md','第 105 章*.md']:
    for p in sorted((root/'新版').glob(pat)): set_first(p)
for p in sorted((root/'已投稿').glob('第105章*.txt')): set_first(p)
# wiki
p=root/'wiki/chapters/ch105.md'
if p.exists():
    txt=p.read_text(encoding='utf-8',errors='ignore'); old=txt
    txt=re.sub(r'(?m)^title:\s*.*$',f'title: {title}',txt,count=1)
    txt=re.sub(r'(?m)^#\s*第?\s*105章.*$',f'# 第105章 {title}',txt,count=1)
    txt=re.sub(r'(## Full Text\s*\n)第\s*105章[^\n]*',r'\1'+f'第105章 {title}',txt,count=1)
    if txt!=old: backup_file(p); p.write_text(txt,encoding='utf-8'); changed.append(str(p))
# table files
for p in [root/'wiki/raw/outline/科武纪元大纲_latest.md', root/'科武纪元大纲 V8_完整版.md']:
    if not p.exists(): continue
    lines=p.read_text(encoding='utf-8',errors='ignore').splitlines(); out=[]; old='\n'.join(lines)+'\n'
    for line in lines:
        if re.search(r'第105章\s*\|',line):
            parts=line.split('|')
            if len(parts)>=4: parts[3]=' '+title+' '; line='|'.join(parts)
        out.append(line)
    new='\n'.join(out)+'\n'
    if new!=old: backup_file(p); p.write_text(new,encoding='utf-8'); changed.append(str(p))
# tracking files
for p in [root/'小说综合跟踪表.md', root/'wiki/raw/chapters/chapter-track.md', root/'新版/chapter-track.md']:
    if not p.exists(): continue
    txt=p.read_text(encoding='utf-8',errors='ignore'); old=txt
    txt=re.sub(r'(\|\s*第105章\s*\|\s*)[^|\n]+(\|)',rf'\1{title} \2',txt)
    txt=re.sub(r'(\|\s*105\s*\|\s*[^|]+\|\s*)[^|\n]+(\|)',rf'\1{title} \2',txt)
    if txt!=old: backup_file(p); p.write_text(txt,encoding='utf-8'); changed.append(str(p))
note=f"\n\n### {stamp} 标题同步：第105章太行雪\n- 按用户确认，将第105章同步为《太行雪》。\n- 仅改标题行/标题字段；未改正文；未触碰番茄后台。\n"
for name in ['STATUS.md','WAL.md']:
    p=root/name
    if p.exists(): backup_file(p); p.write_text(p.read_text(encoding='utf-8',errors='ignore')+note,encoding='utf-8'); changed.append(str(p))
out=root/'审核记录'/f'标题同步_105_太行雪_报告_{stamp}.json'
out.write_text(json.dumps({'stamp':stamp,'backup':str(backup),'changed':changed},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'stamp':stamp,'backup':str(backup),'report':str(out),'changed_count':len(changed)},ensure_ascii=False,indent=2))
