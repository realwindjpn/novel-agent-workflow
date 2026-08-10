# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-08-07T08:35:32
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260807_0819
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 7
- fresh_news_card_count: 7
- valid_input_count: 7
- skipped_count: 92
- body_fetch_evidence_count: 10
- skip_reason_counts: {"stale_domestic_article": 3, "no_dyson_tree_match": 14, "low_value_expo_or_conference": 2, "low_value_policy_or_commentary": 1, "query_plan_no_body": 58, "summary_not_body_evidence": 3, "not_article_page_url": 1, "duplicate_within_run": 6, "duplicate_url": 2, "title_too_short": 1, "missing_body_path": 1}
- stale_domestic_blocked_count: 3
- p0_missing: True
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 7, "ARCHIVE_WITH_REASON": 0}
- conversion_task_count: 7

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260807_0819_final/bridge_runs/cron_20260807_0819/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260807_0819_final/bridge_runs/cron_20260807_0819/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260807_0819_final/bridge_runs/cron_20260807_0819/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| CHAPTER_PREP_ONLY | 20260807_90f8a5d48b | 2月9日上午，习近平总书记来到位于北京亦庄的国家信创园，了解信息技术应用创新和北京加快建设国际科技创新中心情况。 | 政策框架/概念文只作制度语境准备，不直接升为OUTLINE_PATCH。 |
| CHAPTER_PREP_ONLY | 20260807_92a5f4ff37 | 题：“低空经济”发展一年间 | 高机动平台与感知/噪声治理可作军事制度细节层。 |
| CHAPTER_PREP_ONLY | 20260807_b5413335bb | 我国具备执行陆海两栖航天搜索回收任务能力 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| CHAPTER_PREP_ONLY | 20260807_d4f24aee71 | 大连理工大学自研新材料将国产轴承使用寿命提高6倍 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| CHAPTER_PREP_ONLY | 20260807_5e462f58a2 | 央视网消息：**自主创新从来都是中国航天的成功“密码”，“航天强国”一词更是出现在“十五五”的规划建议中。2025年，中国航天不断突破，国家战略与市场活力深度交 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| CHAPTER_PREP_ONLY | 20260807_f1cb5420dc | NASA’s SkyFall Helicopters at Work (Artist’s Concept) | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| CHAPTER_PREP_ONLY | 20260807_a401dbbdf2 | I Am Artemis: Tom Percy | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |

## Missing Cards by Tier

| tier | missing_card_ids |
|---|---|
| P0 | 央视网消息___自主创新从来都是中国航天的成功_密码___航天强国_一词更是出现在_十_ea48a587cb62f3ba, 我国具备执行陆海两栖航天搜索回收任务能力_fcb55685188dc7e5, 题__低空经济_发展一年间_8add9e2ccc4db32f |
| P1 | 2月9日上午_习近平总书记来到位于北京亦庄的国家信创园_了解信息技术应用创新和北京加快建设_6036fc2a4b39a27a, 大连理工大学自研新材料将国产轴承使用寿命提高6倍_e18513cf4f3c6d02 |

## Skipped

| title | source status | reason |
|---|---|---|
| c1003 40079580 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c461139 40620596 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| c404214 40769205 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| 上海人工智能实验室发布“珠穆朗玛计划”——志在打造科学智能“全国中枢” | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| ARTIiLGt5s118iViaUCrbrOu240126 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| ARTIynLK1bjZHDmZmSGnA7M8260513 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| VIDEDmpUPOMkLqorhgFs4Lm4260720 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
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
| [QP:nasa.gov] Artemis lunar program | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:esa.int] lunar exploration deep | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:darpa.mil] autonomous systems drone | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:defense.gov] drone swarm military | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
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
| Educators &#038; Teens Get Hands-On With TEMPO Data to Help Investigate Local Ai | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Taking Flight to Prepare for Space | SUMMARY_ONLY | summary_not_body_evidence |
| ExoMars stretches out its legs | SUMMARY_ONLY | summary_not_body_evidence |
| Your chance to run software in deep space on ESA's asteroid mission | SUMMARY_ONLY | summary_not_body_evidence |
| Levitating sensor for magnetic fields could detect ultrafaint brain activity | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| AI agents are checking the scientific literature — and spotting decades-old erro | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| NASA’s SkyFall Helicopters at Work (Artist’s Concept) | SUMMARY_ONLY | duplicate_within_run |
| I Am Artemis: Tom Percy | SUMMARY_ONLY | duplicate_within_run |
| Taking Flight to Prepare for Space | SUMMARY_ONLY | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| ExoMars stretches out its legs | SUMMARY_ONLY | duplicate_within_run |
| Your chance to run software in deep space on ESA's asteroid mission | SUMMARY_ONLY | duplicate_within_run |
| Operational Tropical Cyclone Forecasting with AI | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
