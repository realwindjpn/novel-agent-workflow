# 下一步决策

- run_id: cron_20260609_1226
- decided_at: 2026-06-09T13:55
- decided_by: xiaomi/mimo-v2.5 (controller takeover)

## 需要主控执行的动作

### 1. [P0] 开G2/六角色会议：Nature AI-maths-physics

- 素材：How AI is reshaping discovery in maths and physics (Nature COMMENT, 2026-06-08)
- URL: https://www.nature.com/articles/d41586-026-01820-1
- 目标章：第95章备注层
- context pack须含：
  - 原文摘要（AI augment not replace，检查证明/搜索反例/提中间步骤）
  - 标注"COMMENT非研究突破"
  - chaos-model: compute_sovereignty
  - 适配区间：90-110章
- 会议输出：OUTLINE_PATCH写入 / NOTE_ONLY / NO_PATCH
- **不改正文/TXT/草稿箱**

### 2. [P1] 国内body_fetch链路修复

- 本轮60条query_plan_no_body，国内源body_fetch=0
- B2段只产出查询骨架（people/xinhua/cctv/cnsa等site:搜索词），未执行web_search→article URL→正文抓取
- 建议：主控检查runner B2段是否跳过搜索直接输出query_plan；若已修复则等下轮cron验证

### 3. [P2] Bridge分类器修复

- NASA Earth Science/气象任务被误标"地月/深空/通信链路"
- 修复方向：分类器须区分NASA目录（Earth Science ≠ Deep Space）；body_fetch后做正文密度检查

## 不需要执行

- 不改大纲/正文/TXT
- 不写正式素材卡（dry-run产物）
- 不升格CHAPTER_PREP_ONLY为OUTLINE_PATCH

## 已归档确认

| 材料 | 理由 |
|---|---|
| SF Metropolitan Mosaic | 正文为空+分类错误（Earth非Deep Space） |
| INCUS Satellites | 气象卫星非深空+分类错误 |
| FIFA+Artemis | 标题重叠已入库 |
| Supersonic! | 同事件去重命中 |
| X-59 First Supersonic | URL已入库 |
| Brain connectome | 低科武相关性 |
