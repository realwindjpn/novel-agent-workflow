# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-08-14T03:42:55
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260814_0331
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 2
- source_card_count: 10
- fresh_news_card_count: 10
- valid_input_count: 10
- skipped_count: 94
- body_fetch_evidence_count: 13
- skip_reason_counts: {"stale_domestic_article": 4, "malformed_search_title": 1, "low_value_policy_or_commentary": 2, "low_value_expo_or_conference": 1, "query_plan_no_body": 54, "no_dyson_tree_match": 7, "summary_not_body_evidence": 11, "missing_body_path": 5, "not_article_page_url": 1, "duplicate_within_run": 6, "duplicate_url": 1, "title_too_short": 1}
- stale_domestic_blocked_count: 4
- p0_missing: True
- disposition_counts: {"OUTLINE_PATCH": 1, "CHAPTER_PREP_ONLY": 2, "ARCHIVE_WITH_REASON": 7}
- conversion_task_count: 2

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260814_0331_final/bridge_runs/cron_20260814_0331/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260814_0331_final/bridge_runs/cron_20260814_0331/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260814_0331_final/bridge_runs/cron_20260814_0331/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260814_8256cd7b56 | 从产业视角看，物理AI的核心价值在于其“改造”物理世界的能力，这不仅能提升生产效率，更可能触发制造模式乃至工业体系重塑。 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| CHAPTER_PREP_ONLY | 20260814_b5413335bb | 我国具备执行陆海两栖航天搜索回收任务能力 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| OUTLINE_PATCH | 20260814_108d415718 | VIDEfc57nFjIDEdkE5VvOz5V260716 | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| CHAPTER_PREP_ONLY | 20260814_3dddbc1fc0 | 科技日报 | 2025-02-11 14:27:01 | 高机动平台与感知/噪声治理可作军事制度细节层。 |
| ARCHIVE_WITH_REASON | 20260814_b73bb132a8 | nasa adds mission to artemis lunar program updates architecture | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260814_f5cfd060f4 | European Gateway experiment will monitor radiation in deep space | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260814_e0b7ce67c9 | capabilities commercial drones | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260814_27daba5234 | department energy announces 71 million research quantum information science | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260814_5d17f6724c | 长十乙首飞成功 我国首次实现运载火箭可控回收 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260814_915f0027ce | 探秘一块锂电池的“重生”之旅 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |

## Missing Cards by Tier

| tier | missing_card_ids |
|---|---|
| P0 | 我国具备执行陆海两栖航天搜索回收任务能力_fcb55685188dc7e5, 科技日报___2025-02-11_14_27_01_030e59eab8b49cac |
| P1 | VIDEfc57nFjIDEdkE5VvOz5V260716_42c1d8d8314bd3de, c1004_40736897_ab11d3ab30bbb779 |

## Skipped

| title | source status | reason |
|---|---|---|
| c1003 27943628 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c1004 40155728 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c1004 40736897 | DISTILLED | malformed_search_title |
| c | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| c 1124855083 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| article | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| ARTIWje0u1f2m25yGB3kONlr241123 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| ARTIynLK1bjZHDmZmSGnA7M8260513 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| [QP:cctv.com] 航天 深空 探测 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:stdaily.com] query_plan | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:stdaily.com] 新材料 先进制造 能源 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:stdaily.com] 人工智能 机器人 量子 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:huanqiu.com] 科技 国防 航天 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:huanqiu.com] 地缘 科技 产业链 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:guancha.cn] 半导体 出口管制 产业链 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:guancha.cn] 航天 军事 科技 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:miit.gov.cn] 新型工业化 先进制造 产业链 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:miit.gov.cn] 人工智能 半导体 算力 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:mod.gov.cn] 科技 国防 无人机 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:mod.gov.cn] 航天 网络 信息化 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:most.gov.cn] query_plan | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:most.gov.cn] 人工智能 量子 新材料 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cnsa.gov.cn] 月球 深空 探测工程 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cnsa.gov.cn] 航天 科技 探测 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cas.cn] 科技突破 重大进展 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cas.cn] 人工智能 量子 新材料 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cas.cn] 航天 深空 机器人 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:iop.cas.cn] 量子 材料 能源 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cac.gov.cn] 人工智能 治理 数据 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cac.gov.cn] 网络安全 数据安全 生成式人工智能 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cmse.gov.cn] 载人航天 空间站 天舟 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cmse.gov.cn] 发射 火箭 运载 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:calt.com] 长征 火箭 运载 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:calt.com] 发射 成功 回收 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:spacechina.com] 长征 火箭 发射 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:spacechina.com] 运载火箭 可重复使用 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| 4 HERITAGE MEETS HARDWARE (USAWC FUTURES SOCOM J7 FINAL PROJECT | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| [QP:noaa.gov] satellite climate ocean | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:pubmed.ncbi.nlm.nih.gov] brain computer interface | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:arxiv.org] quantum computing | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:arxiv.org] AI safety robotics | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:openalex.org] quantum computing AI | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:nature.com] quantum computing AI | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:science.org] quantum AI energy | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:ieee.org] AI chips robotics | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:bis.gov] export control semiconductors | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:semiconductors.org] semiconductor industry chips | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:g7.canada.ca] G7 Summit Kananaskis | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:g7.canada.ca] Group of Seven | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:canada.ca] G7 Summit Kananaskis | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:international.gc.ca] G7 summit Canada | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:whitehouse.gov] G7 Summit Kananaskis | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:whitehouse.gov] Group of Seven | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:consilium.europa.eu] G7 Summit Kananaskis | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:consilium.europa.eu] Group of Seven | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:state.gov] ceasefire Iran Israel | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:state.gov] treaty ceasefire official | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:treasury.gov] sanctions Iran technology | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:treasury.gov] sanctions export controls | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:anthropic.com] Claude model disabled | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:anthropic.com] model availability Claude | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:status.anthropic.com] Claude model availability | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:openai.com] model availability deprecated | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| APOD: 2026 August 13 – Total Solar Eclipse Over Spain | SUMMARY_ONLY | summary_not_body_evidence |
| Cascade Volcanoes Shrouded in Smoke | SUMMARY_ONLY | summary_not_body_evidence |
| NASA Data Helps Commercial Space Plan Living Off Our Moon | SUMMARY_ONLY | summary_not_body_evidence |
| 2026 Total Solar Eclipse in Spain | SUMMARY_ONLY | summary_not_body_evidence |
| MTG-I1 captures eclipse path of totality over Europe | SUMMARY_ONLY | summary_not_body_evidence |
| Musification of the 2026 total solar eclipse | SUMMARY_ONLY | summary_not_body_evidence |
| Lion Nebula roars to life for Webb | SUMMARY_ONLY | summary_not_body_evidence |
| Wildfires, drought and extreme heat, 2026 | SUMMARY_ONLY | summary_not_body_evidence |
| Author Correction: Cretaceous bird from Brazil informs the evolution of the avia | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Can Anthropic’s invisible watermarks curb ‘AI slop’? Researchers remain sceptica | NEED_FETCH_BODY | missing_body_path |
| AI isn’t ready to research itself | NEED_FETCH_BODY | missing_body_path |
| 会“说人话”的AI为何“读不懂人话” | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| 两部门联合启动2026年度计量支撑产业新质生产力发展项目征集工作 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 科技成果赋智企业“深度行”（拉萨站）活动成功举办 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| NASA Data Helps Commercial Space Plan Living Off Our Moon | SUMMARY_ONLY | duplicate_within_run |
| 2026 Total Solar Eclipse in Spain | SUMMARY_ONLY | duplicate_within_run |
