# 中文 README 改写 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将根目录 README 改为第一人称、以中文为主的项目参与说明与使用指南。

**Architecture:** `README.md` 是唯一交付文件。它以原项目为基础、我的后续参与为主线，保留实际启动命令、端口和安全边界；实现细节继续由 `web/README.md` 与 `docs/` 承担。

**Tech Stack:** Markdown、Git、现有 Windows 启动器与本地 MCP 运行契约。

---

### Task 1: 重写根目录 README

**Files:**
- Modify: `README.md`

- [x] **Step 1: 根据提交历史提炼叙述主线**

使用以下提交类别作为事实来源：网页运行器与启动器、本地书库与 MCP、自由创作与浮动工作台、可恢复回收区。不要逐条列出提交或夸大为原项目的全部创作。

- [x] **Step 2: 写入中文 README**

README 必须包含：项目来源和我的参与说明、自然语言概述的核心能力、可复制的 Windows 启动命令、`localhost:8080` 与 `8081` 的区别、选书与自由创作的日常路径、回收区说明，以及贡献范围边界。

- [x] **Step 3: 校验文档**

Run: `git diff --check && rg -n "F:\\\\bookworkflow" README.md`

Expected: `git diff --check` 成功；README 不把个人绝对路径写成通用默认路径。

- [x] **Step 4: 提交并推送**

```powershell
git add README.md
git commit -m "docs: rewrite Chinese project overview"
git push origin main
git push partner main:codex/local-mcp-library-plan
```
