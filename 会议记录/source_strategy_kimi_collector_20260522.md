# 科武纪元素材源策略会议·采集工程顾问报告

> 角色：采集工程顾问（只读不改）  
> 日期：2026-05-22  
> 依据：`sensenova_daily_kewu_learning.py`、`orchestrator_v3.py`、`时事素材/INDEX.md`、当日`control_report`与`current_events_hotlist.json`

---

## 一、最稳采集源Top10

按"历史入库转化率 × 自动化稳定性 × 对小说直接帮助"排序。

| 排名 | 源 | 类型 | 核心价值 | 历史入库案例 |
|---|---|---|---|---|
| 1 | **DefenseNews** | 军事新闻RSS | 军事AI/蜂群/采购/制度摩擦/盟友协同 | 无人机训练、容器化导弹、反蜂群、NATO供应商池、Aselsan |
| 2 | **ArsTechnica** | 科技新闻RSS | 深空工程/算力监管/开源治理/军事技术 | Skydweller太阳能无人机、xAI燃气轮机、俄罗斯无人机动员、旅行者号 |
| 3 | **NewScientist** | 科学新闻RSS | 量子计算/生物技术/深空推进/AI安全 | 量子分子模拟、NHS源代码、光帆metajets、九章四号 |
| 4 | **TechCrunch**（科技政策/基础设施子集） | 科技新闻RSS | 算力资本/机器人/数据隐私/供应链安全 | Config机器人、Anduril融资、NYC Health泄露、富士康勒索软件 |
| 5 | **Reuters/AP/BBC**（政治/科技子集） | 通讯社RSS | 地缘政治/芯片主权/台海/霍尔木兹/中美谈判 | 中美元首峰会、H200交付、Barakah核电站、台湾军售 |
| 6 | **Nature + arXiv（quant-ph/cs.CR/cs.MA）** | 学术OpenCLI | 量子纠错/生物安全/后量子密码/蜂群算法 | DI-QKD、连续变量量子纠错、基因编辑脱靶 |
| 7 | **NASA NTRS / TechPort / 中科院官网** | 机构报告/官网 | 深空工程硬核参数（辐射、ISRU、推进、能源） | 月球核反应堆MOU、火星ISRU、50MeV质子微束、旅行者号 |
| 8 | **中科院物理所/中国科学报** | 中文科普/科研进展 | 核聚变/量子/芯片/材料（中文场景可直接化用） | EAST亿度千秒、悟空卫星、拓扑绝缘体、存算一体 |
| 9 | **B站字幕（差评君/军事科普/航天科普）** | 视频字幕 | 科普口径/武器原理/历史案例（适合作者角色训练） | 反导系统、单兵外骨骼、FAST深空信号 |
| 10 | **SpaceNews / IEEE Spectrum**（航天/政策子集） | 行业媒体RSS | 卫星/发射市场/太空政策/6G/频谱 | 星链竞争、太空碎片、频谱争夺 |

**Top10之外，以下源降级为P2补充，不纳入自动主路径**：
- 36kr：产业大会/投融资稿占比过高，今日7条被`strong_negative:产业大会`命中，0入库。
- ESA/NASA Breaking News（纯PR类）：需二级过滤，否则大量人事/教育/地球观测/奖项混入。
- ScienceDaily：医学/生物/心理学泛科学占比高，需关键词加权后少量采用。
- 观察者网专栏：政治敏感度高，质量不稳，改为人动手动触发。

---

## 二、自动化难度

| 源 | 难度 | 瓶颈 | 建议 |
|---|---|---|---|
| DefenseNews | 低 | RSS稳定，正文无paywall | urllib直接抓RSS+正文，无需浏览器 |
| ArsTechnica | 低 | RSS稳定，正文无paywall | 同上 |
| NewScientist | 低 | RSS稳定，部分摘要需点入 | RSS标题+摘要已够初筛；正文轻量抓取 |
| TechCrunch | 低 | 正文无paywall，但噪声高 | RSS+正文易抓，**难点在过滤规则** |
| Reuters/AP/BBC | 低 | RSS稳定 | 英文RSS标准化高，直接解析 |
| Nature/arXiv | 中 | 学术语言/摘要页/有时PDF | OpenCLI已接arxiv；Nature用RSS摘要+DOI链接 |
| NASA NTRS/中科院 | 中 | PDF多/中文页面结构不一 | NTRS识别PDF直链；中科院用urllib正则兜底+crawl4ai |
| 物理所 | 中 | 页面需JS/crawl4ai | 保持现有crawl4ai+urllib双轨 |
| B站字幕 | 中 | 需cookie/API+字幕下载 | 现有逻辑成熟，维持 |
| SpaceNews/IEEE | 低-中 | RSS偶有不稳定 | urllib RSS，失败重试即可 |
| 微信公众号 | 高 | 需用户转发链接/二维码/cookie | **不可全自动**，维持"用户转发→脚本直抓"模式 |

