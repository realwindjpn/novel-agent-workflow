# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-06-09T08:35:56
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/prod_cnsa_fallback_20260609_031025
- dry_run: True
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- valid_input_count: 9
- skipped_count: 11
- skip_reason_counts: {"not_official_verified": 1, "query_plan_no_body": 8, "STALE_DOMESTIC_ARTICLE": 2}
- stale_domestic_blocked_count: 0
- disposition_counts: {"OUTLINE_PATCH": 1, "CHAPTER_PREP_ONLY": 4, "ARCHIVE_WITH_REASON": 4}
- conversion_task_count: 4

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/verification_runs/bridge_hardening_20260609/bridge_run/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/verification_runs/bridge_hardening_20260609/bridge_run/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/verification_runs/bridge_hardening_20260609/bridge_run/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| CHAPTER_PREP_ONLY | 20260609_a60f797b5a | 期待，中国深空探测“大动作”！ | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260609_011e9afe32 | Supersonic! | 重复或已入库：SAME_EVENT_X59_FIRST_SUPERSONIC_FLIGHT |
| CHAPTER_PREP_ONLY | 20260609_27dff0322f | 新质生产力赋能高质量发展的实现路径 - 理论- 人民网 | 政策框架/概念文只作制度语境准备，不直接升为OUTLINE_PATCH。 |
| CHAPTER_PREP_ONLY | 20260609_4b90b75e2e | NASA’s INCUS Satellites Progress Toward Launch | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| OUTLINE_PATCH | 20260609_a3ac514696 | “图灵进化”完成新一轮数千万级别融资 - 人民网 | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| CHAPTER_PREP_ONLY | 20260609_eb6086966e | 推动科技创新和产业创新融合发展 - 新华网 | 生物伦理/人才争夺/科研治理素材，可作后续章节准备。 |
| ARCHIVE_WITH_REASON | 20260609_46489de369 | NASA’s X-59 Aircraft Flies Supersonic for First Time | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260609_7615a28737 | NASA Announces Winners of 2026 University Innovation Competition | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260609_7d54703422 | NASA’s Artemis II Moon Mission Research Continues on Earth | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |

## Skipped

| title | source status | reason |
|---|---|---|
| 探月“三步走” 收官“有看头”——中国探月工程嫦娥五号任务正式启航 | DISCOVERY_ONLY | not_official_verified |
| [QP:unknown] 微博热榜 科技 航天 | DISCOVERY_PENDING | query_plan_no_body |
| [QP:unknown] Twitter space technology | DISCOVERY_PENDING | query_plan_no_body |
| 科技创新引领制造业高质量发展 - 理论- 人民网 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| [QP:unknown] 知乎热榜 科技 半导体 | DISCOVERY_PENDING | query_plan_no_body |
| 新质生产力的内涵特征和发展重点 - 新华网 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| [QP:unknown] reddit technology defense | DISCOVERY_PENDING | query_plan_no_body |
| [QP:unknown] B站热门 科技 航天 | DISCOVERY_PENDING | query_plan_no_body |
| [QP:unknown] Hacker News AI | DISCOVERY_PENDING | query_plan_no_body |
| [QP:unknown] 百度热搜 科技 航天 | DISCOVERY_PENDING | query_plan_no_body |
| [QP:unknown] ResetEra technology defense | DISCOVERY_PENDING | query_plan_no_body |
