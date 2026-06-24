# MiroFish 模型推演裁决 — cron_20260610_0826

- 裁决者：xiaomi/mimo-v2.5（控制器接管，非GPT-5.5/SharedChat）
- 裁决时间：2026-06-10
- 事件来源：`/root/workspace/agent_inbox/sensenova_mirofish_bridge_events.jsonl` line 30

## 总览

| 指标 | 值 |
|---|---|
| valid_input_count | 6 |
| skipped_count | 59 |
| skip_reason_counts | query_plan_no_body=59 |
| stale_domestic_blocked_count | 0 |
| OUTLINE_PATCH | 1 |
| CHAPTER_PREP_ONLY | 2 |
| ARCHIVE_WITH_REASON | 3 |
| conversion_task_count | 2 |

## 跳过原因分析

全部59项跳过原因为 `query_plan_no_body`：均为官方域查询骨架（QP skeleton），未完成正文抓取。
国内源（people/xinhua/cctv/guancha/huanqiu/miit/mod/most/cnsa/cas/cac）+ 海外源（nasa/esa/darpa/defense/energy/noaa/nih/pubmed/arxiv/openalex/nature/science/ieee/bis/semiconductors）+ discovery（微博/知乎/B站/百度/小红书/Twitter/Reddit/HN/ResetEra/YouTube/Discord）全部停留在查询计划阶段。

**body_fetch 链路仍未打通**：59项 QP 骨架无正文，比上一轮（cron_20260610_0326）的55项还多4项。问题持续恶化。

## 逐项裁决

### 1. OUTLINE_PATCH: 量子纠缠如何催生全新技术革命（央视网/新华网）

| 字段 | 值 |
|---|---|
| material_id | 20260610_195de60a7d |
| source_url | https://news.cctv.com/2026/06/09/ARTI66SdPwygxOMuFMkEyHVi260609.shtml |
| source | 央视网（新华网供稿），2026-06-09 |
| body_len | 346 |
| evidence_complete | true（bridge标记） |
| bridge disposition | OUTLINE_PATCH → ch95 |
| bridge reason | 算法/算力/技术主权主线直接相关 |

**控制器裁决：REJECT OUTLINE_PATCH → ARCHIVE**

理由：
1. **正文未抓取**：body仅346字符，全部为页面导航/页脚/编辑信息，无实际文章内容。AI Distill自身也写明"正文未有效提取，仅捕获页面框架（导航/页脚），无实际文章内容。需重新抓取或补充正文。"
2. **bridge evidence_complete 误标**：346字符导航污染体不应标 `evidence_complete=true`。这是 bridge bug。
3. **无事实核**：标题"量子纠缠如何催生全新技术革命"为科普标题，但无正文则无任何可核事实（无量子比特数、无保真度、无实验结果、无应用场景细节）。
4. **现有量子素材已充足**：时事INDEX已有九章四号(2026-05-14)、量子比特可移动(2026-05-10)、量子先存后解(2026-05-07)、本源悟空180(2026-05-13)、DI-QKD 62英里(2026-05-18)、QKD中继(2026-05-19)等正式卡。知识库量子计算线已有多张深度卡。
5. **主控行动**：若该选题有价值，应从新华网原始链接重抓正文（`https://www.news.cn/...`），确认有实际科普内容后再评估是否入卡。不可以在无正文时写大纲补丁。

**现有素材对照**：
- 九章四号：1024压缩态/8176模式/3050光子/25微秒 vs 10^42年 → 已有深度工程细节
- 量子比特可移动：代尔夫特/QuTech → 已有
- 本源悟空180：量子算力服务化 → 已有
- 当前卡仅标题级线索，不构成增量

### 2. CHAPTER_PREP_ONLY → ARCHIVE: Flight Dynamics Research Facility

| 字段 | 值 |
|---|---|
| material_id | 20260610_7b087574f8 |
| source_url | https://www.nasa.gov/directorates/armd/aetc/fdrf-characteristics |
| body_len | 5758 |
| bridge target_chapter | 217 |
| bridge reason | 高机动平台与感知/噪声治理可作军事制度细节层 |

**控制器裁决：DOWNGRADE CHAPTER_PREP_ONLY → ARCHIVE**

