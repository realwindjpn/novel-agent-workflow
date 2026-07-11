# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-06T19:08:31
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260706_1845
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 9
- fresh_news_card_count: 9
- valid_input_count: 9
- skipped_count: 93
- body_fetch_evidence_count: 10
- skip_reason_counts: {"body_clean_too_short": 1, "http_403|jina_timeout": 2, "not_article_page_url": 1, "duplicate_within_run": 2, "duplicate_url": 2, "connection_error|jina_timeout": 7, "worker_timeout:fetch_body:14s": 1, "missing_body_path": 11, "summary_not_body_evidence": 1, "query_plan_no_body": 65}
- stale_domestic_blocked_count: 0
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 2, "CHAPTER_PREP_ONLY": 0, "ARCHIVE_WITH_REASON": 7}
- conversion_task_count: 0

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260706_1845_final/bridge_runs/cron_20260706_1845/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260706_1845_final/bridge_runs/cron_20260706_1845/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260706_1845_final/bridge_runs/cron_20260706_1845/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260706_cd0ebde5ac | NASA’s Hubble Captures Crimson Cloud Sparkling with White, Blue Stars | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260706_03323aa936 | NASA’s Artemis II Breaks Agency Streaming Record | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260706_c93eabdf5f | Electrodeposited self-assembled molecules for perovskite photovoltaics | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| OUTLINE_PATCH | 20260706_95bcbfe09f | 中国队夺得2026年RoboCup机器人世界杯冠军 | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| ARCHIVE_WITH_REASON | 20260706_5dd03329e4 | 中方代表团出席国际热核聚变实验堆(ITER)计划理事会第三十八届会议 | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260706_82ce83647e | The rise of computer chips — and the race to control them | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| OUTLINE_PATCH | 20260706_18fb258c53 | g7 leaders statement ai prosperity | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| ARCHIVE_WITH_REASON | 20260706_88ffee1295 | president donald j trump attends the 51st g7 summit in kananaskis alberta canada | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260706_821888ac55 | president trump attends the g7 official welcome | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |

## Skipped

| title | source status | reason |
|---|---|---|
| The most spectacular aurora of the εpsilon mission (so far!) | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| Earth from Space: Grand Canyon, US | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| NASA’s Artemis II Breaks Agency Streaming Record | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Earth from Space: Grand Canyon, US | BODY_FETCH_FAIL | duplicate_within_run |
| Observation of disorder-free localization using a (2+1)D lattice gauge theory on | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| about | BODY_FETCH_FAIL | CONNECTION_ERROR|JINA_TIMEOUT |
| g7 energy and environment ministers meeting energy and artificial intelligence | BODY_FETCH_FAIL | WORKER_TIMEOUT:fetch_body:14s |
| g7 leaders statement on ai for prosperity | BODY_FETCH_FAIL | CONNECTION_ERROR|JINA_TIMEOUT |
| chairs summary | BODY_FETCH_FAIL | CONNECTION_ERROR|JINA_TIMEOUT |
| g7 leaders summit | BODY_FETCH_FAIL | CONNECTION_ERROR|JINA_TIMEOUT |
| priorities | BODY_FETCH_FAIL | CONNECTION_ERROR|JINA_TIMEOUT |
| g7 energy and ai work plan | BODY_FETCH_FAIL | CONNECTION_ERROR|JINA_TIMEOUT |
| g7 call to action on enhancing energy security | BODY_FETCH_FAIL | CONNECTION_ERROR|JINA_TIMEOUT |
| president trump attends g7 summit in canada | NEED_FETCH_BODY | missing_body_path |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 高质量数据集建设激活人工智能发展新动能 | SUMMARY_ONLY | summary_not_body_evidence |
| 250617 ai | NEED_FETCH_BODY | missing_body_path |
| 122137343534723345 | NEED_FETCH_BODY | missing_body_path |
| 1271398617891201 | NEED_FETCH_BODY | missing_body_path |
| full text iran national security council statement ceasefire | NEED_FETCH_BODY | missing_body_path |
| israel hits key iranian petrochemical plant in massive gas field as mediators fl | NEED_FETCH_BODY | missing_body_path |
| irans supreme national security council says it has accepted two week ceasefire  | NEED_FETCH_BODY | missing_body_path |
| trump israel iran ceasefire | NEED_FETCH_BODY | missing_body_path |
| 1513116870173998 | NEED_FETCH_BODY | missing_body_path |
| trump announces extending iran ceasefire but says blockade remains | NEED_FETCH_BODY | missing_body_path |
| trumpceasefirevalidation | NEED_FETCH_BODY | missing_body_path |
| [QP:people.com.cn] 科技 创新 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:people.com.cn] 先进制造 产业升级 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:people.com.cn] 人工智能 半导体 算力 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
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
