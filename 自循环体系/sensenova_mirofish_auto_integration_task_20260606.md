任务：实现 SenseNova 采集素材自动由 MiroFish 推演转化的闭环，主控不直接改脚本。

现状证据：
- skill 已写入规则：SenseNova 内置 MiroFish 投喂即转卡。
- 已有 MVP/手工推演：/root/workspace/科武纪元/实验/mirofish_variable_injection_mvp/
- 2026-06-04 有 10 张 SenseNova 卡手工 MiroFish 推演报告。
- 但当前 cron 脚本 /root/.hermes/scripts/run_sensenova_split_pipeline_cron_20260601.sh 不含 mirofish/feed_to_card。
- 当前 runner /root/workspace/scripts/sensenova_split_pipeline_runner.py 搜不到 mirofish/feed_to_card/OUTLINE_PATCH/CHAPTER_PREP_ONLY。

目标：不要停在文档/MVP，要落到自动化链路。

要求：
1. 只读审计当前 runner、cron、最新 run_dir、MiroFish MVP 目录。
2. 设计最小补丁，不直接改大纲/正文/TXT/草稿箱。
3. 增加或生成一个可调用阶段：mirofish_feed_to_card。
4. 输入：SenseNova 有效 cards/review.json/material candidates。
5. 输出：
   - MiroFish 投喂包
   - 三态裁决：OUTLINE_PATCH / CHAPTER_PREP_ONLY / ARCHIVE_WITH_REASON
   - 对 CHAPTER_PREP_ONLY 且证据齐全非重复者，转正式素材卡候选或给确定性转卡任务清单
   - 同步建议：时事素材 INDEX、知识库 INDEX、RAG、final_report
6. 若直接改生产 runner 风险大，先写补丁方案+独立桥接脚本，并做 dry-run。
7. 产物落：/root/workspace/科武纪元/自循环体系/sensenova_mirofish_auto_integration_20260606/
8. 必产：IMPLEMENTATION_PLAN.md、patch_or_script、DRY_RUN_REPORT.md、NEXT_ACTION.md。

边界：
- 不改正文。
- 不改大纲正式版。
- 不上传番茄。
- 不伪造有效素材卡。
- 不把 query_plan 当有效素材。

模型：SharedChat CLI / GPT-5.5。
