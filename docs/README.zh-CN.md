# Novel Agent Workflow 中文说明

[English](../README.md) · [初学者指南](BEGINNER_GUIDE.zh-CN.md)

这是一个面向长篇小说的**文件优先、工具中立、门禁驱动**工作流。它帮助初学者从一个想法出发，经过概念审查、故事圣经、大纲审查、章节签发、作者候选稿、独立审查、返修复审，最终生成可追溯的发布凭证。

它不承诺“一键写完小说”。它解决的是长篇协作中常见的假完成：大纲未过就写章节、候选稿冒充终稿、自写自审、审查无证据、返修后旧门禁仍被当成有效。

## 主链

`idea interview → concept review/repair → story bible → master outline review/repair → volume outline review/repair → chapter outline review/repair → outline all-PASS → chapter issue → author draft → independent reviews → repair/re-review → release receipt`

所有大纲层级均为 `PASS` 并锁定前，禁止签发章节。

## 可选模型路由

核心工作流仍可离线运行，不依赖模型或网络。需要接入模型时，可使用
provider-neutral 配置：

```bash
novel-workflow model init-config model_routing.toml
novel-workflow model smoke --config model_routing.toml
novel-workflow model route-plan --config model_routing.toml \
  --genre 科幻 --risk physics --risk combat
novel-workflow model model-ledger --config model_routing.toml \
  --genre 科幻 -o model-ledger.jsonl
```

配置只保存环境变量名，不保存密钥值。每次运行先做新鲜的语义响应
smoke，只有本次 `PASS` 候选可分配角色；旧 ledger 不能授权新运行。
候选可使用 OpenAI-compatible HTTP 或自定义命令适配器。`author`、
`editor`、`reader` 是核心角色；顾问按题材与大纲风险动态选择，军事与
科学不是全局默认。详见 `templates/model_routing.example.toml` 与
`templates/env.example`。

仓库不内置、不推荐任何生产模型名单或私有节点，所有 provider/model 均由
用户自行配置。既可让一个模型分次承担多个角色，也可为不同角色配置不同
模型。这里的“独立”是指角色调用与证据身份分离：作者、编辑、读者应使用
不同的 provenance identifier；并不强制底层 model 名称不同。

六角色会显著放大调用量。先用 `model budget` 按启用角色数、预计返修轮数、
每次输入/输出 token 估算总调用量；只有用户自行填写单价时才估金额，不会
臆测价格。再看 `model route-plan` 的 `continuity`：单路角色标
`READY_SINGLE_ROUTE`，无人值守有断链风险；至少两条本轮 smoke PASS 路由才
标 `READY_WITH_FALLBACK`。运行时应逐角色落盘，首选路由失败后切到下一条
当前 PASS 候选；全部耗尽须显式 BLOCKED，不能静默卡死。恢复时从首个未完成
角色继续，勿重复烧掉已完成角色的算力。

## 六角色

| 角色 | 职责 | 证据契约 |
|---|---|---|
| `controller` | 拆阶段、记状态、核证据、阻断假完成。 | 状态文件、事件流、发布凭证。 |
| `author` | 按章节契约和 Author Role OS 写候选稿。 | 候选稿与写前卡校验和。 |
| `editor` | 独立编辑审查：结构、节奏、文体、DEAI、人味与读者尊重。 | `editor:<id>` 审查文件。 |
| `reader` | 独立真实读感审查：清晰、沉浸、疲劳、过度解释。 | `reader:<id>` 读感文件。 |
| `military_consultant` | 有战术、冲突、组织、后勤内容时审查可信度。 | `military:<id>` PASS/FAIL/SKIP_WITH_REASON。 |
| `science_consultant` | 有物理、生物、技术、世界规则内容时审查可信度。 | `science:<id>` PASS/FAIL/SKIP_WITH_REASON。 |

编辑与读者不得与作者同一身份，读者也不得与编辑同一身份。军事、科学无适用内容时可以 `SKIP_WITH_REASON`，但必须写明检查范围与跳过原因，不能缺席。

## 章节门禁

- `author`：候选稿存在，且有 Author Role OS 写前卡。
- `editor`：DEAI 与 audience respect 证据存在且 PASS。
- `reader`：真实读感证据存在且 PASS。
- `military`：PASS、FAIL，或带理由的 SKIP_WITH_REASON。
- `science`：PASS、FAIL，或带理由的 SKIP_WITH_REASON。

返修会把受影响门禁重置为 `PENDING`，删除旧发布凭证，并要求重新审查。

## 快速验证

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
python -m unittest discover -s tests -v
python scripts/release_check.py
```

## 不包含

- 小说正文、私有设定、账号状态、浏览器资料、凭据或发布自动化。
- 模型调用、托管服务接入、第三方仓库代码复制。
- 任何用户私有项目的专名、路径、日志或正文。

## 许可

Apache License 2.0 仅覆盖本公开仓库。用户自己的正文、设定、模型输出和资料仍归用户或原权利人所有。
