#!/usr/bin/env python3
"""G2 会诊席位当轮 smoke（skill：起跑前每席当轮 smoke，静态名单一律不信）。"""
import json, sys, urllib.request, concurrent.futures as cf
sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]
PROBE = "只回复一行：9乘17等于多少？然后写OK"

CANDIDATES = [
    ("rsiai", "claude-opus-5"),
    ("workbuddy-hy3", "cn:glm-5.3-flash"),
    ("agentrouter-dsv4", "deepseek-v4-flash"),
    ("chun-grok46", "grok-4.6"),
    ("tokeasy", "deepseek-v4-flash"),
    ("bmapi", "gpt-5.6-sol"),
    ("sensenova", "glm-5.2"),
    ("sensenova2", "glm-5.2"),
    ("yezi-gemini", "gemini-3.8-flash"),
    ("yi-hydrogel", "grok-4.7"),
]


def call(prov, model, timeout=45):
    cfg = PR[prov]
    base = (cfg.get("base_url") or "").rstrip("/")
    key = C.get_env_value_prefer_dotenv(cfg.get("key_env"))
    if not key:
        return {"provider": prov, "model": model, "ok": False, "err": "no_key", "reply": ""}
    url = f"{base}/responses" if cfg.get("api_mode") == "codex_responses" else f"{base}/chat/completions"
    payload = {"model": model, "stream": False,
               "messages": [{"role": "user", "content": PROBE}],
               "max_tokens": 60, "temperature": 0.1}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Authorization": "Bearer " + key,
                                          "Content-Type": "application/json",
                                          "originator": "codex_exec"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    try:
        txt = d["choices"][0]["message"]["content"] or ""
    except Exception:
        try:
            txt = d["output"][0]["content"][0]["text"] or ""
        except Exception:
            txt = ""
    return {"provider": prov, "model": model, "ok": bool(txt.strip()),
            "reply": txt.strip()[:40], "err": ""}


with cf.ThreadPoolExecutor(max_workers=4) as ex:
    futs = [ex.submit(call, p, m) for p, m in CANDIDATES]
    for f in cf.as_completed(futs):
        try:
            r = f.result()
        except Exception as e:
            r = {"provider": "?", "model": "?", "ok": False,
                 "err": f"{type(e).__name__}: {str(e)[:70]}", "reply": ""}
        print(f"{'PASS' if r['ok'] else 'FAIL'}  {r['provider']:20s} {r['model']:26s} "
              f"{r.get('reply','')[:32]} {r.get('err','')}")
