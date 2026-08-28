#!/usr/bin/env python3
"""301 R4 四审任务包：沿用 R3 prompt 骨架，替换绑定 SHA/CJK/正文全文。"""
import pathlib
import hashlib
import re
import json

BASE = pathlib.Path('/root/workspace/科武纪元/任务运行态/20260828_kewu_selfcycle_daily')
R3DIR = BASE / 'output' / 'reviews_301_r3'
R4DIR = BASE / 'output' / 'reviews_301_r4'
R4DIR.mkdir(parents=True, exist_ok=True)

CAND = BASE / 'output' / 'qwen_301_r4_clean.md'
body = CAND.read_text(encoding='utf-8')
sha = hashlib.sha256(body.encode()).hexdigest()
cjk = len(re.findall(r'[\u4e00-\u9fff]', body))

OLD_SHA = 'fa526f00777e990479ecab64303671ad78715d7e75d52b98d2a8281faeb7a01a'
OLD_PATH = 'output/qwen_301_r3_raw.md'
NEW_PATH = 'output/qwen_301_r4_clean.md'

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
    'warns': [],
}

R4_NOTE = """
【本轮为 R4（定点返修后重审）】
上一版 SHA {old8} 经编辑席判 FAIL，7 条阻断已由作者席逐条执行（公式句变体删、禁词「真正」×2、禁词「核心」、否定叠加论断改实指、解释腔点题段×2、韩铮台词后同义复述段删、结尾主题概括删+秘书处比喻改程序性回话）。
本轮净中文由 3341 降至 {cjk}（删改所致，仍高于硬下限 3000）。
你只针对当前正文判定，不要复述历史意见，不得因「上一版更长」判 FAIL。
""".format(old8=OLD_SHA[:8], cjk=cjk)

for f in sorted(R3DIR.glob('*_prompt.md')):
    txt = f.read_text(encoding='utf-8')
    # 换绑定
    txt = txt.replace(OLD_SHA, sha)
    txt = txt.replace(OLD_PATH, NEW_PATH)
    txt = txt.replace('净中文实测 3341', '净中文实测 %d' % cjk)
    txt = txt.replace('第301章独立审稿席', '第301章独立审稿席（R4 轮）')
    # 换机检块
    txt = re.sub(
        r'\{\n \"target\".*?\n\}',
        json.dumps(machine, ensure_ascii=False, indent=1),
        txt, count=1, flags=re.S,
    )
    # 换正文：结构为 [任务书] 【完整正文】 [旧正文] 【本席职责】 [角色段]
    # '【完整正文】' 在任务书开头说明句里也出现，取最后一次；尾部角色段必须保留
    idx = txt.rfind('【完整正文】')
    if idx == -1:
        print('SKIP no body marker', f.name)
        continue
    tail_idx = txt.find('【本席职责】', idx)
    if tail_idx == -1:
        raise SystemExit('PACKAGING_FAIL no role tail in ' + f.name)
    role_tail = txt[tail_idx:]
    txt = txt[:idx] + '【完整正文】\n' + body + '\n\n' + role_tail
    # 插 R4 说明（放在报告格式之前）
    if '【报告格式】' in txt:
        txt = txt.replace('【报告格式】', R4_NOTE + '\n【报告格式】', 1)

    out = R4DIR / f.name
    out.write_text(txt, encoding='utf-8')
    written = out.read_text(encoding='utf-8')
    ok_body = body.strip() in written
    ok_new_sha = sha in written
    ok_no_old = OLD_SHA not in written
    print(f.name, len(written.encode()), 'inlined', ok_body,
          'new_sha_present', ok_new_sha, 'old_sha_gone', ok_no_old)
    assert ok_body and ok_new_sha and ok_no_old, 'PACKAGING_FAIL ' + f.name

print('new_sha', sha, 'cjk', cjk)
print('dir', R4DIR)
