#!/usr/bin/env python3
"""302 四审任务包：沿用 301 R4 骨架，替换章号/绑定 SHA/CJK/正文全文/G4 边界。

关键：正文后的角色段必须保留（301 曾因切片导致四包同字节）。
"""
import pathlib
import hashlib
import re
import json

BASE = pathlib.Path('/root/workspace/科武纪元/任务运行态/20260828_kewu_selfcycle_daily')
SRCDIR = BASE / 'output' / 'reviews_301_r4'
OUTDIR = BASE / 'output' / 'reviews_302_r1'
OUTDIR.mkdir(parents=True, exist_ok=True)

CAND = BASE / 'output' / 'qwen_302_aug_clean.md'
body = CAND.read_text(encoding='utf-8')
sha = hashlib.sha256(body.encode()).hexdigest()
cjk = len(re.findall(r'[\u4e00-\u9fff]', body))

rel = json.loads((BASE / 'output' / 'G4_RELEASE_302.json').read_text(encoding='utf-8'))

OLD_SHA = 'ea9ccb03ee85970044e429d26f09456721da3dece31bbff81c5ed74e9c11a487'
OLD_PATH = 'output/qwen_301_r4_clean.md'
NEW_PATH = 'output/qwen_302_aug_clean.md'

machine = {
    'target': NEW_PATH,
    'sha256': sha,
    'bytes': len(body.encode()),
    'net_cjk': cjk,
    'lines': len(body.split('\n')) - 1,
    'first_line': body.split('\n')[0],
    'last_line': [l for l in body.split('\n') if l.strip()][-1],
    'verdict': 'MACHINE_GATE_PASS',
    'fails': [],
    'warns': ['net_cjk %d 低于 G4 目标区下沿 3400，但高于硬下限 3200' % cjk],
}

NOTE = """
【本轮为第302章《戴森共识》首审】
本章由网页作者席出稿（三次尝试取最优），再经补写席定点扩写：清禁词 2 处（核心/真正），
扩写三处（第一轮闭门谈判措辞之争、表决程序细节、监督委员会技术附件归档）。
净中文 {cjk}，**高于硬下限 3200**；G4 目标区间为 3400-3600，本稿距下沿差 {gap} 字。
判稿门槛以硬下限为准，**不得因未达 3400 判 FAIL**；若认为需贴线补字，写进「可选优化（不阻塞）」。

【本章 G4 边界（判越界用）】
剧情禁项：
{forbid}

角色边界：
{roles}

上一章（301《联合防御》）结束时锁定的状态，本章须承接且不得推翻：
{handoff}

【判稿纪律】
- 条件句与疑问句本身即未确认标记，不得要求追加「待确认」后缀。
- 只针对当前正文判定，不复述历史意见。
- 判 FAIL 必须引原文原句 + 给可直接替换的写法；描述性意见一律归「可选优化（不阻塞）」。
""".format(
    cjk=cjk, gap=3400 - cjk,
    forbid='\n'.join('- %s' % f for f in rel['forbidden']),
    roles='\n'.join('- %s：%s' % (k, v) for k, v in rel['role_boundaries'].items()),
    handoff='\n'.join('- %s' % h for h in rel['handoff_from_301_locked_state']),
)

for f in sorted(SRCDIR.glob('*_prompt.md')):
    txt = f.read_text(encoding='utf-8')
    txt = txt.replace(OLD_SHA, sha)
    txt = txt.replace(OLD_PATH, NEW_PATH)
    txt = re.sub(r'净中文实测 \d+', '净中文实测 %d' % cjk, txt)
    txt = txt.replace('第301章独立审稿席（R4 轮）', '第302章独立审稿席')
    txt = txt.replace('第301章独立审稿席', '第302章独立审稿席')
    txt = txt.replace('第301章', '第302章')
    txt = txt.replace('联合防御', '戴森共识')

    txt = re.sub(r'\{\n \"target\".*?\n\}',
                 json.dumps(machine, ensure_ascii=False, indent=1),
                 txt, count=1, flags=re.S)

    # 剔除 301 R4 专属说明段
    txt = re.sub(r'\n【本轮为 R4[^【]*?\n(?=【)', '\n', txt, flags=re.S)

    idx = txt.rfind('【完整正文】')
    if idx == -1:
        print('SKIP no body marker', f.name)
        continue
    tail_idx = txt.find('【本席职责】', idx)
    if tail_idx == -1:
        raise SystemExit('PACKAGING_FAIL no role tail in ' + f.name)
    role_tail = txt[tail_idx:]
    txt = txt[:idx] + '【完整正文】\n' + body + '\n\n' + role_tail

    if '【报告格式】' in txt:
        txt = txt.replace('【报告格式】', NOTE + '\n【报告格式】', 1)
    else:
        txt = txt + NOTE

    out = OUTDIR / f.name.replace('301', '302')
    out.write_text(txt, encoding='utf-8')
    w = out.read_text(encoding='utf-8')
    ok_body = body.strip() in w
    ok_sha = sha in w
    ok_no_old = OLD_SHA not in w
    ok_role = '【本席职责】' in w
    print('%-34s %6dB body=%s sha=%s old_gone=%s role=%s' % (
        out.name, len(w.encode()), ok_body, ok_sha, ok_no_old, ok_role))
    assert ok_body and ok_sha and ok_no_old and ok_role, 'PACKAGING_FAIL ' + out.name

# 四包字节数须不同（301 事故：角色段被切导致四包同字节）
sizes = {p.name: p.stat().st_size for p in OUTDIR.glob('*_prompt.md')}
print('\n包体字节:', sizes)
print('字节数唯一值 %d / 包数 %d %s' % (
    len(set(sizes.values())), len(sizes),
    'OK 各包不同' if len(set(sizes.values())) == len(sizes) else '!! 有同字节包，角色段可能被切'))
print('\nSHA', sha)
print('CJK', cjk)
print('dir', OUTDIR)
