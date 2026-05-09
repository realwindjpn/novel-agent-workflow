#!/usr/bin/env python3
from pathlib import Path
import json, re, shutil
base=Path('/root/workspace/科武纪元')
kg=base/'wiki/kg'
backup=base/'备份/20260508_kg_sync'
backup.mkdir(parents=True,exist_ok=True)
for p in [kg/'relations.md',kg/'triples.jsonl',kg/'entities.json']:
    if p.exists(): shutil.copy2(p, backup/p.name)

def add_json_file(ch, entities, concepts, relations, notes):
    data={'chapter':ch,'updated':'2026-05-08','entities':entities,'concepts':concepts,'relations':relations,'notes':notes}
    p=kg/f'ch{ch:03d}_20260508_sync.json'
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return p

files=[]
files.append(add_json_file(73,
 ['林星辰','陈思琪','方宁','谢云','赵刚','铁幕联盟','蓝幔贸易','Blue Mantle Trading','瓦尔帕莱索港','刚果残余势力'],
 ['钴矿供应链','矿物指纹','哈希校验','服务器灾备接管箱','独立卫星链路','权限链','AIS异常航线'],
 [
  ['第73章','contains_entity','蓝幔贸易'],['蓝幔贸易','registered_in','开曼'],['蓝幔贸易','payment_route','卢森堡账户'],
  ['第73章','contains_concept','矿物指纹'],['矿物指纹','evidence_for','钴矿来源溯源'],['第73章','contains_concept','哈希校验'],['哈希校验','secures','服务器镜像证据'],
  ['服务器灾备接管箱','has_capability','独立卫星链路'],['服务器灾备接管箱','threatens','矿区远程调度权'],
  ['第73章','ending_hook','刚果残余势力天亮后收网'],['第73章','next','第74章']
 ],
 '上传前复审补强：数字取证与灾备接管箱技术前提已闭环。'))
files.append(add_json_file(74,
 ['林星辰','陈思琪','方宁','谢云','赵刚','穆巴拉克上校','联合国监督组','铁幕联盟','南美锂三角'],
 ['刚果残局','联合国框架清剿','只读取证','管理员硬件钥匙','远端擦写','Salar','Litio','Triángulo','锂盐湖'],
 [
  ['第74章','contains_entity','穆巴拉克上校'],['穆巴拉克上校','represents','当地政府军代价'],['第74章','contains_entity','联合国监督组'],['联合国监督组','constrains','清剿取证边界'],
  ['第74章','contains_concept','管理员硬件钥匙'],['管理员硬件钥匙','accesses','海运系统/海外服务器'],['第74章','contains_concept','远端擦写'],
  ['Salar','points_to','盐湖'],['Litio','points_to','锂'],['Triángulo','points_to','南美锂三角'],['第74章','ending_hook','南美锂三角'],['第74章','next','第75章']
 ],
 '上传前复审补强：章末论文腔已压缩，南美锂三角钩子保留。'))
files.append(add_json_file(0,
 ['铁幕联盟','主角团/南天门','月面规则参与方','无人蜂群','量子攻击方'],
 ['V8.6','国产算力训练主权','地月规则竞赛','军事AI蜂群','OODA压缩','量子先存后解','后量子密钥'],
 [
  ['国产算力训练主权','maps_to','第78章'],['国产算力训练主权','maps_to','第95章'],['国产算力训练主权','maps_to','第221章'],
  ['地月规则竞赛','maps_to','第156章'],['地月规则竞赛','maps_to','第169章'],['地月规则竞赛','maps_to','第221章'],
  ['军事AI蜂群','maps_to','第184章'],['军事AI蜂群','maps_to','第306章'],['军事AI蜂群','maps_to','第307章'],
  ['量子先存后解','maps_to','第220章'],['量子先存后解','maps_to','第261章'],['量子先存后解','maps_to','第381章'],
  ['国产算力训练主权','source_card','素材卡_国产算力训练主权_能推到能训'],['量子先存后解','source_card','素材卡_量子先存后解_后量子密钥']
 ],
 'V8.6时事素材与大纲章节映射。'))

trip=kg/'triples.jsonl'
existing=set(trip.read_text(encoding='utf-8').splitlines()) if trip.exists() else set()
new_lines=[]
for fp in files:
    data=json.loads(fp.read_text(encoding='utf-8'))
    ch=data['chapter']
    subj=f'ch{ch:03d}' if ch else 'V8.6'
    new_lines.append(json.dumps({'s':subj,'p':'has_kg_sync','o':fp.name,'chapter':ch},ensure_ascii=False))
    if ch:
        for e in data['entities']:
            new_lines.append(json.dumps({'s':subj,'p':'contains_entity','o':e,'chapter':ch},ensure_ascii=False))
        for c in data['concepts']:
            new_lines.append(json.dumps({'s':subj,'p':'contains_concept','o':c,'chapter':ch},ensure_ascii=False))
    for s,p,o in data['relations']:
        new_lines.append(json.dumps({'s':s,'p':p,'o':o,'chapter':ch},ensure_ascii=False))
