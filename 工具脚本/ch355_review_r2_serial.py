import sys, json, os, time, urllib.request

sys.path.insert(0, "/root/.hermes/hermes-agent")
from hermes_cli import config as C
import yaml

CARD_DIR = "/root/workspace/科武纪元/任务运行态/20260923_kewu_selfcycle_daily/output"
CHAPTER = "/root/workspace/科武纪元/新版/第355章.md"
OUT = "/root/workspace/科武纪元/审核记录/ch355_review_r2"
PR = yaml.safe_load(open("/root/.hermes/config.yaml"))["providers"]

BODY = open(CHAPTER, encoding="utf-8").read()


def _https(prov, model, content, maxtok=8000, timeout=560):
    cfg = PR[prov]
    base = (cfg.get("base_url") or "").rstrip("/")
    key = C.get_env_value_prefer_dotenv(cfg.get("key_env"))
    url = f"{base}/responses" if cfg.get("api_mode") == "codex_responses" else f"{base}/chat/completions"
    return _post(url, key, model, content, maxtok, timeout)


def _post(url, key, model, content, maxtok=8000, timeout=560):
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
        return d["choices"][0]["message"]["content"] or ""
    except Exception:
        try:
            return d["output"][0]["content"][0]["text"] or ""
        except Exception:
            return ""


def retry(label, fn, tries=3, wait=25):
    """串行 + 指数退避；524/503 是同出口代理过忙，并发会打爆。"""
    last = ""
    for i in range(tries):
        try:
            txt = fn()
            if txt and txt.strip():
                return txt, None
            last = "empty content"
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:160]}"
        print(f"  {label} try{i+1}/{tries} FAIL :: {last}", flush=True)
        if i < tries - 1:
            time.sleep(wait * (i + 1))
    return "", last


os.makedirs(OUT, exist_ok=True)
results = {}

# ---- 1. editor: bmapi/gpt-5.6-sol
card = open(f"{CARD_DIR}/review_355_editor.md", encoding="utf-8").read()
p = card + "\n\n" + "=" * 20 + "\n待审正文（第355章 重写版）：\n" + "=" * 20 + "\n\n" + BODY
t, e = retry("editor", lambda: _https("bmapi", "gpt-5.6-sol", p))
results["editor"] = {"seat": "editor", "provider": "bmapi", "model": "gpt-5.6-sol",
                     "ok": bool(t), "error": e or "", "text": t}
print(f"editor ok={bool(t)} len={len(t)}", flush=True)
time.sleep(8)

# ---- 2. structure: sensenova/glm-5.2（思考模型须 maxtok>=8000）
card = open(f"{CARD_DIR}/review_355_structure.md", encoding="utf-8").read()
p = card + "\n\n" + "=" * 20 + "\n待审正文（第355章 重写版）：\n" + "=" * 20 + "\n\n" + BODY
t, e = retry("structure", lambda: _https("sensenova", "glm-5.2", p))
results["structure"] = {"seat": "structure", "provider": "sensenova", "model": "glm-5.2",
                        "ok": bool(t), "error": e or "", "text": t}
print(f"structure ok={bool(t)} len={len(t)}", flush=True)
time.sleep(8)

# ---- 3. reader: agentrouter-dsv4/deepseek-v4-flash
card = open(f"{CARD_DIR}/review_355_reader.md", encoding="utf-8").read()
p = card + "\n\n" + "=" * 20 + "\n待审正文（第355章 重写版）：\n" + "=" * 20 + "\n\n" + BODY
t, e = retry("reader", lambda: _https("agentrouter-dsv4", "deepseek-v4-flash", p))
results["reader"] = {"seat": "reader", "provider": "agentrouter-dsv4", "model": "deepseek-v4-flash",
                     "ok": bool(t), "error": e or "", "text": t}
print(f"reader ok={bool(t)} len={len(t)}", flush=True)
time.sleep(8)

# ---- 4. science_mil: yi-hydrogel 同节点链（用户 HARD 要求不许退到别家）
card = open(f"{CARD_DIR}/review_355_science_mil.md", encoding="utf-8").read()
p = card + "\n\n" + "=" * 20 + "\n待审正文（第355章 重写版）：\n" + "=" * 20 + "\n\n" + BODY
key = C.get_env_value_prefer_dotenv("YI_HYDROGEL_API_KEY")
base = "https://api-yi-hydrogel.seeseed1ck.icu/v1/chat/completions"
sci_txt, sci_model, sci_err = "", "none", "not attempted"
for m in ["grok-4.7", "grok-4.6", "qwen3.7-plus", "mimo-v2.6-flash"]:
    t, e = retry(f"science/{m}", lambda mm=m: _post(base, key, mm, p), tries=2, wait=20)
    if t:
        sci_txt, sci_model, sci_err = t, m, ""
        break
    sci_err = e
results["science_mil"] = {"seat": "science_mil", "provider": "yi-hydrogel", "model": sci_model,
                          "ok": bool(sci_txt), "error": sci_err or "", "text": sci_txt}
print(f"science_mil ok={bool(sci_txt)} model={sci_model} len={len(sci_txt)}", flush=True)
time.sleep(8)

# ---- 5. deai: qoder/Qwen3.8-Flash 本地 7864
card = open(f"{CARD_DIR}/review_355_deai.md", encoding="utf-8").read()
p = card + "\n\n" + "=" * 20 + "\n待审正文（第355章 重写版）：\n" + "=" * 20 + "\n\n" + BODY
qkey = C.get_env_value_prefer_dotenv("QODER_API_KEY")
t, e = retry("deai", lambda: _post("http://127.0.0.1:7864/v1/chat/completions", qkey, "Qwen3.8-Flash", p))
results["deai"] = {"seat": "deai", "provider": "qoder", "model": "Qwen3.8-Flash",
                   "ok": bool(t), "error": e or "", "text": t}
print(f"deai ok={bool(t)} len={len(t)}", flush=True)

print("\n===== SUMMARY =====")
for k, v in results.items():
    open(f"{OUT}/{v['seat']}.md", "w", encoding="utf-8").write(v["text"])
    open(f"{OUT}/{v['seat']}.json", "w", encoding="utf-8").write(
        json.dumps({kk: vv for kk, vv in v.items() if kk != "text"}, ensure_ascii=False, indent=1))
    head = (v["text"] or "").strip().split("\n")[0][:50]
    print(f"{v['seat']:12s} {v['provider']}/{v['model']:22s} ok={v['ok']} len={len(v['text'])} first={head} {v['error']}")
