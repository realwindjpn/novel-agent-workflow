import sys, json, os, urllib.request, concurrent.futures as cf

sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

SEATS = [
    ("editor",      "bmapi",       "gpt-5.6-sol"),
    ("structure",   "siliconflow", "deepseek-ai/DeepSeek-V3"),
    ("science_mil", "tingfeng",    "deepseek-v4-flash"),
    ("reader",      "rsiai",       "claude-opus-5"),
    ("deai",        "sensenova",   "glm-5.2"),
]

CARD_DIR = "/root/workspace/科武纪元/任务运行态/20260923_kewu_selfcycle_daily/output"
OUT = "/root/workspace/科武纪元/审核记录/ch355_review_r1"

PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]


def call(seat, prov, model):
    card = open(f"{CARD_DIR}/review_355_{seat}.md", encoding="utf-8").read()
    cfg = PR[prov]
    base = (cfg.get("base_url") or "").rstrip("/")
    key = C.get_env_value_prefer_dotenv(cfg.get("key_env"))
    mode = cfg.get("api_mode", "chat_completions")
    url = f"{base}/responses" if mode == "codex_responses" else f"{base}/chat/completions"
    payload = {"model": model, "stream": False,
               "messages": [{"role": "user", "content": card}],
               "max_tokens": 4000, "temperature": 0.2}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "originator": "codex_exec"})
    try:
        with urllib.request.urlopen(req, timeout=560) as r:
            d = json.loads(r.read().decode())
    except Exception as e:
        return {"seat": seat, "provider": prov, "model": model, "ok": False,
                "error": f"{type(e).__name__}: {str(e)[:250]}", "text": ""}
    txt = ""
    try:
        txt = d["choices"][0]["message"]["content"]
    except Exception:
        try:
            txt = d["output"][0]["content"][0]["text"]
        except Exception:
            txt = json.dumps(d)[:500]
    return {"seat": seat, "provider": prov, "model": model,
            "ok": bool(txt and txt.strip()), "error": "", "text": txt or ""}


def main():
    os.makedirs(OUT, exist_ok=True)
    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        for r in ex.map(lambda a: call(*a), SEATS):
            open(f"{OUT}/{r['seat']}.md", "w", encoding="utf-8").write(r["text"])
            open(f"{OUT}/{r['seat']}.json", "w", encoding="utf-8").write(
                json.dumps({k: v for k, v in r.items() if k != "text"}, ensure_ascii=False, indent=1))
            head = (r["text"] or "").strip().split("\n")[0][:48]
            print(f"{r['seat']:12s} {r['provider']}/{r['model']:26s} ok={r['ok']} len={len(r['text'])} first={head} {r['error']}")


main()
