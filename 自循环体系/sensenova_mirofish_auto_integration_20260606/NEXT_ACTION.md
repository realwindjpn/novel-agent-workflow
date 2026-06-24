# NEXT_ACTION 2026-06-06

## 当前裁决

本轮可判 `BRIDGE_DRY_RUN_PASS`。

## 已完成

- 只读审计 runner/cron/latest run/MiroFish MVP。
- 写独立桥接脚本：/root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/scripts/mirofish_feed_to_card_bridge_20260606.py
- 完成 py_compile。
- 用 latest run dry-run：/root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260606_1146
- 产出 MiroFish 投喂包、三态 decision_cards、转正式卡任务清单、dry-run 报告。

## 本轮不做

- 不改生产 runner。
- 不改 cron。
- 不写正式素材卡。
- 不更新时事素材 INDEX / 知识库 INDEX / Wiki。
- 不改大纲/正文/TXT/草稿箱。

## 下一步建议

1. 主控抽查 `bridge_run/decision_cards.json` 中 3-5 条 CHAPTER_PREP_ONLY，确认分类阈值。
2. 若通过，给 bridge 增加 `--apply-formal-card-tasks` 的只生成草稿卡模式，但仍不自动写 INDEX/Wiki。
3. 连续两轮 cron 后，用同脚本对最新 run dry-run，对比 query_plan 排除与 conversion_task_count。
4. 再决定是否 patch runner：在 E `card_review` 后插入 G `mirofish_feed_to_card`，并让 F `report_qq` 汇总 G。
5. 若要接 cron，先建单独 no_agent watcher 调 bridge，不直接改现有 launcher。

## 阻塞/风险

- 当前 bridge 的三态为确定性规则，不是模型推演；可作自动化骨架与任务清单，不能替代 G2/六角色裁决。
- 正式素材卡写入仍需正文证据、去重、人审/主控确认。
- 国内短讯与搜索命中可能存在伪正文，转卡前须复核 body 文件。


## 复验后下一步

- 当前 dry-run 三态：{"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 5, "ARCHIVE_WITH_REASON": 4}。
- 转正式卡任务清单：5 条，均须先读源卡+正文证据+去重后再写正式卡。
- 本轮 OUTLINE_PATCH=0，故勿启动大纲补丁；可把 CHAPTER_PREP_ONLY 作为 G3/上传线准备素材候选。
