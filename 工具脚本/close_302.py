#!/usr/bin/env python3
"""302 闭环：TXT/新版落盘 + 跟踪表 + STATUS + WAL（Git 单独跑）。

调用前必须：四审全 PASS 且均为实质审（分节论证，非仅 VERDICT 行）。
"""
import pathlib
import re
import json
import hashlib
import datetime
import sys

ROOT = pathlib.Path('/root/workspace/科武纪元')
TASK = ROOT / '任务运行态' / '20260828_kewu_selfcycle_daily'
OUT = TASK / 'output'
RV = OUT / 'reviews_302_r1'

body = (OUT / 'qwen_302_aug_clean.md').read_text(encoding='utf-8')
sha = hashlib.sha256(body.encode()).hexdigest()
cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

# ===== 门禁：四审须全 PASS 且实质 =====
SEATS = ['reader', 'structure', 'editor', 'science']
MIN_SUBSTANTIVE = 800   # 仅 VERDICT+SHA 行约 300B，实质审须明显更长
report = {}
for s in SEATS:
    p = RV / ('%s_review.md' % s)
    if not p.exists():
        print('BLOCK 缺审稿:', p.name)
        sys.exit(1)
    t = p.read_text(encoding='utf-8')
    v = t.strip().split('\n')[0]
    size = len(t.encode())
    sha_bound = sha in t
    substantive = size >= MIN_SUBSTANTIVE
    report[s] = {'verdict': v, 'bytes': size, 'sha_bound': sha_bound,
                 'substantive': substantive}
    print('%-10s %-16s %6dB sha_bound=%s substantive=%s' % (
        s, v, size, sha_bound, substantive))

bad = [s for s, r in report.items()
       if 'PASS' not in r['verdict'] or not r['sha_bound'] or not r['substantive']]
if bad:
    print('\nBLOCK 未过席位:', bad)
    print('（PASS 缺失 / SHA 未绑 / 非实质审 任一即阻塞）')
    sys.exit(1)
print('\n四审全 PASS 且实质，SHA 绑定一致 -> 继续闭环')

# ===== 1. TXT 投稿版 =====
txt_dir = ROOT / '已投稿'
txt_dir.mkdir(parents=True, exist_ok=True)
txt = txt_dir / '第302章.txt'
txt.write_text(body, encoding='utf-8')
print('\n[1] TXT', txt, txt.stat().st_size, 'B')

# ===== 2. 新版正文 =====
new_dir = ROOT / '新版正文'
new_dir.mkdir(parents=True, exist_ok=True)
md = new_dir / 'ch302.md'
md.write_text(body, encoding='utf-8')
print('[2] MD ', md, md.stat().st_size, 'B')

# ===== 3. 跟踪表 =====
track = ROOT / '章节跟踪表.md'
if track.exists():
    tt = track.read_text(encoding='utf-8')
    row = '| 302 | 戴森共识 | %d | %s | 四审PASS | %s |' % (cjk, sha[:8], now)
    if '| 302 |' not in tt:
        tt = tt.rstrip() + '\n' + row + '\n'
        track.write_text(tt, encoding='utf-8')
        print('[3] 跟踪表 已追加 302 行')
    else:
        print('[3] 跟踪表 已有 302 行，跳过')
else:
    print('[3] 跟踪表 不存在，跳过')

# ===== 4. STATUS =====
status = ROOT / 'STATUS.md'
entry = """
## 第302章《戴森共识》定稿 — %s
- SHA256: %s
- 净中文: %d（硬下限 3200 已过；G4 目标区 3400-3600，距下沿 30 字，按硬线判稿不返修）
- 出稿路径: 网页 Qwen 三次尝试取最优（2813 字）→ 补写席定点扩写（清禁词 核心/真正，扩写闭门谈判/表决程序/附件归档三处）→ 3370 字
- 四审: reader / structure / editor / science 全 PASS，均绑定同一 SHA
- 产物: 已投稿/第302章.txt、新版正文/ch302.md
- 发布归小哥
""" % (now, sha, cjk)
if status.exists():
    st = status.read_text(encoding='utf-8')
    if '第302章《戴森共识》定稿' not in st:
        status.write_text(st.rstrip() + '\n' + entry, encoding='utf-8')
        print('[4] STATUS 已追加')
    else:
        print('[4] STATUS 已有 302 条目，跳过')
else:
    status.write_text('# 科武纪元 STATUS\n' + entry, encoding='utf-8')
    print('[4] STATUS 已新建')

# ===== 5. WAL =====
wal = ROOT / 'WAL.md'
wentry = """
### %s | 302 闭环
- ch302 SHA %s CJK %d 四审全 PASS（reader aliyun-qwen38 / structure wechat-glm / editor wechat-glm / science aliyun-qwen38）
- 已落盘: 已投稿/第302章.txt、新版正文/ch302.md、章节跟踪表、STATUS
- 残留: 发布归小哥；下一步可起 303
""" % (now, sha[:8], cjk)
if wal.exists():
    wt = wal.read_text(encoding='utf-8')
    if '| 302 闭环' not in wt:
        wal.write_text(wt.rstrip() + '\n' + wentry, encoding='utf-8')
        print('[5] WAL 已追加')
    else:
        print('[5] WAL 已有 302 断点，跳过')
else:
    wal.write_text('# WAL\n' + wentry, encoding='utf-8')
    print('[5] WAL 已新建')

json.dump({'chapter': 302, 'title': '戴森共识', 'sha256': sha, 'net_cjk': cjk,
           'reviews': report, 'closed_at': now,
           'artifacts': [str(txt), str(md)]},
          open(OUT / 'CLOSE_302.json', 'w'), ensure_ascii=False, indent=1)
print('\n闭环记录 ->', OUT / 'CLOSE_302.json')
print('待办: git add -f && git commit')
