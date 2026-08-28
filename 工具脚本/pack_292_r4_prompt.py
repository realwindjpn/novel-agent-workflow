#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第292章 R4 作者返修提示包打包器（确定性）。

铁律：
- 用 Path.read_text 读原文字节，禁用 read_file 展示层文本。
- 提示包必须内联 R3 全文（84 行完整正文）。
- 打包后自验：字节数、首尾锚点、10 处修复锚点在原文中唯一存在。
"""
from __future__ import annotations
import hashlib
import re
import sys
from pathlib import Path

BASE = Path("/root/workspace/科武纪元/任务运行态/20260823_kewu_selfcycle_daily/output")
SRC = BASE / "candidate_292_r3.md"
OUT = BASE / "author_repair_prompt_292_r4.md"

# (编号, 描述, 原文唯一锚点, 修复后写法)
FIXES = [
    (1, "引号错位：叙述句被裹进对话引号内",
     '"整流转换 74%。他拿 0.62 乘 0.74，链路总效率取整 46%。"',
     '"整流转换 74%。"他拿 0.62 乘 0.74，链路总效率取整 46%。'),
    (2, "赘字病句：工时重复",
     "每错一次损失 5 工时精磨工时",
     "每错一次损失 5 个精磨工时"),
    (3, "除法方向写反",
     "他拿 5.4 去除 0.3",
     "他拿 5.4 除以 0.3"),
    (4, "缺谓语／歧义",
     "沃罗诺夫最后一个进气闸门",
     "沃罗诺夫最后一个进的气闸门"),
    (5, "遮挡频次与光照率互斥（保留 96.3%）",
     "火星本影每 687 天扫过 L1 一次，遮挡期最长 4.7 小时",
     "火星本影每 24.6 小时扫过 L1 一次，遮挡期最长 54 分钟"),
    (6, "产线配额链断裂：进炉量与日产结论互斥",
     "配额只够第一班 4 件进炉",
     "配额只够第一班 4 件里进 1 件炉，余下 3 件跟第二班一起错窗"),
    (7, "节拍表首行与第 6 处同步（同一表，同步改）",
     "第一班四件进炉 06:00",
     "第一班一件进炉 06:00"),
    (8, "月产×月数≠总产出：补爬产口径，数字 351／274／5326 全部保留不动",
     "14 个月，月产 30，总产出 351 件。",
     "14 个月，前两个月爬产，月产 30，总产出 351 件。"),
    (9, "道具连续性断裂：终端塞回包里，后文却仍在桌面使用",
     "帕特尔把终端塞回包里。",
     "帕特尔把终端合上，压在基准表上面。"),
    (10, "与第 9 处配套：后文避免重复合上动作",
     "帕特尔把终端合上。",
     "帕特尔把终端推到一边。"),
    (11, "作者抢答：删除心理旁白整句（删除，不替换）",
     "他不想让任何人先看见这行字。",
     "（整句删除，前后文自然衔接，不补新句）"),
    (12, "余波跳空：人物零反应",
     "沃罗诺夫没反对。",
     "沃罗诺夫没反对。他看了一眼自己搁在桌上的笔，没拿。"),
]

HEADER = """# 第292章 定点返修任务（R4）

## 你要做的唯一一件事

下面【原文全文】给出的是第292章已定稿的完整正文，共 84 行。
你的任务：**把这份原文原样复制输出，只在指定的 12 个位置做句级替换。**

## 绝对禁止（违反任一条即作废）

1. 禁止重写场景、禁止新增剧情、禁止改场景顺序、禁止换角色。
2. 禁止输出任何审稿过程、修改说明、清单、编号、总结、致辞。
3. 禁止只输出被改的段落。必须输出**完整第292章原文**，从第一行标题到末行「（本章完）」。
4. 禁止删减、压缩、概括未点名的任何一行。原文 84 行的剧情必须全部保留，
   段落顺序、人物动作、对白、数字链一字不动（除下列点名处）。
5. 禁止改动这些核心锚点：母线配额表、陈若水、L1 枢纽原位、总质量 16.9 吨、
   420 kW 缺口、949 千瓦设计功率、5200 平方米、分四段运、在轨对接三次。
6. 禁止改动其余全部数字：180／420／913／949／5200／16.2→16.9／351／274／5326／
   590／31%／62%／74%／46%／108 万公里／5.8 吉赫兹／70 公里／22 公里 等。
7. 禁止加 markdown 标题符号、禁止加引号包裹全文、禁止加代码块。

## 定点修复清单（共 12 处，逐处原地替换）

"""

FOOTER = """
## 输出格式

- 第一行必须是：第292章 能源瓶颈
- 最后一行必须是：（本章完）
- 净中文不少于 3200 字（原文 3629 字，本轮为定点修复，字数应基本持平）
- 直接给正文。不要任何前言、说明、编号、标题符号。

---

# 原文全文（以下为第292章完整正文，请在此基础上做上述 12 处定点替换后完整输出）

"""


def cjk(t: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", t))


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    src_sha = hashlib.sha256(src.encode("utf-8")).hexdigest()
    errs = []

    # 1. 校验每个锚点在原文中唯一存在
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
        parts.append(f"原文（唯一出现一次）：\n{old}\n")
        parts.append(f"改为：\n{new}\n\n")
    parts.append(FOOTER)
    parts.append(src if src.endswith("\n") else src + "\n")
    prompt = "".join(parts)

    OUT.write_text(prompt, encoding="utf-8")

    # 2. 读回自验
    back = OUT.read_text(encoding="utf-8")
    checks = {
        "prompt_bytes": len(back.encode("utf-8")),
        "prompt_cjk": cjk(back),
        "src_bytes": len(src.encode("utf-8")),
        "src_cjk": cjk(src),
        "src_lines": len([l for l in src.splitlines() if l.strip()]),
        "src_sha256": src_sha,
        "inlined_full_body": src.strip() in back,
        "has_title_anchor": "第292章 能源瓶颈" in back,
        "has_tail_anchor": "（本章完）" in back,
        "no_display_prefix": re.search(r"(?m)^\d+\|", back) is None,
        "bytes_gt_src": len(back.encode("utf-8")) > len(src.encode("utf-8")),
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
