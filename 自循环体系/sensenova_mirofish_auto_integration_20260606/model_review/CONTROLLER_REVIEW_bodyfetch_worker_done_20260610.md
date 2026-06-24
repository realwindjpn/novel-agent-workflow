# 控制器复核报告

- run_id: bodyfetch_worker_done_20260610
- 复核时间: 2026-06-10
- 复核模型: xiaomi/mimo-v2.5（非 GPT-5.5，显式声明）
- 注意：本文件替代 GPT55_REVIEW，因未实际调用 GPT-5.5/SharedChat

## 复核范围

- 来源 run: bodyfetch_worker_done_20260610
- pipeline_state status: partial（C/E 段 SKIP_MODELS）
- B2 body_fetch: done, 3 success / 0 fail / 18 candidates
- D card_distill: done, 18 items
- valid_content_cards: 4
- query_plan_cards: 14

## 正文质量复核

### BODY_FETCHED 条目审计

| candidate_id | title | body_len | 真实正文占比 | 问题 |
|---|---|---|---|---|
| bd16a9830940c344 | Artemis III Crew | 15479 | ~30%（line 198-230 有效） | 导航噪声 197 行 |
| fb33c9ed56e20ad1 | FDRF Characteristics | 5756 | ~10% | 设施参考页，非新闻 |
| 505545fb22d75043 | Tyndall's Trail of Bergs | 10585 | ~40% | 冰川地球科学，弱相关 |

### query_plan 条目审计（14 条，全部 OFFICIAL_QUERY_PLAN/DISCOVERY_PENDING）

全部为 query_plan 骨架，无 URL、无正文。标签：
- NEED_TARGETED_ARTICLE_URL: 0（Bing 未返回有效国内文章 URL）
- query_plan_no_body: 14

**结论**：14 条 query_plan 全数空转，body_fetch 链路对国内源仍不通。

## Skip 统计

- 总候选: 18
- body_fetch 成功: 3（均为海外 NASA）
- body_fetch 未尝试: 15（limit=8 且优先海外 official）
- 国内源命中: 0

## GPT55_REVIEW 命名说明

本报告原应命名为 `GPT55_REVIEW_bodyfetch_worker_done_20260610.md`，但：
1. 未实际调用 GPT-5.5 / SharedChat / Codex CLI
2. 由 xiaomi/mimo-v2.5 在控制器接管 cron 中完成
3. 按 skill 门禁，命名为 `CONTROLLER_REVIEW_*`

建议：若需 GPT-5.5 真实复核，主控应显式 delegate 给 GPT-5.5 池（aixiaobai/byeapi/hikari/freemodel）。

## 裁决

| 项目 | 裁决 |
|---|---|
| Artemis III 卡 | CHAPTER_PREP_ONLY，可入准备包 |
| FDRF 卡 | ARCHIVE_WITH_REASON |
| Tyndall 卡 | ARCHIVE_WITH_REASON |
| Satellite Puzzler | ARCHIVE_WITH_REASON（NO_BODY） |
| 14 条 query_plan | 不进推演，留待 body_fetch 链路修复后重采 |
| body_fetch 质量 | NAV_POLLUTED，需清洗层 |
| 国内源覆盖 | FAIL，0 条国内源 |

## 下一步建议

1. body_fetch 后增加正文提取清洗（剥离 <nav>/<footer>/<sidebar> 导航噪声）
2. 国内源 query_plan→article URL 链路仍断，需修 Bing/Tavily 国内站点搜索
3. Artemis III 事实核可直接入 CHAPTER_PREP_ONLY 准备包
