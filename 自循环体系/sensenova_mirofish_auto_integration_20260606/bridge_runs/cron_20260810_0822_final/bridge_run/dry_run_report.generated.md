# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-08-10T08:34:44
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260810_0822
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 2
- source_card_count: 11
- fresh_news_card_count: 11
- valid_input_count: 11
- skipped_count: 79
- body_fetch_evidence_count: 15
- skip_reason_counts: {"stale_domestic_article": 2, "query_plan_no_body": 55, "malformed_search_title": 2, "low_value_policy_or_commentary": 1, "short_navigation_body": 1, "http_403|jina_timeout": 1, "no_dyson_tree_match": 4, "summary_not_body_evidence": 4, "missing_body_path": 2, "not_article_page_url": 1, "duplicate_within_run": 5, "duplicate_url": 1}
- stale_domestic_blocked_count: 2
- p0_missing: True
- disposition_counts: {"OUTLINE_PATCH": 2, "CHAPTER_PREP_ONLY": 5, "ARCHIVE_WITH_REASON": 4}
- conversion_task_count: 5

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260810_0822_final/bridge_runs/cron_20260810_0822/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260810_0822_final/bridge_runs/cron_20260810_0822/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260810_0822_final/bridge_runs/cron_20260810_0822/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| CHAPTER_PREP_ONLY | 20260810_79c857179a | 产业创新红利加速兑现 科创板“预喜”公告揭示成长动能 | 生物伦理/人才争夺/科研治理素材，可作后续章节准备。 |
| CHAPTER_PREP_ONLY | 20260810_92a5f4ff37 | 题：“低空经济”发展一年间 | 高机动平台与感知/噪声治理可作军事制度细节层。 |
| CHAPTER_PREP_ONLY | 20260810_b5413335bb | 我国具备执行陆海两栖航天搜索回收任务能力 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260810_f5cfd060f4 | European Gateway experiment will monitor radiation in deep space | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260810_e0b7ce67c9 | capabilities commercial drones | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260810_27daba5234 | department energy announces 71 million research quantum information science | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260810_5f84d42890 | satellites | 气象/地球观测素材，可作章节准备包中的遥感盲区/侦察代价参考；非地月深空链。 |
| OUTLINE_PATCH | 20260810_3a4a119dfd | Abstract. | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| OUTLINE_PATCH | 20260810_509890f6fe | Abstract | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| CHAPTER_PREP_ONLY | 20260810_915f0027ce | 探秘一块锂电池的“重生”之旅 | 政策框架/概念文只作制度语境准备，不直接升为OUTLINE_PATCH。 |
| ARCHIVE_WITH_REASON | 20260810_5d17f6724c | 长十乙首飞成功 我国首次实现运载火箭可控回收 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |

## Missing Cards by Tier

| tier | missing_card_ids |
|---|---|
| P0 | 产业创新红利加速兑现_科创板_预喜_公告揭示成长动能_b7c1648e0eb0a031, 我国具备执行陆海两栖航天搜索回收任务能力_fcb55685188dc7e5, 题__低空经济_发展一年间_8add9e2ccc4db32f |
| P1 | Abstract_41a1ad6b7c09692a, Abstract_8949cbea440085e3, artemis_8d279be15a4247ac, c1004_40736897_ab11d3ab30bbb779, satellites_d5eeee1e403284bf |

## Skipped

| title | source status | reason |
|---|---|---|
| c459166 40299406 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| [QP:people.com.cn] 先进制造 产业升级 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| c1004 40736897 | DISTILLED | malformed_search_title |
| c | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| c 128765346 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| [QP:cctv.com] 先进制造 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cctv.com] query_plan | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cctv.com] 人工智能 半导体 算力 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
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
| artemis | DISTILLED | short_navigation_body |
| UNLEASHING U.S. MILITARY DRONE DOMINANCE | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| 41221369 | DISTILLED | malformed_search_title |
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
| 2026 IGARSS Hyperwall Schedule | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| NASA’s Lunar Development and Test Facility Prepares Artemis Hardware for Moon | SUMMARY_ONLY | summary_not_body_evidence |
| Join us live and enjoy the total solar eclipse! | SUMMARY_ONLY | summary_not_body_evidence |
| IRIS² reinforced and accelerated as implementation advances | SUMMARY_ONLY | summary_not_body_evidence |
| Operational Tropical Cyclone Forecasting with AI | NEED_FETCH_BODY | missing_body_path |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| NASA’s Lunar Development and Test Facility Prepares Artemis Hardware for Moon | SUMMARY_ONLY | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Join us live and enjoy the total solar eclipse! | SUMMARY_ONLY | duplicate_within_run |
| IRIS² reinforced and accelerated as implementation advances | SUMMARY_ONLY | duplicate_within_run |
| Operational Tropical Cyclone Forecasting with AI | NEED_FETCH_BODY | duplicate_within_run |
| Announcements Jul 9, 2026 Inviting hard questions We’re asking the public for th | SUMMARY_ONLY | summary_not_body_evidence |
| sanctions dual use goods en | NEED_FETCH_BODY | missing_body_path |
| emerging resilience in the semiconductor supply chain | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| chip supply chain investments | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 探秘一块锂电池的“重生”之旅 | DISTILLED | duplicate_within_run |
