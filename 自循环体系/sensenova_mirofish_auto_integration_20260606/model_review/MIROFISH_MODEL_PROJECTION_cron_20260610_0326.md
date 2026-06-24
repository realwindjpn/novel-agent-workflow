# MiroFish 模型推演报告

- run_id: cron_20260610_0326
- 复核时间: 2026-06-10T13:30+00:00
- 复核模型: xiaomi/mimo-v2.5（非 GPT-5.5/SharedChat，显式声明）
- bridge 事件: valid=12, skipped=59, stale_domestic_blocked=0

## 三态裁决

### OUTLINE_PATCH（0 条）

无。本轮无素材达到大纲补丁门槛。

### CHAPTER_PREP_ONLY（4 条）

| # | 标题 | 来源 | 证据质量 | 适用章节 | 裁决 |
|---|------|------|----------|----------|------|
| 1 | Artemis III crew announcement (ESA video) | ESA official | body_len=2058, 有效正文约60% | §135-217 月面/深空 | **保留**：机组4人、ESM第三台、地球轨道对接测试→真实工程节点 |
| 2 | Proba-3 recovery & formation flying | ESA official | body_len=3659, 有效正文约70% | §200+ 深空工程 | **降级风险**：编队飞行/日冕仪技术有映射，但与主线因果链弱。建议仅作技术背景参考 |
| 3 | 2026是个什么年？ | 央视网/人民日报 | body_len=461, 2025-12-30 发布 | 不适用 | **应降为 ARCHIVE**：旧文(半年前)、泛政策概述、无具体科武事实 |
| 4 | NASA Knows: Mass Distribution | NASA educational | body_len 待核 | 不适用 | **应降为 ARCHIVE**：科普教育页，非新闻/进展 |

### ARCHIVE_WITH_REASON（8 条）

| # | 标题 | 理由 |
|---|------|------|
| 1 | NASA Marches Toward Artemis III (nasa.gov press release) | TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY，重复入库 |
| 2 | June 2026 Satellite Puzzler | 地球科学谜题，与主线因果链不足 |
| 3 | San Francisco's Metropolitan Mosaic | ISS 城市遥感，与主线因果链不足 |
| 4 | How NASA Science and Artemis Shaping 2026 FIFA World | 科普+世界杯，非硬科学进展 |
| 5 | Luca Parmitano on Artemis III selection | ESA 宇航员访谈视频，与 #1 同事件 |
| 6 | ESA astronaut Luca Parmitano joins NASA's Artemis III | ESA 公告，与 #1/#5 同事件 |
| 7 | Cleaner air and prosperity (Copernicus/Sentinel-5P) | 地球科学/环保，与主线因果链不足 |
| 8 | AI technology must serve human cognitive development (Nature) | **body_fetch: NO, body_len=0**。无正文→不可推演→ARCHIVE |

## Bridge 质量审计

### 发现的 Bridge Bug

1. **Nature AI card 无正文却被 DISTILLED**：candidate `04821ed1be746e88` 的 `body_fetch: NO`, `body_len: 0`，但仍被标记为 DISTILLED 并进入 bridge。Bridge 应在 body_len=0 时直接 ARCHIVE，不应依赖标题做三态裁决。
2. **CCTV 旧文未被时效门禁拦截**：`2026是个什么年` 发布于 2025-12-30，距今超 5 个月。Bridge 的 `stale_domestic_blocked_count=0` 说明时效门禁未触发——可能是该卡 source_group=domestic 但发布时间解析未命中旧文规则。
3. **Artemis III 同事件三卡未去重**：ESA video + ESA announcement + Luca Parmitano selection 三张卡同事件不同 URL，bridge 未用事件签名归档。应标 `SAME_EVENT_ARTEMIS_III_CREW_ANNOUNCEMENT_20260609`。

### 导航污染

body_fetch 产出的正文普遍含 30-70% 导航/侧栏/页脚噪声。有效正文被压缩在总 body 的小比例内。需增加 post-fetch 正文清洗层。

## 国内源覆盖

- 国内源命中: 1/12（CCTV，且为旧文泛概述）
- 国内源 body_fetch 成功: 0（CCTV 的 body 来自 overseas_official 路径或直接 requests，非国内源搜索链路）
- 国内源覆盖率: **FAIL**，body_fetch 对国内源仍 0% 功能
