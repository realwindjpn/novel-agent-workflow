#!/usr/bin/env python3
from pathlib import Path
import re, json, shutil

base = Path('/root/workspace/科武纪元')
now = '2026-05-08'

def fanqie_count(text):
    lines = [x for x in text.splitlines() if x.strip()]
    title = lines[0] if lines else ''
    return len(re.sub(r'\s+', '', text)) - len(re.sub(r'\s+', '', title))

def cn_count(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))

bak = base / '备份' / '20260508_wiki_tracking_rag_sync'
bak.mkdir(parents=True, exist_ok=True)
for p in [base/'wiki/chapters/ch073.md', base/'wiki/chapters/ch074.md', base/'小说综合跟踪表.md', base/'wiki/concepts/chaos-model.md', base/'rag_kb/science/cards/science_cards.jsonl']:
    if p.exists():
        shutil.copy2(p, bak / p.name)

chapter_meta = {
    73: {
        'title': '钴矿夺回',
        'function': '夺回钴矿主矿区后，完成从战术控制到供应链证据闭环的转换，并牵引刚果残局。',
        'events': [
            '三号皮带廊清除AI机器人硬点，封存机体缓存。',
            '调度楼恢复地磅日志，定位B-17中转仓。',
            'B-17仓库缴获服务器、权限腕带、装船单与资金流证据。',
            '陈思琪补齐哈希校验、矿物指纹和航线/预付款节点，形成证据闭环。',
            '北侧山谷出现铁幕残余车队，携服务器灾备接管箱撤向旧钻石矿。',
        ],
        'actions': [
            '林星辰承担突入、清场、押解和现场压力。',
            '陈思琪负责调度内网、服务器镜像、哈希校验、矿物指纹与闭环图。',
            '赵刚限定行动边界：不越境、不碰防区、证据优先。',
            '方宁处理机体核心、服务器与灾备接管箱风险。',
        ],
        'hook': '刚果残余势力进入清剿残局，服务器灾备接管箱仍在车队手里，天亮后收网。',
        'risks': ['数字取证需有哈希校验，已补。', '灾备接管箱远程干扰需有独立卫星链路，已补。', '上传TXT需去除wikilink。'],
        'source_material': ['时事素材/素材卡/2026-05-07/素材卡_国产算力训练主权_能推到能训.md — 供应链与算力主权背景，仅作后续线索承接。'],
    },
    74: {
        'title': '刚果残局',
        'function': '把主战后的残余清剿、联合国框架、证据留存与政治代价写实落地，并引出南美锂三角。',
        'events': [
            '港区清剿中发现重复登记入口与壳公司暗线。',
            '拖车拦截确认矿袋与数据盘转移。',
            '仓库中发现自毁服务器、管理员硬件钥匙和远端擦写风险。',
            '吊机控制室交火后抢回部分数据，证据恢复率有限。',
            '残缺邮件关键词指向Salar/Litio/Triángulo，牵引南美锂三角。',
        ],
        'actions': [
            '林星辰负责现场突入、拦截与控制室攻坚，付出膝盖伤口代价。',
            '陈思琪执行只读取证、镜像、数据恢复和关键词识别。',
            '赵刚反复压住行动边界，保证联合国监督框架内取证。',
            '穆巴拉克上校体现当地政府军伤亡与程序成本冲突。',
        ],
        'hook': '下一份行动简报关键词变为锂盐湖、蒸发池、矿权公司、重卡电池和南美锂三角。',
        'risks': ['章末论文腔已压缩，并补动作反馈。', '含联合国框架，上传前注意现实机构表达克制。', '上传TXT需去除wikilink。'],
        'source_material': ['时事素材/2026-05-07.md — 资源战/供应链现实背景；未直接引用具体机构。'],
    },
}

