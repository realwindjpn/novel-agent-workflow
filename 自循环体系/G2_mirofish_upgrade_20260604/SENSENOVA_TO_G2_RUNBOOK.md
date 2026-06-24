# SENSENOVA_TO_G2_RUNBOOK

status: READY_FOR_SKYCLAW_REVIEW
next_sensenova_eta: 2026-06-04 19:42 后
trigger: SenseNova 跑完即启动全套新流程

## 0. 总边界

自动可做：
- 定位 SenseNova 最新 run_dir。
- 读取报告与素材卡。
- 生成 MiroFish decision_cards。
- 启动 G2 六角色会议。
- 产出三态处置、delta 候选、G3准备包、归档理由。
- 写 state/inbox，交 SkyClaw 审核。

需用户确认：
- 把 OUTLINE_PATCH apply 到正式大纲 latest。
- 改正文/新版/TXT。
- 写 Wiki/RAG/知识库。
- 创建/修改 cron/job。
- 上传番茄/草稿箱/发布。
- Git commit。

## 1. 素材卡定位

输入：SenseNova run_dir。
判定最新目录：优先读取当前 cron 输出；否则按 mtime 取 `/root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_*` 最新。

必查文件：
- reports/final_report.md
- reports/card_review_summary.md
- cards/*.md
- cards/card_distill_plan.json
- raw/body_fetch_report.json

通过条件：
- overall=DONE。
- card_review status=done。
- valid_content_cards > 0。
- card_pass_count > 0。
- 至少一个 cards/*.md 有 URL 与正文证据。

失败动作：
- 无 cards：NEED_CONTROLLER。
- 只有 query_plan_cards：ARCHIVE_WITH_REASON，不进入 G2。
- body_fetch 大量失败但仍有正文证据卡：只处理有效卡，失败项写 excluded_materials。

## 2. MiroFish 决策卡

谁做：MiMo/GPT5.5。
输入：每张有效素材卡 + 只读大纲/Wiki索引。
输出目录：`G2_mirofish_<date>/decision_cards/`。
每卡输出：DECISION_CARD_SCHEMA.json 实例。

每卡必须含：
- material_id、source_url、title、captured_at。
- fact_kernel。
- force_reactions。
- chain_conflicts。
- chapter_hooks。
- outline_delta_candidate。
- anti_patterns。
- recommended_disposition。

自动推进：可。
用户确认：不需要。
禁止：不改正式大纲，不改正文。

## 3. G2 六角色会议

谁做：六角色。
输入：decision_cards。
输出：
- g2_role_votes.json。
- material_disposition.md。
- outline_delta_candidates.md。
- chapter_prep_notes.md。
- archive_reasons.md。
- g2_meeting_summary.md。

硬门禁：
- 禁 NOTE_ONLY。
- 每张素材必须有且仅有一个最终 disposition。
- OUTLINE_PATCH 只能是 candidate。
- 六角色独立发言必须存在；单模型主席裁决只可标 preliminary。

自动推进：可自动跑会议与生成候选。
用户确认：apply 大纲前必须确认。

## 4. 大纲 delta 候选

OUTLINE_PATCH 输出至 outline_delta_candidates。
每项含：
- material_id。
- target_chapter。
- target_outline_section。
- proposed_delta_text。
- reason。
- risk。
- required_review。
- apply_status=PENDING_USER_CONFIRM。

自动推进：生成候选可自动。
用户确认：写入正式大纲 latest 前必须确认。
禁止：直接把今日 2 个 OUTLINE_PATCH 写入大纲。

## 5. G3准备包/备注层

CHAPTER_PREP_ONLY 输出至 chapter_prep_notes。
每项含：
- material_id。
- target_chapters。
- usage_scene。
- fact_anchor。
- anti_patterns。
- retrieval_tag。

自动推进：可进入 G3 准备包。
用户确认：若只写准备包/备注层，不改正式文件，可自动；若要写入 Wiki/RAG/正式大纲，需确认。

## 6. G4/G6边界

G4 章节精修启动条件：
- G2 三态完成。
- G3 准备包完成。
- 目标章节为当前上传线 N+1/N+2 或用户明确授权。
- 源稿存在且完整。
- 六角色闭环路线可用。

G4 禁止条件：
- 只有 MiroFish 预处理，无 G2 六角色裁决。
- OUTLINE_PATCH 尚未确认但会影响目标章功能。
- 目标章无源稿。

G6 项目同步启动条件：
- 正式大纲/正文实际修改后。
- 六角色复审 PASS 后。

本流程包本轮不触发 G4/G6，只定义边界。

## 7. SkyClaw审核

谁做：SkyClaw。
审核点：
- 文件齐。
- 三态规则完整。
- 无 NOTE_ONLY。
- 无正式文件越界。
- STATUS 与 inbox 存在。

输出：PASS / FAIL / NEED_CONTROLLER。
主控终验后再决定是否接入下一次 SenseNova run。
