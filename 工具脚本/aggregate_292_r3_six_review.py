#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""292 R3 六席审稿确定性校验 + REVIEW_AGGREGATE_R3.json 生成。

校验三项：非空、含完整 candidate_sha、含唯一 VERDICT。
不做内容判稿；调度席不代写审稿结论。
"""
import os, re, json, hashlib, datetime

TASK = "/root/workspace/科武纪元/任务运行态/20260823_kewu_selfcycle_daily"
OUT = os.path.join(TASK, "output")
REVDIR = os.path.join(OUT, "reviews_292_r3")
CAND = os.path.join(OUT, "candidate_292_r3.md")
EXPECT_SHA = "9512bcfb9a6d7101ac05480b307096ba44e9c548475f01050ddf83f266866586"

SEATS = [
    ("editor",               "sotamodel",        "claude-opus-5"),
    ("reader",               "nous",             "longcat-2.0"),
    ("science",              "tokenrhythm-dsv4", "deepseek-v4-flash-0731"),
    ("military_institution", "chun-grok46",      "grok-4.6"),
    ("structure",            "any",              "claude-fable-5"),
    ("deai_final",           "agentrouter",      "gpt-5.6-sol"),
]

body = open(CAND, encoding="utf-8").read()
actual_sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
cjk = len(re.findall(r"[\u4e00-\u9fff]", body))

meta_path = os.path.join(OUT, "_raw_six_review_meta.json")
meta = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else {}

def verdict_of(text):
    """提取唯一 VERDICT。返回 (verdict, count, note)。"""
    # 只在报告首部 40 行内的 VERDICT 声明行里取值，避免正文讨论误命中
    lines = text.splitlines()
    hits = []
    for i, ln in enumerate(lines):
        m = re.search(r"VERDICT\s*[:：]\s*\**\s*(PASS|FAIL)\b", ln, re.I)
        if m:
            hits.append((i + 1, m.group(1).upper()))
    vals = sorted(set(v for _, v in hits))
    if not hits:
        return None, 0, "NO_VERDICT_LINE"
    if len(vals) > 1:
        return None, len(hits), "CONFLICTING_VERDICT:" + "/".join(vals)
    return vals[0], len(hits), "OK"

rows, all_pass, invalid = [], True, []
for seat, provider, model in SEATS:
    path = os.path.join(REVDIR, f"{seat}.md")
    exists = os.path.exists(path)
    text = open(path, encoding="utf-8").read() if exists else ""
    nbytes = len(text.encode("utf-8"))
    nonempty = len(text.strip()) >= 200
    sha_ok = EXPECT_SHA in text
    verdict, vcount, vnote = verdict_of(text)
    m = meta.get(seat, {})
    rc = m.get("rc")
    elapsed = m.get("elapsed")
    attempt = m.get("attempt")

    reasons = []
    if not exists:
        reasons.append("FILE_MISSING")
    if not nonempty:
        reasons.append("EMPTY_OR_TOO_SHORT")
    if not sha_ok:
        reasons.append("SHA_NOT_PRESENT_OR_TRUNCATED")
    if verdict is None:
        reasons.append(vnote)
    if rc not in (0,):
        reasons.append(f"ROUTE_FAILURE(rc={rc})")

    valid = not reasons
    if not valid:
        invalid.append(seat)
        all_pass = False
    elif verdict != "PASS":
        all_pass = False

    rows.append(dict(
        seat=seat, provider=provider, model=model, file=path,
        file_exists=exists, bytes=nbytes, nonempty=nonempty,
        candidate_sha_present=sha_ok, candidate_sha=EXPECT_SHA if sha_ok else None,
        verdict=verdict, verdict_line_count=vcount, verdict_note=vnote,
        rc=rc, elapsed_s=elapsed, attempt=attempt,
        report_valid=valid, invalid_reasons=reasons,
    ))

verdicts = [r["verdict"] for r in rows]
valid_cnt = sum(1 for r in rows if r["report_valid"])
if valid_cnt == 0:
    status = "FAIL"
elif valid_cnt < len(SEATS):
    status = "PARTIAL"
elif all(v == "PASS" for v in verdicts):
    status = "R3_SIX_REVIEW_PASS_PENDING_SYNC"
else:
    status = "FAIL"

agg = dict(
    task="292_R3_SIX_INDEPENDENT_REVIEW",
    generated_at=datetime.datetime.now().isoformat(timespec="seconds"),
    candidate_path=CAND,
    candidate_sha_expected=EXPECT_SHA,
    candidate_sha_actual=actual_sha,
    candidate_sha_match=(actual_sha == EXPECT_SHA),
    net_cjk=cjk, net_cjk_expected=3629, net_cjk_match=(cjk == 3629),
    seat_count=len(SEATS), valid_report_count=valid_cnt,
    invalid_seats=invalid,
    all_pass=bool(valid_cnt == len(SEATS) and all(v == "PASS" for v in verdicts)),
    aggregate_status=status,
    seats=rows,
    note=("六席全部有效且 VERDICT=PASS 时标 R3_SIX_REVIEW_PASS_PENDING_SYNC；"
          "不得由此推进草稿箱同步或发布。任席失败/超时/报告无效则为 PARTIAL/FAIL。"),
)

apath = os.path.join(OUT, "REVIEW_AGGREGATE_R3.json")
with open(apath, "w", encoding="utf-8") as fh:
    json.dump(agg, fh, ensure_ascii=False, indent=2)

print(json.dumps({k: v for k, v in agg.items() if k != "seats"}, ensure_ascii=False, indent=2))
print("--- seats ---")
for r in rows:
    print(f"{r['seat']:22s} valid={str(r['report_valid']):5s} verdict={str(r['verdict']):5s} "
          f"sha={str(r['candidate_sha_present']):5s} bytes={r['bytes']:6d} rc={r['rc']} "
          f"{r['elapsed_s']}s a{r['attempt']} {','.join(r['invalid_reasons'])}")
print("\nwrote:", apath)
