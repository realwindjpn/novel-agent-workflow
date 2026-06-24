# SkyClaw 只读审核报告 — G2 MiroFish 升级补丁

审核时间: 2026-06-04
审核者: SkyClaw (skywork-ai/skyclaw-v1)
输入目录: /root/workspace/科武纪元/自循环体系/G2_mirofish_upgrade_20260604/
参考: /root/workspace/科武纪元/实验/mirofish_variable_injection_mvp/sensenova_20260604_inference/INFERENCE_REPORT.md

---

## 一、五项审核口径逐项判定

### 1. 是否解决"素材去向不明/全部NOTE_ONLY"问题

**判定: PASS**

证据:
- SPEC §1 明确将"NOTE_ONLY 可吞掉素材去向"列为旧 G2 失败点。
- SPEC §5 禁止项第一条: "禁止输出 NOTE_ONLY 作为终态"。
- PATCH 第37-40行: "禁止使用 NOTE_ONLY 作为终态" + "禁止出现可参考/以后再看/暂存但无去向"。
- DECISION_CARD_SCHEMA.json: `recommended_disposition` 和 `final_disposition.status` 的 enum 仅含三态，NOTE_ONLY 不在合法值中。
- MODEL_LEDGER verification[0]: "无NOTE_ONLY"。
- INFERENCE_REPORT 实测: 10张卡 → 2 OUTLINE_PATCH + 4 CHAPTER_PREP_ONLY + 4 ARCHIVE_WITH_REASON，零 NOTE_ONLY。

结论: 从规范层(SPEC/SCHEMA)到执行层(INFERENCE_REPORT)均消除 NOTE_ONLY 作为终态的可能。

### 2. 是否强制三态：OUTLINE_PATCH / CHAPTER_PREP_ONLY / ARCHIVE_WITH_REASON

**判定: PASS**

证据:
- SPEC §4 完整定义三态，每态有明确定义、必填字段、输出动作。
- PATCH 第15行: "每张素材必须最终落入且仅落入以下三态之一"。
- SCHEMA: `recommended_disposition` enum = [OUTLINE_PATCH, CHAPTER_PREP_ONLY, ARCHIVE_WITH_REASON]。
- SCHEMA: `final_disposition.status` enum 同上。
- SPEC §5: "禁止空 disposition"。
- SPEC §109 验收: "素材数 = 三态处置数总和"。
- RUNBOOK §3 硬门禁: "每张素材必须有且仅有一个最终 disposition"。

结论: 三态强制，无逃逸路径。

### 3. 是否保持边界：不直接改正式大纲/正文/TXT/Wiki/RAG/Git

**判定: PASS**

证据:
- SPEC 顶部 hard_boundary: "不改正式大纲 latest；不改正文/TXT/Wiki/RAG/cron/job"。
- SPEC §5 禁止项: "禁止 OUTLINE_PATCH 直接写大纲 latest" + "禁止把今日 2 个 OUTLINE_PATCH 实测项直接入纲"。
- RUNBOOK §0 明确区分"自动可做"与"需用户确认"：apply 大纲、改正文、写 Wiki/RAG、cron、Git commit 全部需用户确认。
- RUNBOOK §4: OUTLINE_PATCH 的 apply_status=PENDING_USER_CONFIRM。
- MODEL_LEDGER: MiroFish boundary="只产预处理卡，不裁决，不改大纲正文"；G2主席 boundary="只产候选，需用户确认后才可apply"；SkyClaw boundary="巡查与异常提醒，不做终验，不改正式文件"；主控 boundary="不写正文，不替代子模型返修，不直接apply大纲"。
- STATUS.json boundaries 数组明确列出三条红线。

结论: 边界清晰，四层角色(预处理/主席/巡查/主控)均有独立 boundary 声明，无越权路径。

### 4. 是否可在SenseNova跑完后自动接入MiroFish→G2

**判定: PASS**

