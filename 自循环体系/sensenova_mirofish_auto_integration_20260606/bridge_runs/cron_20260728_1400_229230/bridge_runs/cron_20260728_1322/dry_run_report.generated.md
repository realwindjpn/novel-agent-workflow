# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-28T14:08:28
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260728_1322
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 2
- fresh_news_card_count: 2
- valid_input_count: 2
- skipped_count: 18
- body_fetch_evidence_count: 11
- skip_reason_counts: {"no_dyson_tree_match": 7, "body_clean_too_short": 1, "not_article_page_url": 1, "duplicate_within_run": 4, "duplicate_url": 2, "low_value_expo_or_conference": 1, "stale_domestic_article": 1, "low_value_policy_or_commentary": 1}
- stale_domestic_blocked_count: 1
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 0, "ARCHIVE_WITH_REASON": 2}
- conversion_task_count: 0

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260728_1400_229230/bridge_runs/cron_20260728_1322/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260728_1400_229230/bridge_runs/cron_20260728_1322/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260728_1400_229230/bridge_runs/cron_20260728_1322/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260728_67c03e739d | NASA Science Soars During August Total Solar Eclipse | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260728_c21f291d9b | Two new Galileo satellites enter service | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |

## Skipped

| title | source status | reason |
|---|---|---|
| Raging wildfires near Madrid, Spain | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Why total solar eclipses are so special | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| Phase-homogeneous mixed halide perovskites for stable tandem photovoltaics | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| ‘Timer’ in the brain tracks sleep — and predicts awakening | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| How to prevent AI from harming mathematics | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 深海“密码曲”：南海抹香鲸声音里藏着什么秘密？ | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| NASA Science Soars During August Total Solar Eclipse | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Why total solar eclipses are so special | BODY_FETCH_FAIL | duplicate_within_run |
| Two new Galileo satellites enter service | DISTILLED | duplicate_within_run |
| How to prevent AI from harming mathematics | ARCHIVE_WITH_REASON | duplicate_within_run |
| Securing Multimodal AI through Internal Information Decomposition | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Announcements Jul 9, 2026 Inviting hard questions We’re asking the public for th | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 高质量数据集建设激活人工智能发展新动能 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c64094 40171173 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c64387 40763414 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
