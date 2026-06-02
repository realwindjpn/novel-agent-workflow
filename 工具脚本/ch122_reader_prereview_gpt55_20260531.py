#!/usr/bin/env python3
"""第122章读者外审 - freemodel/gpt-5.5"""
import json, os, sys
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
SOURCE = BASE / '新版/第122章.md'
OUT = BASE / '审核记录/自循环体系会议_20260530/ch122_reader_prereview_gpt55.md'

source = SOURCE.read_text()

prompt = f"""你是《科武纪元》读者外审角色。模型：freemodel/gpt-5.5。

任务：对第122章源稿做原文读者外审。

=== 第122章源稿全文 ===
{source}

外审要点：
1. 作为真实读者：读完想不想看下一章？（追读意愿1-5分）
2. 哪些段落卡顿/无聊/解释腔？
3. 人物口吻是否自然？
4. 章末钩子是否成立？
5. AI味检查：排比口号、文艺比喻、说明腔

输出格式：
首行 PASS 或 FAIL。
追读意愿评分。
具体卡顿点。
用中文，≤800字。"""

api_key = os.environ['FREEMODEL_API_KEY']
base_url = 'https://api.freemodel.dev/v1'

import urllib.request
messages = [{"role": "user", "content": prompt}]
body = json.dumps({"model": "gpt-5.5", "messages": messages, "max_tokens": 3072, "temperature": 0.3}).encode()
req = urllib.request.Request(f"{base_url}/chat/completions", data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, method="POST")

try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
        content = data['choices'][0]['message']['content']
        report = f"# 第122章读者外审报告\n\n审核模型：freemodel/gpt-5.5\n审核时间：2026-05-31\n源稿：新版/第122章.md\n\n---\n\n{content}\n"
        OUT.write_text(report)
        print(f"PASS/FAIL: {content[:10].strip()}")
        sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    OUT.write_text(f"# 读者外审失败\n\n{e}\n")
    sys.exit(1)
