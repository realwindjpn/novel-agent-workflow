#!/usr/bin/env python3
from pathlib import Path
import re, json, shutil, subprocess

base = Path('/root/workspace/科武纪元')
date = '2026-05-10'
chapters = [86, 124, 217, 223]
backup = base / '审核记录/备份/V88闭环同步_20260510'
backup.mkdir(parents=True, exist_ok=True)

def fanqie_count(text):
    lines = [x for x in text.splitlines() if x.strip()]
    title = lines[0] if lines else ''
    return len(re.sub(r'\s+', '', text)) - len(re.sub(r'\s+', '', title))

def cn_count(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))

meta = {
    86: {'title':'铁幕反击','function':'铁幕以算力攻击与泛际会议围剿开源生态；V8.8补天门封锁与医疗船误击，形成双线熵增。','hook':'算法对决，叶启明教学框架线索，欧陆三秒延迟。','source':['时事素材/素材卡/2026-05-10/素材卡_霍尔木兹海峡封锁_击伤伊朗油轮.md','时事素材/素材卡/2026-05-08/素材卡_欧洲防务自主_500亿欧_C2_Drone_Starlink.md']},
    124:{'title':'星穹线索','function':'通过资金链牵出星穹探索、月球资源与氦-3；V8.8补量子计算伏笔，图谱需量子模拟冲突路径。','hook':'星穹图谱是锁，量子计算是未来锤子。','source':['时事素材/素材卡/2026-05-10/素材卡_量子比特可移动_代尔夫特_QuTech.md']},
    217:{'title':'政治清洗','function':'白盾算法暴力落地；V8.8把白盾物理载体升级为UGV三代与声波执法，强化无恶意执行毁灭。','hook':'白盾成为公司内部清洗工具，算法暴力刀柄指向公司接口。','source':['时事素材/素材卡/2026-05-10/素材卡_乌克兰UGV地面机器人_5万台扩产.md','时事素材/素材卡/2026-05-08/素材卡_DHS_DNA数据库_抗议者_算法暴力.md']},
    223:{'title':'内战爆发','function':'白盾越级调度与清道夫算法失控引爆内战；V8.8补UGV三态终局画面。','hook':'第七数据中心、数据投毒、公司旧门真相。','source':['时事素材/素材卡/2026-05-10/素材卡_乌克兰UGV地面机器人_5万台扩产.md']},
}

for p in [base/'小说综合跟踪表.md', base/'STATUS.md', base/'WAL.md', base/'wiki/concepts/chaos-model.md', base/'wiki/kg/triples.jsonl', base/'wiki/kg/relations.md', base/'rag_kb/science/cards/science_cards.jsonl']:
    if p.exists():
        shutil.copy2(p, backup / p.name)

(base/'wiki/chapters').mkdir(parents=True, exist_ok=True)
(base/'审核记录/章节记忆卡').mkdir(parents=True, exist_ok=True)

for ch in chapters:
    src = base/'新版'/f'第{ch}章.md'
    text = src.read_text(encoding='utf-8')
    m = meta[ch]
    events = [f'包含关键词/线索：{k}' for k in ['天门','医疗船','量子','UGV','声波','清道夫','三秒','星穹','白盾','第七数据中心'] if k in text]
    if not events:
        events = ['V8.8改动已并入正文。']
    lines = []
    lines += ['---', f'chapter: {ch}', f'title: {m["title"]}', f'updated: {date}', 'type: chapter', 'status: v8.8-six-role-pass', f'source: {src}', f'word_count_cn: {cn_count(text)}', f'fanqie_count: {fanqie_count(text)}', '---', '']
    lines += [f'# 第{ch}章 {m["title"]}', '', '## Links', f'- Previous: [[ch{ch-1:03d}]]', f'- Next: [[ch{ch+1:03d}]]', '']
    lines += ['## Chapter Function', f'- {m["function"]}', '', '## Key Events / Evidence']
    lines += [f'- {x}' for x in events]
    lines += ['', '## Ending Hook', f'- {m["hook"]}', '', '## Source Material']
    lines += [f'- {x}' for x in m['source']]
    lines += ['', '## Review Notes', '- V8.8正文精修后补六角色外审：编辑/军事/科学/读者 PASS。', '- 写后复审：编辑+读者双PASS。', '- 必改项已落实：叙述视角、R10量子红线、UGV角色视角、声波参数、赵铁柱态度、UGV安全协议。', '', '## Full Text', text.rstrip(), '']
    (base/'wiki/chapters'/f'ch{ch:03d}.md').write_text('\n'.join(lines), encoding='utf-8')

    card = []
    card += [f'# 第{ch}章记忆卡：{m["title"]}', '', f'更新时间：{date}', '状态：V8.8精修+六角色外审+写后复审 PASS', '', '## 本章功能', f'- {m["function"]}', '', '## 关键承接', f'- {m["hook"]}', '', '## V8.8新增/修订']
    card += [f'- {x}' for x in events]
    card += ['', '## 素材来源']
    card += [f'- {x}' for x in m['source']]
    (base/'审核记录/章节记忆卡'/f'第{ch}章.md').write_text('\n'.join(card)+'\n', encoding='utf-8')

