#!/usr/bin/env python3
"""回收器兜底：消息级选择器失配时，用 body 文本切片取最后一条回执。

背景（2026-09-26 ch356）：Qwen 已生成完整章节（含「（本章完）」），
但 [data-role=assistant] / [class*=assistant-message] / [class*=ai-message] 全部 0 命中，
多段会话下容器类名与脚本假设不符。正解是 skill「三之三」写的 body 文本切片兜底：
定位本轮请求卡末位，正文紧随其后，取到第一个「（本章完）」为止。
"""
import itertools
import json
import re
import urllib.request
from pathlib import Path

import websocket

CDP = "http://127.0.0.1:9223"
CONV = "efd57675-1b77-47c0-9783-f3d7820e37ed"
PROMPT_TAIL = "不把会议改成别的场景，章名与题材不变"   # 本轮卡末句，用于定位正文起点
OUT = Path("/root/workspace/科武纪元/任务运行态/20260925_kewu_selfcycle_daily/output/ch356_zhuque_rewrite_r1.md")
STATE = Path("/root/workspace/科武纪元/任务运行态/20260925_kewu_selfcycle_daily/output/ch356_zq_r1_state.json")
CJK = re.compile(r"[\u4e00-\u9fff]")
TITLE = "第356章 谈判桌上的刀光"
UI_JUNK = re.compile(
    r"^(Thinking completed|已经完成思考|Auto|AI-generated content.*|"
    r"I prefer this response|Response \d|\d+\s*/\s*\d+|Skip|Skip to content)$")


def main():
    tabs = json.loads(urllib.request.urlopen(f"{CDP}/json/list", timeout=8).read())
    tgt = [x for x in tabs if CONV in x.get("url", "")]
    if not tgt:
        raise SystemExit("NO_TAB")
    t = tgt[0]
    urllib.request.urlopen(f"{CDP}/json/activate/{t['id']}", timeout=5).read()
    ws = websocket.create_connection(t["webSocketDebuggerUrl"], suppress_origin=True, timeout=40)
    ids = itertools.count(1)

    def ev(e):
        i = next(ids)
        ws.send(json.dumps({"id": i, "method": "Runtime.evaluate",
                            "params": {"expression": e, "returnByValue": True}}))
        while True:
            m = json.loads(ws.recv())
            if m.get("id") == i:
                return m.get("result", {}).get("result", {}).get("value")

    body = ev("document.body.innerText") or ""
    print(f"body_len={len(body)}")

    # 卡末句之后 = 正文起点
    st = body.rfind(PROMPT_TAIL)
    if st == -1:
        raise SystemExit("CARD_TAIL_NOT_FOUND")
    st += len(PROMPT_TAIL)
    # 正文首个「（本章完）」为终点（卡内要求文本不含该锚，不会误切）
    end = body.find("（本章完）", st)
    if end == -1:
        raise SystemExit("END_ANCHOR_NOT_FOUND")
    end += len("（本章完）")

    raw = body[st:end]
    lines = [l.rstrip() for l in raw.split("\n")]
    lines = [l for l in lines if l.strip() and not UI_JUNK.match(l.strip())]
    # 剥 markdown 标题符，还原裸首行
    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"^#+\s*", "", cleaned)
    # 正文起点可能夹带卡尾残句（最后一段禁改清单），从标题行切
    ti = cleaned.find(TITLE)
    if ti == -1:
        raise SystemExit(f"TITLE_NOT_FOUND in slice (len={len(cleaned)})")
    cleaned = cleaned[ti:].strip()

    OUT.write_text(cleaned, encoding="utf-8")
    rec = {
        "url": f"https://chat.qwen.ai/c/{CONV}",
        "out": str(OUT), "chars": len(cleaned),
        "cjk": len(CJK.findall(cleaned)),
        "first_line": cleaned.split("\n")[0],
        "last_line": [l for l in cleaned.split("\n") if l.strip()][-1],
    }
    STATE.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rec, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
