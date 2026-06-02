#!/usr/bin/env python3
"""第121章读者写后复审 - freemodel/gpt-5.5 (aixiaobai 504 fallback)"""
import json, os, sys
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
CANDIDATE = BASE / '审核记录/自循环体系会议_20260530/ch121_author_refined_mimo.md'
SUMMARY = BASE / '审核记录/自循环体系会议_20260530/ch121_author_refined_mimo_summary.md'
OUT = BASE / '审核记录/自循环体系会议_20260530/ch121_reader_postreview_gpt55.md'

candidate = CANDIDATE.read_text()
summary = SUMMARY.read_text()

# Truncate candidate to reduce payload for reader review
# Keep first 6000 + last 6000 chars to cover beginning, end, and key sections
if len(candidate) > 12000:
    candidate_for_prompt = candidate[:6000] + "\n\n[...中间段落省略...]\n\n" + candidate[-6000:]
else:
    candidate_for_prompt = candidate

prompt = f"""你是《科武纪元》读者复审角色。模型：freemodel/gpt-5.5 (aixiaobai fallback)。

任务：对第121章候选稿做写后读者复审。

=== 修改说明（摘要）===
{summary[:2000]}

=== 候选稿全文（首尾+关键段）===
{candidate_for_prompt}

复审要点：
1. 作为真实读者回答：
   - 读完想不想看下一章？（追读意愿1-5分）
   - 哪些段落卡顿/无聊/解释腔？
   - 人物口吻是否自然？
   - 章末钩子是否成立？
2. 检查AI味：有无排比口号、文艺比喻、说明腔
3. 检查"航道外十二海里线"是否自然融入
4. 检查无"北纬30度线"残留

输出格式：
首行必须是 PASS 或 FAIL。
追读意愿评分。
具体卡顿点（若有）。
用中文，≤800字。"""

api_key = os.environ['FREEMODEL_API_KEY']
base_url = 'https://api.freemodel.dev/v1'

import urllib.request

messages = [{"role": "user", "content": prompt}]
body = json.dumps({
    "model": "gpt-5.5",
    "messages": messages,
    "max_tokens": 3072,
    "temperature": 0.3,
}).encode()

req = urllib.request.Request(
    f"{base_url}/chat/completions",
    data=body,
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
        content = data['choices'][0]['message']['content']
        report = f"# 第121章读者写后复审报告\n\n审核模型：freemodel/gpt-5.5 (aixiaobai 504 fallback)\n审核时间：2026-05-31\n候选稿：ch121_author_refined_mimo.md\n\n---\n\n{content}\n"
        OUT.write_text(report)
        print(f"PASS/FAIL: {content[:10].strip()}")
        print(f"Report saved to: {OUT}")
        sys.exit(0)
except Exception as e:
    err = f"ERROR: {e}"
    print(err, file=sys.stderr)
    OUT.write_text(f"# 读者复审失败\n\n{err}\n")
    sys.exit(1)
