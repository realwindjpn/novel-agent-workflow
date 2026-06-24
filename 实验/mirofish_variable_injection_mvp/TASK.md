# MiroFish × 科武纪元：变量注入推演 MVP

## 目标
验证 MiroFish 类“变量注入 + 群体/势力推演”是否能为《科武纪元》提供真实增益。

## 硬边界
- 沙盒实验，不接入正式流程。
- 不改大纲。
- 不改正文。
- 不改已投稿TXT。
- 不改现有 skill。
- 不入 RAG/知识库。
- 不建长期 cron。
- 不影响每日自循环/上传线。

## 项目目录
`/root/workspace/科武纪元/实验/mirofish_variable_injection_mvp/`

## 输入背景
- MiroFish 思路：GraphRAG 实体关系 → 多智能体/群体推演 → 变量注入 → Report Agent 汇总。
- 科武现有机制：SenseNova/确定性采集 → 素材卡 → Wiki/RAG/角色OS → 多模型会议/六角色 → 大纲备注或章节精修。
- 本实验只取轻量机制：变量注入、势力反应、连锁冲突、反模式。

## 测试变量
变量：`某国突然宣布对民用AI训练集群实施许可证制度，个人/小企业训练大模型必须登记算力来源、数据来源和用途。`

## 必须产物
1. `README.md`：实验说明、运行方式、边界。
2. `variable_injection_template.md`：可复用 prompt 模板。
3. `test_case.json`：本轮变量、输入实体、势力、约束。
4. `simulation_result.md`：一次推演结果。
5. `EVALUATION.md`：评估是否值得吸收。
6. `STATUS.json`：阶段状态。
7. `EXECUTION_LOG.md`：执行记录。

## 推演输出要求
`simulation_result.md` 至少包含：
- 受影响实体/势力。
- 第一层反应。
- 第二层连锁。
- 赢家/输家。
- 可写成章节冲突的 3 个钩子。
- 对角色OS的影响。
- 反模式/禁忌。
- 是否需要进入六角色会议。

## 评估标准
`EVALUATION.md` 必须回答：
- 是否比现有六角色/素材会多出有效冲突链？
- 是否增加复杂度？增加在哪里？
- 是否容易幻觉？如何防？
- 是否能接 SenseNova 素材？
- 是否只需 1 次 LLM 调用？
- 是否建议正式吸收？结论只能为：`吸收 / 只保留参考 / 不吸收`。

## 模型分工
- MiMo Pro：写 MVP 产物草案。
- SkyClaw：执行官与只读评估，检查是否越界、是否有用。
- 主控：最终验收与裁决。

## 汇报规则
- 普通执行静默。
- 完成/阻塞/超时写 `/root/workspace/agent_inbox/mirofish_kewu_mvp.jsonl`。
- 若缺资料，可用项目已有 Wiki/INDEX 摘要，不做大规模采集。
