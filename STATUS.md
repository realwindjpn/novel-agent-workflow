# 《科武纪元》项目状态

## 当前路由纠偏
- 2026-08-11：HS 火山方舟 LLM provider 已删除。
- `HS_API_KEY` 仅保留给 TTS；不得用于科学审、结构审、军事审或任何文本 fallback。
- 旧任务 ledger 中的 `hs/*` 记录仅作历史证据；不得作为现行席位依据。
- 科学席：仅使用实时 smoke 通过的 GLM provider；当前优先 `nexotoken-glm/glm-5.2`、`chun/glm-5.2`。均失败则 `NO_SEAT`，禁止自动回落至 hs 或 onefor 冒充 GLM。

## 任务门禁
- 作家主席：网页端 Qwen 固定项目会话。
- 五审须绑定同一候选 SHA；科学席缺失时不得写回、上传或发布。
- 主控只负责路由、监控、验收；不得代写、代审。

## 证据
- Hermes 配置检查：`hermes config check` 已通过。
- 全局 `model.fallback_providers` 与顶层 `fallback_providers` 已移除。
- 科学席错误记录已在 `任务运行态/20260811_kewu_selfcycle_cron_20260811_1400/MODEL_LEDGER.md` 标记 `INVALIDATED`。
- 路由账本：`/root/workspace/记忆体系/model-routing-active-ledger.md`。
- 路由笔记：`/root/workspace/记忆体系/model-routing-notes.md`。

## 最新进展
- 2026-08-14：确定性状态收口（254/257/258 前沿不变）；258 复核为 BLOCKED_WEB_AUTHOR，不得抬为草稿闭环；261/262 非草稿箱证据，不抬高前沿；G2 候选 108d415718 终态 NOTE_ONLY_ARCHIVED_PENDING_PRIMARY_SOURCE。
- 2026-08-12 08:47：第259章草稿箱闭环（未发布）；KOL雷达 sidecar_20260812_0732 归档（PARTIAL/无正式卡）。
- 2026-08-11：科学席路由纠偏完成，HS火山方舟已删除。

## 当前结论
`ROUTING_CORRECTED / SCIENCE_SEAT_NO_SEAT_UNTIL_FRESH_SMOKE`

下一步：对 `nexotoken-glm/glm-5.2`、`chun/glm-5.2` 做当轮语义 smoke；仅 PASS 者可重派科学审。 

## 最近同步
- 2026-08-14 | 状态收口：CURRENT_UPLOAD_PROGRESS / 跟踪表 / STATUS / WAL / cron G2_FINAL+STATUS / 20260814_kewu_status_reconcile
- 2026-08-12 08:43 | 同步章节 259
- 2026-08-12 12:38 | 同步章节 259
- 2026-08-12 22:15 | 同步章节 260
- 2026-08-13 22:09 | 同步章节 261
- 2026-08-13 22:09 | 同步章节 262
- 2026-08-15 00:15 | 同步章节 263
- 2026-08-15 00:17 | 同步章节 264
- 2026-08-15 13:09 | 同步章节 265

## G4_CLOSED_266 | 2026-08-15T14:18 | SHA fdc1418cb8aaf4de | CJK 4047 | 五审四席全PASS- 2026-08-15 18:51 | 同步章节 266
- 2026-08-16 15:12 | 同步章节 269
- 2026-08-16 15:13 | 同步章节 270
- 2026-08-16 17:12 | 同步章节 269
- 2026-08-16 17:13 | 同步章节 270
- 2026-08-16 17:47 | 同步章节 271
- 2026-08-16 17:48 | 同步章节 271
- 2026-08-16 17:49 | 同步章节 272
- 2026-08-16 18:13 | 同步章节 271
- 2026-08-16 18:24 | 同步章节 271
- 2026-08-16 18:25 | 同步章节 272
- 2026-08-18 02:59 | 第273章三审全PASS（编辑wahuiliyi-grok/grok-4.6、科学onefor/gpt-5.6-sol、读者agentrouter/gpt-5.6-sol），R1/R2定点返修后终稿SHA 728dbb65，净中文4101
- 2026-08-18 03:01 | 第273章跟踪表补行后二次同步
