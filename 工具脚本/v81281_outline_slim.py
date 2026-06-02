#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.8.1 大纲备注层瘦身：
- 旧顶部（执行索引/源稿门禁/常驻红线/V8.12.8合并摘要/历史补丁入口）整体归档
- 新顶部按会议综合裁决五段定式
- 严格保证 body 不变（body_equal=True）
"""
import hashlib
import pathlib
import shutil
import sys

ROOT = pathlib.Path('/workspace/科武纪元')
LATEST = ROOT / 'wiki/raw/outline/科武纪元大纲_latest.md'
ARCH_DIR = ROOT / 'wiki/raw/outline/archive'
ARCH_FILE = ARCH_DIR / 'outline_V8.12.8_merged_summary_20260526.md'
BAK = LATEST.with_suffix(LATEST.suffix + '.bak_v81281_20260526')

SEPARATOR = '---'

NEW_TOP = '''# 当前执行索引（V8.12.8.1 · 日切 2026-05-26）
- 已投稿最新：第112章；明日上传线：第113、第114（P0 上传线，源稿存在，旧PASS增量复核+TXT）。
- 回改线：第223章（P1，源稿存在，不生成TXT）。
- 仅备注/准备包：第358、第378（P2，无源稿>260，禁正文精修）。
- 禁派回压：第95、第217、第221、第226（已闭环不回压）。
- 禁派无源稿：第306、第307、第330、第361、第371-381（仅锚点/备注层）。

# 源稿门禁（硬约束·不动）
- 新版完整范围：1-260。
- 章节号 >260 或在无源稿列表内：禁止派正文精修，禁止生成任务卡，禁止生成TXT。
- 任务卡生成前必须查 `新版/第N章.md` 完整正文存在。
- 已闭环章不重复全审；仅按会议裁决要求做增量复核/必要小修。
- 非上传章不得生成/保留 `已投稿/第N章.txt`。
- 容错弹性槽正文新增 ≤ 300 字/章。
- Git 只 add 本轮相关文件，禁止 `git add -A`。

# 常驻红线（V8.12.8.1 合并·共11条 + 制度链5条）
## 红线 11 条
1. AI 不写灵魂/觉醒，只写目标函数/奖励/停机惩罚/通信丢包/权限越界。
2. 量子非万能：九章≠破解器；QKD≠规模化；每次必带工程代价。
3. 材料先打烂再用：炉温/张力/缺陷/批次。
4. 算力=电/热/水/许可/审计，不是显卡。
5. 战争摩擦与代价具名（签字链/担责链/审批链/通报延迟/联络官）。
6. 素材转正门禁：CARD_PENDING / MISSING_RAW 不得入正文。
7. 同章多补丁按线名对账，不按章号误判闭环。
8. 热力学：散热不可突破兰道下限，只写工程极限区。
9. 先进材料性能受批次/张力/缺陷约束。
10. AI 自主行为=参数漂移/反馈增益超阈值/目标函数偏移。
11. 传感器/感知必带误差边界/模型漂移/置信度回读。
## 制度链 5 条（GLM 升常驻）
1. 战争险触发链：涉海上封锁必写商业后果（战争险条款→船东拒航→商业先行中断）。
2. 算法主权=可审计权：谁看日志/谁签字/谁担责。
3. 白盾有限免责：民事/调查/刑事三道门。
4. 军售采购签字链：谁签/谁扩产/谁退货。
5. 多域指挥摩擦：联络官+情报等级+火力审批卡+通报延迟。

# 最新摘要（V8.12.8.1 · 2026-05-26 弹性优化会议落地）
- 性质：备注层瘦身补丁；**不发 V8.12.9，不重排章号，不改大纲主体章节**。
- 顶部五段定式：执行索引 → 源稿门禁 → 常驻红线(含制度链) → 最新摘要 → 归档入口。
- 容错弹性槽（备注层占位，不动章号）：
  - S1-T 卷一尾(55)/S2-T 卷二尾(105)：历史已用，上限 800 字。
  - S3-M 卷三中段(155)：预占，触发条件 ≥140 推进+≥2 张素材卡。
  - S4-T 卷四卷尾(205)：预占，触发条件 ≥190 推进。
  - S5-M 250 前中段(255)：预占，触发条件 ≥240 推进+226 收束。
  - S6-F 源稿边界(260)：预占，触发条件 261+源稿首次补齐，上限 1200 字。
- 队列裁决：P0=113/114（上传线·旧 PASS 增量复核+TXT+草稿箱）；P1=223（回改·不生成 TXT）；P2=358/378（无源稿>260·NOTE_ONLY 准备包）。
- 禁派：95/217/221/226（已闭环不回压）；306/307/330/361/371-381（无源稿仅锚点）。
- 旧 V8.12.5/6/7/V8.12.8 合并层（含 2026-05-25 增量 4 条）整体归档：见归档入口。
- 会议综合裁决：`审核记录/goal模式/整体大纲弹性优化会议_20260526/会议综合裁决.md`。
- 落地验收报告：`审核记录/goal模式/整体大纲弹性优化会议_20260526/V81281_落地验收_20260526.md`。

# 归档入口
- V8.4—V8.12.4：`wiki/raw/outline/archive/outline_version_archive_V8.4-V8.12.4_20260517.md`。
- V8.12.5/6/7 原始层：`wiki/raw/outline/archive/outline_V8.12.5-7_20260524.md`。
- V8.12.5–V8.12.8 合并摘要（含 2026-05-25 增量 4 条·原顶部完整快照）：`wiki/raw/outline/archive/outline_V8.12.8_merged_summary_20260526.md`。
- latest 顶部不再展开历史版本。

'''


def sha(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def split_old(text: str):
    lines = text.splitlines(keepends=True)
    sep_idx = None
    for i, ln in enumerate(lines):
        if ln.strip() == SEPARATOR:
            sep_idx = i
            break
    if sep_idx is None:
        raise SystemExit('FATAL: separator --- not found in latest outline')
    return ''.join(lines[:sep_idx]), ''.join(lines[sep_idx:])


def main():
    raw = LATEST.read_text(encoding='utf-8')
    old_top, body = split_old(raw)
    body_sha_before = sha(body)

    shutil.copy2(LATEST, BAK)

    ARCH_DIR.mkdir(parents=True, exist_ok=True)
    arch_payload = (
        '# 归档·V8.12.5/6/7 + V8.12.8 合并摘要层（含 2026-05-25 增量 4 条）\n'
        '\n'
        '归档时间：2026-05-26\n'
        '触发：V8.12.8.1 备注层瘦身补丁（弹性优化会议落地）\n'
        '原文件：`wiki/raw/outline/科武纪元大纲_latest.md` 顶部（旧执行索引/源稿门禁/常驻红线/V8.12.8合并摘要/历史补丁入口）\n'
        '裁决文件：`审核记录/goal模式/整体大纲弹性优化会议_20260526/会议综合裁决.md`\n'
        '\n'
        '> 本快照为旧顶部完整原文，**不再用于 latest 顶部**，仅供历史回溯。\n'
        '\n'
        '---\n'
        '\n'
        + old_top
    )
    ARCH_FILE.write_text(arch_payload, encoding='utf-8')

    new_full = NEW_TOP + body
    LATEST.write_text(new_full, encoding='utf-8')

    after = LATEST.read_text(encoding='utf-8')
    _, body_after = split_old(after)
    body_sha_after = sha(body_after)
    body_equal = body_sha_before == body_sha_after

    report = {
        'old_top_lines': old_top.count('\n'),
        'new_top_lines': NEW_TOP.count('\n'),
        'body_lines': body.count('\n'),
        'body_sha_before': body_sha_before,
        'body_sha_after': body_sha_after,
        'body_equal': body_equal,
        'backup': str(BAK),
        'archive': str(ARCH_FILE),
    }
    for k, v in report.items():
        print(f'{k}: {v}')

    if not body_equal:
        sys.exit('FATAL: body changed unexpectedly')


if __name__ == '__main__':
    main()
