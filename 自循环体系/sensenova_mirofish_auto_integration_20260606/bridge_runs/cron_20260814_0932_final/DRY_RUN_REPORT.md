# MiroFish feed-to-card bridge dry-run report

- created_at: 2026-08-14T09:48:01
- source_run_dir: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260814_0932
- dry_run: False
- production_runner_modified: NO
- formal_cards_written: NO
- outline_text_txt_draft_modified: NO
- expert_gate_pass: True
- expert_voice_card_count: 2
- source_card_count: 12
- fresh_news_card_count: 12
- valid_input_count: 12
- skipped_count: 94
- body_fetch_evidence_count: 14
- skip_reason_counts: {"low_value_expo_or_conference": 2, "stale_domestic_article": 3, "low_value_policy_or_commentary": 1, "query_plan_no_body": 54, "no_dyson_tree_match": 10, "summary_not_body_evidence": 11, "missing_body_path": 4, "not_article_page_url": 1, "duplicate_within_run": 6, "duplicate_url": 1, "title_too_short": 1}
- stale_domestic_blocked_count: 3
- p0_missing: True
- disposition_counts: {"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 4, "ARCHIVE_WITH_REASON": 8}
- conversion_task_count: 4

## Outputs

- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260814_0932_final/bridge_runs/cron_20260814_0932/mirofish_feed_package.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260814_0932_final/bridge_runs/cron_20260814_0932/decision_cards.json
- /root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260814_0932_final/bridge_runs/cron_20260814_0932/card_conversion_tasks.json

## Disposition table

| disposition | material_id | title | reason |
|---|---|---|---|
| ARCHIVE_WITH_REASON | 20260814_2b0c6cb0cd | “本源悟空”初步具备搭载人工智能运算能力 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260814_30773c61e5 | 打个“飞的”到机场、乘坐“空中出租车”跨长江、在长城边喝一杯无人机送来的咖啡……低空经济不断上“新”，逐渐走进人们生活。 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| CHAPTER_PREP_ONLY | 20260814_b5413335bb | 我国具备执行陆海两栖航天搜索回收任务能力 | 地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。 |
| CHAPTER_PREP_ONLY | 20260814_d75028888a | 当你坐着C919大飞机去旅行，是不是特别有自豪感？这个“大飞机梦”的实现，可是咱们多年关键核心技术攻关啃下来的硬骨头。 | 生物伦理/人才争夺/科研治理素材，可作后续章节准备。 |
| CHAPTER_PREP_ONLY | 20260814_108d415718 | VIDEfc57nFjIDEdkE5VvOz5V260716 | 政策框架/概念文只作制度语境准备，不直接升为OUTLINE_PATCH。 |
| ARCHIVE_WITH_REASON | 20260814_ea7cc8e9b0 | what is the artemis program grades 5 8 | 展会/航展/博览会文，低技术突破增益，归档。 |
| ARCHIVE_WITH_REASON | 20260814_f5cfd060f4 | European Gateway experiment will monitor radiation in deep space | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260814_ec59d28129 | defense official discusses unmanned aircraft systems human decision making ai | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| ARCHIVE_WITH_REASON | 20260814_610e925bee | quantum information science | 重复或已入库：TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY |
| CHAPTER_PREP_ONLY | 20260814_34f00e063c | satellites ocean | 气象/地球观测素材，可作章节准备包中的遥感盲区/侦察代价参考；非地月深空链。 |
| ARCHIVE_WITH_REASON | 20260814_5d17f6724c | 长十乙首飞成功 我国首次实现运载火箭可控回收 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |
| ARCHIVE_WITH_REASON | 20260814_915f0027ce | 探秘一块锂电池的“重生”之旅 | 重复或已入库：SOURCE_URL_ALREADY_IN_INDEX_OR_CARD |

## Missing Cards by Tier

| tier | missing_card_ids |
|---|---|
| P0 | 我国具备执行陆海两栖航天搜索回收任务能力_fcb55685188dc7e5 |
| P1 | VIDEfc57nFjIDEdkE5VvOz5V260716_42c1d8d8314bd3de, satellites_ocean_6d07af5cd70f8ba0, what_is_the_artemis_program_grades_5_8_c173b4b63cc4959f, 当你坐着C919大飞机去旅行_是不是特别有自豪感_这个_大飞机梦_的实现_可是咱们多年关键_97a6687180e515d4 |

## Skipped

| title | source status | reason |
|---|---|---|
| c1004 40772501 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c1004 40155728 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| c1002 40778424 | BODY_FETCH_FAIL | LOW_VALUE_EXPO_OR_CONFERENCE |
| c | BODY_FETCH_FAIL | LOW_VALUE_POLICY_OR_COMMENTARY |
| c 1124855083 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
| ARTIiLGt5s118iViaUCrbrOu240126 | BODY_FETCH_FAIL | STALE_DOMESTIC_ARTICLE |
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
| uh 60mx black hawk army | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
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
| [QP:state.gov] treaty ceasefire official | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:treasury.gov] sanctions Iran technology | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:treasury.gov] sanctions export controls | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:anthropic.com] Claude model disabled | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:anthropic.com] model availability Claude | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:status.anthropic.com] Claude model availability | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| [QP:openai.com] model availability deprecated | DISCOVERY_ONLY_NOT_CARDABLE | query_plan_no_body |
| NASA’s 737 Reveals New Paint | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| APOD: 2026 August 13 – Total Solar Eclipse Over Spain | SUMMARY_ONLY | summary_not_body_evidence |
| Cascade Volcanoes Shrouded in Smoke | SUMMARY_ONLY | summary_not_body_evidence |
| NASA Data Helps Commercial Space Plan Living Off Our Moon | SUMMARY_ONLY | summary_not_body_evidence |
| MTG-I1 captures eclipse path of totality over Europe | SUMMARY_ONLY | summary_not_body_evidence |
| Musification of the 2026 total solar eclipse | SUMMARY_ONLY | summary_not_body_evidence |
| Lion Nebula roars to life for Webb | SUMMARY_ONLY | summary_not_body_evidence |
| Wildfires, drought and extreme heat, 2026 | SUMMARY_ONLY | summary_not_body_evidence |
| Author Correction: Cretaceous bird from Brazil informs the evolution of the avia | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| Can Anthropic’s invisible watermarks curb ‘AI slop’? Researchers remain sceptica | NEED_FETCH_BODY | missing_body_path |
| AI isn’t ready to research itself | NEED_FETCH_BODY | missing_body_path |
| 第二届世界人形机器人运动会参赛机器人数量翻两番 | SUMMARY_ONLY | summary_not_body_evidence |
| “AI桂林”文旅大模型正式上线 “AI桂林”文旅大模型在第22届中国—东盟博览会正式上线。这是桂林市与人民网深度合作开发的首个聚焦打造“世界级旅游城市”的全域智 | BODY_FETCH_FAIL | NOT_ARTICLE_PAGE_URL |
| 植保作业、大田播种、畜禽巡检、果蔬分拣……“晋字号”机器人在田间大显身手 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| AI破圈好物持续“上新” 中国智造圈粉世界 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 两部门联合启动2026年度计量支撑产业新质生产力发展项目征集工作 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| 科技成果赋智企业“深度行”（拉萨站）活动成功举办 | ARCHIVE_WITH_REASON | NO_DYSON_TREE_MATCH |
| NASA’s 737 Reveals New Paint | ARCHIVE_WITH_REASON | duplicate_within_run |
| NASA Data Helps Commercial Space Plan Living Off Our Moon | SUMMARY_ONLY | duplicate_within_run |
