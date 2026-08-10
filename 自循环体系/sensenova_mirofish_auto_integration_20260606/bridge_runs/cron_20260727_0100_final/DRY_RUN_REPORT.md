# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-27T01:15:50
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260727_0100
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 5
- fresh_news_card_count: 5
- valid_input_count: 5
- skipped_count: 108
- body_fetch_evidence_count: 10
- skip_reason_counts: {"no_dyson_tree_match": 14, "body_clean_too_short": 1, "not_article_page_url": 1, "duplicate_within_run": 6, "duplicate_url": 2, "summary_not_body_evidence": 1, "missing_body_path": 12, "low_value_expo_or_conference": 1, "stale_domestic_article": 1, "low_value_policy_or_commentary": 2, "title_too_short": 1, "query_plan_no_body": 66}
- stale_domestic_blocked_count: 1
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 0, "ARCHIVE_WITH_REASON": 5}
- conversion_task_count: 0

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260727_0100_final/bridge_runs/cron_20260727_0100/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260727_0100_final/bridge_runs/cron_20260727_0100/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260727_0100_final/bridge_runs/cron_20260727_0100/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260727_47458aabf3 | New Crew Members Welcomed to International Space Station | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260727_9996f197a2 | NASA Announces New Spacecraft Technology Demonstration Mission at Moon | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260727_f5d0ac0ad5 | NASA to Support Blue Origin New Glenn Rocket Testing, Advance Artemis | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260727_c21f291d9b | Two new Galileo satellites enter service | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260727_670ce1765b | White House rolls out AI funding — and signals a new era for US science | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |

## Skipped

| title | source status | reason |
|---|---|---|
| NASA’s ESCAPADE Snaps Family Portrait of Earth, Moon | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Hubble Spies One-Sided Spiral | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Why total solar eclipses are so special | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| NASA’s ESCAPADE Snaps Family Portrait of Earth, Moon | ARCHIVE_WITH_REASON | duplicate_within_run |
| NASA Announces New Spacecraft Technology Demonstration Mission at Moon | DISTILLED | duplicate_within_run |
| NASA to Support Blue Origin New Glenn Rocket Testing, Advance Artemis | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Why total solar eclipses are so special | SUMMARY_ONLY | duplicate_within_run |
| Two new Galileo satellites enter service | SUMMARY_ONLY | duplicate_within_run |
| White House rolls out AI funding — and signals a new era for US science | NEED_FETCH_BODY | duplicate_within_run |
| Announcements Jul 9, 2026 Inviting hard questions We’re asking the public for th | SUMMARY_ONLY | summary_not_body_evidence |
| g7 leaders statement ai prosperity | NEED_FETCH_BODY | missing_body_path |
| backgrounder en | NEED_FETCH_BODY | missing_body_path |
| prime minister carney concludes 2025 g7 leaders summit | NEED_FETCH_BODY | missing_body_path |
| g7 leaders statement on ai for prosperity | NEED_FETCH_BODY | missing_body_path |
| g7 leaders summit | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| chairs summary | NEED_FETCH_BODY | missing_body_path |
| priorities | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| g7 energy and ai work plan | NEED_FETCH_BODY | missing_body_path |
| g7 call to action on enhancing energy security | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump attends g7 summit in canada | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump participates in a g7 family photo | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump attends the g7 official welcome | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump participates in an official greeting with g7 leaders | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 高质量数据集建设激活人工智能发展新动能 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| 250617 ai | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 250617 summary | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| trump brokered ceasefire agreement contact with israel iran white house official | NEED_FETCH_BODY | missing_body_path |
| watch live white house holds briefing as trump agrees to two week ceasefire in i | NEED_FETCH_BODY | missing_body_path |
| israel joins us brokered ceasefire with iran white house says | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| china recovered its first reusable rocket and showed a new way to do it | NEED_FETCH_BODY | missing_body_path |
| china recovers long march 10b reusable rocket maiden launch | NEED_FETCH_BODY | missing_body_path |
| making history china lands rocket during an orbital launch for 1st time ever | NEED_FETCH_BODY | missing_body_path |
| c1024 40247782 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c64387 40763414 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| c1004 40765423 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| c | ARCHIVE_WITH_REASON | TITLE_TOO_SHORT |
| c | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
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
| [QP:esa.int] lunar exploration deep | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:darpa.mil] autonomous systems drone | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
