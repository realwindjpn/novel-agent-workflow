# MiroFish 模型推演报告

- run_id: codecli_bodyfetch_repair_20260610_1400
- 生成时间: 2026-06-10
- 处理模型: xiaomi/mimo-v2.5 (控制器接管，非GPT-5.5复核)

## 输入摘要

- valid_input_count: 3
- skipped_count: 15
- skip_reason_counts: query_plan_no_body=14, summary_not_body_evidence=1
- stale_domestic_blocked_count: 0

## 裁决总览

| disposition | count | 详情 |
|---|---|---|
| ARCHIVE_WITH_REASON | 2 | Tyndall冰山文(low relevance), Artemis III(duplicate) |
| CHAPTER_PREP_ONLY | 1 | FDRF风洞规格(ch217军事平台细节) |
| OUTLINE_PATCH | 0 | 无 |

## 逐条推演

### 1. Tyndall's Trail of Bergs → ARCHIVE_WITH_REASON ✅

- 来源: NASA Earth Observatory (official)
- 正文长度: 3761字
- 裁决理由: 与算力主权、地月争夺、群体智能、军事制度主线因果链不足
- 推演确认: 正文为冰山漂移科普，无技术/制度/地缘压力变量。归档正确。
- 2029 horizon: 不影响终局。

### 2. Flight Dynamics Research Facility Characteristics → CHAPTER_PREP_ONLY ⚠️

- 来源: NASA ARMD/AETC (official)
- 正文长度: 694字（规格表为主）
- 裁决理由: 高机动平台与感知/噪声治理可作军事制度细节层
- 推演审读:
  - 正文仅含风洞技术参数（截面20ft×24ft，速度0-172ft/s，动压0-35psf，雷诺数0-1.10×10^6/ft）
  - 无叙事性内容，纯设施规格页
  - 可用于：飞行器气动测试工程约束、联邦/白盾体系硬件能力描述
  - 不可用于：直接写入正文台词/动作（过于技术表格化）
  - 增益级别: **LOW** — 可作背景素材备查，但694字规格表不构成强情节支撑
- 适配区间: ch217+（军事平台/测试设施线）
- 缺证补采: 无。规格完整但叙事价值有限。
- 建议: 保留准备包候选，不升格为OUTLINE_PATCH。

### 3. NASA Marches Toward Artemis III Mission in 2027, Names Crew Members → ARCHIVE_WITH_REASON ✅

- 来源: NASA News Release (official)
- 正文长度: 10832字
- 裁决理由: TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY
- 推演确认: 已入库条目，桥正确拦截。无需重复推演。
- 2029 horizon: Artemis III 2027年任务规划已在既有素材卡覆盖。

## 跨条目关系

本批3条均为NASA官方源（overseas_official），无跨源交叉。无同事件不同URL去重问题。

## 关键阻塞识别

**国内body_fetch仍为0%**：14条query_plan_no_body均为国内官方源（CNSA×2, 人民日报×3, 新华社×1）的搜索骨架，未解析到具体文章URL。这是自2026-06-08以来的持续阻塞。

- 根因: Bing搜索→国内官方站文章URL解析失败，body_fetch候选读取为空
- 影响: 国内素材完全缺席MiroFish投喂，地缘政治/制度/产业三轴严重偏科
- 建议: 主控须继续推动body_fetch候选读取/心跳/每候选timeout修复；或切换Tavily API fallback

## 结论

本轮无OUTLINE_PATCH进入G2/六角色会议。1个CHAPTER_PREP_ONLY候选（FDRF）增益偏低，仅作背景备查。主控优先级：修复国内body_fetch > 推演新素材。
