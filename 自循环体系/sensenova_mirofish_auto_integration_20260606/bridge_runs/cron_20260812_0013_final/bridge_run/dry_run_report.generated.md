# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-08-12T00:28:39
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260812_0013
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 2
- source_card_count: 9
- fresh_news_card_count: 9
- valid_input_count: 9
- skipped_count: 89
- body_fetch_evidence_count: 12
- skip_reason_counts: {"query_plan_no_body": 55, "low_value_expo_or_conference": 2, "low_value_policy_or_commentary": 2, "stale_domestic_article": 3, "short_navigation_body": 1, "no_dyson_tree_match": 7, "summary_not_body_evidence": 8, "missing_body_path": 4, "not_article_page_url": 1, "duplicate_within_run": 5, "duplicate_url": 1}
- stale_domestic_blocked_count: 3
- p0_missing: True
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 2, "ARCHIVE_WITH_REASON": 7}
- conversion_task_count: 2

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260812_0013_final/bridge_runs/cron_20260812_0013/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260812_0013_final/bridge_runs/cron_20260812_0013/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260812_0013_final/bridge_runs/cron_20260812_0013/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260812_47ed4d5272 | 竞逐物理AI时代新机遇 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260812_92a5f4ff37 | 题：“低空经济”发展一年间 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| CHAPTER_PREP_ONLY | 20260812_108d415718 | VIDEfc57nFjIDEdkE5VvOz5V260716 | 政策框架/概念文只作制度语境准备，不直接升为OUTLINE_PATCH。 |
| ARCHIVE_WITH_REASON | 20260812_8de4971d50 | 央视新闻 | 2025年12月01日 06:21:32 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| CHAPTER_PREP_ONLY | 20260812_5e462f58a2 | 央视网消息：**自主创新从来都是中国航天的成功“密码”，“航天强国”一词更是出现在“十五五”的规划建议中。2025年，中国航天不断突破，国家战略与市场活力深度交 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260812_f5cfd060f4 | European Gateway experiment will monitor radiation in deep space | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260812_e0b7ce67c9 | capabilities commercial drones | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260812_5d17f6724c | 长十乙首飞成功 我国首次实现运载火箭可控回收 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260812_915f0027ce | 探秘一块锂电池的“重生”之旅 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |

## Missing Cards by Tier

| tier | missing_card_ids |
|---|---|
| P0 | VIDEfc57nFjIDEdkE5VvOz5V260716_42c1d8d8314bd3de, 央视网消息___自主创新从来都是中国航天的成功_密码___航天强国_一词更是出现在_十_ea48a587cb62f3ba |

## Skipped

| title | source status | reason |
|---|---|---|
| [QP:people.com.cn] 科技 创新 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| c1004 40650510 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c1004 40724419 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| c 128765346 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c 1127368611 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| ARTIiLGt5s118iViaUCrbrOu240126 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| ARTIynLK1bjZHDmZmSGnA7M8260513 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
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
| nasa adds mission to artemis lunar program updates architecture | DISTILLED | short_navigation_body |
| 4 HERITAGE MEETS HARDWARE (USAWC FUTURES SOCOM J7 FINAL PROJECT | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| [QP:energy.gov] quantum energy research | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
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
| NASA Telescopes Create Colorful ‘Craft’ From Nearby Nebula | SUMMARY_ONLY | summary_not_body_evidence |
| Building the Moon Base: NASA Stories at the Ion | SUMMARY_ONLY | summary_not_body_evidence |
| NASA Shares Station Research Today Supporting Moon, Mars Tomorrow | SUMMARY_ONLY | summary_not_body_evidence |
| APOD: 2026 August 11 – Six Moons of Saturn | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| A total solar eclipse is coming to Europe | SUMMARY_ONLY | summary_not_body_evidence |
| Lion Nebula roars to life for Webb | SUMMARY_ONLY | summary_not_body_evidence |
| AI tools speed up analysis, but scientific truths must be grounded in reality | NEED_FETCH_BODY | missing_body_path |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| 两部门联合启动2026年度计量支撑产业新质生产力发展项目征集工作 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 科技成果赋智企业“深度行”（拉萨站）活动成功举办 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Building the Moon Base: NASA Stories at the Ion | SUMMARY_ONLY | duplicate_within_run |
| NASA Shares Station Research Today Supporting Moon, Mars Tomorrow | SUMMARY_ONLY | duplicate_within_run |
| APOD: 2026 August 11 – Six Moons of Saturn | ARCHIVE_WITH_REASON | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| A total solar eclipse is coming to Europe | SUMMARY_ONLY | duplicate_within_run |
| AI tools speed up analysis, but scientific truths must be grounded in reality | NEED_FETCH_BODY | duplicate_within_run |
