from pathlib import Path
import re, json, shutil, datetime
root=Path('/root/workspace/科武纪元')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup=root/'审核记录'/'备份'/f'章节标题落地_{stamp}'
backup.mkdir(parents=True, exist_ok=True)
changes={
  6:'自主组网',7:'两封邮件',8:'入营',9:'人机接口',13:'偏科',15:'红色警戒',16:'加密数据包',17:'综合小测',18:'站桩',19:'深舱',20:'协议过载',37:'白鹭线索',71:'供应链绞杀',87:'伦理死循环',105:'烽火暂歇',106:'多边博弈',131:'内鬼',133:'三十EFLOPS',140:'天基之眼',155:'月面初行',156:'双箭齐发',157:'遗迹优先',159:'着陆沙克尔顿',164:'L1防线',167:'月背遗迹',175:'共振传递',184:'不变量',207:'命名权',213:'签署日',228:'六小时窗口',233:'调拨单',250:'K17路'
}
report=[]

def backup_file(p):
    if not p.exists(): return
    rel=p.relative_to(root)
    dest=backup/rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists(): shutil.copy2(p,dest)

def repl_first_title_line(p,ch,title):
    if not p.exists(): return False
    txt=p.read_text(encoding='utf-8', errors='ignore')
    lines=txt.splitlines()
    idx=None
    for i,l in enumerate(lines[:20]):
        if l.strip(): idx=i; break
    if idx is None: return False
    old=lines[idx]
    new=f'第{ch}章 {title}'
    if old.lstrip().startswith('#'):
        m_hash=re.match(r'^(#+)\s*', old)
        hashes=m_hash.group(1) if m_hash else '#'
        new=f'{hashes} 第{ch}章 {title}'
    if old==new: return False
    backup_file(p)
    lines[idx]=new
    p.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    report.append({'file':str(p),'chapter':ch,'old':old,'new':new})
    return True

def update_wiki(p,ch,title):
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore')
    oldtxt=txt
    # frontmatter title
    txt=re.sub(r'(?m)^title:\s*.*$', f'title: {title}', txt, count=1)
    # h1
    txt=re.sub(r'(?m)^#\s*第?\s*%d章.*$'%ch, f'# 第{ch}章 {title}', txt, count=1)
    # Full Text first title line after marker
    txt=re.sub(r'(## Full Text\s*\n)第\s*%d章[^\n]*'%ch, r'\1'+f'第{ch}章 {title}', txt, count=1)
    if txt!=oldtxt:
        backup_file(p); p.write_text(txt, encoding='utf-8'); report.append({'file':str(p),'chapter':ch,'old':'wiki title/fulltext','new':title})

def update_outline(titlemap):
    p=root/'wiki'/'raw'/'outline'/'科武纪元大纲_latest.md'
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt
    lines=txt.splitlines()
    out=[]
    for line in lines:
        done=False
        for ch,title in titlemap.items():
            # table form: 第105章 | 卷 | oldtitle | ...
            if re.search(rf'第{ch}章\s*\|', line):
                parts=line.split('|')
                # preserve leading indentation/index column; title usually third field after chapter/volume
                # examples: "   189|第105章 | 第二卷·烽火 | 卷二终章 | ..."
                if len(parts)>=4:
                    parts[3]=' '+title+' '
                    line='|'.join(parts); done=True; break
            # non-table form
            if re.search(rf'第\s*{ch}\s*章[：:、\s-]', line):
                line=re.sub(rf'(第\s*{ch}\s*章[：:、\s-]+)([^|｜（(【。；;\n]+)', rf'\1{title}', line, count=1)
                done=True; break
        out.append(line)
    txt='\n'.join(out)+'\n'
    if txt!=old:
        backup_file(p); p.write_text(txt, encoding='utf-8'); report.append({'file':str(p),'chapter':'outline','old':'outline titles','new':'updated'})

def update_tracking(titlemap):
    p=root/'小说综合跟踪表.md'
    if not p.exists(): return
    txt=p.read_text(encoding='utf-8', errors='ignore'); old=txt
    for ch,title in titlemap.items():
        # lines like | 第133章 | 算力危机 |
        txt=re.sub(rf'(\|\s*第{ch}章\s*\|\s*)[^|\n]+(\|)', rf'\1{title} \2', txt)
    if txt!=old:
        backup_file(p); p.write_text(txt, encoding='utf-8'); report.append({'file':str(p),'chapter':'tracking','old':'tracking titles','new':'updated'})

# 新版 and 已投稿 and wiki
for ch,title in changes.items():
    # normal source
    for p in sorted((root/'新版').glob(f'第{ch}章*.md')):
        repl_first_title_line(p,ch,title)
    # special spaced source for 105
    if ch==105:
        for p in sorted((root/'新版').glob('第 105 章*.md')):
            repl_first_title_line(p,ch,title)
    for p in sorted((root/'已投稿').glob(f'第{ch}章*.txt')):
        repl_first_title_line(p,ch,title)
    update_wiki(root/'wiki'/'chapters'/f'ch{ch:03d}.md',ch,title)
update_outline(changes)
update_tracking(changes)
# STATUS/WAL append
for name in ['STATUS.md','WAL.md']:
    p=root/name
    if p.exists():
        backup_file(p)
        add=f"\n\n### {stamp} 章节标题去重落地\n- 按 GPT-5.5 终审表同步32章标题；重点修复37/133《算力危机》、105/106《卷二终章》。\n- 仅改标题行/标题字段；不改正文段落；不动番茄草稿箱。\n- 备份目录：{backup}\n"
        p.write_text(p.read_text(encoding='utf-8', errors='ignore')+add, encoding='utf-8')
        report.append({'file':str(p),'chapter':'status_wal','old':'append','new':'title dedup note'})
# report
out=root/'审核记录'/f'章节标题落地报告_{stamp}.json'
out.write_text(json.dumps({'stamp':stamp,'backup':str(backup),'changes':changes,'files_changed':report}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'stamp':stamp,'backup':str(backup),'report':str(out),'changed_entries':len(report)}, ensure_ascii=False, indent=2))
