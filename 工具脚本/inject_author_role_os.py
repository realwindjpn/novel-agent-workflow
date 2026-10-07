#!/usr/bin/env python3
"""作者卡角色OS 注入器（HARD，2026-10-07 · 修订2）

修订史：
  v1：把 7 个 OS 文件全文塞进作者卡 → 26.5K 字符，作者席上下文被挤爆。
  v2（本版）：**不塞全文**。写入「前置读取清单 + 回执要求」，
      让 Qwen 作者席自己去读项目知识库里已有的文件。

为什么改（用户原话）：
  「作家席不应该在知识库就有作家OS风格吗？你要提示他读取知识库的相关文件啊」
  项目知识库里本来就有作家风格OS 四件套 + 写作角色OS + 写作技法蒸馏。
  全文再贴一遍既浪费上下文，又制造两份可能不同步的副本。
  正确做法＝给作者卡写**强制读取指令**，由作者席自己去 KB 取。

溯源（参考资料/作家风格OS/README.md L33 已把这个坑写死）：
  「莫仁3 围-撤-围、莫仁6 智斗多方博弈、姬叉5 对话随关系定制——只活在技法层，
    从未下沉到 author_prompt_patch.md，而它的前置读取与项目资料喂养层都没有列
    写作技法蒸馏.md。结论：作者席没有任何强制路径读到它，三条技法在体系里是孤岛。」
  → 本注入器的核心职责就是补上这条强制路径。

前置读取清单来源：参考资料/作家风格OS/author_prompt_patch.md（风格层 + 项目资料喂养层）

用法：
    python3 工具脚本/inject_author_role_os.py --check
    python3 工具脚本/inject_author_role_os.py --card <卡> [--out <输出>]

行为：
    1. 校验所有前置读取文件存在，缺任一即退出非 0（不降级为裸卡）。
    2. 把「前置读取清单 + 回执要求」写到作者卡最前面（**不贴 OS 全文**）。
    3. 打印回执（文件名 + 字节数 + 用途）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

OS_ROOT = Path('/root/workspace/写作角色OS')
STYLE_OS = Path('/root/workspace/科武纪元/参考资料/作家风格OS')
TECHNIQUE = Path('/root/workspace/科武纪元/写作技巧')

# (文件路径, 用途) —— 用途写给作者席看，说明「为什么必须读这个」
REQUIRED_READS: list[tuple[Path, str]] = [
    # ── 风格层 ──
    (STYLE_OS / 'voice_rules.md',
     '风格规则：谈判/会议场景六层写法、语言指纹四轴'),
    (STYLE_OS / 'bad_phrases.md',
     '禁用词与替代表达'),
    (STYLE_OS / 'scene_method.md',
     '场景展开方法'),
    (STYLE_OS / 'author_prompt_patch.md',
     '风格铁律 + 项目资料喂养层（本清单的来源卡）'),
    # ── 执行层：写作角色OS ──
    (OS_ROOT / 'writer_role_core.md',
     '作家角色底层规则：动作先于解释、写反馈不写解释、写代价不写胜利'),
    (OS_ROOT / 'experience_distillation_rules.md',
     '采集经验如何蒸馏成写作规则'),
    (OS_ROOT / 'kewu_author_prompt.md',
     '作者完整指令：核心公式、项目资料喂养法、动作链与反馈链'),
    (OS_ROOT / 'kewu_author_training_index.md',
     '训练索引：同类章节样本 + 对应素材卡 + 同类章节被审 FAIL 的原因'),
    (OS_ROOT / 'kewu_author_training_examples.md',
     '样本：动作链/反馈链/代价的具体写法'),
    (OS_ROOT / 'deai_route_manifest.md',
     '去AI腔路由'),
    (OS_ROOT / 'DEAI_WRITING_STYLE_SPEC_20260903.md',
     '去AI腔风格规格'),
    # ── 技法层（README.md L33 点名的孤岛） ──
    (TECHNIQUE / '写作技法蒸馏.md',
     '技法层：莫仁3 围-撤-围、莫仁6 智斗多方博弈、姬叉5 对话随关系定制。'
     '注：本卡历史上未列进 author_prompt_patch 的前置读取，技法长期未下沉，'
     '谈判/博弈类章节由此缺层次。现强制补入，不得跳过。'),
]


def build_read_block() -> tuple[str, list[str]]:
    missing = [(p, u) for p, u in REQUIRED_READS if not p.exists()]
    if missing:
        raise FileNotFoundError(
            '作者角色OS/风格OS缺失，拒绝裸写：\n  '
            + '\n  '.join(f'{p}  （用途：{u}）' for p, u in missing)
            + '\n修复或重建后再组卡。'
              '（教训见 skill kewu-selfcycle-production/'
              'references/role-os-present-but-not-injected-20261007.md）')

    lines = ['# 前置读取 · 强制（写正文前必须先做完这一步）', '',
             '这些文件已在你的项目知识库中。**开始写之前，逐个读取以下文件**，',
             '它们的优先级高于本任务卡的任何措辞。', '']
    receipt = []
    for i, (p, u) in enumerate(REQUIRED_READS, 1):
        size = p.stat().st_size
        receipt.append(f'{p.name}({size}B)')
        lines.append(f'{i}. `{p}`')
        lines.append(f'   用途：{u}')
    lines += [
        '',
        '## 回执要求（不遵守则整稿作废）',
        '',
        '读完后，在输出正文**之前**先给一行回执，格式：',
        '',
        '```',
        'OS_READ_OK: <已读文件数>/<应读文件数>',
        '```',
        '',
        f'例如 `OS_READ_OK: {len(REQUIRED_READS)}/{len(REQUIRED_READS)}`。',
        '若某文件读不到，**不要静默跳过**：立刻指出缺哪个文件并停止后续动作，',
        '等待主控修复。静默跳过 = 任务失败。',
        '',
        '## 为什么这么要求',
        '',
        '历史事故：写作技法蒸馏.md（莫仁3 围-撤-围、莫仁6 智斗多方博弈、',
        '姬叉5 对话随关系定制）曾长期未出现在任何前置读取清单里，',
        '作者席没有强制路径读到它，三条技法在体系里成了孤岛。',
        '本清单的用途即在此：凡是要真正约束你的材料，都必须在这里列出。',
        '',
        '────────',
        '',
    ]
    return '\n'.join(lines), receipt


def build_full_card(card_text: str) -> tuple[str, list[str]]:
    if not card_text.strip():
        raise ValueError('作者卡正文为空')
    block, receipt = build_read_block()
    return block + card_text.lstrip('\n'), receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--card', help='原始作者卡路径（--check 时可省略）')
    ap.add_argument('--out', help='输出路径；默认覆盖原卡')
    ap.add_argument('--check', action='store_true', help='只校验完整性，不组卡')
    a = ap.parse_args()

    if a.check:
        try:
            _, receipt = build_read_block()
        except FileNotFoundError as e:
            print(str(e), file=sys.stderr)
            return 1
        print(f'作者OS/风格OS 完整，可派工（{len(receipt)} 项）：')
        for r in receipt:
            print(f'  OK {r}')
        return 0

    if not a.card:
        print('缺少 --card', file=sys.stderr)
        return 2
    card = Path(a.card)
    if not card.exists():
        print(f'作者卡不存在: {card}', file=sys.stderr)
        return 1
    try:
        full, receipt = build_full_card(card.read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        return 1

    out = Path(a.out) if a.out else card
    out.write_text(full, encoding='utf-8')
    print(f'已写入前置读取清单: {out}（{len(full)} 字符，未贴 OS 全文）')
    print(f'回执（{len(receipt)} 项）：')
    for r in receipt:
        print(f'  OK {r}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