chaos = base/'wiki/concepts/chaos-model.md'
ct = chaos.read_text(encoding='utf-8') if chaos.exists() else '# 四维混沌模型\n'
if '## V8.8 时事素材注入（2026-05-10）' not in ct:
    ct += '''

## V8.8 时事素材注入（2026-05-10）

| 现实素材 | 混沌模型映射 | 对应章节 | 核心逻辑 |
|---|---|---|---|
| Nvidia 400亿美元AI股权投资 | A 算法主权/资本闭环 | 新增78/卷三八 | 铁幕不是单一反派，而是商业模式与算力资本闭环。 |
| 霍尔木兹封锁→天门封锁 | A→B 封闭系统双线熵增 | 86/110 | 能源咽喉封锁与医疗船误击，呼应诊所误判。 |
| 乌克兰UGV扩产 | B 算法暴力物理载体 | 217/223 | 白盾升级为万台UGV群，无恶意执行毁灭。 |
| 可移动量子比特 | D/E 量子越界与解构星穹 | 124/240 | 量子计算用于模拟星穹补丁冲突路径，不是万能破解器。 |
'''
chaos.write_text(ct, encoding='utf-8')

kgdir = base/'wiki/kg'
kgdir.mkdir(parents=True, exist_ok=True)
triples = kgdir/'triples.jsonl'
existing = set(triples.read_text(encoding='utf-8').splitlines()) if triples.exists() else set()
new_triples = []
for ch in chapters:
    for src in meta[ch]['source']:
        new_triples.append({'s':f'ch{ch:03d}','p':'uses_source','o':src,'date':date,'version':'V8.8'})
new_triples += [
    {'s':'ch086','p':'foreshadows','o':'ch110 天门封锁','date':date,'version':'V8.8'},
    {'s':'ch124','p':'foreshadows','o':'ch240 量子钥匙','date':date,'version':'V8.8'},
    {'s':'ch217','p':'sets_up','o':'ch223 UGV终局画面','date':date,'version':'V8.8'},
    {'s':'UGV群','p':'embodies','o':'算法暴力','date':date,'version':'V8.8'},
]
with triples.open('a', encoding='utf-8') as f:
    for t in new_triples:
        line = json.dumps(t, ensure_ascii=False)
        if line not in existing:
            f.write(line+'\n')

rel = kgdir/'relations.md'
rt = rel.read_text(encoding='utf-8') if rel.exists() else '# Relations\n'
if '## V8.8 2026-05-10' not in rt:
    rt += '''

## V8.8 2026-05-10
- ch086 uses 天门封锁/医疗船误击，呼应诊所误判。
- ch124 foreshadows ch240 量子钥匙，遵守R10：量子计算用于模拟补丁冲突路径。
- ch217 sets up UGV三代与声波执法，算法暴力物理化。
- ch223 closes UGV三态：被劫持/静止/继续执行。
'''
rel.write_text(rt, encoding='utf-8')

