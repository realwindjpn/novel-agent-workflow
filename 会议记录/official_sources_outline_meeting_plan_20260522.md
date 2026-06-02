# official_sources_outline_meeting_plan_20260522

状态：RUNNING
启动时间：2026-05-22 21:35
边界：只讨论，不改正文，不提交git，不改大纲。

## Context
- /root/workspace/科武纪元/会议记录/official_sources_outline_context_20260522.md

## MODEL_LEDGER
| 角色 | provider/model | 子任务名 | 输出文件 | callback |
|---|---|---|---|---|
| 主席/结构 | aiapi-gpt55 / gpt-5.5 | kewu-official-outline-chair-20260522 | /root/workspace/科武纪元/会议记录/official_sources_meeting_chair_aiapi_gpt55_20260522.md | /root/workspace/科武纪元/会议记录/official_sources_meeting_aiapi_gpt55_done_20260522.json |
| 科学红线 | zai / glm-5.1 | kewu-official-outline-science-glm51-20260522 | /root/workspace/科武纪元/会议记录/official_sources_meeting_science_zai_glm51_20260522.md | /root/workspace/科武纪元/会议记录/official_sources_meeting_zai_glm51_done_20260522.json |
| 编辑/执行审计 | alibaba / qwen3.6-plus | kewu-official-outline-editor-qwen-20260522 | /root/workspace/科武纪元/会议记录/official_sources_meeting_editor_qwen_20260522.md | /root/workspace/科武纪元/会议记录/official_sources_meeting_qwen_done_20260522.json |

## 验收
- 三份报告至少一份完成即 PARTIAL；三份完成再汇总裁决。
- 若模型失败，保留 child log 和 callback，标 BLOCKED_BY_MODEL，不视为采集失败。
