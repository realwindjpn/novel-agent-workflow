#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""292 R3 六席独立审稿并发派发器。

调度席专用：正文全文内联送审，六份 stdout 原样落盘，不代写内容。
"""
import subprocess, concurrent.futures, time, json, hashlib, os, re, sys

TASK = "/root/workspace/科武纪元/任务运行态/20260823_kewu_selfcycle_daily"
OUT = os.path.join(TASK, "output")
CAND = os.path.join(OUT, "candidate_292_r3.md")
REVDIR = os.path.join(OUT, "reviews_292_r3")
EXPECT_SHA = "9512bcfb9a6d7101ac05480b307096ba44e9c548475f01050ddf83f266866586"

os.makedirs(REVDIR, exist_ok=True)

body = open(CAND, encoding="utf-8").read()
sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
assert sha == EXPECT_SHA, f"SHA MISMATCH {sha}"
cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
assert cjk == 3629, f"CJK MISMATCH {cjk}"

SEATS = [
    ("editor",               "sotamodel",        "claude-opus-5"),
    ("reader",               "nous",             "longcat-2.0"),
    ("science",              "tokenrhythm-dsv4", "deepseek-v4-flash-0731"),
    ("military_institution", "chun-grok46",      "grok-4.6"),
    ("structure",            "any",              "claude-fable-5"),
    ("deai_final",           "agentrouter",      "gpt-5.6-sol"),
]

COMMON_HEAD = f"""你是《科武纪元》审稿席，本次只审第292章《能源瓶颈》R3 候选稿。

【报告首部必须逐字照写这三行，不得省略、不得改写】
candidate_sha: {EXPECT_SHA}
role: {{ROLE}}
VERDICT: PASS 或 FAIL（只写一个，二选一，禁止写 PASS_WITH_FIXES / 条件PASS / 部分PASS 等第三种值）

【硬规则】
1. 只审下方内联的正文全文。不得引用不在正文中的句子、章节、人物、数字。禁虚构。
2. 判 FAIL 必须给出：① 精确原句（从正文原样复制，不得改写）② 问题类型 ③ 最小修复建议（只改该句，不要求重写全章）。
3. 无法定位到精确原句的问题不得作为 FAIL 依据，只能列为「建议（不阻断）」。
4. 若全部检查项通过，VERDICT 写 PASS，并简述通过依据。
5. 报告用中文，控制在 1500 字以内。不要输出正文原文全文回显。

