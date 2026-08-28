#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""292 R3 六审席位路由烟测（短 prompt，仅验证 provider/model 可达非空）。"""
import subprocess, concurrent.futures, time, json, sys

SEATS = [
    ("editor",               "sotamodel",        "claude-opus-5"),
    ("reader",               "nous",             "longcat-2.0"),
    ("science",              "tokenrhythm-dsv4", "deepseek-v4-flash-0731"),
    ("military_institution", "chun-grok46",      "grok-4.6"),
    ("structure",            "any",              "claude-fable-5"),
    ("deai_final",           "agentrouter",      "gpt-5.6-sol"),
]

Q = "只回复两个字：可用"

def run(seat, provider, model):
    t0 = time.time()
    cmd = ["hermes", "chat", "-Q", "--provider", provider, "-m", model,
           "--ignore-rules", "-t", "", "-q", Q]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd="/root")
        out = (p.stdout or "").strip()
        err = (p.returncode, (p.stderr or "").strip()[-300:])
        return dict(seat=seat, provider=provider, model=model, rc=p.returncode,
                    elapsed=round(time.time()-t0,1), out=out[-400:], err=err[1])
    except subprocess.TimeoutExpired:
        return dict(seat=seat, provider=provider, model=model, rc="TIMEOUT",
                    elapsed=round(time.time()-t0,1), out="", err="timeout120")

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(run, *s) for s in SEATS]
    res = [f.result() for f in concurrent.futures.as_completed(futs)]

res.sort(key=lambda r: [s[0] for s in SEATS].index(r["seat"]))
for r in res:
    print(json.dumps(r, ensure_ascii=False))
