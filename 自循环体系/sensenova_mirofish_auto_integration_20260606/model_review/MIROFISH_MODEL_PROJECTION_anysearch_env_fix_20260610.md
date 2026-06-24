# MiroFish 模型推演 — anysearch_env_fix_20260610

run_id: anysearch_env_fix_20260610
reviewed_at: 2026-06-10T23:15:00
reviewed_by: xiaomi/mimo-v2.5（控制器复核，非GPT5.5）

## 事件摘要

anysearch 环境修复后首次验证 run。valid=7，skipped=13。out=0/CHAPTER=1/ARCHIVE=6。

## OUTLINE_PATCH 推演

本轮 bridge 标 OUTLINE_PATCH=0，控制器无追加。

## CHAPTER_PREP_ONLY 推演

### FDRF（Flight Dynamics Research Facility）
- 来源：NASA官方 https://www.nasa.gov/directorates/armd/aetc/fdrf-characteristics
- 正文：694字实际正文，含具体工程参数（20ft垂直测试段、0-117mph、雷诺数1.1×10^6/ft、主动温控79°F）
- 发布：2026-06-09
- 小说映射：ch217 军事高机动平台/风洞试验/旋翼稳定性/噪声治理
- 评估：**保留CHAPTER_PREP_ONLY**。参数具体、可写入工程细节层（风洞尺寸→飞行器旋翼回收测试→军事部署验证链）。非大纲补丁，不触发G2。
- 风险：低。NASA primary源，无争议。
- 准备包建议：可入第217章准备包，与既有"风洞测试/飞行稳定性"素材并列。

## ARCHIVE_WITH_REASON 裁决确认

| ID | 标题 | 归档理由 | 控制器裁定 |
|---|---|---|---|
| e628a62319 | c40531 40521652（people.com.cn理论频道） | 主线因果不足 | 确认归档 |
| 1f81f6d3b3 | c1004 40732291（people.com.cn财经频道） | 主线因果不足 | 确认归档 |
| 1152496bed | article（新华社客户端） | 主线因果不足 | 确认归档 |
| 574d10c292 | Tyndall's Trail of Bergs（NASA冰川） | 科武主线无关 | 确认归档 |
| 1370f40ea0 | Artemis III Mission 2027 | 已入库重复 | 确认归档 |
| 762e5caf54 | June 2026 Satellite Puzzler | 科武主线无关 | 确认归档 |

全部归档理由成立，无需追加。

## Bridge Bug 记录

1. **标题未清洗**：people.com.cn 两条卡标题为 URL slug（`c40531 40521652`、`c1004 40732291`），未从正文/网页提取真实标题。bridge title净化逻辑未覆盖此类路径模式。
2. **新华社标题同为 slug**：`article` 来自 `app.xinhuanet.com/news/article.html?articleId=...`，标题提取失败。
3. **10条 QP 无正文**：discovery query_plan（微博/知乎/B站/百度/Reddit/HN/ResetEra/Twitter/CNSA/NASA Artemis）均未走 body_fetch，全数跳过。说明 anysearch 环境修复后 B2 仍未对 discovery 源补正文。

## 趋势

- valid_input 持续低位：06-08起 7→9→10→7→10→10→12→6→10→10→**7**（本轮）
- query_plan_no_body 占绝对多数：本轮59条（=skipped总量-2 stale-1 malformed），是主瓶颈
- stale_domestic_article 正确拦截2条
- domestic body_fetch 依然近零（自06-08起），主线国内源缺席

## 结论

- OUTLINE_PATCH：0，不触发G2
- CHAPTER_PREP_ONLY：1（FDRF），入准备包
- ARCHIVE：6，全部确认
- 不写正式素材卡、不改大纲/正文/TXT
