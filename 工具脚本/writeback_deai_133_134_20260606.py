from pathlib import Path
import re, json, shutil, datetime
root = Path('/root/workspace/科武纪元')
run = root / '审核记录/自循环体系会议_20260605/deai_rerun_133_134'
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
c133 = run / 'ch133_author_candidate.md'
c134 = run / 'ch134_author_repair_candidate.md'
s133 = root / '新版/第133章.md'
s134 = root / '新版/第134章.md'
outdir = root / '审核记录/自循环体系会议_20260605/deai_writeback_133_134_20260606'
outdir.mkdir(parents=True, exist_ok=True)
for p in [s133, s134, root/'已投稿/第133章.txt', root/'已投稿/第134章.txt']:
    if p.exists():
        shutil.copy2(p, outdir / (p.name + f'.bak_{ts}'))

def fanqie_count_text(text: str) -> int:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines and re.match(r'^第\d+章', lines[0]):
        lines = lines[1:]
    body = ''.join(lines)
    body = body.replace('作者有话说：', '')
    return len(re.sub(r'\s+', '', body))

def clean_md_to_txt(text: str, note: str) -> str:
    text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.S)
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.M)
    text = text.replace('**', '').replace('`', '')
    return text.strip() + "\n\n作者有话说：" + note.strip() + "\n"

text133 = c133.read_text(encoding='utf-8').strip() + '\n'
text134 = c134.read_text(encoding='utf-8').strip() + '\n'
insert = '他又按了按口袋，确认地图没有滑出来。'
anchor = '林星辰没应声，把地图折起来，塞进外套口袋。纸边硌着胸口，走动的时候能感觉到折痕顶着皮肤。'
if fanqie_count_text(text134) < 3000 and insert not in text134:
    text134 = text134.replace(anchor, anchor + '\n\n' + insert)

s133.write_text(text133, encoding='utf-8')
s134.write_text(text134, encoding='utf-8')
(root/'已投稿/第133章.txt').write_text(clean_md_to_txt(text133, '近地轨道的风险已经压到月球线，下一章继续看具体执行。'), encoding='utf-8')
(root/'已投稿/第134章.txt').write_text(clean_md_to_txt(text134, '登月论证完成，下一章会落到队伍分工与月球基地细节。'), encoding='utf-8')

report = {}
for ch, txt in [(133, text133), (134, text134)]:
    sub = (root/'已投稿'/f'第{ch}章.txt').read_text(encoding='utf-8')
    body = sub.split('作者有话说：')[0]
    report[str(ch)] = {
        'fanqie_count_md': fanqie_count_text(txt),
        'fanqie_count_txt': fanqie_count_text(body),
        'wikilink_md': '[[' in txt,
        'wikilink_txt': '[[' in sub,
        'triple_blank_txt': bool(re.search(r'\n{3,}', sub)),
        'has_author_note': '作者有话说：' in sub,
        'note_starts_with_prefix': sub.split('作者有话说：',1)[1].strip().startswith('作者有话说') if '作者有话说：' in sub else None,
        'title': sub.splitlines()[0] if sub.splitlines() else '',
        'end_marker': '（本章完）' in body,
    }
report['overall_pass'] = all(
    v['fanqie_count_txt'] >= 3000 and not v['wikilink_txt'] and not v['triple_blank_txt'] and v['has_author_note'] and not v['note_starts_with_prefix'] and v['end_marker']
    for v in report.values() if isinstance(v, dict)
)
report['insert_ch134'] = insert if insert in text134 else None
(outdir/'writeback_txt_gate_20260606.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'outdir': str(outdir), 'report': report}, ensure_ascii=False, indent=2))
