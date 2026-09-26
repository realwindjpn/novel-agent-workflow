#!/usr/bin/env python3
"""人味体系三席审计（2026-09-26 用户口径：回源读全文 → 异构席列覆盖/缺口/误伤边界）。

不摘要送审、不主控自判。三席跨族、任务不重叠：
  A 覆盖度席 (Qwen hy4)   —— 现有规则对第356章实际写法的覆盖情况
  B 缺口席   (Gemini)     —— 谈判/多方对话体裁缺什么
  C 误伤席   (Grok)       —— 哪些现有规则会误伤正常人味

每席独立产物文件，文件为空即作废。
"""
import os
import re
import subprocess
import time
from pathlib import Path

ROOT = Path("/root/workspace/科武纪元")
OUT = ROOT / "任务运行态/20260925_kewu_selfcycle_daily/output/humanize_audit"
OUT.mkdir(parents=True, exist_ok=True)

STYLE_FILES = [
    ROOT / "参考资料/作家风格OS/voice_rules.md",
    ROOT / "参考资料/作家风格OS/scene_method.md",
    ROOT / "参考资料/作家风格OS/bad_phrases.md",
    ROOT / "参考资料/作家风格OS/author_prompt_patch.md",
    Path("/root/workspace/写作角色OS/humanize_ai_check_absorption_20260710.md"),
    ROOT / "写作技巧/写作技法蒸馏.md",
]
CHAPTER = ROOT / "新版/第356章.md"

TASKS = {
    "A_coverage": ("custom:workbuddy-hy3", "cn:hy4-preview", """你是《科武纪元》人味体系审计·覆盖度席。

【硬约束·先读】下面三段「现有规则体系」「第356章正文」已完整内联在你这次对话里。
禁止调用任何工具、禁止尝试读文件、禁止联网。材料齐了，直接基于内联文本作答。
若你觉得材料不足，就写「材料不足」并说明缺哪一块，不许去调工具找。

任务：拿下面这份「现有规则体系」去逐条核对第356章的真实写法，列出：
1. COVERED —— 规则里已有、且第356章确实照做并见效的条目。每条给：规则出处 + 356里的具体例证（引原文片段，标明是哪一段的行为）。
2. UNDERUSED —— 规则里有、但第356章没用上或用得不够的条目。每条给：规则出处 + 为什么这章没吃透 + 该怎么落到这个体裁上。
3. CONFLICT —— 规则之间互相打架、或规则与本项目既有硬约束冲突的地方。每条给出两处原文和裁决建议。

硬要求：
- 必须引原文，禁止凭印象下判断。检索不到就写「未找到例证」，不许编。
- 行号必须真实（356 共 97 行）。行号越界视为幻觉，整份作废。
- 不要给修改后的正文，只给规则层面的结论。
- 结论不许只写 PASS/FAIL，必须写清检查范围与依据。"""),

    "B_gap": ("custom:sensenova", "glm-5.2", """你是《科武纪元》人味体系审计·缺口席。

【硬约束·先读】下面「现有规则体系」「第356章正文」已完整内联在你这次对话里。
禁止调用任何工具、禁止尝试读文件、禁止联网。材料齐了，直接基于内联文本作答。
若你觉得材料不足，就写「材料不足」并说明缺哪一块，不许去调工具找。

背景：第356章是「谈判桌」体裁——多方博弈、席位对坐、文件与程序博弈，没有战斗也没有技术操作。
现有体系明显偏战斗段与技术段。

任务：
1. 现有规则对「谈判/会议/多方对话」这一体裁的覆盖缺口，逐条列。特别检查这几条有没有落进作者席真正注入的风格卡：
   - 莫仁技法3 围-撤-围节奏（打→停→谈）
   - 莫仁技法6 智斗多方博弈（每方各有利益和信息差，不让任何一方全知全能）
   - 姬叉技法5 对话风格随关系定制（光看对话能分辨说话者）
2. 针对第356章，指出这个体裁下「人味」到底由什么构成——现在这章的对话能不能分辨说话者？多方博弈的信息差写出来没有？
3. 给出可执行的补充规则草案，每条要能直接进风格卡（有正例、有反例、有判定口径），不是原则口号。

硬要求：必须引第356章原文举证，行号真实（97 行内），检索不到就写「未找到」。不许编造例证。"""),

    "C_falsepositive": ("custom:bmapi", "gpt-5.6-sol", """你是《科武纪元》人味体系审计·误伤边界席。

【硬约束·先读】下面「现有规则体系」「第356章正文」已完整内联在你这次对话里。
禁止调用任何工具、禁止尝试读文件、禁止联网。材料齐了，直接基于内联文本作答。
若你觉得材料不足，就写「材料不足」并说明缺哪一块，不许去调工具找。

任务：现有规则体系里，哪些条目在执行时会**误伤**正常的人味写法？也就是把好东西当 AI 味改掉。

逐条审：
1. 禁用词表（仿佛/微微/缓缓/意味着/意识到/不禁/不由得/宛如/这一刻/某种意义上/这不仅是…更��…/时代洪流/命运齿轮）——哪些在中文小说里其实是正常用法？给出第356章里的真实命中或同体裁合理用法。
2. 九信号里的 BURSTINESS_FLAT（句长段长均匀）——如果一条规则要求「打散节奏」，会不会反过来逼作者写出花哨的碎句？第356章均句长 10.0 字，风格卡 voice_rules 明写「短句」为目标质感。这两者冲突吗？给裁决。
3. DEAI 规范第三节「禁止中文弯引号」与 humanize 吸收文档「科武正文对白按项目规范使用中文弯引号」直接冲突（第356章有 18 个对白段用「」）。这是谁的错？该怎么改？
4. 九信号 / DEAI / 风格卡 三套规则叠加后，有没有互相打架、或者叠加后门槛高到写不出正常段落的地方？

硬要求：必须引原文举证，行号真实（第356章 97 行内）。不许凭印象。不许建议放宽一切。"""),
}


