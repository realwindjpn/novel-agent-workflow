import sys, json, urllib.request

sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]
BASE = "https://api-yi-hydrogel.seeseed1ck.icu/v1"
KEY = C.get_env_value_prefer_dotenv("YI_HYDROGEL_API_KEY")
OUT = "/root/workspace/科武纪元/审核记录/ch355_review_r1/science_mil.md"
CARD = "/root/workspace/科武纪元/任务运行态/20260923_kewu_selfcycle_daily/output/review_355_science_mil.md"

# 用户指定同节点顺序：grok-4.7 -> qwen3.7-plus -> mimo-v2.6-flash -> grok-4.6
CHAIN = ["grok-4.7", "qwen3.7-plus", "mimo-v2.6-flash", "grok-4.6"]


def call(model, content, maxtok=8000, timeout=560):
    payload = {"model": model, "stream": False,
               "messages": [{"role": "user", "content": content}], "max_tokens": maxtok}
    req = urllib.request.Request(BASE + "/chat/completions", data=json.dumps(payload).encode(),
                                headers={"Authorization": "Bearer " + KEY,
                                         "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    try:
        msg = d["choices"][0]["message"]
        return (msg.get("content") or ""), d["choices"][0].get("finish_reason")
    except Exception:
        return "", ""


card = open(CARD, encoding="utf-8").read()
for m in CHAIN:
    try:
        txt, fr = call(m, card)
        if txt and txt.strip():
            open(OUT, "w", encoding="utf-8").write(txt)
            open(OUT.replace(".md", ".json"), "w", encoding="utf-8").write(json.dumps(
                {"seat": "science_mil", "provider": "yi-hydrogel", "model": m,
                 "ok": True, "error": "", "finish_reason": fr}, indent=1))
            print(f"FINAL OK {m} len={len(txt)} finish={fr} first={txt.strip().splitlines()[0][:48]}")
            break
        print(f"EMPTY {m} finish={fr}")
    except Exception as e:
        print(f"FAIL {m} :: {type(e).__name__} {str(e)[:150]}")
