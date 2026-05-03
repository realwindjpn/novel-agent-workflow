#!/usr/bin/env python3
from pathlib import Path
import re,json,difflib
base=Path('/root/workspace/科武纪元')
sensitive=re.compile(r'美国|日本|伊朗|欧洲|中东|台湾|联合国|北约|华尔街|MIT|俄罗斯|中国|巴基斯坦|印度')
report=[]
for ch in [61,62]:
    md=base/'新版'/f'第{ch}章.md'
    old=base/'已投稿'/f'第{ch}章.txt'
    item={'chapter':ch,'md':str(md),'md_exists':md.exists(),'posted_exists':old.exists()}
    if md.exists():
        txt=md.read_text(encoding='utf-8',errors='ignore')
        lines=[x.rstrip() for x in txt.splitlines()]
        while lines and not lines[0].strip(): lines.pop(0)
        while lines and not lines[-1].strip(): lines.pop()
        if lines and lines[0].startswith('#'): lines[0]=lines[0].lstrip('#').strip()
        body='\n'.join(lines)
        item['first']=lines[0] if lines else ''
        item['last']=lines[-1] if lines else ''
        item['chars']=sum(1 for c in body if '\u4e00'<=c<='\u9fff')
        item['format_ok']=bool(lines and re.match(rf'^第\s*{ch}\s*章',lines[0]) and lines[-1].strip()=='（本章完）')
        item['word_count_ok']=item['chars']>=2500
        item['sensitive']=sorted(set(sensitive.findall(body)))
        # continuity snippets
        prev=base/'已投稿'/f'第{ch-1}章.txt'
        if prev.exists():
            pl=[x.rstrip() for x in prev.read_text(encoding='utf-8',errors='ignore').splitlines() if x.strip()]
            item['prev_tail5']=pl[-5:]
        item['head5']=[x for x in lines[:5]]
        item['tail5']=[x for x in lines[-5:]]
        if old.exists():
            oldtxt=old.read_text(encoding='utf-8',errors='ignore')
            item['similarity_to_posted']=round(difflib.SequenceMatcher(None,body,oldtxt).ratio(),4)
    report.append(item)
out=base/'审核记录'/f'上传前审核_第61-62章.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(out)
print(json.dumps(report,ensure_ascii=False,indent=2))
