#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第292章 R9 定点返修提示包打包器（确定性）。

本轮唯一目的：微波输电链路物理自洽收口。
- L36：发射天线口径 1 公里 → 相控发射天线口径 4.6 公里
  （圆孔第一零直径 2.44*λ*L/D，λ=0.12236m@2.45GHz，L=1.08e9m，D=4.606km 给 70km 光斑）
- L38：开头句改为显式相控整形句，使 22 公里阵面 62% 截获成为工程设定
  （均匀圆孔 Airy 下 22km 仅截约 30%，须写出相控整形兜底）

铁律：
- Path.read_text 读原文字节，禁用 read_file 展示层文本。
- 提示包必须内联 R8 全文（84 行完整正文），prompt_bytes 必须 > src_bytes。
- 打包前预检：每个 before 锚点在源稿中 count()==1，否则 ANCHOR_FAIL 退出。
- 打包后读回自验：inlined_full_body / 首尾锚点 / 无 ^\\d+\\| / 字节数。
- 引号一律沿用源稿 ASCII 直引号（源稿全篇 146 个 ASCII 引号、0 个全角）。
"""
from __future__ import annotations
import hashlib
import re
import sys
from pathlib import Path

BASE = Path("/root/workspace/科武纪元/任务运行态/20260823_kewu_selfcycle_daily/output")
SRC = BASE / "candidate_292_r8.md"
OUT = BASE / "author_repair_prompt_292_r9.md"
EXPECT_SRC_SHA = "8a7dc3dbe500a856f57b737920d300f4cbe5bcbbd2b5a6184603b4fe20e6799e"

# (编号, 描述, 原文唯一锚点, 修复后写法)
FIXES = [
    (1, "发射天线口径与衍射光斑自洽：2.45 吉赫兹波长 0.12236 米、链路 108 万公里，"
        "要得到 70 公里光斑，圆孔第一零直径公式 2.44λL/D 反解出口径约 4.6 公里，1 公里口径算不出 70 公里",
     "发射天线口径 1 公里",
     "相控发射天线口径 4.6 公里"),
    (2, "截获率 62% 须写明相控整形来源：均匀圆孔 Airy 分布下 22 公里阵面只截约 30%，"
        "显式写出相控整形把主瓣压进阵面，62% 才成为工程设定而非裸衍射结论",
     '"口径 22 公里，截获率 62%。"',
     '"相控整形把主瓣能量压进 22 公里阵面，截获率 62%。"'),
]

HEADER = """# 第292章 定点返修任务（R9）

## 你要做的唯一一件事

下面【原文全文】给出的是第292章已定稿的完整正文，共 84 行。
你的任务：**把这份原文原样复制输出，只在指定的 2 个位置做句级替换。**

除这 2 处以外，全文一字不动。这是两处微波输电链路物理自洽的定点修正，不是重写。

## 绝对禁止（违反任一条即作废）

1. 禁止重写场景、禁止新增剧情、禁止改场景顺序、禁止增删角色。
2. 禁止输出任何审稿过程、修改说明、修改清单、编号标注、总结、致辞、思考过程。
3. 禁止只输出被改的段落或被改的句子。必须输出**完整第292章正文**，
   从第一行标题「第292章 能源瓶颈」到末行「（本章完）」，共 84 行。
4. 禁止删减、压缩、概括、合并未点名的任何一行。原文 84 行的段落顺序、
   人物动作、对白、标点、数字链一字不动（除下列 2 处点名替换）。
5. 禁止改动这些核心锚点：总产出 351 件、可用 274、缺口 5326、需求侧 5600、
   L1 枢纽原位、420 千瓦缺口、949 千瓦设计功率、5200 平方米、16.9 吨、
   第 14 月停线切并网、分四段运、在轨对接三次、
   陈若水、方宁、韩铮、沃罗诺夫、帕特尔、赫斯特、林星辰。
