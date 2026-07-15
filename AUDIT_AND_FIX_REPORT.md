# AUDIT_AND_FIX_REPORT

- generated_at: 2026-07-12T00:45:00+08:00
- scope: SenseNova 主采集线；KOL/平台号雷达线；社媒助手 Chrome CDP 9224 只读补充能力
- boundary: 未改小说正文、latest 大纲、已投稿 TXT、草稿箱；未发布；未 git commit/push；未输出 Cookie/Token

## 结论

本轮发现并修复 5 个硬缺口：

1. `kewu_domain_scorer.py` 原先以静态 `outline_chapters` 为主，不能证明实际解析 latest 大纲。
2. 戴森球能力树原先只是 `+1` 弱加分，不能作为正式候选门禁。
3. SenseNova D 段未把 latest 大纲解析数、映射率、戴森归档原因写入正式报告。
4. KOL 雷达健康门禁仍允许 `min_domains_with_results=2` 后报 `HEALTHY`，违反 2/9 域不得健康。
5. 社媒助手 CDP 未有安全适配层；之前只能凭扩展页存在，不能证明可采集。

已完成修复：两线均真实调用九域本体与评分器；latest 大纲被动态解析；正式候选必须有 `dyson_tree_matches`，否则写 `ARCHIVE_WITH_REASON` / `NO_DYSON_TREE_MATCH`；KOL 报告输出九域健康矩阵；CDP 9224 只读探测并只允许小红书/抖音/B站/快手/TikTok既有打开页可见文本补充。

## latest 大纲基准

- outline_path: `/root/workspace/科武纪元/wiki/raw/outline/科武纪元大纲_latest.md`
- parser: `kewu_domain_scorer.parse_latest_outline()`
- parsed_chapters: 383
- chapter_mapping_source: latest outline occurrence parser + ontology keyword match；静态域章号只作为已解析 latest 章节内的弱 fallback。

## 修复文件

- `/root/workspace/科武纪元/工具脚本/kewu_domain_scorer.py`
  - 新增 `parse_latest_outline()`、`outline_parse_stats()`、`match_outline_chapters()`。
  - `score_item_domain_aware()` 默认解析 latest 大纲并返回 `outline_parse`、`outline_match_details`。
  - `match_dyson_tree()` 支持由 latest 章节命中反推能力树节点。
  - `score_and_classify_item()` 输出 `dyson_gate_status` 与 `archive_reason`；无戴森命中为 `ARCHIVE_NO_DYSON_TREE_MATCH`。

- `/root/workspace/scripts/sensenova_split_pipeline_runner.py`
  - D 段真实调用 `_score_and_classify_item()` 后，统计 `domain_scored_candidates`、`outline_mapped_candidates`、`dyson_tree_matched_candidates`、`archived_no_dyson_tree_match`。
  - 无 `dyson_tree_matches` 的候选写入 `ARCHIVE_WITH_REASON`，不生成正式素材卡。
  - 正式卡 metadata/report 写入 `domain_score`、`outline_chapter_hits`、`dyson_tree_matches`、`dyson_gate_status`。
  - final report 增加 latest 大纲路径、解析章节数、映射率、戴森命中/归档数。

- `/root/workspace/科武纪元/工具脚本/platform_radar_v2_20260622.py`
  - 接入 `score_and_classify_item()` / `outline_parse_stats()`。
  - 平台观点默认标记 `platform_commentary_discovery_not_primary_fact`，并要求 `official_crosscheck_required=True`。
  - 无 `dyson_tree_matches` 的 KOL 条目改为 `ARCHIVE_WITH_REASON`，不进入 MiroFish feed。
  - 健康门禁改为 9/9 域才可 `HEALTHY`；summary 输出九域配置账户数、查询数、产出账户数、正文成功数、缺失域。
  - 新增 CDP 9224 安全探测与只读正文补充：只读 `/json/version`、`/json/list`、扩展页公开 window key；只对已打开且 URL 完全匹配的小红书/抖音/B站/快手/TikTok页面读取可见文本；不读取 Cookie/localStorage/header，不导航，不互动，不发布。

- `/root/workspace/scripts/tests/test_kewu_ontology.py`
  - 增加 latest 大纲解析、动态章节映射、戴森门禁状态测试。

- `/root/workspace/科武纪元/工具脚本/tests/test_p0_kol_freshness.py`
  - 把 KOL 健康门禁测试从 2 域阈值改为 9 域阈值；修正域 ID 为 `ai`。

## 验收证据

- deps: `python3 /root/.hermes/skills/novel/kewu-science-material-collector/scripts/check_kewu_collector_deps.py` -> PASS
- py_compile: ontology/scorer/SenseNova/KOL -> PASS
- ontology tests: `/root/workspace/scripts/tests/test_kewu_ontology.py` -> 110 PASS, 0 FAIL
- KOL fixture tests: `/root/workspace/科武纪元/工具脚本/tests/test_p0_kol_freshness.py` -> 49 PASS, 0 FAIL
- SenseNova related tests:
  - `/root/workspace/scripts/tests/test_p0_sensenova_fix.py` -> 76 PASS, 0 FAIL
  - `/root/workspace/scripts/test_domestic_body_fetch_fix.py` -> PASS

## CDP 探测结果

- cdp_url: `http://127.0.0.1:9224`
- status: `CDP_AVAILABLE`
- browser: `Chrome/150.0.7871.115`
- extension_pages: 3
- platform_pages: 0
- extension_capability: `EXTENSION_PAGE_VISIBLE_NO_PUBLIC_API_DETECTED`
- conclusion: 当前扩展页存在，但未暴露可确认的采集 API；本轮不虚报社媒采集成功。安全替代路径已实现为“已打开平台页可见文本补充”，本次无小红书/抖音/B站/快手/TikTok匹配页可补正文。

## 剩余风险

- SenseNova 全链路生产小样 180 秒内只完成 A/F，未自然跑到 D；已用 runner D 段本地回放证明新门禁，但下一轮 cron/no-skip 仍需观察全链路是否在真实候选上跑完。
- KOL full 9账号小样超过 300 秒被外部 timeout 截断，仅留下 CDP probe；完整九域生产跑仍需更长执行窗口或新增每域限量参数。
- 社媒助手扩展未提供公开 API contract；若后续需要主动搜索/正文补充，需用户提供扩展接口说明，或保持当前只读既有页面适配，不绕平台安全。
