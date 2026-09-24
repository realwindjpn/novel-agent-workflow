import os, hashlib

base = "/root/workspace/科武纪元/新版"
chapters = [331, 332, 333, 334]

# 读取每章正文，去掉修改清单尾巴（对齐审稿焦点为正文，但保留全文供逐字引证）
bodies = {}
shas = {}
linecounts = {}
for n in chapters:
    f = os.path.join(base, f"第{n}章.md")
    raw = open(f, "rb").read()
    shas[n] = hashlib.sha256(raw).hexdigest()
    txt = raw.decode("utf-8")
    lines = txt.splitlines()
    linecounts[n] = len(lines)
    numbered = "\n".join(f"{i+1}|{ln}" for i, ln in enumerate(lines))
    bodies[n] = numbered

header = """你是《科武纪元》第331-334章的独立编辑审席。四章各自独立审读全文并给出判定。

【审核焦点】大纲对齐、叙事结构、因果链、节奏、人物动机、去AI化（禁解释腔/文艺腔/清单腔/"不是X而是Y"公式句）。

【格式硬规 — 必须严格遵守】
1. 输出首行必须且只能是：VERDICT: PASS 或 VERDICT: FAIL （这是对第331章的总判定）。
2. 四章各给一行独立 VERDICT，格式：第NNN章 VERDICT: PASS 或 第NNN章 VERDICT: FAIL。四行按 331/332/333/334 顺序。
3. 若某章 FAIL，逐条列出问题，每条不超两行，并附机器可校验证据：
   EVIDENCE: {"chapter":NNN,"quote":"<从下方带行号正文逐字复制，不含行号前缀 N|>","line":N}
   quote 必须是正文中逐字存在的原句；line 为该 quote 所在的行号（下方每行以 N| 前缀标注，N| 只是渲染标记，不属于正文，请勿抄进 quote）。
4. 全部输出控制在 900 字以内。
5. 禁草稿腔、禁裸 FAIL 无理由（FAIL 必须给 EVIDENCE）。
6. 必须审读正文全文，不得凭摘要。
7. 只用中文输出。若引用的 quote 在正文中检索不到或 line 越界，整份报告作废，请务必逐字复制。

【各章正文行数（用于 line 越界自检）】
"""
header += "\n".join(f"第{n}章：共 {linecounts[n]} 行，SHA={shas[n]}" for n in chapters)
header += "\n\n下面是四章带行号全文：\n"

parts = [header]
for n in chapters:
    parts.append(f"\n========== 第{n}章 正文（带行号） ==========\n")
    parts.append(bodies[n])
    parts.append("\n")

prompt = "".join(parts)
out = "/root/workspace/科武纪元/审核记录/editor_331_334_prompt.txt"
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(prompt)
print("prompt written:", out)
print("prompt bytes:", len(prompt.encode("utf-8")))
for n in chapters:
    print(f"第{n}章 lines={linecounts[n]} sha={shas[n]}")
