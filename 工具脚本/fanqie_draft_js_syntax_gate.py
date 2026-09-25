#!/usr/bin/env python3
"""fanqie_update_draft_chapter.py JS 模板语法回归闸。

2026-09-25 事故：--chapter 351 报 "SyntaxError: Invalid or unexpected token"。
根因：JS 模板里一条中文注释写了「不转换 \\n 为段落」，f-string 反转义后
\\n 变成真换行，把注释切断，后半行裸中文落在字符串外 → 语法错。
人工点「存草稿」能成功，所以现象极具迷惑性（看起来像页面/权限问题）。

本闸：对每章真实生成的 JS 跑 node --check；任何一章失败即 FAIL。
应在修改该脚本的 JS 模板后立即运行。
"""
import json, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, "/root/workspace/科武纪元/工具脚本")
import fanqie_update_draft_chapter as m

PROJECT = Path("/root/workspace/科武纪元")
CHAPTERS = [int(a) for a in sys.argv[1:]] or [349, 350, 351, 352, 353, 354, 355]


def capture(js_box: dict):
    """捕获 replace_body 期间 ALL js_eval 调用（adapter 主路径 + fallback 都要验）。

    2026-09-25：只取最后一次会漏掉 adapter 主路径——它才是真正出语法错的那段。
    """
    def fake(session, js, timeout=60, state_path=None):
        js_box.setdefault("all", []).append(js)
        js_box["js"] = js
        return {"ok": True}
    return fake


fails = []
for ch in CHAPTERS:
    try:
        data = m.parse_local(PROJECT, ch)
    except Exception as e:
        print(f"{ch}: SKIP ({type(e).__name__}: {str(e)[:60]})")
        continue
    box = {}
    orig = m.js_eval
    m.js_eval = capture(box)
    try:
        m.replace_body("dry", data)
    except Exception:
        pass
    finally:
        m.js_eval = orig
    js_list = box.get("all") or ([box["js"]] if box.get("js") else [])
    if not js_list:
        print(f"{ch}: NO_JS_CAPTURED")
        fails.append((ch, "no_js"))
        continue
    for idx, js in enumerate(js_list):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(js)
            p = f.name
        r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
        status = "PASS" if r.returncode == 0 else "FAIL"
        print(f"{ch}: [{idx}] {status}  js_len={len(js)}")
        if r.returncode != 0:
            tail = [l for l in (r.stderr or "").strip().split("\n") if "SyntaxError" in l or "Error" in l]
            print("    ", tail[0][:160] if tail else "")
            fails.append((ch, r.stderr[:200]))

print()
if fails:
    print(f"JS_TEMPLATE_GATE: FAIL ({len(fails)} 章语法错)")
    sys.exit(1)
print("JS_TEMPLATE_GATE: PASS")
