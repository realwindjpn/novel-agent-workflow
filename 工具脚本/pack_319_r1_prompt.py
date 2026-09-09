#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第319章 R1 定点返修 prompt 打包器。

规则遵循 qwen-web-longform-pipeline 三之七：内联源稿全文，逐处给原文级 before 锚点，
锚点唯一性预检不通过即 ANCHOR_FAIL 退出，打包后自验 prompt_bytes > 源稿字节数。
"""
import hashlib
import json
import re
import sys
from pathlib import Path

SRC = Path('/root/workspace/科武纪元/任务运行态/20260908_kewu_selfcycle_daily319320/output/qwen_319_draft.md')
OUT = Path('/root/workspace/科武纪元/任务运行态/20260909_ch319_r1_webqwen/prompt/qwen_319_r1_prompt.md')
EXPECT_SHA = '19b1e0e5e9e416305a234b01c26d6e8961c37f659bd22159db26b2107d555f92'

# 四处 hard_zero 命中：原文唯一锚点 + 修复要求（不写死措辞，由作者席定稿）
FIXES = [
    {
        'line': 5,
        'anchor': '这种错号章在转运组内部意味着"已核验，与原单不符"。',
        'demand': '删掉“意味着”这个词。保留“错号章＝已核验与原单不符”这层意思与引号内原文，'
                  '换成转运组会用的平实说法（例如以“指”“代表”“就是”一类词衔接，或改成判断句）。'
                  '句子须通顺，不得留下病句，不得改动“三十七份箱单，十七份盖了错号章。”这句。',
    },
    {
        'line': 124,
        'anchor': '但上游的人，那个真正指挥这一切的人，至今没有露面。',
        'demand': '删掉“真正”这个词。保留“上游有人在指挥、此人至今未露面”这层意思。'
                  '注意本句前半已出现“上游的人”，改写后不得与之重复啰嗦，'
                  '可把同位语改成动作或职能描述（例如落在“下令”“发号施令”“定路线”一类实指上）。',
    },
    {
        'line': 128,
        'anchor': '工程停在半程意味着已经铸造的部分无法继续，未铸造的部分无法开始。',
        'demand': '删掉“意味着”这个词。保留“已铸造部分无法继续、未铸造部分无法开始”这两个后果，'
                  '改成周棠脑内的直接判断或因果并列句，不要解释腔。'
                  '不得改动同段“整个节点修复体系会因为一个环节的中断而全面停滞。”这句。',
    },
    {
        'line': 130,
        'anchor': '庚申四一九已经被调包了，真正的钨料不知道在哪。',
        'demand': '删掉“真正”这个词。保留“庚申四一九已被调包、原本那批钨料下落不明”这层意思，'
                  '换成韩铮口中会说的实指（例如“原货”“那批钨料”“正品”一类），编号庚申四一九不得改动。',
    },
]

BANNED = ['真正', '核心', '关键', '意味着', '值得关注', '赋能', '生态闭环']


def main() -> int:
    if not SRC.exists():
        print('PACKAGING_FAIL src_missing')
        return 2
    body = SRC.read_text(encoding='utf-8')
    sha = hashlib.sha256(body.encode('utf-8')).hexdigest()
    if sha != EXPECT_SHA:
        print('SHA_FAIL got=%s' % sha)
        return 2

    lines = body.split('\n')
    for fx in FIXES:
        if body.count(fx['anchor']) != 1:
            print('ANCHOR_FAIL line=%s count=%s' % (fx['line'], body.count(fx['anchor'])))
            return 2
        if fx['anchor'] not in lines[fx['line'] - 1]:
            print('ANCHOR_LINE_MISMATCH line=%s' % fx['line'])
            return 2

    cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
    first_line = lines[0].strip()
    last_line = [x for x in lines if x.strip()][-1].strip()

    fix_blocks = []
    for i, fx in enumerate(FIXES, 1):
        fix_blocks.append(
            '### 第%d处（位于原文第%d行）\n\n原文（全文中只出现一次，必须精确定位）：\n%s\n\n修改要求：\n%s\n'
            % (i, fx['line'], fx['anchor'], fx['demand'])
        )

    head = f"""你是《科武纪元》第319章的返修执笔。下面【原文全文】是已定稿正文，共 {len(lines)} 行、净中文 {cjk} 字。

你的唯一任务：把这份原文**原样复制输出**，只在下面点名的 4 个位置做句级改写。除这 4 句以外，一个字都不许动。

## 绝对禁止

1. 禁止重写场景、重新构思情节、更换视角。
2. 禁止输出审稿意见、修改说明、清单、思考过程。只输出正文。
3. 禁止只输出被改的段落。必须输出**全章完整正文**。
4. 禁止删减、合并、拆分任何未被点名的行；段落顺序、空行结构与原文一致。
5. 禁止改动首行标题「{first_line}」与末行「{last_line}」。
6. 禁止改动任何数字与编号（庚申四零二、庚申四一九、三十七份、十七份、六组、二十四小时、戊字仓线等一律照抄）。
7. 禁止改动人物名（周棠、韩铮、陈若水、李文博）、制度名与设定名。
8. 禁止出现这些词：真正、核心、关键、意味着、值得关注、赋能、生态闭环。
9. 禁止出现「不是……而是」句式。
10. 禁止阿拉伯数字、拉丁字母、弯引号（“ ” ‘ ’）、破折号、双方括号链接、markdown 粗体。数字一律用汉字；引号必须照抄原文所用的半角双引号，不得替换成弯引号或直角引号。
11. 禁止加 markdown 标题标记、代码块、列表符号。

## 需要改的 4 处

{chr(10).join(fix_blocks)}
## 输出格式

- 首行必须是：{first_line}
- 末行必须是：{last_line}
- 净中文不得少于 {cjk - 20} 字（改写属等量替换，字数应与原文基本持平）
- 只输出正文，不要任何前后缀、说明、引号包裹。

# 原文全文

"""

    prompt = head + body.rstrip('\n') + '\n'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(prompt, encoding='utf-8')

    back = OUT.read_text(encoding='utf-8')
    report = {
        'prompt_path': str(OUT),
        'prompt_bytes': len(back.encode('utf-8')),
        'src_bytes': len(body.encode('utf-8')),
        'prompt_bytes_gt_src': len(back.encode('utf-8')) > len(body.encode('utf-8')),
        'inlined_full_body': body.strip() in back,
        'first_line_present': first_line in back,
        'last_line_present': last_line in back,
        'no_readfile_gutter': re.search(r'(?m)^\d+\|', back) is None,
        'anchors_unique_in_src': all(body.count(f['anchor']) == 1 for f in FIXES),
        'src_sha': sha,
        'src_cjk': cjk,
        'src_lines': len(lines),
        'banned_in_src_count': {w: body.count(w) for w in BANNED},
    }
    ok = all([
        report['prompt_bytes_gt_src'], report['inlined_full_body'],
        report['first_line_present'], report['last_line_present'],
        report['no_readfile_gutter'], report['anchors_unique_in_src'],
    ])
    report['verdict'] = 'PACKAGING_PASS' if ok else 'PACKAGING_FAIL'
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
