#!/usr/bin/env python3
"""素材总线 → G2 decision_cards 桥接器

背景：G1 脚本 kewu_selfcycle_g1_20260605.py 硬编码读 2026-06-05 三个旧 JSON；
G2 脚本 run_g2_council.py 读 bridge_runs/decision_cards.json（长期为空）。
今日真素材在 /workspace/素材总线/kewu/audit/usable_unconsumed_readable_YYYYMMDD.json。

本脚本把当日总线卡转成 G2 期望的 decision_cards.json 格式，消除断链。

用法：
    python3 bus_to_g2_bridge.py                    # 用今天日期
    python3 bus_to_g2_bridge.py --date 20260829    # 指定日期
    python3 bus_to_g2_bridge.py --max-cards 40     # 限制卡数（G2 上下文有限）
"""
import argparse
import datetime
import json
import os
from pathlib import Path

BUS_AUDIT = Path("/workspace/素材总线/kewu/audit")
BRIDGE_DIR = Path("/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs")


def load_bus_cards(date_str):
    """读当日总线可用未消费卡。"""
    path = BUS_AUDIT / f"usable_unconsumed_readable_{date_str}.json"
    if not path.exists():
        # fall back to latest available
        candidates = sorted(BUS_AUDIT.glob("usable_unconsumed_readable_*.json"))
        if not candidates:
            raise FileNotFoundError(f"no readable audit file in {BUS_AUDIT}")
        path = candidates[-1]
        print(f"WARN: {date_str} not found, using {path.name}")
    with open(path, encoding="utf-8") as f:
        cards = json.load(f)
    if not isinstance(cards, list):
        raise ValueError(f"{path} is not a list")
    return cards, path


def score_card(c):
    """打分：新鲜度 + 正文长度 + 置信度 + 章节映射。"""
    score = 0.0
    score += float(c.get("confidence_score", 0)) * 10
    body = int(c.get("body_len_effective") or c.get("body_len") or 0)
    if body >= 2000:
        score += 8
    elif body >= 800:
        score += 5
    elif body >= 300:
        score += 2
    age = float(c.get("age_days", 999))
    if age <= 1:
        score += 12
    elif age <= 3:
        score += 8
    elif age <= 7:
        score += 4
    band = c.get("chapter_band", "")
    if band.startswith("P0"):
        score += 10
    elif band.startswith("P1"):
        score += 6
    elif band.startswith("P2"):
        score += 3
    if c.get("verification_status") == "official_verified":
        score += 5
    if c.get("is_new_vs_prev"):
        score += 6
    return score


def to_decision_card(c):
    """转成 G2 期望格式。"""
    return {
        "id": c.get("id", ""),
        "title": c.get("title", "")[:200],
        "domain": (c.get("domain_ids") or ["unknown"])[0],
        "quality": c.get("quality", ""),
        "verification": c.get("verification_status", ""),
        "platform": c.get("platform", ""),
        "url": c.get("url", ""),
        "host": c.get("host", ""),
        "body_len": c.get("body_len_effective") or c.get("body_len") or 0,
        "age_days": c.get("age_days"),
        "created_at": c.get("created_at", ""),
        "chapter_band": c.get("chapter_band", ""),
        "chapter_target": c.get("chapter_target", ""),
        "audit_flags": c.get("audit_flags", []),
        "confidence": c.get("confidence_score"),
        "is_new": c.get("is_new_vs_prev", False),
        "_bridge_score": round(score_card(c), 2),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().strftime("%Y%m%d"))
    ap.add_argument("--max-cards", type=int, default=40)
    ap.add_argument("--min-body", type=int, default=300,
                    help="过滤正文过短的卡（默认 300 字）")
    ap.add_argument("--out-dir", default=None,
                    help="输出 bridge_run 目录；默认按日期新建")
    args = ap.parse_args()

    cards, src_path = load_bus_cards(args.date)

    # filter + rank
    usable = [c for c in cards
              if int(c.get("body_len_effective") or c.get("body_len") or 0) >= args.min_body]
    ranked = sorted(usable, key=score_card, reverse=True)
    selected = ranked[:args.max_cards]

    decision_cards = [to_decision_card(c) for c in selected]

    out_dir = Path(args.out_dir) if args.out_dir else BRIDGE_DIR / f"bus_bridge_{args.date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "decision_cards.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(decision_cards, f, ensure_ascii=False, indent=2)

    meta = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "source": str(src_path),
        "total_bus_cards": len(cards),
        "after_min_body_filter": len(usable),
        "selected": len(decision_cards),
        "min_body": args.min_body,
        "max_cards": args.max_cards,
        "domains": {},
        "bands": {},
        "fresh_le3d": len([c for c in selected if float(c.get("age_days", 999)) <= 3]),
    }
    for c in selected:
        d = (c.get("domain_ids") or ["unknown"])[0]
        meta["domains"][d] = meta["domains"].get(d, 0) + 1
        b = c.get("chapter_band", "NONE")
        meta["bands"][b] = meta["bands"].get(b, 0) + 1
    with open(out_dir / "bridge_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "status": "BRIDGE_OK",
        "decision_cards": str(out_path),
        "count": len(decision_cards),
        "source": src_path.name,
        "domains": meta["domains"],
        "bands": meta["bands"],
        "fresh_le3d": meta["fresh_le3d"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
