# NEXT_DECISION — cron_20260609_2226

- processed_at: 2026-06-10T00:15
- controller: xiaomi/mimo-v2.5

## 本轮裁决汇总

### 保留准备包（2条）

| material_id | 标题 | 证据状态 | 下一步 |
|---|---|---|---|
| 20260609_4b90b75e2e | NASA INCUS Satellites | USABLE_EXTRACT_WITH_CAVEAT | 补 NASA INCUS mission 全文 |
| 20260609_d5c878ae84 | ESA Cleaner air & prosperity | FULL_EXTRACT | 主控确认归属分类后转正式卡 |

### 降级归档（1条，bridge 原判 CHAPTER_PREP_ONLY 降为 ARCHIVE）

| material_id | 标题 | 降级理由 |
|---|---|---|
| 20260609_11f9f54468 | CCTV "2026是个什么年" | 泛化短讯+目标章已完成+2025年末展望 |

### bridge 确认归档（7条，无需变更）

全部合理，无误杀。

## OUTLINE_PATCH 判定

本轮无 OUTLINE_PATCH。不触发六角色会议。

## 主控待办

1. **INCUS 补文**：访问 `https://science.nasa.gov/mission/incus/` 抓取任务科学目标全页，评估是否值得转正式卡
2. **ESA air quality 转卡**：正文完整、数据明确、来源权威。建议归入"数据治理/算法主权"分类，写正式素材卡→INDEX→RAG。chain 标签需修正为 `earth_observation/data_governance`
3. **国内源持续空洞**：本轮国内仅1条（CCTV 旧文），2026当前国内权威源=0。body_fetch 国内链路仍需主控关注
4. **QP 骨架堆积**：55条 `query_plan_no_body` 持续复发，说明 A/B 段搜索→正文抓取链路未打通，仅产出域名+关键词骨架

## 风险提示

- ESA air quality 虽正文完整，但主题为环境监测非深空/月面，若主控不确认归属，可能长期停在准备包
- INCUS 作为 photojournal entry 内容极浅，补文后若仍无实质科学目标描述，应降级归档
- 本轮 valid=10 但实际有价值仅2条（INCUS 弱、ESA 中等），有效产出率 20%，采集质量需关注
