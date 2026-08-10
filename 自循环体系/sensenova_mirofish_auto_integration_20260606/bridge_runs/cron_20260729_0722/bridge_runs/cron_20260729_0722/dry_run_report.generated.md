# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-29T12:30:52
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260729_0722
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 1
- fresh_news_card_count: 1
- valid_input_count: 1
- skipped_count: 49
- body_fetch_evidence_count: 11
- skip_reason_counts: {"http_403|jina_timeout": 2, "body_clean_too_short": 1, "no_dyson_tree_match": 7, "not_article_page_url": 1, "duplicate_within_run": 4, "duplicate_url": 2, "low_value_expo_or_conference": 1, "stale_domestic_article": 1, "low_value_policy_theory_source": 1, "title_too_short": 1, "query_plan_no_body": 28}
- stale_domestic_blocked_count: 1
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 0, "ARCHIVE_WITH_REASON": 1}
- conversion_task_count: 0

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260729_0722/bridge_runs/cron_20260729_0722/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260729_0722/bridge_runs/cron_20260729_0722/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260729_0722/bridge_runs/cron_20260729_0722/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260729_67c03e739d | NASA Science Soars During August Total Solar Eclipse | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |

## Skipped

| title | source status | reason |
|---|---|---|
| How Sentinel-1 measured movement of Venezuela quakes | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| Raging wildfires near Madrid, Spain | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| Why total solar eclipses are so special | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| It’ll grow on you: live fungi formed into sustainable fashion | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Use AI, but don’t mask it | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| NASA Science Soars During August Total Solar Eclipse | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| How Sentinel-1 measured movement of Venezuela quakes | DISTILLED | duplicate_within_run |
| Why total solar eclipses are so special | BODY_FETCH_FAIL | duplicate_within_run |
| Use AI, but don’t mask it | SKIP_DUPLICATE_BODY | duplicate_within_run |
| Securing Multimodal AI through Internal Information Decomposition | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Announcements Jul 9, 2026 Inviting hard questions We’re asking the public for th | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| position open weights models | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| latest news | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 高质量数据集建设激活人工智能发展新动能 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c1024 40247782 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c40531 40710030 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| c1004 40763580 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| c | ARCHIVE_WITH_REASON | TITLE_TOO_SHORT |
| [QP:xinhuanet.com] query_plan | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:xinhuanet.com] 人工智能 半导体 算力 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:xinhuanet.com] 新材料 能源 动力装备 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:xinhuanet.com] 航天 深空 探测 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
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
