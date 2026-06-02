#!/usr/bin/env python3
"""第122章读者写后复审 - xiaomi/mimo-v2.5-pro (freemodel 503 fallback)"""
import json, os, sys, yaml
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
CANDIDATE = BASE / '审核记录/自循环体系会议_20260530/ch122_author_refined_mimo.md'
SUMMARY = BASE / '审核记录/自循环体系会议_20260530/ch122_author_refined_mimo_summary.md'
OUT = BASE / '审核记录/自循环体系会议_20260530/ch122_reader_postreview_mimo.md'

candidate = CANDIDATE.read_text()
summary = SUMMARY.read_text() if SUMMARY.exists() else ''

if len(candidate) > 12000:
    cand_prompt = candidate[:6000] + "\n\n[...中间省略...]\n\n" + candidate[-6000:]
else:
    cand_prompt = candidate

prompt = f"""你是《科武纪元》读者复审角色。模型：xiaomi/mimo-v2.5-pro (freemodel 503 fallback)。

任务：对第122章候选稿做写后读者复审。

=== 修改说明 ===
{summary[:1500]}

=== 候选稿（首尾+关键段）===
{cand_prompt}

复审要点：
1. 追读意愿1-5分
2. 卡顿/无聊/解释腔段落
3. 人物口吻自然度
4. 章末钩子是否成立
5. AI味检查

首行 PASS 或 FAIL。≤800字。"""

with open('/root/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
api_key = cfg['providers']['xiaomi']['api_key']
base_url = 'https://token-plan-cn.xiaomimimo.com/v1'

import urllib.request
body = json.dumps({"model": "mimo-v2.5-pro", "messages": [{"role": "user", "content": prompt}], "max_tokens": 3072, "temperature": 0.3}).encode()
req = urllib.request.Request(f"{base_url}/chat/completions", data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, method="POST")

try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
        content = data['choices'][0]['message']['content']
        OUT.write_text(f"# 第122章读者写后复审\n\n模型：xiaomi/mimo-v2.5-pro (freemodel 503 fallback)\n时间：2026-05-31\n\n---\n\n{content}\n")
        print(f"Result: {content[:10].strip()}")
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
