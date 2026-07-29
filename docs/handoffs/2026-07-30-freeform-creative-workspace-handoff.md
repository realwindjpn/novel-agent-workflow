# 自由创作工作区开发交接报告

日期：2026-07-30

## 一、交接目标

把当前“白话模式”的严格命令翻译器升级为真正的自由创作工作区：模型可以自然讨论、主动决定、推翻未确认方向并生成试写；用户确认方案后，系统才把内容编译成现有 core 所需的结构化数据，并通过原有 MCP 状态机正式写入。

本次交接只包含已确认的设计和完整开发计划，功能代码尚未开始实现。

## 二、仓库与分支

- 本地仓库：`F:\bookworkflow`
- GitHub：`zhuxice-ctrl/bookworkflow`
- 工作分支：`codex/local-mcp-library-plan`
- 目标分支：`main`
- 现有 PR：`#1`，保持 Draft
- 功能基线提交：`d932d9f fix: keep local-only launcher available`
- 设计提交：`ff8a5bd docs: design freeform creative workspace`
- 计划提交：`3f4dd2c docs: plan freeform creative workspace`

开始执行前必须运行：

```powershell
cd F:\bookworkflow
git status -sb
git log --oneline -5
```

工作树应当干净，分支必须是 `codex/local-mcp-library-plan`。不要切到 `main` 直接开发。

## 三、权威文档

按以下顺序阅读：

1. `docs/superpowers/specs/2026-07-30-freeform-creative-workspace-design.md`
2. `docs/superpowers/plans/2026-07-30-freeform-creative-workspace.md`
3. `docs/superpowers/specs/2026-07-29-local-library-chat-init-ux-design.md`
4. `docs/superpowers/specs/2026-07-28-local-mcp-library-design.md`

第 1 项定义产品行为，第 2 项定义 11 个实施任务和精确验收步骤。后两项提供现有书库、本地 MCP、路径和公共端隔离背景。

如果实现与权威设计冲突，停止执行并向用户报告，不要自行改变产品方向。

## 四、用户已经确认的产品决策

以下决策无需再次询问：

1. 用户说“你来决定”时，模型可以自主提出完整创意方向；正式写入前必须给用户一键确认。
2. 模型认为内容成熟时可以主动建议生成方案；用户也可以随时点击“生成创意方案”。
3. 自由创作对话按书籍持久保存，重启和重新打开书籍后自动续聊。
4. 左侧固定 22 步默认收进“创作进度”抽屉，仅在正式检查点展开。
5. 大纲锁定前允许生成试写片段，但只能存入创作草稿区，不能成为正式章节。
6. 采用“双层创作架构”：自由创作层负责发散，结构化编译层负责生成正式契约，现有 core 负责最终状态和安全闸门。
7. 本地无法读写时继续保留浏览器会话，提供一个 ZIP 下载链接和手动导入流程。
8. 导入碰撞必须让用户选择合并、另存副本或取消，禁止静默覆盖。
9. 模型错误必须显示真实原因，不能静默降级为“没听懂”。
10. 页面不能再把 `<b>` 等标签作为普通文字显示。

## 五、根因判断

当前问题不是模型本身能力不足，而是实现把四种职责压进同一轮严格 JSON：

- 创意生成；
- 意图识别；
- CLI 参数构造；
- 单行 JSON 序列化。

`web/llm.js` 当前要求所有响应符合有限的 JSON kind，并使用偏保守的生成参数。任何网络、跨域、解析或形状错误都会返回 fallback；`web/chat.js` 随即调用关键词规则引擎，所以开放输入会显示“没听懂”。15 字段 intake 也被直接暴露给用户。

正确修复不是单纯提高模型温度，而是拆开自由回复、成熟度判断、结构化编译和正式执行。

## 六、实施任务顺序

必须按开发计划顺序完成，不要并行修改相同文件：

1. 创建受限的 active-book 创作存储。
2. 持久化对话、事实、方案和试写。
3. 实现安全的单 ZIP 导出与导入。
4. 通过现有认证本地桥暴露创作存储。
5. 增加浏览器存储和零依赖 ZIP 降级。
6. 拆分自由创作、成熟度判断和结构化编译模型调用。
7. 创建自由创作控制器。
8. 把确认方案编译为正式 plan，同时保持 core 闸门。
9. 把白话页面改为自由创作主界面和抽屉布局。
10. 完成下载、导入预览、碰撞选择和恢复状态。
11. 更新文档，运行全量回归和真实浏览器验收。

每个任务必须遵循 TDD：先写失败测试，确认失败原因，再写最小实现，运行聚焦测试，最后单独提交。

建议使用 `subagent-driven-development`：每个任务由新的实现代理完成，然后做规格和代码质量审查。进度写入该计划专属账本，防止上下文压缩后重复实施。

## 七、不可突破的边界

