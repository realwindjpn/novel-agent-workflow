import os, re, json

base = "/root/workspace/科武纪元/新版"
raw_path = "/root/workspace/科武纪元/审核记录/editor_331_334_raw.md"
chapters = [331, 332, 333, 334]

# load candidate lines per chapter
lines_by_ch = {}
for n in chapters:
    txt = open(os.path.join(base, f"第{n}章.md"), encoding="utf-8").read()
    lines_by_ch[n] = txt.splitlines()

raw = open(raw_path, encoding="utf-8").read()

# shell check
first_line = raw.splitlines()[0].strip() if raw.strip() else ""
print("SHELL first_line:", repr(first_line), "OK" if first_line in ("VERDICT: PASS", "VERDICT: FAIL") else "BAD")

# extract EVIDENCE json objects
ev_re = re.compile(r'EVIDENCE:\s*(\{.*?\})')
results = []
for m in ev_re.finditer(raw):
    try:
        obj = json.loads(m.group(1))
    except Exception as e:
        results.append(("JSON_PARSE_FAIL", m.group(1)[:60]))
        continue
    ch = obj.get("chapter")
    quote = obj.get("quote", "")
    line = obj.get("line")
    lines = lines_by_ch.get(ch, [])
    total = len(lines)
    # normalize quote: strip possible N| prefix
    q_norm = re.sub(r'^\s*\d+\|', '', quote)
    # substring hit anywhere in chapter
    full = "\n".join(lines)
    hit_anywhere = (quote in full) or (q_norm in full)
    # line in range and matches
    line_ok = isinstance(line, int) and 1 <= line <= total
    line_content = lines[line-1] if line_ok else ""
    line_match = line_ok and (quote in line_content or q_norm in line_content or q_norm.strip() in line_content)
    verdict = "HIT" if hit_anywhere else "QUOTE_MISS"
    results.append((ch, line, "range_ok" if line_ok else f"LINE_OOR(total={total})",
                    "line_match" if line_match else "line_mismatch", verdict, q_norm[:40]))

miss = [r for r in results if len(r) >= 5 and r[4] == "QUOTE_MISS"]
oor = [r for r in results if len(r) >= 3 and isinstance(r[2], str) and r[2].startswith("LINE_OOR")]
print(f"\nTotal EVIDENCE: {len(results)}  QUOTE_MISS: {len(miss)}  LINE_OOR: {len(oor)}")
for r in results:
    print(r)
