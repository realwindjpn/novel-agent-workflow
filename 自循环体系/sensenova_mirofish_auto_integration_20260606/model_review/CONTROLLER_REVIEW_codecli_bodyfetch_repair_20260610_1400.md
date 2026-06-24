# 控制器复核报告

- run_id: codecli_bodyfetch_repair_20260610_1400
- 复核时间: 2026-06-10
- 复核模型: xiaomi/mimo-v2.5（控制器接管）
- ⚠️ 非GPT-5.5/SharedChat真实复核，标注为控制器复核

## 门禁检查

### stale_domestic_blocked_count
- 值: 0
- 判定: ✅ 无旧文进入推演

### skip_reason_counts
- query_plan_no_body: 14 → 国内官方源未解析到文章URL，阻塞持续
- summary_not_body_evidence: 1 → 正确拦截摘要页

### GPT55_REVIEW 命名检查
- 本批无GPT55_REVIEW文件
- 判定: ✅ 无命名问题

### X-59/Supersonic同事件去重
- 本批无X-59相关素材
- 判定: ✅ 不适用

### Nature/截断正文
- 本批无Nature来源
- 判定: ✅ 不适用

### query_plan/无URL条目进入推演
- 14条query_plan已全部标SKIP，未进入推演
- 判定: ✅ 正确拦截

## Bridge运行质量

| 指标 | 值 | 判定 |
|---|---|---|
| valid_input_count | 3 | 偏低，国内0贡献 |
| body_fetch_success | 3/9 | 33%成功率，全为overseas |
| domestic_body_fetch | 0/14 | ❌ 持续阻塞 |
| conversion_task_count | 1 | FDRF单条 |
| 正确去重 | 1 (Artemis III) | ✅ |
| 正确归档 | 2 (Tyndall + Artemis) | ✅ |
| 正确准备包 | 1 (FDRF) | ⚠️ 增益偏低 |

## Bridge Bug检测

本批无新bridge bug。已知bug清单不变：
1. 国内body_fetch 0% — 非bridge层问题，是B2层query_plan→article URL解析失败
2. 同事件去重 — 本批无触发场景

## 风险评估

- **高风险**: 国内素材持续缺席。自06-08以来连续5+批cron零国内贡献，地缘/制度/产业轴完全空白。MiroFish推演只基于海外NASA官方源，严重偏科。
- **中风险**: FDRF规格表作为CHAPTER_PREP_ONLY候选，694字纯参数，叙事转化成本高。
- **低风险**: Artemis III去重正确，Tyndall归档正确。

## 下一步建议

1. **P0**: 主控必须恢复国内body_fetch链路。当前14条query_plan全部NEED_TARGETED_ARTICLE_URL。需修Bing搜索→国内官方站文章URL解析，或切Tavily API fallback。
2. **P1**: FDRF候选降级为ARCHIVE备查（规格表叙事价值低），或等有正文的军事测试设施新闻再合并。
3. **P2**: 验证body_fetch修复后，跑一次完整no-skip-models生产形态，确认国内BODY_FETCHED≥1。
