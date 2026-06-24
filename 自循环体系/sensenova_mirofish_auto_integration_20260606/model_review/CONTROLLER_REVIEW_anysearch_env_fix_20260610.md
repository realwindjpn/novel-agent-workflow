# 控制器复核 — anysearch_env_fix_20260610

复核时间：2026-06-10T23:15:00
复核模型：xiaomi/mimo-v2.5（非GPT5.5，标注为控制器复核）
前序：cron_20260610_1827（已复核，valid=2）

## 本轮对比

| 指标 | cron_20260610_1827 | anysearch_env_fix_20260610 |
|---|---|---|
| valid_input | 2 | 7 |
| skipped | 67 | 13 |
| stale_blocked | 1 | 2 |
| OUTLINE_PATCH | 2→0（降级） | 0 |
| CHAPTER_PREP_ONLY | 0 | 1 |
| ARCHIVE | 0 | 6 |

valid 从2→7有改善，但根因是分母缩小（69→20条），非国内正文恢复。

## 质量审计

### FDRF CHAPTER_PREP_ONLY 有效性
- 正文证据：✅ 694字，含具体参数
- URL可达：✅ NASA官方
- 发布日期：✅ 2026-06-09
- 科武关联：⚠️ 中等。风洞参数可写入军事/航空细节层，但非算力/地月/群体智能主线
- 去重：✅ INDEX/RAG 无同条
- 结论：**保留CHAPTER_PREP_ONLY**，不升格为大纲补丁

### people.com.cn 两条标题异常
- `c40531 40521652`：理论频道文章，标题=URL路径slug
- `c1004 40732291`：财经频道文章，标题=URL路径slug
- 根因：bridge 标题提取逻辑对 `people.com.cn/n1/YYYY/MMDD/cNNNN-NNNNNNNN.html` 格式未做正文标题解析
- 影响：低（两条已归档），但属 bridge 持续性 bug

### 新华社客户端标题异常
- `article`：标题=页面类型名，非文章标题
- 根因：`app.xinhuanet.com/news/article.html?articleId=...` 格式的标题提取失败
- 影响：低（已归档），但说明国内客户端URL的标题净化需单独特化

## 旧文/历史规划门禁

- stale_domestic_article=2，正确拦截
- 无CNSA旧文进入推演
- NASA FDRF 发布 2026-06-09，非旧文

## GPT55_REVIEW 命名声明

本轮 decision_cards 无 GPT55_REVIEW 文件。若后续产出，须真实调用GPT-5.5/SharedChat；否则标注"控制器复核/历史误名"。

## 结论

- 本轮 valid 有改善但国内正文仍缺席
- FDRF 保留为 CHAPTER_PREP_ONLY，入准备包
- bridge 标题 bug 已记录3处（people×2 + xinhua客户端×1）
- 不触发G2/G3/六角色会议
- 下一步：主控须修复 domestic body_fetch 链路，否则采集持续空转
