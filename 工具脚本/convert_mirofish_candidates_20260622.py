from pathlib import Path
import json, re, datetime

base = Path('/root/workspace/科武纪元')
bridge = base/'自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260622_1604_final/bridge_runs/cron_20260622_1604'
tasks = json.loads((bridge/'card_conversion_tasks.json').read_text(encoding='utf-8'))
decisions = {d['material_id']: d for d in json.loads((bridge/'decision_cards.json').read_text(encoding='utf-8'))}

out_dir = base/'时事素材/素材卡/2026-06-22'
raw_dir = base/'时事素材/原文备份/2026-06-22'
out_dir.mkdir(parents=True, exist_ok=True)
raw_dir.mkdir(parents=True, exist_ok=True)

index_path = base/'时事素材/INDEX.md'
kb_index_path = base/'知识库/INDEX.md'
wal_path = base/'WAL.md'
status_report = base/'自循环体系/sensenova_mirofish_auto_integration_20260606/bridge_runs/cron_20260622_1604_final/FORMAL_CARD_INGEST_REPORT.md'

category_map = {
    'Tropical Storm Arthur': ('太空探索/地球观测', '第156章准备：遥感盲区、灾害观测、侦察代价；只作细节变量。'),
    'Galileo signal updated for internet-of-things use': ('深空通信/导航抗干扰', '第156章准备：低功耗定位、E5a-QP、抗欺骗/抗干扰、IoT定位链路。'),
    '科学家让活细胞成像既全又清': ('生物技术/AI成像', '第359章远端准备：活细胞长时观测、大视野AI复原、科研治理与人才争夺。'),
    '央地共建粤港澳大湾区国际科技创新中心工作推进会在广州召开': ('制度工程/区域科创', '第125章背景：国家级科创中心、数据算力算法应用一体、湾区产业组织。'),
    '两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动': ('社会治理/算法治理', '第125章背景：基层网格、平台治理、跨境诈骗人口与资金链治理。'),
}

slug_map = {
    'Tropical Storm Arthur': '素材卡_Tropical_Storm_Arthur_遥感灾害观测_20260622.md',
    'Galileo signal updated for internet-of-things use': '素材卡_Galileo_E5a_QP_低功耗定位_20260622.md',
    '科学家让活细胞成像既全又清': '素材卡_LargePNet_活细胞AI成像_20260622.md',
    '央地共建粤港澳大湾区国际科技创新中心工作推进会在广州召开': '素材卡_粤港澳科创中心_产业组织_20260622.md',
    '两部门部署在全国开展2026年“全民反诈在行动”集中宣传月活动': '素材卡_全民反诈_基层治理与平台治理_20260622.md',
}

blocked = []
written = []
index_lines = []
kb_lines = []

existing_index = index_path.read_text(encoding='utf-8', errors='ignore') if index_path.exists() else ''
existing_kb = kb_index_path.read_text(encoding='utf-8', errors='ignore') if kb_index_path.exists() else ''

