# 下一步决策（批量合并）

决策时间：2026-06-11T15:00:00
覆盖事件：cron_20260611_0356 / cron_20260611_0856 / bodyfetch_rootfix_smoke_20260611

## 一、准备包清单

### ch156 准备包（地月/深空）
| # | 素材 | URL | 证据状态 | 备注 |
|---|---|---|---|---|
| 1 | Artemis III Booster Segments 运输 | nasa.gov | 可信 | 工程进度，非技术突破 |

### ch359 准备包（生物伦理/基因治理）
| # | 素材 | URL | 证据状态 | 备注 |
|---|---|---|---|---|
| 1 | Nature WGD 全基因组复制 | nature.com | 可信+CAVEAT | 可能为摘要，标 CAVEAT |

### 待补证
| # | 素材 | URL | 补证动作 |
|---|---|---|---|
| 1 | Xinhua article #1 | app.xinhuanet.com/articleId=20260530... | 重新抓取标题+正文 |
| 2 | Xinhua article #2 | app.xinhuanet.com/articleId=ff4dd821... | 重新抓取标题+正文 |

## 二、无需六角色会议

三轮合计 0 个 OUTLINE_PATCH。无需发起 G2/六角色战略会议。

## 三、主控必须跟进的系统性问题

### 1. B2 body_fetch 阻塞（P0）
- query_plan_no_body 占 skip ~86%
- 三轮 valid 仅 28 项，且多为重复
- 有效新素材仅 2-3 个主题
- **建议**：暂停 bridge 生产 cron，优先修 B2 body_fetch 确定性抓取
- **不暂停**：bridge 继续跑只会重复投喂同一批候选

### 2. bridge 标题质量门禁（P1）
- malformed_title "c64094 40722548" 和 "article" 漏入 CHAPTER_PREP_ONLY
- 建议 bridge 增加：title 长度 < 10 或全数字/路径片段 → 自动降级 SKIP

### 3. bridge 跨 run 去重（P2）
- 同一素材在 3 个 run 中反复出现
- 建议 bridge 增加 material_id 级跨 run 去重

### 4. 新华客端 title_extract（P2）
- app.xinhuanet.com 文章 body_fetch 成功但 title_extract 失败
- 建议 body_fetch 成功后二次尝试 title_extract

## 四、cron 行为建议

| 项目 | 建议 |
|---|---|
| bridge 生产 cron | 建议暂停至 B2 body_fetch 修复后恢复 |
| 本批不产生正式卡 | 全部 dry_run，无正式素材卡/INDEX/RAG 写入 |
| 本批不改大纲/正文 | ✓ 合规 |
| 准备包 | 仅 2 项有效，积累至主控统一处理 |

## 五、更新清单

| 文件 | 动作 |
|---|---|
| sensenova_mirofish_model_takeover_state.json | 更新 last_processed_run_dir 到 batch 3 个 run |
| MIROFISH_MODEL_PROJECTION_batch_20260611.md | 已写入 |
| CONTROLLER_REVIEW_batch_20260611.md | 已写入 |
| NEXT_DECISION_batch_20260611.md | 已写入 |
