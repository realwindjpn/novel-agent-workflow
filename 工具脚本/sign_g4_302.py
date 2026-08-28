#!/usr/bin/env python3
"""解 302 依赖并签发 G4_RELEASE_302.json。301 已定稿，依赖可解。"""
import json
import pathlib
import hashlib
import datetime

TASK = pathlib.Path('/root/workspace/科武纪元/任务运行态/20260828_kewu_selfcycle_daily')
OUT = TASK / 'output'
KEWU = pathlib.Path('/root/workspace/科武纪元')

# 301 定稿证据
body301 = (OUT / 'qwen_301_r4_clean.md').read_text(encoding='utf-8')
sha301 = hashlib.sha256(body301.encode()).hexdigest()

g3 = json.loads((OUT / 'G3_prep.json').read_text(encoding='utf-8'))
c302 = g3['chapters']['302']

# 解依赖
c302['depends_on']['final_sha256'] = sha301
c302['depends_on']['state'] = 'FINALIZED_WRITTEN_BACK'
c302['state'] = 'PREP_COMPLETE_AWAITING_G4'
c302['pending_reason'] = None
(OUT / 'G3_prep.json').write_text(
    json.dumps(g3, ensure_ascii=False, indent=1), encoding='utf-8')
print('G3 302 state ->', c302['state'])
print('G3 302 depends ->', c302['depends_on'])

# 301 交棒锁定状态（从 301 G3 包读，若有）
c301 = g3['chapters'].get('301', {})
handoff = c301.get('handoff_to_302_locked_state', [
    '火星防御联盟已成立，章程确立技术共享原则：共享核查方法、观测口径与时序基准，不共享遗迹本体接入权。',
    '值守机制落地：轮值席位、双人在位、封签交接、观测同步窗口、任何一方不得单独接入。',
    '主战派签名链被联盟章程第十一条程序性冻结，马库斯·维尔授权链在火星失去本地效力；拒绝执行派以观察员身份入场。',
    '缺口一百四十千瓦未消，L1 阵列授权仍卡在泛际会议，三一九开尔文硬线未变。',
    '遗迹机制、权限与边界仍未知；联盟保障的是能源/算力/制造三段链路不被单一方切断。',
    '宪章层表决尚未发生，常设监督机构尚未设立——本章（302）承接。',
])

release = {
    'chapter': 302,
    'title': c302['title'],
    'outline_ref': c302.get('outline_ref'),
    'outline_raw': c302.get('outline_raw'),
    'signed_at': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    'run_id': g3.get('run_id'),
    'gate_chain': {
        'G1': {'ref': 'output/G1_material_match.json', 'state': 'DONE'},
        'G2': {'ref': 'output/G2_verdict.json', 'verdict': c302.get('g2_verdict'), 'state': 'DONE'},
        'G3': {'ref': 'output/G3_prep.json', 'state': 'PREP_COMPLETE'},
        'DAILY_DIGEST': {'ref': 'output/DAILY_DIGEST_COMPLETE.json', 'date': '2026-08-28'},
    },
    'depends_on': {
        'chapter': 301,
        'final_sha256': sha301,
        'state': 'FINALIZED_WRITTEN_BACK',
        'evidence': [
            '已投稿/第301章.txt',
            '新版/第301章.md',
            'output/VERIFY_301_R4.json (VERIFY_PASS)',
            'output/CLOSE_LOOP_301.json (CLOSE_LOOP_TXT_READY)',
            'output/reviews_301_r4/ (4 seats all PASS)',
            'git 0f742d0bf',
        ],
    },
    'handoff_from_301_locked_state': handoff,
    'plot': c302.get('plot'),
    'role_boundaries': c302.get('role_boundaries'),
    'forbidden': c302.get('forbidden'),
    'author_hard_gate': c302.get('author_hard_gate'),
    'author_seat': {
        'type': 'web_qwen_project',
        'project_url': 'https://chat.qwen.ai/p/18dab9a0-fea0-490f-abc2-aff83b85ee04',
        'model': 'qwen3.8-max',
        'rule': '每章新建对话，禁复用旧会话；--cdp-url "" 冷启动 + 3 次重试',
    },
    'review_seats_forbidden_family': [
        'claude-opus-5 (主控同族：sotamodel / gorouter-opus5 均禁)',
    ],
    'state': 'SIGNED',
}

p = OUT / 'G4_RELEASE_302.json'
p.write_text(json.dumps(release, ensure_ascii=False, indent=1), encoding='utf-8')
print('signed', p)

# 回读验真
back = json.loads(p.read_text(encoding='utf-8'))
print('verify state:', back['state'])
print('verify dep sha:', back['depends_on']['final_sha256'][:16], '==', sha301[:16])
print('verify hard_gate first_line:', back['author_hard_gate'].get('first_line'))
print('verify cjk target:', back['author_hard_gate'].get('net_cjk_target'))
assert back['state'] == 'SIGNED'
assert back['depends_on']['final_sha256'] == sha301
print('G4_302_SIGNED_OK')
