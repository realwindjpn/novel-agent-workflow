# MiroFish 模型接管状态简报

日期：2026-06-10
模型：xiaomi/mimo-v2.5（控制器接管，非 GPT-5.5）

## 已处理事件

| run_id | valid | skipped | stale_blocked | OUTLINE_PATCH | PREP_ONLY | ARCHIVE | 说明 |
|---|---|---|---|---|---|---|---|
| cron_20260610_0826 | 6 | 59 | 0 | 1→0 | 2→0 | 3 | 已处理。量子CCTV nav污染降级，FDRF/Mass无ch映射降级 |
| byeapi_b2_empty_smoke_20260610_101500 | 0 | 0 | - | 0 | 0 | 0 | smoke，无素材 |
| verify_bodyfetch_after_patch_20260610_1148 | 0 | 0 | - | 0 | 0 | 0 | verify，无素材 |

## 当前阻塞

- **body_fetch 链路完全断裂**：连续多轮 `BODY_FETCH_STOPPED_AFTER_ATTEMPT_CAP`，国内 official `BODY_FETCHED=0`。
- **QP 骨架积压**：cron_20260610_0826 有 59 个 `query_plan_no_body`，无法生成正文候选。
- **最新 smoke** `prod_bodyfetch_card_smoke_20260610_1212`：body_fetch `running` 但 `items_total=1, items_done=0`，heartbeat 停 12:09:32。符合 0/0/0 静默模式。

## 下一步

1. body_fetch 候选读取/心跳/timeout 修复仍需推进。
2. 国内 official 源需 Tavily/browser fallback 打通 article URL → body 链路。
3. 等 body_fetch 真实产出后，bridge 才有新材料可推演。
