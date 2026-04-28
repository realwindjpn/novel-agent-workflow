#!/usr/bin/env python3
"""Update DeepSeekV4 summary card with Micron, EU, and Open Source themes."""
import json
from pathlib import Path

OUT_DIR = Path("/workspace/科武纪元/硬科学素材/B站字幕/DeepSeekV4_ShenYi")
card_path = OUT_DIR / "summary_card.json"

# Load existing
if card_path.exists():
    with open(card_path) as f:
        card = json.load(f)
else:
    card = {"id": "bili_shenyi_deepseek_v4", "source": "B站 - 沈逸观察", "domains": []}

# Add new content blocks
new_content = """
【1. 算力与生态垄断 (The Moat)】
- "Softbank + OpenAI + Nvidia" 组成的完美护城河。
- 核心底座是：英伟达的卡 + CUDA 生态。
- 小说映射：主角方打破护城河的关键在于"去 CUDA 化"（如昇腾生态），而不仅仅是造出更快的卡。算力垄断导致了生态垄断。

【2. 开源 vs 闭源 (Ideological War)】
- 开源是"人类命运共同体"的体现，闭源是"世界帝国/赛博朋克 2077"的路径。
- DeepSeek 的伟大在于开源，让全世界多了一个选项，不让 AI 成为少数人的金融游戏。
- 小说映射：主角方坚持开源，引发全球技术狂欢，遭到闭源巨头的疯狂围剿（因为打破了他们的金融泡沫）。

【3. 美光 (The Malicious Player)】
- 沈逸点名"美光"是芯片界做得最恶劣的，不仅游说制裁，还试图断供服务（DUV 维修）。
- 蠢在不知道"杀敌一千自损八百"：一旦断供服务，中国江浙中小企业立刻接手，抢走一辈子耗材生意。
- 小说映射：反派阵营中的"急先锋"，看似凶狠实则愚蠢，主角方利用其"断供"行为完成国产替代的最后一块拼图。

【4. 欧洲政客 (The Delusional)】
- 评价欧盟为"脑皮层光滑"，领导人像"夜场小公主"，沉迷于 PUA 自己，以为拥有道德高地，实则实力不济。
- 小说映射：西方阵营中的"啦啦队"，只会口头谴责，实际上被主角方的技术红利分化拉拢。
"""

# Update
card["content"] = card.get("content", "") + new_content

# Save
with open(card_path, "w") as f:
    json.dump(card, f, ensure_ascii=False, indent=2)

print("Card updated with Micron, EU, Open Source themes.")
