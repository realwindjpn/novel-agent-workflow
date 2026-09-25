import sys, json, urllib.request

sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]
BASE = "https://api-yi-hydrogel.seeseed1ck.icu/v1"
KEY = C.get_env_value_prefer_dotenv("YI_HYDROGEL_API_KEY")
OUT = "/root/workspace/科武纪元/审核记录/ch355_review_r1/science_mil.md"

# STAGE 1: 同节点 /v1/models 拿真实 ID + 短探针
def models():
    req = urllib.request.Request(BASE + "/models", headers={"Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())
    return [m.get("id") or m.get("name") for m in (d.get("data") or [])]

try:
    ids = models()
    print("MODELS:", ids)
except Exception as e:
    ids = []
    print("MODELS_FAIL", type(e).__name__, str(e)[:150])

cands = []
for want in ["mimo-v2.6-flash", "grok-4.6", "grok-4.7"]:
    hit = [i for i in ids if i == want]
    cands += hit or ([want] if want in ("mimo-v2.6-flash", "grok-4.6", "grok-4.7") else [])
# 去重保序
seen = set()
CHAIN = []
for c in cands:
    if c not in seen:
        seen.add(c)
        CHAIN.append(c)
print("CHAIN:", CHAIN)

def call(model, content, maxtok=8000, timeout=560):
    payload = {"model": model, "stream": False,
               "messages": [{"role": "user", "content": content}], "max_tokens": maxtok}
    req = urllib.request.Request(BASE + "/chat/completions", data=json.dumps(payload).encode(),
                                headers={"Authorization": "Bearer " + KEY,
                                         "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    try:
        return d["choices"][0]["message"]["content"]
    except Exception:
        return ""

# STAGE 2: 短探针
alive = []
for m in CHAIN:
    try:
        r = call(m, "只回复一行：9乘17等于多少，然后写OK")
        if r and r.strip():
            alive.append(m)
            print(f"PROBE OK   {m} :: {str(r)[:50]!r}")
        else:
            print(f"PROBE EMPTY {m}")
    except Exception as e:
        print(f"PROBE FAIL {m} :: {type(e).__name__} {str(e)[:100]}")

# STAGE 3: 首个活模型投长卡
CARD = "/root/workspace/科武纪元/任务运行态/20260923_kewu_selfcycle_daily/output/review_355_science_mil.md"
card = open(CARD, encoding="utf-8").read()
for m in alive:
    try:
        txt = call(m, card, 3000, 560)
        if txt and txt.strip():
            open(OUT, "w", encoding="utf-8").write(txt)
            open(OUT.replace(".md", ".json"), "w", encoding="utf-8").write(json.dumps(
                {"seat": "science_mil", "provider": "yi-hydrogel", "model": m, "ok": True, "error": ""}, indent=1))
            print(f"FINAL OK {m} len={len(txt)} first={txt.strip().splitlines()[0][:48]}")
            break
        print(f"FINAL EMPTY {m}")
    except Exception as e:
        print(f"FINAL FAIL {m} :: {type(e).__name__} {str(e)[:150]}")
