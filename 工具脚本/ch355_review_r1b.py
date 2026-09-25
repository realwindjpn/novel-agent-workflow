import sys, json, os, urllib.request, concurrent.futures as cf

sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

CARD_DIR = "/root/workspace/科武纪元/任务运行态/20260923_kewu_selfcycle_daily/output"
OUT = "/root/workspace/科武纪元/审核记录/ch355_review_r1"
PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]


def call(prov, model, content, maxtok=4000, timeout=560):
    cfg = PR[prov]
    base = (cfg.get("base_url") or "").rstrip("/")
    key = C.get_env_value_prefer_dotenv(cfg.get("key_env"))
    mode = cfg.get("api_mode", "chat_completions")
    url = f"{base}/responses" if mode == "codex_responses" else f"{base}/chat/completions"
    payload = {"model": model, "stream": False,
               "messages": [{"role": "user", "content": content}],
               "max_tokens": maxtok, "temperature": 0.2}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "originator": "codex_exec"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    try:
        return d["choices"][0]["message"]["content"]
    except Exception:
        try:
            return d["output"][0]["content"][0]["text"]
        except Exception:
            return ""


def run_seat(seat, prov, model):
    card = open(f"{CARD_DIR}/review_355_{seat}.md", encoding="utf-8").read()
    try:
        txt = call(prov, model, card)
    except Exception as e:
        return {"seat": seat, "provider": prov, "model": model, "ok": False,
                "error": f"{type(e).__name__}: {str(e)[:250]}", "text": ""}
    return {"seat": seat, "provider": prov, "model": model,
            "ok": bool(txt and txt.strip()), "error": "", "text": txt or ""}


# 1) smoke grok-4.7
try:
    sm = call("yi-hydrogel", "grok-4.7", "只回复一行：9乘17等于多少，然后写OK", 60, 60)
    print(f"SMOKE yi-hydrogel/grok-4.7 :: {str(sm)[:80]!r}")
    grok_ok = bool(sm and sm.strip())
except Exception as e:
    print(f"SMOKE yi-hydrogel/grok-4.7 FAIL :: {type(e).__name__} {str(e)[:150]}")
    grok_ok = False

SEATS = []
if grok_ok:
    SEATS.append(("science_mil", "yi-hydrogel", "grok-4.7"))
SEATS.append(("reader", "agentrouter-dsv4", "deepseek-v4-flash"))
SEATS.append(("deai", "agnes-text", "agnes-3.0-flash"))

os.makedirs(OUT, exist_ok=True)
with cf.ThreadPoolExecutor(max_workers=3) as ex:
    for r in ex.map(lambda a: run_seat(*a), SEATS):
        open(f"{OUT}/{r['seat']}.md", "w", encoding="utf-8").write(r["text"])
        open(f"{OUT}/{r['seat']}.json", "w", encoding="utf-8").write(
            json.dumps({k: v for k, v in r.items() if k != "text"}, ensure_ascii=False, indent=1))
        head = (r["text"] or "").strip().split("\n")[0][:48]
        print(f"{r['seat']:12s} {r['provider']}/{r['model']:24s} ok={r['ok']} len={len(r['text'])} first={head} {r['error']}")
