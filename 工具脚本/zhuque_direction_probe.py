#!/usr/bin/env python3
"""返修方向验证：356 会议戏改写为「可核查过程寄存器」能否过线。

已确证（移植实验，因果级）：
  356 原样 3009 字            → 人工 11.3%
  换入 354 寄存器 6 段        → 人工 12.2%
  换入 354 寄存器 12 段       → 人工 18.7%   单调上升
  纯 354 寄存器 1449 字       → 人工 66.0%

结论：朱雀奖励「可核查的过程细节 + 因果链」，与字数/句长/段落结构无关。
356 全章是「并行观察」（席位牌、耳机、灯光、淤青同时发生，互不约束），
354 全章是「收敛因果链」（每步结果限定下一步选项，倒计时逼近）。

本轮取 356 的换牌场景（L42-49）改写为过程寄存器，替换原段，测读数。
仅作方向验证，产物不写回 新版/，正文改写须派作者席。
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zhuque_probe import CJK, detect, get_key  # noqa: E402

CH356 = Path("/root/workspace/科武纪元/新版/第356章.md")
OUT = Path("/root/workspace/科武纪元/审核记录/ch356_direction_probe_20260926.json")

# 原 L42-49：换牌场景（并行观察）
REWRITE = """换牌的那个人从席位上站起来，绕过桌角，走到主席台侧面的投影控制台前。他伸手在面板上按下第二个键，投影幕亮起来之前先黑了两秒。
幕上滚出的是一份名单。十七个实验室编号，四个大洲，编号后面跟人员编制和算力配额。汇总行压在最下面：肆万。
林星辰把这个数字和他三天前在预备文件里看到的那个对了一下。对得上。差的是后面那十二个算力节点——预备文件里只列了九个。
「创世纪任务。」换牌的那个人开口。他的声音从主席台话筒出来，比刚才在席位上时大了三倍。「十七个实验室。四万名研究人员。十二个超算节点全时调度。」
他停了半秒。
「对标规模，各位可以自行比对。」
林星辰没有抬头。他盯着汇总行下面那行小字。调度窗口：全年。括号里写着并网条件：优先。
优先。优先于谁，文件没写。他把这一页翻过去。背面是空白。
主席台上，秘书长的手已经伸向了那份黑色封皮的文件。她在取之前看了那个换牌的人一眼，停了不到一秒，然后继续取。"""

PARA_MARK = "原来的牌面上印着：星穹探索公司，首席技术顾问。"


def measure(tag, text, key):
    res = detect(text, key)
    lr = res.get("labels_ratio") or {}
    cjk = len(CJK.findall(text))
    rec = {
        "tag": tag, "cjk": cjk,
        "human": round(float(lr.get("0", 0)) * 100, 1),
        "ai": round(float(lr.get("1", 0)) * 100, 1),
        "suspect": round(float(lr.get("2", 0)) * 100, 1),
    }
    print(f"  {tag:32s} CJK={cjk:5d}  人工 {rec['human']:5.1f}%  "
          f"AI {rec['ai']:5.1f}%  疑似 {rec['suspect']:5.1f}%")
    return rec


if __name__ == "__main__":
    key = get_key()
    raw = CH356.read_text(encoding="utf-8")
    lines = raw.split("\n")
    i_start = next(i for i, l in enumerate(lines) if PARA_MARK in l)
    # 原段范围：从「那人走到席位前面」到「像换了一张名片。」之后一行
    i_from = next(i for i, l in enumerate(lines) if "那人走到席位前面" in l)
    i_to = next(i for i, l in enumerate(lines) if "像换了一张名片" in l)
    variant = "\n".join(lines[:i_from] + REWRITE.split("\n") + lines[i_to + 1:])

    print("返修方向验证（基线 356 原样 = 人工 11.3%）")
    recs = [
        measure("D1 原样", raw, key),
        measure("D2 换牌场景改过程寄存器", variant, key),
    ]
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n替换行 {i_from}-{i_to}；已写 {OUT}")
