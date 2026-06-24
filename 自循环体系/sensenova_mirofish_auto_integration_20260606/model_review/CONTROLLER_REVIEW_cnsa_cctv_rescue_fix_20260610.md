# Controller Review: cnsa_cctv_rescue_fix_20260610

reviewed_at: 2026-06-11T01:30:00
reviewer: xiaomi/mimo-v2.5 (controller takeover, NOT GPT-5.5)
is_gpt55_review: false

## 裁决：BRIDGE 裁决正确，全部归档确认

### ARCHIVE_WITH_REASON × 3

1. **c40531_40706201** (theory.people.com.cn 2026-04-22) — 习近平科技自立自强论述。泛理论文，无具体事件/数据/技术突破。归档正确。
2. **c40531_40521652** (theory.people.com.cn 2025-07-15) — 同类型理论文，且为2025年旧文。归档正确。
3. **c1004_40732291** (finance.people.com.cn 2026-06-02) — 智博会具身智能馆报道。有"150多种具身机器人""算力/芯片/操作系统系统性突破"等描述，但为展会新闻，无具体技术参数/工程数据/竞争格局。对科武主线（算力主权/地月争夺/群体智能）因果链不足。归档正确。

### 拦截项审计

- **stale_domestic_blocked: 1** — CNSA content.html，body_fetch_fail，旧文。正确拦截。
- **summary_not_body_evidence: 6** — NASA Artemis III 相关文章，仅有摘要/标题，无全文正文。正确跳过。这些文章（Artemis III 2027任务进展、Luca Parmitano入选乘组等）本身有科武价值，但缺正文不可进入素材卡。
- **malformed_search_title: 1** — 标题 "c"，畸形，正确跳过。
- **query_plan_no_body: 13** — 含 QP 骨架与 discovery 模板，均无正文。正确跳过。

### Bridge bugs

本 run 无 bridge bug。Slug 标题问题已在前次 review 中记录（people.com.cn 系列），本 run 未新增。

### Body fetch 状态

rescue run body_fetch_success=0。国内源正文抓取仍为 0%，与前次趋势一致。该 rescue fix 未能改善正文抓取链路。

### 指数：有效输入持续低位

| run | valid | stale_blocked | OUTLINE_PATCH | CHAPTER_PREP |
|---|---|---|---|---|
| cron_20260610_1827 | 2 | 1 | 2 | 0 |
| anysearch_env_fix | 7 | 2 | 0 | 1 |
| cnsa_cctv_rescue_fix | 3 | 1 | 0 | 0 |

有效输入从 7→3，分母缩小（24→3候选），说明 rescue run 产出更少。