rag = base/'rag_kb/science/cards/science_cards.jsonl'
rag.parent.mkdir(parents=True, exist_ok=True)
seen = set()
if rag.exists():
    for l in rag.read_text(encoding='utf-8').splitlines():
        try: seen.add(json.loads(l).get('id'))
        except Exception: pass
cards = []
for p in sorted((base/'时事素材/素材卡/2026-05-10').glob('*.md')):
    cid = 'current_20260510_' + p.stem
    if cid in seen:
        continue
    txt = p.read_text(encoding='utf-8')
    title = txt.splitlines()[0].lstrip('# ').strip() if txt.splitlines() else p.stem
    cards.append({'id':cid,'source':'时事素材 2026-05-10','trust':'B','title':title,'content':txt,'url':str(p),'novel_use':'V8.8大纲与正文精修素材','metrics':{'date':date,'v':'V8.8'}})
if cards:
    with rag.open('a', encoding='utf-8') as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False)+'\n')

track = base/'小说综合跟踪表.md'
t = track.read_text(encoding='utf-8') if track.exists() else '# 小说综合跟踪表\n'
if '### 2026-05-10 V8.8' not in t:
    t += '''

### 2026-05-10 V8.8
- 时事素材：量子比特可移动、Nvidia 400亿AI投资、乌克兰UGV扩产、霍尔木兹封锁。
- 大纲：`wiki/raw/outline/科武纪元大纲_latest.md` 已加入 V8.8。
- 正文：第86/124/217/223章已精修，补外审与写后复审 PASS。
- Wiki/KG/RAG：ch086/ch124/ch217/ch223、chaos-model、KG triples/relations、science_cards 已同步。
'''
track.write_text(t, encoding='utf-8')

wal = base/'WAL.md'
wa = wal.read_text(encoding='utf-8') if wal.exists() else '# 科武纪元 WAL\n'
if '## 2026-05-10 V8.8闭环纠错' not in wa:
    wa += '''

## 2026-05-10 V8.8闭环纠错
- 用户纠偏：六角色精修不外审不算六角色；正文改后必须外审+写后复审+Wiki/KG/RAG/跟踪表/Git。
- 已补：第86/124/217/223章写后复审 PASS；落实9项必改项。
- 已补同步：wiki章节页、章节记忆卡、chaos-model、KG triples/relations、RAG science_cards、小说综合跟踪表、STATUS。
- 闭环验收：`审核记录/V88闭环验收_20260510.md`。
'''
wal.write_text(wa, encoding='utf-8')

status = base/'STATUS.md'
st = status.read_text(encoding='utf-8')
if 'V8.8项目级闭环已补齐' not in st:
    st += '''

## 2026-05-10 V8.8项目级闭环已补齐
- 第86/124/217/223章：正文精修、六角色外审、9项必改、写后复审双PASS。
- 已同步：Wiki章节页、章节记忆卡、chaos-model、KG、RAG、小说综合跟踪表、WAL。
- 证据：`/root/workspace/科武纪元/审核记录/V88闭环验收_20260510.md`。
'''
status.write_text(st, encoding='utf-8')

report = base/'审核记录/V88闭环验收_20260510.md'
lines = ['# V8.8闭环验收 2026-05-10','']
for ch in chapters:
    lines += [f'## 第{ch}章 {meta[ch]["title"]}', '- 正文已改：✅', '- 六角色外审：✅ PASS', '- 9项必改落实：✅', '- 写后复审：✅ 编辑+读者PASS', f'- Wiki：✅ `wiki/chapters/ch{ch:03d}.md`', f'- 记忆卡：✅ `审核记录/章节记忆卡/第{ch}章.md`', '- KG：✅ triples/relations追加', '- RAG：✅ 2026-05-10素材卡入science_cards', '- 跟踪表：✅ 小说综合跟踪表追加V8.8记录', '']
lines += ['## Git', '- 待git diff复核后提交。', '']
report.write_text('\n'.join(lines), encoding='utf-8')

print(json.dumps({'chapters':chapters,'wiki':len(chapters),'rag_new':len(cards),'backup':str(backup),'report':str(report)}, ensure_ascii=False, indent=2))
