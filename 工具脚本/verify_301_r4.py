#!/usr/bin/env python3
"""301 R4 回收验收：首尾锚点、CJK、SHA、10 处修复命中、diff 越界核查。"""
import pathlib
import hashlib
import re
import difflib
import json
import sys

BASE = pathlib.Path('/root/workspace/科武纪元/任务运行态/20260828_kewu_selfcycle_daily')
SRC = BASE / 'output' / 'qwen_301_r3_raw.md'
NEW = BASE / 'output' / 'qwen_301_r4_raw.md'

src = SRC.read_text(encoding='utf-8')
raw = NEW.read_text(encoding='utf-8')

# sanitize：剥首行 markdown 标记与 Thinking completed 残留，与源稿格式对齐
lines = raw.split('\n')
while lines and lines[0].strip() in ('', 'Thinking completed', '已经完成思考'):
    lines.pop(0)
if lines:
    lines[0] = re.sub(r'^#+\s*', '', lines[0])
clean = '\n'.join(lines)
if not clean.endswith('\n'):
    clean += '\n'

CLEANP = BASE / 'output' / 'qwen_301_r4_clean.md'
CLEANP.write_text(clean, encoding='utf-8')


def cjk(t):
    return len(re.findall(r'[\u4e00-\u9fff]', t))


src_cjk, new_cjk = cjk(src), cjk(clean)
src_sha = hashlib.sha256(src.encode()).hexdigest()
new_sha = hashlib.sha256(clean.encode()).hexdigest()
nonempty = [l for l in clean.split('\n') if l.strip()]

# 10 处修复：(编号, 旧写法必须归零, 新写法必须存在或 None)
FIX_CHECKS = [
    ('1 公式句删', '靠的从来都不是互信，是算清楚了独占的代价比联合的代价大得多', '各方最终坐到了同一张桌上。'),
    ('2a 禁词真正', '真正让所有人同时安静下来', '最后一条底线让所有人同时停了口'),
    ('2b 禁词真正', '真正的问题还压在桌上', '桌上还压着一条没动'),
    ('3 禁词核心', '但核心诉求一致', '但要的是同一件事'),
    ('4 否定叠加', '那就不再是一个工程问题，也不只是一个程序问题', '一次否决就能停掉整条链路的下一步'),
    ('5a 三段链路点题删', '章程保障的就是这件事', '任何一只手不能同时掐住两段以上'),
    ('5b 开篇排比并入引文', '谁单独承担保护责任，谁就单独承担误判的全部后果', '三项均无权限说明'),
    ('6 同义复述段删', '也不打算假装证明得了', None),
    ('7a 没有人赢删', '没有人赢', None),
    ('7b 秘书处比喻改', '门不在本议程的授权范围里，尺子的刻度可以公开', '本议程的授权范围不含接入权限'),
]

results = []
for name, old, new in FIX_CHECKS:
    old_gone = old not in clean
    new_ok = True if new is None else (new in clean)
    ok = old_gone and new_ok
    results.append({'fix': name, 'old_gone': old_gone, 'new_present': new_ok, 'pass': ok})

# 硬门禁
banned_words = ['真正', '核心', '关键', '意味着', '赋能', '生态闭环']
banned_hit = [w for w in banned_words if w in clean]
formula = ['不是', '而是']
formula_pair = bool(re.search(r'不是[^。；\n]{0,30}而是', clean))

gates = {
    'first_line': nonempty[0] == '第301章 联合防御' if nonempty else False,
    'last_line': nonempty[-1] == '（本章完）' if nonempty else False,
    'cjk_min_3000': new_cjk >= 3000,
    'sha_changed': new_sha != src_sha,
    'no_markdown': not re.search(r'^\s*[#*\-] ', clean, re.M),
    'no_numbered_prefix': len(re.findall(r'^\d+\|', clean, re.M)) == 0,
    'no_banned_words': not banned_hit,
    'no_formula_pattern': not formula_pair,
    'no_chapter_selfref': not re.search(r'第[一二三四五六七八九十百零\d]+章', clean.replace('第301章 联合防御', '', 1)),
}

# diff 越界
sl = src.split('\n')
nl = clean.split('\n')
diff = list(difflib.unified_diff(sl, nl, lineterm='', n=0))
changed_src = []
for d in diff:
    if d.startswith('@@'):
        m = re.match(r'@@ -(\d+)(?:,(\d+))? \+', d)
        if m:
            changed_src.append(int(m.group(1)))

report = {
    'src_path': str(SRC), 'src_sha256': src_sha, 'src_cjk': src_cjk, 'src_lines': len(sl),
    'new_path': str(CLEANP), 'new_sha256': new_sha, 'new_cjk': new_cjk, 'new_lines': len(nl),
    'cjk_delta': new_cjk - src_cjk,
    'gates': gates,
    'fixes': results,
    'banned_word_hits': banned_hit,
    'changed_src_line_positions': changed_src,
    'diff_hunk_count': len(changed_src),
    'first_line': nonempty[0] if nonempty else '',
    'last_line': nonempty[-1] if nonempty else '',
}
all_fix = all(r['pass'] for r in results)
all_gate = all(gates.values())
report['verdict'] = 'VERIFY_PASS' if (all_fix and all_gate) else 'VERIFY_FAIL'

OUTJ = BASE / 'output' / 'VERIFY_301_R4.json'
OUTJ.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')

for k, v in gates.items():
    print(('OK  ' if v else 'FAIL'), k)
for r in results:
    print(('OK  ' if r['pass'] else 'FAIL'), r['fix'], 'old_gone=', r['old_gone'], 'new=', r['new_present'])
print('cjk', src_cjk, '->', new_cjk, 'delta', new_cjk - src_cjk)
print('lines', len(sl), '->', len(nl))
print('diff hunks', len(changed_src), changed_src)
print('new_sha', new_sha)
print('VERDICT', report['verdict'])
print('saved', OUTJ)
sys.exit(0 if report['verdict'] == 'VERIFY_PASS' else 1)