- 不删除、重命名或清理 `book/` 中现有用户书籍和验收目录。
- 不操作用户正在运行的 ngrok 或其他穿透进程。
- 不新增任意路径读写 API；创作存储只能访问当前书籍的 `creative/` 子树。
- 不让未确认内容改变 `workflow.json`、章节账本或发布凭证。
- 不削弱 core 的评审、签发、锁定、发布和防覆盖规则。
- 不把 API 凭据写进对话、ZIP、日志或仓库。
- 公共 8081 页面不能读取本地创作资料，本地 API 路径必须继续返回 404。
- 不把试写稿伪装成正式章节。
- 不在 `web/sources.js` 手工修改 Python 快照；需要同步 core 时只能运行 `scripts/gen_web_sources.py`。
- PR #1 保持 Draft，除非用户明确要求 Ready for review。

## 八、当前运行方式

本地开发建议使用：

```powershell
.\一键启动.cmd --no-tunnel
```

该模式启动本地 8080 和公共内存版 8081，但跳过内置 cloudflared，不影响现有 ngrok。关闭启动器窗口会停止本项目服务。

开始浏览器验收前要先检查端口拥有者：

```powershell
Get-NetTCPConnection -State Listen |
  Where-Object { $_.LocalPort -in 8080,8081 } |
  Select-Object LocalAddress,LocalPort,OwningProcess
```

只允许停止命令行明确包含 `scripts\launch_web.py` 的进程。

## 九、最低验证要求

聚焦开发期间按计划运行相应测试。最终至少运行：

```powershell
node --test tests\js\test_local_adapter.mjs tests\js\test_creative_adapter.mjs tests\js\test_llm_adapter.mjs tests\js\test_creative_chat.mjs
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\release_check.py
.\.venv\Scripts\python.exe _local_acceptance.py
```

必须得到：

- JavaScript 全部通过；
- Python 全部通过，平台跳过项必须有明确原因；
- `RELEASE_CHECK_PASS`；
- 本地 acceptance 每一步为 `OK`；
- `git diff --check` 无错误。

## 十、真实页面验收

必须使用一次性 QA 书执行，不要用用户正式书籍做破坏性验证。

重点验证：

1. “你来决定这个创意方向”返回真实创意内容，不出现 JSON、CLI、15 字段表单或“没听懂”。
2. 刷新页面、重启启动器、重新打开书籍后继续同一段对话。
3. 模型主动建议和用户手动按钮都能生成创意方案。
4. 用户确认采用后，只出现正式 plan 预览；未点击执行前 core 状态不变。
5. 大纲未锁定时可以保存试写，但正式章节列表不增加。
6. 模拟写盘失败后出现“需要下载备份”，ZIP 可以下载并重新导入。
7. 导入前显示书名、导出时间、对话、方案、草稿数量。
8. 合并、另存副本、取消三条路径都不静默覆盖。
9. 390×844 窄屏下输入框、方案按钮、抽屉和备份入口可达。
10. 控制台 error/warn 为空。
11. 公共端不显示本地创作资料，本地 API 路径返回 404。

## 十一、完成定义

只有同时满足以下条件才算完成：

- 11 个计划任务全部有独立提交和测试证据；
- 设计中的 12 项 acceptance criteria 全部覆盖；
- 本地真实页面已创建、续接、编译、确认、试写、导出、导入；
- 公共端隔离仍有效；
- 全量测试、发布检查、本地 acceptance 和 GitHub CI 通过；
- 工作树干净；
- 当前分支推送到远端；
- PR #1 仍是 Draft。

## 十二、已知注意事项

- 这是大功能，不应只改 `temperature` 或提示词后宣称完成。
- `web/chat.js`、`web/llm.js`、`web/app.js` 已较大，计划通过新建 `web/creative.js`、`web/zip.js` 和 `web/creative-chat.js` 控制复杂度。
- ZIP 必须是单文件、无第三方运行依赖，并防止路径穿越、链接、超大解压和凭据泄露。
- 浏览器自由回复应接受普通文本；只有编译调用使用结构化校验和一次修复重试。
- 结构化编译失败不得清空对话，也不得调用关键词菜单。
- 当前 core 的 15 字段 intake 仍是正式写入契约，只是不再直接要求用户填写。

## 十三、给小策的启动指令

可以把下面这段原样交给执行者：

> 在 `F:\bookworkflow` 的 `codex/local-mcp-library-plan` 分支执行自由创作工作区计划。先完整阅读 `docs/superpowers/specs/2026-07-30-freeform-creative-workspace-design.md` 和 `docs/superpowers/plans/2026-07-30-freeform-creative-workspace.md`。严格按 Task 1 到 Task 11 顺序做 TDD，每项独立提交并做规格/代码质量审查。不要修改或删除现有 `book/` 用户资料，不要操作 ngrok，不要开放任意磁盘路径，不要削弱 core 闸门，保持公共 8081 与本地创作资料隔离。完成后运行全部 JS/Python、`release_check.py`、`_local_acceptance.py` 和真实浏览器验收，推送当前分支，等待 PR #1 CI，通过后保持 PR 为 Draft并提交完整执行报告。
