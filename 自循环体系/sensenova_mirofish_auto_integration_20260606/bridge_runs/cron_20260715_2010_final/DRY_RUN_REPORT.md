# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-15T20:26:45
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260715_2010
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 5
- fresh_news_card_count: 5
- valid_input_count: 5
- skipped_count: 121
- body_fetch_evidence_count: 12
- skip_reason_counts: {"no_dyson_tree_match": 24, "body_clean_too_short": 1, "not_article_page_url": 1, "duplicate_within_run": 4, "duplicate_url": 2, "summary_not_body_evidence": 2, "missing_body_path": 15, "title_too_short": 2, "low_value_expo_or_conference": 1, "stale_domestic_article": 1, "low_value_policy_theory_source": 1, "low_value_policy_or_commentary": 1, "query_plan_no_body": 66}
- stale_domestic_blocked_count: 1
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 1, "CHAPTER_PREP_ONLY": 1, "ARCHIVE_WITH_REASON": 3}
- conversion_task_count: 1

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260715_2010_final/bridge_runs/cron_20260715_2010/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260715_2010_final/bridge_runs/cron_20260715_2010/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260715_2010_final/bridge_runs/cron_20260715_2010/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260715_4105eee13b | NASA Invites Media to Serbia Artemis Accords Signing Ceremony | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260715_ac608178dd | NASA Astronaut Anil Menon, Crewmates Arrive at Space Station | 展会/航展/博览会文，低技术突破增益，归档。 |
| OUTLINE_PATCH | 20260715_57ed9719fb | Hubble Sees Crimson Cloud and Stars | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| CHAPTER_PREP_ONLY | 20260715_58327154f3 | Metallic waves on ancient Mars | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260715_18d73b0b52 | Artemis II astronauts visit ESA | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |

## Skipped

| title | source status | reason |
|---|---|---|
| Curiosity Blog, Sols 4947-4953: Gale Crater Then and Now | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| NASA Jets Turn Red, White, and Blue | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 8 things to know about this year’s solar eclipse | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| AI models: one country’s fears become everyone’s constraint | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| NASA Invites Media to Serbia Artemis Accords Signing Ceremony | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Metallic waves on ancient Mars | SUMMARY_ONLY | duplicate_within_run |
| Artemis II astronauts visit ESA | SUMMARY_ONLY | duplicate_within_run |
| AI models: one country’s fears become everyone’s constraint | ARCHIVE_WITH_REASON | duplicate_within_run |
| Does AI work for us, or do we work for AI? | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| From ML Predictions to Informed Diagnostic Assistance Using the Toulmin Model of | SUMMARY_ONLY | summary_not_body_evidence |
| Inviting hard questions Announcements Jul 9, 2026 We’re asking the public for th | SUMMARY_ONLY | summary_not_body_evidence |
| Features Jul 6, 2026 The Making of Claude Code The inside story of how Claude Co | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| g7 leaders statement ai prosperity | NEED_FETCH_BODY | missing_body_path |
| about | ARCHIVE_WITH_REASON | TITLE_TOO_SHORT |
| backgrounder en | NEED_FETCH_BODY | missing_body_path |
| g7 leaders statement on ai for prosperity | NEED_FETCH_BODY | missing_body_path |
| chairs summary | NEED_FETCH_BODY | missing_body_path |
| g7 leaders summit | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| priorities | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| g7 energy and ai work plan | NEED_FETCH_BODY | missing_body_path |
| prime minister carney announces canadas g7 priorities ahead of leaders summit | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump attends g7 summit in canada | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump participates in a g7 family photo | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump participates in an official greeting with g7 leaders | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump attends the g7 official welcome | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| claude fable 5 mythos 5 | NEED_FETCH_BODY | missing_body_path |
| model deprecations | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| bis guidance may 31 2026 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| department commerce revises license review policy semiconductors exported china | NEED_FETCH_BODY | missing_body_path |
| bis guidance may 31 2026 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| department commerce announces rescission biden era artificial intelligence diffu | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| commerce strengthens restrictions advanced computing semiconductors enhance foun | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 高质量数据集建设激活人工智能发展新动能 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| 250617 summary | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 250617 ai | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| iran threatens halt mideast energy exports us reimposes blockade rcna587593 | NEED_FETCH_BODY | missing_body_path |
| trump brokered ceasefire agreement contact with israel iran white house official | NEED_FETCH_BODY | missing_body_path |
| trump israel iran ceasefire | NEED_FETCH_BODY | missing_body_path |
| trump iran ceasefire | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| model deprecations | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| claude mythos preview is deprecated but its replacement is currently unavailable | NEED_FETCH_BODY | missing_body_path |
| us says ban on ai chip shipments applies to chinese firms outside china | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| chinas long march 10b rocket successfully launches and lands in a global spacefl | NEED_FETCH_BODY | missing_body_path |
| 106903708 | NEED_FETCH_BODY | missing_body_path |
| 106891890 | NEED_FETCH_BODY | missing_body_path |
| c1024 40247782 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c40531 40710030 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| c1004 40760598 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| c | ARCHIVE_WITH_REASON | TITLE_TOO_SHORT |
| c | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| [QP:xinhuanet.com] 人工智能 半导体 算力 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:xinhuanet.com] 新材料 能源 动力装备 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:xinhuanet.com] 航天 深空 探测 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cctv.com] 先进制造 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cctv.com] query_plan | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cctv.com] 人工智能 半导体 算力 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cctv.com] 新材料 能源 动力装备 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cctv.com] 航天 深空 探测 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:stdaily.com] query_plan | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:stdaily.com] 新材料 先进制造 能源 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:stdaily.com] 人工智能 机器人 量子 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:huanqiu.com] 科技 国防 航天 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:huanqiu.com] 地缘 科技 产业链 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:guancha.cn] 半导体 出口管制 产业链 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:guancha.cn] 航天 军事 科技 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:miit.gov.cn] 新型工业化 先进制造 产业链 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:miit.gov.cn] 人工智能 半导体 算力 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:mod.gov.cn] 科技 国防 无人机 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:mod.gov.cn] 航天 网络 信息化 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:most.gov.cn] query_plan | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:most.gov.cn] 人工智能 量子 新材料 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cnsa.gov.cn] 月球 深空 探测工程 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cnsa.gov.cn] 航天 科技 探测 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cas.cn] 科技突破 重大进展 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cas.cn] 人工智能 量子 新材料 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
