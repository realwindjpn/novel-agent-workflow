# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-11T02:56:26
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260711_0234
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 8
- fresh_news_card_count: 8
- valid_input_count: 8
- skipped_count: 110
- body_fetch_evidence_count: 12
- skip_reason_counts: {"body_clean_too_short": 1, "not_article_page_url": 1, "duplicate_within_run": 5, "duplicate_url": 2, "summary_not_body_evidence": 5, "missing_body_path": 24, "low_value_expo_or_conference": 1, "stale_domestic_article": 1, "low_value_policy_theory_source": 1, "malformed_search_title": 2, "query_plan_no_body": 67}
- stale_domestic_blocked_count: 1
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 2, "ARCHIVE_WITH_REASON": 6}
- conversion_task_count: 2

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260711_0234_final/bridge_runs/cron_20260711_0234/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260711_0234_final/bridge_runs/cron_20260711_0234/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260711_0234_final/bridge_runs/cron_20260711_0234/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| CHAPTER_PREP_ONLY | 20260711_cffadf74b3 | Waxing Gibbous Moon | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260711_7944bd4a36 | Where Venezuela’s Earthquakes Shifted the Ground | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260711_814542297c | NASA Sets Coverage for Astronaut Anil Menon Launch to Space Station | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260711_8939edd9a3 | Satellites in tandem reveal 30 years of Antarctic ice flow | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260711_dd80ed61d1 | Deep space software upgrade for Hera’s asteroid visit | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260711_316aacc555 | Which ‘AI scientist’ suits your lab? A guide for the perplexed | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260711_5ce272a001 | 从无人机到动力舟桥 科技设备搭建广西洪灾救援保障线 | 国内权威短讯可作上传线现实细节，但须先人工复核正文核。 |
| ARCHIVE_WITH_REASON | 20260711_5dd03329e4 | 中方代表团出席国际热核聚变实验堆(ITER)计划理事会第三十八届会议 | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |

## Missing Cards by Tier

| tier | missing_card_ids |
|---|---|
| P1 | c1004_40753873_3602ea7ec61bc251 |

## Skipped

| title | source status | reason |
|---|---|---|
| 8 things to know about this year’s solar eclipse | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| Waxing Gibbous Moon | SKIP_DUPLICATE_BODY | duplicate_within_run |
| Where Venezuela’s Earthquakes Shifted the Ground | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Satellites in tandem reveal 30 years of Antarctic ice flow | DISTILLED | duplicate_within_run |
| Deep space software upgrade for Hera’s asteroid visit | SUMMARY_ONLY | duplicate_within_run |
| Which ‘AI scientist’ suits your lab? A guide for the perplexed | NEED_FETCH_BODY | duplicate_within_run |
| Does AI work for us, or do we work for AI? | SUMMARY_ONLY | summary_not_body_evidence |
| QANTIS: Hardware-Calibrated Sequential POMDP Belief Updates on IBM Heron | SUMMARY_ONLY | summary_not_body_evidence |
| Evaluating SageMath-Augmented LLM Agents for Computational and Experimental Math | SUMMARY_ONLY | summary_not_body_evidence |
| Inviting hard questions Announcements Jul 9, 2026 We’re asking the public for th | SUMMARY_ONLY | summary_not_body_evidence |
| Features Jul 6, 2026 The Making of Claude Code The inside story of how Claude Co | SUMMARY_ONLY | summary_not_body_evidence |
| g7 leaders statement ai prosperity | NEED_FETCH_BODY | missing_body_path |
| about | NEED_FETCH_BODY | missing_body_path |
| index | NEED_FETCH_BODY | missing_body_path |
| g7 leaders statement on ai for prosperity | NEED_FETCH_BODY | missing_body_path |
| g7 leaders summit | NEED_FETCH_BODY | missing_body_path |
| chairs summary | NEED_FETCH_BODY | missing_body_path |
| priorities | NEED_FETCH_BODY | missing_body_path |
| g7 energy and ai work plan | NEED_FETCH_BODY | missing_body_path |
| g7 call to action on enhancing energy security | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | NEED_FETCH_BODY | missing_body_path |
| president trump attends g7 summit in canada | NEED_FETCH_BODY | missing_body_path |
| president trump attends the g7 official welcome | NEED_FETCH_BODY | missing_body_path |
| president trump participates in a g7 family photo | NEED_FETCH_BODY | missing_body_path |
| president trump participates in an official greeting with g7 leaders | NEED_FETCH_BODY | missing_body_path |
| claude fable 5 mythos 5 | NEED_FETCH_BODY | missing_body_path |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 高质量数据集建设激活人工智能发展新动能 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| 250617 ai | NEED_FETCH_BODY | missing_body_path |
| 250617 summary | NEED_FETCH_BODY | missing_body_path |
| watch live white house holds briefing as trump agrees to two week ceasefire in i | NEED_FETCH_BODY | missing_body_path |
| trump israel iran ceasefire | NEED_FETCH_BODY | missing_body_path |
| israel iran ceasefire is in effect trump says | NEED_FETCH_BODY | missing_body_path |
| model deprecations | NEED_FETCH_BODY | missing_body_path |
| claude mythos preview is deprecated but its replacement is currently unavailable | NEED_FETCH_BODY | missing_body_path |
| introducing claude fable 5 and claude mythos 5 | NEED_FETCH_BODY | missing_body_path |
| c1024 40247782 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c40531 40710030 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| c1004 40753873 | DISTILLED | malformed_search_title |
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
| [QP:cmse.gov.cn] 载人航天 空间站 天舟 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cmse.gov.cn] 发射 火箭 运载 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:calt.com] 长征 火箭 运载 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:calt.com] 发射 成功 回收 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:spacechina.com] 长征 火箭 发射 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:spacechina.com] 运载火箭 可重复使用 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:nasa.gov] Artemis lunar program | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
