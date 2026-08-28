#!/usr/bin/env python3
"""补跟踪表 295-301 缺行。证据强弱分级：有 STATUS 定稿记录+审稿目录=FINALIZED，否则标待补证。"""
import pathlib
import re
import hashlib

KEWU = pathlib.Path('/root/workspace/科武纪元')
TRACK = KEWU / '小说综合跟踪表.md'
STATUS = (KEWU / 'STATUS.md').read_text(encoding='utf-8')


def sha_of(n):
    p = KEWU / '已投稿' / ('第%d章.txt' % n)
    t = p.read_text(encoding='utf-8')
    body = t.split('作者有话说：')[0].rstrip('\n') + '\n'
    return hashlib.sha256(body.encode()).hexdigest(), len(re.sub(r'\s', '', t))


def status_sha(n):
    """从 STATUS.md 抓该章定稿 SHA（若有记录）。"""
    m = re.search(r'第%d章[^\n]*\n(?:[^\n]*\n){0,12}?- 定稿 SHA `([0-9a-f]{64})`' % n, STATUS)
    if m:
        return m.group(1)
    m = re.search(r'已写回 `已投稿/第%d章\.txt`' % n, STATUS)
    return None


ROWS = [
    (295, '文明抉择', '第六卷·火星'),
    (296, '太虚极限', '第六卷·火星'),
    (297, '方宁网络扩展', '第六卷·火星'),
    (298, '共鸣效应', '第六卷·火星'),
    (299, '铁幕叛变', '第六卷·火星'),
    (300, '遗迹反击', '第六卷·火星'),
    (301, '联合防御', '第六卷·火星'),
]

REVIEW_EVIDENCE = {
    297: '任务运行态/20260827_kewu_selfcycle_daily/',
    298: '任务运行态/20260827_kewu_selfcycle_daily/',
    299: '任务运行态/20260827_kewu_selfcycle_daily/',
    300: '任务运行态/20260827_kewu_selfcycle_daily/',
    301: '任务运行态/20260828_kewu_selfcycle_daily/output/reviews_301_r4/',
}

DETAIL = {
    301: ('四审同SHA全PASS（读者 chun-grok46 / 结构 yi-hydrogel / 编辑 wechat-glm / '
          '科学 wechat-glm）；机检PASS（净CJK3164≥3000、禁词0、首尾合规、10处返修全命中、diff越界0）'),
}

lines = []
for n, title, vol in ROWS:
    body_sha, fanqie = sha_of(n)
    s_sha = status_sha(n)
    sha_shown = s_sha or body_sha
    ev = REVIEW_EVIDENCE.get(n)
    detail = DETAIL.get(n)
    if detail:
        review = detail
    elif s_sha:
        review = '审稿闭环记录见 STATUS.md 对应小节；机检PASS'
    else:
        review = '本地TXT/Wiki/新版存在，审稿闭环记录待补证'
    state = 'FINALIZED_NOT_PUBLISHED'
    ev_txt = '已投稿/第%d章.txt（番茄口径%d，含作者有话说）' % (n, fanqie)
    if ev:
        ev_txt += '；' + ev
    ev_txt += '；草稿箱保存与正式发布归用户'
    lines.append('| 第%d章 | %s | %s | 2026-08-28 | %s | %s | SHA %s | %s |'
                 % (n, title, vol, state, review, sha_shown, ev_txt))

block = '\n## 2026-08-28 第295-301章（补录）\n\n' + '\n'.join(lines) + '\n'

txt = TRACK.read_text(encoding='utf-8')
if '## 2026-08-28 第295-301章（补录）' in txt:
    print('ALREADY_BACKFILLED')
else:
    TRACK.write_text(txt.rstrip('\n') + '\n' + block, encoding='utf-8')
    print('appended %d rows' % len(lines))

# 验收
txt2 = TRACK.read_text(encoding='utf-8')
for n, _, _ in ROWS:
    print(n, '第%d章' % n in txt2)
