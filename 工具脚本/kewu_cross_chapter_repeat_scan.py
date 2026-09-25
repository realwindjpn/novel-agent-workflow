#!/usr/bin/env python3
"""跨章重复扫描：写新章前扫前 N 章，统计伤处词与读数词的跨章复用。

背景（2026-09-25 用户纠偏）：354 把方宁右手碳化写了十六段，355 还在接
（筋膜碳化纹路 / 肌肉抽搐 / 护具 / 结尾再滴一滴组织液），读者读到第三遍
只会疲劳。另一类是仪表读数：散热 809 千瓦 / 灼痕 318K / 倒计时 51:46，
350→355 每章复述一遍。

用法：
    python3 kewu_cross_chapter_repeat_scan.py --chapter 355 --window 6
    python3 kewu_cross_chapter_repeat_scan.py --chapter 355 --file <新章路径>

判据：
    WOUND_HARD   同一伤处词在前 window 章里出现 >= 3 章 → 新章不得再写实写
    NUMBER_HARD  同一读数在连续 >= 4 章出现 → 新章最多提一次
"""
import argparse
import json
import re
import sys
from pathlib import Path

BASE = Path("/root/workspace/科武纪元")
NEW_DIR = BASE / "新版"

# 伤处词：按「部位+损伤」分组，同一组算同一处伤
WOUND_GROUPS = {
    "手部碳化": ["碳化", "筋膜", "组织液", "残端", "全层烧伤", "清创", "护具", "抽搐"],
    "颅脑过载": ["血丝", "淤青", "渗血", "毛细血管", "眼眶", "后脑", "接口"],
    "躯干创伤": ["肋骨", "内脏", "腹腔", "胸腔", "脾", "肝"],
    # 四肢创伤：2026-09-25 修正。「大腿/膝盖/肩/锁骨」在久坐、靠墙、撑地等
    # 姿势描写里高频出现，会被误判成伤处。只有与损伤词同句或相邻才算伤处，
    # 因此这里只保留明确指向创伤的词，姿势词交给组合判据处理。
    "四肢创伤": ["小腿骨折", "膝盖骨裂", "肩胛骨", "锁骨骨折", "踝关节扭伤", "韧带断裂"],
}

# 读数词：跨章复述类
NUMBER_PATTERNS = {
    "散热上限": r"八百零九",
    "灼痕温度": r"三百一十八|三百一十九",
    "倒计时": r"五十一小时四十六分|五十二小时",
    "带宽": r"百分之八十七|百分之八十六|百分之八十八",
    "带宽基线": r"百分之十二|百分之十(?![二])",
}


def chapter_files(chapter: int, window: int):
    """返回 [chapter-window, chapter-1] 已定稿章节文件（按章号升序）。"""
    out = []
    for n in range(chapter - window, chapter):
        p = NEW_DIR / f"第{n}章.md"
        if p.exists():
            out.append((n, p))
    return out


def scan_prior(chapter: int, window: int):
    prior = {}
    for n, p in chapter_files(chapter, window):
        text = p.read_text(encoding="utf-8")
        prior[n] = text
    return prior


