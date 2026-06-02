#!/usr/bin/env python3
"""第122章科学外审 - xiaomi/mimo-v2.5-pro (zai/glm no key)"""
import json, os, sys, yaml
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
SOURCE = BASE / '新版/第122章.md'
OUT = BASE / '审核记录/自循环体系会议_20260530/ch122_science_prereview_mimo.md'

source = SOURCE.read_text()

prompt = f"""你是《科武纪元》科学/军事顾问外审角色。模型：xiaomi/mimo-v2.5-pro。

任务：对第122章源稿做科学/军事技术外审。

=== 第122章源稿全文 ===
{source}

外审要点：
1. 科学概念/技术设定是否有硬伤？
2. 军事/战术/装备表述是否可信？
3. AI/量子/电磁/航天表述是否合理？
4. 地理/距离/时间线是否自洽？
5. 列出问题与行号

输出格式：
首行 PASS 或 FAIL。
列具体技术问题。
用中文，≤1000字。"""

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
        report = f"# 第122章科学/军事外审报告\n\n审核模型：xiaomi/mimo-v2.5-pro\n审核时间：2026-05-31\n源稿：新版/第122章.md\n\n---\n\n{content}\n"
        OUT.write_text(report)
        print(f"PASS/FAIL: {content[:10].strip()}")
        sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    OUT.write_text(f"# 科学外审失败\n\n{e}\n")
    sys.exit(1)
