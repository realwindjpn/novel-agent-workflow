# 控制器复核报告（批量合并）

复核时间：2026-06-11T15:00:00
复核模型：xiaomi/mimo-v2.5
覆盖：cron_20260611_0356 / cron_20260611_0856 / bodyfetch_rootfix_smoke_20260611
注意：本报告为控制器复核，非 GPT-5.5/SharedChat 终审。不使用 GPT55_REVIEW 文件名。

## 一、bridge 裁决质量审计

### 裁决一致性
三轮候选高度重复——同一组素材（Artemis III booster、ESA ILA/Arrakihs、WGD Nature、Xinhua articles）反复出现在 0356/0856/rootfix_smoke 三个 run 中。bridge 去重仅限于 TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY，未做跨 run 的 material_id 去重。

### 裁决准确性

| 素材 | bridge 裁决 | 控制器裁决 | 差异 |
|---|---|---|---|
| Artemis III Booster | CHAPTER_PREP_ONLY | CHAPTER_PREP_ONLY ✓ | 一致 |
| ESA ILA 2026 | CHAPTER_PREP_ONLY | ARCHIVE ↓ | bridge 偏宽，展会文 |
| ESA Arrakihs | CHAPTER_PREP_ONLY | ARCHIVE ↓ | bridge 偏宽，纯基础科学 |
| Nature WGD | CHAPTER_PREP_ONLY | CHAPTER_PREP_ONLY ✓ | 一致 |
| cpc.people.com.cn | CHAPTER_PREP_ONLY | ARCHIVE ↓ | malformed title 漏拦截 |
| Xinhua article #1 | CHAPTER_PREP_ONLY | NEED_TITLE_RESOLVE | title="article"，需补证 |
| Xinhua article #2 | CHAPTER_PREP_ONLY | NEED_TITLE_RESOLVE | 同上 |

**结论**：bridge 对展会/纯基础科学/malformed_title 的门禁偏松。11 个 CHAPTER_PREP_ONLY 中，仅 2 个确认有效（Artemis III booster + WGD Nature），2 个需补证（Xinhua），3 个应降级为 ARCHIVE，4 个为重复。

### stale_domestic 拦截
- 4 项被拦截，机制正常
- 被拦截项为旧文/非当前事件，不得进入推演

## 二、GPT55_REVIEW 命名检查

三轮均未产生 GPT55_REVIEW 文件。✓ 正确——本批复核由 xiaomi/mimo-v2.5 执行，不应命名为 GPT55_REVIEW。

## 三、证据完整性检查

| 素材 | evidence_complete | 实际状态 | 判定 |
|---|---|---|---|
| Artemis III Booster | true | NASA 官方图+文，URL 可访问 | 可信 |
| ESA ILA 2026 | true | ESA 官方，URL 可访问 | 可信但低增益 |
| ESA Arrakihs | true | ESA 官方，URL 可访问 | 可信但低增益 |
| Nature WGD | true | Nature 论文，可能为摘要 | 标 CAVEAT |
| cpc article | true | 标题畸形，内容未验证 | 不可信 |
| Xinhua #1 | true | title="article"，标题未解析 | 不可信 |
| Xinhua #2 | true | title="article"，标题未解析 | 不可信 |

**结论**：7/10 证据可信。3 项（malformed title + Xinhua x2）证据不可信，需补证。

## 四、重复素材检查

同一组素材跨 3 个 run 重复出现：
- Artemis III Booster：3 次出现
- ESA ILA 2026：3 次出现
- ESA Arrakihs：3 次出现
- Nature WGD：3 次出现
- Xinhua articles：3 次出现

bridge 跨 run 去重不足。建议：bridge 增加 material_id 级跨 run 去重，或在 converter_tasks 中标记 "already_in_previous_run"。

## 五、最终裁决汇总

### 有效准备包候选（2 项）
1. **Artemis III Booster Segments** → ch156 准备包
2. **Nature WGD 全基因组复制** → ch359 准备包（标 CAVEAT）

### 需补证（2 项）
1. **Xinhua article #1** → NEED_TITLE_RESOLVE
2. **Xinhua article #2** → NEED_TITLE_RESOLVE

### 确认归档（17+3 项）
- 17 项原 ARCHIVE 确认
- 3 项降级：ESA ILA 2026 / ESA Arrakihs / cpc.people.com.cn
