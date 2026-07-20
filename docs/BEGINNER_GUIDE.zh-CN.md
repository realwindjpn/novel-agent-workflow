# 初学者指南：从一个想法到章节签发

本指南假设你只有一个原始想法。它的目的不是让你立刻写正文，而是阻止你过早起草。

## 0. 安装

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

## 1. 初始化项目

```bash
novel-workflow init demo --title "静默中继"
```

这会创建 `workflow.json`、`.novel-workflow/` 状态目录，以及 idea、story-bible、outlines、chapters、reviews、releases 等工作目录。

## 2. 结构化初始化访谈

使用 `templates/idea_interview.md`，按七步逐项确定：

1. 目标读者、题材定位、预计总字数、卷章规模。
2. 核心梗概、持续冲突、代价与结局承诺。
3. 时代地点、社会结构、技术/魔法、经济与世界硬规则。
4. 主角、配角、对立力量、关系网、知识边界与人物弧。
5. 视角、时态、语气、节奏、对白、描写密度与禁用写法。
6. 总体阶段、卷功能、升级阶梯、中点、低谷、高潮与伏笔回收。
7. 内容边界、平台风险，以及从既往阅读中提炼的抽象技法。

以前读过、分析过的小说可用于提炼抽象规律，例如升级节奏、线索距离、关系压力、人物变化触发点；不可复制原句、专名、独特设定组合、场景、人物套装或私有语料。系统只记录“规律 + 本项目如何变形 + 相似性检查”。

可随时检查完整度：

```bash
novel-workflow intake-check demo --interview '{...}'
```

它会返回完成比例、缺失字段和下一问。15项未完整时，概念审查会被硬闸阻断。完成后再记录：

```bash
novel-workflow idea demo --summary "一句话概念" --interview '{完整的15项结构化JSON}'
novel-workflow intake-check demo
```

## 3. 概念审查与返修

概念必须 PASS，才能写故事圣经。

```bash
printf '# Concept Review
PASS
' > demo/concept-review.md
novel-workflow concept-review demo PASS --artifact concept-review.md --reviewer controller:concept-reviewer
```

如果 FAIL，先修想法，再复审：

```bash
novel-workflow concept-repair demo --summary "修订后的一句话概念" PASS --artifact concept-review.md --reviewer controller:concept-reviewer
```

## 4. 故事圣经

使用 `templates/story_bible.md`。概念 PASS 后记录：

```bash
printf '# Story Bible
世界规则、人物、知识边界。
' > demo/story-bible.md
novel-workflow bible demo --artifact story-bible.md
```

## 5. 大纲阶梯

按顺序使用：

1. `templates/outline_master.md`
2. `templates/outline_volume.md`
3. `templates/outline_chapter.md`

每一层都必须写作、审查、必要时返修，并 PASS 后才能进入下一层。

```bash
novel-workflow outline-write demo master --artifact outlines/master.md
novel-workflow outline-review demo master PASS --artifact reviews/master-review.md --reviewer controller:master-reviewer
novel-workflow outline-write demo volume --artifact outlines/volume-1.md
novel-workflow outline-review demo volume PASS --artifact reviews/volume-review.md --reviewer controller:volume-reviewer
novel-workflow outline-write demo chapter --artifact outlines/chapter-1.md
novel-workflow outline-review demo chapter PASS --artifact reviews/chapter-outline-review.md --reviewer controller:chapter-reviewer
novel-workflow outline-lock demo
```

任何一层 FAIL，都要 `outline-repair` 并复审。所有大纲层级 PASS 前，章节签发会被 CLI 拒绝。

## 6. 章节签发

```bash
novel-workflow issue demo 1 --title "第一束信号" --goal "引出争议信号，但不解决谜题"
```

签发只生成章节契约，不等于正文候选稿。

## 7. 候选稿与审查

### 先看算力预算与断链风险

六角色不是六次调用就结束。一次初稿通常调用作者、编辑、读者；若章节涉及军事或科学，还会增加顾问。返修后，受影响角色必须重新读取全文并复审。最保守的全角色估算为：

`调用次数 = 本轮启用角色数 × 预计完整轮数`

例如启用作者、编辑、读者、军事、科学五个模型角色，预计初审后返修两次，即三轮，最多约15次角色调用。若每次输入约1.2万token、输出约2500 token，估算总量约21.75万token。长章、长大纲、跨章材料会继续增加输入。实际只重跑受影响门禁时可低于此数；模型重试和超时重投可能高于此数。

先运行预算命令：

```bash
novel-workflow model budget --config model_routing.toml \
  --genre 科幻 --risk physics --risk combat \
  --revision-rounds 3 \
  --input-tokens-per-call 12000 \
  --output-tokens-per-call 2500
```

命令必给调用次数和token估算。只有你在配置中自行填写`input_cost_per_million`与`output_cost_per_million`时，它才计算金额区间；价格缺失时明确显示未知，不猜费用。

再运行`model route-plan`。输出中的`continuity`有三种状态：

- `READY_WITH_FALLBACK`：该角色至少有两个本轮smoke通过的候选，可承受一次路由故障。
- `READY_SINGLE_ROUTE`：可运行，但无备用；无人值守执行有中途卡住风险。
- `BLOCKED_NO_ROUTE`：无可用候选，禁止启动该角色。

若任务必须无人值守不断链，每个必需角色至少配置两个候选。运行时首选失败后，应按当前PASS链切换下一候选，并保存失败轨迹。已经完成的角色产物和状态必须先落盘；恢复时从首个未完成角色继续，不得整轮重烧算力。所有候选耗尽时要显式标`BLOCKED`，不能静默悬停或伪报完成。

起草前先填写 `templates/author_role_os_prewrite.md`。写前卡缺少 Author Role OS 必要字段时，CLI 会拒绝记录候选稿。

