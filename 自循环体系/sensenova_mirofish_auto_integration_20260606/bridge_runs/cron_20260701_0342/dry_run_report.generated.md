# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-01T03:58:33
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260701_0342
- dry_run: True
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 7
- fresh_news_card_count: 7
- valid_input_count: 7
- skipped_count: 104
- body_fetch_evidence_count: 12
- skip_reason_counts: {"duplicate_url": 4, "body_clean_too_short": 1, "body_too_short_link_only": 1, "not_article_page_url": 1, "duplicate_within_run": 5, "summary_not_body_evidence": 5, "missing_body_path": 21, "already_in_previous_bridge_run": 1, "stale_domestic_article": 1, "low_value_policy_theory_source": 1, "low_value_expo_or_conference": 1, "query_plan_no_body": 62}
- stale_domestic_blocked_count: 1
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 1, "ARCHIVE_WITH_REASON": 6}
- conversion_task_count: 1

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260701_0342/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260701_0342/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260701_0342/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260701_ef42fb623e | La NASA adjudica nuevas misiones científicas para Base Lunar y adelanta nuevas o | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260701_3aaa313f9a | NextSTEP-3 B: Moon Base Demonstrations | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260701_f72d191efe | NASA Awards More Moon Base Science, Previews New Opportunities | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260701_83fc945dbb | Starry Chandelier Cluster | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260701_d977200ade | 关于2025年人工智能应用典型案例入选名单的公示 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260701_0d2d0a4c9b | 工业和信息化部办公厅关于公布2025年度工业和信息化质量提升与品牌建设典型案例名单的通知 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260701_bf6e20dd8d | 科技部副部长林新访问马来西亚、老挝并出席中马政府间科技创新合作联委会、中老政府间科技合作联委会和中国—东盟科技创新合作联委会会议 | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |

## Skipped

| title | source status | reason |
|---|---|---|
| Time to say goodbye to Sentinel-1A | SKIP_DUPLICATE | DUPLICATE_URL |
| This Month at ESA: June 2026 | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| 一组数据带你看懂“十五五”能源强国新图景 | BODY_FETCH_FAIL | BODY_TOO_SHORT_LINK_ONLY |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| 央地共建粤港澳大湾区国际科技创新中心工作推进会在广州召开 | SKIP_DUPLICATE | DUPLICATE_URL |
| La NASA adjudica nuevas misiones científicas para Base Lunar y adelanta nuevas o | DISTILLED | duplicate_within_run |
| NextSTEP-3 B: Moon Base Demonstrations | DISTILLED | duplicate_within_run |
| NASA Awards More Moon Base Science, Previews New Opportunities | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Time to say goodbye to Sentinel-1A | SKIP_DUPLICATE | duplicate_within_run |
| This Month at ESA: June 2026 | SUMMARY_ONLY | duplicate_within_run |
| Dartmouth’s AI summer and what came next | SUMMARY_ONLY | summary_not_body_evidence |
| AI-Model Network: Concept, Current State and Future | SUMMARY_ONLY | summary_not_body_evidence |
| DysLexLens: A Low-Resource LLM Framework for Analysing Dyslexic Learners Insight | SUMMARY_ONLY | summary_not_body_evidence |
| Statement on the US government directive to suspend access to Fable 5 and Mythos | SUMMARY_ONLY | summary_not_body_evidence |
| Product Jun 30, 2026 Introducing Claude Sonnet 5 Sonnet 5 delivers frontier perf | SUMMARY_ONLY | summary_not_body_evidence |
| powering ai the semiconductor ecosystem at the foundation of data centers | NEED_FETCH_BODY | missing_body_path |
| strengthening the global semiconductor supply chain in an uncertain era | NEED_FETCH_BODY | missing_body_path |
| g7 leaders statement ai prosperity | NEED_FETCH_BODY | missing_body_path |
| g7 energy and environment ministers meeting energy and artificial intelligence | NEED_FETCH_BODY | missing_body_path |
| index | NEED_FETCH_BODY | missing_body_path |
| canada to host g7 industry digital and technology ministers meeting in montreal | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | NEED_FETCH_BODY | missing_body_path |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 高质量数据集建设激活人工智能发展新动能 | DISTILLED | already_in_previous_bridge_run |
| 250617 ai | NEED_FETCH_BODY | missing_body_path |
| 1022261090060174 | NEED_FETCH_BODY | missing_body_path |
| 122137343534723345 | NEED_FETCH_BODY | missing_body_path |
| 661295 | NEED_FETCH_BODY | missing_body_path |
| 122137413596723345 | NEED_FETCH_BODY | missing_body_path |
| iran war us trump strikes ceasefire lebanon israel | NEED_FETCH_BODY | missing_body_path |
| iran us ceasefire hezbollah israel 12 june 2026 7085e386e1c40ee6cfe634210970143f | NEED_FETCH_BODY | missing_body_path |
| israel says iran violating ceasefire trump announced will respond with force | NEED_FETCH_BODY | missing_body_path |
| watch live white house holds briefing as trump agrees to two week ceasefire in i | NEED_FETCH_BODY | missing_body_path |
| trump us iran war ceasefire strait hormuz israel live updates 04 08 2026 | NEED_FETCH_BODY | missing_body_path |
| Twelve Day War ceasefire | NEED_FETCH_BODY | missing_body_path |
| model deprecations | NEED_FETCH_BODY | missing_body_path |
| anthropic claude model deprecations on june 15 2026 | NEED_FETCH_BODY | missing_body_path |
| us blocks foreign access anthropics most advanced ai models axios reports 2026 0 | NEED_FETCH_BODY | missing_body_path |
| c1024 40247782 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c40531 40625089 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
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
