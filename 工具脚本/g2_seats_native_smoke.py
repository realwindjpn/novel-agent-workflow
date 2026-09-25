#!/usr/bin/env python3
"""G2 会诊席位当轮语义 smoke（走 hermes 原生 dispatch_to_model）。

skill 铁律：判节点死活走原生 smoke，不用裸 urllib 脚本（会被 WAF 按 UA 拦，
403/1010 是浏览器指纹拦截，不是 key 失效、不是节点退役）。
"""
import sys
sys.path.insert(0, "/root/.hermes/hermes-agent")

PROBE = ("只回复一行：9乘17等于多少？然后写OK。"
         "不要解释，不要写代码，第一行就是答案。")

CANDIDATES = [
    ("rsiai", "claude-opus-5", "主席/结构"),
    ("workbuddy-hy3", "cn:glm-5.3-flash", "编辑/连续性"),
    ("agentrouter-dsv4", "deepseek-v4-flash", "科学顾问"),
    ("chun-grok46", "grok-4.6", "军事制度"),
    ("tokeasy", "deepseek-v4-flash", "海外新鲜度"),
    ("bmapi", "gpt-5.6-sol", "备用A"),
    ("sensenova", "glm-5.2", "备用B"),
    ("yezi-gemini", "gemini-3.8-flash", "备用C"),
    ("yi-hydrogel", "grok-4.7", "备用D"),
]

results = []
for prov, model, seat in CANDIDATES:
    try:
        from hermes_multimodel import dispatch_to_model
    except Exception:
        pass
    print(f"### {seat} | {prov}/{model}")
    print(f"PROBE: {PROBE}")
    print("---")
