#!/usr/bin/env python3
"""
SenseNova -> MiroFish feed-to-card bridge (2026-06-06)

Read-only bridge for current SenseNova split runner outputs.
It does NOT modify production runner/cron, outline, chapter text, TXT, Fanqie drafts,
time-material INDEX, KB INDEX, or Wiki. It only writes a feed package, decision cards,
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
WIKI_ROOT = PROJECT / 'wiki'
CARD_DIRS = [PROJECT / '时事素材' / '素材卡', PROJECT / '知识库']
VALID_DISPOSITIONS = ('OUTLINE_PATCH', 'CHAPTER_PREP_ONLY', 'ARCHIVE_WITH_REASON')
CROSS_RUN_DEDUPE_FILE = DEFAULT_OUT / 'bridge_run' / 'processed_signatures.json'

STORY_VALUE_KEYWORDS = (
    '算力', '芯片', '半导体', '算法主权', '军事', '太空', '卫星', '人工智能',
    'ai', 'compute', 'computing', 'chip', 'semiconductor', 'military', 'space', 'satellite',
)

MEETING_RELEASE_MARKERS = (
    '出席会议并讲话', '主持会议', '通报', '交流发言', '指出', '强调',
    '工作推进会', '座谈会', '部署会', '动员会', '电视电话会议',
    '全体会议', '工作会议', '协调会', '专题会议',
)

TECH_DATA_RE = re.compile(
    r'\d+(?:\.\d+)?\s*(?:GHz|nm|TFLOPS|TOPS|GB/s|Gbps|Mbps|km|公里|吨|颗|枚|台|套|个|座|芯片|卫星)',
    re.IGNORECASE,
)

# Broader tech-data pattern: engineering constraints, quantitative benchmarks,
# specific product/process names that indicate real technical content vs pure policy vision.
TECH_DATA_BROAD_RE = re.compile(
    r'(?:\d+(?:\.\d+)?\s*(?:GHz|nm|TFLOPS|TOPS|GB/s|Gbps|Mbps|km|公里|吨|颗|枚|台|套|个|座|芯片|卫星|纳米|制程|良率|%)'
    r'|(?:华为|台积电|三星|中芯|ASML|光刻机|EUV|DUV|封装|流片|晶圆|硅片|衬底|外延|掺杂|蚀刻|CVD|PVD)'
    r'|(?:突破|攻克|量产|下线|交付|首台|首颗|首枚|自主研发|国产替代|技术封锁|卡脖子))',
    re.IGNORECASE,
)


def load_cross_run_dedupe(path: Path = CROSS_RUN_DEDUPE_FILE) -> dict[str, set[str]]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        records = data.get('records')
        if isinstance(records, dict):
            return {
                str(sig): set(str(run_id) for run_id in run_ids)
                for sig, run_ids in records.items()
                if isinstance(run_ids, list)
            }
        return {str(sig): {'__legacy__'} for sig in data.get('signatures', [])}
    except Exception:
        return {}


def save_cross_run_dedupe(records: dict[str, set[str]], path: Path = CROSS_RUN_DEDUPE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({
            'signatures': sorted(records),
            'records': {sig: sorted(run_ids) for sig, run_ids in sorted(records.items())},
        }, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


def is_cross_run_processed(sig: str, records: dict[str, set[str]], run_id: str) -> bool:
    run_ids = records.get(sig, set())
    return any(item not in {run_id, '__legacy__'} for item in run_ids)


def now() -> str:
    return dt.datetime.now().isoformat(timespec='seconds')


def sha(s: str, n: int = 12) -> str:
    return hashlib.sha1((s or '').encode('utf-8')).hexdigest()[:n]


def safe_name(s: str) -> str:
    return re.sub(r'[^\w\u4e00-\u9fff\-]+', '_', s or '').strip('_') or 'run'


def normalize_url(url: str) -> str:
    u = (url or '').strip().lower().rstrip('/').split('?', 1)[0].split('#', 1)[0]
    return u


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


def raw_body_files(run_dir: Path) -> list[Path]:
    bodies_dir = run_dir / 'raw' / 'bodies'
    if not bodies_dir.exists():
        return []
    return sorted(p for p in bodies_dir.glob('*.txt') if p.is_file())


def body_path_for_card(card_item: dict[str, Any], run_dir: Path) -> Path | None:
    keys = [
        str(card_item.get('material_id') or '').strip(),
        str(card_item.get('candidate_id') or '').strip(),
    ]
    body_evidence = card_item.get('_bridge_body_fetch_evidence') or card_item.get('body_fetch_evidence')
    if isinstance(body_evidence, dict):
        keys.append(str(body_evidence.get('candidate_id') or '').strip())
        body_path = Path(str(body_evidence.get('body_path') or ''))
        try:
            if body_path.exists() and body_path.resolve().parent == (run_dir / 'raw' / 'bodies').resolve():
                return body_path
        except Exception:
            pass
    for key in keys:
        if not key:
            continue
        path = run_dir / 'raw' / 'bodies' / f'{key}.txt'
        if path.exists():
            return path
    return None


def text_has_story_value_keywords(text: str) -> bool:
    low = (text or '').lower()
    return any(k in low for k in STORY_VALUE_KEYWORDS)


def is_meeting_release_without_tech_data(body: str) -> bool:
    """Detect meeting/press-release style content with no real engineering data.

    Returns True only when the text has meeting-style markers AND lacks both
    narrow tech data (GHz/nm/etc) AND broad engineering references (company names,
    process terms, breakthrough claims with numbers).
    """
    if not body:
        return False
    has_meeting_markers = any(k in body for k in MEETING_RELEASE_MARKERS)
    if not has_meeting_markers:
        return False
    has_narrow_tech = bool(TECH_DATA_RE.search(body))
    has_broad_tech = bool(TECH_DATA_BROAD_RE.search(body))
    # If it has any real tech data (narrow or broad), don't demote
    return not has_narrow_tech and not has_broad_tech


def missing_cards_by_tier(run_dir: Path, decision_cards: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, list[str]]:
    """Return high-tier distilled items that should have a bridge decision but do not.

    This gate must not scan every raw/bodies/*.txt file.  A run may contain raw
    bodies that were intentionally skipped before bridge decisions (duplicate,
    stale, navigation, summary-only, already indexed).  Treating those raw files
    as missing decision cards creates false P0/P1 blockers and stalls G1→G2.
    Only non-duplicate, valid card_distill_plan items are expected to receive a
    decision card.
    """
    decision_ids = {str(dc.get('material_id') or '').strip() for dc in decision_cards if isinstance(dc, dict)}
    decision_ids |= {
        str((dc.get('body_fetch_evidence') or {}).get('candidate_id') or '').strip()
        for dc in decision_cards
        if isinstance(dc, dict) and isinstance(dc.get('body_fetch_evidence'), dict)
    }
    decision_ids = {item for item in decision_ids if item}
    plan = load_json(run_dir / 'cards' / 'card_distill_plan.json', {}) or {}
    plan_items = plan.get('items') if isinstance(plan, dict) else []
    expected_ids_by_tier: dict[str, list[str]] = {}
    for item in plan_items or []:
        if not isinstance(item, dict):
            continue
        status = str(item.get('status') or '').upper()
        if status in {'SKIP_DUPLICATE', 'SUMMARY_ONLY', 'NEED_FETCH_BODY', 'BODY_FETCH_FAIL', 'CARD_REVIEW_FAIL'}:
            continue
        if item.get('counts_as_valid_content_card') is not True:
            continue
        card_path = Path(str(item.get('card') or ''))
        body_path = Path(str(item.get('body_path') or ''))
        if not card_path.exists() or not body_path.exists():
            continue
        # Cross-run duplicate / already-indexed items may be intentionally
        # archived or skipped.  If their source URL is already in indexes, they
        # must not block a clean bridge pass.
        dup, _dup_reason = is_duplicate(item, load_dedupe_text())
        if dup:
            continue
        story_value = item.get('story_value_classification') if isinstance(item.get('story_value_classification'), dict) else {}
        tier = str(item.get('story_tier') or item.get('tier') or story_value.get('story_tier') or '').upper()
        if tier not in {'P0', 'P1'}:
            continue
        key = str(item.get('candidate_id') or item.get('material_id') or item.get('id') or '').strip()
        if key:
            expected_ids_by_tier.setdefault(tier, []).append(key)
    missing: dict[str, list[str]] = {}
    for tier, ids in expected_ids_by_tier.items():
        for key in ids:
            if not any(decision_id and decision_id in key or key in decision_id for decision_id in decision_ids):
                missing.setdefault(tier, []).append(key)
    return {tier: sorted(set(ids)) for tier, ids in sorted(missing.items()) if ids}


def latest_run_dir() -> Path:
    dirs = [p for p in RUNS_BASE.iterdir() if p.is_dir() and (p / 'pipeline_state.json').exists()]
    if not dirs:
        raise SystemExit(f'no SenseNova run_dir with pipeline_state under {RUNS_BASE}')
    candidates: list[Path] = []
    for p in dirs:
        state = load_json(p / 'pipeline_state.json', {}) or {}
        if is_verify_run(p):
            continue
        if int(state.get('valid_content_cards') or 0) <= 0:
            continue
        candidates.append(p)
    return sorted(candidates or dirs, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def gate_allows_mirofish_input(run_dir: Path) -> tuple[bool, dict[str, Any], int, str]:
    gate_path = run_dir / 'raw' / 'mirofish_input_gate.json'
    gate = load_json(gate_path, {}) or {}
    body_files = [
        p for p in (run_dir / 'raw' / 'bodies').glob('*.txt')
        if p.is_file() and p.stat().st_size > 0
    ]
    status = str(gate.get('status') or '')
    if status != 'ALLOW_MIROFISH_INPUT':
        return False, gate, len(body_files), 'NO_VALID_BODY_FOR_MIROFISH'
    if not body_files:
        return False, gate, len(body_files), 'NO_BODY_FILES_FOR_MIROFISH'
    return True, gate, len(body_files), ''


def gate_allows_expert_input(run_dir: Path) -> tuple[bool, dict[str, Any], str]:
    gate_path = run_dir / 'raw' / 'expert_gate_report.json'
    alt_gate_path = run_dir / 'raw' / 'mirofish_input_gate.json'
    gate = load_json(gate_path, {}) or {}
    if not gate:
        # Fallback: derive from mirofish_input_gate.json (pipeline P3 format)
        alt_gate = load_json(alt_gate_path, {}) or {}
        if alt_gate:
            # Map mirofish_input_gate fields to expert_gate_report fields
            status = str(alt_gate.get('status') or '')
            valid_cards = alt_gate.get('valid_content_cards', 0)
            gate = {
                'status': status,
                'expert_gate_pass': status == 'ALLOW_MIROFISH_INPUT' and int(valid_cards or 0) > 0,
                'valid_content_cards': valid_cards,
                'failure_tags': [] if status == 'ALLOW_MIROFISH_INPUT' else ['EXPERT_GATE_INSUFFICIENT'],
                'reason': alt_gate.get('reason', ''),
                'source': 'derived_from_mirofish_input_gate',
                'expert_gate_report_path': str(gate_path),
                'mirofish_input_gate_path': str(alt_gate_path),
                'required_experts': ['沈逸', '高志凯'],
            }
        else:
            return False, {
                'status': 'BLOCKED',
                'expert_gate_pass': False,
                'failure_tags': ['EXPERT_GATE_INSUFFICIENT'],
                'reason': 'missing raw/expert_gate_report.json and raw/mirofish_input_gate.json',
                'expert_gate_report_path': str(gate_path),
                'mirofish_input_gate_path': str(alt_gate_path),
                'required_experts': ['沈逸', '高志凯'],
            }, 'EXPERT_GATE_INSUFFICIENT'
    if gate.get('expert_gate_pass') is not True:
        tags = gate.get('failure_tags') or ['EXPERT_GATE_INSUFFICIENT']
        return False, gate, str(tags[0] if tags else 'EXPERT_GATE_INSUFFICIENT')
    return True, gate, ''


def expert_voice_cards_from_gate(gate: dict[str, Any]) -> list[dict[str, Any]]:
    fields = gate.get('fields') if isinstance(gate, dict) else {}
    cards = fields.get('expert_voice_cards') if isinstance(fields, dict) else []
    return [item for item in cards if isinstance(item, dict)] if isinstance(cards, list) else []


def source_cards_from_decisions(decision_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for dc in decision_cards:
        if not isinstance(dc, dict):
            continue
        projection = dc.get('mirofish_projection') if isinstance(dc.get('mirofish_projection'), dict) else {}
        cards.append({
            'material_id': dc.get('material_id', ''),
            'title': dc.get('title', ''),
            'url': dc.get('source_url', ''),
            'source_card_path': dc.get('source_card_path', ''),
            'source_group': dc.get('source_group', ''),
            'source_type': dc.get('source_type', ''),
            'verification_status': dc.get('verification_status', ''),
            'body_fetch_evidence': dc.get('body_fetch_evidence', {}),
            'evidence_complete': bool(dc.get('evidence_complete')),
            'disposition': dc.get('disposition', ''),
            'chapter_hint': projection.get('chapter_hint', 0),
            'story_axis': projection.get('story_axis', ''),
        })
    return cards


def fresh_news_cards_from_source_cards(source_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fresh_cards: list[dict[str, Any]] = []
    for card in source_cards:
        if not isinstance(card, dict):
            continue
        fresh_cards.append({
            **card,
            'card_family': 'fresh_news_card',
            'bridge_retained': True,
        })
    return fresh_cards


def load_body_fetch_evidence(run_dir: Path) -> dict[str, dict[str, Any]]:
    report = load_json(run_dir / 'raw' / 'body_fetch_report.json', {}) or {}
    evidence: dict[str, dict[str, Any]] = {}
    bodies_dir = (run_dir / 'raw' / 'bodies').resolve()
    for item in report.get('items', []) if isinstance(report, dict) else []:
        if not isinstance(item, dict):
            continue
        if item.get('status') != 'BODY_FETCHED' or not item.get('counts_as_body_success'):
            continue
        body_path = Path(str(item.get('body_path') or ''))
        try:
            resolved = body_path.resolve()
        except Exception:
            continue
        if (
            body_path.suffix != '.txt'
            or resolved.parent != bodies_dir
            or not resolved.exists()
            or resolved.stat().st_size <= 0
        ):
            continue
        for key in (item.get('candidate_id'), item.get('url')):
            key_s = str(key or '').strip().lower()
            if key_s:
                evidence[key_s] = item
    return evidence


def raw_body_path_from_evidence(item: dict[str, Any] | None, run_dir: Path) -> str:
    if not item:
        return ''
    body_path = Path(str(item.get('body_path') or ''))
    bodies_dir = (run_dir / 'raw' / 'bodies').resolve()
    try:
        resolved = body_path.resolve()
    except Exception:
        return ''
    if body_path.suffix == '.txt' and resolved.parent == bodies_dir and resolved.exists() and resolved.stat().st_size > 0:
        return str(resolved)
    return ''


def body_fetch_item_for(card_item: dict[str, Any], evidence: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    for key in (card_item.get('candidate_id'), card_item.get('url')):
        key_s = str(key or '').strip().lower()
        if key_s and key_s in evidence:
            return evidence[key_s]
    return None


def body_fetch_evidence_item_count(evidence: dict[str, dict[str, Any]]) -> int:
    paths = {
        str(item.get('body_path') or '')
        for item in evidence.values()
        if item.get('body_path')
    }
    return len(paths)


def is_verify_run(run_dir: Path) -> bool:
    name = run_dir.name.lower()
    return name.startswith('verify_') or '_verify_' in name or name.startswith('linkfix_')


def load_dedupe_text() -> str:
    chunks = [read_text(TS_INDEX), read_text(KB_INDEX), read_text(WIKI_ROOT / 'log.md')]
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


MALFORMED_TITLE_EXACT = {
    'article', 'news', 'story', 'post', 'untitled', 'no title',
    '正文', '详情', '无标题', 'content', 'title', 'default',
}
MALFORMED_TITLE_RE = re.compile(
    r'^(?:[cC]?\d{5,}(?:\s+\d+)?|'
    r'\d{5,}(?:\s+\d+)?|'
    r'[a-z]{3,8}\s+\d{4,}|'
    r'\d{4,}\s+[a-z]{3,8})$'
)


def is_malformed_search_title(title: str) -> bool:
    if not title:
        return True
    t = title.strip()
    low = t.lower()
    if low in MALFORMED_TITLE_EXACT:
        return True
    if MALFORMED_TITLE_RE.match(t):
        return True
    # pure numeric or path token like "c64094 40722548"
    if re.search(r'\b[cC]?\d{4,}(?:\s+\d{4,})?\b', t) and len(re.findall(r'[\u4e00-\u9fffA-Za-z]{2,}', t)) == 0:
        return True
    if any(c in title for c in ('›', '»', '‹', '«')):
        return True
    if 'http' in low and re.search(r'[a-z0-9]+\.(com|cn|net|org)https?://', low):
        return True
    if len(t) < 4:
        return True
    return False


def navigation_heavy_stats(body: str) -> dict[str, Any]:
    """Detect pages whose extracted text is dominated by site navigation.

    NASA and news sites often put Explore/Search/News/Missions/Planets menus
    before the article body. If we classify against that raw prefix, navigation
    words like Artemis/Moon/Mars pollute the material axis.
    """
    lines = [ln.strip() for ln in (body or '').splitlines() if ln.strip()]
    if not lines:
        return {'nav_lines': 0, 'total_lines': 0, 'ratio': 1.0, 'heavy': True}
    nav_terms = (
        '首页', '频道', '栏目', '专题', '视频', '图片', '更多', '导航',
        'explore', 'search', 'news', 'events', 'missions', 'humans in space',
        'the solar system', 'the universe', 'science', 'aeronautics', 'technology',
        'downloads', 'follow nasa', 'suggested searches', 'mars perseverance',
        'the moon', 'artemis', 'planets', 'earth', 'space', 'nasa+', 'image of the day',
    )
    nav_lines = 0
    for ln in lines:
        low = ln.lower()
        if len(ln) <= 80 and any(k in low for k in nav_terms):
            nav_lines += 1
    ratio = nav_lines / max(len(lines), 1)
    return {'nav_lines': nav_lines, 'total_lines': len(lines), 'ratio': ratio, 'heavy': ratio >= 0.45 and nav_lines >= 12}


def strip_navigation_text(body: str) -> str:
    """Return article-like text by dropping leading navigation/menu lines."""
    if not body:
        return ''
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return ''
    drop_terms = (
        'explore', 'search', 'news & events', 'missions', 'humans in space',
        'the solar system', 'the universe', 'science', 'aeronautics', 'technology',
        'downloads', 'suggested searches', 'mars perseverance', 'the moon',
        'artemis', 'planets', 'nasa+', 'image of the day', '首页', '频道', '栏目', '导航'
    )
    kept: list[str] = []
    dropping = True
    for ln in lines:
        low = ln.lower()
        is_nav = len(ln) <= 90 and any(k in low for k in drop_terms)
        if dropping and is_nav:
            continue
        dropping = False
        kept.append(ln)
    return '\n'.join(kept) if kept else '\n'.join(lines)


def is_short_navigation_body(body: str) -> bool:
    if not body:
        return True
    low = body.lower()
    nav = ('首页', '频道', '栏目', '专题', '视频', '图片', '更多', '导航', 'news', 'tech', 'sports', 'finance', 'military', 'world', 'domestic', 'ent', 'space')
    if len(body) < 300:
        hits = sum(1 for k in nav if k in low)
        return hits >= 4
    return navigation_heavy_stats(body).get('heavy', False)


def material_years(title: str, url: str, body: str) -> list[int]:
    blob = ' '.join([title or '', url or '', (body or '')[:2500]])
    years = [int(y) for y in re.findall(r'(?<!\d)(20\d{2})(?!\d)', blob)]
    return sorted(set(years), reverse=True)


def published_years(body: str) -> list[int]:
    """Prefer article publish dates over captured_at/future planning years."""
    sample = (body or '')[:2500]
    explicit = [
        r'(?:发布时间|发布日期|发表时间|发稿时间)[:：\s]*(20\d{2})[-年/.]',
        r'(?:发布时间|发布日期|发表时间|发稿时间)[:：\s]*.*?(20\d{2})年',
    ]
    years: list[int] = []
    for pat in explicit:
        years.extend(int(y) for y in re.findall(pat, sample))
    if years:
        return sorted(set(years), reverse=True)
    body_only = sample.split('## Body Extract', 1)[-1]
    years = [int(y) for y in re.findall(r'(?<!captured_at: )(20\d{2})[-年/.]\d{1,2}[-月/.]\d{1,2}日?', body_only)]
    return sorted(set(years), reverse=True)


def is_stale_material(title: str, url: str, body: str, max_age_years: int = 1) -> bool:
    pub_years = published_years(body)
    if pub_years:
        return max(pub_years) < dt.datetime.now().year - max_age_years
    years = material_years(title, url, body)
    if not years:
        return False
    return max(years) < dt.datetime.now().year - max_age_years


def event_signature(item: dict[str, Any]) -> str:
    title = normalize_title(item.get('title', '')).lower()
    url = (item.get('url') or item.get('source_url') or '').strip().lower()
    blob = f'{title}\n{url}'
    # NASA sometimes publishes the same event under image-article and article URLs.
    if ('x-59' in blob or 'x59' in blob or 'supersonic' in blob) and ('nasa.gov' in blob or 'nasa' in blob):
        return 'nasa_x59_first_supersonic_flight'
    return ''


def is_duplicate(item: dict[str, Any], dedupe_text: str) -> tuple[bool, str]:
    url = (item.get('url') or item.get('source_url') or '').strip().lower()
    title = normalize_title(item.get('title', ''))
    if url and url in dedupe_text:
        return True, 'SOURCE_URL_ALREADY_IN_INDEX_OR_CARD'
    sig = event_signature(item)
    if sig == 'nasa_x59_first_supersonic_flight' and ('x-59' in dedupe_text or 'x59' in dedupe_text) and 'supersonic' in dedupe_text:
        return True, 'SAME_EVENT_X59_FIRST_SUPERSONIC_FLIGHT'
    toks = title_tokens(title)
    if len(toks) >= 3 and sum(1 for t in toks if t in dedupe_text) >= min(4, len(toks)):
        return True, 'TITLE_TOKEN_OVERLAP_WITH_EXISTING_LIBRARY'
    return False, ''


def classification_body(body: str) -> str:
    """Prefer distilled/summary text over raw site body for semantic routing."""
    if not body:
        return ''
    parts: list[str] = []
    if '## Summary' in body:
        after = body.split('## Summary', 1)[1]
        summary_part = after.split('## Body Extract', 1)[0]
        parts.append(summary_part)
    if '## AI Distill' in body:
        parts.append(body.split('## AI Distill', 1)[1])
    if parts:
        return '\n'.join(parts)
    return strip_navigation_text(body)


def classify_material(title: str, summary: str, body: str, source_group: str) -> tuple[str, int, str, str]:
    clean_body = classification_body(body)
    text = f'{title}\n{summary}\n{clean_body[:2500]}'.lower()
    cn = f'{title}\n{summary}\n{clean_body[:2500]}'
    # P0: 展会/航展/博览会 — 无论来源都归档，不入 CHAPTER_PREP_ONLY
    expo_hit = any(k in text for k in [
        'ila ', 'ila2026', ' ila ', 'berlin airshow', 'air show', 'airshow',
        'exhibition', 'trade show', 'booth ', 'demonstration', 'aerospace exhibition',
        'defense expo', 'space symposium',
    ])
    if expo_hit:
        return 'ARCHIVE_WITH_REASON', 0, '展会/航展/博览会文，低技术突破增益，归档。', 'expo_event'
    # P0: 纯基础科学（Arrakihs 类暗物质/宇宙学）— 与科武主线因果链不足
    basic_cosmology_hit = any(k in text for k in [
        'arrakihs', 'dark matter', 'cosmic web', 'primordial',
        'early universe', 'galaxy formation', 'gravitational wave',
    ])
    # 但如果同时命中深空通信/月球链，则保留给空间链判断
    space_tech_hit = any(k in text for k in [
        'artemis', 'moon', 'lunar', 'mars', 'space communications',
        'deep space', 'lunar gateway', 'antenna', 'relay', 'satellite',
    ])
    if basic_cosmology_hit and not space_tech_hit:
        return 'ARCHIVE_WITH_REASON', 0, '纯基础天体物理/宇宙学，与科武主线因果链不足。', 'basic_cosmology'
    earth_observation_hit = any(k in text for k in ['earth observation', 'meteorology', 'weather', 'convective', 'storm', 'urban development', 'international space station', 'astronaut photography']) or any(k in cn for k in ['地球观测', '气象', '对流', '风暴', '城市', '国际空间站'])
    deep_space_hit = any(k in text for k in ['artemis', 'moon', 'lunar', 'mars', 'space communications', 'deep space', 'lunar gateway']) or any(k in cn for k in ['月球', '航天', '火箭', '深空', '载人航天'])
    # Generic satellite is too broad: Earth-observation/weather satellites should not become space_chain.
    satellite_only = ('satellite' in text or '卫星' in cn) and not deep_space_hit
    if earth_observation_hit and satellite_only:
        return 'CHAPTER_PREP_ONLY', 156, '气象/地球观测素材，可作章节准备包中的遥感盲区/侦察代价参考；非地月深空链。', 'earth_observation'
    # target chapter is only a hint for prep/G2, not an outline write.
    if deep_space_hit or (('satellite' in text or '卫星' in cn) and any(k in text for k in ['communications', 'antenna', 'relay'])):
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
    ap.add_argument('--dry-run', action='store_true', help='write bridge artifacts only; never write formal cards/index/Wiki')
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()

    run_dir = Path(args.run_dir) if args.run_dir else latest_run_dir()
    out_dir = Path(args.out_dir)
    state = load_json(run_dir / 'pipeline_state.json', {}) or {}
    run_id = str(state.get('run_id') or run_dir.name)
    per_run_dir = out_dir / 'bridge_runs' / safe_name(run_id)
    root_bridge_dir = out_dir / 'bridge_run'
    bridge_dir = per_run_dir
    bridge_dir.mkdir(parents=True, exist_ok=True)

    gate_ok, mirofish_gate, body_file_count, gate_block_reason = gate_allows_mirofish_input(run_dir)
    expert_gate_ok, expert_gate, expert_gate_block_reason = gate_allows_expert_input(run_dir)
    expert_voice_cards = expert_voice_cards_from_gate(expert_gate)
    if not gate_ok:
        blocked_package = {
            'schema': 'sensenova_mirofish_feed_package_v1',
            'created_at': now(),
            'status': 'NO_VALID_BODY_FOR_MIROFISH',
            'reason': gate_block_reason,
            'source_run_dir': str(run_dir),
            'mirofish_input_gate': mirofish_gate,
            'mirofish_input_gate_path': str(run_dir / 'raw' / 'mirofish_input_gate.json'),
            'expert_voice_cards': expert_voice_cards,
            'expert_voice_card_count': len(expert_voice_cards),
            'source_cards': [],
            'source_card_count': 0,
            'fresh_news_cards': [],
            'fresh_news_card_count': 0,
            'body_fetch_report_path': str(run_dir / 'raw' / 'body_fetch_report.json'),
            'raw_bodies_dir': str(run_dir / 'raw' / 'bodies'),
            'body_file_count': body_file_count,
            'policy': {
                'query_plan_excluded': True,
                'formal_cards_written': False,
                'production_runner_modified': False,
                'outline_text_txt_draft_modified': False,
                'root_outputs_updated': False,
                'body_success_requires_raw_bodies_txt': True,
            },
            'valid_input_count': 0,
            'skipped_count': 0,
        }
        report = '\n'.join([
            '# MiroFish feed-to-card bridge blocked',
            '',
            f'- created_at: {now()}',
            f'- source_run_dir: {run_dir}',
            f'- status: NO_VALID_BODY_FOR_MIROFISH',
            f'- reason: {gate_block_reason}',
            f'- gate_status: {mirofish_gate.get("status", "")}',
            f'- body_fetch_report_path: {run_dir / "raw" / "body_fetch_report.json"}',
            f'- raw_bodies_dir: {run_dir / "raw" / "bodies"}',
            f'- body_file_count: {body_file_count}',
            '- root_outputs_updated: NO',
            '- formal_cards_written: NO',
            '- outline_text_txt_draft_modified: NO',
            '',
        ])
        (bridge_dir / 'mirofish_feed_package.json').write_text(json.dumps(blocked_package, ensure_ascii=False, indent=2), encoding='utf-8')
        (bridge_dir / 'decision_cards.json').write_text('[]\n', encoding='utf-8')
        (bridge_dir / 'card_conversion_tasks.json').write_text('[]\n', encoding='utf-8')
        (bridge_dir / 'dry_run_report.generated.md').write_text(report, encoding='utf-8')
        print(json.dumps({
            'status': 'NO_VALID_BODY_FOR_MIROFISH',
            'reason': gate_block_reason,
            'run_dir': str(run_dir),
            'out_dir': str(out_dir),
            'per_run_bridge_dir': str(per_run_dir),
            'root_updated': False,
            'valid_input_count': 0,
            'skipped_count': 0,
            'body_file_count': body_file_count,
            'gate_status': mirofish_gate.get('status', ''),
            'report': str(bridge_dir / 'dry_run_report.generated.md'),
        }, ensure_ascii=False, indent=2))
        return 0

    if not expert_gate_ok:
        blocked_package = {
            'schema': 'sensenova_mirofish_feed_package_v1',
            'created_at': now(),
            'status': 'EXPERT_GATE_BLOCKED',
            'reason': expert_gate_block_reason or 'EXPERT_GATE_INSUFFICIENT',
            'source_run_dir': str(run_dir),
            'mirofish_input_gate': mirofish_gate,
            'mirofish_input_gate_path': str(run_dir / 'raw' / 'mirofish_input_gate.json'),
            'expert_gate_report': expert_gate,
            'expert_gate_report_path': str(run_dir / 'raw' / 'expert_gate_report.json'),
            'expert_voice_cards': expert_voice_cards,
            'expert_voice_card_count': len(expert_voice_cards),
            'source_cards': [],
            'source_card_count': 0,
            'fresh_news_cards': [],
            'fresh_news_card_count': 0,
            'body_fetch_report_path': str(run_dir / 'raw' / 'body_fetch_report.json'),
            'raw_bodies_dir': str(run_dir / 'raw' / 'bodies'),
            'body_file_count': body_file_count,
            'policy': {
                'query_plan_excluded': True,
                'formal_cards_written': False,
                'production_runner_modified': False,
                'outline_text_txt_draft_modified': False,
                'root_outputs_updated': False,
                'body_success_requires_raw_bodies_txt': True,
                'expert_gate_required_before_mirofish': True,
                'search_summary_is_not_source_body': True,
                'no_search_result_is_not_no_advice': True,
            },
            'valid_input_count': 0,
            'skipped_count': 0,
        }
        report = '\n'.join([
            '# MiroFish feed-to-card bridge blocked',
            '',
            f'- created_at: {now()}',
            f'- source_run_dir: {run_dir}',
            f'- status: EXPERT_GATE_BLOCKED',
            f'- reason: {expert_gate_block_reason or "EXPERT_GATE_INSUFFICIENT"}',
            f'- gate_status: {mirofish_gate.get("status", "")}',
            f'- expert_gate_pass: {expert_gate.get("expert_gate_pass", False)}',
            f'- expert_failure_tags: {json.dumps(expert_gate.get("failure_tags", []), ensure_ascii=False)}',
            f'- expert_gate_report_path: {run_dir / "raw" / "expert_gate_report.json"}',
            '- root_outputs_updated: NO',
            '- formal_cards_written: NO',
            '- outline_text_txt_draft_modified: NO',
            '',
        ])
        (bridge_dir / 'mirofish_feed_package.json').write_text(json.dumps(blocked_package, ensure_ascii=False, indent=2), encoding='utf-8')
        (bridge_dir / 'decision_cards.json').write_text('[]\n', encoding='utf-8')
        (bridge_dir / 'card_conversion_tasks.json').write_text('[]\n', encoding='utf-8')
        (bridge_dir / 'dry_run_report.generated.md').write_text(report, encoding='utf-8')
        print(json.dumps({
            'status': 'EXPERT_GATE_BLOCKED',
            'reason': expert_gate_block_reason or 'EXPERT_GATE_INSUFFICIENT',
            'run_dir': str(run_dir),
            'out_dir': str(out_dir),
            'per_run_bridge_dir': str(per_run_dir),
            'root_updated': False,
            'valid_input_count': 0,
            'skipped_count': 0,
            'body_file_count': body_file_count,
            'gate_status': mirofish_gate.get('status', ''),
            'expert_gate_pass': expert_gate.get('expert_gate_pass', False),
            'expert_failure_tags': expert_gate.get('failure_tags', []),
            'report': str(bridge_dir / 'dry_run_report.generated.md'),
        }, ensure_ascii=False, indent=2))
        return 0

    plan = load_json(run_dir / 'cards' / 'card_distill_plan.json', {}) or {}
    items = plan.get('items', []) if isinstance(plan, dict) else []
    if args.limit > 0:
        items = items[:args.limit]
    body_fetch_evidence = load_body_fetch_evidence(run_dir)
    evidence_item_count = body_fetch_evidence_item_count(body_fetch_evidence)
    dedupe_text = load_dedupe_text()
    cross_run_dedupe_file = out_dir / 'bridge_run' / 'processed_signatures.json'
    cross_run_records = load_cross_run_dedupe(cross_run_dedupe_file)

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
        body_fetch_item = body_fetch_item_for(it, body_fetch_evidence)
        if not body_fetch_item:
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': it.get('url'), 'status': status, 'reason': 'missing_body_fetch_evidence'})
            continue
        raw_body_path = raw_body_path_from_evidence(body_fetch_item, run_dir)
        if not raw_body_path:
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': it.get('url'), 'status': status, 'reason': 'missing_raw_body_txt'})
            continue
        if it.get('source_role') == 'primary_official_social' and body_fetch_item.get('source_role') not in ('primary_official_social', 'official_social_discovery'):
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': it.get('url'), 'status': status, 'reason': 'source_role_mismatch'})
            continue
        if it.get('may_count_as_primary') is False and it.get('source_role') != 'secondary_authoritative':
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': it.get('url'), 'status': status, 'reason': 'secondary_fallback_source_role_missing'})
            continue
        url = it.get('url', '')
        if is_index_like_url(url):
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': url, 'status': status, 'reason': 'index_or_channel_url'})
            continue
        title = it.get('title', '')
        if is_malformed_search_title(title):
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': title, 'url': url, 'status': status, 'reason': 'malformed_search_title'})
            continue
        raw_body_preview = read_text(Path(raw_body_path), 1000)
        title_body_mismatch = text_has_story_value_keywords(raw_body_preview) and not text_has_story_value_keywords(title)
        card_path = Path(it.get('card', ''))
        if not card_path.exists():
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': url, 'status': status, 'reason': 'card_file_missing'})
            continue
        card_preview = read_text(card_path, 4000)
        if is_short_navigation_body(card_preview):
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': url, 'status': status, 'reason': 'short_navigation_body'})
            continue
        # Body substance gate: must have ## Body Extract with >100 chars of evidence
        body_extract = ''
        if '## Body Extract' in card_preview:
            body_extract = card_preview.split('## Body Extract', 1)[1].strip()
        if not body_extract or len(body_extract) < 100:
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': url, 'status': status, 'reason': 'card_body_too_short_or_missing'})
            continue
        # Cross-run dedupe by normalized signature
        sig = sha(f"{normalize_url(url)}{normalize_title(title)}", 16)
        if is_cross_run_processed(sig, cross_run_records, run_id):
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': title, 'url': url, 'status': status, 'reason': 'already_in_previous_bridge_run'})
            continue
        domestic_hint = (it.get('source_group') == 'domestic') or bool(re.search(r'(\.gov\.cn|people\.com\.cn|xinhuanet\.com|cnsa\.gov\.cn)', url.lower())) or any(k in card_preview for k in ['发布时间：', '发布日期：', '来源：新华社', '来源：人民日报', '国家航天局'])
        if domestic_hint and is_stale_material(title, url, card_preview):
            skipped.append({'candidate_id': it.get('candidate_id'), 'title': it.get('title'), 'url': url, 'status': status, 'reason': 'stale_domestic_article'})
            continue
        valid_items.append(it)
        it['_title_body_mismatch'] = title_body_mismatch
        it['_bridge_body_fetch_evidence'] = {
            'body_fetch_report_path': str(run_dir / 'raw' / 'body_fetch_report.json'),
            'body_path': raw_body_path,
            'candidate_id': body_fetch_item.get('candidate_id', ''),
            'status': body_fetch_item.get('status', ''),
            'counts_as_body_success': bool(body_fetch_item.get('counts_as_body_success')),
            'source_role': body_fetch_item.get('source_role', ''),
            'source_confidence': body_fetch_item.get('source_confidence', ''),
        }

    decision_cards = []
    conversion_tasks = []
    counts = {k: 0 for k in VALID_DISPOSITIONS}
    for it in valid_items:
        card_path = Path(it['card'])
        card_text = read_text(card_path, 6000)
        body_path = body_path_for_card(it, run_dir)
        raw_body_text = read_text(body_path, 6000) if body_path else ''
        dup, dup_reason = is_duplicate(it, dedupe_text)
        # BUG-P4 fix: when title-body mismatch detected, classify using body-dominant text
        # to avoid policy-concept title overriding real engineering content in body.
        title_for_classify = it.get('title', '')
        if it.get('_title_body_mismatch'):
            # Use a body-derived pseudo-title to prevent title's policy keywords
            # from overriding body's actual story value (e.g. semiconductor breakthrough)
            body_first_line = (raw_body_text or '').strip().split('\n', 1)[0][:120]
            if body_first_line and text_has_story_value_keywords(body_first_line):
                title_for_classify = body_first_line
        disp, chapter, reason, axis = classify_material(title_for_classify, '', f'{card_text}\n{raw_body_text}', it.get('source_group',''))
        if disp == 'OUTLINE_PATCH' and is_meeting_release_without_tech_data(raw_body_text or card_text):
            disp, chapter, reason = 'CHAPTER_PREP_ONLY', chapter or 125, '会议通稿且无具体技术数据，只作章节准备，不得直接升为OUTLINE_PATCH。'
        if dup:
            disp, chapter, reason = 'ARCHIVE_WITH_REASON', 0, f'重复或已入库：{dup_reason}'
        counts[disp] += 1
        material_id = f"{dt.datetime.now().strftime('%Y%m%d')}_{sha(it.get('candidate_id') or it.get('url') or it.get('title'), 10)}"
        evidence_complete = bool(it.get('url')) and card_path.exists() and not dup and not is_malformed_search_title(it.get('title',''))
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
            'body_fetch_evidence': it.get('_bridge_body_fetch_evidence', {}),
            'title_body_mismatch': bool(it.get('_title_body_mismatch')),
            'evidence_complete': evidence_complete,
            'duplicate_check': {'duplicate': dup, 'reason': dup_reason},
            'mirofish_projection': make_projection(it, card_text, disp, chapter, reason, axis),
            'disposition': disp,
            'disposition_reason': reason,
            'disposition_by': 'deterministic_bridge_20260606',
            'disposition_at': now(),
            'bridge_policy': 'dry_run_no_formal_card_no_index_no_wiki_write' if args.dry_run else 'bridge_artifacts_only_no_production_write',
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
                'required_checks_before_write': ['read_source_card', 'verify_body_evidence', 'dedupe_TS_INDEX_KB_INDEX_Wiki', 'write_formal_card', 'append_TS_INDEX', 'copy_or_link_KB_INDEX', 'append_Wiki'],
                'not_done_in_dry_run': True,
            })

    # Persist cross-run signatures for non-archived items
    for dc in decision_cards:
        if dc['disposition'] != 'ARCHIVE_WITH_REASON':
            sig = sha(f"{normalize_url(dc['source_url'])}{dc['title']}", 16)
            cross_run_records.setdefault(sig, set()).add(run_id)
    save_cross_run_dedupe(cross_run_records, cross_run_dedupe_file)
    source_cards = source_cards_from_decisions(decision_cards)
    fresh_news_cards = fresh_news_cards_from_source_cards(source_cards)
    missing_by_tier = missing_cards_by_tier(run_dir, decision_cards, state)
    p0_missing_cards = missing_by_tier.get('P0', [])
    p1_missing_cards = missing_by_tier.get('P1', [])
    # BUG-P4 gate: P0/P1 missing cards should block clean PASS
    p0_p1_gate_blocked = bool(p0_missing_cards) or bool(p1_missing_cards)

    skip_reason_counts: dict[str, int] = {}
    for s in skipped:
        r = str(s.get('reason') or 'unknown').lower()
        skip_reason_counts[r] = skip_reason_counts.get(r, 0) + 1

    feed_package = {
        'schema': 'sensenova_mirofish_feed_package_v1',
        'created_at': now(),
        'source_run_dir': str(run_dir),
        'mirofish_input_gate': mirofish_gate,
        'mirofish_input_gate_path': str(run_dir / 'raw' / 'mirofish_input_gate.json'),
        'expert_gate_report': expert_gate,
        'expert_gate_report_path': str(run_dir / 'raw' / 'expert_gate_report.json'),
        'expert_voice_cards': expert_voice_cards,
        'expert_voice_card_count': len(expert_voice_cards),
        'source_cards': source_cards,
        'source_card_count': len(source_cards),
        'fresh_news_cards': fresh_news_cards,
        'fresh_news_card_count': len(fresh_news_cards),
        'body_fetch_report_path': str(run_dir / 'raw' / 'body_fetch_report.json'),
        'raw_bodies_dir': str(run_dir / 'raw' / 'bodies'),
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
            'body_success_requires_raw_bodies_txt': True,
            'expert_gate_required_before_mirofish': True,
        },
        'valid_input_count': len(valid_items),
        'skipped_count': len(skipped),
        'skip_reason_counts': skip_reason_counts,
        'body_fetch_evidence_count': evidence_item_count,
        'body_fetch_evidence_key_count': len(body_fetch_evidence),
        'stale_domestic_blocked_count': skip_reason_counts.get('stale_domestic_article', 0),
        'missing_cards_by_tier': missing_by_tier,
        'p0_missing': bool(p0_missing_cards),
        'p0_missing_cards': p0_missing_cards,
        'p1_missing_cards': p1_missing_cards,
        'p0_p1_gate_blocked': p0_p1_gate_blocked,
        'skipped': skipped,
        'decision_cards_path': str(bridge_dir / 'decision_cards.json'),
        'conversion_tasks_path': str(bridge_dir / 'card_conversion_tasks.json'),
        'cross_run_dedupe_path': str(cross_run_dedupe_file),
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
        f'- expert_gate_pass: {expert_gate.get("expert_gate_pass", False)}',
        f'- expert_voice_card_count: {len(expert_voice_cards)}',
        f'- source_card_count: {len(source_cards)}',
        f'- fresh_news_card_count: {len(fresh_news_cards)}',
        f'- valid_input_count: {len(valid_items)}',
        f'- skipped_count: {len(skipped)}',
        f'- body_fetch_evidence_count: {evidence_item_count}',
        f'- skip_reason_counts: {json.dumps(skip_reason_counts, ensure_ascii=False)}',
        f'- stale_domestic_blocked_count: {skip_reason_counts.get("stale_domestic_article", 0)}',
        f'- p0_missing: {bool(p0_missing_cards)}',
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
    if missing_by_tier:
        lines += ['', '## Missing Cards by Tier', '', '| tier | missing_card_ids |', '|---|---|']
        for tier, card_ids in missing_by_tier.items():
            lines.append(f"| {tier} | {', '.join(card_ids)} |")
    lines += ['', '## Skipped', '', '| title | source status | reason |', '|---|---|---|']
    for s in skipped[:80]:
        lines.append(f"| {str(s.get('title',''))[:80]} | {s.get('status','')} | {s.get('reason','')} |")
    report = '\n'.join(lines) + '\n'
    (bridge_dir / 'dry_run_report.generated.md').write_text(report, encoding='utf-8')
    root_updated = (not is_verify_run(run_dir)) and len(valid_items) > 0
    if root_updated:
        root_bridge_dir.mkdir(parents=True, exist_ok=True)
        (root_bridge_dir / 'mirofish_feed_package.json').write_text(json.dumps(feed_package, ensure_ascii=False, indent=2), encoding='utf-8')
        (root_bridge_dir / 'decision_cards.json').write_text(json.dumps(decision_cards, ensure_ascii=False, indent=2), encoding='utf-8')
        (root_bridge_dir / 'card_conversion_tasks.json').write_text(json.dumps(conversion_tasks, ensure_ascii=False, indent=2), encoding='utf-8')
        (root_bridge_dir / 'dry_run_report.generated.md').write_text(report, encoding='utf-8')
        (out_dir / 'DRY_RUN_REPORT.md').write_text(report, encoding='utf-8')
        latest_valid = {
            'updated_at': now(),
            'run_id': run_id,
            'run_dir': str(run_dir),
            'per_run_bridge_dir': str(per_run_dir),
            'valid_input_count': len(valid_items),
            'skipped_count': len(skipped),
            'disposition_counts': counts,
            'conversion_task_count': len(conversion_tasks),
            'missing_cards_by_tier': missing_by_tier,
            'p0_missing': bool(p0_missing_cards),
            'p0_missing_cards': p0_missing_cards,
            'report': str(out_dir / 'DRY_RUN_REPORT.md'),
        }
        if p0_p1_gate_blocked:
            latest_valid['p0_p1_gate_blocked'] = True
            latest_valid['p1_missing_cards'] = p1_missing_cards
        (out_dir / 'LATEST_VALID_BRIDGE_RUN.json').write_text(json.dumps(latest_valid, ensure_ascii=False, indent=2), encoding='utf-8')
    else:
        report += '\n## Root Output Guard\n\nRoot DRY_RUN_REPORT.md was not overwritten because this run is verify-like or has zero valid input.\n'
        (bridge_dir / 'dry_run_report.generated.md').write_text(report, encoding='utf-8')
    bridge_status = 'DRY_RUN_DONE' if args.dry_run else 'BRIDGE_DONE'
    if p0_p1_gate_blocked:
        bridge_status = 'BRIDGE_P0_P1_GATE_BLOCKED' if not args.dry_run else 'DRY_RUN_P0_P1_GATE_BLOCKED'
    print(json.dumps({'status': bridge_status, 'run_dir': str(run_dir), 'out_dir': str(out_dir), 'per_run_bridge_dir': str(per_run_dir), 'root_updated': root_updated, 'expert_gate_pass': expert_gate.get('expert_gate_pass', False), 'valid_input_count': len(valid_items), 'skipped_count': len(skipped), 'skip_reason_counts': skip_reason_counts, 'stale_domestic_blocked_count': skip_reason_counts.get('stale_domestic_article', 0), 'missing_cards_by_tier': missing_by_tier, 'p0_missing': bool(p0_missing_cards), 'p0_missing_cards': p0_missing_cards, 'p1_missing_cards': p1_missing_cards, 'p0_p1_gate_blocked': p0_p1_gate_blocked, 'disposition_counts': counts, 'conversion_task_count': len(conversion_tasks), 'report': str((out_dir / 'DRY_RUN_REPORT.md') if root_updated else (bridge_dir / 'dry_run_report.generated.md'))}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
