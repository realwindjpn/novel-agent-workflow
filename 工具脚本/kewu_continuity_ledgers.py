#!/usr/bin/env python3
"""Generate lightweight continuity, provenance, and budget ledgers for Kewu selfcycle tasks.

This is a controller-side helper. It does not call models and does not alter the
G1→G4 content chain. It reads task artifacts and writes three auditable files:

- output/MODEL_CONTINUITY.md
- output/ROLE_PROVENANCE_LEDGER.jsonl
- output/budget_estimate.json

It is intentionally permissive about missing optional files so it can be used on
older task packages after the fact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

CORE_ROLES = ["author", "editor", "reader", "science", "military", "structure"]
REVIEW_ROLE_HINTS = {
    "editor": ["editor", "deai", "编辑"],
    "reader": ["reader", "读者"],
    "science": ["science", "scientific", "科技", "科学"],
    "military": ["military", "system", "制度", "军事"],
    "structure": ["structure", "final", "终审", "gate"],
}
DEFAULT_TOKENS = {
    "author": {"input": 14000, "output": 4200},
    "editor": {"input": 10000, "output": 1800},
    "reader": {"input": 9000, "output": 1200},
    "science": {"input": 9000, "output": 1400},
    "military": {"input": 9000, "output": 1400},
    "structure": {"input": 6000, "output": 1000},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_provider_model(text: str) -> tuple[str | None, str | None]:
    provider = None
    model = None
    # Preferred ledger form used by Kewu reviews: "provider/model: hs / glm-latest".
    m = re.search(
        r"provider\s*/\s*model\s*[:=]\s*([A-Za-z0-9_.:-]+)\s*/\s*([A-Za-z0-9_.:/-]+)",
        text,
        re.I,
    )
    if m:
        return m.group(1), m.group(2)
    m = re.search(r"provider\s*[:=]\s*([A-Za-z0-9_.:-]+)", text, re.I)
    if m:
        provider = m.group(1)
    # Avoid matching the "model" half inside "provider/model".
    m = re.search(r"(?<!/)\bmodel\s*[:=]\s*([A-Za-z0-9_.:/-]+)", text, re.I)
    if m:
        model = m.group(1)
    # Common prose fallback: hs/glm-latest, sensenova/sensenova-...
    m = re.search(r"\b([A-Za-z0-9_.-]+)/(glm-[A-Za-z0-9_.-]+|grok-[A-Za-z0-9_.-]+|sensenova-[A-Za-z0-9_.-]+|claude-[A-Za-z0-9_.-]+|deepseek-[A-Za-z0-9_.-]+)\b", text)
    if m and not (provider and model):
        provider = provider or m.group(1)
        model = model or m.group(2)
    return provider, model


def verdict(text: str) -> str:
    upper = text.upper()
    if "VERDICT=FAIL" in upper or re.search(r"\bFAIL\b", upper) and "PASS" not in upper:
        return "FAIL"
    if "VERDICT=PASS" in upper or re.search(r"\bPASS\b", upper):
        return "PASS"
    return "UNKNOWN"


def role_from_name(path: Path) -> str:
    low = path.name.lower()
    for role, hints in REVIEW_ROLE_HINTS.items():
        if any(h.lower() in low for h in hints):
            return role
    return "unknown"


def candidate_rows(task: Path) -> list[dict]:
    rows = []
    for p in sorted(task.glob("ch*/candidate_final.md")):
        ch_m = re.search(r"ch(\d+)", str(p))
        rows.append({
            "chapter": int(ch_m.group(1)) if ch_m else None,
            "path": str(p),
            "sha256": sha256(p),
            "bytes": p.stat().st_size,
        })
    mg = task / "output" / "machine_gate_final.json"
    if mg.exists():
        try:
            by_path = {r["path"]: r for r in rows}
            data = json.loads(read_text(mg))
            for item in data.get("reports", []):
                r = by_path.get(item.get("path"))
                if r:
                    r.update({"cjk": item.get("cjk"), "machine_status": item.get("status")})
        except Exception:
            pass
    return rows


def review_rows(task: Path, candidates: list[dict]) -> list[dict]:
    candidate_sha_set = {r["sha256"] for r in candidates}
    rows = []
    review_dir = task / "reviews"
    for p in sorted(review_dir.glob("*.md")) if review_dir.exists() else []:
        text = read_text(p)
        provider, model = extract_provider_model(text)
        mentioned = [s for s in candidate_sha_set if s in text]
        rows.append({
            "ts": datetime.now().isoformat(timespec="seconds"),
            "role": role_from_name(p),
            "provider": provider or "unknown",
            "model": model or "unknown",
            "artifact": str(p),
            "artifact_sha256": sha256(p),
            "candidate_sha256": mentioned[0] if mentioned else None,
            "candidate_sha_bound": bool(mentioned),
            "verdict": verdict(text),
        })
    # Author/raw candidates as provenance too.
    for p in sorted(task.glob("ch*/qwen_author_raw*.md")) + sorted(task.glob("ch*/candidate_final.md")):
        ch_m = re.search(r"ch(\d+)", str(p))
        rows.append({
            "ts": datetime.now().isoformat(timespec="seconds"),
            "role": "author" if "qwen_author" in p.name else "candidate_final",
            "provider": "web_qwen" if "qwen_author" in p.name else "controller_merge",
            "model": "Qwen3.8" if "qwen_author" in p.name else "n/a",
            "artifact": str(p),
            "artifact_sha256": sha256(p),
            "chapter": int(ch_m.group(1)) if ch_m else None,
            "verdict": "ARTIFACT",
        })
    return rows


def continuity_rows(prov: list[dict]) -> list[dict]:
    rows = []
    for role in CORE_ROLES:
        role_rows = [r for r in prov if r.get("role") == role]
        candidates = sorted({f"{r.get('provider')}/{r.get('model')}" for r in role_rows if r.get("provider") and r.get("provider") != "unknown"})
        if len(candidates) >= 2:
            continuity = "READY_WITH_FALLBACK"
        elif len(candidates) == 1:
            continuity = "READY_SINGLE_ROUTE"
        else:
            continuity = "BLOCKED_NO_ROUTE"
        rows.append({"role": role, "routes_seen": candidates, "continuity": continuity, "artifact_count": len(role_rows)})
    return rows


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def write_continuity(path: Path, rows: list[dict], candidates: list[dict]) -> None:
    lines = ["# MODEL_CONTINUITY", "", f"generated_at: {datetime.now().isoformat(timespec='seconds')}", "", "## candidate finals", ""]
    for c in candidates:
        lines.append(f"- ch{c.get('chapter')}: `{c['sha256']}` cjk={c.get('cjk')} status={c.get('machine_status')} path={c['path']}")
    lines += ["", "## role continuity", "", "| role | continuity | routes_seen | artifacts |", "|---|---|---|---:|"]
    for r in rows:
        lines.append(f"| {r['role']} | {r['continuity']} | {', '.join(r['routes_seen']) or '-'} | {r['artifact_count']} |")
    lines += ["", "## note", "", "READY_SINGLE_ROUTE means runnable but fragile; repeated failure should trigger same-role fallback or controller takeover."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def budget_estimate(chapters: int, rounds: int, active_roles: list[str]) -> dict:
    calls = chapters * rounds * len(active_roles)
    role_totals = {}
    input_total = output_total = 0
    for role in active_roles:
        t = DEFAULT_TOKENS.get(role, {"input": 8000, "output": 1000})
        role_calls = chapters * rounds
        role_input = role_calls * t["input"]
        role_output = role_calls * t["output"]
        role_totals[role] = {"calls": role_calls, "input_tokens": role_input, "output_tokens": role_output}
        input_total += role_input
        output_total += role_output
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "chapters": chapters,
        "revision_rounds": rounds,
        "active_roles": active_roles,
        "estimated_calls": calls,
        "input_tokens": input_total,
        "output_tokens": output_total,
        "total_tokens": input_total + output_total,
        "pricing_complete": False,
        "cost_note": "No prices supplied; token/call estimate only.",
        "role_totals": role_totals,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="task directory, e.g. /root/workspace/任务运行态/...")
    ap.add_argument("--rounds", type=int, default=2, help="conservative full revision rounds")
    ns = ap.parse_args()
    task = Path(ns.task)
    if not task.exists():
        raise SystemExit(f"task not found: {task}")
    out = task / "output"
    out.mkdir(parents=True, exist_ok=True)
    candidates = candidate_rows(task)
    prov = review_rows(task, candidates)
    cont = continuity_rows(prov)
    write_jsonl(out / "ROLE_PROVENANCE_LEDGER.jsonl", prov)
    write_continuity(out / "MODEL_CONTINUITY.md", cont, candidates)
    active = [r["role"] for r in cont if r["artifact_count"] > 0 and r["role"] in DEFAULT_TOKENS]
    if "author" not in active:
        active.insert(0, "author")
    (out / "budget_estimate.json").write_text(json.dumps(budget_estimate(max(1, len(candidates)), ns.rounds, active), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"written": [str(out / "MODEL_CONTINUITY.md"), str(out / "ROLE_PROVENANCE_LEDGER.jsonl"), str(out / "budget_estimate.json")], "candidates": len(candidates), "provenance_rows": len(prov)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
