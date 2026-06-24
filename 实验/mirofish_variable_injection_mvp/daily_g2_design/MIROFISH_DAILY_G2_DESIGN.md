# MiroFish 每日 G2 融纲会议优化设计

version: 1.0
date: 2026-06-04
author: MiMo Pro (设计) / SkyClaw (待审)

---

## 1. 结论：部分能

MiroFish 变量注入机制**能**优化每日融纲会议，但**不能替代**六角色会议。

能做的：
- 为每张 SenseNova 素材卡产出「势力反应→连锁冲突→章节钩子→大纲delta候选」结构化推演
- 强制每张卡有明确去向（三态处置），消灭"不采用"的模糊结论
- 在会议前提供可审议的结构化提案，降低会议"全票NOTE_ONLY"的概率

不能做的：
- 替代六角色对角色心理/对话质感的深度判断
- 直接改大纲/正文（只产候选，裁决权归G2会议）
- 保证所有推演非套路化（需编辑审+反模式约束）

---

## 2. 根因分析：为什么过去素材常未进入大纲？

### 根因 A：素材到大纲的转化路径缺失（主因，权重40%）

现状流程：
```
SenseNova采集 → 素材卡 → 六角色会议 → NOTE_ONLY → 归档
```

问题：素材卡是「事实核」（NASA做了X、ESA发了Y），但六角色会议缺乏将「事实」映射到「章节/势力/冲突链」的结构化步骤。每个席位只能基于直觉判断"这个素材有没有用"，没有工具帮助回答"用在哪里、怎么用"。

证据：0603会议67张有效卡全部NOTE_ONLY，但GPT-5.5门禁独立评估后结论是OUTLINE_PATCH，说明会议遗漏了可落地素材。

### 根因 B：会议门槛过保守（权重25%）

六角色会议默认保守：宁可NOTE_ONLY也不冒险改大纲。这是合理的防御，但缺少「压力测试」——没有人强制推演"如果这个素材不用，会错过什么冲突机会？"

### 根因 C：缺少强制处置卡（权重20%）

会议结论只写"NOTE_ONLY"或"可采用"，不写：
- 用在哪一章？
- 用作什么层（备注/钩子/冲突/红线）？
- 不用的话归档理由是什么？

导致素材卡堆积、无人回顾、过期作废。

### 根因 D：缺少大纲delta输出要求（权重15%）

会议不要求产出「大纲diff」——即"如果采纳这条素材，大纲具体要加/改/删哪一行"。没有diff，编辑无法评估改动成本，自然倾向保守。

---

## 3. 新流程设计

```
SenseNova素材卡（11张/日）
        │
        ▼
┌─────────────────────────┐
│  MiroFish 变量注入预处理  │  ← 单次LLM/卡，产出结构化推演
│  输入：素材卡 + Wiki实体  │
│  输出：decision_card.json │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│  G2 多角色融纲会议        │  ← 六角色审议 decision_card
│  输入：decision_card集    │
│  输出：三态处置裁决        │
└─────────────────────────┘
        │
        ├──→ OUTLINE_PATCH      → 大纲delta_proposals.md → 编辑apply
        ├──→ CHAPTER_PREP_ONLY  → chapter_prep_notes.md  → 写作时调用
        └──→ ARCHIVE_WITH_REASON → daily_material_disposition.md → 归档
```

### 3.1 MiroFish 预处理层（新增）

**触发时机**：SenseNova cron完成后、G2会议前
**输入**：
- 当日所有 valid_content_cards（11张/日）
- Wiki 实体表（势力/角色/技术树）
- 当前大纲最新版

**处理逻辑**：
对每张素材卡，执行一次变量注入推演（复用 `variable_injection_template.md`），产出：
1. 势力反应（哪些势力会因这条素材产生行为变化）
2. 连锁冲突（2-4条因果链，带时间锚点）
3. 章节钩子（1-3个具体钩子，标注适合章节编号）
4. 大纲delta候选（如果采纳，大纲应增/改/删什么）
5. 反模式禁忌（哪些写法是套路化、应避免）
6. 六角色建议（是否需要六角色深度审议，以及理由）

**输出**：每张卡对应一份 `decision_card.json`

**成本**：11张卡 × 1次LLM = 11次调用/日，可接受

### 3.2 G2 会议改造

**变更点**：会议输入从「原始素材卡」改为「decision_card集」

**每个席位必须对每张 decision_card 给出三态裁决**：
- `OUTLINE_PATCH`：应进入大纲，附带具体delta
- `CHAPTER_PREP_ONLY`：不改大纲，但写作时可调用，附带使用场景
- `ARCHIVE_WITH_REASON`：不采用，**必须写理由**（不是"没有用"，而是"因为X所以不适合Y"）

**主席汇总规则**：
- 任何一席给出 OUTLINE_PATCH → 该卡进入 outline_delta_proposals.md
- 多席给出 CHAPTER_PREP_ONLY → 汇总进 chapter_prep_notes.md
- 全席 ARCHIVE_WITH_REASON → 进 disposition 归档，理由必须具体

### 3.3 三态处置产出

| 状态 | 产出文件 | 后续动作 |
|---|---|---|
| OUTLINE_PATCH | outline_delta_proposals.md | 编辑审→apply到大纲 |
| CHAPTER_PREP_ONLY | chapter_prep_notes.md | 下次写到对应章节时调用 |
| ARCHIVE_WITH_REASON | daily_material_disposition.md | 归档，30天后可回顾 |

---

## 4. 最小落地文件设计

### 4.1 decision_card.json Schema

