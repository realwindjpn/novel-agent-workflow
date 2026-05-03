#!/usr/bin/env python3
"""作者模型对比测试：qwen3.6-plus vs MiniMax-M2.7 vs mimo-v2.5"""

from pathlib import Path
import re, yaml, requests, os, json, time

env_path = Path.home() / '.hermes' / '.env'
if env_path.exists():
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

ch = 91
proj = Path('/root/workspace/科武纪元')
text = (proj / '待确认投稿' / f'第{ch}章改.txt').read_text(encoding='utf-8', errors='ignore')

AUTHORS = {
    'qwen3.6-plus':   {'provider': 'alibaba',   'base_url': 'https://coding.dashscope.aliyuncs.com/v1', 'key_env': 'DASHSCOPE_API_KEY'},
    'MiniMax-M2.7':   {'provider': 'minimax-cn', 'base_url': 'https://api.minimaxi.com/v1',             'key_env': 'MINIMAX_CN_API_KEY'},
    'mimo-v2.5':      {'provider': 'xiaomi',     'base_url': 'https://token-plan-cn.xiaomimimo.com/v1',  'key_env': 'XIAOMI_API_KEY'},
}

prompt = f'''你是《科武纪元》作者。改写第91章《南部海域再战》。只输出正文。

*** 字数硬约束：全文必须 3200-5200 中文字。不足3200字视为不合格。
展开方法：每个动作节点补充物理反馈/环境细节/角色反应；对话穿插动作和感官描写；战术/技术环节写清操作步骤和结果验证。禁止用一句话概括本应展开的场景。

首行：第91章 南部海域再战
末行：（本章完）
不得解释，不得输出正文外任何内容。

V8锚点：第二卷《南部海域再战》。南部海域封锁被撕开后并未安静，苏雨晴指挥后续清剿战。
上章承接：承接第90章行动后果。
本章必须发生：写出清剿代价、无人艇反制、海上秩序重建；虚化真实国名。
禁止发生：不提前解决后续谜题；不写成报告；不靠口号推进。
章末钩子：海底矿物开采权回归联合政府管理，牵引第92章盐滩计划。
风格：物理反馈/行动链/短句；禁文艺比喻；技术解释进入动作。

原版全文：
{text[:6000]}
'''

results = {}
for name, cfg in AUTHORS.items():
    key = os.environ.get(cfg['key_env'], '')
    if not key:
        print(f'{name}: SKIP (no key)')
        continue
    print(f'\n▶ {name} 写作中...', flush=True)
    t0 = time.time()
    try:
        r = requests.post(cfg['base_url']+'/chat/completions',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'model': name, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 10000, 'temperature': 0.3},
            timeout=360)
        elapsed = time.time() - t0
        if not r.ok:
            print(f'{name}: FAIL {r.status_code} {r.text[:200]}')
            continue
        data = r.json()
        content = (data.get('choices') or [{}])[0].get('message', {}).get('content', '')
        usage = (data.get('usage') or {})
        content = content.strip()
        content = re.sub(r'^```(?:txt|md)?\s*', '', content).strip()
        content = re.sub(r'\s*```$', '', content).strip()
        if not content.splitlines() or not content.splitlines()[0].startswith(f'第{ch}章'):
            content = f'第{ch}章 南部海域再战\n\n' + content
        cn = len(re.findall(r'[\u4e00-\u9fff]', content))
        print(f'{name}: {elapsed:.0f}s | {cn}中文字 | {usage.get("total_tokens", "?")}tokens | {content[:120]}...')
        results[name] = {
            'chars': cn, 'elapsed': round(elapsed, 1),
            'tokens': usage.get('total_tokens', 0),
            'preview': content[:300],
            'full': content
        }
    except Exception as e:
        print(f'{name}: ERROR {e}')

print('\n=== 对比汇总 ===')
for name, r in results.items():
    print(f'{name}: {r["chars"]}字, {r["elapsed"]}s, {r["tokens"]}tokens')

# 保存结果
for name, r in results.items():
    out_path = proj / f'test/作者对比_91_{name}.txt'
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(r['full'], encoding='utf-8')
