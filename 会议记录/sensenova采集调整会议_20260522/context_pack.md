# SenseNova采集调整会议 context pack 2026-05-22

## 用户问题
- SenseNova采集任务是否都修复好了？
- 这两天大纲没优化，是否因为采集范围缺少时事素材、科学/科普最新进展？
- 请各可用强模型开会，每类模型一个代表，讨论如何调整采集任务。

## 当前cron
- `67cc540dd63a` SenseNova每5小时科武计划驱动采集蒸馏：enabled=true, last_status=ok, next=2026-05-22 16:33。
- MiniMax自维护巡检当前不在cron列表；历史规则要求有MiniMax/低成本接管巡检，但当前 MiniMax smoke 429，不可用。

## 今日已读证据
### control_report
- `state_learned_count: 105`
- `queue_status_counts`: SKIP_DUPLICATE 34, CARD_DONE 59, CARD_REVIEW_FAIL 31, CARD_REVIEWED 6, CARD_AUTODISTILLED 38, SKIP_NOISE 3, CARD_PENDING 3
- `kb_new_cards_this_run: 4`
- 状态：OK_DISTILLED
- 落地报告：`/root/workspace/科武纪元/学习记录/SenseNova蒸馏落地/2026-05-22_1128_landing.md`
- 缺口：月球/深空工程 score=912；算力/芯片主权 387；量子通信/量子计算 176；生物技术/遗传战 11；军事AI/蜂群 -7

### landing摘要
- 本轮已归档4张知识库卡：城市级AI服务、五粮液财务变脸、AI+电竞战略发布、AI+电竞全流程赋能。
- 书单学习补了月球史、轨道力学、Lunar Sourcebook、量子通信网络。
- 下一轮建议方向：月球南极永久阴影区/能源；HBM3e/CoWoS先进封装良率；QKD中继距离与DI-QKD。
- 但素材偏产业会议信息与书单规则，缺少当日P0时事、硬科学论文/官方源原文卡。

### 早上修复报告：`sensenova_repair_kimi1_20260522.md`
已修：
1. 噪声过滤：流程标记/无正文/SKIP等不再转卡。
2. 书单释放机制：learned_book_titles从119降到30，可继续学。
3. 增加OpenCLI HN与36kr新闻补充。
4. 定向检索DDG/Bing失败时 fallback 到OpenCLI/36kr。
5. dry-run 书单正常；定向检索可入队5条36kr。
仍需主控：确认下轮cron；更新next_instruction；可选清历史噪声；观察OpenCLI判重过严。

### 只读审计报告：`sensenova_repair_review_freemodel_20260522.md`
结论：不是没抓，是四段断：
1. 采集层已抓到数据：RSS/CAS/IOP/OpenCLI。
2. 入队层断：CAS/IOP/OpenCLI/定向检索产物基本没进CARD_PENDING。
3. 去重过滤过严：OpenCLI 39条 added=0。
4. 蒸馏阶段被噪声pending误导。
建议：恢复/创建MiniMax接管巡检；但先修脚本门禁。

## 当前模型可用性smoke
- WF Opus47：custom:WF / claude-opus-4-7-high-fast PASS
- ZAI GLM：zai / glm-5.1 PASS
- Alibaba Qwen：alibaba / qwen3.6-plus PASS
- Kimi coding：kimi1 / kimi-for-coding PASS
- Freemodel GPT-5.5：503 unavailable
- MiniMax-M2.7：429 usage limit

## 会议任务
只产方案，不改正文/大纲。输出应回答：
1. SenseNova是否算修好？哪些已修，哪些未闭环？
2. 大纲两天未优化的主因：采集缺时事？缺科学/科普最新进展？还是融纲流程没被触发？
3. 采集任务如何调整：源、关键词、队列状态、转卡、巡检、融纲触发。
4. MiniMax不可用时谁接管巡检？
5. 下轮最小可验证方案：下次cron前/后要看哪些文件，验收标准是什么。

## 输出要求
- 每位代表≤900字。
- 必须给可执行调整清单。
- 不得安排改正文，不得直接改大纲。
- 证据路径必须写清。
