from pathlib import Path
import re, shutil, datetime, json
root=Path('/root/workspace/科武纪元')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup=root/'审核记录'/'备份'/f'章节标题副本补丁_{stamp}'
backup.mkdir(parents=True, exist_ok=True)
changes={6:'自主组网',7:'两封邮件',8:'入营',9:'人机接口',13:'偏科',15:'红色警戒',16:'加密数据包',17:'综合小测',18:'站桩',19:'深舱',20:'协议过载',37:'白鹭线索',71:'供应链绞杀',87:'伦理死循环',105:'太行雪',106:'多边博弈',131:'内鬼',133:'三十EFLOPS',140:'天基之眼',155:'月面初行',156:'双箭齐发',157:'遗迹优先',159:'着陆沙克尔顿',164:'L1防线',167:'月背遗迹',175:'共振传递',184:'不变量',207:'命名权',213:'签署日',228:'六小时窗口',233:'调拨单',250:'K17路'}
changed=[]

def backup_file(p):
    if not p.exists(): return
    dest=backup/p.relative_to(root); dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists(): shutil.copy2(p,dest)

def update_table_file(p):
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt
    lines=[]
    for line in txt.splitlines():
        for ch,title in changes.items():
            if re.search(rf'第{ch}章\s*\|', line):
                parts=line.split('|')
                if len(parts)>=4:
                    parts[3]=' '+title+' '
                    line='|'.join(parts)
        lines.append(line)
    txt='\n'.join(lines)+'\n'
    if txt!=old:
        backup_file(p); p.write_text(txt, encoding='utf-8'); changed.append(str(p))

def update_track(p):
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt
    for ch,title in changes.items():
        txt=re.sub(rf'(\|\s*{ch}\s*\|\s*[^|]+\|\s*)[^|\n]+(\|)', rf'\1{title} \2', txt)
        txt=re.sub(rf'(\|\s*第{ch}章\s*\|\s*)[^|\n]+(\|)', rf'\1{title} \2', txt)
    if txt!=old:
        backup_file(p); p.write_text(txt, encoding='utf-8'); changed.append(str(p))

update_table_file(root/'科武纪元大纲 V8_完整版.md')
update_track(root/'wiki'/'raw'/'chapters'/'chapter-track.md')
# append status/wal
for name in ['STATUS.md','WAL.md']:
    p=root/name
    if p.exists():
        backup_file(p)
        p.write_text(p.read_text(encoding='utf-8', errors='ignore')+f"\n- {stamp} 标题副本补丁：同步根目录大纲副本与 chapter-track 标题；未改正文。\n", encoding='utf-8')
        changed.append(str(p))
out=root/'审核记录'/f'章节标题副本补丁报告_{stamp}.json'
out.write_text(json.dumps({'stamp':stamp,'backup':str(backup),'changed':changed}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'stamp':stamp,'backup':str(backup),'report':str(out),'changed':changed}, ensure_ascii=False, indent=2))