理由：
1. **正文导航污染**：body 5758字符中绝大部分为NASA网站导航菜单（新闻、图片、视频、任务列表、教育等），有效设施描述仅约5行。
2. **内容与小说无增量**：FDRF是NASA大型亚音速风洞，用于大气层飞行器的稳定性/可控性/螺旋测试。这不是高机动平台（无人机/外骨骼/群体智能），而是传统风洞设施。
3. **ch217映射不成立**："高机动平台与感知/噪声治理"与"亚音速风洞飞行器稳定性测试"无因果链。
4. **无工程细节**：无风速数据、无测试结果、无失败模式、无成本约束。5行设施描述不足以支撑章节素材。
5. **与上一轮类似**：上一轮（cron_20260610_0326）已将"NASA Mass Distribution"降级为ARCHIVE，理由同为"nav-polluted body, K-8 content, no engineering substance"。

### 3. CHAPTER_PREP_ONLY → ARCHIVE: NASA Knows: What Is Mass Distribution?

| 字段 | 值 |
|---|---|
| material_id | 20260610_eaecde5dae |
| source_url | https://www.nasa.gov/learning-resources/nasa-knows-what-is-mass-distribution |
| body_len | 8741 |
| bridge target_chapter | 156 |
| bridge reason | 地月/深空/通信链路素材 |

**控制器裁决：DOWNGRADE CHAPTER_PREP_ONLY → ARCHIVE**

理由：
1. **K-8教育内容**：明确标注"for students grades 5-8"，为NASA基础科学教育页。
2. **通用概念**：质量分布是基础物理概念（星系形态→飞机设计→行星自转），无任何深空/地月/通信链路特定工程内容。
3. **ch156映射错误**：ch156为"重返月球"，需要的是月面工程/地月转移轨道/深空通信延迟等具体数据。"质量分布是什么"是中学物理概念，不构成章节素材。
4. **正文导航污染**：8741字符中绝大部分为NASA网站导航，有效科普内容仅约300字符。
5. **与上一轮完全一致**：上一轮`cron_20260610_0326`已有`20260610_eaecde5dae`被降级。本轮同一素材卡ID重复出现，说明 bridge 未正确去重跨 run 的同一候选。

### 4-6. ARCHIVE 确认

| material_id | title | 理由 | 裁决 |
|---|---|---|---|
| 20260610_1370f40ea0 | NASA Marches Toward Artemis III | TITLE_TOKEN_OVERLAP | ✅ ARCHIVE 确认 |
| 20260610_762e5caf54 | June 2026 Satellite Puzzler | low_kewu_relevance | ✅ ARCHIVE 确认 |
| 20260610_752009b549 | AI technology must serve human cognitive development (Nature) | TITLE_TOKEN_OVERLAP | ✅ ARCHIVE 确认 |

## Bridge Bug 汇总

| # | Bug | 严重度 | 建议 |
|---|---|---|---|
| 1 | 量子纠缠CCTV卡body仅346字符导航污染，bridge标 `evidence_complete=true` 并产出 `OUTLINE_PATCH` | **高** | body_len < 500 且含"返回首页/京ICP/加载更多"等导航关键词时，必须标 `NAV_POLLUTED` 并拒绝 OUTLINE_PATCH |
| 2 | FDRF卡body含大量导航污染但被标为 evidence_complete | 中 | 同上，有效内容占比 < 20% 时不应标 evidence_complete |
| 3 | Mass Distribution 卡跨 run 重复出现（同一 material_id） | 中 | bridge 应维护 processed material_id set，跨 run 去重 |
| 4 | 59项 QP 骨架无正文，body_fetch 链路持续阻塞 | **高** | 非 bridge bug，而是 runner B2 body_fetch 未打通 |

## 汇总

| 类别 | 数量 | 说明 |
|---|---|---|
| bridge产出有效裁决 | 0/6 | 全部降级或确认归档 |
| 新增 OUTLINE_PATCH | 0 | 量子纠缠→ARCHIVE（无正文） |
| 新增 CHAPTER_PREP_ONLY | 0 | FDRF→ARCHIVE, Mass Distribution→ARCHIVE |
| ARCHIVE 确认 | 6/6 | 含3项bridge原判+3项降级 |
| bridge bug | 2（高） | evidence_complete误标、跨run未去重 |
| QP骨架积压 | 59 | body_fetch链路持续阻塞 |
