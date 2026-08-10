# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-25T01:04:07
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260725_0045
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 6
- fresh_news_card_count: 6
- valid_input_count: 6
- skipped_count: 103
- body_fetch_evidence_count: 10
- skip_reason_counts: {"no_dyson_tree_match": 14, "body_clean_too_short": 1, "not_article_page_url": 1, "duplicate_within_run": 4, "duplicate_url": 2, "summary_not_body_evidence": 3, "missing_body_path": 7, "low_value_expo_or_conference": 1, "query_plan_no_body": 70}
- stale_domestic_blocked_count: 0
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 1, "CHAPTER_PREP_ONLY": 1, "ARCHIVE_WITH_REASON": 4}
- conversion_task_count: 1

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260725_0045_final/bridge_runs/cron_20260725_0045/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260725_0045_final/bridge_runs/cron_20260725_0045/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260725_0045_final/bridge_runs/cron_20260725_0045/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260725_f5d0ac0ad5 | NASA to Support Blue Origin New Glenn Rocket Testing, Advance Artemis | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260725_5391fc0a57 | Crews Move Artemis IV Liquid Hydrogen Tank | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260725_c21f291d9b | Two new Galileo satellites enter service | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260725_b5bd384e2b | 我国成功发射天链二号06星 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| ARCHIVE_WITH_REASON | 20260725_35db936c5d | AINTMA: Agentic AI Architecture for Autonomous Test Management with Generative I | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| OUTLINE_PATCH | 20260725_bb69cc6bf3 | ClickGuard: Detecting and Spoiling Clickbait News with Informativeness Measures  | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |

## Skipped

| title | source status | reason |
|---|---|---|
| Hubble Spies One-Sided Spiral | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Why total solar eclipses are so special | BODY_FETCH_FAIL | BODY_CLEAN_TOO_SHORT |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| NASA to Support Blue Origin New Glenn Rocket Testing, Advance Artemis | DISTILLED | duplicate_within_run |
| Crews Move Artemis IV Liquid Hydrogen Tank | DISTILLED | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Why total solar eclipses are so special | BODY_FETCH_FAIL | duplicate_within_run |
| Two new Galileo satellites enter service | DISTILLED | duplicate_within_run |
| JAXBench: Benchmarking Autonomous TPU Kernel Optimization | SUMMARY_ONLY | summary_not_body_evidence |
| DC-Leap: Training-Free Acceleration of dLLMs via Draft-Guided Contiguous Leaping | SUMMARY_ONLY | summary_not_body_evidence |
| Inviting hard questions Announcements Jul 9, 2026 We’re asking the public for th | SUMMARY_ONLY | summary_not_body_evidence |
| Features Jul 6, 2026 The Making of Claude Code The inside story of how Claude Co | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| prime minister carney announces canadas g7 priorities | NEED_FETCH_BODY | missing_body_path |
| canada opens g7 energy and environment ministers meeting | NEED_FETCH_BODY | missing_body_path |
| backgrounder g7 energy and environment ministers meeting energy and artificial i | NEED_FETCH_BODY | missing_body_path |
| g7 leaders statement on ai for prosperity | NEED_FETCH_BODY | missing_body_path |
| chairs summary | NEED_FETCH_BODY | missing_body_path |
| g7 leaders summit | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| priorities | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| g7 energy and ai work plan | NEED_FETCH_BODY | missing_body_path |
| g7 call to action on enhancing energy security | NEED_FETCH_BODY | missing_body_path |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president donald j trump attends the 51st g7 summit in kananaskis alberta canada | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump attends g7 summit in canada | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump attends the g7 official welcome | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump participates in a g7 family photo | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| president trump participates in an official greeting with g7 leaders | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 高质量数据集建设激活人工智能发展新动能 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| varcoe g7 leaders wrap up kananaskis summit touting energy security and critical | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| white house claims two week ceasefire with iran as a victory for the united stat | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| model deprecations | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| c1024 40756187 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| [QP:people.com.cn] 先进制造 产业升级 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
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
| [QP:cmse.gov.cn] 载人航天 空间站 天舟 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:cmse.gov.cn] 发射 火箭 运载 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:calt.com] 长征 火箭 运载 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:calt.com] 发射 成功 回收 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:spacechina.com] 长征 火箭 发射 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:spacechina.com] 运载火箭 可重复使用 | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:nasa.gov] Artemis lunar program | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:esa.int] lunar exploration deep | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:darpa.mil] autonomous systems drone | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:defense.gov] drone swarm military | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:energy.gov] quantum energy research | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:noaa.gov] satellite climate ocean | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:pubmed.ncbi.nlm.nih.gov] brain computer interface | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
| [QP:arxiv.org] quantum computing | QUERY_PLAN_NO_BODY_NOT_CARDABLE | query_plan_no_body |
