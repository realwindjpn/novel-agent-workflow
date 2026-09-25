import sys, json, os, urllib.request, concurrent.futures as cf

sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

CARD_DIR = "/root/workspace/科武纪元/任务运行态/20260923_kewu_selfcycle_daily/output"
# 新版正文已重写（v10, SHA 81ef715d, CJK 3003），审稿卡须读新正文
CHAPTER = "/root/workspace/科武纪元/新版/第355章.md"
OUT = "/root/workspace/科武纪元/审核记录/ch355_review_r2"
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


def call_raw(base_url, key_env, model, content, maxtok=8000, timeout=560):
    """yi-hydrogel 同节点直连（用户指定：fallback 不许退到别家节点）"""
    key = C.get_env_value_prefer_dotenv(key_env)
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {"model": model, "stream": False,
               "messages": [{"role": "user", "content": content}],
               "max_tokens": maxtok, "temperature": 0.2}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    try:
        return d["choices"][0]["message"]["content"] or ""
    except Exception:
        return ""


def run_seat(seat, prov, model):
    card = open(f"{CARD_DIR}/review_355_{seat}.md", encoding="utf-8").read()
    body = open(CHAPTER, encoding="utf-8").read()
    prompt = card + "\n\n" + "=" * 20 + "\n以下是本次待审正文（第355章，重写版）：\n" + "=" * 20 + "\n\n" + body
    try:
        txt = call(prov, model, prompt)
    except Exception as e:
        return {"seat": seat, "provider": prov, "model": model, "ok": False,
                "error": f"{type(e).__name__}: {str(e)[:250]}", "text": ""}
    return {"seat": seat, "provider": prov, "model": model,
            "ok": bool(txt and txt.strip()), "error": "", "text": txt or ""}


def run_deai_qoder():
    seat = "deai"
    card = open(f"{CARD_DIR}/review_355_{seat}.md", encoding="utf-8").read()
    body = open(CHAPTER, encoding="utf-8").read()
    prompt = card + "\n\n" + "=" * 20 + "\n以下是本次待审正文（第355章，重写版）：\n" + "=" * 20 + "\n\n" + body
    try:
        txt = call_raw("http://127.0.0.1:7864/v1", "QODER_API_KEY", "Qwen3.8-Flash", prompt)
    except Exception as e:
        return {"seat": seat, "provider": "qoder", "model": "Qwen3.8-Flash", "ok": False,
                "error": f"{type(e).__name__}: {str(e)[:250]}", "text": ""}
    return {"seat": seat, "provider": "qoder", "model": "Qwen3.8-Flash",
            "ok": bool(txt and txt.strip()), "error": "", "text": txt or ""}


def run_science_yh():
    """科学军事席：锁死 yi-hydrogel 同节点内链（用户 HARD 要求）"""
    seat = "science_mil"
    card = open(f"{CARD_DIR}/review_355_{seat}.md", encoding="utf-8").read()
    body = open(CHAPTER, encoding="utf-8").read()
    prompt = card + "\n\n" + "=" * 20 + "\n以下是本次待审正文（第355章，重写版）：\n" + "=" * 20 + "\n\n" + body
    base = "https://api-yi-hydrogel.seeseed1ck.icu/v1"
    for m in ["grok-4.7", "qwen3.7-plus", "mimo-v2.6-flash", "grok-4.6"]:
        try:
            txt = call_raw(base, "YI_HYDROGEL_API_KEY", m, prompt)
            if txt and txt.strip():
                print(f"science_mil 命中 {m}")
                return {"seat": seat, "provider": "yi-hydrogel", "model": m,
                        "ok": True, "error": "", "text": txt}
            print(f"science_mil {m} 空回")
        except Exception as e:
            print(f"science_mil {m} FAIL :: {type(e).__name__} {str(e)[:120]}")
    return {"seat": seat, "provider": "yi-hydrogel", "model": "none", "ok": False,
            "error": "all yi-hydrogel models failed", "text": ""}


os.makedirs(OUT, exist_ok=True)

# 五席（跨 provider 跨族，按用户指定路由）
# editor=bmapi/gpt-5.6-sol
# structure=sensenova/glm-5.2（思考模型，maxtok 须 >=8000 否则 content 空）
# science_mil=yi-hydrogel 同节点链
# reader=agentrouter-dsv4/deepseek-v4-flash
# deai=qoder/Qwen3.8-Flash（本地 7864）
JOBS = [
    ("editor", lambda: run_seat("editor", "bmapi", "gpt-5.6-sol")),
    ("structure", lambda: run_seat("structure", "sensenova", "glm-5.2")),
    ("reader", lambda: run_seat("reader", "agentrouter-dsv4", "deepseek-v4-flash")),
    ("science_mil", run_science_yh),
    ("deai", run_deai_qoder),
]

with cf.ThreadPoolExecutor(max_workers=5) as ex:
    futs = {ex.submit(fn): name for name, fn in JOBS}
    for fut in cf.as_completed(futs):
        name = futs[fut]
        try:
            r = fut.result()
        except Exception as e:
            r = {"seat": name, "provider": "?", "model": "?", "ok": False,
                 "error": f"{type(e).__name__}: {str(e)[:200]}", "text": ""}
        open(f"{OUT}/{r['seat']}.md", "w", encoding="utf-8").write(r["text"])
        open(f"{OUT}/{r['seat']}.json", "w", encoding="utf-8").write(
            json.dumps({k: v for k, v in r.items() if k != "text"}, ensure_ascii=False, indent=1))
        head = (r["text"] or "").strip().split("\n")[0][:48]
        print(f"{r['seat']:12s} {r['provider']}/{r['model']:24s} ok={r['ok']} len={len(r['text'])} first={head} {r['error']}", flush=True)
