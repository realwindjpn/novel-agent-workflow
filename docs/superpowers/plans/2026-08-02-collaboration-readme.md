# 协作分支 Codex README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为合作仓库的 `codex/local-mcp-library-plan` 分支提供可独立接手的中文 README。

**Architecture:** 只重写根目录 `README.md`，将当前项目的运行架构、接手路径、验证方式和 Git 边界集中在一个入口。文档不改变任何运行行为，也不面向或推送到合作仓库 `main`。

**Tech Stack:** Markdown、Git、Python CLI、本地 MCP 桥接、Windows 启动器。

---

### Task 1: 编写协作分支交接 README

**Files:**
- Modify: `README.md`

- [x] **Step 1: 提取当前分支事实**

以 `src/novel_workflow/core.py`、`src/novel_workflow/mcp_server.py`、
`scripts/local_mcp_bridge.py`、`scripts/launch_web.py`、`web/` 和测试目录
为事实来源，说明状态机、MCP、书库、自由创作与回收区；明确无平台投稿实现。

- [x] **Step 2: 重写 README**

按以下顺序写作：分支身份与 Git 禁区、运行架构、启动方式、接手阅读路径、
日常验证、关键安全边界、已实现/未实现能力。每条命令必须可从仓库根目录运行。

- [x] **Step 3: 校验 README**

Run: `git diff --check && rg -n "codex/local-mcp-library-plan|8080|8081|番茄|main" README.md`

Expected: 格式检查通过；README 明确协作分支与合作仓库 `main` 的隔离。

- [x] **Step 4: 提交并仅推送合作分支**

```powershell
git add README.md
git commit -m "docs: add collaboration branch handoff"
git push partner HEAD:codex/local-mcp-library-plan
```