with trip.open('a',encoding='utf-8') as f:
    for l in new_lines:
        if l not in existing: f.write(l+'\n')

entities=kg/'entities.json'
edata=json.loads(entities.read_text(encoding='utf-8')) if entities.exists() else {'entities':[],'concepts':[]}
def upsert(arr,name,typ):
    for x in arr:
        if x.get('name')==name:
            x['chapter_mentions']=max(int(x.get('chapter_mentions',0)),1); x['updated']='2026-05-08'; return
    arr.append({'name':name,'type':typ,'chapter_mentions':1,'updated':'2026-05-08'})
for fp in files:
    data=json.loads(fp.read_text(encoding='utf-8'))
    for e in data['entities']: upsert(edata.setdefault('entities',[]),e,'entity')
    for c in data['concepts']: upsert(edata.setdefault('concepts',[]),c,'concept')
entities.write_text(json.dumps(edata,ensure_ascii=False,indent=2),encoding='utf-8')

lines=trip.read_text(encoding='utf-8').splitlines()
chapters=set(); ents=set(); cons=set()
for l in lines:
    try: d=json.loads(l)
    except: continue
    if d.get('chapter'): chapters.add(d.get('chapter'))
    if d.get('p')=='contains_entity': ents.add(d.get('o'))
    if d.get('p')=='contains_concept': cons.add(d.get('o'))
rel=kg/'relations.md'
rt=rel.read_text(encoding='utf-8') if rel.exists() else '# KG Relations\n\n## Relation Types\n\n## Stats\n- chapters: 0\n- triples: 0\n- entities: 0\n- concepts: 0\n'
rt=re.sub(r'- chapters: .*', f'- chapters: {len(chapters)}', rt)
rt=re.sub(r'- triples: .*', f'- triples: {len(lines)}', rt)
rt=re.sub(r'- entities: .*', f'- entities: {len(ents)}', rt)
rt=re.sub(r'- concepts: .*', f'- concepts: {len(cons)}', rt)
add='''

## 2026-05-08 闭环同步
- synced_chapters: 73, 74
- synced_outline: V8.6 current-events mapping
- source: `ch073_20260508_sync.json`, `ch074_20260508_sync.json`, `ch000_20260508_sync.json`
- backup: `/root/workspace/科武纪元/备份/20260508_kg_sync/`
'''
if '## 2026-05-08 闭环同步' not in rt: rt=rt.rstrip()+add
rel.write_text(rt,encoding='utf-8')

script=base/'工具脚本/kewu_closure_check.py'
st=script.read_text(encoding='utf-8')
if 'KG同步文件存在' not in st:
    st=st.replace("evidence=BASE/'审核记录/证据包'/f'第{ch}章_证据包.md'", "evidence=BASE/'审核记录/证据包'/f'第{ch}章_证据包.md'\n    kgfile=BASE/'wiki/kg'/f'ch{ch:03d}_20260508_sync.json'")
    st=st.replace("if evidence.exists():\n        res.append(('证据包存在', True, str(evidence)))", "if evidence.exists():\n        res.append(('证据包存在', True, str(evidence)))\n    res.append(('KG同步文件存在', kgfile.exists(), str(kgfile)))")
    st=st.replace("BASE/'wiki/plot-threads/v8.6-current-events.md',", "BASE/'wiki/plot-threads/v8.6-current-events.md',\n        BASE/'wiki/kg/ch000_20260508_sync.json',\n        BASE/'wiki/kg/relations.md',")
    script.write_text(st,encoding='utf-8')

status=base/'STATUS.md'
txt=status.read_text(encoding='utf-8')
txt=txt.replace('Wiki/跟踪/RAG同步：','Wiki/KG/跟踪/RAG同步：').replace('73-74章节Wiki、','73-74章节Wiki、KG同步文件、')
status.write_text(txt,encoding='utf-8')
wal=base/'WAL.md'
wt=wal.read_text(encoding='utf-8')
if '## 2026-05-08 KG补同步' not in wt:
    wt += '\n\n## 2026-05-08 KG补同步\n- 已补KG：`wiki/kg/ch073_20260508_sync.json`、`wiki/kg/ch074_20260508_sync.json`、`wiki/kg/ch000_20260508_sync.json`。\n- 已追加 triples 并更新 `wiki/kg/entities.json`、`wiki/kg/relations.md`。\n- 已将 KG 纳入 `kewu_closure_check.py` 门禁。\n'
wal.write_text(wt,encoding='utf-8')
print(json.dumps({'kg_files':[str(x) for x in files],'backup':str(backup),'triples':len(lines),'entities':len(ents),'concepts':len(cons)},ensure_ascii=False,indent=2))