6. 禁止改动其余全部数字：180／420／590／31%／913／949／5200／16.2／16.9／
   2.45 吉赫兹／108 万公里／70 公里／22 公里／62%／74%／46%／15 公里／
   0.004 毫瓦／0.2 度／96.3%／100%／3.7%／18.5%／22%／1.38／0.02／
   24.6 小时／54 分钟／85 千瓦／47.2%／78%／23 件／400／30 件／8 件／13 件／
   351／274／5326／5600／120／92%／110／40 千瓦／72 小时／300 炉次／179.7／
   1.7 乘 10 的 22 次方／38%／20 克／14.6 克／11 天 等，一律原样保留。
7. 禁止加 markdown 标题符号（#）、禁止用引号包裹全文、禁止加代码块围栏。
8. 引号一律沿用原文的半角直引号 "，不要换成中文全角引号“”。
9. 第 1 处只改「发射天线口径 1 公里」这一处措辞与数值，同句的
   「频段选 2.45 吉赫兹」「108 万公里」「地面光斑直径 70 公里」全部原样不动。
10. 第 2 处只替换该行开头这一句完整对白，该行后面的
    「方宁在方框旁边写了个数。"整流转换 74%。"他拿 0.62 乘 0.74，链路总效率取整 46%。」
    一字不动。下一行「打在 22 公里阵之外的部分」也不动。

## 定点修复清单（共 2 处，逐处原地替换）

"""

FOOTER = """
## 输出格式

- 第一行必须是：第292章 能源瓶颈
- 最后一行必须是：（本章完）
- 总行数 84 行（与原文一致）
- 净中文不少于 3200 字（原文 3697 字，本轮两处定点替换净增 13 字，应为 3710 字左右）
- 直接给正文。不要任何前言、说明、编号、标题符号、思考过程。

---

# 原文全文（以下为第292章完整正文，请在此基础上做上述 2 处定点替换后完整输出）

"""


def cjk(t: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", t))


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    src_sha = hashlib.sha256(src.encode("utf-8")).hexdigest()
    if src_sha != EXPECT_SRC_SHA:
        print("SRC_SHA_MISMATCH")
        print("  got=" + src_sha)
        print("  expect=" + EXPECT_SRC_SHA)
        return 4

    errs = []
    for num, desc, old, new in FIXES:
        c = src.count(old)
        if c != 1:
            errs.append(f"FIX{num} anchor count={c} (expect 1): {old[:40]}")
    if errs:
        print("ANCHOR_FAIL")
        for e in errs:
            print("  " + e)
        return 2

    parts = [HEADER]
    for num, desc, old, new in FIXES:
        parts.append(f"### 第 {num} 处｜{desc}\n")
        parts.append(f"原文（在全文中唯一出现一次）：\n{old}\n")
        parts.append(f"改为：\n{new}\n\n")
    parts.append(FOOTER)
    parts.append(src if src.endswith("\n") else src + "\n")
    prompt = "".join(parts)

    OUT.write_text(prompt, encoding="utf-8")

    back = OUT.read_text(encoding="utf-8")
    # 预期净增汉字数（纯替换，供回收后 CJK 增量核对）
    delta = 0
    for _, _, old, new in FIXES:
        delta += cjk(new) - cjk(old)

    checks = {
        "prompt_bytes": len(back.encode("utf-8")),
        "prompt_cjk": cjk(back),
        "src_bytes": len(src.encode("utf-8")),
        "src_cjk": cjk(src),
        "src_lines": len(src.splitlines()),
        "src_sha256": src_sha,
        "expected_cjk_delta": delta,
        "expected_clean_cjk": cjk(src) + delta,
        "inlined_full_body": src.strip() in back,
        "has_title_anchor": "第292章 能源瓶颈" in back,
        "has_tail_anchor": "（本章完）" in back,
        "no_display_prefix": re.search(r"(?m)^\d+\|", back) is None,
        "bytes_gt_src": len(back.encode("utf-8")) > len(src.encode("utf-8")),
        "fix_count": len(FIXES),
    }
    ok = (checks["inlined_full_body"] and checks["has_title_anchor"]
          and checks["has_tail_anchor"] and checks["no_display_prefix"]
          and checks["bytes_gt_src"])
    for k, v in checks.items():
        print(f"{k}={v}")
    print("PACKAGING_" + ("OK" if ok else "FAIL"))
    print("prompt_path=" + str(OUT))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
