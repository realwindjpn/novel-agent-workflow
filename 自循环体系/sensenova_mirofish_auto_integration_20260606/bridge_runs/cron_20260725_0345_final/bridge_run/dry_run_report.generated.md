# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-25T03:58:09
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260725_0345
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 5
- fresh_news_card_count: 5
- valid_input_count: 5
- skipped_count: 116
- body_fetch_evidence_count: 11
- skip_reason_counts: {"no_dyson_tree_match": 17, "body_clean_too_short": 1, "not_article_page_url": 1, "duplicate_within_run": 5, "duplicate_url": 2, "summary_not_body_evidence": 5, "missing_body_path": 13, "title_too_short": 2, "low_value_expo_or_conference": 1, "stale_domestic_article": 1, "low_value_policy_theory_source": 1, "low_value_policy_or_commentary": 1, "query_plan_no_body": 66}
- stale_domestic_blocked_count: 1
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 1, "ARCHIVE_WITH_REASON": 4}
- conversion_task_count: 1

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260725_0345_final/bridge_runs/cron_20260725_0345/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260725_0345_final/bridge_runs/cron_20260725_0345/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260725_0345_final/bridge_runs/cron_20260725_0345/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260725_47458aabf3 | New Crew Members Welcomed to International Space Station | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260725_9996f197a2 | NASA Announces New Spacecraft Technology Demonstration Mission at Moon | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260725_f5d0ac0ad5 | NASA to Support Blue Origin New Glenn Rocket Testing, Advance Artemis | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260725_c21f291d9b | Two new Galileo satellites enter service | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260725_b5bd384e2b | 我国成功发射天链二号06星 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |

## Skipped

| title | source status | reason |
|---|---|---|
| NASA’s ESCAPADE Snaps Family Portrait of Earth, Moon | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Hubble Spies One-Sided Spiral | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Why total solar eclipses are so special | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| NASA’s ESCAPADE Snaps Family Portrait of Earth, Moon | ARCHIVE_WITH_REASON | duplicate_within_run |
| NASA Announces New Spacecraft Technology Demonstration Mission at Moon | DISTILLED | duplicate_within_run |
| NASA to Support Blue Origin New Glenn Rocket Testing, Advance Artemis | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Why total solar eclipses are so special | SUMMARY_ONLY | duplicate_within_run |
| Two new Galileo satellites enter service | SUMMARY_ONLY | duplicate_within_run |
| AINTMA: Agentic AI Architecture for Autonomous Test Management with Generative I | SUMMARY_ONLY | summary_not_body_evidence |
| ClickGuard: Detecting and Spoiling Clickbait News with Informativeness Measures  | SUMMARY_ONLY | summary_not_body_evidence |
| JAXBench: Benchmarking Autonomous TPU Kernel Optimization | SUMMARY_ONLY | summary_not_body_evidence |
| DC-Leap: Training-Free Acceleration of dLLMs via Draft-Guided Contiguous Leaping | SUMMARY_ONLY | summary_not_body_evidence |
| Announcements Jul 9, 2026 Inviting hard questions We’re asking the public for th | SUMMARY_ONLY | summary_not_body_evidence |
| g7 leaders statement ai prosperity | NEED_FETCH_BODY | missing_body_path |
| about | ARCHIVE_WITH_REASON | TITLE_TOO_SHORT |
| prime minister carney concludes 2025 g7 leaders summit | NEED_FETCH_BODY | missing_body_path |
| g7 leaders statement on ai for prosperity | NEED_FETCH_BODY | missing_body_path |
| chairs summary | NEED_FETCH_BODY | missing_body_path |
| g7 leaders summit | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| priorities | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| g7 energy and ai work plan | NEED_FETCH_BODY | missing_body_path |
| g7 call to action on enhancing energy security | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump attends g7 summit in canada | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump attends the g7 official welcome | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump participates in a g7 family photo | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump participates in an official greeting with g7 leaders | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| claude fable 5 mythos 5 | NEED_FETCH_BODY | missing_body_path |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 高质量数据集建设激活人工智能发展新动能 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| 250617 summary | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 250617 ai | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| iran said to threaten israel reject us ceasefire proposal passed along by iraqi  | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 0000019f 936e d1a3 adff f3ff9a1d0000 | NEED_FETCH_BODY | missing_body_path |
| 4007651 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| trump brokered ceasefire agreement contact with israel iran white house official | NEED_FETCH_BODY | missing_body_path |
| trump diplomacy iran israel ceasefire | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| trump israel iran ceasefire | NEED_FETCH_BODY | missing_body_path |
| israel iran ceasefire is in effect trump says | NEED_FETCH_BODY | missing_body_path |
| 消息人士称伊朗拒绝特朗普停火提议 | NEED_FETCH_BODY | missing_body_path |
| 川普宣布以色列和伊朗已同意 全面停火 222707882 | NEED_FETCH_BODY | missing_body_path |
| model deprecations | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| c1024 40247782 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c40531 40710030 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| c1004 40765423 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
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
| [QP:cas.cn] 航天 深空 机器人 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:iop.cas.cn] 量子 材料 能源 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cac.gov.cn] 人工智能 治理 数据 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cac.gov.cn] 网络安全 数据安全 生成式人工智能 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cmse.gov.cn] 载人航天 空间站 天舟 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
