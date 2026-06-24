# MiroFish Model Projection: cnsa_cctv_rescue_fix_20260610

reviewed_at: 2026-06-11T01:30:00
model: xiaomi/mimo-v2.5

## Summary

CNSA/CCTV rescue fix run 产出极低。valid_input=3，全部 ARCHIVE_WITH_REASON。无 OUTLINE_PATCH、无 CHAPTER_PREP_ONLY、无 conversion_task。

## 3 valid items

| ID | 来源 | 标题 | 裁决 | 理由 |
|---|---|---|---|---|
| 20260610_299be7638e | theory.people.com.cn | 习近平科技观（理论版） | ARCHIVE | 泛理论文，无具体科技事件/数据/突破 |
| 20260610_e628a62319 | theory.people.com.cn | 习近平科技观（理论版2025） | ARCHIVE | 同上，重复类型 |
| 20260610_1f81f6d3b3 | finance.people.com.cn | 智博会具身智能馆 | ARCHIVE | 有具身机器人/算力描述，但为展会报道，无具体技术参数或突破数据 |

Bridge 裁决正确：三条均为低科武因果链的泛政策/展会报道，归档合理。

## Skipped analysis (21 items)

- **stale_domestic_article: 1** — CNSA content.html body_fetch_fail，旧文，正确拦截
- **query_plan_no_body: 13** — 含 cnsa.gov.cn/xinhuanet.com QP骨架 + 微博/知乎/B站/HN/Reddit/X/小红书/YouTube 等 discovery QP，均无正文，正确跳过
- **summary_not_body_evidence: 6** — NASA Artemis III 相关（Marches Toward Artemis III / Luca Parmitano / Satellite Puzzler 等），仅为摘要，无全文正文
- **malformed_search_title: 1** — 标题仅为 "c"，畸形

## Pipeline state

body_fetch_success: 0, valid_content_cards: 0, card_pass_count: 0 — rescue run 未产出任何新正文抓取成功。

## 2029 Horizon projection

无素材可推演。全部归档。
