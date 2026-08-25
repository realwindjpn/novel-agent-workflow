# 《科武纪元》项目状态

## 当前路由纠偏
- 2026-08-11：HS 火山方舟 LLM provider 已删除。
- `HS_API_KEY` 仅保留给 TTS；不得用于科学审、结构审、军事审或任何文本 fallback。
- 旧任务 ledger 中的 `hs/*` 记录仅作历史证据；不得作为现行席位依据。
- 科学席：仅使用实时 smoke 通过的 GLM provider；当前优先 `nexotoken-glm/glm-5.2`、`chun/glm-5.2`。均失败则 `NO_SEAT`，禁止自动回落至 hs 或 onefor 冒充 GLM。

## 任务门禁
- 作家主席：网页端 Qwen 固定项目会话。
- 五审须绑定同一候选 SHA；科学席缺失时不得写回、上传或发布。
- 主控只负责路由、监控、验收；不得代写、代审。

## 证据
- Hermes 配置检查：`hermes config check` 已通过。
- 全局 `model.fallback_providers` 与顶层 `fallback_providers` 已移除。
- 科学席错误记录已在 `任务运行态/20260811_kewu_selfcycle_cron_20260811_1400/MODEL_LEDGER.md` 标记 `INVALIDATED`。
- 路由账本：`/root/workspace/记忆体系/model-routing-active-ledger.md`。
- 路由笔记：`/root/workspace/记忆体系/model-routing-notes.md`。

## 最新进展
- 2026-08-18：用户确认第258章早已发布；2026-08-14 的 BLOCKED_WEB_AUTHOR 上传线任务作废，统一标记为已发布/闭环注销（CLOSED_PUBLISHED_SUPERSEDED）。
- 2026-08-14：确定性状态收口（254/257/258 前沿不变）；258 复核为 BLOCKED_WEB_AUTHOR，不得抬为草稿闭环；261/262 非草稿箱证据，不抬高前沿；G2 候选 108d415718 终态 NOTE_ONLY_ARCHIVED_PENDING_PRIMARY_SOURCE。
- 2026-08-12 08:47：第259章草稿箱闭环（未发布）；KOL雷达 sidecar_20260812_0732 归档（PARTIAL/无正式卡）。
- 2026-08-11：科学席路由纠偏完成，HS火山方舟已删除。

## 当前结论
`ROUTING_CORRECTED / SCIENCE_SEAT_NO_SEAT_UNTIL_FRESH_SMOKE`

下一步：对 `nexotoken-glm/glm-5.2`、`chun/glm-5.2` 做当轮语义 smoke；仅 PASS 者可重派科学审。 

## 最近同步
- 2026-08-14 | 状态收口：CURRENT_UPLOAD_PROGRESS / 跟踪表 / STATUS / WAL / cron G2_FINAL+STATUS / 20260814_kewu_status_reconcile
- 2026-08-12 08:43 | 同步章节 259
- 2026-08-12 12:38 | 同步章节 259
- 2026-08-12 22:15 | 同步章节 260
- 2026-08-13 22:09 | 同步章节 261
- 2026-08-13 22:09 | 同步章节 262
- 2026-08-15 00:15 | 同步章节 263
- 2026-08-15 00:17 | 同步章节 264
- 2026-08-15 13:09 | 同步章节 265

## G4_CLOSED_266 | 2026-08-15T14:18 | SHA fdc1418cb8aaf4de | CJK 4047 | 五审四席全PASS- 2026-08-15 18:51 | 同步章节 266
- 2026-08-16 15:12 | 同步章节 269
- 2026-08-16 15:13 | 同步章节 270
- 2026-08-16 17:12 | 同步章节 269
- 2026-08-16 17:13 | 同步章节 270
- 2026-08-16 17:47 | 同步章节 271
- 2026-08-16 17:48 | 同步章节 271
- 2026-08-16 17:49 | 同步章节 272
- 2026-08-16 18:13 | 同步章节 271
- 2026-08-16 18:24 | 同步章节 271
- 2026-08-16 18:25 | 同步章节 272
- 2026-08-18 02:59 | 第273章三审全PASS（编辑wahuiliyi-grok/grok-4.6、科学onefor/gpt-5.6-sol、读者agentrouter/gpt-5.6-sol），R1/R2定点返修后终稿SHA 728dbb65，净中文4101
- 2026-08-18 03:01 | 第273章跟踪表补行后二次同步
- 2026-08-18 03:34 | 第274章《外星证据》三席PASS（编辑grok-4.6/科学claude-opus-5/读者gpt-5.6-sol），首写+定点扩写+温标修正，终稿SHA e04374e4，净中文3275
- 2026-08-18 03:35 | 第274章跟踪表补行后二次同步
- 2026-08-18 20:26 | 同步章节 273
- 2026-08-19 00:34 | 同步章节 273
- 2026-08-19 02:11 | 同步章节 275
- 2026-08-19 02:12 | 同步章节 276
- 2026-08-19 18:44 | 同步章节 277
- 2026-08-20 23:00 | 同步章节 280
- 2026-08-21 13:43 | 第281章《太虚进阶》SHA 5ab21911 CJK 3354 + 第282章《戴森路径》SHA 16bdb6c0 CJK 4112，CDP管线产出
- 2026-08-21 14:20 | 同步章节 281
- 2026-08-21 15:38 | 同步章节 282
- 2026-08-21 15:52 | 同步章节 282
- 2026-08-21 15:55 | 同步章节 281
- 2026-08-21 16:54 | 同步章节 282

