# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-08-15T06:44:35
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260815_0633
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 2
- source_card_count: 7
- fresh_news_card_count: 7
- valid_input_count: 7
- skipped_count: 100
- body_fetch_evidence_count: 13
- skip_reason_counts: {"stale_domestic_article": 4, "no_dyson_tree_match": 11, "malformed_search_title": 2, "low_value_policy_or_commentary": 1, "low_value_expo_or_conference": 1, "query_plan_no_body": 54, "http_403|jina_timeout": 1, "summary_not_body_evidence": 12, "missing_body_path": 5, "not_article_page_url": 1, "duplicate_within_run": 6, "duplicate_url": 1, "title_too_short": 1}
- stale_domestic_blocked_count: 4
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 1, "CHAPTER_PREP_ONLY": 1, "ARCHIVE_WITH_REASON": 5}
- conversion_task_count: 1

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260815_0633_final/bridge_runs/cron_20260815_0633/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260815_0633_final/bridge_runs/cron_20260815_0633/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260815_0633_final/bridge_runs/cron_20260815_0633/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| OUTLINE_PATCH | 20260815_1521900046 | 习近平在2026世界人工智能大会暨人工智能全球治理高级别会议开幕式上的主旨讲话（全文） | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| CHAPTER_PREP_ONLY | 20260815_d75028888a | 当你坐着C919大飞机去旅行，是不是特别有自豪感？这个“大飞机梦”的实现，可是咱们多年关键核心技术攻关啃下来的硬骨头。 | 生物伦理/人才争夺/科研治理素材，可作后续章节准备。 |
| ARCHIVE_WITH_REASON | 20260815_b73bb132a8 | nasa adds mission to artemis lunar program updates architecture | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260815_610e925bee | quantum information science | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260815_3eef90b708 | satellite ocean heat content suite | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260815_5d17f6724c | 长十乙首飞成功 我国首次实现运载火箭可控回收 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260815_915f0027ce | 探秘一块锂电池的“重生”之旅 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |

## Missing Cards by Tier

| tier | missing_card_ids |
|---|---|
| P1 | 59374_overview_1e34214f1442f5c5, c1004_40736897_ab11d3ab30bbb779, satellite_ocean_heat_content_suite_dc7ca9c1b7e4cdcc, 习近平在2026世界人工智能大会暨人工智能全球治理高级别会议开幕式上的主旨讲话_全文_19e1eeaf78ab7200, 当你坐着C919大飞机去旅行_是不是特别有自豪感_这个_大飞机梦_的实现_可是咱们多年关键_97a6687180e515d4 |

## Skipped

| title | source status | reason |
|---|---|---|
| c459166 40299406 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c461139 40620596 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| c1004 40736897 | DISTILLED | malformed_search_title |
| c | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| article | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| article | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c 1127368611 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| ARTIV5uJYUc1Twkp5zzx33ht240314 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| 扫一扫 分享到微信 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| [QP:cctv.com] 新材料 能源 动力装备 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
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
| 59374 overview | DISTILLED | malformed_search_title |
| uh 60mx black hawk army | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| UNLEASHING U.S. MILITARY DRONE DOMINANCE | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
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
| NASA Competition Invites Students to Help Imagine a Future Enabled by Lunar Tech | SUMMARY_ONLY | summary_not_body_evidence |
| NASA Announces MAX POWER: America&#8217;s Newest Aerospace Expo, Airshow | SUMMARY_ONLY | summary_not_body_evidence |
| Volunteer Develops Machine-Learning Tool to Identify Rare Clouds | SUMMARY_ONLY | summary_not_body_evidence |
| NASA’s COFFIES Uses AI to Predict Storm-Causing Active Regions on Sun | SUMMARY_ONLY | summary_not_body_evidence |
| Total Solar Eclipse in Sunflower Field | SUMMARY_ONLY | summary_not_body_evidence |
| A look back at the 2026 total solar eclipse | SUMMARY_ONLY | summary_not_body_evidence |
| MTG-I1 captures eclipse path of totality over Europe | SUMMARY_ONLY | summary_not_body_evidence |
| Musification of the 2026 total solar eclipse | SUMMARY_ONLY | summary_not_body_evidence |
| Briefing Chat: Anthropic rolls out new AI watermark — will it make a difference? | NEED_FETCH_BODY | missing_body_path |
| Einstein the musician, AI prophets and more: Books in brief | NEED_FETCH_BODY | missing_body_path |
| Undocumented migration does not raise crime rates, huge study finds | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 第二届世界人形机器人运动会参赛机器人数量翻两番 | SUMMARY_ONLY | summary_not_body_evidence |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| 植保作业、大田播种、畜禽巡检、果蔬分拣……“晋字号”机器人在田间大显身手 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