for t in tasks:
    title = t['title']
    d = decisions.get(t['material_id'], {})
    if title not in slug_map:
        # Verified mismatch/duplicate: conversion title says high-quality dataset, but source body is Tau law and already indexed.
        blocked.append({
            'title': title,
            'reason': 'SOURCE_TITLE_BODY_MISMATCH_OR_DUPLICATE_AFTER_CONTROLLER_REVIEW',
            'source_url': t.get('source_url',''),
            'source_card_path': t.get('source_card_path',''),
        })
        continue
    source_card = Path(t['source_card_path'])
    if not source_card.exists():
        blocked.append({'title': title, 'reason': 'SOURCE_CARD_MISSING', 'source_card_path': str(source_card)})
        continue
    text = source_card.read_text(encoding='utf-8', errors='ignore')
    body_match = re.search(r'## Body Extract\n\n(.*?)(?:\n## AI Distill|\Z)', text, flags=re.S)
    body = (body_match.group(1).strip() if body_match else '')
    if len(body) < 500:
        blocked.append({'title': title, 'reason': 'BODY_TOO_SHORT_AFTER_REVIEW', 'source_card_path': str(source_card)})
        continue
    raw_path = raw_dir/(slug_map[title].replace('素材卡_', '原文_').replace('.md','.md'))
    raw_path.write_text(f"# 原文备份：{title}\n\n来源：{t['source_url']}\n抓取日期：2026-06-22\n源卡：{source_card}\n\n## 正文\n\n{body}\n", encoding='utf-8')
    category, mapping = category_map[title]
    reason = d.get('disposition_reason','')
    target_ch = t.get('target_chapter_hint', '')
    out_path = out_dir/slug_map[title]
    card = f"""# 素材卡：{title}

日期：2026-06-22
来源：{t['source_url']}
类型：{category}
可信度：primary_official
状态：CHAPTER_PREP_ONLY
MiroFish material_id：{t['material_id']}
源卡：{source_card}
原文备份：{raw_path}

## 一句话
{reason or mapping}

## 关键事实
"""
    # lightweight fact extraction from visible source-card lines
    facts = []
    for line in text.splitlines():
        s=line.strip('- ').strip()
        if not s or s.startswith('#') or s.startswith('source:') or len(s)<12:
            continue
        if any(k in s for k in ['2026', 'NASA', 'Galileo', 'LargePNet', '公安', '科技部', '公里', '英里', '倍', '亿元', '万', 'dB', '卫星', 'AI', '人工智能']):
            facts.append(s)
        if len(facts)>=6:
            break
    if not facts:
        facts=[reason or mapping]
    for f in facts[:6]:
        card += f"- {f}\n"
    card += f"""
## 可用细节
- 来源已抓正文，非 query_plan 骨架。
- MiroFish 裁决：{d.get('disposition','CHAPTER_PREP_ONLY')}。
- 适配章节：第{target_ch}章准备包；不直接改大纲。

## 小说映射
- 可映射章节/卷：第{target_ch}章准备包
- 对应变量：{category}
- 使用建议：{mapping}

## 反模式/禁忌
- 不把素材写成万能外挂。
- 不直接改大纲、正文、TXT或草稿箱。
- 不把 query_plan、频道页、导航文本当正文证据。

## MiroFish 裁决
- disposition：{d.get('disposition','')}
- reason：{reason}
- decision_cards：{bridge/'decision_cards.json'}
"""
    out_path.write_text(card, encoding='utf-8')
    rel = out_path.relative_to(base)
    index_line = f"| 2026-06-22 | {title} | {category} | `{raw_path.relative_to(base)}` | `{rel}` | {mapping} |"
    kb_line = f"| [{title}]({rel}) | primary official；MiroFish={d.get('disposition','')} | {mapping} | {t['source_url']} |"
    if str(rel) not in existing_index:
        index_lines.append(index_line)
    if str(rel) not in existing_kb:
        kb_lines.append(kb_line)
    written.append({'title': title, 'card': str(out_path), 'raw': str(raw_path), 'category': category, 'mapping': mapping})

if index_lines:
    section = "\n\n## MiroFish Bridge 转正式素材卡 2026-06-22\n\n| 日期 | 主题 | 领域 | 原文 | 素材卡 | 可用方向 |\n|---|---|---|---|---|---|\n" + "\n".join(index_lines) + "\n"
    index_path.write_text(existing_index.rstrip()+section, encoding='utf-8')
if kb_lines:
    section = "\n\n## MiroFish Bridge 素材准备包 2026-06-22\n\n| 素材卡 | 核心数据 | 小说映射 | 来源 |\n|--------|---------|---------|------|\n" + "\n".join(kb_lines) + "\n"
    kb_index_path.write_text(existing_kb.rstrip()+section, encoding='utf-8')

wal_entry = f"""
## 2026-06-22 {datetime.datetime.now().strftime('%H:%M')}｜MiroFish Bridge 转正式素材卡
- 来源：SenseNova run `cron_20260622_1604` → MiroFish bridge `cron_20260622_1604_final`。
- 已写正式素材卡：{len(written)} 张；同步时事素材 INDEX 与知识库 INDEX。
- 未写：{len(blocked)} 条；原因见报告，多为标题正文不匹配/重复。
- 边界：只做 CHAPTER_PREP_ONLY 素材入库；未改大纲、正文、TXT、草稿箱。
- 报告：`{status_report}`。
"""
wal_old = wal_path.read_text(encoding='utf-8', errors='ignore') if wal_path.exists() else ''
wal_path.write_text(wal_entry + "\n" + wal_old, encoding='utf-8')

report = {
    'status': 'DONE_WITH_BLOCKED_ITEMS',
    'source_bridge': str(bridge),
    'written_count': len(written),
    'written': written,
    'blocked_count': len(blocked),
    'blocked': blocked,
    'index_updated': bool(index_lines),
    'kb_index_updated': bool(kb_lines),
    'wal_updated': True,
}
status_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