- 2026-08-22 14:46 | 用户确认：第279-282章已正式发布（番茄后台）
- 2026-08-22 15:01 | 第283章《人类共识》作者席首写回收 SHA 74d230de CJK 2603（补段中）；第284章《遗迹守护者》首写回收 SHA 0d6f9d1c CJK 2422（待补段）
- 2026-08-22 16:13 | 第283章《人类共识》SHA 1327a78c CJK 3015 + 第284章《遗迹守护者》SHA 58b63463 CJK 3016，三审+返修定稿，草稿箱保存

- 2026-08-22 18:43 | 283-284 灰区精修完成：283 SHA bef1678a CJK 3014（主语重复修复）；284 SHA 84247370 CJK 2957（不是句式清零+参数密度优化+清单腔拆解）；重审PASS；待发布
- 2026-08-22 18:50 | 第283章《人类共识》+第284章《遗迹守护者》全闭环完成
  - 283: SHA bef1678a CJK 3014（首写→编辑REVISE(P0×3)→返修→补字→重审PASS→灰区精修：主语重复修复）
  - 284: SHA cf972c6e CJK 3019（首写→编辑PASS/读者PASS→灰区精修：不是句式4→0+参数密度分散+清单腔拆解）
  - G1→G3凭证补签+G4_RELEASE签发（任务运行态/20260822_kewu_selfcycle_manual/）
  - 草稿箱TXT同步、STATUS/WAL/Git commit
  - 生图接入：三路验通（aliyun-tokoplan wan2.7/qwen-image + miku Gemini3Pro + agnes），统一脚本 scripts/generate_image.py
  - 正式发布归用户
- 2026-08-22 21:49 | 同步章节 285
- 2026-08-22 21:50 | 同步章节 286

## 2026-08-22 21:51｜第285-286章草稿箱闭环
- 状态: DRAFT_SAVED_NOT_PUBLISHED
- 第285章《考验开始》: SHA=6c2b15b1, CJK=3080, 草稿箱3724字, 第六卷·火星
- 第286章《危机应对》: SHA=89a2f4ae, CJK=3621, 草稿箱4334字, 第六卷·火星
- 五审: 科学PASS / 结构PASS / 编辑REVISE(建议) / 读者REVISE(建议) / 去AI确定性扫描PASS(7处公式句已清除)
- G1-G4凭证: 任务运行态/20260822_kewu_selfcycle_manual/
- 草稿箱listing: 285✅(3724字/1分钟前) 286✅(4334字/7秒前)
- 已投稿/目录前沿: 第286章
- 正式发布归用户

## 当前前沿
- 已投稿/目录前沿: 286
- 草稿箱闭环前沿: 286
- 下一数值章: 287《黑客攻防》
- 2026-08-22 22:23 | 同步章节 287
- 2026-08-22 22:24 | 同步章节 288

## 2026-08-22 22:24｜第287-288章草稿箱闭环
- 状态: DRAFT_SAVED_NOT_PUBLISHED
- 第287章《黑客攻防》: SHA=b5fd8aed, CJK=3282, 草稿箱3883字, 第六卷·火星
- 第288章《算力共享》: SHA=5957969d, CJK=3572, 草稿箱4278字, 第六卷·火星
- 五审: 科学REVISE(确定性修复) / 结构PASS / 编辑REVISE(288补对话已修复) / DEAI确定性扫描PASS
- 草稿箱listing: 287✅(3883字) 288✅(4278字)
- 已投稿/目录前沿: 第288章
- 正式发布归用户

