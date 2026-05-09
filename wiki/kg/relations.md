# KG Relations

## Relation Types
- `has_title`: 章节标题
- `previous` / `next`: 章节顺序
- `contains_entity`: 章节包含人物/组织
- `contains_concept`: 章节包含概念/技术点
- `ending_hook`: 章末钩子

## Stats
- chapters: 64
- triples: 728
- entities: 18
- concepts: 34

## V8.5 对手角色补丁（2026-05-06）
- characters_added: 10
- factions_added: 5
- chapter_cast_rows: 16
- source: `kg/v8.5-opponent-characters.json`

## 2026-05-08 闭环同步
- synced_chapters: 73, 74
- synced_outline: V8.6 current-events mapping
- source: `ch073_20260508_sync.json`, `ch074_20260508_sync.json`, `ch000_20260508_sync.json`
- backup: `/root/workspace/科武纪元/备份/20260508_kg_sync/`


## 2026-05-08 V8.7 时事素材关系
- Mozilla Agent Harness → 流云硬反馈闭环 → 章节 95,184,269,286,317,339
- DHS DNA Database Lawsuit → 白盾生物数据算法暴力 → 章节 217,223,226,233,243
- European Defense Autonomy → 欧陆C2自主摩擦 → 章节 86,106,121,306,307,309
- Turkey Yildirimhan Propellant → 推进剂供应链威慑 → 章节 308,311,337,340

### V8.7 Body Sync (2026-05-08)
- 欧陆C2备份链 → causes → 三秒延迟 (ch86)
- 审计权冲突 → manifests_as → 签名队列死循环 (ch86)
- 流云自生成代码 → requires → 红队harness验证 (ch95)
- 模型自证安全 → is_prohibited_by → 双模型复核 (ch95)
- 流云推演 → requires → 三层验证链 (ch184)
- 集中命令/边缘自主 → is_structural_defect_of → 铁幕AI架构 (ch184)
- 白盾风险分 → incorporates → 生物数据标签 (ch217)
- DNA/面部/车牌/社媒/位置 → 拼成 → 长期风险标签 (ch217)
- 白盾标签 → enters → 多部门系统 (ch233)
- 标签跨部门 → has_property → 不可单点撤销 (ch233)
- 执行者 → sees → 红色风险等级 (ch233)
- 执行者 → cannot_see → 标签来源 (ch233)


## V8.8 2026-05-10
- ch086 uses 天门封锁/医疗船误击，呼应诊所误判。
- ch124 foreshadows ch240 量子钥匙，遵守R10：量子计算用于模拟补丁冲突路径。
- ch217 sets up UGV三代与声波执法，算法暴力物理化。
- ch223 closes UGV三态：被劫持/静止/继续执行。
