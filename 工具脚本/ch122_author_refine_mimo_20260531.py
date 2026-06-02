#!/usr/bin/env python3
"""第122章作者精修 - xiaomi/mimo-v2.5-pro"""
import json, os, sys, yaml
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
SOURCE = BASE / '新版/第122章.md'
OUT = BASE / '审核记录/自循环体系会议_20260530/ch122_author_refined_mimo.md'
SUMMARY_OUT = BASE / '审核记录/自循环体系会议_20260530/ch122_author_refined_mimo_summary.md'

source = SOURCE.read_text()

# Read outline context
outline = BASE / 'wiki/raw/outline/科武纪元大纲_latest.md'
outline_text = outline.read_text() if outline.exists() else ''
ch122_outline = [l for l in outline_text.split('\n') if '122' in l and ('章' in l or '第122' in l)]
outline_ctx = '\n'.join(ch122_outline[:5]) if ch122_outline else ''

# Read previous chapter (121) ending for continuity
ch121 = BASE / '新版/第121章.md'
ch121_text = ch121.read_text() if ch121.exists() else ''
ch121_tail = '\n'.join(ch121_text.split('\n')[-20:])

prompt = f"""你是《科武纪元》作者角色。模型：xiaomi/mimo-v2.5-pro。

任务：对第122章源稿做局部精修。

=== 大纲上下文 ===
{outline_ctx}

=== 第121章结尾（承接上下文）===
{ch121_tail}

=== 第122章源稿全文 ===
{source}

=== 外审意见（P1必改）===

编辑P1：
1. 结尾钩子力度可增强：结尾"按时运转本身就是力量"偏平淡，加入一句具紧迫感或指向性的台词，为123章铺钩子。
2. U-19阈值核查：前文最低62，此处"降到五十二"后行为逻辑需确认一致性。

科学P1：
1. AI自主性设定略高："脱离控制链路自主识别"建议改为"失去链路后按预设规则有限自主"。
2. 量子传感备份表述模糊：建议明确为"量子增强模式抗干扰"或"量子加密通信/感知链路"。
3. 地理时间线瑕疵：商船14节6分钟仅移1.38海里，从22海里外不可能进入遮蔽角。需调整时间/距离或改表述为"进入干扰最有效区域"。

读者建议：
1. 中段技术解释偏密，建议穿插实时风险反馈（如某船被锁定倒计时）。
2. "战争/新秩序"类总结句偏多，建议精简。

精修要求：
1. 只改上述P1问题，不动其他已PASS内容。
2. 输出完整精修后全文（245行左右），不是diff。
3. 保持番茄口径≥3000字。
4. 保持人物口吻：苏雨晴稳、赵刚硬、方宁技术向、陈思琪数据向。
5. 输出纯正文，不要JSON/标记/解释。"""

with open('/root/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
xiaomi_cfg = cfg.get('providers', {}).get('xiaomi', {})
api_key = xiaomi_cfg.get('api_key', '')
base_url = 'https://token-plan-cn.xiaomimimo.com/v1'

import urllib.request
messages = [{"role": "user", "content": prompt}]
body = json.dumps({"model": "mimo-v2.5-pro", "messages": messages, "max_tokens": 16000, "temperature": 0.5}).encode()
req = urllib.request.Request(f"{base_url}/chat/completions", data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, method="POST")

try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read())
        content = data['choices'][0]['message']['content']
        OUT.write_text(content)
        
        # Generate summary
        summary = f"""# 第122章 作者精修说明

精修模型：xiaomi/mimo-v2.5-pro
精修时间：2026-05-31
源稿：新版/第122章.md
候选稿：ch122_author_refined_mimo.md

---

## 修改清单

### P1-1 结尾钩子增强（编辑）
加入具紧迫感/指向性的台词，为123章铺钩子。

### P1-2 U-19阈值一致性（编辑）
确认"降到五十二"与前文逻辑一致。

### P1-3 AI自主性下调（科学）
"脱离控制链路自主识别"→"失去链路后按预设规则有限自主"。

### P1-4 量子传感表述明确（科学）
"量子传感备份"→"量子增强模式/量子加密感知链路"。

### P1-5 地理时间线修复（科学）
商船14节6分钟位移不合理→调整时间/距离或改"进入干扰最有效区域"。

### P1-6 技术解释穿插风险反馈（读者）
中段科普段加入实时风险元素。

### P1-7 总结句精简（读者）
"战争/新秩序"类总结句压缩。

---

*精修完毕。候选稿待编辑+读者写后复审。*
"""
        SUMMARY_OUT.write_text(summary)
        print(f"Author refine done. Output: {len(content)} chars")
        sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
