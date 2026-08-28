#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""292 R9 结构审确定性机扫（只读，不改稿）。"""
import re, hashlib, json, sys

P = "/root/workspace/科武纪元/任务运行态/20260823_kewu_selfcycle_daily/output/candidate_292_r9.md"
t = open(P, encoding="utf-8").read()
L = t.split("\n")
def line(n): return L[n-1]

out = []
def p(*a): out.append(" ".join(str(x) for x in a))

p("sha256", hashlib.sha256(t.encode()).hexdigest())
p("net_cjk", len(re.findall(r"[\u4e00-\u9fff]", t)), "lines", len(L))

p("\n=== F1-F6 ===")
p("F1 L38:", line(38))
p("F2 new:", t.count("每错一次损失 5 个精磨工时"), "old:", t.count("损失 5 工时精磨工时"))
p("F3 new:", t.count("他拿 5.4 除以 0.3"), "old:", t.count("5.4 去除"))
p("F4 new:", t.count("最后一个穿过气闸门"), "old:", t.count("最后一个进的气闸门"))
p("F5 L54:", line(54))
p("F5 reverse:", round(1 - 54/(24.6*60), 6))
p("F6 L70:", line(70))
p("F6 L71:", line(71))
p("F6 8+13+30*11 =", 8+13+30*11, "| 8+13+30*12 =", 8+13+30*12)
p("F6 351*0.78 =", round(351*0.78, 2), "| 5600-274 =", 5600-274)
p("F6 tokens: 第3至13月=", t.count("第 3 至 13 月"), "第3至14月=", t.count("第 3 至 14 月"),
  "第14月停线切并网=", t.count("第 14 月停线切并网"))

p("\n=== NUMBER CHAIN ===")
p("0.62*0.74 =", round(0.62*0.74, 4), "| tok46:", t.count("链路总效率取整 46%"))
p("420/0.46 =", round(420/0.46, 2), "| tok913:", t.count("913"))
p("913000/(590*0.31) =", round(913000/(590*0.31), 1), "| tok5000:", t.count("5000 平方米"))
p("913*1.04 =", round(913*1.04, 1), "| tok949:", t.count("949"))
p("5000*1.04 =", 5000*1.04, "| tok5200:", t.count("5200"))
p("16.2*1.04 =", round(16.2*1.04, 2), "| tok16.9:", t.count("16.9"))
p("16.2*1.22 =", round(16.2*1.22, 2), "| tok19.8:", t.count("19.8"))
p("30*0.78 =", round(30*0.78, 2), "| tok23:", t.count("可用 23 件"), "| 400-23 =", 400-23, "| tok377:", t.count("377"))
p("120*0.92 =", round(120*0.92, 1), "| tok110:", t.count("月可用 110"))
p("85/180 =", round(85/180*100, 2), "% | tok47.2:", t.count("47.2%"))
p("600-180 =", 600-180, "| 420-60 =", 420-60, "| tok360:", t.count("360"))
p("100/96.3-1 =", round((100/96.3-1)*100, 2), "% | tok多3.7%:", t.count("多 3.7%"), "| 3.7*5 =", 3.7*5, "| tok18.5:", t.count("18.5%"))
p("2.44*0.12236*1.08e9/4600 m =", round(2.44*0.12236*1.08e9/4600/1000, 2), "km")
p("400*14 =", 400*14, "| tok5600:", t.count("5600"), "| 5600-274 =", 5600-274, "| tok5326:", t.count("5326"))

p("\n=== 291 ANCHORS ===")
for k in ["600 千瓦", "180 千瓦", "420", "120 件", "78%", "47 千瓦", "0.8 千瓦", "12 分钟",
          "4 台 120 千瓦", "40 到 85 千瓦", "1.8 吉瓦", "零点零零", "92%", "3.6"]:
    p("  ", k, "=", t.count(k))

p("\n=== 293 BOUNDARY ===")
for k in ["外星", "信号", "CTC", "星座", "开工", "并网之后"]:
    p("  ", k, "=", t.count(k))
p("  bare chapter regex:", re.findall(r"第\s*2\d\d\s*章", t))

p("\n=== AI FORMULA ===")
pats = [r"不是[^。！？\n]{0,25}而是", r"这意味着", r"核心在于", r"真正的[^。\n]{0,15}是",
        r"仿佛", r"似乎", r"宛如", r"首先", r"其次", r"总的来说", r"由此可见",
        r"不仅[^。\n]{0,20}而且", r"值得注意", r"某种程度上", r"与此同时"]
hits = 0
for pa in pats:
    m = re.findall(pa, t)
    if m:
        hits += 1
        p("  HIT", pa, m)
p("  formula_hit_patterns =", hits)

p("\n=== FORMAT ===")
q = t.count('"')
p("halfwidth dquote:", q, "even:", q % 2 == 0)
p("odd-quote lines:", [i+1 for i, l in enumerate(L) if l.count('"') % 2])
p("fullwidth quotes:", t.count("\u201c") + t.count("\u201d"))
p("first:", repr(L[0]))
p("last non-empty:", repr([x for x in L if x.strip()][-1]))
p("markdown heading:", len(re.findall(r"^#", t, re.M)), "| display prefix:", len(re.findall(r"^\d+\|", t, re.M)))

p("\n=== LINXINGCHEN ===")
for i, l in enumerate(L, 1):
    if "林星辰" in l:
        p(f"  L{i}:", l)

p("\n=== KEY LINES ===")
for i in (2, 28, 31, 36, 38, 44, 46, 48, 49, 50, 55, 56, 57, 59, 64, 65, 70, 71, 76, 78, 81, 83):
    p(f"L{i}:", line(i))

print("\n".join(out))