```bash
novel-workflow draft demo 1 --artifact chapters/chapter-1-draft.md --prewrite chapters/chapter-1-prewrite.md --author author:writer-a
novel-workflow review demo 1 editor PASS --artifact reviews/chapter-1-editor.md --reviewer editor:editor-b
novel-workflow review demo 1 reader PASS --artifact reviews/chapter-1-reader.md --reviewer reader:reader-c
novel-workflow review demo 1 military SKIP_WITH_REASON --artifact reviews/chapter-1-military.md --reviewer military:military-d --reason "本章无战术、组织、指挥、后勤内容。"
novel-workflow review demo 1 science SKIP_WITH_REASON --artifact reviews/chapter-1-science.md --reviewer science:science-e --reason "本章无科学或技术可信度内容。"
```

编辑 PASS 必须包含 `DEAI` 与 `Audience respect`。读者 PASS 必须包含 `Real reading experience`、`Immersion`、`Over-explanation`。

## 8. 返修与发布

门禁 FAIL 后，返修并声明受影响门禁：

```bash
novel-workflow repair demo 1 --artifact chapters/chapter-1-draft-r2.md --affected editor reader
```

受影响门禁会回到 `PENDING`，旧发布凭证会删除，必须复审。

所有门禁满足后，章节是 `READY_TO_RELEASE`。只有显式执行发布命令，才会进入 `RELEASED`：

```bash
novel-workflow release demo 1
novel-workflow check demo --security
```

## 9. 全书视图

当你有不止一章时，用台账看全书进度：

```bash
novel-workflow chapters demo
```

它会读取 `workflow.json.chapters`（每次 issue/review/repair/release 都会同步），显示每章的状态、门禁与发布时间。`.novel-workflow/` 下的章状态文件是事实来源；台账是只读摘要。

## 10. 进阶路线（从初学者到长篇）

上面的初学者路线是最小可行路径：一个想法到一个已发布章节，不用资产卡，不做跨章校验。长篇会逐步引入门禁与资产层。这些都不是发布第一章的前提。

| 等级 | 引入什么 | 防什么坑 |
|------|----------|----------|
| L1 多章串行 | 章节进度台账、串行签发 | 跨章人名/代词/物体漂移 |
| L2 资产管理 | character/scene/object/concept 卡 + 版本号 | 同名设定漂移、角色状态失连 |
| L3 角色一致性门禁 | 编辑/读者审追加六项评分（任一≤2 即 FAIL） | 角色无因突变、知识越界、无代价新能力 |
| L4 跨章一致性 | `CROSS_CHAPTER_CONSISTENCY` 字段 | 通讯中断被默认恢复、物体瞬移 |
| L5 数值自洽 | 科学顾问 `NUMERICAL_CONSISTENCY` | 硬科幻数值自相矛盾 |
| L6 大纲对齐 | 草稿标题 vs 章纲标题（`SOURCE_MISMATCH`） | 写得很好但写错了章 |
| L7 写后 DEAI 机器扫 | NOT_BUT/枚举/总结腔标签扫描，只标不自动改 | AI 味被评成"可接受"就放行 |
| L8 错词机械门禁 | 确定性错词表扫描 | 模型审结构审不出别字 |
| L9 格式清洁 | 清 wikilink、引号配平、首尾格式、禁词 | 发布格式污染 |
| L10 持续推进纪律 | 每章闭环即汇报，不把"会继续"当"已完成" | 汇报失真 |

使用资产卡时，填写 `templates/character_card.md`（以及 scene/object/concept），存到 `assets/` 下，并在章节契约的 `asset_cards_used` 字段列出本章依赖的卡。角色发生有据可查的变化时，写明触发事件，更新卡片并升版本号；无据变化是阻塞性编辑错误。

## 11. 十条最易踩的坑与本工作流的防护

1. **跳过外审直接报完成。** 状态机在所有门禁 PASS 或 SKIP_WITH_REASON 前拒绝 `release`。"改正文了"不等于"闭环了"。
2. **把大纲更新当成正文完成。** 大纲与章节是独立状态。大纲必须 LOCKED 后才能签发章节；锁定后改大纲要走大纲返修，不能静默改章。
3. **把同一次执行冒充多个独立角色。** 一个底层模型可以分次承担多个角色，也可以每个角色使用不同模型；模型由用户自行配置。provenance 是 `role:identifier`，作者、编辑、读者必须使用独立调用上下文和不同 identifier。同一执行身份自写自审会被拒绝。
4. **只读摘要不读全文。** 审稿模板要求 `reviewed_fulltext: true`。按约定，缺此字段的 PASS 无效；后续扫描器可强制。
5. **写前卡走过场。** `record_draft` 在写前卡缺少六个必备字段之一时拒绝记录。一份纯"笔记"过不了。
6. **返修后不重审就报 PASS。** `repair` 把受影响门禁重置为 PENDING，删除旧发布凭证。这些门禁必须重审。
7. **写得好但写错了章。** `record_draft` 比对草稿标题与章纲标题，不一致即 `SOURCE_MISMATCH` 拒绝。
8. **AI 味被评成"可接受"放行。** 编辑 PASS 必须含 DEAI 段；DEAI 清单列出八类违规。一词 PASS 会被拒绝。
9. **角色无因突变。** 编辑与读者模板含六项角色一致性评分；任一项≤2 即阻塞 FAIL。无据变化是 `ASSET_CONFLICT` 或 `TEXT_ERROR`；有据变化是 `REASONABLE_GROWTH` 并升卡片版本。
10. **"会继续"当"已完成"。** `READY_TO_RELEASE` 不等于 `RELEASED`。发布需要显式命令并产生回执。返修会撤销回执。从"门禁过了"到"发出去"之间没有捷径。
