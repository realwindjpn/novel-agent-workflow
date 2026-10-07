#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""作者卡派工前自检 card_selfcheck.py（2026-10-07）

源起：370 的 R2 返修卡在卡内写了禁用句的字面样例（「不是同时亮的，是」），
卡自己命中了对举扫描器 —— 等于在教模型用禁用表达。
本脚本把 pack_357_author_prompt.py 里那段一次性自检抽成通用工具。

检查项（任一不过 → 退出 1，禁止派工）：
  1. 卡内不得出现破折号 ——
  2. 卡内不得出现弯引号 “ ” ‘ ’
  3. 卡内不得出现迟疑报时样例（停了一瞬 / 顿了顿 / 停住片刻）
  4. 卡内不得出现对举样例（不是…，是 / 并非 / 谈不上）
  5. 卡内不得混入非 CJK 字母串（>=3 个连续拉丁字母且非白名单）
  6. 必含硬闸锚点：首行标题、末行（本章完）、CJK 下限数字
  7. 若注入了 OS，必须含 OS_READ_OK 回执要求

用法：
    python3 工具脚本/card_selfcheck.py <作者卡路径> [--no-os-check]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 白名单：允许出现在卡里的拉丁词（术语 / 路径 / 型号禁词本身 / OS 文件名）
WHITELIST = {
    'CJK', 'OS', 'OK', 'READ', 'SHA', 'JSON', 'MD', 'PACK', 'MATERIAL',
    'VBCI', 'output', 'author', 'prompt', 'role', 'txt', 'md', 'PDF',
    # 写作角色OS / 风格OS 文件名及其构成词（注入清单必含，非污染）
    'DEAI', 'SPEC', 'STYLE', 'WRITING', 'FAIL',
    'bad', 'core', 'deai', 'distillation', 'examples', 'index',
    'voice', 'rules', 'scene', 'method', 'training',
    'experience', 'writer', 'kewu', 'phrases', 'manifest',
    # 注入清单里的绝对路径构成词
    'patch', 'root', 'route', 'workspace', '参考资料',
}


def check(text: str, want_os: bool = True) -> tuple[bool, list[str]]:
    errs = []

    # 1. 破折号
    if '——' in text:
        errs.append(f'含破折号 ×{text.count("——")}')

    # 2. 弯引号
    curly = re.findall(r'[“”‘’]', text)
    if curly:
        errs.append(f'含弯引号 ×{len(curly)}: {sorted(set(curly))}')

    # 3. 迟疑报时样例
    hesitate = re.findall(r'停了一瞬|顿了顿|停住片刻|停了片刻', text)
    if hesitate:
        errs.append(f'含迟疑报时样例: {sorted(set(hesitate))}')

    # 4. 对举样例（卡里写这些＝教模型用）
    duiju = re.findall(r'不是[^，。\n]{0,8}，是|并非[^，。\n]{0,8}|谈不上', text)
    if duiju:
        errs.append(f'含对举样例: {sorted(set(duiju))}')

    # 5. 非 CJK 混入
    stray = [w for w in re.findall(r'[A-Za-z]{3,}', text) if w not in WHITELIST]
    if stray:
        errs.append(f'可疑拉丁字符串: {sorted(set(stray))[:10]}')

    # 6. 硬闸锚点
    if '（本章完）' not in text:
        errs.append('缺末行锚点 （本章完）')
    if not re.search(r'第\d+章', text):
        errs.append('缺首行锚点「第N章 标题」')
    if not re.search(r'CJK\s*[≥>]\s*\d{3,}', text) and not re.search(r'\d{3,}\s*[字CJK]', text):
        errs.append('未声明 CJK 下限')

    # 7. OS 回执要求
    if want_os and 'OS_READ_OK' not in text:
        errs.append('未含 OS_READ_OK 回执要求（未走 inject_author_role_os.py？）')

    return (not errs), errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('card')
    ap.add_argument('--no-os-check', action='store_true',
                    help='跳过 OS_READ_OK 检查（非作者卡时使用）')
    a = ap.parse_args()

    p = Path(a.card)
    if not p.exists():
        print(f'卡不存在: {p}', file=sys.stderr)
        return 2
    t = p.read_text(encoding='utf-8')
    ok, errs = check(t, want_os=not a.no_os_check)

    if ok:
        print(f'SELFCHECK_PASS  {p.name}  ({len(t.encode("utf-8"))}B)')
        return 0
    print(f'SELFCHECK_FAIL  {p.name}', file=sys.stderr)
    for e in errs:
        print(f'  ✗ {e}', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
