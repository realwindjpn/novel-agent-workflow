# MiroFish × 科武纪元：变量注入推演 MVP

## 实验目标
验证"变量注入 + 群体/势力推演"机制是否能为《科武纪元》冲突设计提供可量化增益。

## 运行方式
1. 填写 `test_case.json`（变量 + 实体/势力/约束）。
2. 将变量输入 `variable_injection_template.md` 模板，调用单次 LLM。
3. 输出 `simulation_result.md`。
4. 按 `EVALUATION.md` 标准判定是否吸收。

## 边界
- 不改大纲/正文/TXT/skill/RAG/知识库。
- 不联网，不安装依赖。
- 不建 cron，不接入自循环。
- 纯沙盒，产物仅留本目录。

## 产物清单
| 文件 | 用途 |
|---|---|
| `variable_injection_template.md` | 可复用 prompt 模板 |
| `test_case.json` | 本轮测试变量与约束 |
| `simulation_result.md` | 推演结果 |
| `EVALUATION.md` | 吸收判定 |
| `STATUS.json` | 阶段状态 |
| `EXECUTION_LOG.md` | 执行日志 |

## 责任分工
- MiMo Pro：写 MVP 产物草案。
- SkyClaw：只读评估。
- 主控：最终验收。
