# 素材卡：Mozilla AI辅助漏洞挖掘：271个Firefox漏洞与Agent Harness

日期：2026-05-08
来源：https://arstechnica.com/information-technology/2026/05/mozilla-says-271-vulnerabilities-found-by-mythos-have-almost-no-false-positives/
类型：AI安全/Agent工程/软件供应链
可信度：secondary

## 一句话
Mozilla用定制agent harness把LLM接入现有fuzzing和sanitizer流水线，两个月发现271个Firefox安全缺陷，关键不是“模型会审代码”，而是“工具闭环给可复现崩溃信号”。

## 关键事实
- 两个月内发现271个Firefox安全缺陷，其中180个sec-high、80个sec-moderate、11个sec-low。（来源：原文）
- 流程包含指定源码文件→生成测试用例→用Mozilla现有fuzzing基础设施与sanitizer build执行→以崩溃作为确认信号。（来源：原文）
- Mozilla称几乎没有误报，并用第二个LLM对第一模型输出进行评分，再交给开发者复核。（来源：原文）

## 可用细节
- “agent harness”给模型文件读写、测试执行和评价工具；模型在循环中工作，不靠一次性回答。
- 崩溃/sanitizer是硬反馈，相当于把模型判断接到物理验收口。
- 双模型不是投票写结论，而是让第二模型审第一模型证据。

## 小说映射
- 可映射章节/卷：95/184/221/269/286/317/339
- 对应变量：AI越界/开源生态/封闭熵增/工具闭环
- 使用建议：补“流云”不是单纯会想，而是被测试、崩溃、回归约束；主角团用硬反馈harness驯化AI，铁幕只用闭源判断导致误报与盲区。

## 小黑盒选题
- 标题方向：AI找漏洞不离谱，离谱的是没有测试闭环
- 玩家/普通人口吻切口：从具体数字/操作链讲，不写宏大口号。
- 可配图/引用：原文截图或机构/项目示意图。

## 不可使用
- 未证实扩展。
- 把诉讼主张当既定判决。
- 把专家报告当已执行政策。
