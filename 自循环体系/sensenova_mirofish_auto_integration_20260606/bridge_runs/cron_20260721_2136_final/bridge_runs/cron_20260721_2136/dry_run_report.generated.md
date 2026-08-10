# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-07-21T21:56:19
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260721_2136
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 0
- source_card_count: 8
- fresh_news_card_count: 8
- valid_input_count: 8
- skipped_count: 112
- body_fetch_evidence_count: 12
- skip_reason_counts: {"no_dyson_tree_match": 15, "http_403|jina_timeout": 1, "not_article_page_url": 1, "duplicate_within_run": 5, "duplicate_url": 2, "summary_not_body_evidence": 2, "title_too_short": 2, "missing_body_path": 13, "low_value_expo_or_conference": 1, "stale_domestic_article": 1, "low_value_policy_theory_source": 1, "query_plan_no_body": 68}
- stale_domestic_blocked_count: 1
- p0_missing: False
- disposition_counts: {"OUTLINE_PATCH": 2, "CHAPTER_PREP_ONLY": 2, "ARCHIVE_WITH_REASON": 4}
- conversion_task_count: 2

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260721_2136_final/bridge_runs/cron_20260721_2136/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260721_2136_final/bridge_runs/cron_20260721_2136/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260721_2136_final/bridge_runs/cron_20260721_2136/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260721_bfd36acb63 | A New Compact Instrument Enables High-Fidelity Measurements of Energetic Particl | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260721_8a56bb4a53 | NASA Sets Briefings for SpaceX Crew-13 Mission to Space Station | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260721_e19b769662 | NASA, GE Aerospace Work Enables Hybrid-Electric Flight Demonstration | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260721_cc018d4854 | New NASA Earth Missions Gear Up to Start Science Flights | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260721_fd65bf0e58 | From Hampton to Mars: How NASA Langley Helped Land on the Red Planet | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| CHAPTER_PREP_ONLY | 20260721_aa12d849dc | ESA’s Mars Express meets NASA’s Psyche | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| OUTLINE_PATCH | 20260721_d34cd224c0 | New hope in the fight against cachexia — cancer’s deadly co-conspirator | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |
| OUTLINE_PATCH | 20260721_2fd47165c1 | 国产算力新品集中亮相 打造“超级大脑” | 与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。 |

## Skipped

| title | source status | reason |
|---|---|---|
| Why Maine’s Sandy Shorelines Turn Jagged | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Artemis II crew at ESTEC | BODY_FETCH_FAIL | HTTP_403|JINA_TIMEOUT |
| Does China’s latest AI model finally equal US rivals? What scientists think | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| A New Compact Instrument Enables High-Fidelity Measurements of Energetic Particl | DISTILLED | duplicate_within_run |
| From Hampton to Mars: How NASA Langley Helped Land on the Red Planet | SUMMARY_ONLY | duplicate_within_run |
| εpsilon | SKIP_DUPLICATE | DUPLICATE_URL |
| Artemis II crew at ESTEC | SUMMARY_ONLY | duplicate_within_run |
| ESA’s Mars Express meets NASA’s Psyche | SUMMARY_ONLY | duplicate_within_run |
| Does China’s latest AI model finally equal US rivals? What scientists think | ARCHIVE_WITH_REASON | duplicate_within_run |
| Deterministic Replay for AI Agent Systems | SUMMARY_ONLY | summary_not_body_evidence |
| Inviting hard questions Announcements Jul 9, 2026 We’re asking the public for th | SUMMARY_ONLY | summary_not_body_evidence |
| Features Jul 6, 2026 The Making of Claude Code The inside story of how Claude Co | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 20292 | ARCHIVE_WITH_REASON | TITLE_TOO_SHORT |
| g7 leaders summit | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| g7 leaders statement ai prosperity | NEED_FETCH_BODY | missing_body_path |
| about | ARCHIVE_WITH_REASON | TITLE_TOO_SHORT |
| g7 leaders statement on ai for prosperity | NEED_FETCH_BODY | missing_body_path |
| chairs summary | NEED_FETCH_BODY | missing_body_path |
| priorities | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| g7 call to action on enhancing energy security | NEED_FETCH_BODY | missing_body_path |
| g7 energy and ai work plan | NEED_FETCH_BODY | missing_body_path |
| bis guidance may 31 2026 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| department commerce revises license review policy semiconductors exported china | NEED_FETCH_BODY | missing_body_path |
| department commerce revises license review policy semiconductors exported china | NEED_FETCH_BODY | missing_body_path |
| commerce strengthens restrictions advanced computing semiconductors enhance foun | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| ai policy statement training ai models may 13 2025 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| bis guidance may 31 2026 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| FDD press release | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动 | SKIP_DUPLICATE | DUPLICATE_URL |
| 高质量数据集建设激活人工智能发展新动能 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| 250617 ai | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 250617 summary | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| artc exclusive tehran initiated proposal currently being promoted by mediators f | NEED_FETCH_BODY | missing_body_path |
| trump brokered ceasefire agreement contact with israel iran white house official | NEED_FETCH_BODY | missing_body_path |
| trump diplomacy iran israel ceasefire | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| model deprecations | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| trump advanced ai semiconductors actions | NEED_FETCH_BODY | missing_body_path |
| china recovered its first reusable rocket and showed a new way to do it | NEED_FETCH_BODY | missing_body_path |
| china recovers long march 10b reusable rocket maiden launch | NEED_FETCH_BODY | missing_body_path |
| making history china lands rocket during an orbital launch for 1st time ever | NEED_FETCH_BODY | missing_body_path |
| c1024 40247782 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c40531 40710030 | BODY_FETCH_FAIL | LOW_VALUE_POLICY_THEORY_SOURCE |
| c1004 40764182 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
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
