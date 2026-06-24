from pathlib import Path
import re, json

base = Path('/root/workspace/科武纪元')
run = base / '审核记录/自循环体系会议_20260604'
posted = base / '已投稿'
posted.mkdir(exist_ok=True)
notes = {
    131: '本章聚焦渗透链路与人质胁迫。技术细节为小说化处理，请以现实安全规范为准。',
    132: '本章写安全升级后的代价与余波。相关技术设定服务剧情，现实中仍以合规与安全为前提。',
}
res = []
for n in (131, 132):
    md = base / '新版' / f'第{n}章.md'
    s = md.read_text(encoding='utf-8')
    s = re.sub(r'\[\[([^\]]+)\]\]', r'\1', s)
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    s = re.sub(r'```.*?```', '', s, flags=re.S)
    s = s.replace('**', '').replace('__', '')
    s = '\n'.join(line.rstrip() for line in s.splitlines()).strip()
    title = next((x.strip() for x in s.splitlines() if x.strip()), '')
    body_count = len(''.join(s.split())) - len(''.join(title.split()))
    txt = s.rstrip() + f'\n\n作者有话说：\n{notes[n]}\n'
    out = posted / f'第{n}章.txt'
    out.write_text(txt, encoding='utf-8')
    checks = {
        'chapter': n,
        'txt': str(out),
        'exists': out.exists(),
        'title': title,
        'fanqie_body_count': body_count,
        'wikilink_clean': ('[[' not in txt and ']]' not in txt),
        'markdown_clean': all(x not in txt for x in ['```', '**', '__']),
        'triple_blank_clean': '\n\n\n' not in txt,
        'author_note': '作者有话说：' in txt,
        'ending': '（本章完）' in s.splitlines()[-1],
    }
    res.append(checks)
report = run / 'uploadline_131_132_txt_export_gate_20260605.json'
report.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'report': str(report), 'results': res}, ensure_ascii=False, indent=2))
