from pathlib import Path
import re, json
base=Path('/root/workspace/科武纪元')
run=base/'审核记录/自循环体系会议_20260605'
posted=base/'已投稿'
posted.mkdir(exist_ok=True)
notes={
  133:'本章聚焦算力危机与近地轨道方案。相关工程数据为小说化设定，请以现实技术发展为准。',
  134:'本章进入登月论证线。月球资源、能源与发射优势均为剧情设定服务，现实以公开科学资料为准。'
}
res=[]
for n in (133,134):
    md=base/'新版'/f'第{n}章.md'
    s=md.read_text(encoding='utf-8')
    s=re.sub(r'\[\[([^\]]+)\]\]', r'\1', s)
    s=s.replace('\r\n','\n').replace('\r','\n')
    s=re.sub(r'```.*?```','',s,flags=re.S)
    s=s.replace('**','').replace('__','')
    s='\n'.join(line.rstrip() for line in s.splitlines()).strip()
    title=next((x.strip() for x in s.splitlines() if x.strip()),'')
    body_count=len(''.join(s.split()))-len(''.join(title.split()))
    txt=s.rstrip()+f'\n\n作者有话说：\n{notes[n]}\n'
    out=posted/f'第{n}章.txt'
    out.write_text(txt,encoding='utf-8')
    res.append({'chapter':n,'txt':str(out),'title':title,'fanqie_body_count':body_count,'wikilink_clean':'[[' not in txt and ']]' not in txt,'markdown_clean':all(x not in txt for x in ['```','**','__']),'triple_blank_clean':'\n\n\n' not in txt,'author_note':'作者有话说：' in txt,'ending':s.strip().endswith('（本章完）')})
report=run/'uploadline_133_134_txt_export_gate_20260605.json'
report.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'report':str(report),'results':res},ensure_ascii=False,indent=2))
