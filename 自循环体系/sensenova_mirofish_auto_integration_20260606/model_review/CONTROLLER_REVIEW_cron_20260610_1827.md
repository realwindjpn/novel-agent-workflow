# 控制器复核 cron_20260610_1827

- 文件名说明: 本文件为控制器接管复核(xiaomi/mimo-v2.5)，非GPT-5.5终审。历史同目录下`GPT55_REVIEW_*`文件名多为误名，实际执行模型非GPT-5.5/SharedChat。

## 运行概况
| 指标 | 值 |
|---|---|
| run_id | cron_20260610_1827 |
| valid_input_count | 2 |
| skipped_count | 67 |
| stale_domestic_blocked | 1 |
| OUTLINE_PATCH (bridge) | 2 |
| OUTLINE_PATCH (controller) | 0 (全部降级) |
| CHAPTER_PREP_ONLY | 2 |
| ARCHIVE_WITH_REASON | 0 |
| conversion_task_count | 0 |

## body_fetch 分析
- body_fetch_attempts: 12
- body_fetch_success: 2 (仅people.com.cn两张卡)
- body_fetch_fail: 7
- DOMESTIC_QUERY_PLAN_BUDGET_EXHAUSTED: 国内查询计划预算耗尽
- 国内body_fetch持续为瓶颈: 自06-08起国内源body_fetch成功率极低

## 逐卡裁决

### c64094_40722548
- bridge: OUTLINE_PATCH → controller: **CHAPTER_PREP_ONLY**
- 理由: 纯政策表态，无技术参数/工程细节/冲突变量。不满足G2会议门槛。
- 置信度: high (正文清晰，无歧义)

### c1004_40732291
- bridge: OUTLINE_PATCH → controller: **CHAPTER_PREP_ONLY**
- 理由: 博览会综述，有硬数据(飞腾SPEC 168.2、1300万片、天河太空算力)，但属聚合报道非单一突破。适合准备包积累。
- 置信度: high

### c40531_40208988 (stale)
- 旧文被时效门禁拦截，标stale_domestic_article，不进入推演
- 正确处置

### 9张NASA/ESA摘要
- summary_not_body_evidence: 摘要可用但非全文，不裁决
- Tyndall's Trail / Flight Dynamics Research Facility / Artemis III / Proba-3 / June Puzzler 等
- 若需这些素材，须主控补web_extract全文后重新投喂

### 57张query_plan_no_body
- 全部为查询骨架，无URL/无正文，正确跳过
- 覆盖: xinhuanet/cctv/stdaily/nasa/esa/darpa/defense/energy/noaa/pubmed/arxiv/mod/openalex/nature/science/ieee/bis/cnsa/cas/iop/cac等

## 关键问题

### P0: 国内body_fetch仍未恢复
自06-08以来，国内源body_fetch成功率持续接近0%。本轮12次尝试仅2次成功(均为people.com.cn)。xinhuanet/cctv/cnsa等国内官方源全部落在query_plan_no_body。根因:
- Bing/搜索引擎对国内官方站返回的URL多为频道页/首页
- body_fetch对频道页的URL→文章URL解析失败
- DOMESTIC_QUERY_PLAN_BUDGET_EXHAUSTED说明配额被无效query plan消耗

### P1: bridge OUTLINE_PATCH自动升格过宽
连续多轮cron中，people.com.cn文章被自动标为OUTLINE_PATCH，但实际多为泛政策文。建议bridge增加:
1. 正文含≥2个可量化/可写入场景的硬事实
2. 标题必须清洗(不可用URL slug)
3. 政策表态类默认CHAPTER_PREP_ONLY，除非含具体技术突破/制度冲突/国际博弈变量

### P2: 9张NASA/ESA摘要卡未处理
Artemis III/Parmitano/Proba-3等有discovery价值，但摘要不足以裁决。需主控补全文后重新投喂bridge。
