# GLM 只读复核：B2 Bridge Patch

- 复核时间：2026-06-11
- 复核模型：zai/glm-5.1
- 复核范围：mirofish_feed_to_card_bridge_20260606.py 全文（664行）
- 对照：child.log diff（9 hunks）、CONTROLLER_REVIEW_batch_20260611.md、NEXT_DECISION_batch_20260611.md

---

## 一、Patch 落地完整性：PASS

child.log 含 9 个 diff hunks，逐一与磁盘文件比对：

| # | hunk 位置 | 内容 | 落地 |
|---|-----------|------|------|
| 1 | L28-44 | CROSS_RUN_DEDUPE_FILE 常量 + load/save 函数 | ✓ |
| 2 | L59-61 | normalize_url() 工具函数 | ✓ |
| 3 | L149-158 | MALFORMED_TITLE_EXACT + MALFORMED_TITLE_RE | ✓ |
| 4 | L161-179 | is_malformed_search_title 增强 | ✓ |
| 5 | L321-340 | classify_material 展会/Arrakihs P0 门禁 | ✓ |
| 6 | L468 | main() 加载 cross_run_sigs | ✓ |
| 7 | L502-513 | Body substance gate + 跨run去重 | ✓ |
| 8 | L532 | evidence_complete 加 malformed 门禁 | ✓ |
| 9 | L565-569 | 持久化 cross_run signatures | ✓ |

**结论**：9/9 hunks 完整落地，无遗漏、无截断。Kimi-k2.6 timeout 发生在最后阶段（hunk 9 之后的写回/清理阶段），但 diff 已全部写入磁盘。

---

## 二、语法与逻辑风险：LOW

### 2.1 语法

无语法错误。所有 regex 合法闭合，缩进一致，类型标注正确。

### 2.2 逻辑审查

| 点 | 判定 | 说明 |
|----|------|------|
| MALFORMED_TITLE_RE 首两个分支重叠 | 无害 | `[cC]?\d{5,}` 已含 `\d{5,}`，冗余但不误判 |
| MALFORMED_TITLE_RE 用 `[a-z]` 匹配原始 title（非 lowercase） | 低风险 | "NASA 12345" 不匹配该 RE，但后续纯数字+无 alpha check 会正确放过（NASA 是合法词）；"ARTICLE 12345" 由 MALFORMED_TITLE_EXACT 拦截。实操无遗漏 |
| body substance gate 不处理 `## Summary` 无 `## Body Extract` 的情况 | 可接受 | 目标是确保有实质内容；无 Body Extract 的卡本身不够格 |
| cross_run_sigs 只对非 ARCHIVE 项持久化 | 正确 | ARCHIVE 项不应占签名位 |
| normalize_url 放在 safe_name 之后 | 无功能影响 | 纯排版 |
| signatures 文件无限增长 | 非问题 | 每条 16 字符 hex，千条 <30KB |

### 2.3 潜在改进（非阻塞）

1. `MALFORMED_TITLE_RE` 可统一用 `re.IGNORECASE`，避免未来遗漏全大写路径标题
2. cross_run_sigs 可加 entries 数上限（如 5000），防极长运行后文件膨胀

---

## 三、覆盖核验

| 门禁需求 | 覆盖 | 机制 | 验证 |
|----------|------|------|------|
| title="article" | ✓ | MALFORMED_TITLE_EXACT 含 `'article'`；evidence_complete 加 `not is_malformed_search_title` | 双重拦截 |
| 数字路径标题 "c64094 40722548" | ✓ | MALFORMED_TITLE_RE `[cC]?\d{5,}` + 纯数字正则 | 已覆盖 |
| 通用 malformed title | ✓ | 空标题 / EXACT 集 / 数字RE / 面包屑符号 / URL混入 / 长度<4 | 六路拦截 |
| ESA ILA（展会） | ✓ | classify_material P0 expo_hit → ARCHIVE_WITH_REASON | 13 个展会关键词 |
| Arrakihs（纯基础宇宙学） | ✓ | classify_material P0 basic_cosmology_hit → ARCHIVE；space_tech_hit 救回机制 | 双条件门禁 |
| 跨 run 去重 | ✓ | url+title SHA1 签名持久化 + 每轮加载比对 | 新增完整 |
| evidence_complete 修正 | ✓ | 增加 `not is_malformed_search_title` 条件 | 修复前 Xinhua "article" 标记为 true |

---

## 四、B2 query_plan_no_body：未修（预期）

bridge 脚本在 L483-484 已有 `card_type == 'query_plan'` 过滤，正确 skip 无 body 项。

但 **root cause** 是上游 B2 body_fetch 阶段对 query_plan 类候选未执行确定性抓取，导致 ~86% 候选为空壳。此问题属于 **上游 pipeline 修复范围**，不在 bridge patch 职责内。

CONTROLLER_REVIEW 和 NEXT_DECISION 均标记此为 P0，建议暂停 bridge cron 至 B2 body_fetch 修复。

**当前状态**：bridge 侧防御完整（skip + 门禁），上游阻塞未解。

---

## 五、最终裁定

### PASS（附 2 项低优先级建议）

**理由**：
- 9/9 hunks 完整落地，无遗漏
- 7 项门禁需求全部覆盖
- 语法无误，逻辑风险 LOW
- B2 query_plan_no_body 为上游问题，bridge 侧已正确防御
- evidence_complete 修正解决了 Xinhua "article" 误判

### 低优先级建议（不阻塞交付）

| # | 建议 | 优先级 |
|---|------|--------|
| S1 | MALFORMED_TITLE_RE 加 `re.IGNORECASE`，防全大写路径标题漏网 | P3 |
| S2 | cross_run signatures 加 entries 上限（建议 5000），超限清理最旧 | P3 |

### 无需返修

本次 patch 无 FAIL 项。返修清单为空。

---

## 六、与 CONTROLLER_REVIEW / NEXT_DECISION 对齐

| CONTROLLER 发现 | bridge patch 状态 |
|-----------------|-------------------|
| ESA ILA 应降 ARCHIVE | ✓ 已修（expo_hit 门禁） |
| ESA Arrakihs 应降 ARCHIVE | ✓ 已修（basic_cosmology 门禁） |
| cpc malformed title 漏拦截 | ✓ 已修（MALFORMED_TITLE_EXACT + enhanced check） |
| Xinhua title="article" 需补证 | ✓ 已修（evidence_complete 门禁 + malformed 拦截） |
| 跨 run 去重不足 | ✓ 已修（signature 持久化） |
| evidence_complete 不可信项 | ✓ 已修（加 malformed check） |
| B2 body_fetch P0 阻塞 | 上游问题，bridge 不负责 |

**NEXT_DECISION 四项跟进**：P0（B2 body_fetch）属上游；P1（标题门禁）已修；P2（跨run去重）已修；P2（新华客端 title_extract）属上游。

---

*GLM readonly review, no files modified.*