**总体判断**：80%有价值的内容可通过RSS+urllib+OpenCLI低成本自动化获取，仅20%（中科院部分栏目、物理所、微信）需要浏览器/复杂解析。

---

## 三、噪声/敏感风险

### 3.1 噪声分级

| 风险等级 | 源/类型 | 表现 | 对策 |
|---|---|---|---|
| 🔴 **高** | 36kr产业大会稿 | "AI Partner·产业大会""圆桌对话""场景新实践" | **已入strong_negative，维持降级** |
| 🔴 **高** | TechCrunch融资/产品发布 | "X raises $Y""Z launches W""startup" | 新增strong_negative：`"raises $""seed round""Series A"`（但保留含"defense""AI safety""space"的投融资） |
| 🔴 **高** | NASA/ESA PR稿 | "Telly Awards""deputy administrator""FIRST Robotics""Earth from Space" | **增加二级过滤**：标题无`moon/Mars/Artemis/rocket/spacecraft/launch/technology/mission`直接skip |
| 🟡 **中** | ScienceDaily泛科学 | 恐龙、心理学、古生物、普通医学 | 按CATEGORY_KEYWORDS加权，无命中则low_priority |
| 🟡 **中** | IEEE Spectrum消费电子 | 手机/5G消费级应用/汽车电子 | 标题命中`smartphone/5G consumer/EV charging`等入negative |
| 🟡 **中** | B站热门 | 娱乐/游戏/生活区混杂 | 维持现有keyword筛选，不扩量 |
| 🟢 **低** | DefenseNews/Ars/NewScientist | 偶有娱乐跨界（如Top Gun 40周年） | strong_negative已覆盖，维持 |

### 3.2 敏感风险（合规/安全）

| 风险类型 | 来源 | 说明 | 对策 |
|---|---|---|---|
| **财经敏感** | 36kr、TechCrunch融资版、Reuters财经 | 股市/IPO/财报/估值对小说帮助小，且可能触发审查 | 过滤词见上；入库素材卡避免直接引用股价/市值数据 |
| **政治敏感** | 观察者网、部分台海/南海报道 | 涉政表述需与小说"技术-制度"叙事分离 | 素材卡只提取"制度摩擦/规则制定/采购流程"等技术政治面，不摘立场性评论 |
| **军事敏感** | DefenseNews部分涉华报道 | 客观报道可采，但需避免直接复制涉密细节或攻击性表述 | 只采公开采购/训练/制度/演习框架，不采具体部署坐标/未公开参数 |
| **生物安全敏感** | 基因编辑/合成生物学/病毒 | 小说需要但平台可能审查 | 素材卡使用学术表述（"脱靶检测""双重用途研究"），避免惊悚化 |

### 3.3 过滤规则补丁建议（给sensenova脚本）

基于今日`current_events_hotlist`数据（62条候选，29条skip，14条low_priority，0条added），过滤效率尚可，但仍有优化空间：

```
RELEVANCE_STRONG_NEGATIVE 追加：
  - "raises $" , "seed round" , "Series A" , "Series B" , "funding round"
  - "deputy administrator" , "telly award" , "FIRST Robotics"（NASA PR）
  - "earth observatory" , "earth from space"（除非命中moon/Mars）
  
NASA/ESA专用二级过滤（标题无以下词→skip）：
  - moon, lunar, Mars, Artemis, spacecraft, rocket, launch, propulsion,
  - technology demonstration, mission, exploration, habitation, ISRU
```

---

## 四、最小脚本策略

### 4.1 当前架构问题

