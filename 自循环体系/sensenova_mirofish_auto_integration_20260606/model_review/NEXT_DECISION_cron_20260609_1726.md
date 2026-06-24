# 下一步裁决：cron_20260609_1726

- generated_at: 2026-06-09T18:45
- generated_by: xiaomi/mimo-v2.5（控制器）

## 待主控执行

### A. OUTLINE_PATCH → G2/六角色会议

| 材料 | 目标章 | 动作 |
|---|---|---|
| Nature: AI reshaping maths/physics discovery | ch95 | 安排 G2 会议裁决是否写入备注层。context pack 须包含：①ch95 原文；②Nature COMMENT 正文（须补全截断部分）；③算法主权/算力变量映射 |

**注意**: Nature 正文截断于 `Compa`。主控安排 G2 前，建议用 web_extract 重抓 `https://www.nature.com/articles/d41586-026-01820-1` 补全全文。

### B. CHAPTER_PREP_ONLY → 审后转正式卡

| 材料 | 判重动作 | 转卡条件 |
|---|---|---|
| 新华社2025十大新闻 | grep INDEX/RAG: "2025" "十大新闻" "新华社" | 需判重；若已有类似卡则 SKIP_DUPLICATE；转卡时标注"2025年度回顾" |
| NASA INCUS Satellites | grep INDEX: "INCUS" "convective" "对流" | 须先补真实正文（web_extract 重抓）；body 为导航文本时不可转卡 |
| 央视网 2026 | grep INDEX: "丙午马年" "十五五" "央视" | 短讯但事实核清晰；可转 SHORT_OFFICIAL_FACT 卡 |

### C. 不可执行（禁止）

- ❌ 不改大纲/正文/TXT/草稿箱
- ❌ 不写正式素材卡（控制器只裁决，不写卡）
- ❌ 不修改 STATUS/WAL

## 待桥接修复

1. **INCUS body_fetch 导航污染**: bridge 对 science.nasa.gov/photojournal URL 应检测导航/链接文本占比，超阈值标 NEED_ARTICLE_BODY
2. **上游候选去重**: 同一 URL 在 card_distill_plan 中出现 4 次，B 段候选生成阶段需去重
3. **Nature 全文截断**: body_len=14253 但实际正文只到 `Compa`，可能被截断或 JS 渲染不完整

## 历史对比

| 轮次 | valid | OP | PREP | ARCHIVE | domestic body |
|---|---|---|---|---|---|
| cron_20260609_1226 | 7 | 1 | 2 | 4 | 0 |
| cron_20260609_1726 | 10 | 1 | 3 | 6 | 2 (旧文) |

趋势：valid_input 从 7→10，domestic body_fetch 从 0→2（均为2025旧文）。国内 2026 当前权威源 body_fetch 仍为 0。
