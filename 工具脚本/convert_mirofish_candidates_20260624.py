"""
MiroFish Bridge 正式落库脚本 — 2026-06-24 cron
基于 2026-06-22 脚本同构，覆盖本轮 5 OUTLINE_PATCH + 1 CHAPTER_PREP_ONLY 共 6 张正式卡。
ARCHIVE_WITH_REASON 6 张不写素材卡，只在 INDEX 末尾的备注区登记。
"""
from pathlib import Path
import json, re, datetime

base = Path('/root/workspace/科武纪元')
bridge_dir = Path('/workspace/任务运行态/20260624_sensenova_2rounds_to_codex_selfcycle/output/sensenova_bridge_manual_20260624_1845/bridge_runs/cron_20260624_1845')
tasks_path = bridge_dir/'card_conversion_tasks.json'
decisions_path = bridge_dir/'decision_cards.json'

tasks = json.loads(tasks_path.read_text(encoding='utf-8'))
decisions = {d['material_id']: d for d in json.loads(decisions_path.read_text(encoding='utf-8'))}

# 本轮 6 张正式卡定义（基于 decision_cards.json 全量提取）
formal_specs = [
    {
        'material_id': '20260624_f0f5434c51',
        'title': '雄安新区：人工智能产业聚力跃升',
        'source_url': 'https://news.cctv.com/2026/06/24/ARTIobtdw6csvfkjOOGfWJLM260624.shtml',
        'source_card_path': '/root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260624_1845/cards/雄安新区_人工智能产业聚力跃升_4aaf41df.md',
        'target_chapter': 125,
        'category': 'AI产业/制度工程/区域科创',
        'mapping': '第125章准备：国家级AI产业集聚区、国产算力中枢（云/边/超/智算融合）、数据大模型"极数"8场景应用；只作制度语境准备，不直接升为OUTLINE_PATCH。',
        'slug': '素材卡_雄安新区_人工智能产业聚力跃升_20260624.md',
        'status': 'CHAPTER_PREP_ONLY',
    },
    {
        'material_id': '20260624_d977200ade',
        'title': '关于2025年人工智能应用典型案例入选名单的公示',
        'source_url': 'https://www.miit.gov.cn/jgsj/kjs/gzdt/art/2026/art_2bf762c3d3be4f5593e80e3e3abd95f9.html',
        'source_card_path': '/root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260624_1845/cards/关于2025年人工智能应用典型案例入选名单的公示_1200a361.md',
        'target_chapter': 95,
        'category': '算法主权/AI治理/制度工程',
        'mapping': '第95章备注层：工信部2025年AI应用典型案例公示（依据工信厅办函〔2025〕476号；公示期2026-06-25至07-01）；与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。',
        'slug': '素材卡_工信部2025年AI应用典型案例公示_20260624.md',
        'status': 'OUTLINE_PATCH',
    },
    {
        'material_id': '20260624_0d2d0a4c9b',
        'title': '工业和信息化部办公厅关于公布2025年度工业和信息化质量提升与品牌建设典型案例名单的通知',
        'source_url': 'https://www.miit.gov.cn/jgsj/kjs/gzdt/art/2026/art_bc6fa4304a0040ccb1446e68ec8eec48.html',
        'source_card_path': '/root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260624_1845/cards/工业和信息化部办公厅关于公布2025年度工业和信息化质量提升与品牌建设典型案例名单的通知_0a7e8c7a.md',
        'target_chapter': 95,
        'category': '产业制度/质量工程/品牌建设',
        'mapping': '第95章备注层：工信部工信厅科函〔2026〕262号公布90项2025年度工业和信息化质量提升与品牌建设典型案例；与产业制度、供应链韧性主线相关，交G2裁决是否写入备注层。',
        'slug': '素材卡_工信部2025质量提升品牌建设典型案例_20260624.md',
        'status': 'OUTLINE_PATCH',
    },
    {
        'material_id': '20260624_83cca36cf3',
        'title': 'Critique of Agent Model',
        'source_url': 'https://arxiv.org/abs/2606.23991',
        'source_card_path': '/root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260624_1845/cards/Critique_of_Agent_Model_ea94375e.md',
        'target_chapter': 95,
        'category': 'AI理论/Agent架构/算法主权',
        'mapping': '第95章备注层：Eric Xing等提出 Goal-Identity-Configurator (GIC) 通用Agent架构，主张真正agency需五维（目标/身份/决策/自调节/学习）内化于系统本身；agentic（外脚手架）vs agentive（内生）边界即"自动化终点"。',
        'slug': '素材卡_Critique_of_Agent_Model_GIC_20260624.md',
        'status': 'OUTLINE_PATCH',
    },
    {
        'material_id': '20260624_e1418de719',
        'title': 'Reinforcement Learning Towards Broadly and Persistently Beneficial Models',
        'source_url': 'https://arxiv.org/abs/2606.24014',
        'source_card_path': '/root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260624_1845/cards/Reinforcement_Learning_Towards_Broadly_and_Persist_2920c71a.md',
        'target_chapter': 95,
        'category': 'AI对齐/RL训练/泛化与持久性',
        'mapping': '第95章备注层：Google DeepMind等在50+独立对齐基准上验证，RL有益行为训练可使超80% OOD基准提升，单一域（健康）RL干预可向非健康域传递对齐改进；增强对抗性提示与有害微调抵抗力。',
        'slug': '素材卡_RL_Broadly_Persistently_Beneficial_20260624.md',
        'status': 'OUTLINE_PATCH',
    },
    {
        'material_id': '20260624_1f472da37a',
        'title': 'emerging resilience in the semiconductor supply chain',
        'source_url': 'https://www.semiconductors.org/emerging-resilience-in-the-semiconductor-supply-chain',
        'source_card_path': '/root/workspace/科武纪元/学习记录/SenseNova分段任务化/cron_20260624_1845/cards/emerging_resilience_in_the_semiconductor_supply_ch_78314b92.md',
        'target_chapter': 95,
        'category': '半导体供应链/产业韧性/制度',
        'mapping': '第95章备注层：美国半导体行业协会(SIA)发声，半导体供应链"emerging resilience"（浮现的韧性）；主控背景信息，非剧情事实。',
        'slug': '素材卡_SIA_emerging_resilience_semiconductor_supply_chain_20260624.md',
        'status': 'OUTLINE_PATCH',
    },
]

