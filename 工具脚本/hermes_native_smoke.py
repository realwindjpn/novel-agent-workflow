import subprocess, concurrent.futures as cf

PROMPT = "只回复一行：9乘17等于多少，然后写OK"

TESTS = [
    ("sensenova/glm-5.2", ["sensenova", "glm-5.2"]),
    ("yi-hydrogel/grok-4.7", ["yi-hydrogel", "grok-4.7"]),
    ("yi-hydrogel/qwen3.7-plus", ["yi-hydrogel", "qwen3.7-plus"]),
    ("yi-hydrogel/mimo-v2.6-flash", ["yi-hydrogel", "mimo-v2.6-flash"]),
    ("yi-hydrogel/grok-4.6", ["yi-hydrogel", "grok-4.6"]),
    ("qoder/Qwen3.8-Flash", ["qoder", "Qwen3.8-Flash"]),
]


def run(t):
    label, args = t
    cmd = ["timeout", "180", "hermes", "chat", "--provider", f"custom:{args[0]}",
           "-m", args[1], "-Q", "-q", PROMPT]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=200)
        out = (r.stdout or "") + (r.stderr or "")
        return f"=== {label} ===\n{out.strip()[:400]}\n"
    except Exception as e:
        return f"=== {label} ===\nERR {type(e).__name__} {str(e)[:150]}\n"


with cf.ThreadPoolExecutor(max_workers=6) as ex:
    for r in ex.map(run, TESTS):
        print(r)
