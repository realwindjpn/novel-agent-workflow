#!/usr/bin/env python3
"""追加 301 终态到 STATUS.md 与 WAL.md。"""
import pathlib

KEWU = pathlib.Path('/root/workspace/科武纪元')

STATUS_BLOCK = """
## 2026-08-28 第301章《联合防御》闭环

- 章节：第301章 联合防御｜第六卷·火星
- 定稿 SHA `ea9ccb03ee85970044e429d26f09456721da3dece31bbff81c5ed74e9c11a487` | 净中文 3164（目标 3200-3400，硬下限 3000）
- 已写回 `已投稿/第301章.txt`（番茄口径 3640，含作者有话说 126 字）与 `新版/第301章.md`
- G1-G4 凭证当日有效：G1 598 卡命中 62 / G2 NO_IMPACT_AUTO / G3 PREP_COMPLETE / G4_RELEASE_301.json SIGNED / DAILY_DIGEST_COMPLETE date=2026-08-28
- 机检 MACHINE_GATE_PASS（zero fails/warns）
- 返修轨迹：R1 CJK 不足 → R2 扩写 → R3 达标 3341 但编辑席 FAIL 7 条 → R4 定点返修（拆 10 处 before/after）
- R4 验收 VERIFY_PASS：10 处修复逐条「旧写法归零 + 新写法存在」、9 项门禁全过、CJK 3341→3164、diff 仅 8 处行位、越界改动 0
- 四审同 SHA 全 PASS（新 SHA 后旧审稿全废并重派）：
  - 读者 chun-grok46/grok-4.6 PASS
  - 结构 yi-hydrogel/grok-4.6 PASS
  - 编辑 wechat-glm/GLM-5.2 PASS（含 DEAI_EDITOR: PASS，逐条引行号举证）
  - 科学 wechat-glm/GLM-5.2 PASS（BLOCKERS: none）
- 审席禁用族：本会话主控为 sotamodel/claude-opus-5，故 claude-opus-5 全族（含 gorouter-opus5）不得任审席
- 科学席换席四次：yi-hydrogel-dsv4 524 / trenddao 501s 超时 / yezi-help 504 → wechat-glm PASS
- 作者说三派：chun-grok46 与 yi-hydrogel 均触公式句「不是…是」（根因为 prompt 素材本身含该句式，已修素材）→ aliyun-qwen38/qwen3.8-max 通过
- 项目同步：Wiki ch301 Full Text 已覆盖（新锚点在、旧句清零）｜跟踪表补录 295-301 共 7 行后 Tracking 命中｜伏笔/角色索引已刷新
- 草稿箱保存与正式发布归用户
- 302《宪章表决》：G3_prep 中为 PENDING_DEPENDENCY，301 已定稿可解依赖
"""

WAL_BLOCK = """
### 2026-08-28 第301章《联合防御》闭环完成

- 定稿 SHA `ea9ccb03ee85970044e429d26f09456721da3dece31bbff81c5ed74e9c11a487`，净中文 3164，番茄口径 3640
- 源稿链：`output/qwen_301_r3_raw.md`（fa526f00，编辑 FAIL 7 条）→ R4 返修包（17096 字节，内联全文，10 锚点 count 全 1）→ `output/qwen_301_r4_clean.md`
- R4 验收脚本 `工具脚本/verify_301_r4.py` → `output/VERIFY_301_R4.json` VERIFY_PASS
- 四审报告落 `output/reviews_301_r4/{reader,structure,editor,science}_review.md`，全 PASS
- 作者说 `output/AUTHOR_NOTE_301.txt`（aliyun-qwen38），前两派因公式句作废留档 `_r1_FORMULA_FAIL.txt` / `_r2_FORMULA_FAIL.txt`
- 闭环脚本 `工具脚本/close_loop_301.py` → `output/CLOSE_LOOP_301.json` CLOSE_LOOP_TXT_READY
- 跟踪表缺口：补录 295-301 共 7 行（`工具脚本/backfill_tracking_295_301.py`），295/296 标「审稿闭环记录待补证」
- 工具事实：`direct_model_call.py` 不支持 `codex_responses`（agentrouter 须走 dispatch_to_model）；CDP 9223 未起，网页作者全程 `--cdp-url ""` 冷启动 + 3 次重试绕 Playwright `setDeviceMetricsOverride` 竞态
- 断点残留：302 待起稿；G1 的 124 张 READY 融纲消费待跑；草稿箱与正式发布归用户
"""


def append(path, block, marker):
    p = KEWU / path
    txt = p.read_text(encoding='utf-8')
    if marker in txt:
        print('ALREADY', path)
        return
    p.write_text(txt.rstrip('\n') + '\n' + block, encoding='utf-8')
    print('appended', path, len(block))


append('STATUS.md', STATUS_BLOCK, '## 2026-08-28 第301章《联合防御》闭环')
append('WAL.md', WAL_BLOCK, '### 2026-08-28 第301章《联合防御》闭环完成')

for f in ['STATUS.md', 'WAL.md']:
    t = (KEWU / f).read_text(encoding='utf-8')
    print(f, 'has_301_block', '第301章《联合防御》闭环' in t, 'sha_in', 'ea9ccb03' in t)
