#!/usr/bin/env python3
"""第121章编辑写后复审 - xiaomi/mimo-v2.5-pro"""
import json, os, sys, time
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
CANDIDATE = BASE / '审核记录/自循环体系会议_20260530/ch121_author_refined_mimo.md'
SUMMARY = BASE / '审核记录/自循环体系会议_20260530/ch121_author_refined_mimo_summary.md'
PREREVIEW = BASE / '审核记录/自循环体系会议_20260530/ch121_editor_prereview_qwen.md'
OUT = BASE / '审核记录/自循环体系会议_20260530/ch121_editor_postreview_mimo.md'

candidate = CANDIDATE.read_text()
summary = SUMMARY.read_text()
prereview = PREREVIEW.read_text() if PREREVIEW.exists() else 'N/A'

prompt = f"""你是《科武纪元》编辑复审角色。模型：xiaomi/mimo-v2.5-pro。

任务：对第121章候选稿做写后编辑复审。

=== 修改说明 ===
{summary}

=== 原编辑外审报告 ===
{prereview[:3000]}

=== 候选稿全文 ===
{candidate}

复审要点：
1. 核对原外审5条必改项是否全部落实：
   - 太极电磁功四要素虚化
   - 金融链信息密度压缩
   - 技术说明融入操作视角
   - 排比收尾减句
   - 前段说明密度压缩
2. 结构/节奏：章节功能是否完成（19海里试探→安全线划定→无人机越线→电磁驱离→商船靠泊→不战而屈）
3. 去AI味：有无解释腔、口号化、文艺比喻残留
4. 章末钩子：是否给读者"想看下一章"的牵引
5. 检查"航道外十二海里线/十二海里"是否统一使用，无"北纬30度线"残留
6. 检查"量子磁传感阵列"是否存在

输出格式：
首行必须是 PASS 或 FAIL。
若 FAIL，列具体问题和行号。
若 PASS（可含小修建议），列已落实项证据。
用中文，≤1500字。"""

# Xiaomi Token Plan API
api_key = os.environ.get('XIAOMI_API_KEY', '')
if not api_key:
    # Try inline from config
    import yaml
    with open('/root/.hermes/config.yaml') as f:
        cfg = yaml.safe_load(f)
    xiaomi_cfg = cfg.get('providers', {}).get('xiaomi', {})
    api_key = xiaomi_cfg.get('api_key', '')
base_url = 'https://token-plan-cn.xiaomimimo.com/v1'

import urllib.request, urllib.error

messages = [{"role": "user", "content": prompt}]
body = json.dumps({
    "model": "mimo-v2.5-pro",
    "messages": messages,
    "max_tokens": 4096,
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
        report = f"# 第121章编辑写后复审报告\n\n审核模型：xiaomi/mimo-v2.5-pro\n审核时间：2026-05-31\n候选稿：ch121_author_refined_mimo.md\n\n---\n\n{content}\n"
        OUT.write_text(report)
        print(f"PASS/FAIL: {content[:10].strip()}")
        print(f"Report saved to: {OUT}")
        sys.exit(0)
except Exception as e:
    err = f"ERROR: {e}"
    print(err, file=sys.stderr)
    OUT.write_text(f"# 编辑复审失败\n\n{err}\n")
    sys.exit(1)
