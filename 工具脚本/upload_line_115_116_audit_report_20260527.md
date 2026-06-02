# 审计报告：upload_line_115_116_sixrole_draft_runner_20260527.py

## 审计时间：2026-05-27T11:38
## 审计人：子代理 (alibaba/qwen3.6-plus)

---

## 一、副作用审计结果

### 已确认无副作用（正文/已投稿/git 安全）

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 新版/第115章.md | **未修改** | mtime=2026-05-15 07:15:47（runner启动于11:31） |
| 新版/第116章.md | **未修改** | mtime=2026-04-29 01:10:26 |
| 已投稿/第115章.txt | **不存在** | 未执行export_txt |
| 已投稿/第116章.txt | **不存在** | 未执行export_txt |
| 备份目录/上传线_20260527/ | **为空** | 未执行write_back（备份文件未创建） |
| git commit | **无相关commit** | git log最新=09b538f "refine: chapter 270" |
| 番茄草稿箱 | **未上传** | 进程在AUTHOR_REFINE round2被kill，未到draft_upload阶段 |
| runner进程 | **已kill，无残留** | ps确认无pid 121558，无hermes子进程 |

### 执行进度（state.json 记录）

- `11:31:31` RUNNER_START
- `11:31:31` ch115 START → PRE_REVIEW（editor+advisor原始审核）
- `11:33:29` ch115 AUTHOR_REFINE round 1（xiaomi/mimo-v2.5-pro调用）
- `11:38:04` ch115 MACHINE_GATE → **FAILED** (TRUNCATION_MARK, 番茄口径7115)
- `11:38:04` ch115 AUTHOR_REFINE round 2 → **被kill**

### 产生的中间文件（可安全清理）

- `审核记录/上传线/20260527_115_116/raw/ch115_pre_editor.json` (editor预审结果)
- `审核记录/上传线/20260527_115_116/raw/ch115_pre_advisor.json` (advisor预审结果)
- `审核记录/上传线/20260527_115_116/raw/ch115_author_round1.json` (作者第一轮精修，含TRUNCATION_MARK)
- `审核记录/上传线/20260527_115_116/state.json` (状态文件)
- `审核记录/上传线/20260527_115_116/events.jsonl` (事件日志)

### 精修区文件（需关注）

- `精修区/第115章_东屿局势_精修.txt` (mtime=11:36:31, 12907 bytes)
- **非本runner脚本写入**（脚本中无`精修区`路径）
- 疑为主控在启动runner前后的其他操作生成
- 内容格式正常（首行标题、末行本章完），但未经六角色闭环验证

### 结论

> **本runner脚本被kill时只完成了ch115的预审+第一轮精修（机器门禁失败），未进入write_back/export_txt/draft_upload/git_commit阶段。正文源文件、已投稿目录、git历史均未被修改。无上传副作用。**

---

## 二、脚本设计问题诊断

### 核心问题：主控自写自执行，无安全门

1. **`if __name__ == '__main__': main()` 直接执行全部流程**——启动即开始调用模型、写文件、执行上传
2. **无dry-run/preview模式**——无法先查看调度计划再确认执行
3. **无显式provider/model日志**——调度哪个模型全靠ROUTES字典，运行时不打印确认
4. **write_back直接覆盖源文件**——虽然有备份，但备份和覆盖在同一流程中
5. **draft_upload三步连续执行**——dryrun→check-login→execute自动串联，无人工断点

### 次要问题

- `call()`函数用subprocess调hermes CLI，exit_code非0时没有足够日志
- author_round1的stdout包含diff格式标记（`┊ review diff`），说明模型返回了非纯净正文
- 精修区文件来源不明，非本脚本写入

---

## 三、合格后台worker方案设计

### 设计原则

1. **主控只监控，不生成内容**——主控通过hermes launch_child派发任务
2. **显式provider/model**——每个角色调用前后记录provider/model/timestamp
3. **分阶段门禁**——每阶段完成后写event，主控可随时暂停/恢复
4. **安全断点**——write_back前必须确认，draft_upload需二次确认
5. **可幂等重跑**——基于state.json跳过已完成阶段

### 架构

```
主控(Hermes Agent)
  ├── launch_child("upload-115") → runner.py --chapter 115
  │     └── 调用模型: author/editor/reader/advisor (显式provider/model)
  │     └── 每阶段写events.jsonl + state.json
  ├── launch_child("upload-116") → runner.py --chapter 116
  │     └── 同上
  └── monitor脚本 → 读state.json/events.jsonl，向用户汇报
```

### 关键改动

1. 移除`if __name__ == '__main__'`的自动执行，改为CLI参数控制
2. 添加`--chapter`参数，每次只处理一章
3. 添加`--stage`参数，支持从指定阶段恢复
4. 添加`--dry-run`模式，只输出调度计划不执行
5. 添加`--confirm-upload`参数，默认不执行上传
6. 每次模型调用前后打印显式日志：`[DISPATCH] role=author provider=xiaomi model=mimo-v2.5-pro`
