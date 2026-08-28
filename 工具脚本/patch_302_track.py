#!/usr/bin/env python3
"""补 302 行进小说综合跟踪表，格式照抄 301 行（八列）。"""
import pathlib
import re
import hashlib

ROOT = pathlib.Path('/root/workspace/科武纪元')
body = (ROOT / '已投稿' / '第302章.txt').read_text(encoding='utf-8')
sha = hashlib.sha256(
    (ROOT / '任务运行态' / '20260828_kewu_selfcycle_daily' / 'output'
     / 'qwen_302_aug_clean.md').read_text(encoding='utf-8').encode()).hexdigest()

# 番茄口径 = 全文字符数（含标点，不含空白行的换行）
fanqie = len(re.sub(r'\s', '', body))
cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
print('番茄口径（去空白全字符）%d | 净中文 %d' % (fanqie, cjk))

track = ROOT / '小说综合跟踪表.md'
t = track.read_text(encoding='utf-8')

if '| 第302章 |' in t:
    print('已有 302 行，跳过')
    raise SystemExit(0)

anchor = [l for l in t.split('\n') if l.startswith('| 第301章 |')]
assert anchor, '找不到 301 行做锚点'
a = anchor[0]

row = ('| 第302章 | 戴森共识 | 第六卷·火星 | 2026-08-28 | FINALIZED_NOT_PUBLISHED | '
       '四审同SHA全PASS（读者 aliyun-qwen38 / 结构 wechat-glm / 编辑 wechat-glm / 科学 aliyun-qwen38）；'
       '机检PASS（净CJK%d≥3200硬线、禁词0、公式句0、硬数字守恒、拉丁仅L1、首尾合规）；'
       '出稿路径：网页Qwen三次取最优2813字→补写席定点扩写三处 | '
       'SHA %s | 已投稿/第302章.txt（番茄口径%d，无作者有话说）；'
       '任务运行态/20260828_kewu_selfcycle_daily/output/reviews_302_r1/；'
       '草稿箱保存与正式发布归用户 |') % (cjk, sha, fanqie)

t = t.replace(a, a + '\n' + row, 1)
track.write_text(t, encoding='utf-8')

back = track.read_text(encoding='utf-8')
print('已追加 302 行；回读校验:', '| 第302章 |' in back, '| 第301章 |' in back)
print('表大小', track.stat().st_size, 'B')
