#!/usr/bin/env python3
"""
kewu_domain_scorer.py  v1  (2026-07-10)

科武纪元 素材域感知评分模块。
查询组合（域×时间×事件）、评分、动态实体抽取、降噪。

不改小说正文/大纲。
"""
from __future__ import annotations

import datetime as dt
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from kewu_domain_ontology import (
    DYSON_SPHERE_CAPABILITY_TREE,
    ENTITY_PATTERNS,
    NOISE_DOMAINS,
    SCORING_WEIGHTS,
    SOURCE_AUTHORITY,
    STABLE_DOMAINS,
    STABLE_DOMAINS as _SD,
    TEMPORAL_KEYWORDS,
    DOMAIN_OFFICIAL_SITES,
    EVENT_SEMANTIC_TEMPLATES,
    TIMELINESS_DECAY,
    get_domain_for_keywords,
    is_noise_domain,
)

DEFAULT_OUTLINE_PATH = Path('/root/workspace/科武纪元/wiki/raw/outline/科武纪元大纲_latest.md')


# ═══════════════════════════════════════════════
# 1. 域×时间×事件 查询组合
# ═══════════════════════════════════════════════

def compose_domain_queries(
    domain_ids: list[str] | None = None,
    temporal: str = 'today',
    max_queries_per_domain: int = 3,
) -> list[dict[str, Any]]:
    """为指定域生成域×时间×事件组合查询。

    Args:
        domain_ids: 域 ID 列表，None 则取全部九域
        temporal: 'today' | 'this_week' | 'this_month'
        max_queries_per_domain: 每域最大查询数

    Returns:
        查询列表，每项含 query, domain_id, category, priority
    """
    if domain_ids is None:
        domain_ids = list(STABLE_DOMAINS.keys())

    temporal_kws = TEMPORAL_KEYWORDS.get(temporal, TEMPORAL_KEYWORDS['today'])
    queries: list[dict[str, Any]] = []

    for domain_id in domain_ids:
        domain = STABLE_DOMAINS.get(domain_id)
        if not domain:
            continue
        domain_kws = domain['query_keywords'][:6]  # 取前6个高频词
        domain_label = domain['label']
        official_sites = DOMAIN_OFFICIAL_SITES.get(domain_id, [])

        count = 0
        # 模板1: 域×时间×事件
        for kw in domain_kws[:2]:
            for tk in temporal_kws[:2]:
                q = f'{kw} {tk}'
                queries.append({
                    'query': q,
                    'domain_id': domain_id,
                    'category': f'domain_time_event:{domain_label}',
                    'priority': 1,
                    'composition': f'{kw} × {tk}',
                })
                count += 1
                if count >= max_queries_per_domain:
                    break
            if count >= max_queries_per_domain:
                break

        # 模板2: site: 官方源定向
        if official_sites and count < max_queries_per_domain:
            site = official_sites[0]
            kw = domain_kws[0] if domain_kws else domain_label
            tk = temporal_kws[0]
            q = f'site:{site} {kw} {tk}'
            queries.append({
                'query': q,
                'domain_id': domain_id,
                'category': f'domain_official:{domain_label}',
                'priority': 2,
                'composition': f'site:{site} × {kw} × {tk}',
            })
            count += 1

        # 模板3: 突破发现
        if count < max_queries_per_domain:
            kw = domain_kws[0] if domain_kws else domain_label
            q = f'{kw} 突破 最新 进展'
            queries.append({
                'query': q,
                'domain_id': domain_id,
                'category': f'domain_breakthrough:{domain_label}',
                'priority': 3,
                'composition': f'{kw} × 突破 × 最新',
            })

    queries.sort(key=lambda x: x['priority'])
    return queries


# ═══════════════════════════════════════════════
# 1b. latest 大纲动态解析
# ═══════════════════════════════════════════════

def _clean_outline_field(value: str) -> str:
    return re.sub(r'\s+', ' ', value or '').strip(' |｜\t\r\n')


