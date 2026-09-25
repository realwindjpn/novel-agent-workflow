#!/usr/bin/env python3
"""从第355章 v10 定稿 MD 重建「已投稿/第355章.txt」。

背景：旧 TXT 只有 644 字节，是被废弃的「合成她」版（主角/性别错乱），
必须按 v10（SHA 81ef715d / CJK 3003）重建。

格式照第351章 TXT：
  第N章 标题
  <正文>
  （本章完）
  <空行>
  作者有话说：
  <note>
"""
import re, hashlib, sys
from pathlib import Path

P = Path("/root/workspace/科武纪元")
MD = P / "新版" / "第355章.md"
TXT = P / "已投稿" / "第355章.txt"

NOTE_TASK = P / "任务运行态/20260923_kewu_selfcycle_daily/output/ch355_note_task.md"
PLACEHOLDER_RE = re.compile(r"^[<＜].*?[>＞]$")  # 任务卡里的 <正文，120-260 字…> 占位符


def _looks_real(s: str) -> bool:
    s = (s or "").strip()
    if not s or PLACEHOLDER_RE.match(s):
        return False
    n = len(re.findall(r"[\u4e00-\u9fff]", s))
    return 120 <= n <= 260


note = None
# ① 优先取 gate 脚本里已过四门禁的定稿（唯一可信源）
g = (P / "工具脚本/ch355_note_gate.py").read_text(encoding="utf-8")
m = re.search(r'RAW = """(.+?)"""', g, flags=re.S)
if m:
    ls = [l for l in m.group(1).strip().split("\n") if l.strip()]
    if len(ls) >= 2 and _looks_real(ls[1]):
        note = ls[1].strip()

# ② 回退：任务卡（须非占位符且在字数区间）
if note is None and NOTE_TASK.exists():
    s = NOTE_TASK.read_text(encoding="utf-8")
    mm = re.search(r"^作者有话说：\s*\n(.+)$", s, flags=re.M)
    if mm and _looks_real(mm.group(1)):
        note = mm.group(1).strip()
assert note, "拿不到已过门禁的作者有话说（可能是占位符未替换）"
assert _looks_real(note), "作者说疑似占位符或字数越界"

md = MD.read_text(encoding="utf-8").strip()
lines = md.split("\n")
head = lines[0].strip()
assert re.match(r"^第355章\s+\S+", head), head
title = head.split(None, 1)[1].strip()

body = "\n".join(lines[1:]).strip()
assert body.endswith("（本章完）"), "正文未以（本章完）结束"
assert "作者有话说" not in body, "MD 正文含作者说"

cjk = len(re.findall(r"[\u4e00-\u9fff]", md))
print("MD CJK:", cjk, "| title:", title)

out = f"{head}\n\n{body}\n\n作者有话说：\n{note}\n"
if TXT.exists():
    bak = P / "archive" / "ch355_txt_pre_rebuild_20260925.txt"
    bak.write_text(TXT.read_text(encoding="utf-8-sig"), encoding="utf-8")
    print("旧 TXT 已备份 ->", bak)
TXT.write_text(out, encoding="utf-8")

# 回读校验
back = TXT.read_text(encoding="utf-8-sig")
bl = back.strip().splitlines()
assert bl[0].strip() == head
assert "作者有话说：" in back
b_body = "\n".join(bl[1:]).split("作者有话说：", 1)[0].strip()
assert b_body.endswith("（本章完）")
bw = len(re.sub(r"\s+", "", b_body))
print("TXT body_words(番茄口径):", bw)
print("TXT SHA:", hashlib.sha256(back.encode()).hexdigest()[:16])
print("TXT_REBUILD: PASS")
