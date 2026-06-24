# 控制器复核报告

- run_id: cron_20260610_0326
- 复核时间: 2026-06-10
- 复核模型: xiaomi/mimo-v2.5（非 GPT-5.5，显式声明）
- 注意：本文件替代 GPT55_REVIEW，因未实际调用 GPT-5.5/SharedChat

## 复核范围

- 来源 run: cron_20260610_0326
- pipeline_state status: done（skip_models=false，全链路）
- B2 body_fetch: done, 15 success / 20 fail
- D card_distill: done, 71 items（12 DISTILLED, 59 query_plan）
- valid_content_cards: 12
- query_plan_cards: 55
- 国内源覆盖: 0% 功能

## 正文质量复核

### BODY_FETCHED 条目审计（12 条 DISTILLED）

| candidate_id | 标题 | body_len | 真实正文占比 | 问题 |
|---|---|---|---|---|
| bd16a9830940c344 | Artemis III crew (NASA press release) | 15479 | ~30% | 导航噪声 197 行 |
| 080248b6fa436508 | Artemis III crew (ESA video) | 2058 | ~60% | 尚可 |
| 96a965cfd442a260 | ESA astronaut joins Artemis III | ~2000 | ~50% | 同事件 |
| f17ffd1d4c23f97a | Luca Parmitano selection | ~2000 | ~50% | 同事件 |
| 47dd5a478d610c6e | Satellite Puzzler | ~1000 | ~40% | 科普谜题 |
| 22d1dad4c90cc3b1 | SF Metropolitan Mosaic | ~3000 | ~50% | ISS 遥感 |
| 070e855ce20d114e | NASA Knows Mass Distribution | ~2000 | ~40% | 教育页 |
| 421b353d2470790c | NASA & FIFA World | ~5000 | ~40% | 科普 |
| 2636f97a8755fe93 | Proba-3 recovery | 3659 | ~70% | **质量最高** |
| 2026*70433572ee597d1c | 2026是个什么年 | 461 | ~80% | 旧文(2025-12-30) |
| 1bb253789f966629 | Cleaner air | 6977 | ~60% | 地球科学 |
| 04821ed1be746e88 | AI technology (Nature) | 0 | 0% | **body_fetch FAIL** |

### query_plan 条目审计（55 条）

全部为 query_plan 骨架。标签：
- OFFICIAL_QUERY_PLAN: 多数（people.com.cn / xinhuanet.com / cnsa.gov.cn 等）
- DISCOVERY_PENDING: 微博/知乎/B站/百度/Reddit/HN 等
- query_plan_no_body: 59

**结论**：55 条 query_plan 全数空转。国内源 body_fetch 链路仍 0% 通。

## Skip 统计

| 项目 | 数量 |
|------|------|
| 总候选 | 71 |
| DISTILLED | 12 |
| query_plan（无正文） | 59 |
| body_fetch 成功 | 15（全部海外 NASA/ESA） |
| body_fetch 失败 | 20 |
| 国内源命中 | 0 |
| duplicate_skip_count | 4 |

## 三态裁决复核

### Bridge 裁决 vs 控制器裁决

| 条目 | Bridge 裁决 | 控制器裁决 | 差异 |
|------|-------------|------------|------|
| Artemis III crew (ESA) | CHAPTER_PREP_ONLY | CHAPTER_PREP_ONLY | 一致 |
| Proba-3 recovery | CHAPTER_PREP_ONLY | CHAPTER_PREP_ONLY（降级风险） | 控制器建议降级 |
| 2026是个什么年 | CHAPTER_PREP_ONLY | **ARCHIVE** | 旧文+泛概述 |
| NASA Knows Mass Dist. | CHAPTER_PREP_ONLY | **ARCHIVE** | 教育页无进展 |
| Nature AI letter | ARCHIVE | ARCHIVE | 一致（无正文） |
| 其余 7 条 | ARCHIVE | ARCHIVE | 一致 |

### Bridge Bug 汇总

1. **Nature AI card body_len=0 仍被 DISTILLED**：应直接 ARCHIVE
2. **CCTV 旧文(2025-12-30)未被时效门禁拦截**：stale_domestic_blocked=0，门禁漏判
3. **Artemis III 同事件三卡未去重**：需事件签名 `SAME_EVENT_ARTEMIS_III_CREW_ANNOUNCEMENT_20260609`

## GPT55_REVIEW 命名说明

本报告原应命名为 `GPT55_REVIEW_cron_20260610_0326.md`，但：
1. 未实际调用 GPT-5.5 / SharedChat / Codex CLI
2. 由 xiaomi/mimo-v2.5 在控制器接管 cron 中完成
3. 按 skill 门禁，命名为 `CONTROLLER_REVIEW_*`

建议：若需 GPT-5.5 真实复核，主控应显式 delegate 给 GPT-5.5 池。

## 裁决

| 项目 | 裁决 |
|------|------|
| 有效 CHAPTER_PREP_ONLY | 2 条（Artemis III crew + Proba-3） |
| 应降级为 ARCHIVE | 2 条（CCTV 旧文 + NASA 教育页） |
| 已 ARCHIVE | 8 条 |
| 国内源覆盖 | FAIL |
| body_fetch 质量 | NAV_POLLUTED（需清洗层） |
| 推演总量 | 有效可准备包候选 2 条 |
