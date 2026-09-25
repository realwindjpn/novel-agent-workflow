import sys, json, urllib.request, concurrent.futures as cf

sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]


def call(prov, model, content, maxtok=60, timeout=60):
    cfg = PR[prov]
    base = (cfg.get("base_url") or "").rstrip("/")
    key = C.get_env_value_prefer_dotenv(cfg.get("key_env"))
    mode = cfg.get("api_mode", "chat_completions")
    url = f"{base}/responses" if mode == "codex_responses" else f"{base}/chat/completions"
    payload = {"model": model, "stream": False,
               "messages": [{"role": "user", "content": content}], "max_tokens": maxtok}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json", "originator": "codex_exec"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    try:
        return d["choices"][0]["message"]["content"]
    except Exception:
        try:
            return d["output"][0]["content"][0]["text"]
        except Exception:
            return ""


CANDS = [
    ("chun-grok46", "grok-4.6"),
    ("futureppo", "grok-4.6"),
    ("grok2api-seeseed1ck", "grok-4.6"),
    ("openfly-grok46", "grok-4.6"),
    ("ai168661-grok", "grok-chat-fast"),
    ("tokenrhythm", "mimo-v2.6-flash"),
    ("yi-hydrogel", "grok-4.6"),
    ("yi-hydrogel", "grok-4.7"),
]


def run(t):
    prov, mod = t
    try:
        r = call(prov, mod, "只回复一行：9乘17等于多少，然后写OK")
        return f"OK   {prov}/{mod} :: {str(r)[:60]!r}"
    except Exception as e:
        return f"FAIL {prov}/{mod} :: {type(e).__name__} {str(e)[:100]}"


with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for r in ex.map(run, CANDS):
        print(r)
