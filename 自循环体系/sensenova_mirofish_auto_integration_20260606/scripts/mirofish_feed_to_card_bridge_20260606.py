#!/usr/bin/env python3
"""
SenseNova -> MiroFish feed-to-card bridge (2026-06-06)

Read-only bridge for current SenseNova split runner outputs.
It does NOT modify production runner/cron, outline, chapter text, TXT, Fanqie drafts,
time-material INDEX, KB INDEX, or RAG. It only writes a feed package, decision cards,
and deterministic conversion task list under the chosen output directory.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

PROJECT = Path('/root/workspace/科武纪元')
RUNS_BASE = PROJECT / '学习记录' / 'SenseNova分段任务化'
DEFAULT_OUT = PROJECT / '自循环体系' / 'sensenova_mirofish_auto_integration_20260606'
TS_INDEX = PROJECT / '时事素材' / 'INDEX.md'
KB_INDEX = PROJECT / '知识库' / 'INDEX.md'
RAG_JSONL = PROJECT / 'rag_kb' / 'science' / 'cards' / 'science_cards.jsonl'
CARD_DIRS = [PROJECT / '时事素材' / '素材卡', PROJECT / '知识库']
VALID_DISPOSITIONS = ('OUTLINE_PATCH', 'CHAPTER_PREP_ONLY', 'ARCHIVE_WITH_REASON')


def now() -> str:
    return dt.datetime.now().isoformat(timespec='seconds')


def sha(s: str, n: int = 12) -> str:
    return hashlib.sha1((s or '').encode('utf-8')).hexdigest()[:n]


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def read_text(path: Path, limit: int | None = None) -> str:
    try:
        txt = path.read_text(encoding='utf-8', errors='ignore')
        return txt[:limit] if limit else txt
    except Exception:
        return ''


def latest_run_dir() -> Path:
    dirs = [p for p in RUNS_BASE.iterdir() if p.is_dir() and (p / 'pipeline_state.json').exists()]
    if not dirs:
        raise SystemExit(f'no SenseNova run_dir with pipeline_state under {RUNS_BASE}')
    return sorted(dirs, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def load_dedupe_text() -> str:
    chunks = [read_text(TS_INDEX), read_text(KB_INDEX), read_text(RAG_JSONL)]
    # Keep small sample from card tree. Full scan avoided for speed and read-only audit.
    for root in CARD_DIRS:
        if root.exists():
            for p in sorted(root.rglob('*.md'), key=lambda x: x.stat().st_mtime, reverse=True)[:200]:
                chunks.append(read_text(p, 4000))
    return '\n'.join(chunks).lower()


def normalize_title(t: str) -> str:
    t = re.sub(r'&#8217;|&rsquo;', '’', t or '')
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def title_tokens(title: str) -> list[str]:
    title = normalize_title(title).lower()
    toks = re.findall(r'[a-zA-Z0-9]{4,}|[\u4e00-\u9fff]{2,}', title)
    stop = {'https', 'www', 'com', 'news', 'tech', 'nasa', 'from', 'with', 'that', 'this', 'first'}
    return [t for t in toks if t not in stop][:10]


def is_index_like_url(url: str) -> bool:
    if not url:
        return False
    u = url.lower().rstrip('/').split('?', 1)[0].split('#', 1)[0]
    if re.search(r'/(index|channel|list|catalog|category)(\.html|\.htm|\.shtml|\.php|\.jsp|\.asp)?$', u):
        return True
    last = u.rsplit('/', 1)[-1]
    if last in ('tech', 'news', 'finance', 'sports', 'ent', 'military', 'world', 'domestic', 'science', 'culture', 'health', 'edu', 'auto', 'game', 'digital', 'space', 'mil', 'channel'):
        return True
    return False


def is_malformed_search_title(title: str) -> bool:
    if not title:
        return True
    if any(c in title for c in ('›', '»', '‹', '«')):
        return True
    low = title.lower()
    if 'http' in low and re.search(r'[a-z0-9]+\.(com|cn|net|org)https?://', low):
        return True
    if len(title.strip()) < 4:
        return True
    return False


def is_short_navigation_body(body: str) -> bool:
    if not body:
        return True
    if len(body) >= 300:
        return False
    low = body.lower()
    nav = ('首页', '频道', '栏目', '专题', '视频', '图片', '更多', '导航', 'news', 'tech', 'sports', 'finance', 'military', 'world', 'domestic', 'ent', 'space')
    hits = sum(1 for k in nav if k in low)
    return hits >= 4


def material_years(title: str, url: str, body: str) -> list[int]:
    blob = ' '.join([title or '', url or '', (body or '')[:2500]])
    years = [int(y) for y in re.findall(r'(?<!\d)(20\d{2})(?!\d)', blob)]
    return sorted(set(years), reverse=True)


def is_stale_material(title: str, url: str, body: str, max_age_years: int = 1) -> bool:
    years = material_years(title, url, body)
    if not years:
        return False
    return max(years) < dt.datetime.now().year - max_age_years


def is_duplicate(item: dict[str, Any], dedupe_text: str) -> tuple[bool, str]:
    url = (item.get('url') or item.get('source_url') or '').strip().lower()
    title = normalize_title(item.get('title', ''))
    if url and url in dedupe_text:
        return True, 'SOURCE_URL_ALREADY_IN_INDEX_OR_CARD'
    toks = title_tokens(title)
    if len(toks) >= 3 and sum(1 for t in toks if t in dedupe_text) >= min(4, len(toks)):
        return True, 'TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY'
    return False, ''


def classify_material(title: str, summary: str, body: str, source_group: str) -> tuple[str, int, str, str]:
    text = f'{title}\n{summary}\n{body[:2000]}'.lower()
    cn = f'{title}\n{summary}\n{body[:2000]}'
    # target chapter is only a hint for prep/G2, not an outline write.
    if any(k in text for k in ['artemis', 'moon', 'lunar', 'mars', 'space communications', 'antenna', 'satellite']) or any(k in cn for k in ['月球', '航天', '卫星', '火箭', '深空', '载人航天']):
        return 'CHAPTER_PREP_ONLY', 156, '地月/深空/通信链路素材，宜入章节准备红线，不直接改大纲。', 'space_chain'
    if any(k in text for k in ['supersonic', 'x-59', 'aircraft', 'hypersonic']) or any(k in cn for k in ['超音速', '飞行器', '航空']):
        return 'CHAPTER_PREP_ONLY', 217, '高机动平台与感知/噪声治理可作军事制度细节层。', 'military_platform'
    if any(k in text for k in ['genome', 'embryo', 'biotech', 'human embryos', 'antibiotic resistance']) or any(k in cn for k in ['基因', '胚胎', '生物', '抗生素', '耐药']):
        return 'CHAPTER_PREP_ONLY', 359, '生物伦理/人才争夺/科研治理素材，可作后续章节准备。', 'bio_governance'
    policy_concept_hit = any(k in cn for k in ['新质生产力', '高质量发展', '产业革命大趋势'])
    compute_hit = bool(re.search(r'\b(ai|robot|semiconductor|computing|chip|quantum)\b', text)) or any(k in cn for k in ['人工智能', '机器人', '半导体', '算力', '芯片', '量子'])
    if compute_hit and not policy_concept_hit:
        return 'OUTLINE_PATCH', 95, '与算法/算力/技术主权主线直接相关，交G2裁决是否写入备注层。', 'compute_sovereignty'
    if policy_concept_hit:
        return 'CHAPTER_PREP_ONLY', 125, '政策框架/概念文只作制度语境准备，不直接升为OUTLINE_PATCH。', 'domestic_policy_context'
    if source_group == 'domestic' and any(k in cn for k in ['央视', '新华社', '工信部', '国防部', '国家航天局', '中科院']):
        return 'CHAPTER_PREP_ONLY', 125, '国内权威短讯可作上传线现实细节，但须先人工复核正文核。', 'domestic_official_brief'
    return 'ARCHIVE_WITH_REASON', 0, '与当前算力主权、地月争夺、群体智能或军事制度主线因果链不足。', 'low_kewu_relevance'


def make_projection(item: dict[str, Any], body: str, disposition: str, chapter: int, reason: str, axis: str) -> dict[str, Any]:
    title = normalize_title(item.get('title', ''))
    force_reactions = [
        {'force': '联邦/白盾体系', 'reaction': f'把「{title[:32]}」作为技术或制度压力测试变量，而非剧情事实照搬。', 'wiki_ref': 'wiki/factions'},
        {'force': '主角团/工程线', 'reaction': '只吸收可测反馈、失败模式、成本约束；不写成万能外挂。', 'wiki_ref': 'wiki/characters'},
    ]
    if disposition == 'ARCHIVE_WITH_REASON':
        force_reactions = [{'force': '主控', 'reaction': '归档备查；不进入G2/G3。', 'wiki_ref': '时事素材/归档'}]
    return {
        'force_reactions': force_reactions,
        'chain_conflicts': [
            {'chain': [axis, 'authority_filter', 'kewu_relevance'], 'time_anchor': 'latest_sensenova_run', 'intensity': 'medium' if disposition != 'ARCHIVE_WITH_REASON' else 'low'}
        ],
        'chapter_hooks': ([] if chapter <= 0 else [{
            'hook_id': f'ch{chapter}_{sha(title, 8)}',
            'description': f'{reason} 来源题名：{title}',
            'suitable_chapters': [chapter],
            'reversal': '仅作细节/变量，不直接改变既有章节功能。'
        }]),
        'outline_delta_candidate': {
            'type': 'note_layer' if disposition == 'OUTLINE_PATCH' else 'red_line',
            'target_chapter': chapter if chapter > 0 else 0,
            'proposed_addition': reason if disposition == 'OUTLINE_PATCH' else '',
            'not_proposed': '' if disposition == 'OUTLINE_PATCH' else reason,
        },
        'anti_patterns': ['不得把query_plan当有效素材', '不得无URL/无正文伪造素材卡', '不得直接改大纲/正文/TXT/草稿箱'],
        'six_role_recommendation': {'needed': disposition == 'OUTLINE_PATCH', 'reason': 'OUTLINE_PATCH必须交G2/六角色裁决；CHAPTER_PREP_ONLY只进准备包。'}
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-dir', default='', help='SenseNova run dir; default latest')
    ap.add_argument('--out-dir', default=str(DEFAULT_OUT))
    ap.add_argument('--dry-run', action='store_true', help='write bridge artifacts only; never write formal cards/index/RAG')
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()

    run_dir = Path(args.run_dir) if args.run_dir else latest_run_dir()
    out_dir = Path(args.out_dir)
    bridge_dir = out_dir / 'bridge_run'
    bridge_dir.mkdir(parents=True, exist_ok=True)

    state = load_json(run_dir / 'pipeline_state.json', {}) or {}
    plan = load_json(run_dir / 'cards' / 'card_distill_plan.json', {}) or {}
    items = plan.get('items', []) if isinstance(plan, dict) else []
    if args.limit > 0:
        items = items[:args.limit]
    dedupe_text = load_dedupe_text()

    valid_items = []
    skipped = []
    seen_input_keys: set[str] = set()
    for it in items:
        key = (it.get('url') or it.get('candidate_id') or it.get('title') or '').strip().lower()
        if key in seen_input_keys:
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': it.get('url'), 'status': it.get('status'), 'reason': 'duplicate_within_run'})
            continue
        seen_input_keys.add(key)
        status = it.get('status')
        if status != 'DISTILLED':
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': it.get('url'), 'status': status, 'reason': it.get('reason') or 'not_distilled'})
            continue
        if not it.get('url') or it.get('card_type') == 'query_plan':
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': it.get('url'), 'status': status, 'reason': 'no_url_or_query_plan'})
            continue
        url = it.get('url', '')
        if is_index_like_url(url):
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': url, 'status': status, 'reason': 'index_or_channel_url'})
            continue
        title = it.get('title', '')
        if is_malformed_search_title(title):
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': title, 'url': url, 'status': status, 'reason': 'malformed_search_title'})
            continue
        card_path = Path(it.get('card', ''))
        if not card_path.exists():
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': url, 'status': status, 'reason': 'card_file_missing'})
            continue
        card_preview = read_text(card_path, 4000)
        if is_short_navigation_body(card_preview):
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': url, 'status': status, 'reason': 'short_navigation_body'})
            continue
        if it.get('source_group') == 'domestic' and is_stale_material(title, url, card_preview):
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': url, 'status': status, 'reason': 'stale_domestic_article'})
            continue
        valid_items.append(it)

    decision_cards = []
    conversion_tasks = []
    counts = {k: 0 for k in VALID_DISPOSITIONS}
    for it in valid_items:
        card_path = Path(it['card'])
        card_text = read_text(card_path, 6000)
        dup, dup_reason = is_duplicate(it, dedupe_text)
        disp, chapter, reason, axis = classify_material(it.get('title',''), '', card_text, it.get('source_group',''))
        if dup:
            disp, chapter, reason = 'ARCHIVE_WITH_REASON', 0, f'重复或已入库：{dup_reason}'
        counts[disp] += 1
        material_id = f"{dt.datetime.now().strftime('%Y%m%d')}_{sha(it.get('candidate_id') or it.get('url') or it.get('title'), 10)}"
        evidence_complete = bool(it.get('url')) and card_path.exists() and not dup
        dc = {
            '$schema': 'decision_card_v1_bridge_20260606',
            'material_id': material_id,
            'source_url': it.get('url',''),
            'title': normalize_title(it.get('title','')),
            'captured_at': now(),
            'source_group': it.get('source_group'),
            'source_type': it.get('source_type'),
            'verification_status': it.get('verification_status'),
            'source_card_path': str(card_path),
            'evidence_complete': evidence_complete,
            'duplicate_check': {'duplicate': dup, 'reason': dup_reason},
            'mirofish_projection': make_projection(it, card_text, disp, chapter, reason, axis),
            'disposition': disp,
            'disposition_reason': reason,
            'disposition_by': 'deterministic_bridge_20260606',
            'disposition_at': now(),
            'bridge_policy': 'dry_run_no_formal_card_no_index_no_rag_write' if args.dry_run else 'bridge_artifacts_only_no_production_write',
        }
        decision_cards.append(dc)
        if disp == 'CHAPTER_PREP_ONLY' and evidence_complete:
            conversion_tasks.append({
                'task': 'FORMAL_CARD_CANDIDATE_AFTER_HUMAN_OR_CONTROLLER_REVIEW',
                'material_id': material_id,
                'title': dc['title'],
                'source_url': dc['source_url'],
                'source_card_path': dc['source_card_path'],
                'target_chapter_hint': chapter,
                'required_checks_before_write': ['read_source_card', 'verify_body_evidence', 'dedupe_TS_INDEX_KB_INDEX_RAG', 'write_formal_card', 'append_TS_INDEX', 'copy_or_link_KB_INDEX', 'append_RAG_jsonl'],
                'not_done_in_dry_run': True,
            })

    feed_package = {
        'schema': 'sensenova_mirofish_feed_package_v1',
        'created_at': now(),
        'source_run_dir': str(run_dir),
        'source_pipeline_state': {
            'run_id': state.get('run_id'),
            'status': state.get('status'),
            'valid_content_cards': state.get('valid_content_cards'),
            'query_plan_cards': state.get('query_plan_cards'),
            'body_fetch_success': state.get('body_fetch_success'),
            'card_pass_count': state.get('card_pass_count'),
        },
        'policy': {
            'query_plan_excluded': True,
            'formal_cards_written': False,
            'production_runner_modified': False,
            'outline_text_txt_draft_modified': False,
        },
        'valid_input_count': len(valid_items),
        'skipped_count': len(skipped),
        'skipped': skipped,
        'decision_cards_path': str(bridge_dir / 'decision_cards.json'),
        'conversion_tasks_path': str(bridge_dir / 'card_conversion_tasks.json'),
    }

    (bridge_dir / 'mirofish_feed_package.json').write_text(json.dumps(feed_package, ensure_ascii=False, indent=2), encoding='utf-8')
    (bridge_dir / 'decision_cards.json').write_text(json.dumps(decision_cards, ensure_ascii=False, indent=2), encoding='utf-8')
    (bridge_dir / 'card_conversion_tasks.json').write_text(json.dumps(conversion_tasks, ensure_ascii=False, indent=2), encoding='utf-8')

    lines = [
        '# MiroFish feed-to-card bridge dry-run report', '',
        f'- created_at: {now()}',
        f'- source_run_dir: {run_dir}',
        f'- dry_run: {args.dry_run}',
        f'- production_runner_modified: NO',
        f'- formal_cards_written: NO',
        f'- outline_text_txt_draft_modified: NO',
        f'- valid_input_count: {len(valid_items)}',
        f'- skipped_count: {len(skipped)}',
        f'- disposition_counts: {json.dumps(counts, ensure_ascii=False)}',
        f'- conversion_task_count: {len(conversion_tasks)}', '',
        '## Outputs', '',
        f'- {bridge_dir / "mirofish_feed_package.json"}',
        f'- {bridge_dir / "decision_cards.json"}',
        f'- {bridge_dir / "card_conversion_tasks.json"}', '',
        '## Disposition table', '',
        '| disposition | material_id | title | reason |',
        '|---|---|---|---|',
    ]
    for dc in decision_cards:
        lines.append(f"| {dc['disposition']} | {dc['material_id']} | {dc['title'][:80]} | {dc['disposition_reason'][:120]} |")
    lines += ['', '## Skipped', '', '| title | source status | reason |', '|---|---|---|']
    for s in skipped[:80]:
        lines.append(f"| {str(s.get('title',''))[:80]} | {s.get('status','')} | {s.get('reason','')} |")
    report = '\n'.join(lines) + '\n'
    (bridge_dir / 'dry_run_report.generated.md').write_text(report, encoding='utf-8')
    # Root required file copy; safe independent artifact.
    (out_dir / 'DRY_RUN_REPORT.md').write_text(report, encoding='utf-8')
    print(json.dumps({'status': 'DRY_RUN_DONE' if args.dry_run else 'BRIDGE_DONE', 'run_dir': str(run_dir), 'out_dir': str(out_dir), 'valid_input_count': len(valid_items), 'skipped_count': len(skipped), 'disposition_counts': counts, 'conversion_task_count': len(conversion_tasks), 'report': str(out_dir / 'DRY_RUN_REPORT.md')}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
