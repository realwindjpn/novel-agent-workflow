# Next Decision: cnsa_cctv_rescue_fix_20260610

decided_at: 2026-06-11T01:30:00
decider: xiaomi/mimo-v2.5

## 状态：BLOCKED — 国内正文抓取仍为 0%

### 本次无动作项

- OUTLINE_PATCH: 0 → 无需进六角色会议
- CHAPTER_PREP_ONLY: 0 → 无准备包
- conversion_task: 0 → 无需转卡

### 累积趋势分析

连续 3 run（cron_20260610_1827 → anysearch_env_fix → cnsa_cctv_rescue_fix）：
- 国内 body_fetch_success 始终为 0
- valid_input 主要来自已抓正文的旧卡复用，非新增正文
- summary_not_body_evidence 持续出现（NASA 摘要类），说明海外源能发现但抓不到全文
- stale_domestic_blocked 每轮 1-2 条，门禁生效

### 根因排序

1. **B2 body_fetch 链路未通**：runner 对国内 official 域（people/xinhua/cctv/cnsa）的正文抓取成功率 ≈ 0%，自 06-08 以来未修复
2. **query_plan 大量无正文**：13/21 跳过项为 query_plan_no_body，说明 A 段搜索→B 段正文链路断裂
3. **NASA 海外源仅摘要**：Artemis III 相关 6 条全部 summary_not_body_evidence，web_extract 未抓到全文
4. **CNSA 专线仍不通**：CNSA content.html stale+body_fetch_fail，历史遗留

### 建议主控下一步

1. **优先修 B2 body_fetch**：不继续投 rescue run，先修 runner 的国内正文抓取链路（requests/charset/GB18030/Jina fallback/timeout）
2. **NASA 全文补抓**：Artemis III 2027 乘组分配是有价值素材，需用 web_extract 补抓全文后重新投喂
3. **暂停 rescue/smoke run**：rescue run 产出极低且消耗 quota，建议暂停直到 B2 body_fetch 修复后做验证 run

### 不做

- 不开六角色会议（无 OUTLINE_PATCH）
- 不建准备包（无 CHAPTER_PREP_ONLY）
- 不改大纲/正文/TXT