def _extract_outline_title(fragment: str) -> str:
    parts = [_clean_outline_field(p) for p in re.split(r'[|｜]', fragment) if _clean_outline_field(p)]
    if not parts:
        return ''
    if len(parts) >= 2 and ('卷' in parts[0] or re.search(r'第[一二三四五六七八九十百\d]+卷', parts[0])):
        return parts[1][:80]
    return parts[0][:80]


@lru_cache(maxsize=8)
def parse_latest_outline(outline_path: str = str(DEFAULT_OUTLINE_PATH)) -> dict[str, Any]:
    """Parse the current latest outline and return chapter records.

    The outline has historical notes and some table rows containing multiple
    chapters on one line, so parsing is occurrence-based rather than line-based.
    """
    path = Path(outline_path)
    text = path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''
    chapters: dict[int, dict[str, Any]] = {}
    matches = list(re.finditer(r'第\s*(\d{1,3})\s*章', text))
    for idx, match in enumerate(matches):
        chapter = int(match.group(1))
        next_start = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        line_end = text.find('\n', match.start(), next_start)
        end = min(x for x in [next_start, line_end if line_end != -1 else next_start] if x >= match.start())
        fragment = text[match.end():end]
        title = _extract_outline_title(fragment)
        context = _clean_outline_field(text[match.start():min(next_start, match.start() + 900)])
        previous = chapters.get(chapter)
        if previous and len(previous.get('context', '')) >= len(context):
            continue
        chapters[chapter] = {
            'chapter': chapter,
            'title': title,
            'context': context,
        }
    return {
        'outline_path': str(path),
        'chapter_count': len(chapters),
        'chapters': chapters,
    }


def outline_parse_stats(outline_path: str = str(DEFAULT_OUTLINE_PATH)) -> dict[str, Any]:
    parsed = parse_latest_outline(outline_path)
    return {
        'outline_path': parsed['outline_path'],
        'chapter_count': parsed['chapter_count'],
    }


