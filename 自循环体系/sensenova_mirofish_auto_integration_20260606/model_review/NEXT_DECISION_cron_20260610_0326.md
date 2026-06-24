# 下一步决策

- run_id: cron_20260610_0326
- 复核时间: 2026-06-10
- 复核模型: xiaomi/mimo-v2.5

## 当前状态

| 指标 | 值 |
|------|-----|
| valid_content_cards | 12 |
| 控制器复核后有效 CHAPTER_PREP_ONLY | 2 |
| 控制器复核后应降级 ARCHIVE | 2 |
| OUTLINE_PATCH | 0 |
| 国内源 body_fetch | 0% |
| 旧文被时效门禁拦截 | 0（Bug） |
| bridge Bug 数 | 3 |

## 有效准备包候选

1. **Artemis III 机组任命（ESA, 2026-06-09）**
   - 事实核：4 人机组（Bresnik/Rubio/Douglas/Parmitano）、ESM 第三台、地球轨道对接测试、Orion 训练
   - 适用：§135-217 月面/深空线
   - 缺证：需补 NASA 官方 press release 原文（当前 ESA 转述）

2. **Proba-3 恢复运行（ESA, 2026-06-09）**
   - 事实核：2026-02 异常→数月恢复→编队飞行恢复→日冕仪 ASPIICS 健康→太阳风结构速度 3-4x 新发现
   - 适用：§200+ 深空工程/编队飞行技术
   - 缺证：因果链较弱，仅作技术背景参考

## G2/六角色会议建议

**不建议当前开 G2/六角色会议。**

理由：
- OUTLINE_PATCH = 0，无素材达到大纲补丁门槛
- 2 条 CHAPTER_PREP_ONLY 均为海外 NASA/ESA，证据完整但因果链偏弱
- 国内源 body_fetch 0%，三轴覆盖严重偏科
- 建议先修复国内源链路，等下一轮有国内素材后再开融纲会

## 主控下一步动作

### P0（必须）

1. **修复 bridge body_len=0 仍 DISTILLED 的 Bug**：增加 post-distill `body_len > 200` 门禁
2. **修复 CCTV 旧文时效门禁**：解析显式发布时间 `2025-12-30`，触发 `stale_domestic_article`
3. **Artemis III 事件签名去重**：桥接层增加 `SAME_EVENT_ARTEMIS_III_CREW_ANNOUNCEMENT_20260609`

### P1（建议）

4. **国内源 body_fetch 链路修复**：当前 55 条 query_plan 全空转，国内 source_matrix 有 13 个源但 0 条命中
5. **body_fetch 正文清洗**：增加 post-fetch 导航/侧栏/页脚剥离
6. **积累 CHAPTER_PREP_ONLY 到准备包**：当前仅 2 条有效，等积累到 5-10 条后考虑开 G2

### P2（可选）

7. 历史 33 条 unprocessed bridge 事件批量处理：多数为 6/6-6/9 旧 cron，可按日期归档