# 6 张 ARCHIVE_WITH_REASON 仅登记
archive_specs = [
    {'material_id': '20260624_f25a08e71b', 'title': 'Playing the Moon Game',
     'reason': 'TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY'},
    {'material_id': '20260624_a24bb4ced1', 'title': 'CSDA Selects Eight Commercial Satellite Data Providers for On-Ramp 2 Contract Awards',
     'reason': 'TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY'},
    {'material_id': '20260624_8160e14528', 'title': '俄罗斯核聚变专家中国行活动成功举办',
     'reason': 'SOURCE_URL_ALREADY_IN_INDEX_OR_CARD'},
    {'material_id': '20260624_f2bac76615', 'title': 'RIFT-Bench: Dynamic Red-teaming For Agentic AI Systems',
     'reason': 'TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY'},
    {'material_id': '20260624_497225b562', 'title': "Statement on the US government directive to suspend access to Fable 5 and Mythos 5",
     'reason': 'TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY'},
    {'material_id': '20260624_9c769cb199', 'title': 'Product Jun 23, 2026 Introducing Claude Tag',
     'reason': 'TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY'},
]

out_dir = base/'时事素材/素材卡/2026-06-24'
raw_dir = base/'时事素材/原文备份/2026-06-24'
out_dir.mkdir(parents=True, exist_ok=True)
raw_dir.mkdir(parents=True, exist_ok=True)

index_path = base/'时事素材/INDEX.md'

blocked = []
written = []
index_lines = []

existing_index = index_path.read_text(encoding='utf-8', errors='ignore') if index_path.exists() else ''

