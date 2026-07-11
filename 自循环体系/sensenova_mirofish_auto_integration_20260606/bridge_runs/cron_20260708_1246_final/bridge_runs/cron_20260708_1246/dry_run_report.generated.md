# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-08T13:04:15
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260708_1246
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 8
- fresh_news_card_count: 8
- valid_input_count: 8
- skipped_count: 106
- body_fetch_evidence_count: 12
- skip_reason_counts: {"body_clean_too_short": 3, "low_value_expo_or_conference": 1, "not_article_page_url": 1, "duplicate_within_run": 7, "duplicate_url": 2, "missing_body_path": 24, "summary_not_body_evidence": 3, "malformed_search_title": 2, "low_value_policy_theory_source": 1, "query_plan_no_body": 62}
- stale_domestic_blocked_count: 0
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 3, "ARCHIVE_WITH_REASON": 5}
- conversion_task_count: 3

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260708_1246_final/bridge_runs/cron_20260708_1246/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260708_1246_final/bridge_runs/cron_20260708_1246/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260708_1246_final/bridge_runs/cron_20260708_1246/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| CHAPTER_PREP_ONLY | 20260708_0f5031582e | Artemis II Crew and Apollo 14 Moon Tree | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260708_e9b52ff113 | July 2026 Satellite Puzzler | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| CHAPTER_PREP_ONLY | 20260708_d6e989d332 | NASA Takes Flight For America’s 250th | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| CHAPTER_PREP_ONLY | 20260708_9245fe17d0 | Unpacking Europe’s new weather imagers | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260708_42f6755785 | Earth from Space: Grand Canyon, US | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260708_16426b4ebc | ‘Humanizer’ tool can erase signs of AI-written text — alarming scientists | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260708_5dd03329e4 | 中方代表团出席国际热核聚变实验堆(ITER)计划理事会第三十八届会议 | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260708_7a7d718505 | 高质量数据集建设激活人工智能发展新动能 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |

## Missing Cards by Tier

| tier | missing_card_ids |
|---|---|
| P1 | c1004_40753873_3602ea7ec61bc251, c461001_40730722_0389701a07463610 |

## Skipped

| title | source status | reason |
|---|---|---|
| The most spectacular aurora of the εpsilon mission (so far!) | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| Listen to Gen Z when it comes to AI in education | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| AI can cause harm: safeguards must catch up | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| 浦江之畔，看机器人加速突围 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| Artemis II Crew and Apollo 14 Moon Tree | DISTILLED | duplicate_within_run |
| July 2026 Satellite Puzzler | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Unpacking Europe’s new weather imagers | DISTILLED | duplicate_within_run |
| Earth from Space: Grand Canyon, US | SUMMARY_ONLY | duplicate_within_run |
| Publisher Correction: A 98-qubit trapped-ion quantum computer with all-to-all co | NEED_FETCH_BODY | missing_body_path |
| Listen to Gen Z when it comes to AI in education | NEED_FETCH_BODY | duplicate_within_run |
| AI can cause harm: safeguards must catch up | NEED_FETCH_BODY | duplicate_within_run |
| ‘Humanizer’ tool can erase signs of AI-written text — alarming scientists | NEED_FETCH_BODY | duplicate_within_run |
| Observation of disorder-free localization using a (2+1)D lattice gauge theory on | SUMMARY_ONLY | summary_not_body_evidence |
| Prompt-to-Paper: Agentic AI System for Bioinformatics | SUMMARY_ONLY | summary_not_body_evidence |
| CSTutorBench: Benchmarking Small Language Models as Tutors for Block-Based Progr | SUMMARY_ONLY | summary_not_body_evidence |
| 20292 | NEED_FETCH_BODY | missing_body_path |
| g7 leaders statement ai prosperity | NEED_FETCH_BODY | missing_body_path |
| backgrounder en | NEED_FETCH_BODY | missing_body_path |
| index | NEED_FETCH_BODY | missing_body_path |
| g7 leaders statement on ai for prosperity | NEED_FETCH_BODY | missing_body_path |
| chairs summary | NEED_FETCH_BODY | missing_body_path |
| g7 leaders summit | NEED_FETCH_BODY | missing_body_path |
| priorities | NEED_FETCH_BODY | missing_body_path |
| g7 energy and ai work plan | NEED_FETCH_BODY | missing_body_path |
| prime minister carney announces canadas g7 priorities ahead of leaders summit | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | NEED_FETCH_BODY | missing_body_path |
| president trump attends g7 summit in canada | NEED_FETCH_BODY | missing_body_path |
| president trump attends the g7 official welcome | NEED_FETCH_BODY | missing_body_path |
| president trump participates in a g7 family photo | NEED_FETCH_BODY | missing_body_path |
| president trump participates in an official greeting with g7 leaders | NEED_FETCH_BODY | missing_body_path |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 250617 summary | NEED_FETCH_BODY | missing_body_path |
| 250617 ai | NEED_FETCH_BODY | missing_body_path |
| netanyahu backs iran truce opposition blames him for diplomatic disaster | NEED_FETCH_BODY | missing_body_path |
| full text iran national security council statement ceasefire | NEED_FETCH_BODY | missing_body_path |
| story | NEED_FETCH_BODY | missing_body_path |
| trump israel iran ceasefire | NEED_FETCH_BODY | missing_body_path |
| model deprecations | NEED_FETCH_BODY | missing_body_path |
| c461001 40730722 | DISTILLED | malformed_search_title |
| c40531 40710030 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| c1004 40753873 | DISTILLED | malformed_search_title |
| [QP:xinhuanet.com] 先进制造 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:xinhuanet.com] query_plan | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
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
| [QP:nasa.gov] Artemis lunar program | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:esa.int] lunar exploration deep | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:darpa.mil] autonomous systems drone | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:defense.gov] drone swarm military | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:energy.gov] quantum energy research | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
