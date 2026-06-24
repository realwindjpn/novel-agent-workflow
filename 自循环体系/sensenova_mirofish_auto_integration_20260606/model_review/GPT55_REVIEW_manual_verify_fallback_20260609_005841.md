# GPT-5.5 复核裁决：manual_verify_fallback_20260609_005841

- 复核模型：xiaomi/mimo-v2.5-pro（GPT-5.5 备用池在 cron 上下文中不可达，由 MiMo 代理确定性复核）
- 复核时间：2026-06-09T02:15
- 来源 run_dir：`/root/workspace/科武纪元/学习记录/SenseNova分段任务化/manual_verify_fallback_20260609_005841`

---

## 复核方法

逐条检查：(1) 是否存在 query_plan 伪正文混入有效卡；(2) URL/正文是否真实可追溯；(3) disposition 是否合理；(4) INDEX/KB 判重是否准确。

---

## OUTLINE_PATCH 复核（2条）

### "图灵进化"融资（20260609_a3ac514696）
- **PASS with caveat**
- URL: `http://finance.people.com.cn/n1/2026/0417/c1004-40703534.html` — 人民网primary域，可达
- Body: 3039字，含实际公司信息、融资用途、产品描述、合作方。非query_plan骨架
- INDEX判重: 未命中现有INDEX，正确
- **裁决**：PASS，但须标 `TIME_ANCHOR_202604`（距今53天）和 `SOURCE_TYPE_PR`（公司公关稿转述）
- **是否应写入大纲备注层**：是，ch95 note_layer，标注证据等级与时间锚

### How AI reshaping discovery in maths and physics（20260609_13e3ef79f2）
- **PASS with caveat**
- URL: `https://www.nature.com/articles/d41586-026-01820-1` — Nature primary域，可达
- Body: 15503字原始抓取，但正文在介绍段后截断（Nature paywall / 反爬截断）。AI Distill标注"内容截断处仅到引言开头，正文未完整"
- INDEX判重: 未命中现有INDEX，正确
- **裁决**：PASS，但须补全文body。可用 `web_extract` 重试或追踪原始研究论文
- **是否应写入大纲备注层**：是，ch95 note_layer，标注body不完整需补证

---

## CHAPTER_PREP_ONLY 复核（6条）

| material_id | 标题 | 判重 | body | 裁决 |
|---|---|---|---|---|
| eb6086966e | 推动科技创新和产业创新融合发展（新华） | 未命中 | 有body | **PASS** — 但时效低（2025-05），泛政策文，CHAPTER_PREP_ONLY合理，不转正式卡 |
| e51fda210e | 石墨烯航空电池（新华） | 未命中 | 有body | **PASS** — 技术有小说价值，CHAPTER_PREP_ONLY合理，可后续转正式卡 |
| 072d6d80cf | "美国重返月球"这盘棋（新华环球） | 未命中 | 有body | **PASS** — 时效好+直接映射ch156，CHAPTER_PREP_ONLY合理，建议优先转正式卡 |
| 52ede877a8 | 新质生产力央视视频 | 未命中 | 视频字幕 | **PASS with downgrade** — 2024年视频，时效已过。建议降为ARCHIVE |
| 011e9afe32 | Supersonic!（NASA） | 未命中 | 有body | **FAIL** — 与X-59素材重复（已入库INDEX），bridge标CHAPTER_PREP_ONLY但应为ARCHIVE。判 `BRIDGE_CLASSIFICATION_ERROR` |
| 4b90b75e2e | NASA's INCUS Satellites | 未命中 | 有body | **PASS** — 气象卫星任务，科武关联弱，CHAPTER_PREP_ONLY合理 |

---

## ARCHIVE 复核（5条）

| material_id | 标题 | 原因 | 裁决 |
|---|---|---|---|
| 46489de369 | NASA X-59 超音速 | SOURCE_URL_ALREADY_IN_INDEX | ✅ 正确归档 |
| 7615a28737 | NASA 2026大学创新赛 | TITLE_TOKEN_OVERLAP | ✅ 正确归档 |
| 7d54703422 | Artemis II 研究 | TITLE_TOKEN_OVERLAP | ✅ 正确归档 |
| 7ba62edc9b | ESA EBRD地球观测 | TITLE_TOKEN_OVERLAP | ✅ 正确归档 |
| 41cc843ef8 | brain-and-cord connectome（Nature） | 低科武关联 | ✅ 正确归档 |

---

## 总裁决

- **PASS**: 2 OUTLINE_PATCH（with caveat）+ 5 CHAPTER_PREP_ONLY
- **FAIL**: 1（Supersonic! 应降为ARCHIVE）
- **需补证**: 1（Nature AI reshaping body不完整）
- **bridge classification bug**: 1（Supersonic! 重复但标CHAPTER_PREP_ONLY）

**整体裁决：PARTIAL_PASS**

bridge 分类基本准确，但有1处重复误分类。2个OUTLINE_PATCH方向正确，均指向ch95算力主权线。
