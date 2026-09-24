import re, hashlib, os
base = "/root/workspace/科武纪元/新版"
for n in (331,332,333,334):
    f = os.path.join(base, f"第{n}章.md")
    raw = open(f, "rb").read()
    txt = raw.decode("utf-8")
    sha = hashlib.sha256(raw).hexdigest()
    cjk = len(re.findall(r"[\u4e00-\u9fff]", txt))
    lines = txt.splitlines()
    print(f"=== {n} ===")
    print("sha256:", sha)
    print("CJK:", cjk, "bytes:", len(raw), "lines:", len(lines))
    print("head:", lines[0] if lines else "")
    print("tail:", lines[-1] if lines else "")
