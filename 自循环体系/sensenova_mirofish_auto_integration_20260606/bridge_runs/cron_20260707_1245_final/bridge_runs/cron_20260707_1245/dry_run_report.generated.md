# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-07T13:02:49
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260707_1245
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 10
- fresh_news_card_count: 10
- valid_input_count: 10
- skipped_count: 93
- body_fetch_evidence_count: 12
- skip_reason_counts: {"body_clean_too_short": 1, "not_article_page_url": 1, "duplicate_within_run": 5, "summary_not_body_evidence": 3, "missing_body_path": 17, "duplicate_url": 1, "low_value_policy_or_commentary": 1, "low_value_policy_theory_source": 1, "low_value_expo_or_conference": 1, "malformed_search_title": 1, "stale_domestic_article": 1, "query_plan_no_body": 60}
- stale_domestic_blocked_count: 1
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 1, "ARCHIVE_WITH_REASON": 9}
- conversion_task_count: 1

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260707_1245_final/bridge_runs/cron_20260707_1245/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260707_1245_final/bridge_runs/cron_20260707_1245/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260707_1245_final/bridge_runs/cron_20260707_1245/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| CHAPTER_PREP_ONLY | 20260707_d6e989d332 | NASA Takes Flight For America’s 250th | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260707_feae32dc09 | NASA Seeks Industry Input on Second Phase of Commercial Space Stations | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260707_e56ae63e06 | NASA’s CAPSTONE Completes Extended Mission Testing Lunar Technologies | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260707_b857af4747 | Examining Algal Blooms in Blue Mesa | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260707_42f6755785 | Earth from Space: Grand Canyon, US | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260707_0a5a17fe93 | Universities are relying on AI-detection software to catch cheating. How well do | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260707_82ce83647e | The rise of computer chips — and the race to control them | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260707_c11845847e | Daily briefing: How cooperation built the world | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260707_5dd03329e4 | 中方代表团出席国际热核聚变实验堆(ITER)计划理事会第三十八届会议 | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260707_7a7d718505 | 高质量数据集建设激活人工智能发展新动能 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |

## Missing Cards by Tier

| tier | missing_card_ids |
|---|---|
| P1 | c_5b35174c990444c5 |

## Skipped

| title | source status | reason |
|---|---|---|
| The most spectacular aurora of the εpsilon mission (so far!) | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| NASA Takes Flight For America’s 250th | DISTILLED | duplicate_within_run |
| NASA’s CAPSTONE Completes Extended Mission Testing Lunar Technologies | DISTILLED | duplicate_within_run |
| Examining Algal Blooms in Blue Mesa | SUMMARY_ONLY | duplicate_within_run |
| Universities are relying on AI-detection software to catch cheating. How well do | NEED_FETCH_BODY | duplicate_within_run |
| The rise of computer chips — and the race to control them | NEED_FETCH_BODY | duplicate_within_run |
| Observation of disorder-free localization using a (2+1)D lattice gauge theory on | SUMMARY_ONLY | summary_not_body_evidence |
| Automated Data Readiness for Scientific AI | SUMMARY_ONLY | summary_not_body_evidence |
| SwarmResearch: Orchestrating Coding Agents for Open-Ended Discovery | SUMMARY_ONLY | summary_not_body_evidence |
| g7 leaders statement ai prosperity | NEED_FETCH_BODY | missing_body_path |
| about | NEED_FETCH_BODY | missing_body_path |
| g7 energy and environment ministers meeting energy and artificial intelligence | NEED_FETCH_BODY | missing_body_path |
| g7 leaders statement on ai for prosperity | NEED_FETCH_BODY | missing_body_path |
| index | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | NEED_FETCH_BODY | missing_body_path |
| president trump attends g7 summit in canada | NEED_FETCH_BODY | missing_body_path |
| president trump attends the g7 official welcome | NEED_FETCH_BODY | missing_body_path |
| foreign secretary statement ceasefire in the middle east 8 april | NEED_FETCH_BODY | missing_body_path |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 250617 ai | NEED_FETCH_BODY | missing_body_path |
| 1022261090060174 | NEED_FETCH_BODY | missing_body_path |
| 122137343534723345 | NEED_FETCH_BODY | missing_body_path |
| 1271398617891201 | NEED_FETCH_BODY | missing_body_path |
| iran war us trump strikes ceasefire lebanon israel | NEED_FETCH_BODY | missing_body_path |
| story | NEED_FETCH_BODY | missing_body_path |
| irans supreme national security council says it has accepted two week ceasefire  | NEED_FETCH_BODY | missing_body_path |
| trump israel iran ceasefire | NEED_FETCH_BODY | missing_body_path |
| c461530 40705990 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| c40531 40521652 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| c1004 40732291 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c | DISTILLED | malformed_search_title |
| c | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
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
| [QP:noaa.gov] satellite climate ocean | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:pubmed.ncbi.nlm.nih.gov] brain computer interface | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:arxiv.org] quantum computing | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:arxiv.org] AI safety robotics | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:openalex.org] quantum computing AI | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:nature.com] quantum computing AI | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:science.org] quantum AI energy | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:ieee.org] AI chips robotics | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:bis.gov] export control semiconductors | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:semiconductors.org] semiconductor industry chips | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:g7.canada.ca] G7 Summit Kananaskis | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:g7.canada.ca] Group of Seven | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:canada.ca] G7 Summit Kananaskis | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
