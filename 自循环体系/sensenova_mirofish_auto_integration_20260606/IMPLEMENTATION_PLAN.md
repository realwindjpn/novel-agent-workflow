# SenseNova × MiroFish 自动转化最小实施计划 2026-06-06

## 结论

采用独立桥接脚本先接入，不直接改生产 runner。

本轮已完成只读审计、独立脚本、dry-run。未改正文/大纲/TXT/草稿箱；未写正式素材卡；未更新 INDEX/Wiki。

## 审计对象

- 任务书：/root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_task_20260606.md
- 生产 runner：/root/workspace/scripts/sensenova_split_pipeline_runner.py
- cron launcher：/root/.hermes/scripts/run_sensenova_split_pipeline_cron_20260601.sh
- 最新 run_dir：/root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260606_1146
- MiroFish MVP：/root/workspace/科武纪元/实验/mirofish_variable_injection_mvp

## 当前状态

### runner

- 现有阶段：A collect_sources、B p0_current_events、B2 body_fetch、C book_learning、D card_distill、E card_review、F report_qq。
- 未发现生产内置 `mirofish_feed_to_card` 阶段。
- D 段已能生成：cards/*.md、card_*.json、card_distill_plan.json。
- F 段 final_report 只统计 valid/query_plan/body_fetch，不含 MiroFish 三态裁决。

### cron

- 现有 job：SenseNova每5小时科武计划驱动采集蒸馏。
- job_id：980b3f9f8d62。
- no_agent：true。
- script：run_sensenova_split_pipeline_cron_20260601.sh。
- cron launcher 只启动 runner，不含 MiroFish bridge。

### latest run

- run_id：cron_20260606_1146
- status：done
- valid_content_cards：20
- query_plan_cards：47
- body_fetch_success：20
- card_pass_count：20

### MiroFish MVP

- 已有 schema：daily_g2_design/templates/decision_card_schema.json。
- 已有历史推演：sensenova_20260604_inference/decision_cards.json。
- 历史三态：OUTLINE_PATCH / CHAPTER_PREP_ONLY / ARCHIVE_WITH_REASON。
- MVP 边界：不改正文、不改大纲、不建 cron。

## 最小接入设计

### 新阶段名

`mirofish_feed_to_card`

### 输入

优先顺序：
1. latest run `cards/card_distill_plan.json` 中 `status=DISTILLED` 且有 URL 的条目。
2. 对应 `cards/*.md` 作为正文证据摘要。
3. `*.review.json` 如存在，作为审卡信号。
4. 排除 `OFFICIAL_QUERY_PLAN` / `DISCOVERY_PENDING` / 无 URL / 缺卡文件项。

### 输出

- `mirofish_feed_package.json`：投喂包。
- `decision_cards.json`：三态裁决卡。
- `card_conversion_tasks.json`：正式转卡任务清单。
- `DRY_RUN_REPORT.md`：dry-run 证据报告。

### 写入边界

当前只写：

`/root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/`

不写：
- 生产 runner。
- cron launcher。
- 时事素材正式卡目录。
- 时事素材 INDEX。
- 知识库 INDEX。
- Wiki JSONL。
- 大纲/正文/TXT/草稿箱。

## 后续生产补丁建议

安全路线：
1. 保留本 bridge 为外部脚本。
2. cron launcher 在 runner 完成后，由 watcher 或单独 no_agent job 调用 bridge。
3. 连续两轮 dry-run PASS 后，再把阶段嵌入 runner：D/E 后、F 前。
4. 嵌入后 F final_report 增加 MiroFish 汇总区。
5. 正式转卡仍须二次门禁：证据齐全、非重复、非 query_plan、人工/主控确认后写 INDEX/Wiki。

## 验收门禁

- `python3 -m py_compile scripts/mirofish_feed_to_card_bridge_20260606.py` PASS。
- dry-run exit=0。
- query_plan 排除数与 report 一致。
- decision_cards 均含三态字段。
- CHAPTER_PREP_ONLY 仅生成任务清单，不伪造正式卡。


## dry-run复验修正

首次 dry-run 后发现确定性规则误把英文单词片段 `ai` 命中为 AI 主题，并且同 run 内 cctv/cmse 重复项未去重。
已修：
- 英文 AI/robot/chip/quantum 改为 word-boundary 匹配。
- 同一 run 内按 URL/candidate_id/title 去重。

复验结果：
- valid_input_count：9
- skipped_count：58
- disposition_counts：{"OUTLINE_PATCH": 0, "CHAPTER_PREP_ONLY": 5, "ARCHIVE_WITH_REASON": 4}
- conversion_task_count：5
- OUTLINE_PATCH 为 0；本轮桥接不建议直接触发大纲候选。