for spec in formal_specs:
    material_id = spec['material_id']
    title = spec['title']
    source_card = Path(spec['source_card_path'])
    if not source_card.exists():
        blocked.append({'title': title, 'reason': 'SOURCE_CARD_MISSING', 'source_card_path': str(source_card)})
        continue
    text = source_card.read_text(encoding='utf-8', errors='ignore')
    body_match = re.search(r'## Body Extract\n\n(.*?)(?:\n## AI Distill|\Z)', text, flags=re.S)
    body = (body_match.group(1).strip() if body_match else '')
    if len(body) < 100:
        blocked.append({'title': title, 'reason': 'BODY_TOO_SHORT_AFTER_REVIEW',
                        'source_card_path': str(source_card), 'body_len': len(body)})
        continue
    raw_name = spec['slug'].replace('素材卡_', '原文_')
    raw_path = raw_dir/raw_name
    raw_path.write_text(
        f"# 原文备份：{title}\n\n来源：{spec['source_url']}\n抓取日期：2026-06-24\n源卡：{source_card}\n\n## 正文\n\n{body}\n",
        encoding='utf-8'
    )
    d = decisions.get(material_id, {})
    reason = d.get('disposition_reason', '')
    out_path = out_dir/spec['slug']
    card = f"""# 素材卡：{title}

日期：2026-06-24
来源：{spec['source_url']}
类型：{spec['category']}
可信度：primary_official
状态：{spec['status']}
MiroFish material_id：{material_id}
源卡：{source_card}
原文备份：{raw_path}

## 一句话
{reason or spec['mapping']}

## 关键事实
"""
    facts = []
    for line in text.splitlines():
        s = line.strip('- ').strip()
        if not s or s.startswith('#') or s.startswith('source:') or len(s) < 12:
            continue
        if any(k in s for k in ['2026', 'arxiv', 'arXiv', 'GIC', 'agentive', 'RL', '工信部', '工信厅', '雄安',
                                  '公里', '英里', '倍', '亿元', '万', '%', 'SIA', 'semiconductor', 'OECD',
                                  'ai', 'AI', '人工智能', '清华', '高校', '调度', '网', '可修正', '对齐', '韧性']):
            facts.append(s[:140])
        if len(facts) >= 6:
            break
    if not facts:
        facts = [reason or spec['mapping']]
    for f in facts[:6]:
        card += f"- {f}\n"
    card += f"""
## 可用细节
- 来源已抓正文，非 query_plan 骨架。
- MiroFish 裁决：{d.get('disposition', spec['status'])}。
- 适配章节：第{spec['target_chapter']}章{'准备包' if spec['status'] == 'CHAPTER_PREP_ONLY' else '备注层/交G2裁决'}；不直接改大纲。

## 小说映射
- 可映射章节/卷：第{spec['target_chapter']}章{'准备包' if spec['status'] == 'CHAPTER_PREP_ONLY' else '备注层'}
- 对应变量：{spec['category']}
- 使用建议：{spec['mapping']}

## 反模式/禁忌
- 不把素材写成万能外挂。
- 不直接改大纲、正文、TXT或草稿箱。
- 不把 query_plan、频道页、导航文本当正文证据。
- {spec['status']}素材不直接驱动大纲变更；'OUTLINE_PATCH'交G2六角色裁决。

## MiroFish 裁决
- disposition：{d.get('disposition', '')}
- reason：{reason}
- decision_cards：{decisions_path}
"""
    out_path.write_text(card, encoding='utf-8')
    rel = out_path.relative_to(base)
    raw_rel = raw_path.relative_to(base)
    index_line = f"| 2026-06-24 | {title} | {spec['category']} | `{raw_rel}` | `{rel}` | {spec['mapping']} |"
    if str(rel) not in existing_index:
        index_lines.append(index_line)
    written.append({'material_id': material_id, 'title': title, 'card': str(out_path),
                    'raw': str(raw_path), 'category': spec['category'],
                    'mapping': spec['mapping'], 'status': spec['status']})

# 6 张 ARCHIVE 备注行（不入素材卡目录，只在 INDEX 备注区登记）
archive_lines = []
for a in archive_specs:
    d = decisions.get(a['material_id'], {})
    archive_lines.append(
        f"| 2026-06-24 | {a['title']} | — | — | — | 归档备查（不进入G2/G3）：{a['reason']} |"
    )

if index_lines or archive_lines:
    sections = ""
    if index_lines:
        sections += "\n## MiroFish Bridge 转正式素材卡 2026-06-24\n\n| 日期 | 主题 | 领域 | 原文 | 素材卡 | 可用方向 |\n|---|---|---|---|---|---|\n"
        sections += "\n".join(index_lines) + "\n"
    if archive_lines:
        sections += "\n## MiroFish Bridge 归档备查 2026-06-24（不入素材卡目录）\n\n"
        sections += "| 日期 | 主题 | 领域 | 原文 | 素材卡 | 备注 |\n|---|---|---|---|---|---|\n"
        sections += "\n".join(archive_lines) + "\n"
    index_path.write_text(existing_index.rstrip() + sections, encoding='utf-8')

report = {
    'status': 'DONE_WITH_ARCHIVE_NOTES' if archive_lines else 'DONE',
    'source_bridge': str(bridge_dir),
    'formal_spec_count': len(formal_specs),
    'archive_spec_count': len(archive_specs),
    'written_count': len(written),
    'written': written,
    'blocked_count': len(blocked),
    'blocked': blocked,
    'archive_notes_written': len(archive_lines),
    'archive_specs': archive_specs,
    'index_updated': bool(index_lines or archive_lines),
    'index_section': 'MiroFish Bridge 转正式素材卡 2026-06-24' if index_lines else None,
    'archive_section': 'MiroFish Bridge 归档备查 2026-06-24（不入素材卡目录）' if archive_lines else None,
    'boundary': '只做正式素材卡入库 + INDEX 备注；未改大纲、正文、TXT、草稿箱、Wiki。',
    'executed_at': datetime.datetime.now().isoformat(timespec='seconds'),
}
print(json.dumps(report, ensure_ascii=False, indent=2))
