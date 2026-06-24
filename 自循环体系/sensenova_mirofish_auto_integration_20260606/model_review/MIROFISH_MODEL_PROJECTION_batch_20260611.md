# MiroFish 模型推演报告（批量合并）

报告时间：2026-06-11T15:00:00
模型：xiaomi/mimo-v2.5（控制器复核，非 GPT-5.5）
覆盖事件：cron_20260611_0356 / cron_20260611_0856 / bodyfetch_rootfix_smoke_20260611

## 一、总览

| run_id | valid | skipped | stale_blocked | OUTLINE_PATCH | CHAPTER_PREP_ONLY | ARCHIVE |
|---|---|---|---|---|---|---|
| cron_20260611_0356 | 10 | 48 | 1 | 0 | 6 | 4 |
| cron_20260611_0856 | 10 | 50 | 2 | 0 | 3 | 7 |
| bodyfetch_rootfix_smoke_20260611 | 8 | 17 | 1 | 0 | 2 | 6 |
| **合计** | **28** | **115** | **4** | **0** | **11** | **17** |

## 二、skip_reason 分析

三轮累计 115 项被跳过，主因：
- `query_plan_no_body`：~137 项（占 ~86%）— B2 body_fetch 持续产出无正文候选
- `stale_domestic_article`：4 项 — 旧文拦截机制生效
- `body_clean_too_short`：5 项 — 正文不足
- `low_value_expo_or_conference`：4 项 — 展会/博览会软文
- `low_value_policy_theory_source`：3 项 — 纯政策理论
- `low_value_policy_or_commentary`：4 项 — 政策评论
- `malformed_search_title`：4 项 — 标题畸形（如 "c64094 40722548"）
- `http_403|jina_timeout`：2 项 — 抓取失败
- `duplicate_within_run`：多处 — 批内去重生效

**核心问题**：query_plan_no_body 仍占压倒性多数。B2 body_fetch 链路虽经多轮修复，生产 cron 仍未产出实质正文。

## 三、CHAPTER_PREP_ONLY 逐条裁决

### 1. Artemis III Booster Segments 运输（NASA 官方）
- URL：https://www.nasa.gov/image-article/train-ride-to-nasa-kennedy-for-artemis-iii-booster-segments
- 裁决：**CHAPTER_PREP_ONLY → 准备包** ch156
- 理由：NASA 官方图+文，Artemis III 助推器段铁路运输至肯尼迪航天中心。属地月/深空基础设施，可作 ch156 工程细节。
- 证据状态：evidence_complete=true，non-duplicate
- **控制器意见**：有价值，但属工程进度通报，非技术突破。进入 ch156 准备包即可，不升 OUTLINE_PATCH。需主控确认是否有 2026 年中 Artemis III 时间线更新。

### 2. ESA at ILA 2026 Day 1 Highlights
- URL：https://www.esa.int/About_Us/Corporate_news/ESA_at_ILA_2026_Day_1_highlights
- 裁决：**CHAPTER_PREP_ONLY → 边界候选** ch156
- 理由：ILA 2026 航展 ESA 亮点，含欧空局防务/航天展示。但 ILA 属商业航展，kewu_relevance 低。
- **控制器意见**：bridge 标为 CHAPTER_PREP_ONLY 偏宽松。实际为展会亮点汇总，缺乏具体技术突破证据。降级为 **ARCHIVE（低增益展会文）**。若后续从 ILA 提取到具体 ESA 技术进展（如可重复使用上面级、在轨服务），可重新评估。

### 3. ESA adopts galactic archaeology mission Arrakihs
- URL：https://www.esa.int/Science_Exploration/Space_Science/ESA_adopts_galactic_archaeology_mission_Arrakihs
- 裁决：**CHAPTER_PREP_ONLY → 边界候选** ch156
- 理由：ESA 采纳银河考古任务 Arrakihs。恒星演化/银河考古属纯基础科学，与当前算法主权/地月争夺/群体智能主线关联弱。
- **控制器意见**：bridge 标 CHAPTER_PREP_ONLY 偏宽松。银河考古任务 2026 采纳是天文界事件，但与《科武纪元》300 章内主线因果链不足。降级为 **ARCHIVE（低小说增益基础科学）**。除非后续发现该任务涉及太空主权/深空通信竞争，否则不进准备包。

