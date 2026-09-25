#!/usr/bin/env python3
"""派工前当轮 smoke（派工规则 #4：cron 派工须当轮 smoke，不凭记忆选节点）。"""
import json, sys, urllib.request, concurrent.futures as cf, os
sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]
PROBE = "只回复一行：9乘17等于多少？然后写OK"


def call(prov, model, timeout=45):
    cfg = PR[prov]
    base = (cfg.get("base_url") or "").rstrip("/")
    key = C.get_env_value_prefer_dotenv(cfg.get("key_env"))
    if not key:
        return {"provider": prov, "model": model, "ok": False, "err": "no_key"}
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
            "reply": txt.strip()[:60], "err": ""}



CANDIDATES=[
 ("qoder","Qwen3.8-Flash"),("qoder","Qwen3-Max"),("yi-hydrogel","glm-5.3-free"),
 ("yi-hydrogel","grok-4.7"),("sensenova2","glm-5.2"),("nim","deepseek-v4-flash"),
 ("openrouter","deepseek/deepseek-v4-flash"),("bmapi","gpt-5.6-sol"),
 ("axai-sol","gpt-5.6-sol"),("zzzcoding-codex","gpt-5.6"),("sharedchat-codex","gpt-5.5"),
 ("onefor","gpt-5.6"),("tokeasy","gpt-5.6"),("yuanown","gpt-5.6"),
]


with cf.ThreadPoolExecutor(max_workers=4) as ex:
    futs = [ex.submit(call, p, m) for p, m in CANDIDATES]
    for f in cf.as_completed(futs):
        try:
            r = f.result()
        except Exception as e:
            r = {"provider": "?", "model": "?", "ok": False, "err": f"{type(e).__name__}: {str(e)[:90]}", "reply": ""}
        flag = "PASS" if r["ok"] else "FAIL"
        print(f"{flag}  {r['provider']:20s} {r['model']:28s} {r.get('reply','')[:40]} {r.get('err','')}")
