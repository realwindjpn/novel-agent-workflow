#!/usr/bin/env python3
"""302 补写稿验收：字数达标 + 禁词清零 + 硬数字守恒 + 剧情不越界 + 拉丁受限。"""
import pathlib
import re
import json
import hashlib
import sys

D = pathlib.Path('/root/workspace/科武纪元/任务运行态/20260828_kewu_selfcycle_daily/output')
RAW = D / 'qwen_302_aug_raw.md'
CLEAN = D / 'qwen_302_aug_clean.md'
BASE = D / 'qwen_302_a2_short_2371.md'

base = BASE.read_text(encoding='utf-8')

if CLEAN.exists() and CLEAN.stat().st_size > 0:
    t = CLEAN.read_text(encoding='utf-8')
else:
    t = RAW.read_text(encoding='utf-8')
    lines = t.split('\n')
    NOISE = ('', '好的', '以下是修改后的正文', 'Thinking completed', '已经完成思考')
    while lines and lines[0].strip() in NOISE:
        lines.pop(0)
    t = '\n'.join(lines).strip() + '\n'
    t = re.sub(r'^#+\s*', '', t, flags=re.M)
    t = re.sub(r'\*\*', '', t)
    CLEAN.write_text(t, encoding='utf-8')

paras = [l.strip() for l in t.split('\n') if l.strip()]
cjk = len(re.findall(r'[\u4e00-\u9fff]', t))
base_cjk = len(re.findall(r'[\u4e00-\u9fff]', base))

BAN = ['真正', '核心', '关键', '意味着', '赋能', '生态闭环', '本质', '值得关注', '维度', '格局']
ban_hit = [b for b in BAN if b in t]

HARD_NUM = ['一百八十二票', '七票反对', '三票弃权', '四十二条', '一百四十千瓦',
            '九百四十九千瓦', '三轮闭门谈判', '泛际会议太空技术监督委员会']
num_missing = [n for n in HARD_NUM if n not in t]

formula = re.findall(r'不是[^。；\n]{0,20}[，,]?\s*(?:而)?是', t)
lat = sorted(set(re.findall(r'[A-Za-z]+\d*', t)))
lat_bad = [x for x in lat if x not in ('L1', 'CTC', 'L')]

FORBID_PLOT = ['第一环组装启动', '戴森环开工', '星火集', '第七层压域', '并网成功']
plot_hit = [b for b in FORBID_PLOT if b in t]

MD = ['##', '- ', '* ', '**', '1. ']
md_hit = [m for m in MD if any(l.startswith(m) for l in paras)]

gates = {
    'cjk_min_3200': cjk >= 3200,
    'cjk_in_target_3400_3600': 3400 <= cjk <= 3600,
    'cjk_grew': cjk > base_cjk,
    'no_banned_word': not ban_hit,
    'hard_numbers_kept': not num_missing,
    'no_formula': not formula,
    'latin_restricted': not lat_bad,
    'no_plot_violation': not plot_hit,
    'first_line_ok': paras[0] == '第302章 戴森共识',
    'last_line_ok': paras[-1] == '（本章完）',
    'no_markdown': not md_hit,
    'no_author_note': '作者有话说' not in t,
}

print('=== 302 补写验收 ===')
for k, v in gates.items():
    print(('OK  ' if v else 'FAIL'), k)
print()
print('CJK %d -> %d (硬线 3200，目标 3400-3600)' % (base_cjk, cjk))
print('段数 %d' % len(paras))
print('首行:', paras[0])
print('末行:', paras[-1])
if ban_hit:
    print('!! 禁词:', ban_hit)
if num_missing:
    print('!! 硬数字缺失:', num_missing)
if formula:
    print('!! 公式句:', formula[:3])
if lat_bad:
    print('!! 越界拉丁:', lat_bad)
if plot_hit:
    print('!! 剧情越界:', plot_hit)
if md_hit:
    print('!! Markdown:', md_hit)

sha = hashlib.sha256(t.encode()).hexdigest()
print('\nSHA:', sha)

ok = all(gates.values())
# 目标区间未达但过硬线，标 SOFT_PASS
soft = (not gates['cjk_in_target_3400_3600']) and gates['cjk_min_3200'] and \
    all(v for k, v in gates.items() if k != 'cjk_in_target_3400_3600')
verdict = 'AUG_PASS' if ok else ('AUG_SOFT_PASS_BELOW_TARGET' if soft else 'AUG_FAIL')
json.dump({'gates': gates, 'cjk': cjk, 'base_cjk': base_cjk, 'paras': len(paras),
           'sha256': sha, 'banned': ban_hit, 'num_missing': num_missing,
           'verdict': verdict},
          open(D / 'VERIFY_302_AUG.json', 'w'), ensure_ascii=False, indent=1)
print('\nVERDICT', verdict)
sys.exit(0 if ok or soft else 1)
