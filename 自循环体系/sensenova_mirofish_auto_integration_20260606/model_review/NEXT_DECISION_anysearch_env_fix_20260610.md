# 下一步裁决 — anysearch_env_fix_20260610

## 裁决

| 项 | 裁决 | 动作 |
|---|---|---|
| OUTLINE_PATCH=0 | 不触发G2 | — |
| FDRF CHAPTER_PREP_ONLY | 入准备包 | 归档至 ch217 准备包候选 |
| ARCHIVE×6 | 确认归档 | 无需动作 |
| QP无正文×10 | 不进推演 | 保持 discovery_pending |
| stale×2 | 正确拦截 | 无需动作 |

## 主控须执行

1. **domestic body_fetch 链路修复（P0）**：自06-08起国内正文近零。当前有效素材主要来自海外NASA/官方源。人民网/新华社/央视/中科院正文抓取未恢复，采集质量持续下降。
2. **bridge 标题净化（P1）**：
   - people.com.cn slug格式（`cNNNN-NNNNNNNN.html`）需正文标题回填
   - 新华社客户端（`app.xinhuanet.com/news/article.html?articleId=...`）需专用提取
3. **discovery query_plan 正文补采（P2）**：当前10条 discovery QP 全数跳过。若需继续采集微博/知乎/B站等线索，须接入 body_fetch 或转 web_search→web_extract 定向查。

## 不做

- 不写正式素材卡
- 不改大纲/正文/TXT/草稿箱
- 不触发六角色会议
- 不新建 GPT55_REVIEW（未实际调用GPT5.5）
