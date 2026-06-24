# MiroFish旧素材A包·二次补证清单
> 生成时间：2026-06-07
> 席别：MiroFish旧素材A包二次补证规划席
> 输入：MiMo裁决、GPT-5.5复核、Kimi-k2.6技术审
> 边界：仅输出补证计划；禁止改大纲/正文/TXT/草稿箱/git

---

## 一、三席冲突汇总

### 1.1 三态分歧矩阵

| # | 素材 | MiMo裁决 | GPT-5.5复核 | Kimi技术审 | 冲突类型 |
|---|------|---------|------------|-----------|---------|
| 2 | 量子预热化/庄子2.0 | OUTLINE_PATCH | **降级→CHAPTER_PREP** | OUTLINE_PATCH | 5.5降 vs 其余升 |
| 6 | 五角大楼AI合同 | OUTLINE_PATCH | **降级→CHAPTER_PREP** | CHAPTER_PREP | 5.5降 vs MiMo升 |
| 7/8 | 自感知人工肌肉 | CHAPTER_PREP | STRONG_CHAPTER_PREP | **OUTLINE_PATCH** | Kimi升 vs 其余守 |
| 9 | 量子百年/三支柱 | OUTLINE_PATCH | **降级→CHAPTER_PREP** | CHAPTER_PREP | 5.5降 vs MiMo升 |
| 5 | OpenAI非营利转营利 | CHAPTER_PREP | **降级→ARCHIVE** | ARCHIVE | 5.5+Kimi降 vs MiMo守 |
| 1 | 分布式工业韧性 | CHAPTER_PREP | CHAPTER_PREP | CHAPTER_PREP | **一致，但均需补证** |

### 1.2 冲突根因

- **MiMo** 偏乐观：权威源=可直接OUTLINE_PATCH，未充分考量"大纲已有近端锚点"的冗余风险。
- **GPT-5.5** 偏保守：所有素材统一降级，核心论据是"大纲已覆盖同类母题，素材只增强怎么写不改变写什么"。
- **Kimi** 偏技术结构：以"事实核硬度+技术约束力"为尺度，人工肌肉/量子预热化给到L4大纲级，但同样要求补primary参数。
- **共识区**：三条线（量子/军事AI/分布式工业）全部需要secondary补证后才能安全入库；OpenAI商业伦理素材技术增益≈0，应归档。

---

## 二、量子线补证清单（素材2+素材9）

### 2.1 素材2：量子预热化平台/"庄子2.0"

**三席分歧**：MiMo和Kimi判OUTLINE_PATCH，GPT-5.5降级为CHAPTER_PREP。
**暂不改大纲理由**：5.5指出"预热化是观测现象，不宜写成战术能力或慢放时间"；Kimi要求补Nature原文DOI和实验参数。在primary参数未落之前，大纲补丁缺乏可约束的技术边界，易导致正文写超现实。

#### 需补证据

| 优先级 | 证据类型 | 目标 | 查询词 | 入库门槛 |
|--------|---------|------|-------|---------|
| P0 | **primary** | Nature原文DOI、摘要、实验参数 | `Nature "prethermalization" "78-qubit" "Zhuangzi" 2025` / `中科院物理所 预热化 庄子2.0 Nature` | 须取得DOI号+退相干时间量级+调控精度；三要素齐全方入 |
| P1 | **official** | 中科院物理所/北大官方新闻稿全文 | `cas.cn 预热化平台` / `pku.edu.cn 量子 预热化` | 官方源确认研究团队、硬件命名、实验结论 |
| P2 | **OSINT** | 国际量子计算社区跟进报道/评论 | `Quantum Computing Report prethermalization` / `TWIML prethermal platform` | 至少1篇独立技术评论确认"可调控中间态"解读 |

#### 补证后裁决逻辑
- P0+P1 PASS → 三态升为OUTLINE_PATCH，进入G3大纲修订
- 仅P1 PASS → 保持CHAPTER_PREP，作科学红线参考
- P0 FAIL → 维持CHAPTER_PREP，不得触发大纲变动

---

### 2.2 素材9：量子百年/三支柱框架

**三席分歧**：MiMo判OUTLINE_PATCH，GPT-5.5和Kimi降级为CHAPTER_PREP。
**暂不改大纲理由**：Kimi指出"飞机比喻为科普修辞，无实验数据支撑"；5.5指出"只作背景与红线，不写量子万能"。该素材宏观可考但技术细节稀薄，不足以单独支撑大纲级技术分层。

#### 需补证据

| 优先级 | 证据类型 | 目标 | 查询词 | 入库门槛 |
|--------|---------|------|-------|---------|
| P0 | **primary** | 九章/祖冲之后继型号最新实验论文 | `arXiv "Jiuzhang" 2025 2026` / `arXiv "Zuchongzhi" quantum 2025` | 须有光量子/超导量子具体比特数、FLOPS等效、实验任务描述 |
| P1 | **official** | 国家量子科技发展战略/白皮书 | `国务院 量子科技 发展纲要` / `科技部 量子 十四五` | 官方文件明确"计算/通信/测量"三支柱表述或等价分层 |
| P2 | **OSINT** | QKD商用部署数据 | `QKD 商用部署 2025 2026 里程 网络` | 至少2个独立源交叉确认QKD实际部署规模 |

#### 补证后裁决逻辑
- P0+P1 PASS → 与素材2合并为一次量子线大纲修订（三支柱+预热化）
- 仅P1 PASS → 保持CHAPTER_PREP，作世界观时间锚点
- P0 FAIL → 归档或仅作L1氛围参考

