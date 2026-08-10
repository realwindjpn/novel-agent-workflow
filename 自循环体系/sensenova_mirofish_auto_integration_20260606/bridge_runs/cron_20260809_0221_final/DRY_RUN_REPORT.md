# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-08-09T02:36:24
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260809_0221
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 2
- source_card_count: 5
- fresh_news_card_count: 5
- valid_input_count: 5
- skipped_count: 90
- body_fetch_evidence_count: 9
- skip_reason_counts: {"stale_domestic_article": 5, "no_dyson_tree_match": 13, "low_value_expo_or_conference": 2, "query_plan_no_body": 58, "summary_not_body_evidence": 2, "not_article_page_url": 1, "duplicate_within_run": 4, "duplicate_url": 2, "stale_news": 1, "missing_body_path": 2}
- stale_domestic_blocked_count: 5
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 3, "ARCHIVE_WITH_REASON": 2}
- conversion_task_count: 3

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260809_0221_final/bridge_runs/cron_20260809_0221/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260809_0221_final/bridge_runs/cron_20260809_0221/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260809_0221_final/bridge_runs/cron_20260809_0221/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| CHAPTER_PREP_ONLY | 20260809_d75028888a | 当你坐着C919大飞机去旅行，是不是特别有自豪感？这个“大飞机梦”的实现，可是咱们多年关键核心技术攻关啃下来的硬骨头。 | 高机动平台与感知/噪声治理可作军事制度细节层。 |
| CHAPTER_PREP_ONLY | 20260809_d4f24aee71 | 大连理工大学自研新材料将国产轴承使用寿命提高6倍 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| CHAPTER_PREP_ONLY | 20260809_d7f089ec0f | 央视新闻 | 2026年02月20日 17:48:08 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260809_bf860c8efb | 2026 IGARSS Hyperwall Schedule | 展会/航展/博览会文，低技术突破增益，归档。 |
| ARCHIVE_WITH_REASON | 20260809_b7431eeba0 | NASA’s Lunar Development and Test Facility Prepares Artemis Hardware for Moon | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |

## Missing Cards by Tier

| tier | missing_card_ids |
|---|---|
| P1 | 大连理工大学自研新材料将国产轴承使用寿命提高6倍_e18513cf4f3c6d02, 央视新闻___2026年02月20日_17_48_08_cf419ca7758db067, 当你坐着C919大飞机去旅行_是不是特别有自豪感_这个_大飞机梦_的实现_可是咱们多年关键_97a6687180e515d4 |

## Skipped

| title | source status | reason |
|---|---|---|
| c1003 40079580 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c461139 40620596 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| c404214 40769205 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c 1124855083 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| 竞逐物理AI时代新机遇 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| article | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c 1116280885 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| ARTIiLGt5s118iViaUCrbrOu240126 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| 数智跨越 中国人工智能产业发展的“加速度” | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
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
| Join us live and enjoy the total solar eclipse! | SUMMARY_ONLY | summary_not_body_evidence |
| IRIS² reinforced and accelerated as implementation advances | SUMMARY_ONLY | summary_not_body_evidence |
| Operational Tropical Cyclone Forecasting with AI | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| NASA’s Lunar Development and Test Facility Prepares Artemis Hardware for Moon | SUMMARY_ONLY | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Join us live and enjoy the total solar eclipse! | SUMMARY_ONLY | duplicate_within_run |
| IRIS² reinforced and accelerated as implementation advances | SUMMARY_ONLY | duplicate_within_run |
| Operational Tropical Cyclone Forecasting with AI | ARCHIVE_WITH_REASON | duplicate_within_run |
| Announcements Jul 9, 2026 Inviting hard questions We’re asking the public for th | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| sanctions dual use goods en | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| historic explosion long sought fusion breakthrough | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
