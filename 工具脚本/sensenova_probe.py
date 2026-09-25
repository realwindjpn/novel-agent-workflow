import sys, json, urllib.request, concurrent.futures as cf

sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]
BASE = "https://token.sensenova.cn/v1"
CARD = "/root/workspace/科武纪元/任务运行态/20260923_kewu_selfcycle_daily/output/review_355_structure.md"
OUT = "/root/workspace/科武纪元/审核记录/ch355_review_r1/structure.md"

PROVS = ["sensenova", "sensenova2"]


def call(prov, model, content, maxtok=60, timeout=90):
    cfg = PR[prov]
    key = C.get_env_value_prefer_dotenv(cfg.get("key_env"))
    payload = {"model": model, "stream": False,
               "messages": [{"role": "user", "content": content}], "max_tokens": maxtok}
    req = urllib.request.Request(BASE + "/chat/completions", data=json.dumps(payload).encode(),
                                headers={"Authorization": "Bearer " + key,
                                         "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode()
    d = json.loads(raw)
    try:
        return d["choices"][0]["message"]["content"], d
    except Exception:
        return "", d


def probe(args):
    prov, model = args
    try:
        txt, d = call(prov, model, "只回复一行：9乘17等于多少，然后写OK")
        return f"OK   {prov}/{model} :: {str(txt)[:60]!r}"
    except Exception as e:
        return f"FAIL {prov}/{model} :: {type(e).__name__} {str(e)[:120]}"


CANDS = [(p, m) for p in PROVS for m in ["glm-5.2", "sensenova-6.7-flash-lite"]]
with cf.ThreadPoolExecutor(max_workers=4) as ex:
    for r in ex.map(probe, CANDS):
        print(r)
