#!/usr/bin/env python3
"""构造 G3_PREP_356.json。

skill 硬规（kewu-selfcycle-production）：
- 必须从上一章 G3_PREP 全量复制再改字段，禁止逐个补齐
- state 必须 G3_READY
- prev_chapter == N-1；prev_sha256 为完整 64 位 SHA256
- target_chapters == [356, 357]（与今日 seed 双章一致）
"""
import hashlib, json
from pathlib import Path

P = Path("/root/workspace/科武纪元")
TPL = P / "任务运行态/20260923_kewu_selfcycle_daily/output/G3_PREP_346.json"
OUTDIR = P / "任务运行态/20260925_kewu_selfcycle_daily/output"
OUT = OUTDIR / "G3_PREP_356.json"

d = json.loads(TPL.read_text(encoding="utf-8"))

prev_md = P / "新版/第355章.md"
prev_sha = hashlib.sha256(prev_md.read_bytes()).hexdigest()

d.update({
    "chapter": 356,
    "target_chapters": [356, 357],
    "slot": "A",
    "nature": "",
    "generated_at": "2026-09-25T18:30:00+08:00",
    "inputs_fingerprint": "g1=cron_20260925_daily_g1;g2=G2_council_356357",
    "state": "G3_READY",
    "prev_chapter": 355,
    "prev_title": "铁幕溃败",
    "prev_sha256": prev_sha,
    "prev_ending": "无瑕项目深空飞行器尾焰光谱吻合，铁幕主节点离线，第七卷收官",
    "title": "谈判桌上的刀光",
    "volume": "第八卷：博弈",
    "outline_ref": "科武纪元大纲 V8_完整版.md#L573",
    "plot_seed": (
        "泛际安全理事会和谈陷入僵局，各方在算力供应链控制权上寸步不让。"
        "铁幕抛出对齐税提案——任何部署军用智能系统的国家必须接受国际监督，"
        "实为削东方算力优势。对面同步启动创世纪任务，十七个实验室、四万人、"
        "全球超算并网，明着对标当年的曼哈顿工程。铁幕内部技术共和国派系完成权力整合，"
        "资本与军工互为表里，多名前高管直接坐进政府要职。"
    ),
    "target_chars": 3200,
    "cjk_target_range": [3000, 4500],
    "hard_gates": {
        "first_line": "第356章 谈判桌上的刀光",
        "last_line": "（本章完）",
        "cjk_min": 3000,
    },
})
d["entry_interface"] = {
    "prev_chapter": 355,
    "prev_title": "铁幕溃败",
    "prev_sha256": prev_sha,
}
d["locked_constraints"] = [
    "谈判桌上的刀光",
    "和谈陷入僵局",
    "算力供应链控制权",
    "对齐税",
    "接受国际监督",
    "创世纪任务",
    "实验室",
    "全球超算",
    "技术共和国派系",
    "权力整合",
    "政治献金和游说",
    "政府合同和监管松绑",
    "政商旋转门",
]
d["provenance_sha256"] = prev_sha

OUTDIR.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("written:", OUT)
print("state:", d["state"], "| prev_chapter:", d["prev_chapter"],
      "| slot:", d["slot"], "| target:", d["target_chapters"])
print("prev_sha256:", prev_sha[:16], "... len", len(prev_sha))
assert d["prev_chapter"] == 355
assert len(d["prev_sha256"]) == 64
assert d["state"] == "G3_READY"
assert d["hard_gates"]["first_line"] == "第356章 谈判桌上的刀光"
print("G3_PREP_SELFCHECK: PASS")
