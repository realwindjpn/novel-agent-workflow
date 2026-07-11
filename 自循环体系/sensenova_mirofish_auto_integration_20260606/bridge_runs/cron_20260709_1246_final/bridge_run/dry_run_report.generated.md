# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-09T13:07:39
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260709_1246
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 11
- fresh_news_card_count: 11
- valid_input_count: 11
- skipped_count: 94
- body_fetch_evidence_count: 14
- skip_reason_counts: {"http_403|jina_timeout": 2, "not_article_page_url": 1, "duplicate_within_run": 3, "duplicate_url": 2, "missing_body_path": 21, "malformed_search_title": 2, "low_value_policy_theory_source": 1, "query_plan_no_body": 62}
- stale_domestic_blocked_count: 0
- p0_missing: True
- disposition_counts: {"OUTLINE_PATCH": 2, "CHAPTER_PREP_ONLY": 2, "ARCHIVE_WITH_REASON": 7}
- conversion_task_count: 2

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260709_1246_final/bridge_runs/cron_20260709_1246/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260709_1246_final/bridge_runs/cron_20260709_1246/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260709_1246_final/bridge_runs/cron_20260709_1246/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260709_c81993ac0c | Students Connect NASA Science With Indigenous Knowledge to Study Coastal Erosion | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260709_b96eaacc0f | NASA Awards Contracts for Mars Advanced Surface Mobility Technology | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260709_dd80ed61d1 | Deep space software upgrade for Hera’s asteroid visit | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260709_9245fe17d0 | Unpacking Europe’s new weather imagers | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| CHAPTER_PREP_ONLY | 20260709_0994e11f8e | 从“拼体力”到“拼算力”，防减救灾用上这些新科技 | 气象/地球观测素材，可作章节准备包中的遥感盲区/侦察代价参考；非地月深空链。 |
| ARCHIVE_WITH_REASON | 20260709_5dd03329e4 | 中方代表团出席国际热核聚变实验堆(ITER)计划理事会第三十八届会议 | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260709_e3675e1e47 | New European exercise device begins testing with first rope-pulling workout in s | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260709_a925771962 | In vivo feasibility study of humanoid robots in surgery | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| OUTLINE_PATCH | 20260709_5e7a7d45f6 | QANTIS: Hardware-Calibrated Sequential POMDP Belief Updates on IBM Heron | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| OUTLINE_PATCH | 20260709_ed8af4951a | Evaluating SageMath-Augmented LLM Agents for Computational and Experimental Math | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| ARCHIVE_WITH_REASON | 20260709_7a7d718505 | 高质量数据集建设激活人工智能发展新动能 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |

## Missing Cards by Tier

| tier | missing_card_ids |
|---|---|
| P0 | c1024_40756187_1c164c77affb25ff, c14540_41605856_7ab8de92b240dae5 |

## Skipped

| title | source status | reason |
|---|---|---|
| The most spectacular aurora of the εpsilon mission (so far!) | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| NASA Awards Contracts for Mars Advanced Surface Mobility Technology | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Deep space software upgrade for Hera’s asteroid visit | BODY_FETCH_FAIL | duplicate_within_run |
| Unpacking Europe’s new weather imagers | DISTILLED | duplicate_within_run |
| Observation of disorder-free localization using a (2+1)D lattice gauge theory on | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| g7 leaders statement ai prosperity | NEED_FETCH_BODY | missing_body_path |
| backgrounder en | NEED_FETCH_BODY | missing_body_path |
| index | NEED_FETCH_BODY | missing_body_path |
| g7 leaders statement on ai for prosperity | NEED_FETCH_BODY | missing_body_path |
| g7 leaders summit | NEED_FETCH_BODY | missing_body_path |
| chairs summary | NEED_FETCH_BODY | missing_body_path |
| priorities | NEED_FETCH_BODY | missing_body_path |
| g7 energy and ai work plan | NEED_FETCH_BODY | missing_body_path |
| g7 call to action on enhancing energy security | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | NEED_FETCH_BODY | missing_body_path |
| president trump attends g7 summit in canada | NEED_FETCH_BODY | missing_body_path |
| president trump attends the g7 official welcome | NEED_FETCH_BODY | missing_body_path |
| president trump participates in a g7 family photo | NEED_FETCH_BODY | missing_body_path |
| president trump participates in an official greeting with g7 leaders | NEED_FETCH_BODY | missing_body_path |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 250617 summary | NEED_FETCH_BODY | missing_body_path |
| 250617 ai | NEED_FETCH_BODY | missing_body_path |
| trump says ceasefire over after us iran trade attacks | NEED_FETCH_BODY | missing_body_path |
| trump israel iran ceasefire | NEED_FETCH_BODY | missing_body_path |
| trumpceasefirevalidation | NEED_FETCH_BODY | missing_body_path |
| watch live white house holds briefing as trump agrees to two week ceasefire in i | NEED_FETCH_BODY | missing_body_path |
| c1024 40756187 | DISTILLED | malformed_search_title |
| c40531 40710030 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| c14540 41605856 | DISTILLED | malformed_search_title |
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
