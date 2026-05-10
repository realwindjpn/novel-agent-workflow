# 素材卡：OpenAI实时语音API与人机协同入口

日期：2026-05-08
来源：https://techcrunch.com/2026/05/07/openai-launches-new-voice-intelligence-features-in-its-api/
类型：AI产品 / 语音接口 / 实时系统
可信度：secondary（TechCrunch报道）

## 一句话
语音AI正在从“问答”变成实时工作接口：听、转写、翻译、推理，并在对话中执行任务。

## 关键事实
- OpenAI 新增 GPT-Realtime-2、GPT-Realtime-Translate、GPT-Realtime-Whisper。
- GPT-Realtime-Translate 支持 70+ 输入语言理解、13种输出语言语音生成。
- GPT-Realtime-Whisper 用于实时语音转文字。
- GPT-Realtime-2 面向更复杂的多步请求。
- Translate/Whisper 按分钟计费，Realtime-2 按 token 计费。
- 内置反滥用与违规中止机制，覆盖垃圾信息、欺诈、恶意语音合成。

## 可用细节
- 多语言现场里，语音接口可同时转写、翻译、下发任务。
- 计费方式会影响系统设计：连续监听按分钟烧钱，复杂推理按token烧钱。
- 安全中止会让某些关键对话突然断流。

## 小说映射
- 可映射章节：78 / 95 / 184 / 221。
- 变量：人机协同、边缘代理、实时指挥、算法接口。
- 使用建议：工厂/战场/调度中心用语音接口连接人类和系统；关键冲突可来自延迟、误译、强制中止。

## 小黑盒选题
- 《语音AI真正可怕的不是会聊天，是能边听边干活》
- 切口：实时转写、翻译、任务执行、分钟计费。

## 不可使用
- 不写成所有语言都能高质量输出语音；输出语音只有13种语言。
- 不忽略安全中止和成本约束。
