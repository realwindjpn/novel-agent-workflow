# 下一步裁决 cron_20260610_1827

## 本轮裁决
- 2张bridge OUTLINE_PATCH → 全部降级为 CHAPTER_PREP_ONLY
- 0张进入G2/六角色会议
- 0张正式转卡
- 本轮无大纲/正文/TXT变更

## 主控待办

### P0: 恢复国内body_fetch
连续3天(06-08~06-10)国内源body_fetch近乎全灭。必须:
1. 排查xinhuanet/cctv/cnsa/miit等官方站的URL解析链路
2. 确认Bing/DDG/Tavily返回的是否为文章页(非频道首页)
3. body_fetch预算应按国内/海外分池，避免海外RSS消耗国内配额
4. 验收: 至少people/xinhua/cctv/cnsa各1条BODY_FETCHED

### P1: 修复bridge标题清洗
当前两张卡标题均为URL slug(c64094 40722548 / c1004 40732291)。bridge应:
1. 优先用body extract首段首句
2. 次选HTML <title>
3. 最后才用URL path派生

### P2: 补9张NASA/ESA摘要全文
Artemis III/Parmitano/Proba-3等有高discovery价值。建议:
- 用web_extract补全文
- 补全后重新投喂bridge

### P3: 准备包状态
当前CHAPTER_PREP_ONLY候选积累:
- 本轮新增2张(算力政策+智博会)
- 前轮累积待统计
- 建议累积≥5张同类后批量开G2，不逐张触发

## 最近5轮趋势
| run_id | valid | OP→CP降级 | stale | body_fetch成功率 |
|---|---|---|---|---|
| cron_20260610_0326 | 12 | 0→0 | 0 | 低 |
| cron_20260610_0826 | 6 | 1→0 | 0 | 低 |
| bodyfetch_worker | 4 | 0→0 | 0 | 低 |
| cron_20260610_1326 | 10 | 1→0 | 0 | 低 |
| cron_20260610_1827 | 2 | 2→0 | 1 | 2/12=17% |

趋势: valid_input持续走低(12→6→4→10→2)，body_fetch无实质恢复。国内源修复是当前最大阻塞项。
