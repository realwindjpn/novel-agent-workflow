#!/usr/bin/env python3
"""第122章编辑写后复审 - xiaomi/mimo-v2.5-pro"""
import json, os, sys, yaml
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
CANDIDATE = BASE / '审核记录/自循环体系会议_20260530/ch122_author_refined_mimo.md'
SUMMARY = BASE / '审核记录/自循环体系会议_20260530/ch122_author_refined_mimo_summary.md'
PREREVIEW = BASE / '审核记录/自循环体系会议_20260530/ch122_editor_prereview_mimo.md'
OUT = BASE / '审核记录/自循环体系会议_20260530/ch122_editor_postreview_mimo.md'

candidate = CANDIDATE.read_text()
summary = SUMMARY.read_text() if SUMMARY.exists() else ''
prereview = PREREVIEW.read_text() if PREREVIEW.exists() else ''

prompt = f"""你是《科武纪元》编辑复审角色。模型：xiaomi/mimo-v2.5-pro。

任务：对第122章候选稿做写后编辑复审。

=== 修改说明 ===
{summary[:2000]}

=== 原编辑外审 ===
{prereview[:2000]}

=== 候选稿全文 ===
{candidate}

复审要点：
1. 核对P1必改项是否落实：结尾钩子增强、U-19阈值一致性、AI自主性下调、量子传感表述明确、地理时间线修复
2. 结构/节奏：章节功能是否完成
3. 去AI味：解释腔、口号化、文艺比喻
4. 章末钩子是否成立

首行 PASS 或 FAIL。列证据。≤1000字。"""

with open('/root/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
api_key = cfg['providers']['xiaomi']['api_key']
base_url = 'https://token-plan-cn.xiaomimimo.com/v1'

import urllib.request
body = json.dumps({"model": "mimo-v2.5-pro", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096, "temperature": 0.3}).encode()
req = urllib.request.Request(f"{base_url}/chat/completions", data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, method="POST")

try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
        content = data['choices'][0]['message']['content']
        OUT.write_text(f"# 第122章编辑写后复审\n\n模型：xiaomi/mimo-v2.5-pro\n时间：2026-05-31\n\n---\n\n{content}\n")
        print(f"Result: {content[:10].strip()}")
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
