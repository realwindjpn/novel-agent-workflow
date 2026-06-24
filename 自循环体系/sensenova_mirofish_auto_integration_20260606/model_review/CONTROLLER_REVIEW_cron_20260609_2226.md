# CONTROLLER_REVIEW — cron_20260609_2226

- processed_at: 2026-06-10T00:15
- controller: xiaomi/mimo-v2.5 (NOT GPT-5.5/SharedChat)
- source_run: /root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260609_2226

## 总览

| 指标 | 值 |
|---|---|
| valid_input | 10 |
| skipped | 60 |
| stale_domestic_blocked | 0 |
| OUTLINE_PATCH | 0 |
| CHAPTER_PREP_ONLY | 3 |
| ARCHIVE_WITH_REASON | 7 |

## skip_reason_counts 审计

- query_plan_no_body: 55 — 大量官方域 QP 骨架未做正文抓取，持续复发
- duplicate_within_run: 4 — CCTV "2026是个什么年" 在同轮出现4次，upstream 去重不足
- duplicate_url: 1

## 正文质量复核

### INCUS（CHAPTER_PREP_ONLY）
- body_len=6619，但实际正文为 NASA photojournal 摘要句（~50字），其余全是导航/侧栏/相关推荐
- AI Distill 截取的"核心事实"仅3行：3颗卫星、Blue Canyon Technologies测试、2026年5月下旬发射
- **判定**：正文抓取有效但内容极浅（photojournal entry 非 full article），标 `USABLE_EXTRACT_WITH_CAVEAT`
- **去重**：时事INDEX/知识库INDEX/RAG 均无，不重复
- **小说映射**：弱。对流上升气流研究属气象遥感，可做"遥感盲区/气象侦察代价"细节参考，但与当前第156章月面/深空主线因果链不足
- **保留为准备包候选**，不升正式卡

### ESA Cleaner air（CHAPTER_PREP_ONLY）
- body_len=6977，正文充实：Sentinel-5P 卫星数据、2475城市、80%实现清洁增长、中国719城（含京沪蓉）、Nature Cities 论文、2019-2024数据
- 发布日期 2026-06-09，时效合格
- **判定**：`FULL_EXTRACT`，正文完整可引用
- **去重**：时事INDEX/知识库INDEX/RAG 均无
- **小说映射**：中等。"数据驱动治理"可映射到算法主权/数据治理变量；卫星监测全球排放变化可做"技术治理 vs 主权冲突"的场景素材
- **bridge 描述有误**：标记为"地月/深空/通信链路素材"，实为地球观测/环境治理，与地月深空无直接关联。bridge chain 标签需修正
- **保留为准备包候选**，映射建议：第156章或更靠后的数据治理/算法主权章节

### CCTV "2026是个什么年"（CHAPTER_PREP_ONLY）
- 发布日期 2025-12-30，属 2025 年底展望文
- body_len=461，极短：丙午马年、十五五开局、长征胜利90周年、米兰冬奥会、美加墨世界杯
- **判定**：`SHORT_OFFICIAL_FACT`，有明确事实核但过于泛化
- **bridge 标签**：target_chapter=125，但当前已投稿最新约第138章附近，125章已完成
- **小说映射**：极弱。"十五五开局"可做时代背景噪声，但无具体事件/技术/冲突
- **降级为 ARCHIVE**：内容泛化、时效已过（2025年展望文）、目标章已完成

## ARCHIVE_WITH_REASON 确认（7条）

1. **SF Metropolitan Mosaic** — 城市景观，无科武关联。归档合理。
2. **NASA Science & FIFA World Cup** — TITLE_TOKEN_OVERLAP 误判可能性低，归档合理。
3. **Supersonic!** — SAME_EVENT_X59，与已入库 X-59 首飞超音速重复。归档合理。
4. **NASA X-59 Flies Supersonic** — SOURCE_URL_ALREADY_IN_INDEX，已入库。归档合理。
5. **Proba-3 ready for more science** — TITLE_TOKEN_OVERLAP，ESA 日照观测任务。归档合理。
6. **ESA/EBRD Earth observation finance** — TITLE_TOKEN_OVERLAP，金融导向非硬科学。归档合理。
7. **AI serve human cognitive development** — TITLE_TOKEN_OVERLAP，政策导向无技术锚。归档合理。

## bridge bug 记录

1. **INCUS body_fetch 导航污染**：body_len=6619 但实际内容仅~50字摘要+导航，需在 B2 body quality gate 加正文/导航比率检测
2. **CCTV 同轮重复4次**：`duplicate_within_run` 机制已拦截，但 upstream distill_plan 仍产出4份相同候选，应在 A/B 段加 hash 去重
3. **ESA Cleaner air chain 标签错误**：bridge 标为 `space_chain→authority_filter→kewu_relevance`，实为地球观测/环境治理，chain 应为 `earth_observation→data_governance`
4. **无 stale_domestic_blocked**：本轮无旧文拦截（国内候选仅 CCTV 一条且为 2025 年末文，但 bridge 未标 stale）
