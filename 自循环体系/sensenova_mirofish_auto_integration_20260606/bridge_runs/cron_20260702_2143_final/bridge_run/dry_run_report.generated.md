# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-02T22:04:28
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260702_2143
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 8
- fresh_news_card_count: 8
- valid_input_count: 8
- skipped_count: 92
- body_fetch_evidence_count: 12
- skip_reason_counts: {"not_article_page_url": 1, "duplicate_url": 3, "duplicate_within_run": 3, "http_403|jina_timeout": 1, "missing_body_path": 19, "stale_domestic_article": 1, "low_value_policy_theory_source": 1, "low_value_expo_or_conference": 1, "malformed_search_title": 1, "query_plan_no_body": 61}
- stale_domestic_blocked_count: 1
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 2, "ARCHIVE_WITH_REASON": 6}
- conversion_task_count: 2

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260702_2143_final/bridge_runs/cron_20260702_2143/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260702_2143_final/bridge_runs/cron_20260702_2143/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260702_2143_final/bridge_runs/cron_20260702_2143/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260702_75e31417c3 | What’s Up: July 2026 Skywatching Tips from NASA | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260702_32d4abbdd0 | NASA Seeks Volunteers for New Yearlong Simulated Moon, Mars Mission | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260702_64be161c54 | LINK Spacecraft Set for Mission to Boost NASA’s Swift Observatory | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260702_2a8a9c7788 | Authorisation paves the way for Aeolus-2 wind mission | 气象/地球观测素材，可作章节准备包中的遥感盲区/侦察代价参考；非地月深空链。 |
| CHAPTER_PREP_ONLY | 20260702_6c4d162cf4 | 我国成功发射海洋二号E卫星 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260702_8cef64f63e | Constructive Alignment: Governing Preference Dynamics in Human-AI Interaction | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260702_35012ff3e3 | RareDxR1: Autonomous Medical Reasoning for Rare Disease Diagnosis Beyond Human A | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260702_7a7d718505 | 高质量数据集建设激活人工智能发展新动能 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |

## Missing Cards by Tier

| tier | missing_card_ids |
|---|---|
| P1 | c_b0c99c5d13a0e3d7 |

## Skipped

| title | source status | reason |
|---|---|---|
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| 央地共建粤港澳大湾区国际科技创新中心工作推进会在广州召开 | SKIP_DUPLICATE | DUPLICATE_URL |
| What’s Up: July 2026 Skywatching Tips from NASA | DISTILLED | duplicate_within_run |
| NASA Seeks Volunteers for New Yearlong Simulated Moon, Mars Mission | DISTILLED | duplicate_within_run |
| LINK Spacecraft Set for Mission to Boost NASA’s Swift Observatory | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Dartmouth’s AI summer and what came next | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| strengthening the global semiconductor supply chain in an uncertain era | NEED_FETCH_BODY | missing_body_path |
| g7 leaders statement ai prosperity | NEED_FETCH_BODY | missing_body_path |
| index | NEED_FETCH_BODY | missing_body_path |
| backgrounder en | NEED_FETCH_BODY | missing_body_path |
| chairs summary | NEED_FETCH_BODY | missing_body_path |
| g7 energy and environment ministers meeting energy and artificial intelligence | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | NEED_FETCH_BODY | missing_body_path |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 250617 summary | NEED_FETCH_BODY | missing_body_path |
| 250617 ai | NEED_FETCH_BODY | missing_body_path |
| 1022261090060174 | NEED_FETCH_BODY | missing_body_path |
| 122137343534723345 | NEED_FETCH_BODY | missing_body_path |
| 51st G7 summit | NEED_FETCH_BODY | missing_body_path |
| 20260701 us iran doha talks end without breakthrough strait of hormuz | NEED_FETCH_BODY | missing_body_path |
| iran war us trump strikes ceasefire lebanon israel | NEED_FETCH_BODY | missing_body_path |
| us iran talks in qatar two sides agree to establish communication channel 1 | NEED_FETCH_BODY | missing_body_path |
| iran fires missiles israel ceasefire strains | NEED_FETCH_BODY | missing_body_path |
| irans supreme national security council says it has accepted two week ceasefire  | NEED_FETCH_BODY | missing_body_path |
| trump israel iran ceasefire | NEED_FETCH_BODY | missing_body_path |
| c1024 40247782 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c40531 40521652 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| c1004 40732291 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c | DISTILLED | malformed_search_title |
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
| [QP:international.gc.ca] G7 summit Canada | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