证据:
- RUNBOOK §1 定义完整通过条件(overall=DONE, card_review=done, valid_content_cards>0, card_pass_count>0, 至少一个卡有URL与正文证据)。
- RUNBOOK §1 定义失败动作(NEED_CONTROLLER / ARCHIVE_WITH_REASON / 只处理有效卡)。
- RUNBOOK §2: MiroFish "自动推进：可"，"用户确认：不需要"。
- RUNBOOK §3: G2 "可自动跑会议与生成候选"，"apply 大纲前必须确认"。
- PATCH 第71-73行: "SenseNova run overall=DONE 且 card_review=done 后，立即进入：素材卡定位 → MiroFish 决策卡 → G2 六角色会议 → 三态处置"。
- STATUS.json next_action: "SenseNova完成后启动全套流程"。

结论: 自动化链路完整，触发条件明确，失败路径有定义。

### 5. 是否有阶段汇报/错误汇报机制

**判定: PASS (有改进建议)**

证据:
- RUNBOOK §1 失败动作: NEED_CONTROLLER 回报告控。
- RUNBOOK §7 SkyClaw审核: 输出 PASS/FAIL/NEED_CONTROLLER 三态。
- PATCH 第67行: state.json 输出 G2_DONE 或 NEED_CONTROLLER。
- MODEL_LEDGER: SkyClaw 角色负责巡查，主控负责终验。

改进建议（非阻塞）:
- state.json 仅定义 G2_DONE / NEED_CONTROLLER 两态，建议增加 G2_FAIL 以区分"需要人工介入"与"流程失败"。
- 建议 inbox 事件增加阶段标记（如 MIROFISH_DONE / G2_MEETING_DONE / SKYCLAW_REVIEW_DONE），便于巡查定位卡点。

## 二、附加发现

### 2.1 MODEL_LEDGER 角色路由审查

- MiroFish: MiMo Pro → GPT5.5，合理。
- G2主席: GPT5.5 (freemodel → byeapi)，合理。
- 编辑席: GPT5.5 (freemodel → byeapi)。
- 读者席: GPT5.5 (freemodel → aixiaobai)，boundary 声明"MiMo不得作闭环读者自审"，合规。
- 科学顾问: GLM-5.1 (glm1 → zai)，合理。
- 军事顾问: GLM-5.1 (glm2 → zai)，合理。

**注意（非阻塞）**: 主席/编辑/读者三席均首选 GPT5.5。若同一模型实例同时扮演三席，六角色"独立裁决"的有效性会打折扣。建议执行时尽量用不同 provider 的 GPT5.5 路由（freemodel/byeapi/aixiaobai 已覆盖），或至少声明模型实例隔离。

### 2.2 fallback_policy 中的 hikari

MODEL_LEDGER fallback_policy 末尾提到 hikari，但当前配置中 hikari provider 是否可用需在执行前验证。若不可用，不影响流程但不影响本次审核结论。

### 2.3 STATUS.json inbox_event 路径

STATUS.json inbox_event 指向 `/root/workspace/agent_inbox/mirofish_kewu_mvp.jsonl`（旧 MVP 路径）。本次审核结果将写入 `kewu_g2_mirofish_flow.jsonl`。建议后续统一 inbox 路径到 G2 专用文件。

### 2.4 INFERENCE_REPORT 实测数据

- 10张卡全部 CARD_PASS，body_fetch 100%。
- 2 OUTLINE_PATCH + 4 CHAPTER_PREP_ONLY + 4 ARCHIVE_WITH_REASON = 10，三态完整。
- 与 0603 会议 67 张卡全部 NOTE_ONLY 形成鲜明对比，验证了新流程的有效性。

## 三、总判定

| 审核项 | 判定 |
|--------|------|
| 解决NOTE_ONLY | PASS |
| 强制三态 | PASS |
| 保持边界 | PASS |
| 自动接入 | PASS |
| 汇报机制 | PASS (建议改进) |

**verdict: PASS**
**blocking: []**

非阻塞建议:
1. state.json 增加 G2_FAIL 态。
2. inbox 增加阶段标记事件。
3. 执行时注意 GPT5.5 多席位的模型实例隔离。
4. 统一 inbox 路径到 G2 专用文件。
5. 执行前验证 hikari fallback 可用性。

**next_action: 可作为下一次 SenseNova 完成后全套流程的执行依据。SenseNova 跑完即触发 MiroFish → G2。**

---
*SkyClaw 只读审核，未改任何正式项目文件。*
