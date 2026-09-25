import json, os, urllib.request, concurrent.futures as cf

BASE = "http://127.0.0.1:7864/v1"
MODEL = "Qwen3.8-Flash"
CARD = "/root/workspace/科武纪元/任务运行态/20260923_kewu_selfcycle_daily/output/review_355_deai.md"
OUT = "/root/workspace/科武纪元/审核记录/ch355_review_r1/deai_qoder.md"


def call(content, maxtok=4000, timeout=560):
    payload = {"model": MODEL, "stream": False,
               "messages": [{"role": "user", "content": content}],
               "max_tokens": maxtok, "temperature": 0.2}
    req = urllib.request.Request(
        BASE + "/chat/completions", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer sk-local"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    return d["choices"][0]["message"]["content"]


card = open(CARD, encoding="utf-8").read()
try:
    txt = call(card)
    open(OUT, "w", encoding="utf-8").write(txt)
    head = txt.strip().split("\n")[0][:48]
    print(f"deai-qoder ok={bool(txt.strip())} len={len(txt)} first={head}")
except Exception as e:
    print(f"deai-qoder FAIL {type(e).__name__} {str(e)[:200]}")
