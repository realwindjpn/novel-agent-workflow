# 下一步决策

- run_id: cron_20260608_2125
- 决策时间: 2026-06-08T22:05
- 决策模型: xiaomi/mimo-v2.5-pro

## 裁决总览

| 裁决 | 数量 | 说明 |
|---|---|---|
| OUTLINE_PATCH → downgrade CHAPTER_PREP_ONLY | 1 | AI抗生素耐药(Nature) |
| CHAPTER_PREP_ONLY confirmed | 1 | ESA ILA柏林航展 |
| ARCHIVE_WITH_REASON confirmed | 7 | 重复/标题重叠 |
| GPT-5.5复核 | PASS | 无需返修 |

## 下一步动作

### 1. 转正式素材卡（主控/下次会话）

两张有效卡均应转正式素材卡：

**卡1: AI助力抗生素耐药性应对**
- 源卡: `cron_20260608_2125/cards/AI_is_taking_on_antibiotic_resistance___here_s_how.md`
- 目标: `时事素材/素材卡/2026-06-08/` + `知识库/生物/`
- 裁决: CHAPTER_PREP_ONLY（不写大纲备注）
- 原因: Nature primary、evidence_complete=true、INDEX判重通过

**卡2: ESA ILA 2026柏林航展**
- 源卡: `cron_20260608_2125/cards/ESA_at_ILA_Berlin_International_Airshow_2026.md`
- 目标: `时事素材/素材卡/2026-06-08/` + `知识库/航天制度/`
- 裁决: CHAPTER_PREP_ONLY（不写大纲备注）
- 原因: ESA primary、evidence_complete=true、INDEX判重通过

### 2. INDEX更新

- `时事素材/INDEX.md` 追加两张卡
- `知识库/INDEX.md` 追加对应分类条目

### 3. 不执行项

- ❌ 不改大纲/大纲备注层
- ❌ 不改正文/TXT/草稿箱
- ❌ 不直接写RAG（转卡后由主控同步）

## 国内源body_fetch问题提醒

本轮60条skipped中，**全部国内源**（people/xinhuanet/cctv/stdaily/huanqiu/guancha/miit/mod/most/cnsa/cas/iop/cac）均为 `BODY_FETCH_FAIL / QUERY_TITLE_NOT_ARTICLE_TITLE`。国内body_fetch链路仍未修复。这已是连续多轮出现，需主控关注。