def match_outline_chapters(
    text: str,
    domain_ids: list[str] | None = None,
    outline_path: str = str(DEFAULT_OUTLINE_PATH),
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Match candidate text to latest-outline chapters by ontology terms.

    Static domain chapter lists are used only as a weak fallback after the
    latest outline has been parsed and verified to contain those chapters.
    """
    parsed = parse_latest_outline(outline_path)
    chapters: dict[int, dict[str, Any]] = parsed.get('chapters', {})
    blob = (text or '').lower()
    if not blob or not chapters:
        return []

    domain_ids = domain_ids or [d for d, _ in get_domain_for_keywords(text)]
    candidate_terms: list[tuple[str, str]] = []
    for domain_id in domain_ids:
        domain = STABLE_DOMAINS.get(domain_id, {})
        for kw in domain.get('query_keywords', []) + domain.get('tech_institution_chars', []) + domain.get('plot_threads', []):
            if kw and kw.lower() in blob:
                candidate_terms.append((domain_id, kw))
    for node_id, node in DYSON_SPHERE_CAPABILITY_TREE.items():
        for kw in node.get('keywords', []):
            if kw and kw.lower() in blob:
                candidate_terms.append((f'dyson:{node_id}', kw))

    hits: dict[int, dict[str, Any]] = {}
    for chapter, rec in chapters.items():
        ctx = f"{rec.get('title', '')} {rec.get('context', '')}".lower()
        matched_terms = []
        matched_domains = set()
        for domain_id, kw in candidate_terms:
            if kw.lower() in ctx:
                matched_terms.append(kw)
                if not domain_id.startswith('dyson:'):
                    matched_domains.add(domain_id)
        if matched_terms:
            hits[chapter] = {
                'chapter': chapter,
                'title': rec.get('title', ''),
                'score': len(set(matched_terms)) * 2 + len(matched_domains),
                'matched_terms': sorted(set(matched_terms))[:10],
                'matched_domains': sorted(matched_domains),
                'mapping_source': 'latest_outline_keyword',
            }

    # Weak fallback: domain lists are accepted only against parsed latest chapters.
    for domain_id in domain_ids:
        domain = STABLE_DOMAINS.get(domain_id, {})
        for chapter in domain.get('outline_chapters', []):
            if chapter not in chapters or chapter in hits:
                continue
            hits[chapter] = {
                'chapter': chapter,
                'title': chapters[chapter].get('title', ''),
                'score': 0.5,
                'matched_terms': [],
                'matched_domains': [domain_id],
                'mapping_source': 'latest_outline_static_domain_fallback',
            }

    return sorted(hits.values(), key=lambda h: (-float(h['score']), int(h['chapter'])))[:limit]


def generate_followup_queries(entities: dict[str, list[str]], domain_ids: list[str]) -> list[dict[str, Any]]:
    """基于动态抽取的实体生成二次查询。

    Args:
        entities: 抽取结果 {entity_type: [entity_value, ...]}
        domain_ids: 当前命中的域 ID

    Returns:
        二次查询列表
    """
    queries: list[dict[str, Any]] = []

    # 型号实体 → 以型号为关键词 + 域时间词
    for model in entities.get('model_designation', []):
        for domain_id in domain_ids[:3]:
            domain = STABLE_DOMAINS.get(domain_id, {})
            domain_label = domain.get('label', '')
            queries.append({
                'query': f'{model} 最新 进展',
                'domain_id': domain_id,
                'category': f'followup_model:{model}',
                'priority': 2,
                'composition': f'entity:{model} × 最新',
            })

    # 组织实体 → 以组织为关键词 + 域
    for org in entities.get('organization', []):
        for domain_id in domain_ids[:2]:
            domain = STABLE_DOMAINS.get(domain_id, {})
            domain_kws = domain.get('query_keywords', [])[:2]
            kw = domain_kws[0] if domain_kws else ''
            if kw:
                queries.append({
                    'query': f'{org} {kw}',
                    'domain_id': domain_id,
                    'category': f'followup_org:{org}',
                    'priority': 2,
                    'composition': f'entity:{org} × {kw}',
                })

    return queries


# ═══════════════════════════════════════════════
# 2. 域感知评分
# ═══════════════════════════════════════════════

def score_item_domain_aware(
    item: dict[str, Any],
    outline_chapter_set: set[int] | None = None,
    outline_path: str = str(DEFAULT_OUTLINE_PATH),
) -> dict[str, Any]:
    """对素材卡进行域感知评分。

    Args:
        item: 素材卡 dict (title, summary, url, source_group_key, published_at, ...)
        outline_chapter_set: 大纲所有章节号集合（用于命中判断）

    Returns:
        评分结果 dict，含 total_score, domain_scores, breakdown, noise_flag, ...
    """
    title = str(item.get('title') or '')
    summary = str(item.get('summary') or '')
    url = str(item.get('url') or '')
    blob = f'{title} {summary} {url}'
    source_group = str(item.get('source_group_key') or '')
    published_at = str(item.get('published_at') or '')

    breakdown: dict[str, float] = {}
    domain_hits: list[tuple[str, float]] = []
    outline_hits: list[int] = []
    outline_match_details: list[dict[str, Any]] = []
    tech_institution_hits: list[str] = []
    character_plot_hits: list[str] = []
    parsed_outline = parse_latest_outline(outline_path)
    if outline_chapter_set is None:
        outline_chapter_set = set(parsed_outline.get('chapters', {}).keys())

    # --- 噪声检查（先检查，命中直接返回） ---
    is_noise, noise_reason = is_noise_domain(blob)
    if is_noise:
        return {
            'total_score': SCORING_WEIGHTS['noise_penalty'],
            'domain_scores': [],
            'breakdown': {'noise_penalty': SCORING_WEIGHTS['noise_penalty']},
            'noise_flag': True,
            'noise_reason': noise_reason,
            'outline_chapter_hits': [],
            'outline_match_details': [],
            'outline_parse': outline_parse_stats(outline_path),
            'tech_institution_hits': [],
            'character_plot_hits': [],
        }

    # --- 域相关性 ---
    domain_hits = get_domain_for_keywords(blob)
    domain_score_sum = 0.0
    for domain_id, hit_count in domain_hits:
        domain_score_sum += hit_count
    breakdown['domain_relevance'] = min(domain_score_sum, 10.0) * (
        SCORING_WEIGHTS['domain_relevance'] / 10.0
    )

    # --- 大纲章节命中 ---
    if outline_chapter_set:
        outline_match_details = match_outline_chapters(
            blob,
            [domain_id for domain_id, _ in domain_hits],
            outline_path=outline_path,
        )
        outline_hits = [
            int(hit['chapter']) for hit in outline_match_details
            if int(hit['chapter']) in outline_chapter_set
        ]
    breakdown['outline_chapter_hit'] = min(len(outline_hits), 5.0) * (
        SCORING_WEIGHTS['outline_chapter_hit'] / 5.0
    )

    # --- 技术-制度关键词 ---
    for domain_id, _ in domain_hits:
        domain = STABLE_DOMAINS.get(domain_id, {})
        for kw in domain.get('tech_institution_chars', []):
            if kw.lower() in blob.lower():
                if kw not in tech_institution_hits:
                    tech_institution_hits.append(kw)
    breakdown['tech_institution'] = min(len(tech_institution_hits), 5.0) * (
        SCORING_WEIGHTS['tech_institution'] / 5.0
    )

    # --- 人物-情节映射 ---
    for domain_id, _ in domain_hits:
        domain = STABLE_DOMAINS.get(domain_id, {})
        for kw in domain.get('plot_threads', []):
            if kw.lower() in blob.lower():
                if kw not in character_plot_hits:
                    character_plot_hits.append(kw)
    breakdown['character_plot'] = min(len(character_plot_hits), 5.0) * (
        SCORING_WEIGHTS['character_plot'] / 5.0
    )

    # --- 来源权威度 ---
    auth_score = SOURCE_AUTHORITY.get(source_group, 0.3)
    breakdown['source_authority'] = auth_score * SCORING_WEIGHTS['source_authority']

    # --- 时效性 ---
    timeliness = _compute_timeliness(published_at)
    breakdown['timeliness'] = timeliness * SCORING_WEIGHTS['timeliness']

    # --- 可信度 ---
    source_role = str(item.get('source_role') or '')
    if source_role == 'primary' or source_group in ('domestic_official', 'overseas_official'):
        credibility = 1.0
    elif source_role == 'secondary':
        credibility = 0.6
    else:
        credibility = 0.3
    breakdown['credibility'] = credibility * SCORING_WEIGHTS['credibility']

    total = sum(breakdown.values())

    return {
        'total_score': round(total, 2),
        'domain_scores': [(d, round(s, 2)) for d, s in domain_hits[:3]],
        'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
        'noise_flag': False,
        'noise_reason': '',
        'outline_chapter_hits': outline_hits[:5],
        'outline_match_details': outline_match_details[:5],
        'outline_parse': outline_parse_stats(outline_path),
        'tech_institution_hits': tech_institution_hits[:5],
        'character_plot_hits': character_plot_hits[:5],
    }


def _compute_timeliness(published_at: str) -> float:
    """计算时效性分数。"""
    if not published_at:
        return 0.3  # 未知日期给中等分

    try:
        # 解析各种格式
        pub = published_at.strip()
        if 'T' in pub:
            pub = pub.split('+')[0].split('Z')[0]  # 去时区
            pub_dt = dt.datetime.fromisoformat(pub)
        elif re.match(r'^\d{4}-\d{2}-\d{2}$', pub):
            pub_dt = dt.datetime.strptime(pub, '%Y-%m-%d')
        else:
            return 0.3

        now = dt.datetime.now()
        delta = now - pub_dt
        days = delta.days

        if days <= 0:
            return TIMELINESS_DECAY['same_day']
        elif days <= 7:
            return TIMELINESS_DECAY['same_week']
        elif days <= 30:
            return TIMELINESS_DECAY['same_month']
        else:
            return TIMELINESS_DECAY['older']
    except Exception:
        return 0.3


# ═══════════════════════════════════════════════
# 3. 动态实体抽取
# ═══════════════════════════════════════════════

def extract_entities(text: str) -> dict[str, list[str]]:
    """从文本中动态抽取新实体（型号/组织/人物）。

    Returns:
        {entity_type: [entity_value, ...]}
    """
    results: dict[str, list[str]] = {}
    for entity_type, config in ENTITY_PATTERNS.items():
        found: list[str] = []
        for pattern in config['patterns']:
            try:
                matches = re.findall(pattern, text)
                for m in matches:
                    m = m.strip()
                    if m and len(m) >= 2 and m not in found:
                        found.append(m)
            except re.error:
                continue
        if found:
            results[entity_type] = found
    return results


def should_generate_followup(entities: dict[str, list[str]]) -> bool:
    """判断是否需要生成二次查询。"""
    # 有新型号或新组织时生成
    return bool(entities.get('model_designation') or entities.get('organization'))


# ═══════════════════════════════════════════════
# 4. 降噪判断
# ═══════════════════════════════════════════════

def classify_noise_degradation(
    title: str,
    summary: str = '',
    url: str = '',
    published_at: str = '',
    source_group: str = '',
) -> tuple[bool, str]:
    """综合降噪判断：泛科普、娱乐、消费评测、旧闻。

    Returns:
        (should_degrade, reason)
    """
    blob = f'{title} {summary} {url}'

    # 1. 关键词噪声域
    is_noise, reason = is_noise_domain(blob)
    if is_noise:
        return True, reason

    # 2. 旧闻判断
    if published_at:
        max_age = _get_max_age(source_group)
        if _is_stale_by_date(published_at, max_age):
            return True, 'STALE_NEWS'

    # 3. 标题过短或无意义
    if title and len(title.strip()) < 6:
        return True, 'TITLE_TOO_SHORT'

    return False, ''


def _get_max_age(source_group: str) -> int:
    """获取来源组的最大允许天数。"""
    if source_group and 'domestic' in source_group:
        return NOISE_DOMAINS['stale_news']['max_age_days_domestic']
    return NOISE_DOMAINS['stale_news']['max_age_days_overseas']


def _is_stale_by_date(published_at: str, max_age_days: int) -> bool:
    """判断是否为旧闻。"""
    try:
        pub = published_at.strip()
        if 'T' in pub:
            pub = pub.split('+')[0].split('Z')[0]
            pub_dt = dt.datetime.fromisoformat(pub)
        elif re.match(r'^\d{4}-\d{2}-\d{2}$', pub):
            pub_dt = dt.datetime.strptime(pub, '%Y-%m-%d')
        else:
            return False  # 无法解析不判旧闻

        now = dt.datetime.now()
        return (now - pub_dt).days > max_age_days
    except Exception:
        return False


# ═══════════════════════════════════════════════
# 5. 戴森球能力树匹配
# ═══════════════════════════════════════════════

def match_dyson_tree(text: str, outline_chapter_hits: list[int] | None = None) -> list[dict[str, Any]]:
    """匹配文本与戴森球能力树节点。

    Returns:
        匹配的节点列表，含 node_id, label, level, chapter_hits, tech_constraints
    """
    text_lower = text.lower()
    matches: list[dict[str, Any]] = []

    outline_chapter_hits = outline_chapter_hits or []
    for node_id, node in DYSON_SPHERE_CAPABILITY_TREE.items():
        kw_hits = [kw for kw in node['keywords'] if kw.lower() in text_lower]
        chapter_hits = [ch for ch in outline_chapter_hits if ch in node.get('outline_chapters', [])]
        if kw_hits or chapter_hits:
            matches.append({
                'node_id': node_id,
                'label': node['label'],
                'level': node['level'],
                'keyword_hits': kw_hits[:5],
                'chapter_hits': chapter_hits[:5],
                'outline_chapters': node.get('outline_chapters', []),
                'tech_constraints': node.get('tech_constraints', []),
                'depends_on': node.get('depends_on', []),
                'match_source': 'keyword' if kw_hits else 'latest_outline_chapter',
            })

    return matches


# ═══════════════════════════════════════════════
# 6. 综合域评分报告
# ═══════════════════════════════════════════════

def score_and_classify_item(
    item: dict[str, Any],
    outline_chapter_set: set[int] | None = None,
    seen_urls: set[str] | None = None,
    outline_path: str = str(DEFAULT_OUTLINE_PATH),
) -> dict[str, Any]:
    """综合评分：域感知 + 降噪 + 实体抽取 + 戴森球匹配 + 去重。

    Args:
        item: 素材卡
        outline_chapter_set: 大纲章节号集合
        seen_urls: 已见 URL 集合（用于去重）

    Returns:
        综合评分结果
    """
    title = str(item.get('title') or '')
    summary = str(item.get('summary') or '')
    url = str(item.get('url') or '')
    published_at = str(item.get('published_at') or '')
    source_group = str(item.get('source_group_key') or '')
    blob = f'{title} {summary} {url}'

    # 1. 降噪判断
    should_degrade, degrade_reason = classify_noise_degradation(
        title, summary, url, published_at, source_group
    )
    if should_degrade:
        return {
            'total_score': SCORING_WEIGHTS['noise_penalty'],
            'domain_scores': [],
            'breakdown': {'noise_penalty': SCORING_WEIGHTS['noise_penalty']},
            'noise_flag': True,
            'noise_reason': degrade_reason,
            'outline_chapter_hits': [],
            'outline_match_details': [],
            'outline_parse': outline_parse_stats(outline_path),
            'tech_institution_hits': [],
            'character_plot_hits': [],
            'dyson_tree_matches': [],
            'dyson_gate_status': 'ARCHIVE_NO_DYSON_TREE_MATCH',
            'archive_reason': degrade_reason,
            'entities': {},
            'dedup_flag': False,
            'followup_needed': False,
        }

    # 2. 域感知评分
    score_result = score_item_domain_aware(item, outline_chapter_set, outline_path=outline_path)

    # 3. 去重
    dedup_flag = False
    if seen_urls and url:
        normalized = url.rstrip('/').lower()
        if normalized in seen_urls:
            dedup_flag = True
            score_result['total_score'] += SCORING_WEIGHTS['dedup_penalty']
            score_result['breakdown']['dedup_penalty'] = SCORING_WEIGHTS['dedup_penalty']

    # 4. 戴森球匹配
    dyson_matches = match_dyson_tree(blob, score_result.get('outline_chapter_hits', []))
    if dyson_matches:
        score_result['total_score'] += 2.5
        score_result['breakdown']['dyson_tree_gate'] = 2.5
        score_result['dyson_gate_status'] = 'PASS_DYSON_TREE'
        score_result['archive_reason'] = ''
    else:
        score_result['dyson_gate_status'] = 'ARCHIVE_NO_DYSON_TREE_MATCH'
        score_result['archive_reason'] = 'NO_DYSON_TREE_MATCH'

    # 5. 实体抽取
    entities = extract_entities(blob)

    # 6. 是否需要二次查询
    followup = should_generate_followup(entities)

    score_result['dyson_tree_matches'] = dyson_matches
    score_result['entities'] = entities
    score_result['dedup_flag'] = dedup_flag
    score_result['followup_needed'] = followup

    return score_result
