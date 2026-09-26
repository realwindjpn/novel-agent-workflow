#!/usr/bin/env python3
"""B/C 两席串行补跑（2026-09-26）。

并行三席时 yezi-gemini / chun-grok46 被 hermes 内部 fallback 链判超时，报
「No reply: every provider in the fallback chain kept failing over」。
手动单跑 B 席不报错、直接撞 420s 工具上限 → 判定是**生成慢 + 并行抢资源**，
不是节点失效。故改为串行、每席 1500s、不带 -q 静默掩盖。

按止损铁律：同一路线失败 3 次即上报人工裁决，本次为第 1 次重试。
"""
import os
import subprocess
import sys
from pathlib import Path

OUT = Path("/root/workspace/科武纪元/任务运行态/20260925_kewu_selfcycle_daily/output/humanize_audit")

SEATS = [
    ("B_gap", "custom:sensenova", "glm-5.2"),
    ("C_falsepositive", "agnes-text", "agnes-3.0-flash"),
]
PER_SEAT_TIMEOUT = 900


def main() -> None:
    only = sys.argv[1:] or [n for n, _, _ in SEATS]
    for name, prov, model in SEATS:
        if name not in only:
            continue
        of = OUT / f"{name}.report.md"
        if of.exists() and of.stat().st_size > 800 and "No reply" not in of.read_text(encoding="utf-8")[:200] \
           and "Stream stalled" not in of.read_text(encoding="utf-8")[:200]:
            print(f"[跳过] {name} 已有有效产物", flush=True)
            continue
        pf = OUT / f"{name}.prompt.md"
        # prompt 一律由主派工脚本重新生成，确保带上最新的「禁止调工具」硬约束
        sys.path.insert(0, str(Path(__file__).parent))
        try:
            import humanize_audit_3seats as main_mod
            prompt = main_mod.build_prompt(name)
        except Exception as e:  # 主模块不可导入时回退读盘
            print(f"     !! 主模块导入失败({e})，回退读盘 prompt", flush=True)
            prompt = pf.read_text(encoding="utf-8")
        pf.write_text(prompt, encoding="utf-8")
        print(f"[跑] {name} {prov}/{model} prompt={len(prompt)}字符 timeout={PER_SEAT_TIMEOUT}s", flush=True)
        stderr = ""
        try:
            p = subprocess.run(
                ["hermes", "chat", "--provider", prov, "-m", model, "-Q", "-q", prompt],
                capture_output=True, text=True, timeout=PER_SEAT_TIMEOUT,
            )
            out = p.stdout or ""
            stderr = p.stderr or ""
        except subprocess.TimeoutExpired as e:
            partial = e.stdout or ""
            out = (partial if isinstance(partial, str) else partial.decode("utf-8", "replace"))
            out += f"\n[TIMEOUT] 超过 {PER_SEAT_TIMEOUT}s"
        of.write_text(out, encoding="utf-8")
        size = of.stat().st_size
        head = out.strip().splitlines()[0][:70] if out.strip() else "(空)"
        bad = size < 200 or "No reply" in out[:200]
        print(f"[收] {name} {size}B 首行:{head}{'  !! 作废' if bad else ''}", flush=True)
        if bad:
            print(f"     stderr: {stderr[:300]}", flush=True)


if __name__ == "__main__":
    main()
