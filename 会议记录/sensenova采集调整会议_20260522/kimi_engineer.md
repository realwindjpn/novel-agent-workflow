# Kimi engineer — 脚本层闭环与验证方案

## 一、已修 vs 未闭环

| 项 | 状态 | 证据 |
|---|---|---|
| 噪声过滤（流程标记/无正文/SKIP不转卡） | 已修 | repair报告第1项 |
| 书单释放（learned从119→30） | 已修 | repair报告第2项 |
| OpenCLI HN+36kr补充源 | 已修 | repair报告第3项 |
| DDG/Bing失败时fallback到OpenCLI/36kr | 已修 | repair报告第4项 |
| CAS/IOP/OpenCLI/定向检索产物入队 | 未闭环 | audit报告第2段断；control_report queue里CARD_PENDING仅3 |
| OpenCLI判重过严（39条added=0） | 未闭环 | audit报告第3段断 |
| CARD_PENDING 3张卡死 | 未闭环 | control_report |
| MiniMax巡检缺位 | 未闭环 | MiniMax 429＋cron列表无巡检job |
| next_instruction更新 | 未闭环 | repair报告"仍需主控确认" |
| 硬科学论文/官方源原文卡 | 未闭环 | landing摘要"缺当日P0时事、硬科学原文卡" |

结论：采集层没坏，坏在入队→去重→蒸馏三段。SenseNova算半修好，门禁未闭。

## 二、大纲两天未优化主因

不是缺时事素材，是有材料但没进大纲流程。四段断：
1. 采集层已抓到RSS/CAS/IOP/OpenCLI（audit第1段）
2. 入队层断：CAS/IOP/OpenCLI基本没进CARD_PENDING（audit第2段）
3. 去重过严：OpenCLI 39条added=0（audit第3段）
4. 蒸馏被噪声pending误导，出来的卡偏产业会议信息，缺硬科学原文卡，没触发融纲（landing摘要）

## 三、MiniMax 429 时替代巡检

可用模型烟搞：WF Opus47、ZAI GLM-5.1、Alibaba Qwen3.6-plus、Kimi coding。
巡检任务轻，可切到 GLM-5.1 或 Qwen3.6-plus 做定时巡检，或由主控手动执行。
不建议用 Opus47（高成本）。

## 四、下轮小步验证方案（不改代码）

### cron前（下一次 16:33 之前）
1. 读 `/root/workspace/科武纪元/学习记录/SenseNova蒸馏落地/control_report.json`，记录 CARD_PENDING数、各状态计数
2. 读 `scripts/sensenova_daily_kewu_learning.py` 中 `next_instruction` 变量，确认是否已按landing建议更新（月球南极/能源、HBM3e/CoWoS、QKD中继/DI-QKD）
3. 检查 OpenCLI 判重参数（是否有日期/标题相似度阈值过低导致全拒），记录阈值

### cron后（等待运行完毕）
4. 对比新旧 control_report：
   - CARD_PENDING ↑ 或 仍=3 → 问题在入队/去重
   - CARD_DONE ↑ 但 kb_new_cards ↑不明显 → 问题在转卡/审核
   - SKIP_DUPLICATE ↑ → OpenCLI判重过严未解
   - 若时事类型卡比例↑ → 采集方向调整有效

### 验收标准
- 通过：CARD_PENDING=0，kb_new_cards_this_run≥3，至少1张硬科学/时事类卡
- 失败：CARD_PENDING≥3且无变化，或 kb_new_cards=0

## 五、可执行调整清单

1. 主控更新 `next_instruction` 为 landing建议方向
2. 主控确认 OpenCLI 判重阈值是否需放松（不改代码，先记录等待）
3. 主控手动触发一次 MiniMax 巡检，若仍429，用 GLM-5.1 或 Qwen3.6-plus 代替
4. 下轮 cron 运行后对比 control_report，按上述验收标准判断
5. 若入队问题持续，再排查 `scripts/sensenova_daily_kewu_learning.py` 中 CAS/IOP 入队逻辑
