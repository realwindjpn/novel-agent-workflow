#!/usr/bin/env python3
from pathlib import Path
import re, shutil, time, json
root=Path('/root/workspace/科武纪元')
run=root/'审核记录/149150_六角色上传线_20260614'
backup=run/'backups_before_writeback'
backup.mkdir(parents=True, exist_ok=True)
chapters={149: run/'09_author_repair_mimo_ch149.md', 150: run/'09_author_repair_mimo_ch150.md'}

def fanqie_count(text):
    lines=[l for l in text.splitlines() if l.strip()]
    title=lines[0].strip() if lines else ''
    return max(0, len(''.join(text.split())) - len(''.join(title.split())))

def clean_body(text, n):
    lines=text.replace('\r\n','\n').replace('\r','\n').split('\n')
    start=None
    for i,l in enumerate(lines):
        if l.strip().startswith(f'第{n}章'):
            start=i; break
    if start is None:
        raise SystemExit(f'MISSING_TITLE {n}')
    body='\n'.join(lines[start:]).strip()+'\n'
    if '（本章完）' not in body:
        raise SystemExit(f'MISSING_END {n}')
    body=body[:body.rfind('（本章完）')+len('（本章完）')]+'\n'
    bad=['作者候选稿','模型：','源稿：','日期：','```','[[',']]']
    hits=[b for b in bad if b in body]
    if hits:
        raise SystemExit(f'BAD_MARKERS {n} {hits}')
    cnt=fanqie_count(body)
    if cnt<3000:
        raise SystemExit(f'LOW_COUNT {n} {cnt}')
    return body,cnt

summary={}
for n,src in chapters.items():
    text=src.read_text(encoding='utf-8')
    body,cnt=clean_body(text,n)
    new=root/'新版'/f'第{n}章.md'
    sub=root/'已投稿'/f'第{n}章.txt'
    for p in [new,sub]:
        if p.exists():
            shutil.copy2(p, backup/f'{p.name}.{time.strftime("%Y%m%d_%H%M%S")}.bak')
    new.write_text(body,encoding='utf-8')
    # 已投稿TXT: 当前只生成正文镜像；作者说后续 ready gate 若需再补
    sub.parent.mkdir(parents=True, exist_ok=True)
    sub.write_text(body,encoding='utf-8')
    summary[n]={'count':cnt,'new':str(new),'txt':str(sub),'size_new':new.stat().st_size,'size_txt':sub.stat().st_size}
(run/'13_writeback_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
