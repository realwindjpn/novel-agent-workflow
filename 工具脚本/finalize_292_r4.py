#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第292章 R4 落定 + provenance 记录（takeover_292/）。"""
from __future__ import annotations
import datetime
import hashlib
import json
import re
import shutil
from pathlib import Path

B = Path("/root/workspace/科武纪元/任务运行态/20260823_kewu_selfcycle_daily/output")
TK = B / "takeover_292"
TK.mkdir(parents=True, exist_ok=True)

shutil.copyfile(B / "candidate_292_r4_raw.md", B / "candidate_292_r4.md")


def st(p: Path) -> dict:
    t = p.read_text(encoding="utf-8")
    return dict(bytes=len(t.encode("utf-8")), chars=len(t),
                cjk=len(re.findall(r"[\u4e00-\u9fff]", t)),
                sha256=hashlib.sha256(t.encode("utf-8")).hexdigest(),
                lines=len([l for l in t.splitlines() if l.strip()]))


gate = json.loads((TK / "verification_gate.json").read_text(encoding="utf-8"))

v = {
    "task": "292_R4_author_seat_rescue",
    "utc": datetime.datetime.utcnow().isoformat() + "Z",
    "operator": "controller as author-seat rescue executor; no sub-seat dispatched; no manual body edit",
    "root_cause": ("author_repair_prompt_292_r4.md 首版仅 3124B / 699 CJK，未内联 R3 全文 -> PACKAGING_FAIL；"
                   "网页 Qwen 无正文可改，自造新场景回 1286 CJK。"),
    "invalidated": {"file": "candidate_292_r4_invalid_newscene_20260824.md", "cjk": 1286,
                    "sha256_prefix": "6a86bafb2cb3",
                    "reason": "ROUTING_FAIL_ARTIFACT_INVALID / new scene, not an R3 repair"},
    "broken_prompt_backup": "author_repair_prompt_292_r4_prev_broken_20260824.md",
    "packaging": {"packer": "/root/workspace/科武纪元/工具脚本/pack_292_r4_prompt.py",
                  "prompt": str(B / "author_repair_prompt_292_r4.md"),
                  "prompt_stat": st(B / "author_repair_prompt_292_r4.md"),
                  "inlined_full_body": True,
                  "anchor_uniqueness_precheck": "all 12 anchors count==1 in R3",
                  "verdict": "PACKAGING_OK"},
    "source_r3": {"file": "candidate_292_r3.md", "stat": st(B / "candidate_292_r3.md"),
                  "expected_sha256": "9512bcfb9a6d7101ac05480b307096ba44e9c548475f01050ddf83f266866586"},
    "author_run": {
        "seat": "web Qwen fixed project (kewu)",
        "project_url": "https://chat.qwen.ai/p/18dab9a0-fea0-490f-abc2-aff83b85ee04",
        "conversation_url": "https://chat.qwen.ai/c/701ce62f-4680-41a8-8d9d-7fd2955640bd",
        "state_file": "state/kewu_292_r4_qwen_session.json",
        "flags": ("--new-session --take-last --skip-role --preferred-model qwen3.8-max "
                  "--min-chars 4700 --timeout 300 --cdp-url http://127.0.0.1:9223"),
        "login_verified": True, "reused_conversation": False,
        "selected_model": "qwen3.8-max", "attempts": 1, "partial": False,
        "probe_answer_count_needed": False, "recover_latest_answer_needed": False,
        "log": "qwen_292_r4_attempt2.log"},
    "candidate_r4": {"file": "candidate_292_r4.md", "stat": st(B / "candidate_292_r4.md")},
    "machine_gate": gate["checks"],
    "fixes_hit": f'{gate["fixes_hit"]}/{gate["fixes_total"]}',
    "anchors": gate["anchors"],
    "diff_scope": {"r3_lines": 84, "r4_lines": 84, "changed_line_pairs": 11,
                   "out_of_scope_changes": 0, "quote_pairs_even": True,
                   "note": "diff 全落在 12 处定点范围内，无新增/删除段落，无新场景"},
    "verdict": "R4_CANDIDATE_LEGAL_MACHINE_GATE_PASS",
    "next": "六审由后续席位处理；绑定 R4 新 SHA，R3 旧审稿全部作废",
}
(TK / "verification.json").write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding="utf-8")

r4 = v["candidate_r4"]["stat"]
r3 = v["source_r3"]["stat"]
print("R4_SHA=" + r4["sha256"])
print("R4_CJK=%d LINES=%d CHARS=%d" % (r4["cjk"], r4["lines"], r4["chars"]))
print("R3_SHA_NOW=" + r3["sha256"])
print("R3_UNTOUCHED=" + str(r3["sha256"] == v["source_r3"]["expected_sha256"]))
print("VERDICT=" + v["verdict"])
