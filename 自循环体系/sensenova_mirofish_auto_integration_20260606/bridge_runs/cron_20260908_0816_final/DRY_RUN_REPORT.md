# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-09-08T11:16:14
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260908_0816
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 2
- source_card_count: 7
- fresh_news_card_count: 7
- valid_input_count: 7
- skipped_count: 13
- body_fetch_evidence_count: 8
- skip_reason_counts: {"stale_domestic_article": 3, "low_value_policy_theory_source": 1, "low_value_expo_or_conference": 2, "low_value_policy_or_commentary": 1, "not_article_page_url": 1, "no_dyson_tree_match": 1, "summary_not_body_evidence": 4}
- stale_domestic_blocked_count: 3
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 2, "CHAPTER_PREP_ONLY": 1, "ARCHIVE_WITH_REASON": 4}
- conversion_task_count: 1

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260908_0816_final/bridge_runs/cron_20260908_0816/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260908_0816_final/bridge_runs/cron_20260908_0816/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260908_0816_final/bridge_runs/cron_20260908_0816/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260908_9e5c184076 | {"url":"http://www.zj.xinhuanet.com/20260821/cdd023c1b641446882d73da55c83d712/c. | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260908_d87c8c233b | {"url":"http://www.xinhuanet.com/20260410/0a421db3567641f4acd9d437d976734e/c.htm | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260908_1489302a93 | {"url":"http://www.xinhuanet.com/tech/20250608/80ddb31da03d47c4bdc4e41211323167/ | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260908_d5defb2f9c | {"url":"https://news.cctv.com/2026/03/10/ARTISRYGteWVLwHtnS1UYUWh260310.shtml"," | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260908_fa7a1ad7dd | 两部门联合启动2026年度计量支撑产业新质生产力发展项目征集工作 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| OUTLINE_PATCH | 20260908_7395a1e325 | 《人工智能医学影像研究伦理指引》发布 | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| OUTLINE_PATCH | 20260908_5b065ab90c | 科研人员研发混合集成气体传感芯片 | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |

## Skipped

| title | source status | reason |
|---|---|---|
| c1024 40247782 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c40531 40513142 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| c1002 40687061 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c 1126414617 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| VIDEYJbZOqLQkNYmpT9iw4N4251009 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| 携手推进平等有序的世界多极化 ——习近平主席中亚中东之行推动全球治理倡议走深走实 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| 科技成果赋智企业“深度行”（福州站）活动成功举办 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 研究揭示芭蕉科染色体演化机制与花苞着色遗传基础 | SUMMARY_ONLY | summary_not_body_evidence |
| 科研人员提出机器学习辅助的“材料—结构—功能”协同设计新策略 | SUMMARY_ONLY | summary_not_body_evidence |
| 海洋热浪生态效应研究取得进展 | SUMMARY_ONLY | summary_not_body_evidence |
| 神舟二十三号航天员乘组圆满完成出舱活动 | SUMMARY_ONLY | summary_not_body_evidence |
