#!/usr/bin/env python3
"""第355章「作者有话说」四门禁校验。

门禁来源（kewu-close-loop SKILL.md）：
- L239：必须有「作者有话说：」段落，内容创作意图/技术要点（≥50字），非情节摘要
- L244：长度 120-260；无公式句；无解释腔词；非空
- references/fanqie-upload-pipeline-pitfalls-20260625.md L50：
  「【作者有话说】」方括号格式不识别，必须全角冒号
"""
import re, sys

RAW = """作者有话说：
这章我把破壁协议写成一次真正的链路事故：数据流灌入神经链路后，带宽占用从基线被撑到高位，身体反应必须跟着每一秒的负载变化走。四百三十二纳米异常谱线先做多普勒频移标定，再扣除运动造成的偏移，最后与六十三号档案发射峰比对；峰值偏差零点三纳米、分辨率约R=1440，判据才站得住。谢云的过载代价落在接口积液、视野模糊和动作延迟上，方宁的手则留在前文伤势的余波里。铁幕主节点离线，作为第七卷收官，落点放在系统证据上。
"""

lines = [l for l in RAW.strip().split("\n") if l.strip()]
fails = []

# 1 首行格式
if lines[0].strip() != "作者有话说：":
    fails.append(f"首行不符: {lines[0]!r}")
if lines[0].strip().startswith("【"):
    fails.append("方括号格式不识别")

# 2 段数与字数
if len(lines) != 2:
    fails.append(f"应为两行，实为 {len(lines)} 行")
note = lines[1] if len(lines) > 1 else ""
n = len(re.findall(r"[\u4e00-\u9fff]", note))
if not (120 <= n <= 260):
    fails.append(f"字数 {n} 不在 120-260")

# 3 禁词（解释腔/文艺腔/清单腔）
BAN = ["不是", "而是", "仿佛", "似乎", "值得一提的是", "总的来说",
       "在这一章里", "本章讲述", "总结一下", "众所周知"]
for w in BAN:
    if w in note:
        fails.append(f"禁词命中: {w}")

# 「不是…而是」公式句
if re.search(r"不是.{0,20}。?\s*是", note):
    fails.append("SPLIT_FORMULA: 不是…是 结构")

# 4 情节复述检测（摘要腔）
if re.search(r"^(这一章|本章)(讲了|写了|讲述|描述)", note.strip()):
    fails.append("情节摘要腔")

# 5 非空 + 技术密度（至少含 2 个数字/技术锚点）
nums = re.findall(r"[0-9]+|零点三|四百三十二|六十三", note)
if len(nums) < 2:
    fails.append(f"技术锚点不足: {nums}")

print("字数(CJK):", n, "| 技术锚点:", nums[:6])
print("禁词检查: 通过" if not any("禁词" in f or "SPLIT" in f for f in fails) else "禁词检查: FAIL")
if fails:
    print("\n".join("FAIL: " + f for f in fails))
    sys.exit(1)
print("AUTHOR_NOTE_GATE: PASS")
