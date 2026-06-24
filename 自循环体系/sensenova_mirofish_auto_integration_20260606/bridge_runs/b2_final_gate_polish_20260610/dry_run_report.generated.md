# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-06-10T22:17:54
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/b2_final_gate_polish_20260610
- dry_run: True
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- valid_input_count: 8
- skipped_count: 12
- skip_reason_counts: {"http_403|jina_timeout": 3, "missing_body_path": 2, "stale_domestic_article": 1, "low_value_policy_theory_source": 1, "low_value_expo_or_conference": 2, "low_value_policy_or_commentary": 1, "malformed_search_title": 1, "query_plan_no_body": 1}
- stale_domestic_blocked_count: 1
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 1, "ARCHIVE_WITH_REASON": 7}
- conversion_task_count: 1

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/b2_final_gate_polish_20260610/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/b2_final_gate_polish_20260610/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/b2_final_gate_polish_20260610/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260610_574d10c292 | Tyndall’s Trail of Bergs | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| CHAPTER_PREP_ONLY | 20260610_7b087574f8 | Flight Dynamics Research Facility Characteristics | 高机动平台与感知/噪声治理可作军事制度细节层。 |
| ARCHIVE_WITH_REASON | 20260610_1370f40ea0 | NASA Marches Toward Artemis III Mission in 2027, Names Crew Members | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260610_d090301e59 | ESA astronaut Luca Parmitano joins NASA’s Artemis III mission as pilot | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260610_7d0bebf0c1 | We’re back: Proba-3 ready for more science | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260610_3b40139555 | When drug discovery fails: scientists share their frustrations with the process | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260610_1152496bed | article | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |
| ARCHIVE_WITH_REASON | 20260610_cefd75b4e6 | article | 与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。 |

## Skipped

| title | source status | reason |
|---|---|---|
| Artemis III NASA announcement highlights: Luca Parmitano assigned as pilot | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| Luca Parmitano on Artemis III selection | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| Cleaner air and prosperity can go hand in hand | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| Gen Z scepticism towards AI is a wake-up call — universities must take it seriou | NEED_FETCH_BODY | missing_body_path |
| How I use AI to turn failed drugs into new medicines | NEED_FETCH_BODY | missing_body_path |
| c40531 40208988 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c40531 40521652 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| c1004 40732291 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| c | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c | DISTILLED | malformed_search_title |
| [QP:cctv.com] 先进制造 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