现有两条线并行：
- `sensenova_daily_kewu_learning.py`（1567行）：计划+书单+采集+过滤+模型调用+归档+报告，过于臃肿
- `orchestrator_v3.py`（707行）：另一套采集实现，与前者产物未自动打通

**问题**：职责混杂、代码重复、维护成本高、一个模块故障拖垮全流程。

### 4.2 最小化重构建议（三件套）

不强制立即重构，但后续迭代应按此方向拆分：

#### A. `collector_mini.py` — 纯采集，无模型调用
职责：只输出候选JSON，不做任何智能判断。

```
输入：源配置（RSS列表、OpenCLI站点、关键词）
输出：/root/workspace/科武纪元/硬科学素材/采集_YYYYMMDD/raw/candidates.jsonl

每条记录：
  {
    "source": "rss:DefenseNews",
    "title": "...",
    "url": "...",
    "summary": "...",
    "date": "...",
    "raw_fetched": true/false,    # 是否成功拉取正文
    "raw_path": "..."             # 正文备份路径
  }
```

源优先级（按本报告Top10）：
1. RSS Top5（DefenseNews, ArsTechnica, NewScientist, TechCrunch, Reuters/AP/BBC）
2. 海外RSS辅助（SpaceNews, IEEE_Spectrum, Nature摘要）
3. OpenCLI（arxiv, openalex, pubmed）
4. 定向检索（DDG/Bing，仅当OpenCLI结果<3时触发）
5. 中文机构（中科院、物理所，低频，每3日一次）
6. B站字幕（按需，不每日跑）

**砍掉**：
- 百度热搜（与科武关联度极低，今日未入库）
- 36kr自动入队（改手动或P2）
- 书单学习循环（移至独立`book_distiller.py`）

#### B. `gatekeeper_mini.py` — 纯过滤与判重
职责：读取candidates.jsonl，输出`CARD_PENDING`队列。

```
输入：candidates.jsonl + 现有INDEX.md/RAG/知识库
输出：更新sensenova_control_queue.json

步骤：
  1. 去重（URL+标题compact匹配）
  2. relevance_gate（strong_negative → SKIP_NOISE；negative+低正向 → skip；positive → keep）
  3. NASA/ESA PR二级过滤
  4. 交叉验证标记（verification_sources/confidence）
  5. 写队列（只写CARD_PENDING，不写DISTILL_FAIL）
```

**关键改进**：
- 判重时**区分"已入库正式卡"与"仅出现在raw/manifest"**。
  当前bug：manifest中的候选URL被误判为已入库，导致新候选被skip。
  修复：判重只查`时事素材/INDEX.md`、`知识库/INDEX.md`、`RAG_CARDS`。

#### C. `archiver_mini.py` — 纯转卡与入库
职责：读取队列中`CARD_AUTODISTILLED`或主控审过的卡，完成最后一步归档。

```
输入：素材卡MD文件 + 队列状态
输出：
  - 知识库分类目录/素材卡_xxx.md
  - 知识库/INDEX.md 追加
  - RAG jsonl 追加
  - 时事素材/INDEX.md 追加（如需要）

步骤：
  1. 检查raw_status（MISSING_RAW → 不入知识库，只留时事素材候选区）
  2. 分类（CATEGORY_KEYWORDS匹配）
  3. 文件名规范化（safe_slug）
  4. 去重（material_hashes）
  5. 追加INDEX / RAG
```

#### D. 模型调用单独成脚本（可选）

```
distiller.py：读取CARD_PENDING，调用SenseNova/MiniMax，输出素材卡MD，更新队列为CARD_AUTODISTILLED。
```

**当前`orchestrator_v3.py`的处理**：
- 其RSS功能与sensenova脚本重复，建议**退役orchestrator的RSS模块**，只保留：
  - 微信直抓（独立功能，用户触发）
  - B站字幕（独立功能）
  - 中科院/物理所列表（低频，可并入collector_mini）

### 4.3 定时策略

| 任务 | 频率 | 触发条件 |
|---|---|---|
| RSS Top5 + 海外RSS | 每日1次 | cron固定 |
| OpenCLI学术检索 | 每日1次 | 按plan.gaps定向query |
| 中文机构（CAS/IOP） | 每3日1次 | 低频，内容更新慢 |
| B站字幕 | 每周1次 | 人工补关键词后触发 |
| 微信直抓 | 即时 | 用户转发链接后手动触发 |
| 定向DDG/Bing | 条件触发 | OpenCLI结果<3条时 |
| 模型蒸馏 | 每日1次 | 待处理队列>0时 |
| 归档入库 | 每日1次 | CARD_AUTODISTILLED存在时 |