```json
{
  "$schema": "decision_card_v1",
  "material_id": "2026-06-04_artemis_ii_057276",
  "source_url": "https://science.nasa.gov/...",
  "title": "A Moonlit Earth as Seen From Artemis II",
  "captured_at": "2026-06-04T14:46:40",

  "mirofish_projection": {
    "force_reactions": [
      {
        "force": "航天国家队",
        "reaction": "月面任务宣传窗口打开，可利用公众关注度推动预算",
        "wiki_ref": "Wiki/势力/航天国家队"
      }
    ],
    "chain_conflicts": [
      {
        "chain": ["月面EVA高关注度", "公众期待vs工程现实落差", "舆论压力→预算争夺"],
        "time_anchor": "近3章内",
        "intensity": "medium"
      }
    ],
    "chapter_hooks": [
      {
        "hook_id": "H001",
        "description": "Artemis照片引发公众对载人航天的浪漫化想象，与科武中月面绞肉机的残酷现实形成反差",
        "suitable_chapters": [371, 373],
        "reversal": "公众以为的太空探索是星辰大海，实际是水循环故障和辐射防护"
      }
    ],
    "outline_delta_candidate": {
      "type": "note_layer",
      "target_chapter": 371,
      "proposed_addition": "月面任务公众认知与工程现实落差备注",
      "not_proposed": "不改主线，只加备注层"
    },
    "anti_patterns": [
      "不得写成'宇航员拍了张照片所以公众支持航天'",
      "不得简化为'照片=舆论胜利'"
    ],
    "six_role_recommendation": {
      "needed": false,
      "reason": "公众认知层素材，编辑+读者席即可裁决"
    }
  },

  "disposition": null,
  "disposition_reason": null,
  "disposition_by": null,
  "disposition_at": null
}
```

### 4.2 daily_material_disposition.md 模板

```markdown
# 每日素材处置 {date}

## 统计
- 总素材卡: {n}
- OUTLINE_PATCH: {n1}
- CHAPTER_PREP_ONLY: {n2}
- ARCHIVE_WITH_REASON: {n3}

## OUTLINE_PATCH
| material_id | title | target_chapter | delta摘要 | 裁决席位 |
|---|---|---|---|---|

## CHAPTER_PREP_ONLY
| material_id | title | 适合章节 | 使用场景 | 裁决席位 |
|---|---|---|---|---|

## ARCHIVE_WITH_REASON
| material_id | title | 归档理由 | 裁决席位 |
|---|---|---|---|
```

### 4.3 outline_delta_proposals.md 模板

```markdown
# 大纲Delta提案 {date}

## 提案 1: {title}
- 来源素材: {material_id}
- 目标章节: {chapter}
- 变更类型: note_layer / hook / conflict / red_line
- 具体文本:
  > {proposed text to add/modify in outline}
- 审核状态: PENDING
- apply后需: 同步Wiki/RAG/跟踪表/STATUS/WAL/Git
```

---

## 5. 边界声明

MiroFish **只做**：
- 输入SenseNova素材卡 + Wiki实体 → 输出势力反应/连锁冲突/章节钩子/大纲delta候选
- 每张卡必须有三态处置，不得空白

MiroFish **不做**：
- 不直接改大纲/正文/TXT/skill/RAG/知识库
- 不替代六角色会议（只提供结构化预审材料）
- 不联网、不装依赖（纯模板+LLM）
- 不做最终裁决（裁决权归G2会议）

---

## 6. 与现有流程的接口

### 6.1 接入点
```
SenseNova cron (DONE)
    ↓
[新增] MiroFish 预处理脚本
    ↓ 读取: 当日 cards/ 目录 + Wiki实体 + 大纲latest
    ↓ 产出: daily_g2_cards/{date}/decision_cards.json
    ↓
G2 会议（输入改为 decision_cards）
    ↓
三态处置文件
```

### 6.2 文件存放约定
```
/root/workspace/科武纪元/实验/mirofish_variable_injection_mvp/daily_g2_design/
├── MIROFISH_DAILY_G2_DESIGN.md   ← 本文件
├── STATUS.json                    ← 状态跟踪
├── templates/
│   ├── decision_card_schema.json  ← JSON Schema
│   ├── daily_material_disposition.md ← 处置模板
│   └── outline_delta_proposals.md    ← delta模板
└── pilot_run/                     ← 首次试运行目录
```

---

## 7. 落地路径（最小可行）

| 步骤 | 谁做 | 产物 | ETA |
|---|---|---|---|
| 1. 审核本设计 | SkyClaw | 审核意见 | 待排 |
| 2. 写 decision_card 模板+脚本 | MiMo Pro | 可执行脚本 | 1天 |
| 3. 用0604素材试跑1轮 | 脚本自动 | 11张decision_card | 1小时 |
| 4. 人工评审decision_card质量 | 编辑+主控 | 质量报告 | 1天 |
| 5. 改造G2会议prompt | 主控 | 新版会议prompt | 半天 |
| 6. 首次正式运行 | cron+G2 | 首份三态处置 | 1天 |
| 7. 评估是否正式吸收 | 主控 | 最终裁决 | — |

---

## 8. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 推演套路化 | 模板加反模式约束 + 编辑审 |
| 11卡×推演 token消耗大 | 单次LLM/卡，可并行，总成本可控 |
| 与六角色会议重复讨论 | 明确边界：MiroFish=推演层，六角色=心理/质感层 |
| decision_card质量不稳定 | 试运行5天后评估，不达标则退回参考模式 |
