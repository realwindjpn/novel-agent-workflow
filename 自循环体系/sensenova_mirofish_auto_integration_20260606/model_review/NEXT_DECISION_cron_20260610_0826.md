# 下一步决策 — cron_20260610_0826

- 决策者：xiaomi/mimo-v2.5（控制器接管）
- 决策时间：2026-06-10

## 本轮结论

**全部归档，无新增准备包/大纲补丁。**

| 原bridge裁决 | 控制器裁决 | 原因 |
|---|---|---|
| OUTLINE_PATCH (量子纠缠CCTV) | ARCHIVE | body=346字符导航污染，无正文，bridge误标evidence_complete |
| CHAPTER_PREP_ONLY (FDRF) | ARCHIVE | 亚音速风洞设施科普，与高机动平台(ch217)无因果链 |
| CHAPTER_PREP_ONLY (Mass Distribution) | ARCHIVE | K-8教育内容，与重返月球(ch156)无因果链；跨run重复 |
| ARCHIVE ×3 | ARCHIVE确认 | Artemis重复、卫星谜题低相关、Nature AI重复 |

## 下一步行动

### 1. 紧急：body_fetch 链路修复（高优先）

59项 QP 骨架无正文，比上轮多4项。连续多轮 body_fetch 链路不通。

建议主控：
- 查 runner B2 `body_fetch` 阶段是否有实际执行
- 确认 Tavily API fallback 是否生效
- 国内源（people/xinhua/cctv/cnsa）是否有定向 body_fetch 配额
- 若 body_fetch 代码有结构性问题，派 glm-5.1 或 kimi-for-coding 修脚本

### 2. 中优先：Bridge body 质量门禁

- 增加导航污染检测：body 含"返回首页/京ICP/加载更多/搜索/新闻频道/全站地图"等关键词占比超阈值 → `NAV_POLLUTED`
- body_len < 500 时默认 `evidence_complete=false`（需人工/控制器确认）
- `evidence_complete` 判定逻辑需与 body 质量联动

### 3. 低优先：跨 run 去重

- bridge 应维护 `processed_material_ids` 文件，跨 run 去重同一 candidate
- 当前 `20260610_eaecde5dae` 在 cron_20260610_0326 和 cron_20260610_0826 两次出现

### 4. 可选：量子纠缠原文补抓

- 若主控认为"量子纠缠催生新技术革命"有小说价值，应从新华网原始链接抓取正文
- 央视网转载页正文抓取失败（346字符导航污染），需尝试 `www.news.cn` 原站或百度搜索结果页
- 有正文后重新评估是否入卡

## 不执行项

- ❌ 不改大纲/正文/TXT
- ❌ 不写正式素材卡
- ❌ 不开六角色会议（无 OUTLINE_PATCH 需讨论）
- ❌ 不派子代理（本轮无有效素材需处理）
