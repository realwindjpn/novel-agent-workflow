from pathlib import Path
import re, json, shutil, datetime
root=Path('/root/workspace/科武纪元')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup=root/'审核记录'/'备份'/f'章节标题105补丁_{stamp}'
backup.mkdir(parents=True, exist_ok=True)
ch=105; title='太行雪'
report=[]

def backup_file(p):
    if not p.exists(): return
    rel=p.relative_to(root); dest=backup/rel; dest.parent.mkdir(parents=True, exist_ok=True)
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
        backup_file(p); lines[idx]=new; p.write_text('\n'.join(lines)+'\n', encoding='utf-8'); report.append((str(p),old,new))
for p in sorted((root/'新版').glob('第105章*.md'))+sorted((root/'新版').glob('第 105 章*.md'))+sorted((root/'已投稿').glob('第105章*.txt')):
    set_first(p)
# wiki
p=root/'wiki'/'chapters'/'ch105.md'
if p.exists():
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt
    txt=re.sub(r'(?m)^title:\s*.*$', f'title: {title}', txt, count=1)
    txt=re.sub(r'(?m)^#\s*第?\s*105章.*$', f'# 第105章 {title}', txt, count=1)
    txt=re.sub(r'(## Full Text\s*\n)第\s*105章[^\n]*', r'\1'+f'第105章 {title}', txt, count=1)
    if txt!=old: backup_file(p); p.write_text(txt, encoding='utf-8'); report.append((str(p),'wiki title',title))
# outline table
p=root/'wiki'/'raw'/'outline'/'科武纪元大纲_latest.md'
if p.exists():
    lines=p.read_text(encoding='utf-8', errors='ignore').splitlines(); out=[]; changed=False
    for line in lines:
        if re.search(r'第105章\s*\|', line):
            parts=line.split('|')
            if len(parts)>=4:
                parts[3]=' '+title+' '; line='|'.join(parts); changed=True
        out.append(line)
    if changed: backup_file(p); p.write_text('\n'.join(out)+'\n', encoding='utf-8'); report.append((str(p),'outline 105',title))
# tracking table
p=root/'小说综合跟踪表.md'
if p.exists():
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt
    txt=re.sub(r'(\|\s*第105章\s*\|\s*)[^|\n]+(\|)', rf'\1{title} \2', txt)
    if txt!=old: backup_file(p); p.write_text(txt, encoding='utf-8'); report.append((str(p),'tracking 105',title))
# status/wal append
for name in ['STATUS.md','WAL.md']:
    p=root/name
    if p.exists():
        backup_file(p)
        p.write_text(p.read_text(encoding='utf-8', errors='ignore')+f"\n- {stamp} 标题去重补丁：第105章由《烽火暂歇》改为《太行雪》，避免与第100章撞名；仅改标题。\n", encoding='utf-8')
        report.append((str(p),'append','105 title fix'))
out=root/'审核记录'/f'章节标题105补丁报告_{stamp}.json'
out.write_text(json.dumps({'stamp':stamp,'backup':str(backup),'report':report}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'stamp':stamp,'backup':str(backup),'report':str(out),'changed':len(report)}, ensure_ascii=False, indent=2))
