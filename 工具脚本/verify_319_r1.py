#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第319章 R1 返修回收验收器（确定性，无 LLM 判断）。

判据：首尾锚点、净CJK、行数持平、diff 越界为零、四处旧命中归零、禁项零命中、
      sanitize 残留（Thinking completed / 分页控件 / markdown 标题）已剥。
"""
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

SRC = Path('/root/workspace/科武纪元/任务运行态/20260908_kewu_selfcycle_daily319320/output/qwen_319_draft.md')
RAW = Path('/root/workspace/科武纪元/任务运行态/20260909_ch319_r1_webqwen/output/qwen_319_r1_raw.md')
CLEAN = Path('/root/workspace/科武纪元/任务运行态/20260909_ch319_r1_webqwen/output/qwen_319_r1.md')

SRC_SHA = '19b1e0e5e9e416305a234b01c26d6e8961c37f659bd22159db26b2107d555f92'
FIRST = '第319章 代理人真相'
LAST = '（本章完）'
TARGET_LINES = [5, 124, 128, 130]

OLD_HITS = [
    '这种错号章在转运组内部意味着',
    '那个真正指挥这一切的人',
    '工程停在半程意味着',
    '真正的钨料不知道在哪',
]
HARD_ZERO = ['真正', '核心', '关键', '意味着', '值得关注', '赋能', '生态闭环']
UI_JUNK = [r'(?mi)^\s*Thinking completed\s*$', r'(?m)^\s*\d+\s*/\s*\d+\s*$',
           r'(?mi)^\s*已经完成思考\s*$']


def cjk(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))


def sanitize(text):
    t = text.replace('\r\n', '\n')
    for pat in UI_JUNK:
        t = re.sub(pat, '', t)
    lines = [ln.rstrip() for ln in t.split('\n')]
    # 剥 markdown 标题标记，与源稿裸标题格式对齐
    lines = [re.sub(r'^#+\s*', '', ln) if ln.lstrip().startswith('#') else ln for ln in lines]
    # 去掉首尾空行，压掉连续空行为单个
    out, prev_blank = [], False
    for ln in lines:
        blank = (ln.strip() == '')
        if blank and prev_blank:
            continue
        out.append(ln)
        prev_blank = blank
    while out and out[0].strip() == '':
        out.pop(0)
    while out and out[-1].strip() == '':
        out.pop()
    return '\n'.join(out) + '\n'


def main():
    if not RAW.exists():
        print(json.dumps({'verdict': 'FAIL', 'reason': 'raw_missing'}, ensure_ascii=False))
        return 2
    src = SRC.read_text(encoding='utf-8')
    if hashlib.sha256(src.encode('utf-8')).hexdigest() != SRC_SHA:
        print(json.dumps({'verdict': 'FAIL', 'reason': 'src_sha_mismatch'}, ensure_ascii=False))
        return 2

    clean = sanitize(RAW.read_text(encoding='utf-8'))
    CLEAN.write_text(clean, encoding='utf-8')
    clean = CLEAN.read_text(encoding='utf-8')

    s_lines = src.rstrip('\n').split('\n')
    c_lines = clean.rstrip('\n').split('\n')
    new_sha = hashlib.sha256(clean.encode('utf-8')).hexdigest()

    changed = [i + 1 for i, (a, b) in enumerate(zip(s_lines, c_lines)) if a != b]
    diff = list(difflib.unified_diff(s_lines, c_lines, lineterm='', n=0))

    old_hit_counts = {h: clean.count(h) for h in OLD_HITS}
    hz = {}
    for w in HARD_ZERO:
        hz[w] = clean.count(w)

    r = {
        'input_sha': SRC_SHA,
        'output_sha': new_sha,
        'sha_changed': new_sha != SRC_SHA,
        'first_line': c_lines[0].strip(),
        'first_line_ok': c_lines[0].strip() == FIRST,
        'last_line': c_lines[-1].strip(),
        'last_line_ok': c_lines[-1].strip() == LAST,
        'src_lines': len(s_lines),
        'out_lines': len(c_lines),
        'line_count_equal': len(s_lines) == len(c_lines),
        'src_cjk': cjk(src),
        'out_cjk': cjk(clean),
        'cjk_min_3200': cjk(clean) >= 3200,
        'changed_lines': changed,
        'changed_lines_within_scope': set(changed).issubset(set(TARGET_LINES)),
        'changed_count': len(changed),
        'old_hits_zeroed': all(v == 0 for v in old_hit_counts.values()),
        'old_hit_counts': old_hit_counts,
        'hard_zero_counts': hz,
        'hard_zero_ok': all(v == 0 for v in hz.values()),
        # 官方 validator（run_pure_api_reviews.py machine_checks）对第 1 行标题豁免
        # arabic_digits / latin_letters，此处照抄其口径，不自造更严阈值。
        'arabic_digits': len(re.findall(r'[0-9]', '\n'.join(c_lines[1:]))),
        'latin_letters': len(re.findall(r'[A-Za-z]', '\n'.join(c_lines[1:]))),
        'curly_quotes': len(re.findall(r'[\u201c\u201d\u2018\u2019]', clean)),
        'dash': len(re.findall(r'[\u2014\u2013]|--', clean)),
        'wikilink': clean.count('[['),
        'markdown_bold': clean.count('**'),
        'not_but': len(re.findall(r'不是[^。！？]{0,24}而是', clean)),
        'ui_junk_residue': sum(len(re.findall(p, clean)) for p in UI_JUNK),
        'gutter_residue': len(re.findall(r'(?m)^\d+\|', clean)),
    }
    r['banned_char_classes_zero'] = all(r[k] == 0 for k in (
        'arabic_digits', 'latin_letters', 'curly_quotes', 'dash',
        'wikilink', 'markdown_bold', 'not_but', 'ui_junk_residue', 'gutter_residue'))
    r['diff_lines'] = [d for d in diff if d.startswith(('-', '+')) and not d.startswith(('---', '+++'))]

    ok = all([
        r['sha_changed'], r['first_line_ok'], r['last_line_ok'], r['line_count_equal'],
        r['cjk_min_3200'], r['changed_lines_within_scope'], r['changed_count'] == 4,
        r['old_hits_zeroed'], r['hard_zero_ok'], r['banned_char_classes_zero'],
    ])
    r['verdict'] = 'PASS' if ok else 'FAIL'
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
