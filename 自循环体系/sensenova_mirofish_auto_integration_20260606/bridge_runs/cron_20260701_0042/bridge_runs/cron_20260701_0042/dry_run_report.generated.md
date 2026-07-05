# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-01T02:48:16
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260701_0042
- dry_run: True
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 12
- fresh_news_card_count: 12
- valid_input_count: 12
- skipped_count: 93
- body_fetch_evidence_count: 14
- skip_reason_counts: {"http_403|jina_timeout": 2, "not_article_page_url": 1, "duplicate_url": 2, "duplicate_within_run": 3, "summary_not_body_evidence": 1, "missing_body_path": 19, "low_value_policy_or_commentary": 1, "low_value_policy_theory_source": 1, "query_plan_no_body": 63}
- stale_domestic_blocked_count: 0
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 1, "ARCHIVE_WITH_REASON": 11}
- conversion_task_count: 1

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260701_0042/bridge_runs/cron_20260701_0042/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260701_0042/bridge_runs/cron_20260701_0042/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260701_0042/bridge_runs/cron_20260701_0042/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260701_83fc945dbb | Starry Chandelier Cluster | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260701_f41f104d04 | NASA, SBA Announce New Initiative to Scale American Space Economy | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260701_258e3198e8 | NASA Astronaut Chris Williams Preps for Spacewalk | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260701_81c6620920 | Time to say goodbye to Sentinel-1A | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260701_d977200ade | 关于2025年人工智能应用典型案例入选名单的公示 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260701_0d2d0a4c9b | 工业和信息化部办公厅关于公布2025年度工业和信息化质量提升与品牌建设典型案例名单的通知 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260701_bf6e20dd8d | 科技部副部长林新访问马来西亚、老挝并出席中马政府间科技创新合作联委会、中老政府间科技合作联委会和中国—东盟科技创新合作联委会会议 | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260701_4aa720227b | εpsilon | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260701_e09a710142 | AI-Model Network: Concept, Current State and Future | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260701_2335733604 | DysLexLens: A Low-Resource LLM Framework for Analysing Dyslexic Learners Insight | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260701_497225b562 | Statement on the US government directive to suspend access to Fable 5 and Mythos | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260701_7a7d718505 | 高质量数据集建设激活人工智能发展新动能 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |

## Skipped

| title | source status | reason |
|---|---|---|
| This Month at ESA: June 2026 | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| 央地共建粤港澳大湾区国际科技创新中心工作推进会在广州召开 | SKIP_DUPLICATE | DUPLICATE_URL |
| NASA, SBA Announce New Initiative to Scale American Space Economy | DISTILLED | duplicate_within_run |
| Time to say goodbye to Sentinel-1A | DISTILLED | duplicate_within_run |
| This Month at ESA: June 2026 | BODY_FETCH_FAIL | duplicate_within_run |
| Dartmouth’s AI summer and what came next | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| Product Jun 23, 2026 Introducing Claude Tag Claude Tag is a new way for teams to | SUMMARY_ONLY | summary_not_body_evidence |
| strengthening the global semiconductor supply chain in an uncertain era | NEED_FETCH_BODY | missing_body_path |
| g7 energy and environment ministers meeting energy and artificial intelligence | NEED_FETCH_BODY | missing_body_path |
| index | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | NEED_FETCH_BODY | missing_body_path |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 1022261090060174 | NEED_FETCH_BODY | missing_body_path |
| inside g7 environment energy | NEED_FETCH_BODY | missing_body_path |
| 250617 ai | NEED_FETCH_BODY | missing_body_path |
| 1146986817331914 | NEED_FETCH_BODY | missing_body_path |
| 122137343534723345 | NEED_FETCH_BODY | missing_body_path |
| 51st G7 summit | NEED_FETCH_BODY | missing_body_path |
| 122137413596723345 | NEED_FETCH_BODY | missing_body_path |
| iran trump ceasefire strait hormuz israel war hezbollah continues | NEED_FETCH_BODY | missing_body_path |
| full text iran national security council statement ceasefire | NEED_FETCH_BODY | missing_body_path |
| white house opted against televised address about iran ceasefire us officials 20 | NEED_FETCH_BODY | missing_body_path |
| israel says iran violating ceasefire trump announced will respond with force | NEED_FETCH_BODY | missing_body_path |
| model deprecations | NEED_FETCH_BODY | missing_body_path |
| anthropic claude model deprecations on june 15 2026 | NEED_FETCH_BODY | missing_body_path |
| claude sonnet 4 opus 4 deprecation migration guide | NEED_FETCH_BODY | missing_body_path |
| anthropic disable advanced ai models us government order | NEED_FETCH_BODY | missing_body_path |
| c461530 40705990 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| c40531 40710030 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| [QP:people.com.cn] 人工智能 半导体 算力 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
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
| [QP:canada.ca] G7 Summit Kananaskis | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
