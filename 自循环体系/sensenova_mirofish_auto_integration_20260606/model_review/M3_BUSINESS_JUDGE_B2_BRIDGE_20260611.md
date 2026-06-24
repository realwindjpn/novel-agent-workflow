# M3 业务裁判：B2 / bridge 恢复判定

- 裁判时间：2026-06-11
- 裁判模型：hs / MiniMax-M3
- 裁判范围：只读业务裁判；未修改 cron；未修改代码。
- 输入文件：
  - GLM_READONLY_REVIEW_B2_BRIDGE_20260611.md
  - CONTROLLER_REVIEW_batch_20260611.md
  - NEXT_DECISION_batch_20260611.md
  - /root/workspace/agent_inbox/sensenova_mirofish_model_takeover_state.json

---

## 一、最终三态

**PAUSE**

生产 bridge cron 暂不恢复。

理由：bridge patch 本身已通过只读复核，但上游 B2 body_fetch / query_plan_no_body 仍是生产阻塞。恢复 bridge 生产 cron 会继续重复投喂低新鲜度、低正文覆盖率候选，业务收益不足，且会放大重复准备包与误入候选的风险。

---

## 二、bridge 是否可恢复 cron

**结论：不可恢复生产 cron。**

可接受范围：
- 可保留只读 / dry-run / 手动 smoke。
- 不宜恢复周期性生产投喂。
- 不宜写正式素材卡、INDEX、RAG。

依据：
1. GLM 复核确认 bridge patch 落地完整。
   - 9/9 hunks 完整落地。
   - 语法无误。
   - malformed title、展会文、Arrakihs、跨 run 去重、evidence_complete 修正均已覆盖。
   - 结论为 bridge patch PASS。

2. 但 CONTROLLER 与 NEXT_DECISION 均指出生产输入仍坏。
   - 三轮 run 中同一组素材反复出现。
   - 11 个 CHAPTER_PREP_ONLY 中，仅 2 个确认有效。
   - 2 个 Xinhua 仍需补证。
   - 3 个应降级 ARCHIVE。
   - 4 个重复。

3. NEXT_DECISION 明确建议：
   - bridge 生产 cron 暂停至 B2 body_fetch 修复后恢复。
   - 本批不产生正式卡。
   - 本批不改大纲 / 正文。

裁判意见：
- bridge 代码防御已足够作为下游安全阀。
- 但安全阀不能替代上游正文抓取。
- 生产 cron 的恢复条件尚未满足。

---

## 三、B2 body_fetch / query_plan_no_body 是否仍阻塞

**结论：仍阻塞。**

阻塞性质：P0，上游生产链路阻塞。

依据：
1. GLM 复核第 68-76 行判定：
   - bridge 已正确 skip `card_type == query_plan`。
   - root cause 是上游 B2 body_fetch 未对 query_plan 类候选执行确定性抓取。
   - query_plan_no_body 不属于 bridge patch 职责。

2. NEXT_DECISION 第 30-35 行判定：
   - query_plan_no_body 占 skip 约 86%。
   - 三轮 valid 仅 28 项，且多为重复。
   - 有效新素材仅 2-3 个主题。
   - 不暂停会继续重复投喂同一批候选。

3. state.json 第 9 行确认：
   - 28 valid，115 skipped。
   - query_plan_no_body 约 86%。
   - B2 body_fetch still dominant blocker。
   - Recommend pause bridge production cron。

业务判定：
- B2 仍未达到可供 bridge 生产消费的输入质量。
- bridge 防御已修，不代表 B2 可用。
- query_plan_no_body 仍是恢复 cron 前的硬阻塞。

---

## 四、允许事项与禁止事项

### 允许

1. 只读巡检。
2. 手动 dry-run smoke。
3. 用小批量真实 body_fetch 修复样本验证 bridge。
4. 对 Xinhua title_extract 做补证验证。
5. 继续审查 B2 抓取报告与 final_report。

### 禁止

1. 恢复 bridge 生产 cron。
2. 将本批 dry-run 输出转正式素材卡。
3. 写入正式 INDEX / RAG。
4. 启动 G2 / 六角色战略会议。
5. 改大纲、正文或上传线。

---

## 五、恢复条件

bridge 生产 cron 恢复需同时满足以下条件：

1. B2 body_fetch 修复完成。
   - query_plan_no_body 占比显著下降。
   - 建议门槛：连续 2 次生产形态 run 中 query_plan_no_body ≤ 30%。

2. 正文抓取有效率达标。
   - 有 Body Extract / 正文摘要 / 原文证据的候选成为主体。
   - 建议门槛：valid 候选中正文可验证项 ≥ 60%。

3. 重复投喂受控。
   - 跨 run 去重文件生效。
   - 同一 URL + title 不再连续进入 CHAPTER_PREP_ONLY。
   - 建议门槛：连续 2 次 run 中重复 CHAPTER_PREP_ONLY ≤ 10%。

4. 标题补证修复。
   - `title="article"`、数字路径标题、malformed title 不再 evidence_complete=true。
   - Xinhua app title_extract 有补证路径，或稳定降级 NEED_TITLE_RESOLVE / ARCHIVE。

5. 生产形态验收通过。
   - 不是小样 smoke。
   - 至少一次真实生产 run 输出：final_report、pipeline_state、body_fetch_report、bridge dry-run report。
   - 主控读回并确认：有效新素材不再只有 2-3 个重复主题。

满足后状态可升为：**ALLOW_WITH_GUARD**。

守护条件：
- 先恢复低频 cron 或一次性 run。
- 首轮只 dry-run，不写正式卡。
- 首轮后复核 CHAPTER_PREP_ONLY 清单。
- 若 query_plan_no_body 回升或重复投喂复发，立即回 PAUSE。

---

## 六、裁判结论

- bridge patch：PASS。
- bridge 生产 cron：PAUSE。
- B2 body_fetch / query_plan_no_body：仍阻塞。
- 当前本批产物：只可作审计参考，不可正式入库。
- 下一步：先修 B2 body_fetch，再用生产形态 run 验证；通过后再 ALLOW_WITH_GUARD 恢复 bridge。