---

## 五、手动跑验收指标

每次手动或自动跑完采集闭环，主控/顾问按以下指标验收。

### 5.1 采集层指标

| 指标 | 合格线 | 验收方式 |
|---|---|---|
| RSS源可用率 | ≥80%（5源中至少4源返回200+有效item） | 检查`raw/rss_feeds.json`各源非失败 |
| 候选总数 | ≥20条/日（含RSS+OpenCLI+定向） | `candidates.jsonl`行数或`current_events_hotlist.json`的results |
| 强噪声过滤率 | ≥70%（skip+low占候选总数比例） | 看skipped_reasons，产业大会/融资/PR应被过滤 |
| 新增CARD_PENDING | ≥2条/日 | `queue_status_counts`中CARD_PENDING增量 |
| MISSING_RAW比例 | ≤30%（候选中无正文的占比） | 素材卡中raw_status为MISSING_RAW的比例 |

### 5.2 内容层指标

| 指标 | 合格线 | 验收方式 |
|---|---|---|
| 入库素材卡小说映射率 | ≥70%（每张卡至少有一个明确章节/卷映射） | 抽查3张新卡，看"可用方向"字段 |
| 交叉验证率 | ≥20%（有≥2个verification_sources的候选占比） | `confidence: high_cross_verified`占比 |
| 重复入库率 | ≤5%（新卡与已有卡标题/URL重叠） | 抽查INDEX去重 |
| 噪声入库率 | 0%（产业大会/纯融资/PR稿不得入知识库） | 抽查知识库新增，发现1张即不合格 |

### 5.3 效率指标

| 指标 | 合格线 | 验收方式 |
|---|---|---|
| 端到端耗时 | ≤15分钟（采集+过滤+转卡+归档） | 看report时间戳差 |
| 人工介入次数 | ≤1次/日（除用户转发的微信文章外） | 记录主控接管/补卡次数 |
| CARD_REVIEW_FAIL积压 | ≤10条 | `queue_status_counts`中CARD_REVIEW_FAIL数量 |

### 5.4 当前状态快照（2026-05-22）

基于最新`control_report`：

| 指标 | 当前值 | 是否合格 | 备注 |
|---|---|---|---|
| 候选总数 | 62（current_events）+27（opencli）=89 | ✅ | 超合格线 |
| 强噪声过滤率 | (29+14)/62=69% | ✅ | 接近合格线 |
| 新增CARD_PENDING | 0 | ❌ | 今日无新增，队列吃老本 |
| MISSING_RAW比例 | 高（OpenCLI多无摘要，NASA/ESA PR无正文价值） | ⚠️ | 需优化源质量 |
| CARD_REVIEW_FAIL积压 | 31 | ❌ | 严重超标，需清理 |
| 噪声入库（今日） | 知识库出现"能落地的请留下""讲故事的请离场"等大会软文 | ❌ | strong_negative过滤有漏洞 |

** immediate action**：
1. 清理31条CARD_REVIEW_FAIL：逐条审，有正文的转CARD_DONE，无价值的改SKIP_NOISE。
2. 补过滤规则：36kr/TechCrunch融资稿、NASA PR稿。
3. 修复判重bug：manifest/raw中的URL不得作为"已入库"依据。

---

## 六、总结

- **最稳Top3**：DefenseNews、ArsTechnica、NewScientist。RSS稳定、正文开放、与科武主线（军事AI/深空/量子/算力）高度重合。
- **最大噪声源**：36kr产业大会、TechCrunch融资、NASA/ESA PR。已过滤但规则需补丁。
- **最大架构债**：sensenova脚本过重（1567行），采集/过滤/模型/归档耦合。建议按collector/gatekeeper/archiver三件套拆分，每次迭代只改一个模块。
- **当前最急**：31条CARD_REVIEW_FAIL积压 + 判重bug导致新候选被误skip + 大会软文漏入知识库。三问题互相关联，清理后新增CARD_PENDING会回升。

---

*报告完。如需针对某一源做深度采集脚本审计，可继续派工。*
