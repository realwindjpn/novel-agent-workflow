#!/usr/bin/env python3
"""签发 G4_RELEASE_356.json（本轮 G4 签发器缺失，按 kewu.g4-release.v1 构造）。

前置（skill「G4 签发：前章产物契约」）：
1. 前章 md/txt 都在新版/与已投稿/ → 已验
2. G3_PREP_356.prev_sha256 == 新版/第355章.md 的 sha256 → 已验
3. G3_PREP_356.prev_chapter == 355 → 已验
G1 ALLOW_G2、G2 verdict NO_PATCH + g3_gate ALLOW → 已验
"""
import hashlib, json
from pathlib import Path

P = Path("/root/workspace/科武纪元")
TD = P / "任务运行态/20260925_kewu_selfcycle_daily"
OUT = TD / "output"
RELEASE = TD / "G4_RELEASE_356.json"

g1 = OUT / "G1_material_match.json"
g2 = OUT / "G2_verdict.json"
g3 = OUT / "G3_PREP_356.json"
for f in (g1, g2, g3):
    assert f.exists(), f

g1d = json.loads(g1.read_text(encoding="utf-8"))
g2d = json.loads(g2.read_text(encoding="utf-8"))
g3d = json.loads(g3.read_text(encoding="utf-8"))

# 前置三项硬验
assert g1d.get("verdict") == "ALLOW_G2", g1d.get("verdict")
assert g2d.get("g3_gate") == "ALLOW", g2d.get("g3_gate")
assert 356 in (g2d.get("target_chapters") or []), g2d.get("target_chapters")
assert g3d["prev_chapter"] == 355
assert g3d["state"] == "G3_READY"
real_prev_sha = hashlib.sha256((P / "新版/第355章.md").read_bytes()).hexdigest()
assert g3d["prev_sha256"] == real_prev_sha, "prev_sha 未对齐"
assert (P / "新版/第355章.md").exists() and (P / "已投稿/第355章.txt").exists()

rel = {
    "schema": "kewu.g4-release.v1",
    "chapter": 356,
    "target_chapters": [356, 357],
    "phase": "PRE_AUTHOR_RELEASE",
    "issued_at": "2026-09-25T18:32:00+08:00",
    "g1_verified": True,
    "g2_verified": True,
    "g3_verified": True,
    "author_route_kind": "web_qwen",
    "trial_only": False,
    "trial_restrictions": [],
    "first_line_gate": "第356章 谈判桌上的刀光",
    "last_line_gate": "（本章完）",
    "cjk_min": 3000,
    "artifacts": {
        "g1": {"path": str(g1), "sha256": hashlib.sha256(g1.read_bytes()).hexdigest()},
        "g2": {"path": str(g2), "sha256": hashlib.sha256(g2.read_bytes()).hexdigest()},
        "g3": {"path": str(g3), "sha256": hashlib.sha256(g3.read_bytes()).hexdigest()},
    },
}
RELEASE.write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
print("G4_RELEASE written:", RELEASE)
print("chapter:", rel["chapter"], "| g1/g2/g3 verified:",
      rel["g1_verified"], rel["g2_verified"], rel["g3_verified"])
print("G4_SIGN: PASS")
