# Opus4.7 主席/系统架构审计意见

会议：SenseNova采集调整会议 2026-05-22
角色：会议主席 + 系统架构只读审计
证据基线：`科武纪元/会议记录/sensenova采集调整会议_20260522/context_pack.md`

---

## 一、SenseNova 修复完成度判定：**部分修复，未闭环**

判为 **60% 修复**。理由按四段链路对账（证据：`sensenova_repair_review_freemodel_20260522.md` 四段断模型）：

| 链路段 | 早上修复 (`sensenova_repair_kimi1_20260522.md`) | 闭环状态 |
|---|---|---|
| 1. 采集层 | 新增 OpenCLI HN/36kr；DDG/Bing fallback | ✅ 已修 |
| 2. 入队层 | 未明确处理 CAS/IOP/OpenCLI 入队断点 | ❌ 未闭环 |
| 3. 去重过滤 | 噪声SKIP不再转卡；但 OpenCLI added=0 未根治 | ⚠️ 半修 |
| 4. 蒸馏/转卡 | 书单从119→30释放；本轮 kb_new_cards=4 | ⚠️ 量太低 |
| 5. 巡检/接管 | 未恢复 MiniMax 接管，且 MiniMax 429 | ❌ 未闭环 |
| 6. 融纲触发 | context_pack 全程未提及融纲被触发 | ❌ 未闭环 |

**关键证据**：`control_report` 显示 CARD_REVIEW_FAIL=31、SKIP_DUPLICATE=34、CARD_AUTODISTILLED=38，但 `kb_new_cards_this_run=4`，转卡转化率约 4/38 ≈ 10%，且 4 张全为产业会议类（城市AI/五粮液/电竞×2），与缺口榜（月球912、算力387、量子176）**零交集**。这是「修了管道、没修分发」。

---

## 二、未闭环项清单（按阻塞优先级）

1. **P0 入队断点**：CAS/IOP/OpenCLI/定向检索抓到但未进 CARD_PENDING（CARD_PENDING仅3）。证据：`sensenova_repair_review_freemodel_20260522.md`。
2. **P0 巡检真空**：MiniMax 429 不可用、cron 中无接管者。证据：`当前cron` 仅列 `67cc540dd63a` 一条 SenseNova。
3. **P1 缺口-产出错配**：4张新卡覆盖0个高分缺口（最高912）。证据：`landing摘要` vs `缺口`。
4. **P1 OpenCLI 判重过严**：39 条 added=0。证据：审计报告第3点。
5. **P2 融纲未触发**：两天大纲未优化的直接原因不是「没素材」，是**没有触发融纲的回调钩子**。context_pack 未出现任何融纲日志路径。
6. **P2 历史噪声 pending 未清**：CARD_REVIEW_FAIL=31 持续占位会拖低下轮蒸馏 ROI。

---

## 三、根因排序（架构视角）

1. **R1 队列状态机缺「源→pending」strict 适配器**：不同源（RSS/CAS/IOP/OpenCLI/定向检索）走各自入队路径，被同一套去重规则拦截，等价于「过滤器作用域错配」。这是大纲两天不动的**真根因**，不是缺时事也不是缺科学。
2. **R2 转卡选择器未挂缺口权重**：autodistilled=38 但出卡只跟「噪声过滤后剩余条目顺序」走，未按 `缺口score` 排序拣选。
3. **R3 融纲触发器与采集解耦**：landing 报告写了「下一轮建议方向」但没有事件总线把它推给融纲流程。
4. **R4 巡检单点**：MiniMax 单点接管，无降级链。
5. **R5 监控盲区**：没有「kb_new_cards 命中缺口数」这一关键 KPI，导致修了三天看起来 OK_DISTILLED 实际无效。

---

## 四、下轮采集 + 转卡 + 融纲触发方案（只产方案，不改文件）

### A. 采集（下次 cron 16:33 前生效）
- 关键词锁定 Top3 缺口：`月球南极/PSR/Artemis/嫦娥八号`、`HBM3e/CoWoS/良率/先进封装`、`QKD中继/DI-QKD/墨子号`。
- 源优先级：arxiv + semantic_scholar + crawl_url_markdown 官方源（NASA/CNSA/TSMC IR/中科大），降低 36kr 权重至 ≤20%。
- OpenCLI 判重阈值临时放宽（标题相似度 0.85→0.92），仅本轮观察。

### B. 入队（修脚本门禁，由 Kimi 执行）
- 为 CAS/IOP/OpenCLI/定向检索各加一行 `enqueue_strict(source_tag, bypass_global_dedup=False, per_source_dedup=True)`，使去重作用域回到「本源内」。
- 验收：下轮 CARD_PENDING ≥ 20。

### C. 转卡（缺口加权拣选）
- 在 autodistilled→kb 这一步加权：`pick_score = base + 缺口score × 0.3`，强制本轮 ≥2 张落在 月球/算力/量子 三缺口。
- 验收：`kb_new_cards_this_run ≥ 6` 且 **缺口命中 ≥ 2**。

### D. 融纲触发（关键闭环）
- landing 报告写完后，追加一步 `emit_event('outline.refresh', payload=landing摘要)`；融纲消费方监听该事件，无事件不跑、有事件必跑。
- 验收：下轮在 `学习记录/SenseNova蒸馏落地/` 出现 `*_landing.md` 后 30 分钟内，`大纲/` 目录有 mtime 更新或出现 `outline_diff_*.md`。

### E. 巡检接管（MiniMax 不可用期）
- 立即由 **ZAI GLM-5.1**（PASS）接管 SenseNova 巡检 cron；备用 **Alibaba Qwen3.6-plus**（PASS）。Kimi 仅做 coding，不进巡检轮值。
- 写入 cron 时标注 `owner=zai-glm-5.1, fallback=alibaba-qwen, restore_minimax_when=smoke_pass`。

### F. 最小可验证清单（下轮 cron 后必看）
1. `control_report.queue_status_counts.CARD_PENDING` ≥ 20
2. `kb_new_cards_this_run` ≥ 6 且缺口命中 ≥ 2
3. `学习记录/SenseNova蒸馏落地/2026-05-22_*_landing.md` 存在且包含「缺口命中明细」段
4. `大纲/` 目录 mtime 在 landing 后 30 分钟内更新
5. cron 列表新增 GLM 巡检条目，next 时间明确

任一不达标即判 SenseNova 仍未闭环，需再开会。

---
字数约 880。
