# G2_MIROFISH_UPGRADE_SPEC

status: READY_FOR_SKYCLAW_REVIEW
scope: SenseNova → MiroFish → G2 六角色融纲会议
hard_boundary: 不改正式大纲 latest；不改正文/TXT/Wiki/RAG/cron/job；只产流程包与候选。
next_sensenova_eta: 2026-06-04 19:42 后；SenseNova 跑完即触发新流程。

## 1. 修复目标

旧 G2 失败点：
- 会议直接看原始素材卡。
- 缺少素材→章节→冲突链转换层。
- NOTE_ONLY 可吞掉素材去向。
- 大纲很久未优化，素材归宿不清。

新 G2 目标：
- 每张 SenseNova 有正文证据的素材卡，先生成 MiroFish 决策卡。
- G2 六角色逐卡裁决三态。
- 每张素材必须有去向。
- OUTLINE_PATCH 只成为大纲 delta 候选，不直接写入 latest。
- CHAPTER_PREP_ONLY 进入章节准备包/备注层。
- ARCHIVE_WITH_REASON 归档且必须写明弃用理由。

## 2. 输入门禁

允许输入：
- SenseNova run_dir。
- cards/ 下素材卡。
- reports/final_report.md。
- reports/card_review_summary.md。
- 当前大纲 latest 只读。
- Wiki/角色/势力/技术索引只读。

拒绝输入：
- query_plan_cards 仅骨架、无正文证据者。
- body_fetch_failed 且无可靠正文证据者。
- 登录/付费/验证码源。
- 来源不明、无 URL、无 captured_at 的素材。

## 3. 流程

1. SenseNova 完成。
2. 主控或 SkyClaw 定位最新 run_dir。
3. 读取 final_report，确认 overall=DONE，valid_content_cards>0，card_review=done。
4. MiroFish 预处理读取每张有效素材卡。
5. 每卡生成 DECISION_CARD_SCHEMA 实例。
6. G2 六角色会议读取 decision_cards，不再只读原始素材。
7. 六角色逐卡输出三态裁决。
8. 主席汇总为三份候选：outline_delta_candidates、chapter_prep_notes、archive_disposition。
9. SkyClaw 巡查字段完整性与越界风险。
10. 主控终验，决定是否进入正式大纲 patch 审批。

## 4. 三态定义

### OUTLINE_PATCH

定义：素材改变章节功能、冲突链、势力策略、技术红线，值得进入大纲 delta 候选。
必须含：
- target_chapter。
- delta_type: note_layer/conflict_chain/force_reaction/red_line/hook。
- proposed_delta_text。
- why_outline_not_prep。
- risk_and_review_needed。

动作：
- 写入 outline_delta_candidates.md/json。
- 状态 PENDING_G2_APPLY_CONFIRM。
- 需用户确认后，才可改正式大纲 latest。

### CHAPTER_PREP_ONLY

定义：素材适合写作时调用，但不改变大纲结构。
必须含：
- target_chapters。
- usage_scene。
- quote_or_fact_anchor。
- anti_patterns。
- retrieval_tag。

动作：
- 写入 chapter_prep_notes.md/json。
- 可自动进入 G3 准备包或备注层。
- 不改正文，不生成 TXT。

### ARCHIVE_WITH_REASON

定义：素材不进入大纲，不进入准备包，但保留可追溯弃用理由。
必须含：
- archive_reason。
- mismatch_dimension: core_conflict/scale/timing/weak_fact/no_story_value/duplicate。
- possible_revisit_condition。

动作：
- 写入 daily_material_disposition.md。
- 30 天内若新线索出现可回看。

## 5. 禁止项

- 禁止输出 NOTE_ONLY 作为终态。
- 禁止空 disposition。
- 禁止 OUTLINE_PATCH 直接写大纲 latest。
- 禁止把今日 2 个 OUTLINE_PATCH 实测项直接入纲。
- 禁止 G2 单模型预裁决冒充六角色会议。
- 禁止 MiMo 自审闭环。
- 禁止 G3/G4/G6 在 G2 三态处置缺项时启动。

## 6. 验收标准

PASS 条件：
- 素材数 = 三态处置数总和。
- 每张 decision_card 有 material_id/source/title/disposition/disposition_reason。
- OUTLINE_PATCH 均为 candidate 状态。
- CHAPTER_PREP_ONLY 有章节与使用场景。
- ARCHIVE_WITH_REASON 有具体弃用理由。
- MODEL_LEDGER 有 MiroFish、六角色、SkyClaw、主控。
- STATUS.status=READY_FOR_SKYCLAW_REVIEW。
- inbox 追加 G2_PATCH_READY。

FAIL 条件：
- 出现 NOTE_ONLY。
- 有素材无去向。
- 改了正式大纲/正文/TXT/Wiki/RAG/cron/job。
- G2 没有六角色独立裁决。
