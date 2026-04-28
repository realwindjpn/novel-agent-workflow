---
title: 跟踪表维护策略
created: 2026-04-28
updated: 2026-04-28
type: concept
tags: [writing-rule, outline]
sources: [小说综合跟踪表.md]
confidence: high
---

# 跟踪表维护策略

唯一主跟踪表：`/root/workspace/科武纪元/小说综合跟踪表.md`。

## 降级文件
- `/root/workspace/科武纪元/新版/chapter-track.md`：历史快照。
- `/root/workspace/科武纪元/chapter-track.md`：旧版历史快照。

## 后续规则
章节修改后只更新：
1. `小说综合跟踪表.md`
2. Wiki 相关页与 `log.md`
3. Git commit

不再重复维护 chapter-track，避免状态分裂。

## 备份策略
Git 是常规版本记录。普通小修不建备份。

只在以下情况建备份：
- 多章批量精修
- 大纲大改
- 卷界调整
- 删除/移动/重编号
- 上传前最终稿

原则：工具只保留必要整合项，不能增加维护负担。
