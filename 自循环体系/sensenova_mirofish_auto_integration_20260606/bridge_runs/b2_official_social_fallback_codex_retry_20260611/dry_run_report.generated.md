# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-06-11T00:48:18
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/b2_official_social_fallback_codex_retry_20260611
- dry_run: True
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- valid_input_count: 8
- skipped_count: 12
- skip_reason_counts: {"body_clean_too_short": 2, "http_403|jina_timeout": 1, "stale_domestic_article": 1, "low_value_expo_or_conference": 1, "low_value_policy_or_commentary": 1, "malformed_search_title": 2, "query_plan_no_body": 4}
- stale_domestic_blocked_count: 1
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 2, "ARCHIVE_WITH_REASON": 6}
- conversion_task_count: 2

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/b2_official_social_fallback_codex_retry_20260611/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/b2_official_social_fallback_codex_retry_20260611/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/b2_official_social_fallback_codex_retry_20260611/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| CHAPTER_PREP_ONLY | 20260611_27bed3fdae | Train Ride to NASA Kennedy for Artemis III Booster Segments | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260611_574d10c292 | Tyndall’s Trail of Bergs | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260611_ea6b18a0c1 | ESA adopts galactic archaeology mission Arrakihs | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260611_d090301e59 | ESA astronaut Luca Parmitano joins NASA’s Artemis III mission as pilot | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260611_28c24f2add | Whole-genome duplication shaped cell-type evolution in the vertebrate brain | 生物伦理/人才争夺/科研治理素材，可作后续章节准备。 |
| ARCHIVE_WITH_REASON | 20260611_27bae72044 | c64094 40722548 | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260611_1152496bed | article | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260611_cefd75b4e6 | article | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |

## Skipped

| title | source status | reason |
|---|---|---|
| Artemis III NASA announcement highlights: Luca Parmitano assigned as pilot | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| Luca Parmitano on Artemis III selection | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| We’re back: Proba-3 ready for more science | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| c40531 40208988 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c1004 40732291 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| c | DISTILLED | malformed_search_title |
| c | DISTILLED | malformed_search_title |
| [QP:cctv.com] 先进制造 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cctv.com] query_plan | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cctv.com] 人工智能 半导体 算力 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cctv.com] 新材料 能源 动力装备 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
