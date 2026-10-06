# -*- coding: utf-8 -*-
"""G2 席位真实负载重测（2026-10-07）。

触发：500 章融纲会议 7 席里 3 席异常
  - 中文文风 hiyo/gpt-6-luna   → HTTP 400 upstream error
  - 编辑/连续性 sensenova2/dsv4-flash → 空回包（ok=True 但 raw 为空）
  - 海外新鲜度 agentrouter-dsv4/dsv4-flash → 空回包

教训（沿用 20261006 席位表）：存活性探针 ≠ 可用，必须跑真实负载。
方法：对候选 (provider, model) 用约 1200 字中文 prompt 实跑，
     要求首行 VERDICT 且正文 ≥120 字才算通过。
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, '/root/workspace/科武纪元/工具脚本')
from kewu_review_direct import PROVIDERS  # noqa: E402

PROMPT = """你是《科武纪元》500章大纲融纲会议的【中文文风与人味】审查席。

以下为第19章《稀有矿震》条目与 3 条候选素材：
- 第19章：全球新闻——中亚帕米尔高原发现超大型稀有稀土矿床，多国立即展开争夺。暗线：中国南天门计划需要这些矿物制造AI芯片和量子元件。
- 素材A：中国开启深空探测新航程（新华网）
- 素材B：我国生成式人工智能用户规模突破7亿人
- 素材C：深空资源开发利用"三步走"规划

请审查：素材若写入本章，中文表达上是否存在翻译腔、术语堆砌、机关公文味？如何改写才有人味？

严格按以下格式回包，首行必须是 VERDICT：
VERDICT: OUTLINE_PATCH 或 NOTE_ONLY 或 NO_PATCH

SUGGESTIONS:
- （至少2条具体建议，每条指出章节号与改写方向）

RISKS:
- （至少1条风险）
"""

MIN_CHARS = 120
TIMEOUT = 280

# 候选：优先同 provider 换模型，再换 provider
CANDIDATES = [
    # 中文文风席候选
    ('hiyo', 'gpt-6-luna'),
    ('hiyo', 'gpt-5.6-luna'),
    ('sensenova', 'glm-5.2'),
    ('sensenova2', 'glm-5.2'),
    ('onefor', 'gpt-5.6-terra'),
    # 编辑/连续性 + 海外新鲜度候选
    ('sensenova2', 'deepseek-v4-flash'),
    ('agentrouter-dsv4', 'deepseek-v4-flash'),
    ('sensenova', 'glm-5.2'),
    ('onefor', 'gpt-6-sol'),
    ('tokenrhythm-dsv4', 'deepseek-v4-flash-0731'),
]


def call(provider, model, timeout=TIMEOUT):
    if provider not in PROVIDERS:
        return {'ok': False, 'err': 'NO_PROVIDER'}
    base, env = PROVIDERS[provider]
    key = os.environ.get(env, '')
    if not key:
        return {'ok': False, 'err': 'NO_KEY %s' % env}
    import urllib.request
    payload = {'model': model, 'messages': [{'role': 'user', 'content': PROMPT}],
               'max_tokens': 1200, 'temperature': 0.2}
    req = urllib.request.Request(
        base.rstrip('/') + '/chat/completions',
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.loads(r.read().decode())
    except Exception as e:
        return {'ok': False, 'err': '%s %s' % (type(e).__name__, str(e)[:120]),
                'sec': round(time.time() - t0, 1)}
    sec = round(time.time() - t0, 1)
    try:
        txt = body['choices'][0]['message']['content'] or ''
    except Exception:
        return {'ok': False, 'err': 'NO_CHOICES %s' % json.dumps(body)[:150], 'sec': sec}
    txt = txt.strip()
    ok = bool(txt) and len(txt) >= MIN_CHARS and txt.upper().startswith('VERDICT')
    return {'ok': ok, 'sec': sec, 'chars': len(txt), 'text': txt[:200],
            'err': '' if ok else ('EMPTY' if not txt else 'SHORT_OR_NO_VERDICT')}


if __name__ == '__main__':
    print('真实负载重测（prompt %d 字，门槛 %d 字+首行VERDICT）'
          % (len(PROMPT), MIN_CHARS))
    print()
    results = []
    for prov, model in CANDIDATES:
        r = call(prov, model)
        flag = '✅' if r.get('ok') else '❌'
        print('%s %-18s %-24s %6ss %5s字 %s'
              % (flag, prov, model, r.get('sec', '-'), r.get('chars', '-'),
                 r.get('err', '')[:60]))
        if r.get('ok'):
            print('     ' + (r.get('text') or '').replace('\n', ' ')[:110])
        results.append({'provider': prov, 'model': model, **r})
        time.sleep(1)
    out = Path('/root/workspace/科武纪元/审核记录/G2_SEATS_REPROBE_20261007.json')
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf-8')
    print()
    ok = [r for r in results if r.get('ok')]
    print('可用 %d / %d → %s' % (len(ok), len(results), out))
