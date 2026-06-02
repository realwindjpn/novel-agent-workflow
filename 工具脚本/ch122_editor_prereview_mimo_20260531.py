#!/usr/bin/env python3
"""第122章编辑外审 - xiaomi/mimo-v2.5-pro"""
import json, os, sys, yaml
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
SOURCE = BASE / '新版/第122章.md'
OUT = BASE / '审核记录/自循环体系会议_20260530/ch122_editor_prereview_mimo.md'

source = SOURCE.read_text()

# Read outline context for ch122
outline = BASE / 'wiki/raw/outline/科武纪元大纲_latest.md'
outline_text = outline.read_text() if outline.exists() else 'N/A'
# Extract ch122 line
ch122_outline = [l for l in outline_text.split('\n') if '122' in l and ('章' in l or '第122' in l)]
outline_ctx = '\n'.join(ch122_outline[:5]) if ch122_outline else '未找到122章大纲行'

prompt = f"""你是《科武纪元》编辑外审角色。模型：xiaomi/mimo-v2.5-pro。

任务：对第122章源稿做原文外审。

=== 大纲上下文（122章相关）===
{outline_ctx}

=== 第122章源稿全文 ===
{source}

外审要点：
1. 是否偏纲？章节功能是否完成？
2. 节奏/钩子问题
3. 信息密度是否合理
4. 去AI味：解释腔、口号化、文艺比喻
5. 列出必改项≤5条（P0/P1/P2分级）

输出格式：
首行 PASS 或 FAIL。
列具体问题与行号。
用中文，≤1200字。"""

# Xiaomi API
with open('/root/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
xiaomi_cfg = cfg.get('providers', {}).get('xiaomi', {})
api_key = xiaomi_cfg.get('api_key', '')
base_url = 'https://token-plan-cn.xiaomimimo.com/v1'

import urllib.request
messages = [{"role": "user", "content": prompt}]
body = json.dumps({"model": "mimo-v2.5-pro", "messages": messages, "max_tokens": 4096, "temperature": 0.3}).encode()
req = urllib.request.Request(f"{base_url}/chat/completions", data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, method="POST")

try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
        content = data['choices'][0]['message']['content']
        report = f"# 第122章编辑外审报告\n\n审核模型：xiaomi/mimo-v2.5-pro\n审核时间：2026-05-31\n源稿：新版/第122章.md\n\n---\n\n{content}\n"
        OUT.write_text(report)
        print(f"PASS/FAIL: {content[:10].strip()}")
        sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    OUT.write_text(f"# 编辑外审失败\n\n{e}\n")
    sys.exit(1)