---

## 三、军事AI线补证清单（素材6）

### 素材6：五角大楼AI合同扩张/民用大模型军用化

**三席分歧**：MiMo判OUTLINE_PATCH，GPT-5.5和Kimi判CHAPTER_PREP。
**暂不改大纲理由**：5.5指出"大纲已有184/306-307/310章覆盖军事AI合同/军民转化方向，素材只增强怎么写不改变写什么"；Kimi指出"缺一手DOD文件，签约≠实战部署"。在primary合同条款未核之前，不宜升纲。

#### 需补证据

| 优先级 | 证据类型 | 目标 | 查询词 | 入库门槛 |
|--------|---------|------|-------|---------|
| P0 | **primary** | DOD官方AI战略文件（2023-2025版） | `DOD AI Strategy 2024 2025 PDF` / `五角大楼 人工智能 战略文件` | 须取得PDF全文或官方发布页，确认AI合同框架、授权边界 |
| P1 | **official** | 具体合同公告/国会听证记录 | `FAS DOD AI contracts 2025` / `Congressional hearing AI weapons 2025` | 至少1份合同编号+签约企业+合同金额范围 |
| P2 | **OSINT** | Project Maven后继项目/贾登道(JADC2)AI整合进展 | `JADC2 AI integration 2025` / `Project Maven successor program` | 至少2个独立OSINT源确认JADC2中AI的实际授权等级 |
| P3 | **official** | 企业端公告（OpenAI/Google/Microsoft合作声明） | `OpenAI DOD partnership announcement` / `Google Pentagon AI contract` | 企业官方新闻稿或投资者关系文件 |

#### 补证后裁决逻辑
- P0+P1 PASS → 升为OUTLINE_PATCH，在军事AI线明确"政府征召民用AI"关键转折机制
- 仅P0或仅P1 PASS → 保持STRONG_CHAPTER_PREP，用于306-350章准备包
- 全部FAIL → 降级为ARCHIVE_WITH_REASON

---

## 四、分布式工业线补证清单（素材1）

### 素材1：分布式工业体系韧性与打不垮的制造网络

**三席分歧**：三席一致判CHAPTER_PREP_ONLY，一致要求补权威证据。
**暂不改大纲理由**：原始数据（70%/60%/40%/10x）全部来自C级自媒体且标注"待二次核验"；Kimi明确"数据量级可作背景参照，但不可写入精确装备损耗比/产能曲率"；5.5指出"大纲已有供应链/黑市/分布式算力线"。在primary数据未换源之前，任何大纲动作均悬空。

#### 需补证据

| 优先级 | 证据类型 | 目标 | 查询词 | 入库门槛 |
|--------|---------|------|-------|---------|
| P0 | **primary** | SIPRI军事支出/产能报告 | `SIPRI military expenditure 2025 ammunition production` | 须有导弹/无人机年度产量或库存的具体统计口径 |
| P1 | **official** | 各国国防部白皮书/军演后勤数据 | `中国国防白皮书 2025 工业` / `US DOD defense industrial base 2025` | 官方文件确认"分布式制造/工业韧性"政策表述 |
| P2 | **OSINT** | 开源卫星图像/工业热成像分析 | `Satellite imagery defense industry 2025` / `MAXAR 军工 产能` | 至少1个开源情报分析报告交叉确认产能数据量级 |
| P3 | **primary** | 自杀式无人机产量十倍增长的独立报道 | `Suicide drone production increase 2024 2025` / `FPV drone manufacturing scale` | 至少2个独立信源（非智谷趋势）确认产量增速 |

#### 补证后裁决逻辑
- P0+P1 PASS → 升为STRONG_CHAPTER_PREP，数据可直接入200-350章准备包
- 仅P0或仅P3 PASS → 保持CHAPTER_PREP，限作背景参照，禁引用具体百分比
- 全部FAIL → 降级为ARCHIVE_WITH_REASON，原C级数据不得入库

---

## 五、归档项（三席共识，无需补证）

| # | 素材 | 裁决 | 理由 |
|---|------|------|------|
| 4 | 采集日报 | ARCHIVE | 工作日志，非素材 |
| 5 | OpenAI非营利转营利 | ARCHIVE | 5.5+Kimi共识：技术增益≈0，C级自媒体缺法庭文件 |
| 10 | 硬科学阶段汇总 | ARCHIVE | 工作汇总，非素材 |

---

## 六、全局缺口与后续建议

### 6.1 信源结构偏科
三席共同指出：A包素材严重偏中科院体系，缺DOD/DARPA/北约一手文件、缺军工型号参数、缺OSINT交叉。如需写国际对抗/装备对比线，须补采Western primary来源。

### 6.2 补证优先级排序
1. **P0第一波**：量子预热化Nature DOI + DOD AI战略文件 + SIPRI产能报告（三条线各1个锚点）
2. **P1第二波**：各线官方源交叉确认
3. **P2第三波**：OSINT/社区评论补全可信度链

### 6.3 执行建议
- 量子线（素材2+9）合并为一次补证任务，避免重复采集中科院源
- 军事AI线独立补证，优先级次之（大纲306-350章近期可能进入写作窗口）
- 分布式工业线优先级最低（数据全部悬空，需换源而非补证）
- 补证任务建议派SenseNova执行（爬虫优先，禁模型裸搜），补证结果回写素材卡后触发复审

---

*补证计划完成。未修改任何大纲/正文/TXT/草稿箱/git。*
