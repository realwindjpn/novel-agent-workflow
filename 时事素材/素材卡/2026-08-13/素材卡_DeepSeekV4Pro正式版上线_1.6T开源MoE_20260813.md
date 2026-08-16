# 素材卡｜DeepSeek V4 Pro 正式版（"满血版"）上线：1.6T 开源 MoE

- 日期：2026-08-13（入卡）；关键节点：2026-04-24 V4 预览版双版本开源 → 2026-07-15/21 V4 正式版（GA）全量上线 → 2026-07-24 老模型名退役
- 领域：人工智能/开源模型/算力主权
- 状态：CONFIRMED_PRIMARY_USABLE（DeepSeek 官方 + 腾讯云开发者社区 + 36Kr 一手报道）
- 适用：CHAPTER_PREP_ONLY；不自动改大纲或正文
- 覆盖关注项：AI 模型发布线（DeepSeek V4 Pro / dp4pro）

## 已证事实

1. DeepSeek V4 预览版 2026-04-24 发布：V4-Pro（总参数 1.6T、每 token 激活 49B）+ V4-Flash（总参数 284B、激活 13B），MoE 架构，全系 1M token 上下文，MIT 协议开源权重与技术报告。
2. V4 正式版（GA，"满血版"）2026-07-15 全量上线、7 月中下旬公告；V4-Pro 正式版为社区关注焦点（"dp4pro"）。7 月 24 日起旧模型名 deepseek-chat / deepseek-reasoner 停服，请求转 V4 系列。
3. 官方评测：V4-Pro 在数学、STEM、竞赛级代码等核心推理评测中超越当时所有已公开开源模型，比肩顶级闭源模型。
4. 定价（预览版）：缓存命中输入 1 元/百万 tokens、未命中 12 元、输出 24 元；正式版首推峰谷计费（V4 Pro 输出离峰约 0.87 美元/百万、高峰 1.74 美元；Flash 更低），延续低成本策略。
5. 能力：非思考+思考双模式（reasoning_effort 可调）、Json Output、Tool Calls、对话前缀续写；兼容 OpenAI ChatCompletions 与 Anthropic 两种接口；Agentic Coding 内部反馈优于 Anthropic Sonnet 4.5、接近 Claude Opus 4.6 非思考模式。
6. 架构创新：预训练 33T tokens；2026-01 mHC（流形约束超连接）论文 + Engram 条件记忆模块（O(1) 哈希替代注意力，100B 嵌入表卸载 CPU 内存）。

## 小说映射（AI 域 plot_threads：算力主权 / 技术共和国 / 硬反馈闭环）

- 1.6T 开源模型 + 1M 上下文 + 超低定价 → "开源算力平权 vs 闭源封锁"科幻冲突的现实锚点。
- mHC/Engram 条件记忆 → "记忆外置 / 残缺阵列训练"设定来源。
- 峰谷计费 → 制度约束层细节（算力资源分配制度）可引用。

## 待核验

- V4-Pro 正式版精确发布日期（7-15 灰度 vs 7-21 公告，社区说法不一）——建议补抓 DeepSeek 官方 API Docs 或官方公告。
- 本卡为技术/产业线；用户点名关注（dp4pro）已覆盖。
