# 下一步决策 cron_20260611_1357

- 决策模型：xiaomi/mimo-v2.5
- 决策时间：2026-06-11T14:30

---

## 一、本次运行结论

| 类别 | 数量 | 决策 |
|---|---|---|
| OUTLINE_PATCH | 0 | 无需六角色会议 |
| CHAPTER_PREP_ONLY | 3 | 入准备包，待主控审后转正式卡 |
| ARCHIVE_WITH_REASON | 7 | 确认归档 |
| Bridge bug | 0 | 无需修复 |
| GPT55 命名违规 | 0 | 无需改名 |

## 二、准备包清单

| 素材 | 章节 | 核心事实 | 转正式卡前提 |
|---|---|---|---|
| Artemis III 助推器运输 | ch156 | SLS 最终助推器段 6/2 犹他→肯尼迪，75%推力 | 已有正文，可直接转 |
| ESA ILA 2026 | ch156 | ISOS 声明、欧洲在轨服务主权 | 补 ESA 具体任务/预算后升级 |
| Nature WGD 论文 | ch359 | WGD→脑细胞进化，ohnologues 驱动 | 远期种子，暂不转正式卡 |

## 三、待主控决策

### 3.1 准备包→正式卡转换

Artemis III 助推器条目证据完整（primary、有正文、有事实核、非 stale），建议主控审后当轮转正式素材卡，入库 `时事素材/素材卡/2026-06-11/` 并同步双 INDEX + RAG。

ESA ILA 条目正文充实但展会性质，建议标注 `CHAPTER_PREP_ONLY` 暂不转正式卡，等 ESA 后续任务/预算细节补强后再转。

Nature WGD 条目为远期种子，建议归入 `知识库/生物/` 并标 `ch359_远期伏笔`，不入时事素材卡。

### 3.2 B2 body_fetch 链路

query_plan_no_body 持续 40+ 条（本轮 43）。B2 runner 生成大量 query_plan 骨架但正文抓取未闭环。这不是 bridge 问题。

**建议**：
- 暂停 SenseNova→MiroFish bridge 生产 cron，直到 B2 body_fetch 产出实质正文
- 修复 B2 runner：direct URL 优先 → official query_plan 二级 → discovery 进 recheck_queue
- 正文成功只认 `raw/bodies/*.txt`
- 用 `raw/mirofish_input_gate.json` 控制 bridge 灰度恢复

### 3.3 历史素材回补

当前 valid 项以海外官方源为主（NASA/ESA/Nature）。国内源 body_fetch 仍为瓶颈。建议：
- 先修复国内 official body_fetch 链路（CCTV/CNSA/people/xinhua）
- 成功后恢复 bridge，用 `stale_domestic_article` 门禁控制旧文流入

---

## 四、状态更新

- last_processed_run_dir: cron_20260611_1357
- last_processed_at: 2026-06-11T14:30
- processed_by_model: xiaomi/mimo-v2.5
- is_gpt55_review: false
- patrol_result: REVIEWED
