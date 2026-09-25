import sys, json, urllib.request

sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]
BASE = "https://token.sensenova.cn/v1"
probe = {p: None for p in ["sensenova", "sensenova2"]}


def raw_call(prov, model, content, maxtok=200, timeout=90):
    key = C.get_env_value_prefer_dotenv(PR[prov].get("key_env"))
    payload = {"model": model, "stream": False,
               "messages": [{"role": "user", "content": content}], "max_tokens": maxtok}
    req = urllib.request.Request(BASE + "/chat/completions", data=json.dumps(payload).encode(),
                                headers={"Authorization": "Bearer " + key,
                                         "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode()


for prov in ["sensenova", "sensenova2"]:
    try:
        raw = raw_call(prov, "glm-5.2", "只回复一行：9乘17等于多少，然后写OK")
        print(f"--- {prov} raw ---")
        print(raw[:900])
    except Exception as e:
        print(f"{prov} FAIL {type(e).__name__} {str(e)[:150]}")
