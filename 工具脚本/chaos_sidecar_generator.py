#!/usr/bin/env python3
"""
chaos_sidecar_generator.py — 混沌模型 sidecar 生成器 (Phase 1 dry-run)

从 SenseNova/MiroFish bridge 运行产物中读取素材卡、决策卡、bridge 输出，
生成混沌模型 sidecar JSON。只读不写正文/大纲/Wiki/RAG。

用法:
  python3 chaos_sidecar_generator.py --run-dir <bridge_run_dir> [--dry-run] [--json]
  python3 chaos_sidecar_generator.py --help
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

# ── 常量 ──────────────────────────────────────────────────────────────────
CHAOS_VARS = ("A", "B", "C", "D", "E", "O")
CHAOS_VAR_LABELS = {
    "A": "算法主权",
    "B": "算法暴力",
    "C": "群体智能",
    "D": "AI越界",
    "E": "地缘摇摆",
    "O": "秩序熵减",
}
VALID_DISPOSITIONS = ("OUTLINE_PATCH", "CHAPTER_PREP_ONLY", "ARCHIVE_WITH_REASON")
VALID_CARD_STATES = ("fact_card", "opinion_card", "trigger_card")

# source_type → 默认 card_state
SOURCE_TYPE_TO_CARD = {
    "official": "fact_card",
    "academic": "fact_card",
    "primary": "fact_card",
    "secondary": "fact_card",
    "expert": "opinion_card",
    "opinion": "opinion_card",
    "commentary": "opinion_card",
    "discovery": "trigger_card",
    "simulation": "trigger_card",
    "mixed": "trigger_card",
}

# 关键词 → 变量映射
KEYWORD_VAR_MAP: list[tuple[list[str], str]] = [
    (["芯片", "算力", "许可", "云接口", "模型治理", "资本闭环", "半导体", "GPU", "供应链", "制裁"], "A"),
    (["白盾", "UGV", "无人机", "执法", "自动武器", "边境", "误伤", "执法系统"], "B"),
    (["蜂群", "黑市", "代理网络", "去中心化", "群体智能", "分布式"], "C"),
    (["AI越界", "目标函数", "权限", "审计", "模型漂移", "拒停", "自主武器", "自动化"], "D"),
    (["航道", "月面", "欧陆", "中东", "地缘", "联盟", "主权", "红线", "神舟", "深空", "月球", "航天"], "E"),
    (["开源", "验证", "冗余", "适应性", "共生", "分布式制造", "韧性"], "O"),
]

# 反馈回路类型
FEEDBACK_LOOP_TYPES = [
    {
        "loop_id": "fact_constraint",
        "name": "事实回路",
        "direction": "fact_card -> 技术/制度约束",
        "output_fields": ["红线", "事实锚", "补证需求"],
    },
    {
        "loop_id": "opinion_motive",
        "name": "观点回路",
        "direction": "opinion_card -> 动机/策略解释",
        "output_fields": ["势力动机", "舆论压力", "制度摩擦"],
    },
    {
        "loop_id": "plot_trigger",
        "name": "剧情触发回路",
        "direction": "trigger_card -> 章节队列",
        "output_fields": ["OUTLINE_PATCH", "CHAPTER_PREP_ONLY"],
    },
    {
        "loop_id": "reverse_constraint",
        "name": "反向约束回路",
        "direction": "章节审修 -> 大纲/素材门禁",
        "output_fields": ["ARCHIVE", "DOWNGRADE", "补采任务"],
    },
    {
        "loop_id": "amplification",
        "name": "放大回路",
        "direction": "小事件 -> 多变量耦合",
        "output_fields": ["escalation_chain"],
    },
]


# ── 工具函数 ──────────────────────────────────────────────────────────────
def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def sha(s: str, n: int = 10) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:n]


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def classify_card_state(source_type: str, title: str, disposition: str) -> str:
    """根据 source_type 和 disposition 信号推断三态。"""
    st = (source_type or "").lower()
    if st in SOURCE_TYPE_TO_CARD:
        return SOURCE_TYPE_TO_CARD[st]
    t = (title or "").lower()
    if any(k in t for k in ("观点", "评论", "看法", "分析")):
        return "opinion_card"
    if any(k in t for k in ("触发", "冲突", "升级", "危机")):
        return "trigger_card"
    if disposition == "OUTLINE_PATCH":
        return "trigger_card"
    return "fact_card"


def infer_chaos_vars(title: str, source_type: str) -> list[str]:
    """从标题和来源推断混沌变量。"""
    text = (title or "") + " " + (source_type or "")
    vars_found: list[str] = []
    for keywords, var in KEYWORD_VAR_MAP:
        if any(k in text for k in keywords):
            if var not in vars_found:
                vars_found.append(var)
    if not vars_found:
        vars_found.append("E")
    return vars_found[:3]


def infer_affected_lines(vars_list: list[str]) -> list[str]:
    """根据变量推断影响线。"""
    line_map = {
        "A": ["科学线", "国际关系线"],
        "B": ["军事线", "人物动机线"],
        "C": ["人物动机线", "舆论线"],
        "D": ["科学线", "军事线"],
        "E": ["国际关系线", "人物动机线"],
        "O": ["科学线", "舆论线"],
    }
    lines: list[str] = []
    for v in vars_list:
        for line in line_map.get(v, []):
            if line not in lines:
                lines.append(line)
    return lines or ["科学线"]


def compute_impact_score(disposition: str, evidence_complete: bool, source_type: str) -> float:
    """计算影响分。"""
    base = {"OUTLINE_PATCH": 0.85, "CHAPTER_PREP_ONLY": 0.65, "ARCHIVE_WITH_REASON": 0.30}
    score = base.get(disposition, 0.40)
    if evidence_complete:
        score += 0.05
    st = (source_type or "").lower()
    if st in ("official", "academic", "primary"):
        score += 0.05
    elif st in ("discovery", "secondary"):
        score -= 0.05
    return round(min(max(score, 0.0), 1.0), 2)


def compute_confidence(evidence_complete: bool, source_type: str) -> str:
    if evidence_complete and (source_type or "").lower() in ("official", "academic", "primary"):
        return "high"
    if evidence_complete:
        return "medium"
    return "low"


def evidence_level(source_type: str, evidence_complete: bool) -> str:
    st = (source_type or "").lower()
    if not evidence_complete:
        return "body_missing"
    if st in ("official", "primary"):
        return "official_body"
    if st == "academic":
        return "academic_body"
    if st == "secondary":
        return "body_valid_secondary"
    return "discovery_only"


# ── 核心生成 ──────────────────────────────────────────────────────────────
def generate_sidecar(run_dir: Path) -> dict[str, Any]:
    """从 bridge run 目录生成混沌 sidecar。"""
    bridge_dir = run_dir
    if (run_dir / "cards").is_dir() and not (run_dir / "decision_cards.json").exists():
        # 这是 SenseNova run dir，找对应 bridge run
        bridge_dir = None
        integration = Path("/root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606")
        latest = integration / "LATEST_VALID_BRIDGE_RUN.json"
        if latest.exists():
            ld = load_json(latest)
            bd = ld.get("per_run_bridge_dir")
            if bd:
                bridge_dir = Path(bd)
        if bridge_dir is None:
            # 尝试 bridge_runs 中找
            br_base = integration / "bridge_runs"
            if br_base.is_dir():
                candidates = sorted(br_base.iterdir(), reverse=True)
                for c in candidates:
                    if (c / "decision_cards.json").exists():
                        bridge_dir = c
                        break
        if bridge_dir is None:
            print("ERROR: 无法找到 bridge run 目录。请直接指定含 decision_cards.json 的目录。", file=sys.stderr)
            sys.exit(1)

    decision_cards_path = bridge_dir / "decision_cards.json"
    if not decision_cards_path.exists():
        print(f"ERROR: 找不到 decision_cards.json: {decision_cards_path}", file=sys.stderr)
        sys.exit(1)

    feed_path = bridge_dir / "mirofish_feed_package.json"
    conversion_path = bridge_dir / "card_conversion_tasks.json"

    decision_cards = load_json(decision_cards_path, [])
    feed_package = load_json(feed_path, {})
    conversion_tasks = load_json(conversion_path, [])

    run_id = feed_package.get("source_pipeline_state", {}).get("run_id", bridge_dir.name)
    created_at = now_iso()

    # ── 1. perturbation_cards ─────────────────────────────────────────
    perturbation_cards: list[dict] = []
    for card in decision_cards:
        title = card.get("title", "")
        source_type = card.get("source_type", "")
        disposition = card.get("disposition", "ARCHIVE_WITH_REASON")
        evidence_complete = card.get("evidence_complete", False)
        material_id = card.get("material_id", "")

        card_state = classify_card_state(source_type, title, disposition)
        vars_list = infer_chaos_vars(title, source_type)
        imp_score = compute_impact_score(disposition, evidence_complete, source_type)
        conf = compute_confidence(evidence_complete, source_type)
        ev_level = evidence_level(source_type, evidence_complete)
        affected = infer_affected_lines(vars_list)

        pc: dict[str, Any] = {
            "material_id": material_id,
            "title": title,
            "card_state": card_state,
            "source_type": source_type,
            "chaos_vars": vars_list,
            "affected_lines": affected,
            "story_value": card.get("story_value", "medium"),
            "evidence_level": ev_level,
            "evidence_complete": evidence_complete,
            "impact_score": imp_score,
            "confidence": conf,
            "disposition": disposition,
            "disposition_reason": card.get("disposition_reason", ""),
        }

        # 专家观点字段
        if card_state == "opinion_card":
            pc["expert_view"] = {
                "expert": "unknown",
                "view_type": "phenomenon",
                "claim_summary": title,
                "confidence": conf,
                "allowed_use": ["motive", "public_opinion"],
                "forbidden_use": ["fact_anchor_without_primary"],
            }

        perturbation_cards.append(pc)

    # ── 2. chaos_signals ──────────────────────────────────────────────
    chaos_signals: list[dict] = []
    for pc in perturbation_cards:
        sig_id = f"CS-{run_id}-{sha(pc['material_id'])}"
        sig: dict[str, Any] = {
            "signal_id": sig_id,
            "source_material_ids": [pc["material_id"]],
            "card_state": pc["card_state"],
            "disposition": pc["disposition"],
            "variables": pc["chaos_vars"],
            "affected_lines": pc["affected_lines"],
            "impact_score": pc["impact_score"],
            "confidence": pc["confidence"],
            "evidence_level": pc["evidence_level"],
            "amplification_path": _amplification_path(pc),
            "downgrade_reason": pc.get("disposition_reason", "") if pc["disposition"] == "ARCHIVE_WITH_REASON" else "",
        }
        chaos_signals.append(sig)

    # ── 3. chaos_state ────────────────────────────────────────────────
    signal_counts: dict[str, int] = {s: 0 for s in VALID_CARD_STATES}
    disposition_counts: dict[str, int] = {d: 0 for d in VALID_DISPOSITIONS}
    var_pressure: dict[str, float] = {v: 0.0 for v in CHAOS_VARS}
    for sig in chaos_signals:
        signal_counts[sig["card_state"]] = signal_counts.get(sig["card_state"], 0) + 1
        disposition_counts[sig["disposition"]] = disposition_counts.get(sig["disposition"], 0) + 1
        for v in sig["variables"]:
            var_pressure[v] = round(var_pressure[v] + sig["impact_score"], 2)

    chaos_state: dict[str, Any] = {
        "version": "sidecar-v0.1",
        "run_id": run_id,
        "generated_at": created_at,
        "total_signals": len(chaos_signals),
        "signal_counts": signal_counts,
        "disposition_counts": disposition_counts,
        "variable_pressure": {v: {"score": var_pressure[v], "label": CHAOS_VAR_LABELS[v]} for v in CHAOS_VARS},
        "sense_gate": "PASS" if signal_counts.get("fact_card", 0) + signal_counts.get("opinion_card", 0) + signal_counts.get("trigger_card", 0) > 0 else "BLOCKED",
        "mirofish_gate": feed_package.get("mirofish_input_gate", {}).get("status", "UNKNOWN"),
    }

    # ── 4. feedback_loops ─────────────────────────────────────────────
    feedback_loops: list[dict] = []
    for loop in FEEDBACK_LOOP_TYPES:
        active_signals = []
        for sig in chaos_signals:
            if loop["loop_id"] == "fact_constraint" and sig["card_state"] == "fact_card":
                active_signals.append(sig["signal_id"])
            elif loop["loop_id"] == "opinion_motive" and sig["card_state"] == "opinion_card":
                active_signals.append(sig["signal_id"])
            elif loop["loop_id"] == "plot_trigger" and sig["card_state"] == "trigger_card":
                active_signals.append(sig["signal_id"])
            elif loop["loop_id"] == "amplification" and len(sig["variables"]) >= 2:
                active_signals.append(sig["signal_id"])
            elif loop["loop_id"] == "reverse_constraint" and sig["disposition"] == "ARCHIVE_WITH_REASON":
                active_signals.append(sig["signal_id"])

        fl: dict[str, Any] = {
            "loop_id": loop["loop_id"],
            "name": loop["name"],
            "direction": loop["direction"],
            "output_fields": loop["output_fields"],
            "active_signal_count": len(active_signals),
            "active_signal_ids": active_signals[:10],
            "status": "active" if active_signals else "idle",
        }
        feedback_loops.append(fl)

    # ── 5. chapter_queue_impact ───────────────────────────────────────
    chapter_impacts: list[dict] = []
    for sig in chaos_signals:
        if sig["disposition"] in ("CHAPTER_PREP_ONLY", "OUTLINE_PATCH"):
            queue_action = "G3_PREP_APPEND" if sig["disposition"] == "CHAPTER_PREP_ONLY" else "OUTLINE_REMARK_CANDIDATE"
            ci: dict[str, Any] = {
                "signal_id": sig["signal_id"],
                "material_id": sig["source_material_ids"][0] if sig["source_material_ids"] else "",
                "card_state": sig["card_state"],
                "variables": sig["variables"],
                "impact_score": sig["impact_score"],
                "affected_lines": sig["affected_lines"],
                "queue_action": queue_action,
                "constraints": ["不改已投稿TXT", "不升版本号", "先大纲再具体章节"],
            }
            chapter_impacts.append(ci)

    # 归档信号汇总
    archived_signals = [sig for sig in chaos_signals if sig["disposition"] == "ARCHIVE_WITH_REASON"]
    chapter_queue_impact: dict[str, Any] = {
        "total_active": len(chapter_impacts),
        "total_archived": len(archived_signals),
        "chapter_impacts": chapter_impacts,
        "archived_summary": [
            {"signal_id": s["signal_id"], "reason": s["downgrade_reason"]} for s in archived_signals
        ],
    }

    # ── 汇总 ──────────────────────────────────────────────────────────
    sidecar: dict[str, Any] = {
        "$schema": "chaos_sidecar_v0.1",
        "chaos_signals": chaos_signals,
        "chaos_state": chaos_state,
        "perturbation_cards": perturbation_cards,
        "feedback_loops": feedback_loops,
        "chapter_queue_impact": chapter_queue_impact,
    }
    return sidecar


def _amplification_path(pc: dict) -> list[str]:
    """根据卡状态推断放大路径。"""
    path = ["事实约束"] if pc["card_state"] == "fact_card" else ["观点解释"]
    if len(pc.get("chaos_vars", [])) >= 2:
        path.append("变量耦合")
    path.extend(["势力反馈", "章节冲突"])
    return path


# ── 报告生成 ──────────────────────────────────────────────────────────────
def generate_markdown_report(sidecar: dict, run_dir: Path, dry_run: bool) -> str:
    state = sidecar["chaos_state"]
    sigs = sidecar["chaos_signals"]
    loops = sidecar["feedback_loops"]
    impact = sidecar["chapter_queue_impact"]

    lines: list[str] = []
    lines.append("# Chaos Sidecar Dry-Run Report")
    lines.append("")
    lines.append(f"- generated_at: {state['generated_at']}")
    lines.append(f"- run_id: {state['run_id']}")
    lines.append(f"- source_run_dir: {run_dir}")
    lines.append(f"- dry_run: {dry_run}")
    lines.append(f"- total_signals: {state['total_signals']}")
    lines.append(f"- sense_gate: {state['sense_gate']}")
    lines.append(f"- mirofish_gate: {state['mirofish_gate']}")
    lines.append("")
    lines.append("## Signal counts")
    for k, v in state["signal_counts"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Disposition counts")
    for k, v in state["disposition_counts"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Variable pressure")
    for v, info in state["variable_pressure"].items():
        lines.append(f"- {v} ({info['label']}): {info['score']}")
    lines.append("")
    lines.append("## Feedback loops")
    for loop in loops:
        lines.append(f"- {loop['name']}: {loop['status']} ({loop['active_signal_count']} signals)")
    lines.append("")
    lines.append("## Chapter queue impact")
    lines.append(f"- active: {impact['total_active']}")
    lines.append(f"- archived: {impact['total_archived']}")
    lines.append("")
    lines.append("## Signal table")
    lines.append("")
    lines.append("| signal_id | card_state | variables | impact | disposition | confidence |")
    lines.append("|---|---|---|---|---|---|")
    for sig in sigs:
        lines.append(f"| {sig['signal_id']} | {sig['card_state']} | {','.join(sig['variables'])} | {sig['impact_score']} | {sig['disposition']} | {sig['confidence']} |")
    lines.append("")
    lines.append("## Perturbation cards")
    lines.append("")
    for pc in sidecar["perturbation_cards"]:
        lines.append(f"- **{pc['material_id']}**: {pc['title'][:60]}")
        lines.append(f"  - state={pc['card_state']} vars={','.join(pc['chaos_vars'])} imp={pc['impact_score']} disp={pc['disposition']}")
    lines.append("")
    lines.append("## Chapter impact details")
    lines.append("")
    if impact["chapter_impacts"]:
        for ci in impact["chapter_impacts"]:
            lines.append(f"- {ci['signal_id']}: action={ci['queue_action']} vars={','.join(ci['variables'])} score={ci['impact_score']}")
    else:
        lines.append("- (无活跃章节影响)")
    lines.append("")
    lines.append("## Archive summary")
    if impact["archived_summary"]:
        for a in impact["archived_summary"]:
            lines.append(f"- {a['signal_id']}: {a['reason'][:80]}")
    else:
        lines.append("- (无归档)")
    lines.append("")
    lines.append("---")
    lines.append("*本报告由 chaos_sidecar_generator.py dry-run 生成。未修改正文/大纲/Wiki/RAG。*")
    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="混沌模型 sidecar 生成器 (dry-run)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
               "  python3 chaos_sidecar_generator.py --run-dir /path/to/bridge_run --dry-run\n"
               "  python3 chaos_sidecar_generator.py --run-dir /path/to/bridge_run --json --dry-run\n",
    )
    p.add_argument("--run-dir", required=True, help="bridge run 或 SenseNova run 目录路径")
    p.add_argument("--dry-run", action="store_true", default=False, help="只输出到 stdout 或 /tmp，不写正式 run 目录")
    p.add_argument("--json", action="store_true", default=False, help="输出 JSON 而非 markdown 报告")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        print(f"ERROR: 目录不存在: {run_dir}", file=sys.stderr)
        sys.exit(1)

    sidecar = generate_sidecar(run_dir)

    if args.dry_run:
        if args.json:
            output = json.dumps(sidecar, ensure_ascii=False, indent=2)
        else:
            output = generate_markdown_report(sidecar, run_dir, dry_run=True)

        # 输出到 stdout
        print(output)

        # 同时写到 /tmp
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = ".json" if args.json else ".md"
        tmp_path = Path(f"/tmp/chaos_sidecar_dryrun_{ts}{suffix}")
        tmp_path.write_text(output, encoding="utf-8")
        print(f"\n[DRY-RUN] 输出已保存: {tmp_path}", file=sys.stderr)
    else:
        # 非 dry-run 模式暂不实现正式写入，Phase 1 只做 dry-run
        print("ERROR: 非 dry-run 模式尚未实现。请加 --dry-run 参数。", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