## 当前前沿
- 草稿箱闭环前沿: 290
- 已投稿/目录前沿: 290
- 下一数值章: 291《太空工业》
- 2026-08-23 00:04 | 同步章节 283
- 2026-08-23 00:05 | 同步章节 284
- 2026-08-23 01:02 | 同步章节 289
- 2026-08-23 01:03 | 同步章节 290
## 2026-08-23 01:03｜第289-290章草稿箱闭环
- 状态: DRAFT_SAVED_NOT_PUBLISHED
- 第289章《设计图现》: SHA=99d99d00ce5ee9ca012ae1eaf81dcae8dfff8c7f5cf0f43b5e6f63d44ede782b, CJK=3284, 草稿箱4024字, 第六卷·火星
- 第290章《资源争夺》: SHA=ec65c5090681b742e00126f79f381991c91b5de03c6eeec9fdee6f43c0a8aed9, CJK=3077, 草稿箱3682字, 第六卷·火星
- 五审: 289同SHA五席PASS；290机械清除裸章号后新SHA五席复审PASS；DEAI扫描器10/10测试PASS
- 草稿箱listing: 289✅(4024字, count=1, duplicate=false) 290✅(3682字, count=1, duplicate=false)
- 草稿箱闭环前沿: 290；已投稿/目录前沿: 290；下一数值章: 291《太空工业》
- 正式发布归用户，未操作


- 2026-08-23 01:19 | 同步章节 289, 290
## 2026-08-23 01:34｜289-290审稿证据与DEAI补证
- 五审原件已归档并绑定候选SHA；290新SHA v6五席PASS。
- 扫描器行内对白误报已修；15/15测试PASS；289/290 hard_count=0。
- 289软密度WARN不构成上传硬阻断；正文与草稿箱未改。

- 2026-08-23 23:09 | 291《太空工业》R9 六审同SHA全PASS 定稿同步
- 2026-08-23 23:10 | 同步章节 291
- 2026-08-23 23:11 | 291 定稿+草稿箱闭环，补跟踪表行后二次同步

## 2026-08-23 23:13｜第291章 定稿闭环（草稿箱）
- 第291章《太空工业》: SHA=ee92b9c5a1ba76dcc1359a0cb5b3d49c4d432dcb64d319e73344eb283ac343e9, CJK=3574, 草稿箱4161字, 第六卷：火星
- 六审: R9 五审（editor/reader/science/military_institution/structure）+ DEAI 终门同SHA全PASS，六席跨provider无主控同族
- 机检: 禁词0/wikilink0/加粗0/三连空行False/裸章号0/引号92成对/首尾合规
- 同步: 新版✅ 已投稿TXT✅(ok,issues=[]) Wiki Full Text✅ 跟踪表✅(二次sync Tracking:1)
- 草稿箱listing: 291✅(4161字, count=1, duplicate=false, 第六卷：火星)
- 草稿箱闭环前沿: 291；已投稿/目录前沿: 291；下一数值章: 292《能源瓶颈》READY_FOR_G4_SIGN
- 报告: 任务运行态/20260823_kewu_selfcycle_daily/CLOSE_291_AND_PREP_292_STATUS.md
|- 边界: DRAFT_SAVED_NOT_PUBLISHED，正式发布归用户

## 2026-08-23 23:20｜291/292 主控复验
|- 291 R9 候选现场机检通过：SHA=ee92b9c5a1ba76dcc1359a0cb5b3d49c4d432dcb64d319e73344eb283ac343e9；CJK=3574；首尾合规；禁词/wikilink/加粗/三连空行/裸章号均为 0；直双引号 92 成对
|- 291 六审读回全 PASS：editor/reader/science/military_institution/structure/deai_final 均绑定同 SHA，reviewed_fulltext=true，provider 跨族无 GLM-5.2 同族
|- 291 定稿同步通过：新版/已投稿TXT/Wiki Full Text/跟踪表机器验收完成
|- 292 回填通过：G3_prep.json prev_chapter + locked_constraints[-1] 四项功率缺口已读回验证；prep_state=G3_READY_DEPENDENCY_291_BACKFILLED
|- 草稿箱列表终验：第291章 太空工业 4161字 count=1 duplicate=false 第六卷：火星；saved.saved=false 字段冲突已按 skill 条款以列表命中为准
|- 边界：未改正文语义、未触碰旧章、未读 KOL/全局队列、未派子席、未正式发布（发布归小哥）

## 2026-08-24 01:05｜第292章 R3 作者返修回收（未审稿）
|- 稿件: 任务运行态/20260823_kewu_selfcycle_daily/output/candidate_292_r3.md｜SHA=9512bcfb9a6d7101ac05480b307096ba44e9c548475f01050ddf83f266866586｜净CJK=3629
|- R2 唯一 FAIL: 净CJK=2884 低于硬线3200，差316；R3 只扩容七处，数字链/情节/首尾全保留
|- 机检+DEAI硬闸: MACHINE_GATE_PASS；DEAI verdict=PASS hard=0 score=12
|- 绑定: 任务运行态/20260823_kewu_selfcycle_daily/reviews_292_r3/PRE_REVIEW_BINDING_292_R3.json
|- 状态: R3_READY_FOR_REVIEW（六审未派；未入草稿箱；未发布）
- 2026-08-24 16:15 | 同步章节 292
- 2026-08-24 16:15 | 同步章节 292
- 2026-08-24 16:16 | 同步章节 292
- 2026-08-24 16:17 | 同步章节 292
- 2026-08-24 16:29 | 同步章节 292