【本章事实基线（判断依据，不得据此虚构正文之外内容）】
- 大纲第292章：核心事件「戴森环生产能耗巨大，现有聚变电站无法满足需求」；硬约束「方宁提出在拉格朗日点建设太阳能阵列补充能源；能源技术节点成制约因素」。卷属第六卷·火星。
- 前章（291）已确立：月面工厂产线节拍锁死，退火两小时窗口只容第一班4件进炉，第二班错窗；日产4件、月产120件、首批良率78%；戴森环桁架节点段首件测试通过。
- 人物性别：林星辰男（他）、方宁男、韩铮男、赫斯特男、帕特尔男、沃罗诺夫男；陈若水女（她）。
- 净中文字符数实测 3629，硬下限 3200，无窄上限。字数达标，不得以字数为由判 FAIL。
"""

ROLE_TASK = {
"editor": """【你的角色：编辑席】
检查项：
1. 大纲对齐：标题、核心事件、硬约束是否落地。偏纲即 FAIL（标 SOURCE_MISMATCH）。
2. 章节功能是否完成：能源缺口如何暴露、聚变路线如何被证伪、L1 太阳能方案如何被提出并立项。
3. 结构三原则：每场景有「因为→所以」因果链；高潮后有余波；情绪目标明确。
4. 节奏与钩子：开篇悬念、中段紧张、结尾钩子、收尾情绪释放。
5. 跨章一致性：人物代词、产线数字、设备状态与前章基线是否矛盾。
6. 裸章号污染：正文段落是否出现「第291章」「291章」这类裸引用（应为 0）。
7. 首末行格式：首行须为「第292章 能源瓶颈」，末行须为「（本章完）」。
另须给出 DEAI_EDITOR_PASS 或 DEAI_EDITOR_FAIL 一行，附证据。""",

"reader": """【你的角色：读者席】
以真实追读者身份判断，不做文学评论：
1. 想不想看下一章？卡顿点在哪（给精确原句）？
2. 技术密度：数字与工程细节是否把你挤出故事？哪里跳读了？
3. 人物是否活的：有立场、有不耐烦对象、有复杂情绪？还是都在念参数？
4. 是否被低估：作者有没有抢答潜台词、替你总结结论、过度解释？
5. 声音塌陷：不同人物口吻是否趋同？
6. AI 味读感：句长是否均匀、有没有报告腔/会议纪要腔/金句收尾。
另须给出 DEAI_READER_PASS 或 DEAI_READER_FAIL 一行，附证据原句。""",

"science": """【你的角色：科学顾问席】
逐项验算正文中出现的每个物理/工程数值，只用正文给出的数字，算不通即 FAIL 并给出正确量级：
1. 火星轨道太阳常数、砷化镓效率、链路效率链（截获率×整流效率）、阵列端功率、有效面积、总质量，逐环是否自洽。
2. 微波输电：L1 到火星表面距离、5.8 GHz 频段、1 公里发射口径、衍射光斑直径是否与衍射极限自洽（θ≈1.22λ/D）。
3. 溢出功率密度与生物安全限、地表温升是否量级合理。
4. 聚变路线：氚种子量缺口除以增殖毯月产得出的周期是否算得对；改氘氚配比后点火阈值与第一壁寿命的因果是否成立。
5. 直流 1.8 吉瓦接交流母线的「相位差」表述是否物理正确（直流是否存在相位差）。
6. 遮挡率、光照率、Δv、运力比例的算术是否自洽。
7. 产线账：月产、良率、缺口、追平月数的算术是否正确。
另须给出 NUMERICAL_CONSISTENCY: PASS 或 FAIL 一行。""",

"military_institution": """【你的角色：军事/制度顾问席】
1. 权限与授权链：轨道防御用电、地表作业通行、监听阵列 A 级保障双方联签、军事许可，各自谁批、流程是否可信、有无越权。
2. 转运窗口分配：贡献积分制、公共池比例、让窗口的代价与补偿是否符合多方博弈逻辑，不是空喊。
3. 防御空窗风险陈述是否具体可核（在轨寿命、空窗天数、后果层级）。
4. 组织行为可信度：谁沉默、谁施压、谁咽回半句话，是否符合各自阵营利益，而非作者调度。
5. 制度连续性：是否与前章已确立的授权状态矛盾；是否把「授权入口已通」写成「具体任务已批」。
6. 是否越界替后续章节（293 拉格朗日计划）提前闭合本不该在本章解决的事。
另须给出 INSTITUTIONAL_CONSISTENCY: PASS 或 FAIL 一行。""",

"structure": """【你的角色：结构终审席】
1. 单场景单章的信息编排：420 kW 缺口如何逐条排除备选路线，排除顺序是否递进不重复。
2. 五条被否路线（电网余量/维生泵/监听阵列/轨道防御/遗迹核心）是否各自有独立否决理由，无重复功能段。
3. 两个选址方案的对照是否构成真实抉择（代价可量化、结论有反悔成本）。
4. 陈若水产线线与方宁能源线是否形成结构对抗，而非并列陈述。
5. 章末是否留下可追索的新问题（运力谈判、积分补偿、界桩作业），并为 293 章留接口而不越界。
6. 段落长度分布：是否存在连续三段长度相近的均匀化（AI 节奏特征）。给出具体段号。
7. 收束判定：STRUCTURE_RELEASE: PASS 或 FAIL 一行。""",

"deai_final": """【你的角色：去AI化终审席】
逐层扫描，每层给证据原句与行内定位：
1. 用词层（Perplexity）：是否趋向均值安全词。禁词清单：真正/核心/关键/意味着/与此同时/值得注意的是/这背后/首先其次最后。
2. 节奏层（Burstiness）：相邻段字数差是否≥2倍；是否有≤10字短句；是否连续三句长度相近。
3. 结构层九信号：结构壳、转场指纹、声音塌陷、RLHF 稳妥腔（过顺/假洞察/金句收尾）。
4. 身份层：人物是否有立场、有不耐烦对象、有复杂情绪，还是塌成中性助手。
5. 公式句硬闸：「不是…而是」「不是…是」句式（对白口语中的正常用法可豁免，须逐条说明豁免理由）。
6. 报告腔/工作状态词：门禁/清洁/闭环/PASS/流程 这类词是否混入正文。
7. 引号：是否全为中文弯引号，数量是否平衡。
另须给出 DEAI_FINAL_PASS 或 DEAI_FINAL_FAIL 一行。""",
}

def build_prompt(role):
    return (COMMON_HEAD.replace("{ROLE}", role)
            + "\n" + ROLE_TASK[role]
            + "\n\n===== 以下是第292章 R3 候选稿正文全文（送审对象，共 %d 行，净中文 %d）=====\n\n" % (body.count("\n")+1, cjk)
            + body
            + "\n\n===== 正文全文结束 =====\n\n请现在输出你的审稿报告，首部三行照写。\n")

def run_seat(seat, provider, model, attempt=1):
    prompt = build_prompt(seat)
    t0 = time.time()
    cmd = ["hermes", "chat", "-Q", "--provider", provider, "-m", model,
           "--ignore-rules", "-t", "", "-q", prompt]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=360, cwd="/root")
        return dict(seat=seat, provider=provider, model=model, rc=p.returncode,
                    elapsed=round(time.time()-t0,1), attempt=attempt,
                    stdout=p.stdout or "", stderr=(p.stderr or "")[-500:])
    except subprocess.TimeoutExpired as e:
        return dict(seat=seat, provider=provider, model=model, rc="TIMEOUT",
                    elapsed=round(time.time()-t0,1), attempt=attempt,
                    stdout=(e.stdout.decode("utf-8","ignore") if isinstance(e.stdout,bytes) else (e.stdout or "")),
                    stderr="timeout360")

results = {}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(run_seat, *s): s[0] for s in SEATS}
    for f in concurrent.futures.as_completed(futs):
        r = f.result()
        results[r["seat"]] = r
        print(f"[done] {r['seat']} rc={r['rc']} {r['elapsed']}s len={len(r['stdout'])}", flush=True)

# 单席失败重试一次（同 provider，禁换 GLM-5.2，禁同 provider 代替别席）
for seat, provider, model in SEATS:
    r = results.get(seat)
    if r is None or r["rc"] != 0 or len(r["stdout"].strip()) < 200:
        print(f"[retry] {seat} rc={r['rc'] if r else 'NONE'} len={len(r['stdout']) if r else 0}", flush=True)
        r2 = run_seat(seat, provider, model, attempt=2)
        print(f"[retry-done] {seat} rc={r2['rc']} {r2['elapsed']}s len={len(r2['stdout'])}", flush=True)
        if len(r2["stdout"].strip()) > len((r or {}).get("stdout","").strip()):
            results[seat] = r2

for seat, _, _ in SEATS:
    r = results[seat]
    path = os.path.join(REVDIR, f"{seat}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(r["stdout"])
    r["file"] = path

with open(os.path.join(OUT, "_raw_six_review_meta.json"), "w", encoding="utf-8") as fh:
    json.dump({k: {kk: vv for kk, vv in v.items() if kk != "stdout"} for k, v in results.items()},
              fh, ensure_ascii=False, indent=2)

print(json.dumps({k: dict(rc=v["rc"], elapsed=v["elapsed"], attempt=v["attempt"],
                          bytes=len(v["stdout"]), file=v["file"]) for k, v in results.items()},
                 ensure_ascii=False, indent=2))
