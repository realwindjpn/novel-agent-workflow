import sys, json, urllib.request

sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]
OUT = "/root/workspace/科武纪元/审核记录/ch355_review_r1/structure.md"
CARD = "/root/workspace/科武纪元/任务运行态/20260923_kewu_selfcycle_daily/output/review_355_structure.md"

# 同 base_url，两把 key：sensenova 先，sensenova2 后
CHAIN = [("sensenova", "glm-5.2"), ("sensenova2", "glm-5.2")]


def call(prov, model, content, maxtok=60, timeout=60):
    cfg = PR[prov]
    base = (cfg.get("base_url") or "").rstrip("/")
    key = C.get_env_value_prefer_dotenv(cfg.get("key_env"))
    payload = {"model": model, "stream": False,
               "messages": [{"role": "user", "content": content}], "max_tokens": maxtok}
    req = urllib.request.Request(base + "/chat/completions", data=json.dumps(payload).encode(),
                                headers={"Authorization": "Bearer " + key,
                                         "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    try:
        return d["choices"][0]["message"]["content"]
    except Exception:
        return ""


card = open(CARD, encoding="utf-8").read()
for prov, model in CHAIN:
    try:
        probe = call(prov, model, "只回复一行：9乘17等于多少，然后写OK")
        print(f"PROBE {prov}/{model} :: {str(probe)[:60]!r}")
        if not (probe and probe.strip()):
            continue
        txt = call(prov, model, card, 3000, 560)
        if txt and txt.strip():
            open(OUT, "w", encoding="utf-8").write(txt)
            open(OUT.replace(".md", ".json"), "w", encoding="utf-8").write(json.dumps(
                {"seat": "structure", "provider": prov, "model": model, "ok": True, "error": ""}, indent=1))
            print(f"FINAL OK {prov}/{model} len={len(txt)} first={txt.strip().splitlines()[0][:48]}")
            break
        print(f"FINAL EMPTY {prov}/{model}")
    except Exception as e:
        print(f"FAIL {prov}/{model} :: {type(e).__name__} {str(e)[:150]}")
