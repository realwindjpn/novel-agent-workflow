# 控制器复核 cron_20260611_1357

- 复核模型：xiaomi/mimo-v2.5（控制器接管，非 GPT5.5）
- 复核时间：2026-06-11T14:30
- 来源 run：/root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260611_1357

---

## 一、运行摘要

| 指标 | 值 |
|---|---|
| valid_input_count | 10 |
| skipped_count | 51 |
| stale_domestic_blocked | 1 |
| OUTLINE_PATCH | 0 |
| CHAPTER_PREP_ONLY | 3 |
| ARCHIVE_WITH_REASON | 7 |
| conversion_task_count | 3 |

## 二、skip_reason_counts 分析

| skip_reason | count | 占比 | 判定 |
|---|---|---|---|
| query_plan_no_body | 43 | 84.3% | B2 链路未闭环，query_plan 无正文候选 |
| body_clean_too_short | 2 | 3.9% | 正文过短拦截（Parmitano 页） |
| low_value_policy_or_commentary | 2 | 3.9% | 低价值过滤正确 |
| stale_domestic_article | 1 | 2.0% | 时效门禁生效 |
| low_value_policy_theory_source | 1 | 2.0% | 低价值过滤正确 |
| low_value_expo_or_conference | 1 | 2.0% | 低价值过滤正确 |
| malformed_search_title | 1 | 2.0% | 畸形标题拦截正确 |

**关键观察**：query_plan_no_body 仍占绝对主导（43/51）。B2 body_fetch 链路尚未修复到产出实质正文的水平。

## 三、valid 项质量评估

### CHAPTER_PREP_ONLY (3条)

1. **Artemis III 助推器段运输** (NASA, primary)
   - 正文 868 字，事实完整（2026-06-02 发货、8段电机、75%推力）
   - 证据完整，非 stale，非摘要
   - 适合 ch156 准备包
   - **评估**: PASS，入准备包

2. **ESA ILA 2026 Day 1** (ESA, primary)
   - 正文 4196 字，含 ISOS 声明、总干事引述
   - ISOS 在轨服务声明有地缘价值
   - ILA 为展会性质，正文内容较充实但不构成制度变量
   - **评估**: PASS，入准备包，标注 ISOS 为欧洲太空主权线索

3. **Nature WGD 论文** (Nature, primary)
   - 正文 130225 字，全文级
   - 进化生物学基础研究，与科武主线因果链弱
   - 可作远期生物伦理伏笔
   - **评估**: PASS，入准备包 ch359

### ARCHIVE_WITH_REASON (7条)

- 5 条重复去重（TITLE_TOKEN_OVERLAP）：正确
- 2 条低相关性（Air Pollution + ESA Arrakihs）：正确
- **评估**: 全部归档理由成立

## 四、Bridge 门禁合规审计

| 门禁项 | 状态 |
|---|---|
| stale_domestic_blocked 生效 | ✓ 1 条被拦截 |
| query_plan 不计有效素材 | ✓ 43 条正确排除 |
| GPT55_REVIEW 命名 | ✓ 无冒充（disposition_by=deterministic_bridge） |
| Nature 正文标注 | ✓ 全文 130K 字，非摘要 |
| 畸形标题拦截 | ✓ 1 条 "c" 被拦截 |
| X-59/Supersonic 重复 | ✓ 本轮无此类条目 |

## 五、趋势观察

与上轮（cron_20260611_0856）对比：
- valid: 10 → 10（持平）
- stale_blocked: 2 → 1（下降）
- CHAPTER_PREP: 3 → 3（持平）
- query_plan_no_body: 43 → 43（持平）

**B2 body_fetch 链路无实质改善**。query_plan_no_body 持续 40+ 条，说明 B2 段生成大量 query_plan 骨架但未能完成正文抓取。这不是 bridge 问题，是 B2 runner 的 body_fetch 阶段未闭环。

## 六、裁决

- 3 条 CHAPTER_PREP_ONLY：全部 PASS，入准备包
- 7 条 ARCHIVE：全部确认
- 0 条 OUTLINE_PATCH：无需六角色会议
- bridge bug：无
- 下一步：准备包落盘，等待主控决定是否转正式素材卡
