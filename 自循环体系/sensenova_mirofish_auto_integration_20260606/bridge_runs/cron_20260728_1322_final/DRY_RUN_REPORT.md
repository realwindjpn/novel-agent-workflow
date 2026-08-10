# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-28T13:40:06
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
- skipped_count: 87
- body_fetch_evidence_count: 11
- skip_reason_counts: {"no_dyson_tree_match": 8, "body_clean_too_short": 1, "not_article_page_url": 1, "duplicate_within_run": 4, "duplicate_url": 2, "low_value_expo_or_conference": 1, "stale_domestic_article": 1, "low_value_policy_or_commentary": 1, "title_too_short": 1, "query_plan_no_body": 67}
- stale_domestic_blocked_count: 1
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 0, "ARCHIVE_WITH_REASON": 2}
- conversion_task_count: 0

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260728_1322_final/bridge_runs/cron_20260728_1322/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260728_1322_final/bridge_runs/cron_20260728_1322/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260728_1322_final/bridge_runs/cron_20260728_1322/card_conversion_tasks.json

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
| c1004 40703534 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
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
| [QP:cac.gov.cn] 人工智能 治理 数据 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cac.gov.cn] 网络安全 数据安全 生成式人工智能 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cmse.gov.cn] 载人航天 空间站 天舟 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:cmse.gov.cn] 发射 火箭 运载 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:calt.com] 长征 火箭 运载 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:calt.com] 发射 成功 回收 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:spacechina.com] 长征 火箭 发射 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:spacechina.com] 运载火箭 可重复使用 | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:nasa.gov] Artemis lunar program | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:esa.int] lunar exploration deep | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:darpa.mil] autonomous systems drone | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:defense.gov] drone swarm military | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:energy.gov] quantum energy research | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:noaa.gov] satellite climate ocean | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:pubmed.ncbi.nlm.nih.gov] brain computer interface | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:arxiv.org] quantum computing | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:arxiv.org] AI safety robotics | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:openalex.org] quantum computing AI | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:nature.com] quantum computing AI | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:science.org] quantum AI energy | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:ieee.org] AI chips robotics | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:bis.gov] export control semiconductors | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:semiconductors.org] semiconductor industry chips | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:g7.canada.ca] G7 Summit Kananaskis | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:g7.canada.ca] Group of Seven | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:canada.ca] G7 Summit Kananaskis | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:international.gc.ca] G7 summit Canada | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:whitehouse.gov] G7 Summit Kananaskis | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:whitehouse.gov] Group of Seven | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:consilium.europa.eu] G7 Summit Kananaskis | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:consilium.europa.eu] Group of Seven | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:state.gov] ceasefire Iran Israel | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
