# Wiki Schema

## Domain
《科武纪元》小说设定库。用于管理人物卡、势力、科武设定、伏笔链、章节事件索引、写作红线与资料来源。

## Conventions
- 根路径：`/root/workspace/科武纪元/wiki/`
- raw/ 为不可变快照；正文改动不在 raw 里直接修。
- 每个页面必须有 YAML frontmatter。
- 页面之间用 `[[wikilinks]]`。
- 每次更新同步 `index.md` 与 `log.md`。
- 章节页按 `chapter-index/chapter-086.md` 命名。
- 伏笔按 `plot-threads/<slug>.md` 命名。
- 人物按 `entities/<name>.md` 命名。

## Frontmatter
```yaml
---
title: 页面标题
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | plot-thread | chapter | rule | query | summary
tags: []
sources: []
confidence: high | medium | low
---
```

## Tag Taxonomy
- role: protagonist, support, antagonist
- story: chapter, outline, plot-thread, foreshadowing, relationship
- science: ai, compute, energy, martial-science, dyson, brain-computer
- faction: nantianmen, iron-curtain, international, black-market
- craft: writing-rule, anti-ai-tone, sensitivity

## Page Thresholds
- 人物/势力/技术体系：核心出现即建页。
- 伏笔：跨章延续或影响后续卷，必须建页。
- 单章事件：只建章节索引，不为一次性细节建独立页。

## Update Policy
新章节精修后：更新对应 chapter 页；若出现人物状态、势力变化、伏笔推进，同步更新 entity/concept/plot-thread 页。
