from pathlib import Path
import re, shutil, datetime, json
root=Path('/root/workspace/科武纪元')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup=root/'审核记录'/'备份'/f'章节标题索引补漏_{stamp}'
backup.mkdir(parents=True, exist_ok=True)
changed=[]

def backup_file(p):
    if not p.exists(): return
    dest=backup/p.relative_to(root); dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists(): shutil.copy2(p,dest)

def replace_file(p, repls):
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt
    for a,b in repls:
        txt=txt.replace(a,b)
    if txt!=old:
        backup_file(p); p.write_text(txt, encoding='utf-8'); changed.append(str(p))

replace_file(root/'wiki'/'chapters'/'ch037.md', [('第37章 算力危机','第37章 白鹭线索')])
replace_file(root/'新版'/'chapter-track.md', [('| 37 | 3533 | 算力危机 | ✅ |','| 37 | 3533 | 白鹭线索 | ✅ |')])
# append status/wal
for name in ['STATUS.md','WAL.md']:
    p=root/name
    if p.exists():
        backup_file(p)
        p.write_text(p.read_text(encoding='utf-8', errors='ignore')+f"\n- {stamp} 标题索引补漏：同步 ch037 Key Events 与 新版/chapter-track；未改正文。\n", encoding='utf-8')
        changed.append(str(p))
out=root/'审核记录'/f'章节标题索引补漏报告_{stamp}.json'
out.write_text(json.dumps({'stamp':stamp,'backup':str(backup),'changed':changed}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'stamp':stamp,'backup':str(backup),'report':str(out),'changed':changed}, ensure_ascii=False, indent=2))