def wound_hits(text: str):
    """返回 {组名: 命中词列表}"""
    res = {}
    for g, words in WOUND_GROUPS.items():
        hit = [w for w in words if w in text]
        if hit:
            res[g] = hit
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--window", type=int, default=6)
    ap.add_argument("--file", default="", help="新章路径；给出则一并扫新章")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    prior = scan_prior(args.chapter, args.window)
    if not prior:
        print(json.dumps({"error": f"no prior chapters found for {args.chapter}"}, ensure_ascii=False))
        return 2

    # 每组的跨章分布
    group_chapters = {g: [] for g in WOUND_GROUPS}
    number_chapters = {k: [] for k in NUMBER_PATTERNS}
    for n, text in prior.items():
        for g in wound_hits(text):
            group_chapters[g].append(n)
        for k, pat in NUMBER_PATTERNS.items():
            if re.search(pat, text):
                number_chapters[k].append(n)

    hard, soft = [], []

    # 单章密度判据：一章内把某处伤写尽，下一章再写同样是疲劳。
    # 2026-09-25：354 单章出现 16 处手伤描写（手套碳化→掌面碳化→表皮碳化→
    # 筋膜气隙→碳化层碎裂→肌肉融合→三级烧伤→切刀清创→护具→组织液），
    # 355 接着写纹路/抽搐/组织液。跨章计数只判 soft，抓不到这种「单章榨干」。
    SINGLE_CHAPTER_WOUND_DENSITY = 6

    for g, words in WOUND_GROUPS.items():
        # 跨章分布
        chs = group_chapters[g]
        if len(chs) >= 3:
            hard.append({
                "type": "WOUND_HARD", "group": g,
                "chapters": chs, "count": len(chs),
                "msg": f"「{g}」在 {len(chs)} 章内重复出现（{chs}）；新章不得再写实写这一处伤，换伤处或只一句带过",
            })
        elif len(chs) == 2:
            soft.append({
                "type": "WOUND_SOFT", "group": g,
                "chapters": chs, "count": len(chs),
                "msg": f"「{g}」近 {len(chs)} 章出现（{chs}）；新章如再写须换角度",
            })
        # 单章榨干：最近一章内该组词命中总数超阈值
        if chs:
            last = max(chs)
            total = sum(prior[last].count(w) for w in words)
            if total >= SINGLE_CHAPTER_WOUND_DENSITY:
                hard.append({
                    "type": "WOUND_EXHAUSTED_HARD", "group": g,
                    "chapter": last, "hits": total,
                    "msg": f"「{g}」在第 {last} 章单章命中 {total} 次（阈值 {SINGLE_CHAPTER_WOUND_DENSITY}），"
                           f"该处伤已写尽；新章不得再写实写，只可一句带过或换伤处",
                })

    for k, chs in number_chapters.items():
        # 连续章计数
        longest = cur = 1
        for i in range(1, len(chs)):
            cur = cur + 1 if chs[i] == chs[i - 1] + 1 else 1
            longest = max(longest, cur)
        if longest >= 4:
            hard.append({
                "type": "NUMBER_HARD", "item": k,
                "chapters": chs, "streak": longest,
                "msg": f"「{k}」连续 {longest} 章复述（{chs}）；新章最多提一次",
            })

    result = {"chapter": args.chapter, "window": args.window,
              "prior_chapters": sorted(prior), "hard": hard, "soft": soft}

    # 新章自检
    if args.file:
        p = Path(args.file)
        if p.exists():
            new = p.read_text(encoding="utf-8")
            new_w = wound_hits(new)
            violations = []
            for h in hard:
                if h["type"] == "WOUND_HARD" and h["group"] in new_w:
                    violations.append({
                        "type": "WOUND_REPEAT_VIOLATION", "group": h["group"],
                        "words": new_w[h["group"]],
                        "msg": f"新章仍在写「{h['group']}」：{new_w[h['group']]}",
                    })
                if h["type"] == "NUMBER_HARD":
                    c = len(re.findall(NUMBER_PATTERNS[h["item"]], new))
                    if c > 1:
                        violations.append({
                            "type": "NUMBER_REPEAT_VIOLATION", "item": h["item"],
                            "count": c, "msg": f"新章「{h['item']}」出现 {c} 次，最多 1 次",
                        })
            result["new_chapter"] = {"wounds": new_w, "violations": violations}

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        print(f"# 跨章重复扫描 目标章 {args.chapter} 窗口 {args.window}")
        print(f"前置章: {sorted(prior)}\n")
        for h in hard:
            print(f"[HARD] {h['msg']}")
        for s in soft:
            print(f"[soft] {s['msg']}")
        if not hard and not soft:
            print("无重复项")
        if "new_chapter" in result:
            print("\n## 新章自检")
            print("伤处:", result["new_chapter"]["wounds"])
            for v in result["new_chapter"]["violations"]:
                print(f"[VIOLATION] {v['msg']}")
            if not result["new_chapter"]["violations"]:
                print("通过")
    return 1 if (hard or result.get("new_chapter", {}).get("violations")) else 0


if __name__ == "__main__":
    sys.exit(main())
