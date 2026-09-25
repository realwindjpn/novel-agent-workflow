import sys, json, urllib.request

sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]
CARD = "/root/workspace/科武纪元/任务运行态/20260923_kewu_selfcycle_daily/output/review_355_science_mil.md"
OUT = "/root/workspace/科武纪元/审核记录/ch355_review_r1/science_mil.md"

CHAIN = [("chun-grok46", "grok-4.6"), ("yi-hydrogel", "grok-4.6"), ("yi-hydrogel", "grok-4.7")]


def call(prov, model, content, timeout=560):
    cfg = PR[prov]
    base = (cfg.get("base_url") or "").rstrip("/")
    key = C.get_env_value_prefer_dotenv(cfg.get("key_env"))
    mode = cfg.get("api_mode", "chat_completions")
    url = f"{base}/responses" if mode == "codex_responses" else f"{base}/chat/completions"
    payload = {"model": model, "stream": False,
               "messages": [{"role": "user", "content": content}],
               "max_tokens": 3000, "temperature": 0.2}
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


card = open(CARD, encoding="utf-8").read()
for prov, model in CHAIN:
    try:
        txt = call(prov, model, card)
        if txt and txt.strip():
            open(OUT, "w", encoding="utf-8").write(txt)
            meta = {"seat": "science_mil", "provider": prov, "model": model, "ok": True, "error": ""}
            open(OUT.replace(".md", ".json"), "w", encoding="utf-8").write(json.dumps(meta, indent=1))
            print(f"OK {prov}/{model} len={len(txt)} first={txt.strip().splitlines()[0][:48]}")
            break
        print(f"EMPTY {prov}/{model}")
    except Exception as e:
        print(f"FAIL {prov}/{model} :: {type(e).__name__} {str(e)[:150]}")
