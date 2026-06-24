# 后续决策：manual_verify_fallback_20260609_005841

- 决策时间：2026-06-09T02:15
- 总裁决：**PARTIAL_PASS**

---

## 需要主控/用户执行的动作

### 1. 转正式素材卡（需主控确认后执行）

以下 CHAPTER_PREP_ONLY 候选建议转正式卡：

| 素材 | 来源 | 章节 | 优先级 | 动作 |
|---|---|---|---|---|
| "美国重返月球"这盘棋 | 新华环球 2026-04-28 | ch156 | P0 | 转正式卡→时事素材/INDEX→知识库/RAG |
| 石墨烯航空电池 | 新华 2025-02-10 | ch217 | P1 | 转正式卡，需先确认技术是否有2026后续 |

### 2. OUTLINE_PATCH 写入大纲备注层（需主控/GPT-5.5终审）

| 素材 | 章节 | 备注内容 | 证据等级 |
|---|---|---|---|
| 图灵进化融资 | ch95 | 国产端侧AI芯片创业→算力去中心化→与英伟达竞合→芯片主权压力 | PR来源+TIME_ANCHOR_202604 |
| AI reshaping discovery | ch95 | AI重构基础科学发现方式→算法主权新维度 | Nature权威但body不完整 |

### 3. 需补证

- [ ] Nature "How AI reshaping discovery" — 用 `web_extract` 重试补全文body，或追踪 Burtsev 等原始研究论文
- [ ] 图灵进化 — 查该公司截至2026-06是否有新进展/产品发布（用Bing/人民网搜索"图灵进化 2026"）

### 4. Bridge bug 修复

- Supersonic!（NASA）应标记为 ARCHIVE（与已入库X-59重复），当前bridge误标CHAPTER_PREP_ONLY。需修复bridge的X-59/超音速去重逻辑。

---

## 谁负责

| 动作 | 责任方 | 截止 |
|---|---|---|
| 转正式卡（美国重返月球/石墨烯） | 主控确认→MiMo/Qwen执行 | 下一轮自循环 |
| OUTLINE_PATCH 终审 | GPT-5.5 或用户 | 需触发 |
| Nature body 补证 | MiMo/主控 | 可同轮 |
| Bridge 分类 bug | GLM-5.1 修脚本 | 非紧急 |

---

## 不做的事

- ❌ 不改大纲/正文/TXT/草稿箱
- ❌ 不直接写正式素材卡/INDEX/RAG（需主控确认）
- ❌ 不改生产 SenseNova runner
- ❌ 不改主 cron