for ch, meta in chapter_meta.items():
    src = base / '新版' / f'第{ch}章.md'
    text = src.read_text(encoding='utf-8')
    prev = f'[[ch{ch-1:03d}]]' if ch > 1 else ''
    nxt = f'[[ch{ch+1:03d}]]'
    body = [
        '---', f'chapter: {ch}', f'title: {meta["title"]}', 'created: 2026-05-03', f'updated: {now}', 'type: chapter', 'status: upload-preflight-pass', f'source: {src}', f'word_count: {cn_count(text)}', f'fanqie_count: {fanqie_count(text)}', '---', '',
        f'# 第{ch}章 {meta["title"]}', '', '## Links', f'- Previous: {prev}', f'- Next: {nxt}', '',
        '## Chapter Function', f'- {meta["function"]}', '',
        '## Key Events', *[f'- {x}' for x in meta['events']], '',
        '## Character Actions', *[f'- {x}' for x in meta['actions']], '',
        '## Ending Hook', f'- {meta["hook"]}', '',
        '## Risk Points', *[f'- {x}' for x in meta['risks']], '',
        '## Source Material', *[f'- {x}' for x in meta['source_material']], '',
        '## Review Notes', '- 2026-05-08 上传前真模型复审 PASS；记录见 `审核记录/六角色外审/上传前复审_73_74_修后复审_20260508.json`。', '',
        '## Full Text', text.rstrip(), ''
    ]
    (base / 'wiki/chapters' / f'ch{ch:03d}.md').write_text('\n'.join(body), encoding='utf-8')

raw_dir = base / 'wiki/raw/outline'
raw_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(base/'科武纪元大纲 V8_完整版.md', raw_dir/'科武纪元大纲V8.6_20260508.md')
shutil.copy2(base/'科武纪元大纲 V8_完整版.md', raw_dir/'科武纪元大纲_latest.md')

chaos = base / 'wiki/concepts/chaos-model.md'
ct = chaos.read_text(encoding='utf-8') if chaos.exists() else '# 四维混沌模型\n'
section = '''

## V8.6 时事素材注入（2026-05-08）

| 现实素材 | 混沌模型映射 | 对应章节 | 核心逻辑 |
| :--- | :--- | :--- | :--- |
| 国产算力训练主权：能推到能训 | **A(算法主权) vs 秩序(熵减)** | 第78/95/221章 | 铁幕封锁高端训练GPU与通信库；主角团用残缺国产阵列、低带宽拓扑和开源生态建立“能训练”的主权线。 |
| 地月规则竞赛：存在即权益 | **E(地缘摇摆) vs 秩序(熵减)** | 第156/169/221章 | 地月空间不是插旗，而是补给、通信、救援、规则制定能力；稳定存在本身就是权益来源。 |
| 军事AI蜂群与OODA压缩 | **C(群体智能)+A(算法主权)** | 第184/306/307章 | 蜂群与边缘AI压缩OODA，集中命令和分布式智能互相拉扯；主角团以群体身法/破阵点反制。 |
| 量子先存后解与后量子密钥 | **A(算法主权) vs D(AI/量子越界)** | 第220/261/381章 | 旧密文会成为未来风险；主角团用后量子密钥和生物电/内功波形建立不可克隆防线。 |
'''
if '## V8.6 时事素材注入（2026-05-08）' not in ct:
    ct = ct.rstrip() + section
ct = re.sub(r'updated: .*', 'updated: 2026-05-08', ct, count=1)
chaos.write_text(ct, encoding='utf-8')

pt = base / 'wiki/plot-threads/v8.6-current-events.md'
pt.parent.mkdir(parents=True, exist_ok=True)
pt.write_text('''# V8.6 时事素材线索映射

更新时间：2026-05-08

## 来源
- `/root/workspace/科武纪元/时事素材/2026-05-07.md`
- `/root/workspace/科武纪元/时事素材/素材卡/2026-05-07/`
- `/root/workspace/科武纪元/审核记录/大纲融合_20260507_V86.md`

## 四条主线

| 线索 | 素材卡 | 大纲章节 | 写作落点 |
|---|---|---|---|
| 国产算力训练主权 | 素材卡_国产算力训练主权_能推到能训.md | 78 / 95 / 221 | 从“能推理”推进到“能训练”，训练接口/通信拓扑/开源生态是主权线。 |
| 地月规则竞赛 | 素材卡_地月规则竞赛_存在即权益.md | 156 / 169 / 221 | 月面存在能力=补给/通信/救援/规则制定权。 |
| 军事AI蜂群 | 素材卡_军事AI蜂群_OODA压缩.md | 184 / 306 / 307 | 集中指挥与分布式智能冲突；蜂群无恐惧，只按杀伤链推进。 |
| 量子先存后解 | 素材卡_量子先存后解_后量子密钥.md | 220 / 261 / 381 | 历史通信包成为未来风险；后量子密钥和不可克隆波形是防线。 |

## 执行规则
- 已上传章：谨慎小改。
- 未上传且在 `新版/` 的章节：先备份，可按大纲重修/大改后覆盖 `新版/第X章.md`。
- 不使用 `待确认投稿/` 制造多版本。
''', encoding='utf-8')

