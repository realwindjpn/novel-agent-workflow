# GLM-5.1 科学/技术顾问意见

## 诊断

采集层已抓到CAS/IOP/OpenCLI数据（审计报告证据），但**入队层断裂**是核心问题。OpenCLI 39条 added=0，去重过严+缺乏科学源专用入队通道。当前105 learned中，硬科学论文/官方原文卡极少，多数为产业会议二手信息。五条缺口方向（月球、算力、量子、生物、军事AI）的score差异巨大，生物技术仅11、军事AI为负值，说明这些方向几乎无有效素材进入。

## 科学/科普源补强方案

### 1. 源分层与入队规则

| 源 | 入队方式 | 去重阈值 | 调整理由 |
|----|----------|----------|----------|
| **arXiv** | OpenCLI `pubmed` namespace 或脚本直调 arXiv API，按五大方向关键词每周拉取 top-5 新论文 | 标题 Jaccard ≤ 0.7（当前过严，建议放宽） | 硬科学原创事实核心源；当前完全缺失 |
| **PubMed** | OpenCLI `pubmed` namespace，关键词：RNA/基因编辑/脑机接口/疫苗平台 | 同arXiv，≤ 0.7 | 生物技术缺口最大（score=11），须补 |
| **CAS（中科院）** | RSS已有抓取，但入队断裂；须在脚本中加 CAS→CARD_PENDING 直通路径，跳过通用去重 | URL精确匹配去重即可，标题模糊匹配 ≤ 0.85 | 国内权威，时事+科研双重价值 |
| **IOP（英国物理学会）** | 同CAS，RSS抓→直通入队 | URL精确匹配 | 月球/量子/深空工程核心源 |
| **OpenCLI（HN/36kr等）** | 已有通道，调松去重阈值：当前 implied threshold 过严导致39→0 | 标题 Jaccard ≤ 0.6，加关键词白名单豁免 | 产业动态+时事，是时事层主力 |

### 2. 去重阈值调整

当前问题：通用去重把科学论文标题中含共同术语（如"quantum""lunar"）的不同论文判为重复。

调整方案：
- **论文/arXiv/PubMed**：以 DOI/arXiv ID 去重，不用标题模糊匹配
- **CAS/IOP RSS**：URL精确去重，辅以 publish_date+title 组合（3天内同标题才算重复）
- **OpenCLI/36kr**：Jaccard ≤ 0.6 放行；关键词白名单命中时豁免去重
- 白名单关键词：五条缺口方向的核心术语（月球/深空/量子/芯片/生物/蜂群 等）

### 3. 验收标准

下轮cron（~16:33）后检查：

| 验收项 | 通过条件 | 检查路径 |
|--------|----------|----------|
| CAS/IOP 入队 | 新增 CARD_PENDING ≥ 2 | control_report queue_status_counts |
| OpenCLI 入队 | added > 0（非全部0） | 同上 |
| 去重率 | SKIP_DUPLICATE / total < 50%（当前 34/~170 ≈ 20%，合理；但需看入队侧） | control_report |
| 硬科学卡 | 新增卡中至少1张有 DOI/arXiv ID/官方源URL | `/知识库/*/素材卡_*.md` |
| 五方向覆盖 | 生物技术/军事AI方向 score > 0 | landing report 缺口表 |

### 4. 可执行清单

1. 脚本加 CAS/IOP RSS→CARD_PENDING 直通路径，跳过通用去重门，仅URL去重
2. arXiv/PubMed 入队：每方向每周 top-5，DOI/ID 去重，不入通用队列
3. OpenCLI 去重阈值从当前（隐含极严）放宽至 Jaccard ≤ 0.6 + 白名单豁免
4. control_report 新增 `source_breakdown` 字段：CAS/IOP/arXiv/PubMed/OpenCLI/RSS 各入队数
5. MiniMax不可用期间，Qwen3.6-plus 接管巡检（smoke已PASS）

### 5. 不做的事

- 不改正文、不改大纲
- 不重置已有105 learned记录
- 不新增采集源（只修复已有源的入队断裂）
