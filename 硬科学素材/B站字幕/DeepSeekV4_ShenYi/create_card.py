#!/usr/bin/env python3
"""Create a summary card for Shen Yi's video on DeepSeek V4."""
import json
from pathlib import Path

OUT_DIR = Path("/workspace/科武纪元/硬科学素材/B站字幕/DeepSeekV4_ShenYi")
OUT_DIR.mkdir(exist_ok=True)

card = {
    "id": "bili_shenyi_deepseek_v4",
    "source": "B站视频 - 沈逸观察",
    "title": "DeepSeek-V4发布与中美芯片战升级",
    "url": "https://www.bilibili.com/video/BV1GWofBcEHw/",
    "trust": "B",
    "domains": ["AI大模型", "芯片制裁", "法律战"],
    "content": """
【核心事件】
1. DeepSeek-V4 发布：接近顶级水平，成本大幅降低，不依赖美国芯片。
2. CUDA 体系绕过：外媒报道这是打破行业惯例的重大变化。优先围绕华为昇腾 AI 体系适配。
3. 美国制裁升级：美国众议院通过“硬件技术管制多边协调法案”，从先进到成熟制程全覆盖（含 DUV 维修、供应链等），企图锁死 28nm。
4. 法律反制：国务院出台《产业链供应链安全规定》和《反外国不当域外管辖条例》。
5. "净值令"机制：若中方认定为不当制裁，在中国境内不得执行，违规企业将面临罚款。

【小说映射点】
- 设定：主角所在阵营发布新一代 AI 架构，不依赖 CUDA，直接引爆美国制裁恐慌。
- 冲突：美国试图通过“净值令”反制中国的法律战，禁止企业配合中国反制措施。
- 细节：黄仁勋担忧 CUDA 生态被撕裂；美国政客将出口挂零甩锅中国政府（“不让人家买”）。
- 背景：中美科技战没有“黄金时代”，只有“你造不出我就卖你高价，你造出来我就封锁你”。
""",
    "date": "2026-04-26"
}

with open(OUT_DIR / "summary_card.json", "w") as f:
    json.dump(card, f, ensure_ascii=False, indent=2)

print("Card saved successfully")