rag = base / 'rag_kb/science/cards/science_cards.jsonl'
existing = []
if rag.exists():
    existing = [json.loads(l) for l in rag.read_text(encoding='utf-8').splitlines() if l.strip()]
titles = {c.get('title') for c in existing}
new = []
for i, p in enumerate(sorted((base/'时事素材/素材卡/2026-05-07').glob('素材卡_*.md')), 1):
    txt = p.read_text(encoding='utf-8')
    title = txt.splitlines()[0].lstrip('# ').replace('素材卡｜', '').strip() if txt.splitlines() else p.stem
    if title in titles:
        continue
    domains = []
    if '算力' in title or '芯片' in title:
        domains = ['AI算力', '芯片封锁', '训练主权']
    elif '地月' in title:
        domains = ['太空探索', '地月规则']
    elif '军事AI' in title or '蜂群' in title:
        domains = ['军事AI', '无人蜂群', 'OODA']
    elif '量子' in title:
        domains = ['量子计算', '通信安全', '后量子密码']
    m = re.search(r'小说映射[：:](.*)', txt) or re.search(r'- 小说映射：([^\n]+)', txt)
    novel_use = m.group(1).strip() if m else 'V8.6时事素材映射。'
    new.append({'id': 'current_20260507_' + str(i).zfill(2), 'source': '时事素材 2026-05-07', 'trust': 'B', 'title': title, 'domains': domains, 'content': txt, 'url': str(p), 'novel_use': novel_use, 'metrics': {'date': '2026-05-07', 'v': 'V8.6'}})
if new:
    with rag.open('a', encoding='utf-8') as f:
        for c in new:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')

track = base / '小说综合跟踪表.md'
t = track.read_text(encoding='utf-8')
t = re.sub(r'更新时间：[^\n]+', '更新时间：2026-05-08', t, count=1)
t = t.replace('**已上传平台**: 1-70章', '**已上传平台**: 1-72章（本地已投稿镜像连续；用户后台正文修改已完成1-19、65）')
t = t.replace('`已投稿/` | 上传用 (TXT, 纯文本) | ✅ 70章 (1-70) |', '`已投稿/` | 上传用 (TXT, 纯文本) | ✅ 72章 (1-72) |')
ops = '''

### 2026-05-08
- 第73-74章：上传前真模型复审 PASS；第73补哈希/矿物指纹/卫星灾备接管箱；第74压缩章末论文腔并补动作反馈。
- 第73-74章上传TXT已生成：`待上传TXT_73_74_20260508/`，无wikilink，白天可传。
- V8.6时事素材同步：大纲快照写入 `wiki/raw/outline/科武纪元大纲V8.6_20260508.md`；新增 `wiki/plot-threads/v8.6-current-events.md`；更新 `wiki/concepts/chaos-model.md`；4张2026-05-07素材卡追加到 RAG `science_cards.jsonl`。
'''
if '### 2026-05-08' not in t:
    t = t.rstrip() + ops
track.write_text(t, encoding='utf-8')

status = base / 'STATUS.md'
st = status.read_text(encoding='utf-8')
if 'Wiki/跟踪/RAG同步' not in st:
    st = st.replace('## 复核/证据\n', '## 复核/证据\n\n- Wiki/跟踪/RAG同步：73-74章节Wiki、V8.6 plot-thread、chaos-model、RAG素材卡、小说综合跟踪表已同步。\n')
status.write_text(st, encoding='utf-8')

wal = base / 'WAL.md'
wa = wal.read_text(encoding='utf-8')
entry = '''

## 2026-05-08 Wiki/跟踪/RAG补同步
- 用户提醒：大纲与章节修改后，Wiki、跟踪表、RAG也需一起更新。
- 已补：`wiki/chapters/ch073.md`、`wiki/chapters/ch074.md`、`wiki/raw/outline/科武纪元大纲V8.6_20260508.md`、`wiki/plot-threads/v8.6-current-events.md`、`wiki/concepts/chaos-model.md`。
- 已补：`小说综合跟踪表.md` 与 `rag_kb/science/cards/science_cards.jsonl`。
- 备份：`/root/workspace/科武纪元/备份/20260508_wiki_tracking_rag_sync/`。
'''
if '## 2026-05-08 Wiki/跟踪/RAG补同步' not in wa:
    wal.write_text(wa.rstrip() + entry, encoding='utf-8')

print(json.dumps({'wiki_chapters': [str(base/'wiki/chapters/ch073.md'), str(base/'wiki/chapters/ch074.md')], 'rag_new': len(new), 'backup': str(bak)}, ensure_ascii=False, indent=2))
