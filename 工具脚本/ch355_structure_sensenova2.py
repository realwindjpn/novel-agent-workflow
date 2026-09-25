import sys, json, urllib.request

sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]
BASE = "https://token.sensenova.cn/v1"
CARD = "/root/workspace/科武纪元/任务运行态/20260923_kewu_selfcycle_daily/output/review_355_structure.md"
OUT = "/root/workspace/科武纪元/审核记录/ch355_review_r1/structure.md"


def call(prov, model, content, maxtok=8000, timeout=560):
    key = C.get_env_value_prefer_dotenv(PR[prov].get("key_env"))
    payload = {"model": model, "stream": False,
               "messages": [{"role": "user", "content": content}], "max_tokens": maxtok}
    req = urllib.request.Request(BASE + "/chat/completions", data=json.dumps(payload).encode(),
                                headers={"Authorization": "Bearer " + key,
                                         "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    try:
        ch = d["choices"][0]["message"]
        txt = ch.get("content") or ""
        return txt, ch.get("reasoning_content", "")[:80], d.get("choices", [{}])[0].get("finish_reason")
    except Exception:
        return "", "", ""


card = open(CARD, encoding="utf-8").read()
for prov in ["sensenova", "sensenova2"]:
    try:
        txt, rsn, fr = call(prov, "glm-5.2", card)
        if txt and txt.strip():
            open(OUT, "w", encoding="utf-8").write(txt)
            open(OUT.replace(".md", ".json"), "w", encoding="utf-8").write(json.dumps(
                {"seat": "structure", "provider": prov, "model": "glm-5.2", "ok": True,
                 "error": "", "finish_reason": fr}, indent=1))
            print(f"FINAL OK {prov} len={len(txt)} finish={fr} first={txt.strip().splitlines()[0][:48]}")
            break
        print(f"EMPTY {prov} finish={fr} reasoning={rsn!r}")
    except Exception as e:
        print(f"FAIL {prov} :: {type(e).__name__} {str(e)[:150]}")