def build_context() -> str:
    parts = ["# 现有规则体系（回源全文）\n"]
    for p in STYLE_FILES:
        parts.append(f"\n===== {p.name} =====\n{p.read_text(encoding='utf-8')}")
    parts.append(f"\n===== 受审章节：第356章（共 97 行，行号即下表编号）=====\n")
    for i, line in enumerate(CHAPTER.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            parts.append(f"{i}| {line}\n")
    return "".join(parts)


def build_prompt(name: str) -> str:
    """按席名重建 prompt。补跑脚本用此保证提示与 TASKS 同步（禁调工具硬约束）。"""
    _prov, _model, task = TASKS[name]
    return f"{task}\n\n---\n{build_context()}"


def main():
    ctx = build_context()
    (OUT / "context.md").write_text(ctx, encoding="utf-8")
    print(f"上下文 {len(ctx)} 字符 -> {OUT/'context.md'}", flush=True)

    procs = []
    for name, (prov, model, task) in TASKS.items():
        prompt = f"{task}\n\n---\n{ctx}"
        pf = OUT / f"{name}.prompt.md"
        pf.write_text(prompt, encoding="utf-8")
        of = OUT / f"{name}.report.md"
        if of.exists() and of.stat().st_size > 200:
            print(f"[跳过] {name} 已有产物", flush=True)
            continue
        cmd = ["hermes", "chat", "--provider", prov, "-m", model, "-Q", "-q", prompt]
        log = open(OUT / f"{name}.log", "w", encoding="utf-8")
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=log, text=True)
        procs.append((name, p, of, log))
        print(f"[派] {name} {prov}/{model} pid={p.pid}", flush=True)

    for name, p, of, log in procs:
        try:
            out, _ = p.communicate(timeout=900)
        except subprocess.TimeoutExpired:
            p.kill()
            out, _ = p.communicate()
            out = f"[TIMEOUT] {name} 超过 900s"
        log.close()
        of.write_text(out or "", encoding="utf-8")
        size = of.stat().st_size
        head = (out or "").strip().splitlines()[0][:70] if (out or "").strip() else "(空)"
        print(f"[收] {name} rc={p.returncode} {size}B  首行: {head}", flush=True)
        if size < 200:
            print(f"     !! {name} 产物过小，视为作废", flush=True)


if __name__ == "__main__":
    main()
