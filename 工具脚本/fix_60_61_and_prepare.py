#!/usr/bin/env python3
from pathlib import Path
import re, shutil, datetime
base=Path('/root/workspace/科武纪元')
new=base/'新版'
posted=base/'已投稿'
backup=base/'archive'/('before_60_61_fix_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
backup.mkdir(parents=True, exist_ok=True)
files=[new/'第60章.md', new/'第61章.md', posted/'第60章.txt']
for p in files:
    if p.exists(): shutil.copy2(p, backup/p.name)
repls={
    '国家安全部，请配合调查':'安全机关，请配合调查',
    '国安方面':'安全机关',
    '武汉':'江城',
    '国内骨干网':'境内骨干网',
    '国内人':'境内人',
    '五国军工集团':'多国军工集团',
    '这五个国家的军工集团':'这些军工集团',
    '海外名校':'境外高校',
    '免费东南亚旅游团':'低价南洋旅行团',
    'Analysts':'分析员',
    'compartmentalization':'分舱隔离',
}
# fix content
for p in [new/'第60章.md', new/'第61章.md']:
    s=p.read_text(encoding='utf-8')
    for a,b in repls.items(): s=s.replace(a,b)
    if p.name=='第61章.md':
        s=s.replace('张维舟舟','张维舟')
        # unify short name to full name in chapter 61 only
        s=s.replace('张维', '张维舟')
        s=s.replace('张维舟舟','张维舟')
    p.write_text(s, encoding='utf-8')
# md to txt helper
def md_to_txt(md_path, txt_path):
    s=md_path.read_text(encoding='utf-8')
    for a,b in repls.items(): s=s.replace(a,b)
    lines=[x.rstrip() for x in s.splitlines()]
    while lines and not lines[0].strip(): lines.pop(0)
    while lines and not lines[-1].strip(): lines.pop()
    if lines and lines[0].startswith('#'): lines[0]=lines[0].lstrip('#').strip()
    if not lines or lines[-1].strip()!='（本章完）': lines += ['', '（本章完）']
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
md_to_txt(new/'第60章.md', posted/'第60章.txt')
md_to_txt(new/'第61章.md', posted/'第61章.txt')
# audit
sensitive=re.compile(r'美国|日本|伊朗|欧洲|中东|台湾|联合国|北约|华尔街|MIT|俄罗斯|中国|巴基斯坦|印度|国家安全部|国安|武汉|国内|五国|海外名校|免费|Analysts|compartmentalization')
for ch in [60,61]:
    p=posted/f'第{ch}章.txt'
    s=p.read_text(encoding='utf-8')
    lines=[x for x in s.splitlines() if x.strip()]
    chars=sum(1 for c in s if '\u4e00'<=c<='\u9fff')
    hits=sorted(set(sensitive.findall(s)))
    print(f'CH{ch}', 'chars', chars, 'first', lines[0], 'last', lines[-1], 'hits', hits)
print('BACKUP', backup)
