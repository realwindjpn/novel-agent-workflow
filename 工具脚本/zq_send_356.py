#!/usr/bin/env python3
"""CDP 直操：把重写卡投进科武 Qwen 项目新会话。

不走 Playwright 冷启动（profile 被 9223 常驻 Chrome 持有，冷启必撞 metrics override）。
流程：激活 qwen 标签 → 视口探针 → 项目页 fetch 验知识库 → 填卡 → CDP Enter 真发送
     → 轮询回执（取最后一条 assistant 消息） → 剥 UI 残留 → 落盘。
每步都有读回证据，禁自报成功。
"""
import itertools
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

import websocket

CDP = "http://127.0.0.1:9223"
PROJECT_ID = "fb4a25fd-6ef1-46ae-a5c4-07df7c138b3d"
PROMPT = Path("/root/workspace/科武纪元/任务运行态/20260925_kewu_selfcycle_daily/output/REWRITE_CARD_356_zhuque.md")
OUT = Path("/root/workspace/科武纪元/任务运行态/20260925_kewu_selfcycle_daily/output/ch356_zhuque_rewrite_r1.md")
STATE = Path("/root/workspace/科武纪元/任务运行态/20260925_kewu_selfcycle_daily/output/ch356_zq_r1_state.json")
CJK = re.compile(r"[\u4e00-\u9fff]")
UI_JUNK = re.compile(
    r"^(Thinking completed|已经完成思考|Auto|AI-generated content.*|"
    r"I prefer this response|Response \d|\d+\s*/\s*\d+)$")


def tabs():
    return json.loads(urllib.request.urlopen(f"{CDP}/json/list", timeout=8).read())


def activate(tid):
    try:
        urllib.request.urlopen(f"{CDP}/json/activate/{tid}", timeout=5).read()
    except Exception:
        pass


