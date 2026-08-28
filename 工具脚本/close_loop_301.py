#!/usr/bin/env python3
"""301 闭环：TXT 作者说合并 + 番茄口径校验 + 终验。

作者说由审席产出（output/AUTHOR_NOTE_301.txt），本脚本只做确定性拼装与校验。
"""
import pathlib
import hashlib
import re
import json
import sys

KEWU = pathlib.Path('/root/workspace/科武纪元')
TASK = KEWU / '任务运行态' / '20260828_kewu_selfcycle_daily'
BODY = TASK / 'output' / 'qwen_301_r4_clean.md'
NOTE = TASK / 'output' / 'AUTHOR_NOTE_301.txt'
TXT = KEWU / '已投稿' / '第301章.txt'

body = BODY.read_text(encoding='utf-8')
note = NOTE.read_text(encoding='utf-8').strip()

# 剥可能的引号包裹与前缀
note = re.sub(r'^作者有话说[：:]\s*', '', note)
note = note.strip('「」"\'' + '“”')

BANNED = ['真正', '核心', '关键', '意味着', '赋能', '生态闭环']
banned_hit = [w for w in BANNED if w in note]
formula = bool(re.search(r'不是[^。；\n]{0,25}[，,]?\s*(而)?是', note))
selfref = bool(re.search(r'第[一二三四五六七八九十百零\d]+章', note))
meta_leak = [w for w in ['审稿', '任务包', '模型', 'AI', '门禁', '流程'] if w in note]
note_cjk = len(re.findall(r'[\u4e00-\u9fff]', note))

note_gates = {
    'len_100_200': 100 <= note_cjk <= 200,
    'no_banned': not banned_hit,
    'no_formula': not formula,
    'no_chapter_selfref': not selfref,
    'no_meta_leak': not meta_leak,
    'first_person': '我' in note,
}

print('=== 作者说门禁 ===')
for k, v in note_gates.items():
    print(('OK  ' if v else 'FAIL'), k)
if banned_hit:
    print('  banned:', banned_hit)
if meta_leak:
    print('  meta_leak:', meta_leak)
print('  note_cjk:', note_cjk)
print('  note:', note)

if not all(note_gates.values()):
    print('\nNOTE_GATE_FAIL — 不写回 TXT，须重派作者说')
    sys.exit(1)

# 拼装 TXT：正文 + 空行 + 作者有话说
txt = body.rstrip('\n') + '\n\n作者有话说：\n' + note + '\n'
TXT.write_text(txt, encoding='utf-8')

# 番茄口径：非空白字符数
fanqie = len(re.sub(r'\s', '', txt))
body_cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
nonempty = [l for l in txt.split('\n') if l.strip()]

final_gates = {
    'first_line': nonempty[0] == '第301章 联合防御',
    'has_author_note': '作者有话说：' in txt,
    'body_end_marker': '（本章完）' in txt,
    'fanqie_min_3000': fanqie >= 3000,
    'no_wikilink': '[[' not in txt,
    'no_markdown_bold': '**' not in txt,
    'no_triple_blank': '\n\n\n' not in txt,
    'body_cjk_min_3000': body_cjk >= 3000,
}

print('\n=== TXT 终验 ===')
for k, v in final_gates.items():
    print(('OK  ' if v else 'FAIL'), k)
print('  番茄口径:', fanqie)
print('  正文净中文:', body_cjk)
print('  TXT SHA:', hashlib.sha256(txt.encode()).hexdigest())
print('  正文 SHA (审稿绑定):', hashlib.sha256(body.encode()).hexdigest())

report = {
    'chapter': 301,
    'title': '联合防御',
    'body_sha256': hashlib.sha256(body.encode()).hexdigest(),
    'txt_sha256': hashlib.sha256(txt.encode()).hexdigest(),
    'body_net_cjk': body_cjk,
    'fanqie_count': fanqie,
    'author_note_cjk': note_cjk,
    'note_gates': note_gates,
    'final_gates': final_gates,
    'txt_path': str(TXT),
    'verdict': 'CLOSE_LOOP_TXT_READY' if all(final_gates.values()) else 'TXT_GATE_FAIL',
}
(TASK / 'output' / 'CLOSE_LOOP_301.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
print('\nVERDICT', report['verdict'])
sys.exit(0 if all(final_gates.values()) else 1)