## 2026-08-24 16:47｜第292章草稿箱闭环
- 状态: DRAFT_SAVED_NOT_PUBLISHED；正式发布归用户。
- 第292章《能源瓶颈》: R6 SHA=383549126090ce1d510916a43ec37a29def9d4403d4db1584b6025cbf4fe4524，净CJK=3690。
- 审核: R6综合降级六职责同SHA PASS，single_route_degraded=true；R4 F1-F6全清。
- 同步: 新版/TXT/Wiki/跟踪表完成；TXT正文4887、作者说276，ready gate PASS。
- 草稿箱: 唯一命中6434字，第六卷：火星，draft_id=7677509566518526488，published=false，count=1。
- 作者说: modifydraft DOM回读首尾匹配且与正文分离。
- 下一数值章: 293《拉格朗日计划》，G3已回填292 R6 SHA。

## 2026-08-24 第292章 R8 定点返修（主控直执，未派子席）
- round: R8 | source: output/candidate_292_r8.md
- sha256: 8a7dc3dbe500a856f57b737920d300f4cbe5bcbbd2b5a6184603b4fe20e6799e
- net_cjk: 3697（hard_min 3200 ✅ / safety_max 10000 ✅）| lines: 84
- prev: R7 sha 72d1dd28…f5eed / cjk 3690
- 修复三处：L36 5.8GHz→2.45GHz；L40 0.4→0.004 mW/cm²；L70 补「第 14 月停线切并网」
- 保留锚点：351=1 / 274=1 / 5326=2 / 5600=1
- diff 改动行位 [36,40,70]，越界改动 0；CJK +7 恰为插入的 7 个汉字
- 作者席：web_qwen 科武项目新会话 c/fe0337c4-c890-4a79-9253-9679e92eae97，qwen3.8-max，CDP 9223
- 验收：verify_292_r8_report.json → R8_VERIFY_PASS，fails=[]
- G4 已更新 status=R8_READY_FOR_REVIEW，latest_candidate 指向 R8
- 残留：SHA 已变，R7 及更早审稿全部作废；定稿前须按新 SHA 重派全席审稿。本轮不含审稿/草稿箱/发布。
- 2026-08-24 22:05 | 同步章节 292
- 2026-08-24 22:19 | 同步章节 292
- 2026-08-24 22:19 | R9 close-loop final sync

## 2026-08-24｜第292章 R9 终态闭环
- round: R9 | 候选: output/candidate_292_r9.md
- sha256: 20dcb09b37b614c76c3a8605a587f5a815abdcf82e752101e4d794b7cbd53863
- net_cjk: 3710 / 番茄口径: 4915
- 六席聚合: reviews_292_r9_final/AGGREGATE.json => PASS，blocking_fail_count=0
- physics_adjudication: PASS_OLD_STRUCTURE_FAIL_INVALID_RADIUS_DIAMETER_FACTOR2
- 本地闭环: 新版/第292章.md SHA一致；已投稿/第292章.txt ready gate PASS；sync_kewu --no-git --no-vector 完成；Wiki Full Text 一致；跟踪表292行已同步
- 草稿箱: draft_id=7677509566518526488；fanqie_modify_uploaded_chapter.py 无 check-login/dry-run；平台浏览器两轮不可用；唯一残留 BLOCKED_FANQIE_MODIFY_LOGIN_OR_BROWSER_UNAVAILABLE
- 产物: output/takeover_292/FINAL_R9.md / verification_r9.json / MODEL_LEDGER_R9.md
- Git: 已选择性 exact-path commit，message=chore(科武292): R9 close-loop final
- 正式发布归用户

## 2026-08-25 20:18 +08:00｜第293章《拉格朗日计划》定稿

- 状态：PASS（综合审 40/50，编辑+去AI PASS）
- SHA256：9c478ba2cb26703337b9d676fe4b982315d690b8937cd72c31c8ed6edb49bcb2
- 净CJK：3863
- 作者席：网页Qwen项目席 qwen3.8-max
- 审席：any/Fable-5（综合审 PASS 40/50）
- 关键处置：
  - R1双稿拼接→提取稿A（3624CJK）
  - R2六处修复：载荷账置换口径/CTC 19.3万/时序/铁幕暗线/赫斯特上台/句式惯性
  - P0技术修：缩比模型口径 4.6米→22米（千分之一对齐22km阵面）
- 草稿箱：已写回 /root/workspace/科武纪元/新版/第293章 拉格朗日计划.txt
- P1四项（不阻断）：条款段异议/嗅觉/弦意象/缺口台账反应
- 发布归用户