### 4. Nature WGD — Whole-genome duplication shaped cell-type evolution
- URL：https://www.nature.com/articles/s41586-026-10629-x
- 裁决：**CHAPTER_PREP_ONLY → 准备包** ch359
- 理由：Nature 2026 论文，全基因组复制塑造脊椎动物脑细胞类型进化。属生物伦理/人才争夺/科研治理变量。
- 证据状态：evidence_complete=true，non-duplicate
- **控制器意见**：Nature 论文，质量高。WGD 与神经进化/脑科学相关，可作 ch359（生物伦理/基因治理）准备包候选。但须注意：Nature 正文可能为摘要/截断，必须标 `USABLE_EXTRACT_WITH_CAVEAT`，不得称全文归档。进入 ch359 准备包。

### 5. cpc.people.com.cn — "c64094 40722548"
- URL：https://cpc.people.com.cn/n1/2026/0519/c64094-40722548.html
- 裁决：**CHAPTER_PREP_ONLY → 降级** 
- 理由：标题为 URL 路径片段（"c64094 40722548"），malformed_search_title。内容可能是政策框架/制度文本。
- **控制器意见**：标题畸形，bridge 判为 CHAPTER_PREP_ONLY 不合理。降级为 **ARCHIVE（malformed_title + 低增益政策文）**。主控需查看原文卡确认是否为有价值的制度素材；如需保留，须先净化标题并标 primary content type。

### 6. 新华社 article（articleId=2026053045842f8efb...）
- URL：https://app.xinhuanet.com/news/article.html?articleId=2026053045842f8efb86497b9ab4d3ca90d7425a
- 裁决：**CHAPTER_PREP_ONLY → 需补证**
- 理由：新华社客户端文章，标题为 "article"（抓取失败导致标题未获取）。
- **控制器意见**：新华社客户端 URL 带 articleId，为有效国内官方源。但标题 "article" 说明正文解析失败或标题提取失败。bridge 标 evidence_complete=true 不可信——标题为 "article" 说明正文质量存疑。标记为 **NEED_TITLE_RESOLVE**，主控须重新抓取或浏览器访问确认内容后再决定。

### 7. 新华社 article（articleId=ff4dd8219220db...）
- URL：https://app.xinhuanet.com/news/article.html?articleId=ff4dd8219220db43267c6724ec97e17f
- 裁决：**CHAPTER_PREP_ONLY → 需补证**
- 理由：同上，标题为 "article"。
- **控制器意见**：同 6，标记 **NEED_TITLE_RESOLVE**。

## 四、ARCHIVE 确认（17 项）

以下 ARCHIVE 理由确认无误：
- Curiosity Blog Sols 4913-4919：火星车日常日志，TITLE_TOKEN_OVERLAP。归档 ✓
- NASA Construction Services Contract：行政合同，TITLE_TOKEN_OVERLAP。归档 ✓
- NASA/NOAA Joint Session：会议预告，TITLE_TOKEN_OVERLAP。归档 ✓
- NASA Robotic Intelligence Spinoff：技术转化，TITLE_TOKEN_OVERLAP。归档 ✓
- ESA astronaut Parmitano Artemis III：人员任命，TITLE_TOKEN_OVERLAP。归档 ✓
- Air Pollution Daily Pulse：环保数据，低 kewu_relevance。归档 ✓

## 五、OUTLINE_PATCH 评估

三轮合计 0 个 OUTLINE_PATCH。bridge 裁决正确：
- 无素材达到大纲补丁门槛
- 所有有效候选均为 CHAPTER_PREP_ONLY 或更低
- **无需发起六角色会议**

## 六、Bridge Bug 检查

1. **malformed_title 未拦截**："c64094 40722548" 和 "article" 标题应被 bridge 拦截为 malformed_search_title 或需 resolve_title，但实际进入了 CHAPTER_PREP_ONLY。bridge bug：标题质量门禁不足。
2. **evidence_complete 标记不可信**：标题为 "article" 的条目标 evidence_complete=true，实际标题未解析。bridge bug：evidence_complete 不应仅看 body_hash 存在。
3. **ILA/Arrakihs 宽松裁决**：展会亮点和纯基础科学不应进 CHAPTER_PREP_ONLY，bridge kewu_relevance 门禁偏松。

## 七、系统性问题

### B2 body_fetch 持续阻塞
- query_plan_no_body 仍占 skip 原因 ~86%
- 三轮 valid 总计仅 28 项，且多为重复候选
- 有效新素材集中在 3 个主题（Artemis III booster、WGD Nature、Xinhua 待确认）
- **建议**：暂停 bridge 生产 cron，优先修复 B2 body_fetch 确定性抓取链路

### 旧文拦截
- stale_domestic_blocked=4，拦截机制正常工作
- 被拦截旧文不得进入推演/准备包

### 标题畸形
- 4 项 malformed_search_title，其中 2 项（cpc.people.com.cn）漏入 CHAPTER_PREP_ONLY
- 新华社 "article" 标题说明 body_fetch 成功但 title_extract 失败
