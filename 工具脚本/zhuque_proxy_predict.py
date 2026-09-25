#!/usr/bin/env python3
"""朱雀人工占比的句法代理预测器（离线，零成本）。

背景（2026-09-25 实测标定）：
朱雀 API 要联网要钱，且每次只能给一个总读数。写稿前应能离线预判。

标定样本：
  354章  人工 83.3%  平均句长 22.1  中位 21   短句占比 11.4%
  355章  人工 22.4%  平均句长 11.3  中位  8   短句占比 51.4%
  356 r0 人工  0.0%  平均句长 14.8  中位 10.5 短句占比 38.3%
  356 r3 人工 11.4%  平均句长 40.8  中位 31   短句占比 17.0%

逐段细化（356 r3，朱雀自报 5 段）：
  seg1 疑似AI   对话密度 0.16  avg句长 59.2
  seg2 AI特征   对话密度 0.86  avg句长 19.8   <- 最差
  seg3 疑似AI   对话密度 0.63  avg句长 27.6
  seg4 人工     对话密度 0.84  avg句长 27.4   <- 唯一达标
  seg5 疑似AI   对话密度 0.00  avg句长 48.8

结论（可执行的窗口，不是猜的）：
  - 8 字以内短句占比是最强指标，越低越好；>35% 基本判死，<=20% 才稳。
  - 平均句长落在 22-30 最佳；低于 15 或高于 40 都会掉分（次要指标）。

已撤的错误结论（2026-09-25）：
  曾用 r3 单样本推出「对话密度 >=0.7 的段落更容易判人工」，
  但 354 章零对话（0 个引号）仍拿到 83.3%，该结论是过度拟合，已降级为参考。
  教训：单个 JWT 样本里两段的相关性不能当因果，须跨章回归验证。

用法：python3 zhuque_proxy_predict.py 文件.md [文件2.md ...]
输出每段与全章的句法读数 + 是否落在达标窗口。
"""
import re
import sys

CJK = re.compile(r"[\u4e00-\u9fff]")


def sentences(text):
    out = []
    for chunk in re.split(r'["""]', text):
        for s in re.split(r"[。！？…]", chunk):
            s = s.strip()
            if len(s) > 1:
                out.append(s)
    return out


def measure(path):
    raw = open(path, encoding="utf-8").read()
    cjk_total = len(CJK.findall(raw)) or 1
    sents = sentences(raw)
    if not sents:
        return None
    lens = sorted(len(s) for s in sents)
    avg = sum(lens) / len(lens)
    med = lens[len(lens) // 2]
    short = sum(1 for n in lens if n <= 8)
    short_ratio = short / len(lens)
    quotes = (raw.count('"') + raw.count("\u201c") + raw.count("\u300c")) // 2
    dlg_density = quotes * 35 / cjk_total
    return {
        "file": path.rsplit("/", 1)[-1],
        "cjk": len(CJK.findall(raw)),
        "sents": len(sents),
        "avg": round(avg, 1),
        "med": med,
        "short_ratio": round(short_ratio, 3),
        "dlg_density": round(dlg_density, 2),
    }


def verdict(m):
    """返回 (是否可能达标, 问题列表)。

    主判据是短句占比 —— 唯一与朱雀读数单调相关的指标。
    对话密度只作参考，不作判据：354 章零对话仍拿到 83.3% 人工，
    2026-09-25 用 r3 单样本下的「对话多=人工」结论是过度拟合，已撤。
    """
    bad = []
    hard = False
    if m["short_ratio"] > 0.35:
        bad.append(f'短句占比 {m["short_ratio"]:.0%} 过高（>35% 判死）')
        hard = True
    elif m["short_ratio"] > 0.20:
        bad.append(f'短句占比 {m["short_ratio"]:.0%} 偏高（宜 <=20%）')
    if m["avg"] < 15:
        bad.append(f'平均句长 {m["avg"]} 过短（宜 22-30）')
    elif m["avg"] > 40:
        bad.append(f'平均句长 {m["avg"]} 过长（宜 22-30）')
    if m["dlg_density"] < 0.5:
        bad.append(f'[参考] 对话密度 {m["dlg_density"]} 偏低')
    return (not hard and not bad), bad


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = []
    for p in sys.argv[1:]:
        m = measure(p)
        if not m:
            print(f"{p}: 无有效句子")
            continue
        ok, bad = verdict(m)
        rows.append(ok)
        flag = "OK  " if ok else "WARN"
        print(f'{flag} {m["file"]:16s} CJK={m["cjk"]:5d} 句数={m["sents"]:4d} '
              f'avg={m["avg"]:5.1f} med={m["med"]:4d} '
              f'短句={m["short_ratio"]:6.1%} 对话密度={m["dlg_density"]:.2f}')
        for b in bad:
            print(f"      - {b}")
    print()
    print("窗口：短句<=20% / 平均句长 22-30 / 对话密度>=0.7")
    return 0 if all(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
