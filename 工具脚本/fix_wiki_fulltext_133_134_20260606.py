from pathlib import Path
import re, datetime, json
root=Path('/root/workspace/科武纪元')
report={}
for ch in (133,134):
    src=root/'新版'/f'第{ch}章.md'
    wiki=root/'wiki/chapters'/f'ch{ch:03d}.md'
    text=src.read_text(encoding='utf-8').strip()+"\n"
    w=wiki.read_text(encoding='utf-8')
    marker='## Full Text\n'
    if marker not in w:
        w=w.rstrip()+"\n\n"+marker+text
    else:
        head=w.split(marker,1)[0]+marker
        # keep only metadata before Full Text; replace all following content with current full text
        w=head+text
    wiki.write_text(w,encoding='utf-8')
    report[str(ch)]={'wiki':str(wiki),'source':str(src),'updated':True,'contains_title':f'第{ch}章' in w}
out=root/'审核记录/自循环体系会议_20260605/deai_writeback_133_134_20260606/wiki_fulltext_fix_20260606.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
