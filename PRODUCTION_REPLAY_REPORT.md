# PRODUCTION_REPLAY_REPORT

- generated_at: 2026-07-12T00:47:00+08:00
- boundary: 未改正文/大纲/已投稿 TXT/草稿箱；未发布；未提交 git

## SenseNova 主采集线

### 生产形态小样

- command: `python3 /root/workspace/scripts/sensenova_split_pipeline_runner.py --max-seconds 180 --skip-models --body-fetch-limit 4 --limit-candidates 8`
- run_dir: `/root/workspace/科武纪元/学习记录/SenseNova分段任务化/20260712_002357`
- final_report: `/root/workspace/科武纪元/学习记录/SenseNova分段任务化/20260712_002357/final_report.md`
- result: `PARTIAL`
- completed stages: A `collect_sources` done=56；F `report_qq` done
- blocker: 180 秒预算内 A 段耗时用尽，B/B2/D 未自然执行；不是代码异常。

### D 段门禁回放

- run_dir: `/root/workspace/科武纪元/学习记录/SenseNova分段任务化/codex_audit_gate_replay_20260712_0042`
- final_report: `/root/workspace/科武纪元/学习记录/SenseNova分段任务化/codex_audit_gate_replay_20260712_0042/final_report.md`
- card_distill_plan: `/root/workspace/科武纪元/学习记录/SenseNova分段任务化/codex_audit_gate_replay_20260712_0042/cards/card_distill_plan.json`
- outline_path: `/root/workspace/科武纪元/wiki/raw/outline/科武纪元大纲_latest.md`
- parsed_chapters: 383
- domain_scored_candidates: 2
- outline_mapped_candidates: 1
- mapping_rate: 0.5
- dyson_tree_matched_candidates: 1
- archived_no_dyson_tree_match: 1
- formal_cards_written: 1
- verdict: PASS for new D-stage gates. Formal candidate has `dyson_tree_matches`; non-Dyson candidate is archived with reason.

## KOL/平台号雷达线

### 截断证据

- command: `python3 /root/workspace/科武纪元/工具脚本/platform_radar_v2_20260622.py --limit 9 --timeout-sec 5 --dry-run-mirofish --out-dir .../codex_audit_small_20260712_0027`
- result: external timeout at 300s
- evidence_dir: `/root/workspace/科武纪元/学习记录/平台号观点雷达/runs/codex_audit_small_20260712_0027`
- written_files: `social_cdp_probe.json` only
- conclusion: 9-account sample needs longer window or per-domain limiting; no fake success reported.

### 完整小样

- command: `python3 /root/workspace/科武纪元/工具脚本/platform_radar_v2_20260622.py --limit 2 --timeout-sec 4 --dry-run-mirofish --out-dir /root/workspace/科武纪元/学习记录/平台号观点雷达/runs/codex_audit_small_20260712_0034`
- run_dir: `/root/workspace/科武纪元/学习记录/平台号观点雷达/runs/codex_audit_small_20260712_0034`
- discovery_json: `/root/workspace/科武纪元/学习记录/平台号观点雷达/runs/codex_audit_small_20260712_0034/platform_discovery.json`
- body_report: `/root/workspace/科武纪元/学习记录/平台号观点雷达/runs/codex_audit_small_20260712_0034/body_fetch_report.json`
- summary: `/root/workspace/科武纪元/学习记录/平台号观点雷达/runs/codex_audit_small_20260712_0034/radar_v2_summary.md`
- social_cdp_probe: `/root/workspace/科武纪元/学习记录/平台号观点雷达/runs/codex_audit_small_20260712_0034/social_cdp_probe.json`

Stats:
- total_queries: 4
- discovered: 12
- body_fetched: 9
- excerpt_only: 1
- fetch_fail: 1
- skipped_non_article: 1
- platform_signal: 3
- archive_with_reason: 9
- dyson_tree_matched: 3
- outline_mapped: 7
- outline_path: `/root/workspace/科武纪元/wiki/raw/outline/科武纪元大纲_latest.md`
- parsed_chapters: 383
- outline_mapping_rate: 7/12 = 0.583
- sidecar_health: `PARTIAL`
- domains_with_results: 1/9
- silent_domains: geopolitics, biology, space, aviation, ai, military, materials, energy
- body_fetch_failures: `BODY_FETCH_FAIL=2`

Nine-domain health matrix is written in `radar_v2_summary.md`. The run correctly refuses to call 1/9 domains `HEALTHY`.

## 社媒助手 CDP

- cdp_url: `http://127.0.0.1:9224`
- status: `CDP_AVAILABLE`
- extension_pages: 3
- supported supplement platforms: 小红书/xiaohongshu, 抖音/douyin, B站/bilibili, 快手/kuaishou, TikTok/tiktok
- platform_pages: 0
- extension_capability: `EXTENSION_PAGE_VISIBLE_NO_PUBLIC_API_DETECTED`
- action: no social harvest claimed. Safe adapter is present for existing matching platform tabs only.

## Regression

- deps: PASS
- py_compile: PASS
- ontology tests: 110 PASS / 0 FAIL
- KOL fixture tests: 49 PASS / 0 FAIL
- SenseNova tests: 76 PASS / 0 FAIL
- domestic body fetch regression: PASS

## Diff Summary

- Added latest-outline parser and dynamic chapter matcher in `kewu_domain_scorer.py`.
- Promoted Dyson tree from weak bonus to explicit gate with `PASS_DYSON_TREE` / `ARCHIVE_NO_DYSON_TREE_MATCH`.
- Added SenseNova D-stage archive behavior and reporting metrics.
- Added KOL nine-domain matrix and 9/9 health rule.
- Added CDP 9224 read-only probe and existing-tab visible-text adapter for allowed social platforms.
- Updated tests to lock latest-outline parsing, Dyson gating, and 9-domain KOL health behavior.
