# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-09-13T11:48:45
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260913_1126
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 2
- source_card_count: 10
- fresh_news_card_count: 10
- valid_input_count: 10
- skipped_count: 10
- body_fetch_evidence_count: 12
- skip_reason_counts: {"stale_domestic_article": 3, "malformed_search_title": 1, "no_dyson_tree_match": 2, "low_value_policy_or_commentary": 1, "low_value_expo_or_conference": 1, "summary_not_body_evidence": 1, "not_article_page_url": 1}
- stale_domestic_blocked_count: 3
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 2, "ARCHIVE_WITH_REASON": 8}
- conversion_task_count: 2

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260913_1126_final/bridge_runs/cron_20260913_1126/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260913_1126_final/bridge_runs/cron_20260913_1126/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260913_1126_final/bridge_runs/cron_20260913_1126/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260913_9e5c184076 | {"url":"http://www.zj.xinhuanet.com/20260821/cdd023c1b641446882d73da55c83d712/c. | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260913_31c9c82bda | {"url":"http://www.xinhuanet.com/tech/20250210/298198e10208406184a67c8cce7030a3/ | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260913_41fb1af616 | {"url":"http://www.xinhuanet.com/photo/20250707/35dac4dbdda7404eb9ee543382b3ac56 | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260913_d5defb2f9c | {"url":"https://news.cctv.com/2026/03/10/ARTISRYGteWVLwHtnS1UYUWh260310.shtml"," | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260913_2fb89a68e4 | 科技新观察丨创新驱动三大指标提前实现 中国科技"十四五"乘风破浪 | 政策框架/概念文只作制度语境准备，不直接升为OUTLINE_PATCH。 |
| CHAPTER_PREP_ONLY | 20260913_bacbeced60 | 2025年度"中国科学十大进展"出炉 --科普时报--数字报 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260913_80d09e7141 | NASA Boosts Open Science, Data Sharing with Artemis Accords | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260913_5a2e1183dd | Monterrey Amid Mountains | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260913_d906ee53d7 | A team of teams like never before: rehearsing a unique launch at ESA mission con | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260913_d195f0fd78 | Watch: FLEX and Sentinel-3C launch on Vega-C | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |

## Skipped

| title | source status | reason |
|---|---|---|
| c1024 40247782 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c461001 40641560 | DISTILLED | malformed_search_title |
| c64387 40714909 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| c | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c 1126414617 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| VIDEYJbZOqLQkNYmpT9iw4N4251009 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| 科技创新的关键在于核心技术自主可控 - 中国科技网 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| 订单加速落地 机器人“皮肤”从实验室迈向商业化量产 | SUMMARY_ONLY | summary_not_body_evidence |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| 科技成果赋智企业“深度行”（福州站）活动成功举办 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
