# 控制器复核报告 — cron_20260610_0826

- 复核者：xiaomi/mimo-v2.5（控制器接管）
- 复核时间：2026-06-10
- 说明：本报告替代旧命名 `GPT55_REVIEW_*`。本轮未实际调用 GPT-5.5/SharedChat。

## 复核结论

**全面降级**：bridge 产出的 1 个 OUTLINE_PATCH 和 2 个 CHAPTER_PREP_ONLY 均不成立，全部降为 ARCHIVE。本轮无有效新增素材进入准备包或大纲补丁。

## 逐项复核

### OUTLINE_PATCH → ARCHIVE: 量子纠缠如何催生全新技术革命

| 检查项 | 结果 |
|---|---|
| URL可访问 | ✅ news.cctv.com/2026/06/09/ARTI... |
| 来源权威性 | ✅ 央视网（新华网供稿），domestic official |
| 发布时间 | 2026-06-09 13:25:15，当前时效 |
| 正文抓取 | ❌ body_len=346，全部为导航/页脚/编辑信息，无实际文章内容 |
| evidence_complete | ❌ bridge误标为true。AI Distill自身写明"正文未有效提取" |
| 事实核 | ❌ 无任何可核事实（无量子比特数/保真度/实验结果/应用场景） |
| 与现有库重叠 | 量子计算线已有6+张正式卡，覆盖九章四号/量子比特可移动/本源悟空/QKD等 |
| 大纲映射 | bridge标ch95，但无正文内容无法评估具体映射 |
| **裁决** | **ARCHIVE** — 主控需从新华网原始链接重抓正文后重新评估 |

### CHAPTER_PREP_ONLY → ARCHIVE: FDRF

| 检查项 | 结果 |
|---|---|
| URL可访问 | ✅ nasa.gov/directorates/armd/aetc/fdrf-characteristics |
| 来源权威性 | ✅ NASA official |
| 正文抓取 | ⚠️ body_len=5758，绝大部分为导航菜单，有效内容约5行（设施类型/测试段/用途/测试项目/研究对象） |
| 事实核 | ⚠️ 基本设施描述存在，但无测试数据/失败模式/成本约束 |
| 小说映射 | ❌ bridge标ch217"高机动平台"，但FDRF是大气层亚音速风洞，与无人机/外骨骼/群体智能无因果链 |
| **裁决** | **ARCHIVE** — 设施科普级内容，无工程增量 |

### CHAPTER_PREP_ONLY → ARCHIVE: Mass Distribution

| 检查项 | 结果 |
|---|---|
| URL可访问 | ✅ nasa.gov/learning-resources/nasa-knows-what-is-mass-distribution |
| 来源权威性 | ✅ NASA official |
| 正文抓取 | ⚠️ body_len=8741，导航污染，有效科普内容约300字符 |
| 内容级别 | K-8教育页（标注"for students grades 5-8"） |
| 小说映射 | ❌ bridge标ch156"重返月球"，但"质量分布是什么"是中学物理概念，与月面工程/深空通信无关联 |
| 跨run重复 | 同 material_id `20260610_eaecde5dae` 在上一轮 `cron_20260610_0326` 已被降级，本轮重复出现 |
| **裁决** | **ARCHIVE** — K-8教育内容，无工程价值；bridge去重失效 |

### ARCHIVE × 3 确认

- **Artemis III (20260610_1370f40ea0)**：TITLE_TOKEN_OVERLAP，库中已有Artemis III相关卡。✅
- **Satellite Puzzler (20260610_762e5caf54)**：NASA Earth Observatory卫星谜题，与科武主线无关。✅
- **Nature AI cognitive development (20260610_752009b549)**：TITLE_TOKEN_OVERLAP，库中已有AI/认知相关卡。✅

## Bridge Bug 清单

| # | Bug描述 | 影响 | 修复建议 |
|---|---|---|---|
| B1 | `evidence_complete=true` 误标在346字符导航污染body上 | 产生无效 OUTLINE_PATCH | 增加 body 质量门禁：body_len < 500 或导航关键词占比 > 50% → 标 NAV_POLLUTED |
| B2 | FDRF 5758字符body有效内容仅5行，被标 evidence_complete | 产生无效 CHAPTER_PREP_ONLY | 增加有效内容占比检查 |
| B3 | material_id `20260610_eaecde5dae` 跨 run 重复出现（已在 cron_20260610_0326 处理过） | 浪费推演资源 | bridge 维护 processed_material_ids set，跨 run 去重 |
| B4 | 59项 QP 骨架（query_plan_no_body）积压，body_fetch 链路持续不通 | 无新增有效素材 | 非 bridge 问题，需修 runner B2 body_fetch |

## 上下文补充

- 本轮与上一轮 `cron_20260610_0326` 高度相似：valid_input 从12降到6，outlook_patch从0变1但被降级。
- 国内源 body_fetch 仍为瓶颈：本轮 domestic official 有效正文抓取 = 0。
- QP 骨架积压从55增到59，body_fetch 链路问题未缓解。
