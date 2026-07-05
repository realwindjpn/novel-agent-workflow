# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-02T01:08:14
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260702_0043
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 10
- fresh_news_card_count: 10
- valid_input_count: 10
- skipped_count: 99
- body_fetch_evidence_count: 13
- skip_reason_counts: {"body_clean_too_short": 1, "not_article_page_url": 1, "duplicate_url": 3, "duplicate_within_run": 3, "http_403|jina_timeout": 1, "missing_body_path": 25, "stale_domestic_article": 1, "low_value_policy_theory_source": 1, "low_value_expo_or_conference": 1, "query_plan_no_body": 62}
- stale_domestic_blocked_count: 1
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 1, "CHAPTER_PREP_ONLY": 1, "ARCHIVE_WITH_REASON": 8}
- conversion_task_count: 1

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260702_0043_final/bridge_runs/cron_20260702_0043/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260702_0043_final/bridge_runs/cron_20260702_0043/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260702_0043_final/bridge_runs/cron_20260702_0043/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260702_32d4abbdd0 | NASA Seeks Volunteers for New Yearlong Simulated Moon, Mars Mission | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260702_64be161c54 | LINK Spacecraft Set for Mission to Boost NASA’s Swift Observatory | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260702_c581e051ad | NASA’s TESS Mission Finds Planetary System in New Way | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260702_e3cc0413b0 | The space under | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| CHAPTER_PREP_ONLY | 20260702_9b15b8b314 | 从科创中心看未来产业 科技成果实现从1到10的突破 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260702_bf6e20dd8d | 科技部副部长林新访问马来西亚、老挝并出席中马政府间科技创新合作联委会、中老政府间科技合作联委会和中国—东盟科技创新合作联委会会议 | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260702_3a0fcb7ad8 | How Can AI Find My Model? A Model-Finding Experimental Study Considering Data Fo | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260702_390423c30c | chip supply chain investments | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| OUTLINE_PATCH | 20260702_e3b73b4e05 | index | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| ARCHIVE_WITH_REASON | 20260702_7a7d718505 | 高质量数据集建设激活人工智能发展新动能 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |

## Skipped

| title | source status | reason |
|---|---|---|
| Thousands of planets are hidden in this photo | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| 央地共建粤港澳大湾区国际科技创新中心工作推进会在广州召开 | SKIP_DUPLICATE | DUPLICATE_URL |
| LINK Spacecraft Set for Mission to Boost NASA’s Swift Observatory | DISTILLED | duplicate_within_run |
| NASA’s TESS Mission Finds Planetary System in New Way | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| The space under | BODY_FETCH_FAIL | duplicate_within_run |
| Dartmouth’s AI summer and what came next | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| g7 leaders statement ai prosperity | NEED_FETCH_BODY | missing_body_path |
| g7 energy and environment ministers meeting energy and artificial intelligence | NEED_FETCH_BODY | missing_body_path |
| g7 leaders statement on ai for prosperity | NEED_FETCH_BODY | missing_body_path |
| chairs summary | NEED_FETCH_BODY | missing_body_path |
| g7 leaders summit | NEED_FETCH_BODY | missing_body_path |
| priorities | NEED_FETCH_BODY | missing_body_path |
| g7 call to action on enhancing energy security | NEED_FETCH_BODY | missing_body_path |
| g7 energy and ai work plan | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | NEED_FETCH_BODY | missing_body_path |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 250617 ai | NEED_FETCH_BODY | missing_body_path |
| 1022261090060174 | NEED_FETCH_BODY | missing_body_path |
| 122137343534723345 | NEED_FETCH_BODY | missing_body_path |
| 51st G7 summit | NEED_FETCH_BODY | missing_body_path |
| 122137413596723345 | NEED_FETCH_BODY | missing_body_path |
| full text iran national security council statement ceasefire | NEED_FETCH_BODY | missing_body_path |
| us iran negotiations whats the latest | NEED_FETCH_BODY | missing_body_path |
| us iran talks secure peace deal restart shipping 6224371 | NEED_FETCH_BODY | missing_body_path |
| iran trump ceasefire strait hormuz israel war hezbollah continues | NEED_FETCH_BODY | missing_body_path |
| iran fires missiles israel ceasefire strains | NEED_FETCH_BODY | missing_body_path |
| trump brokered ceasefire agreement contact with israel iran white house official | NEED_FETCH_BODY | missing_body_path |
| irans supreme national security council says it has accepted two week ceasefire  | NEED_FETCH_BODY | missing_body_path |
| model deprecations | NEED_FETCH_BODY | missing_body_path |
| anthropic claude model deprecations on june 15 2026 | NEED_FETCH_BODY | missing_body_path |
| claude sonnet 4 opus 4 deprecation migration guide | NEED_FETCH_BODY | missing_body_path |
| us blocks foreign access anthropics most advanced ai models axios reports 2026 0 | NEED_FETCH_BODY | missing_body_path |
| c1024 40247782 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c40531 40521652 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| c1004 40732291 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
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
