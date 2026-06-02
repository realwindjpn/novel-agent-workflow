#!/usr/bin/env python3
from pathlib import Path
import re, json, shutil, datetime

BASE = Path('/root/workspace/科武纪元')
NOTES = {
    95: '本章写算力战从破坏转向争夺调度权。开源生态、审计链、许可证续期和可回滚执行都做了小说化处理，重点不是模型多聪明，而是系统必须能被验证、能追责、能回滚。',
    96: '本章写数字攻击落到城市现场。电、水、交通、通信这些接口一旦连锁失灵，技术问题就会变成民生问题。相关基础设施描写为小说化处理。',
}

def clean_md_to_txt(ch:int):
    src = BASE/'新版'/f'第{ch}章.md'
    dst = BASE/'已投稿'/f'第{ch}章.txt'
    if not src.exists():
        raise FileNotFoundError(src)
    text = src.read_text(encoding='utf-8').strip()
    # remove duplicate markdown heading line if present; keep plain first title line
    lines = text.splitlines()
    cleaned=[]
    for i,line in enumerate(lines):
        if i==1 and line.strip().startswith('# 第'):
            continue
        cleaned.append(re.sub(r'^#+\s*','',line))
    text='\n'.join(cleaned)
    text=re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text=text.replace('[[','').replace(']]','')
    text=re.sub(r'\n{3,}', '\n\n', text).strip()
    if not text.endswith('（本章完）'):
        text += '\n\n（本章完）'
    if '作者有话说：' in text:
        text = text.split('作者有话说：',1)[0].rstrip()
    note = NOTES[ch]
    final = text.rstrip() + '\n\n作者有话说：' + note + '\n'
    if dst.exists():
        bak = BASE/'审核记录'/'备份'/('上传TXT重写_'+datetime.date.today().isoformat())
        bak.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dst, bak/f'第{ch}章.txt.bak')
    dst.write_text(final, encoding='utf-8')
    fanqie_count = len(re.sub(r'\s+','',text))-len(re.sub(r'\s+','',text.splitlines()[0] if text.splitlines() else ''))
    assert '作者有话说：' in final
    assert '[[' not in final and ']]' not in final
    assert not re.search(r'\n\s*\n\s*\n', final)
    return {'chapter':ch,'txt':str(dst),'fanqie_count':fanqie_count,'note_len':len(note),'first':final.splitlines()[0]}

print(json.dumps([clean_md_to_txt(95), clean_md_to_txt(96)], ensure_ascii=False, indent=2))
