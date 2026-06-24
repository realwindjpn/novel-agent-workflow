# 下一步裁决

- run_id: codecli_bodyfetch_repair_20260610_1400
- 裁决时间: 2026-06-10
- 裁决模型: xiaomi/mimo-v2.5（控制器接管）

## 本批处置

### OUTLINE_PATCH
- 数量: 0
- 动作: 无。无需进入G2/六角色会议。

### CHAPTER_PREP_ONLY → 准备包
| 素材 | 目标章 | 增益级别 | 动作 |
|---|---|---|---|
| FDRF风洞规格 | ch217 | LOW | 保留候选，不升格。等叙事性更强的军事测试设施素材合并使用。 |

### ARCHIVE_WITH_REASON → 归档
| 素材 | 理由 |
|---|---|
| Tyndall's Trail of Bergs | 冰山科普，与主线因果链不足 |
| Artemis III 2027 Crew | 已入库，TITLE_TOKEN_OVERLAP |

## 主控待办（按优先级）

### 🔴 P0 — 必须立即处理
**恢复国内body_fetch链路**
- 当前状态: 14/14国内query_plan全部NEED_TARGETED_ARTICLE_URL
- 持续时间: 自2026-06-08起连续多批
- 阻塞影响: 地缘政治/制度/产业三轴零贡献
- 建议动作:
  1. 检查Bing搜索→国内官方站文章URL解析是否修复
  2. 切换Tavily API fallback（读取TAVILY_API_KEY）
  3. 验证: 跑skip-models smoke，确认至少people/xinhua/cctv 1条BODY_FETCHED

### 🟡 P1 — 本批内处理
**FDRF候选归档降级**
- 当前CHAPTER_PREP_ONLY，但694字纯规格表叙事价值低
- 建议: 降为ARCHIVE_WITH_REASON，等有正文的军事测试设施新闻再合并

### 🟢 P2 — 下一批观察
**监控cron产出质量**
- 连续多批valid_input≤10且全为overseas_official
- 需确认国内body_fetch修复后国内素材进入MiroFish投喂

## 不做
- 不改大纲/正文/TXT/草稿箱
- 不写正式素材卡（dry_run policy）
- 不开六角色会议（无OUTLINE_PATCH）
- 不重命名旧GPT55_REVIEW文件（本批无此问题）
