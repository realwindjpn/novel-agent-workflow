# 科武纪元 · 工作流体系

## 仓库结构

```
novel-agent-workflow/
├── .github/
│   └── WORKFLOW.md           # 本文件
├── docs/                     # 流程文档
│   ├── 知识库构建流程.md
│   ├── 六角色四层审核流程.md
│   ├── 采集调度器说明.md
│   └── 写作执行规范.md
├── scripts/                  # 工具脚本
│   ├── orchestrator_v3.py    # 素材采集调度器
│   ├── search_semantic.py    # RAG语义检索
│   └── build_index.py        # RAG索引构建
├── templates/                # 模板文件
│   ├── 素材卡模板.md
│   ├── 审核包模板.md
│   └── WAL模板.md
└── wiki/                     # 小说Wiki体系
    ├── chapters/             # 章节页
    ├── chapter-index/        # 卷索引
    ├── entities/             # 角色/势力
    ├── concepts/             # 设定/术语
    └── plot-threads/         # 伏笔线
```

## 核心流程

### 1. 知识库构建流程
```
查重(INDEX.md) → 定向采集 → 生成素材卡 → 入库 → 填充RAG → 写作引用
```
- 知识库位置: `知识库/INDEX.md`
- RAG索引: `rag_kb/science/cards/science_cards.jsonl`
- 素材卡模板: `知识库/{科技线}/素材卡_*.md`

### 2. 六角色四层审核流程
```
写作 → Git提交 → Wiki更新 → RAG扫描 → 六角色外审 → 门禁通过 → 下一章
```
- 六角色：主控、作者、编辑、读者、军事顾问、科学顾问
- 四层：格式→大纲→风格→敏感词
- 审核包模板: `templates/审核包模板.md`

### 3. 素材采集流程
```
搜索链接 → 爬虫采集 → 去重 → 生成素材卡 → 归档原始文件
```
- 调度器: `scripts/orchestrator_v3.py`
- 支持平台：微信/B站/观察者网/中科院/物理所/RSS

## 分支策略

| 分支 | 用途 |
|------|------|
| main | 稳定版本（已投稿章节+审核通过的流程） |
| feature/workflow | 工作流改进（采集器/审核流程/知识库） |
| feature/chapter-NNN | 单章写作分支 |
| hotfix | 紧急修复（错别字/敏感词） |

## 提交规范

- `feat: 写作第NN章` - 新章节
- `fix: 修改第NN章` - 章节修改
- `docs: 更新审核流程` - 流程文档
- `scripts: 新增采集器` - 工具脚本
- `wiki: 更新角色设定` - Wiki更新