class Tab:
    def __init__(self, target):
        self.ws = websocket.create_connection(
            target["webSocketDebuggerUrl"], suppress_origin=True, timeout=40)
        self.ids = itertools.count(1)

    def call(self, method, params=None):
        i = next(self.ids)
        self.ws.send(json.dumps({"id": i, "method": method, "params": params or {}}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == i:
                if "error" in m:
                    raise RuntimeError(m["error"])
                return m.get("result", {})

    def js(self, expr):
        r = self.call("Runtime.evaluate",
                      {"expression": expr, "returnByValue": True, "awaitPromise": True})
        if "exceptionDetails" in r:
            return "EXC:" + str(r["exceptionDetails"])[:200]
        return r.get("result", {}).get("value")

    def enter(self):
        for t in ("keyDown", "keyUp"):
            self.call("Input.dispatchKeyEvent", {
                "type": t, "key": "Enter", "code": "Enter",
                "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})


def main():
    prompt = PROMPT.read_text(encoding="utf-8")
    # 卡体上限约 7KB（编辑器塞不下就静默丢卡），按字节判不是按字符
    if len(prompt.encode()) < 4000 or len(prompt.encode()) > 7100:
        raise SystemExit(f"PACKAGING_FAIL: 卡体 {len(prompt.encode())}B 越界（需 4000-7100B）")

    ts = [t for t in tabs() if "chat.qwen.ai" in t.get("url", "")]
    proj = [t for t in ts if f"/p/{PROJECT_ID}" in t.get("url", "")]
    if not proj:
        raise SystemExit("NO_PROJECT_TAB")
    tgt = proj[0]
    activate(tgt["id"])
    tb = Tab(tgt)

    # 1 视口探针
    vw = tb.js("innerWidth+'x'+innerHeight")
    if vw == "1x1":
        tb.call("Emulation.setDeviceMetricsOverride",
                {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False})
        time.sleep(1.5)
        vw = tb.js("innerWidth+'x'+innerHeight")
    print(f"[1] viewport={vw}")

    # 2 登录态 + 知识库
    tok = tb.js("(localStorage.getItem('token')||'').length")
    files = tb.js("""(async()=>{const t=localStorage.getItem('token');
        const r=await fetch('/api/v2/projects/%s/files',{headers:{'Authorization':'Bearer '+t}});
        const j=await r.json();
        return JSON.stringify((j.data||j).map(f=>({n:f.name||f.filename,s:f.size})));})()"""
                  % PROJECT_ID)
    print(f"[2] token_len={tok} kb_files={files}")
    if not tok or int(tok) < 50:
        raise SystemExit("LOGIN_NOT_VERIFIED")
    if not files or files == "[]":
        raise SystemExit("KB_FILES_EMPTY")

    # 3 探模型选择器 + 新会话
    model = tb.js("(document.querySelector('[class*=model]')||{}).innerText||''")
    print(f"[3] model_sel={model!r}")

    # 4 填卡
    filled = tb.js("""(()=>{const ta=document.querySelector('textarea,[contenteditable=true],[role=textbox]');
        if(!ta) return 'NO_COMPOSER';
        const v=%s;
        if(ta.tagName==='TEXTAREA'){
            const s=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;
            s.call(ta,v); ta.dispatchEvent(new Event('input',{bubbles:true}));}
        else{ ta.innerText=v; ta.dispatchEvent(new InputEvent('input',{bubbles:true})); }
        return 'LEN='+((ta.value!==undefined?ta.value:ta.innerText)||'').length;})()"""
                  % json.dumps(prompt))
    print(f"[4] filled={filled}")
    if not str(filled).startswith("LEN=") or int(str(filled)[4:]) < len(prompt) * 0.9:
        raise SystemExit(f"FILL_FAIL {filled}")

    # 5 真发送
    before = tb.js("document.querySelectorAll('[data-role=assistant],[class*=assistant-message],[class*=ai-message]').length")
    tb.enter()
    time.sleep(3)
    after = tb.js("document.querySelectorAll('[data-role=assistant],[class*=assistant-message],[class*=ai-message]').length")
    emptied = tb.js("""(()=>{const ta=document.querySelector('textarea,[contenteditable=true]');
        return ((ta&&(ta.value!==undefined?ta.value:ta.innerText))||'').length;})()""")
    print(f"[5] asst {before}->{after} composer_left={emptied}")
    if int(emptied) > 50:
        raise SystemExit("SEND_FAIL: composer 未清空")

    url = tb.js("location.href")
    print(f"[6] url={url}")

    # 7 轮询回执
    # 退出条件不能把字数硬门槛与稳定计数绑在一起：短稿（补段/定点改写）
    # 永远达不到 2600，会空转到超时。稳定 4 轮即出，达标字数另行判。
    stable, last = 0, ""
    deadline = time.time() + 1500
    while time.time() < deadline:
        time.sleep(20)
        got = tb.js("""(()=>{const sel=['[data-role=assistant]','[class*=assistant-message]',
            '[class*=ai-message]','[class*=bot-message]','[class*=markdown]'];
            let best=[];
            for(const s of sel){const n=[...document.querySelectorAll(s)]
                .filter(e=>(e.innerText||'').length>200);
                if(n.length>best.length) best=n;}
            return best.length?(best[best.length-1].innerText||''):''})()""")
        got = got or ""
        n = len(CJK.findall(got))
        print(f"    poll len={len(got)} cjk={n} {'STABLE' if got==last else ''}")
        if got == last and n > 0:
            stable += 1
            if stable >= 4:
                break
        else:
            stable = 0
        last = got

    # 8 剥残留 + 落盘
    lines = [l for l in last.split("\n") if not UI_JUNK.match(l.strip())]
    body = "\n".join(lines).strip()
    if body.startswith("Thinking completed"):
        body = body.split("\n", 1)[1]
    OUT.write_text(body, encoding="utf-8")
    rec = {"url": url, "out": str(OUT), "chars": len(body),
           "cjk": len(CJK.findall(body)), "prompt_bytes": len(prompt.encode()),
           "model_selector": model, "token_len": tok}
    STATE.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[8] saved {OUT} cjk={rec['cjk']}")
    print(json.dumps(rec, ensure_ascii=False))


if __name__ == "__main__":
    main()
