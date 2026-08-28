#!/usr/bin/env python3
"""platform_radar_v2.py — 多路由KOL/平台号观点雷达采集 v2

替代旧版 ddgs-only 串行超时脚本。
流程：工具采URL → platform_discovery.json → 观点推演/筛噪 → platform_mirofish_feed_package.json

用法：
  python3 platform_radar_v2.py                           # 全量跑
  python3 platform_radar_v2.py --platform wechat         # 只跑微信
  python3 platform_radar_v2.py --limit 3                 # 只跑前3个account
  python3 platform_radar_v2.py --resume                  # 从已有discovery续跑
  python3 platform_radar_v2.py --timeout-sec 10          # ddgs单条超时
  python3 platform_radar_v2.py --dry-run-mirofish        # 只产出discovery不跑模型
  python3 platform_radar_v2.py --discovery-json /path/x.json  # 用已有discovery做后段
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, re, subprocess, sys, time
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except Exception:  # pragma: no cover - optional runtime dependency
    requests = None

try:
    import websocket
except Exception:  # pragma: no cover - optional runtime dependency
    websocket = None

# ── paths ──
BASE = Path('/root/workspace/科武纪元')
TOOL = BASE / '工具脚本'
OUT_BASE = BASE / '学习记录/平台号观点雷达/runs'
WATCH = BASE / '学习记录/平台号观点雷达/platform_watchlist.json'
COLLECT_WEB = Path('/root/.hermes/skills/research/web-data-collection-suite/scripts/collect_web.py')
ANYSEARCH_CLI = Path('/root/workspace/IMA素材/external_skills/anysearch-skill_20260604/repo/scripts/anysearch_cli.py')
SOCIAL_CDP_URL = os.getenv('KEWU_SOCIAL_CDP_URL', 'http://127.0.0.1:9224').rstrip('/')
SOCIAL_CDP_PORT = int(os.getenv('KEWU_SOCIAL_CDP_PORT', '9224'))
SOCIAL_CDP_PROFILE = Path(os.getenv('KEWU_SOCIAL_CDP_PROFILE', '/root/.hermes/browser_profiles/socialext-cft'))
SOCIAL_CDP_EXT_DIR = Path(os.getenv('KEWU_SOCIAL_CDP_EXT_DIR', '/root/.hermes/chrome_extensions/socialext-v3.3.2'))
SOCIAL_CDP_BINARY = os.getenv('KEWU_SOCIAL_CDP_BINARY', '/usr/bin/google-chrome')
SOCIAL_CDP_STARTUP_TIMEOUT = int(os.getenv('KEWU_SOCIAL_CDP_STARTUP_TIMEOUT', '15'))
SOCIAL_CDP_ALLOWED_PLATFORMS = {'xiaohongshu', 'douyin', 'bilibili', 'kuaishou', 'tiktok'}
SOCIAL_CDP_DOMAIN_MAP = {
    'xiaohongshu': ['xiaohongshu.com', 'xhslink.com'],
    'douyin': ['douyin.com'],
    'bilibili': ['bilibili.com'],
    'kuaishou': ['kuaishou.com'],
    'tiktok': ['tiktok.com'],
}

sys.path.insert(0, str(TOOL))
try:
    from kewu_domain_scorer import score_and_classify_item, outline_parse_stats
    _HAS_DOMAIN_SCORER = True
except Exception:
    _HAS_DOMAIN_SCORER = False

TODAY = datetime.date.today().isoformat()
RUN_DIR = OUT_BASE / f'run_{TODAY}_v2'

# ── standard item schema ──
EMPTY_ITEM = {
    'account': '', 'platform': '', 'query': '', 'url': '',
    'title': '', 'author': '', 'published_at': '',
    'source_route': '', 'discovery_status': '', 'body_status': '',
    'evidence': '', 'viewpoint_inference': '', 'material_policy': '',
    'failure_tag': '', 'domain_id': '', 'domain_name': '',
}

NOISE_TERMS = [
    'bw2026', '哔哩哔哩游戏', '直播', '下载中心', '微信公众平台接口调试',
    'miniprogram/landing_page', '客服服务', 'login', 'signup',
    'register', 'download app',
]
SIGNAL_KW = [
    'ai', '人工智能', '芯片', '半导体', '中美', '地缘', '科技',
    '量子', '航天', '出口管制', '产业链', '数据安全', '互联网',
    # P0: 科技突破关键词扩展（修正G1手术误判NOISE）
    '手术', '机器人', '首飞', '回收', '长征', '运载火箭', '商业航天',
    '重复使用', '活体', '精准', '微创', '外骨骼', '仿生', '具身智能',
    '可控回收', '垂直返回', '可复用', '网系捕获',
    # Domain expansion: 9-domain coverage for Dyson tree
    # 生物
    '基因编辑', '脑机接口', '生物技术', '生命科学', '合成生物学', '神经科学',
    # 航空
    '战斗机', '航空发动机', '六代机', '无人机', 'C919', '运20',
    # 材料
    '超导', '新材料', '碳纤维', '纳米', '稀土', '碳基材料',
    # 能源
    '可控核聚变', '核聚变', 'ITER', '储能', '光伏', '氢能', '碳中和',
    # 军事（扩展）
    '导弹', '国防', '军备', '航母', '潜艇',
]

HOTSPOT_ACTION_TERMS = (
    '发布', '推出', '开放', '开源', '权重', '宣布', '发现', '证明', '突破', '攻破',
    '漏洞', '攻击', '越狱', '投毒', '首飞', '发射', '回收', 'released', 'launched',
    'open-weight', 'open weight', 'open-source', 'announced', 'discovered', 'proved',
    'breakthrough', 'attack', 'exploit', 'jailbreak', 'poisoning', 'vulnerability',
)

HOTSPOT_AI_SCIENCE_DOMAINS = {'frontier_tech', 'biology', 'space', 'ai', 'materials', 'energy'}


def platform_alias(platform: str) -> str:
    return {
        '微信公众号': 'wechat', '公众号': 'wechat',
        'B站': 'bilibili', '微博': 'weibo', '知乎': 'zhihu', '网站': 'generic',
    }.get(platform, platform) or platform


def build_account_query_plan(
    accounts: list[dict],
    platform_filter: set[str] | None = None,
    coverage_sweep: bool = False,
    max_queries: int = 0,
) -> list[tuple[dict, str, str]]:
    """Plan queries explicitly; coverage sweeps rotate across all configured domains."""
    platform_filter = platform_filter or set()

    def eligible_platforms(account: dict) -> list[tuple[str, str]]:
        rows = []
        for raw in account.get('platform_candidates', []):
            normalized = platform_alias(raw)
            if normalized == 'generic':
                continue
            if platform_filter and raw not in platform_filter and normalized not in platform_filter:
                continue
            rows.append((raw, normalized))
        return rows

    plan: list[tuple[dict, str, str]] = []
    if not coverage_sweep:
        for account in accounts:
            for raw, normalized in eligible_platforms(account):
                plan.append((account, raw, normalized))
                if max_queries > 0 and len(plan) >= max_queries:
                    return plan
        return plan

    by_domain: dict[str, list[dict]] = {}
    domain_order: list[str] = []
    for account in accounts:
        domain_id = account.get('domain_id', '') or 'unknown'
        if domain_id not in by_domain:
            by_domain[domain_id] = []
            domain_order.append(domain_id)
        by_domain[domain_id].append(account)
    selected_per_domain: dict[str, set[str]] = {domain_id: set() for domain_id in domain_order}
    selected_names: set[str] = set()
    max_rounds = max((len(rows) for rows in by_domain.values()), default=0)
    for _ in range(max_rounds):
        for domain_id in domain_order:
            domain_accounts = by_domain[domain_id]
            remaining = [account for account in domain_accounts if account.get('name', '') not in selected_per_domain[domain_id]]
            if not remaining:
                continue
            account = next((row for row in remaining if row.get('name', '') not in selected_names), remaining[0])
            platforms = eligible_platforms(account)
            if not platforms:
                selected_per_domain[domain_id].add(account.get('name', ''))
                continue
            raw, normalized = platforms[0]
            plan.append((account, raw, normalized))
            selected_per_domain[domain_id].add(account.get('name', ''))
            selected_names.add(account.get('name', ''))
            if max_queries > 0 and len(plan) >= max_queries:
                return plan
    return plan


# A missing date has several distinct causes that were all collapsed into a
# single DATE_UNKNOWN tag, so diagnostics could not tell "we never fetched the
# page" from "we fetched it and it genuinely carries no date". These subtypes
# keep DATE_UNKNOWN as the prefix so existing prefix-based consumers still
# match, while making the cause actionable.
DATE_UNKNOWN_TAGS = frozenset({
    'DATE_UNKNOWN',
    'DATE_UNKNOWN_BODY_TRUNCATED',
    'DATE_UNKNOWN_BODY_FETCH_FAIL',
    'DATE_UNKNOWN_NON_ARTICLE',
    # Legacy subtype kept for old sidecars; new runs demote aggregators to
    # WEIBO_AGGREGATOR_PAGE + ARCHIVE_WITH_REASON so they leave eligible.
    'DATE_UNKNOWN_AGGREGATOR_PAGE',
    'DATE_UNKNOWN_NO_METADATA',
})


def is_date_unknown_tag(tag: str) -> bool:
    """True for any DATE_UNKNOWN subtype (see DATE_UNKNOWN_TAGS)."""
    return (tag or '') in DATE_UNKNOWN_TAGS


def kol_hotspot_health_metrics(items: list[dict]) -> dict:
    eligible = [item for item in items if item.get('material_policy') in ('PLATFORM_SIGNAL', 'DISCOVERY_ONLY')]
    dated = [item for item in eligible if item.get('published_at') and not is_date_unknown_tag(item.get('failure_tag'))]
    dynamic_entities = {
        entity
        for item in eligible
        for values in (item.get('domain_score', {}).get('entities', {}) or {}).values()
        for entity in values
    }
    eventful = [
        item for item in dated
        if any(term.lower() in f"{item.get('title', '')} {item.get('evidence', '')}".lower() for term in HOTSPOT_ACTION_TERMS)
    ]
    ai_science = [
        item for item in eventful
        if (item.get('domain_id_scored') or item.get('domain_id')) in HOTSPOT_AI_SCIENCE_DOMAINS
    ]
    return {
        'fresh_dated_count': len(dated),
        'hotspot_event_count': len(eventful),
        'ai_science_hotspot_count': len(ai_science),
        'dynamic_entity_count': len(dynamic_entities),
        'dynamic_entities': sorted(dynamic_entities)[:30],
        'date_unknown_ratio': round(sum(1 for item in eligible if is_date_unknown_tag(item.get('failure_tag'))) / max(1, len(eligible)), 3),
    }


# ══════════════════════════════════════════
#  P0 fix (2026-08-11): per-domain diagnostics
#  — each domain MUST emit failure_reason, body_fetched, fresh_dated,
#    excerpt_only independently; no invention of success from excerpt+unknown.
# ══════════════════════════════════════════
_STRICT_FAILURE_TAGS = frozenset({'STALE_KOL_ARTICLE', 'DATE_OLD_YEAR'}) | DATE_UNKNOWN_TAGS
_NO_RESULT_POLICIES = frozenset({'NOISE', 'ARCHIVE_WITH_REASON'})


def compute_domain_diagnostics(domain_id: str, domain_items: list[dict], cdp_available: bool) -> dict:
    """Return independent per-domain counters + failure_reason.

    Contract:
      - body_fetched = items with body_status == 'fetched' (raw count).
      - body_fetched_strict = fetched AND failure_tag NOT in DATE_UNKNOWN/STALE AND policy NOT NOISE/ARCHIVE.
        This is the metric used by the strict health gate; excerpt_only NEVER counts here.
      - excerpt_only, fresh_dated_count, date_unknown_count counted independently.
      - failure_reason is a join of all observed failure causes for the domain.
    """
    total = len(domain_items)
    body_fetched = sum(1 for it in domain_items if it.get('body_status') == 'fetched')
    excerpt_only = sum(1 for it in domain_items if it.get('body_status') == 'excerpt_only')
    fetch_fail = sum(1 for it in domain_items if it.get('body_status') == 'fetch_fail')
    skipped_na = sum(1 for it in domain_items if it.get('body_status') == 'skipped_non_article')
    truncated = sum(1 for it in domain_items if it.get('body_status') == 'truncated_by_budget')
    dom_mismatch = sum(1 for it in domain_items if it.get('body_status') == 'skipped_domain_mismatch')
    no_hits_items = 0
    for it in domain_items:
        if it.get('discovery_status') == 'discovered':
            no_hits_items += 0
        elif not it.get('url'):
            no_hits_items += 1

    date_unknown = sum(1 for it in domain_items if is_date_unknown_tag(it.get('failure_tag')))
    stale = sum(1 for it in domain_items if it.get('failure_tag') in ('STALE_KOL_ARTICLE', 'DATE_OLD_YEAR'))
    noise = sum(1 for it in domain_items if it.get('material_policy') == 'NOISE')
    archive = sum(1 for it in domain_items if it.get('material_policy') == 'ARCHIVE_WITH_REASON')
    signal = sum(1 for it in domain_items if it.get('material_policy') == 'PLATFORM_SIGNAL')
    disc_only = sum(1 for it in domain_items if it.get('material_policy') == 'DISCOVERY_ONLY')

    # Fresh dated: has published_at AND not unknown/stale
    fresh_dated = sum(
        1 for it in domain_items
        if it.get('published_at')
        and it.get('failure_tag') not in _STRICT_FAILURE_TAGS
    )

    # Strict body: real body fetch AND not stale/unknown AND not noise/archive
    body_fetched_strict = sum(
        1 for it in domain_items
        if it.get('body_status') == 'fetched'
        and it.get('failure_tag') not in _STRICT_FAILURE_TAGS
        and it.get('material_policy') not in _NO_RESULT_POLICIES
    )

    reasons: list[str] = []
    if total == 0:
        reasons.append('NO_QUERY_EXECUTED')
    if no_hits_items > 0 and body_fetched == 0 and excerpt_only == 0:
        reasons.append(f'NO_HITS={no_hits_items}')
    if truncated > 0:
        reasons.append(f'BUDGET_TRUNCATED={truncated}')
    if stale > 0:
        reasons.append(f'STALE={stale}')
    if date_unknown > 0:
        suffix = '_CDP_UNAVAILABLE' if not cdp_available else ''
        reasons.append(f'DATE_UNKNOWN{suffix}={date_unknown}')
    if fetch_fail > 0:
        reasons.append(f'BODY_FETCH_FAIL={fetch_fail}')
    if skipped_na > 0:
        reasons.append(f'NON_ARTICLE_SKIPPED={skipped_na}')
    if dom_mismatch > 0:
        reasons.append(f'DOMAIN_MISMATCH={dom_mismatch}')
    if noise > 0:
        reasons.append(f'NOISE={noise}')
    if archive > 0:
        reasons.append(f'ARCHIVE_NO_DYSON={archive}')
    if body_fetched == 0 and excerpt_only == 0 and fetch_fail == 0 and skipped_na == 0 and truncated == 0 and total > 0:
        reasons.append('NO_URL_DISCOVERED')
    elif body_fetched == 0 and total > 0:
        reasons.append('NO_BODY_FETCHED')
    if signal == 0 and disc_only == 0 and body_fetched_strict == 0:
        reasons.append('NO_STRICT_RESULT')

    if not reasons:
        reasons.append('OK')

    return {
        'total_items': total,
        'body_fetched': body_fetched,
        'body_fetched_strict': body_fetched_strict,
        'excerpt_only': excerpt_only,
        'fetch_fail': fetch_fail,
        'skipped_non_article': skipped_na,
        'truncated_by_budget': truncated,
        'domain_mismatch': dom_mismatch,
        'no_hits_items': no_hits_items,
        'fresh_dated_count': fresh_dated,
        'date_unknown_count': date_unknown,
        'stale_count': stale,
        'noise_count': noise,
        'archive_count': archive,
        'signal_count': signal,
        'discovery_only_count': disc_only,
        'failure_reason': '|'.join(reasons),
    }

NON_ARTICLE_URL_PATTERNS = [
    r'/search\?', r'/search$', r'/tag/', r'/channel/', r'/account/',
    r'space\.bilibili\.com/\d+/?$', r'm\.bilibili\.com/search\?',
    r'search\.bilibili\.com',
    r'weibo\.com/\d+/?$', r'weibo\.com/u/\d+/?$',
    r'weibo\.com/[A-Za-z0-9_\-]+/?$',
    r'h5\.video\.weibo\.com/',
    r'zhihu\.com/people/', r'zhihu\.com/search\?',
    r'\.pdf($|\?)', r'\.pdf#',
    r'youtube\.com/@', r'youtube\.com/c/', r'youtube\.com/channel/',
]


def is_non_article_url(url: str) -> bool:
    u = (url or '').strip().lower()
    if not u:
        return True
    return any(re.search(p, u) for p in NON_ARTICLE_URL_PATTERNS)


def evidence_is_body(text: str) -> bool:
    t = re.sub(r'\s+', ' ', text or '').strip()
    if len(t) < 80:
        return False
    return bool(re.search(r'[。！？；：，,.;:]', t))


def sha12(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec='seconds')


def _host(url: str) -> str:
    try:
        return (urlparse(url).netloc or '').lower().lstrip('www.')
    except Exception:
        return ''


def _platform_from_url(url: str) -> str:
    host = _host(url)
    for platform, domains in SOCIAL_CDP_DOMAIN_MAP.items():
        if any(host == d or host.endswith('.' + d) for d in domains):
            return platform
    return ''


def _cdp_json(path: str) -> object:
    if not requests:
        raise RuntimeError('requests_unavailable')
    resp = requests.get(f'{SOCIAL_CDP_URL}{path}', timeout=3)
    resp.raise_for_status()
    return resp.json()


def _cdp_eval(ws_url: str, expression: str, timeout: int = 3) -> dict:
    if not websocket:
        return {'ok': False, 'error': 'websocket_unavailable'}
    try:
        ws = websocket.create_connection(ws_url, timeout=timeout)
        payload = {
            'id': 1,
            'method': 'Runtime.evaluate',
            'params': {'expression': expression, 'returnByValue': True},
        }
        ws.send(json.dumps(payload))
        raw = ws.recv()
        ws.close()
        data = json.loads(raw)
        if data.get('error'):
            return {'ok': False, 'error': data['error']}
        return {'ok': True, 'value': data.get('result', {}).get('result', {}).get('value')}
    except Exception as exc:
        return {'ok': False, 'error': repr(exc)[:200]}


def probe_social_cdp() -> dict:
    """Probe the already-running social helper Chrome through CDP.

    The probe is intentionally read-only and sanitizes page records. It never
    requests cookies, localStorage, headers, or extension secrets.
    """
    report = {
        'created_at': now_iso(),
        'cdp_url': SOCIAL_CDP_URL,
        'status': 'UNPROBED',
        'allowed_platforms': sorted(SOCIAL_CDP_ALLOWED_PLATFORMS),
        'pages': [],
        'extension_pages': [],
        'platform_pages': [],
        'extension_capability': 'UNKNOWN',
        'body_supplement_policy': 'existing_tab_visible_text_only_no_cookie_no_publish_no_interaction',
    }
    # 2026-08-12: 显式关闭时直接早退，省掉每轮 3s 连接超时。
    # status=CDP_DISABLED_BY_CONFIG 与 CDP_UNAVAILABLE 区分开，
    # 便于日后重建登录态时区分「按设计关闭」与「真的连不上」。
    if os.getenv('KEWU_DISABLE_SOCIAL_CDP') == '1':
        report['status'] = 'CDP_DISABLED_BY_CONFIG'
        report['disabled_reason'] = (
            'socialext-cft profile has no Default/Extensions and Cookies is ~20KB; '
            'social helper extension and platform login state are absent. '
            'Unset KEWU_DISABLE_SOCIAL_CDP after rebuilding login state.'
        )
        return report
    try:
        version = _cdp_json('/json/version')
        targets = _cdp_json('/json/list')
        report['browser'] = {
            'Browser': (version or {}).get('Browser', ''),
            'Protocol-Version': (version or {}).get('Protocol-Version', ''),
        }
    except Exception as exc:
        report['status'] = 'CDP_UNAVAILABLE'
        report['blocker'] = repr(exc)[:200]
        return report

    callable_hits = []
    for target in targets if isinstance(targets, list) else []:
        url = str(target.get('url') or '')
        page = {
            'id': target.get('id', ''),
            'type': target.get('type', ''),
            'title': str(target.get('title') or '')[:120],
            'url_host': _host(url),
            'platform': _platform_from_url(url),
            'is_extension': url.startswith('chrome-extension://'),
        }
        report['pages'].append(page)
        if page['is_extension']:
            report['extension_pages'].append(page)
            ws_url = target.get('webSocketDebuggerUrl', '')
            if ws_url:
                expr = """(() => {
                  const keys = Object.keys(window).filter(k => {
                    if (/^on/i.test(k)) return false;
                    return /(social|xhs|xiaohongshu|douyin|bilibili|kuaishou|tiktok|assistant|collector)/i.test(k);
                  }).slice(0, 30);
                  return {title: document.title, runtime: !!(window.chrome && chrome.runtime), keys};
                })()"""
                ev = _cdp_eval(ws_url, expr)
                if ev.get('ok'):
                    value = ev.get('value') or {}
                    callable_hits.append({'target_id': page['id'], 'title': page['title'], 'capability_keys': value.get('keys', []), 'chrome_runtime': value.get('runtime', False)})
        if page['platform'] in SOCIAL_CDP_ALLOWED_PLATFORMS:
            report['platform_pages'].append(page)

    report['extension_probe'] = callable_hits
    has_callable_keys = any(hit.get('capability_keys') for hit in callable_hits)
    if callable_hits and has_callable_keys:
        report['extension_capability'] = 'POSSIBLE_WINDOW_API_NEEDS_MANUAL_CONTRACT'
    elif callable_hits:
        report['extension_capability'] = 'EXTENSION_PAGE_VISIBLE_NO_PUBLIC_API_DETECTED'
    else:
        report['extension_capability'] = 'NO_EXTENSION_TARGET_DETECTED'
    report['status'] = 'CDP_AVAILABLE'
    return report


def social_cdp_visible_text_for_url(url: str, max_chars: int = 500) -> tuple[str, str]:
    """Return visible text from an already-open supported platform tab."""
    if os.getenv('KEWU_DISABLE_SOCIAL_CDP') == '1':
        return '', 'CDP_DISABLED'
    platform = _platform_from_url(url)
    if platform not in SOCIAL_CDP_ALLOWED_PLATFORMS:
        return '', 'CDP_PLATFORM_NOT_ALLOWED'
    try:
        targets = _cdp_json('/json/list')
    except Exception as exc:
        return '', f'CDP_UNAVAILABLE:{repr(exc)[:80]}'
    target_url_norm = (url or '').split('#')[0].rstrip('/')
    for target in targets if isinstance(targets, list) else []:
        current_url = str(target.get('url') or '').split('#')[0].rstrip('/')
        if not current_url or current_url != target_url_norm:
            continue
        ws_url = target.get('webSocketDebuggerUrl', '')
        if not ws_url:
            return '', 'CDP_NO_WEBSOCKET'
        expr = f"""(() => {{
          const text = (document.body && document.body.innerText || '').replace(/\\s+/g, ' ').trim();
          return text.slice(0, {int(max_chars)});
        }})()"""
        ev = _cdp_eval(ws_url, expr)
        if ev.get('ok') and ev.get('value'):
            return str(ev['value'])[:max_chars], ''
        return '', f"CDP_EVAL_FAIL:{ev.get('error', '')}"
    return '', 'CDP_NO_MATCHING_OPEN_TAB'


# ── P0 freshness gate ──
def _parse_relative_date(text: str, today: datetime.date | None = None) -> str:
    """Parse Weibo/Chinese relative time strings to ISO date.
    Returns '' if unparseable.
    """
    now = today or datetime.date.today()
    if not text:
        return ''
    t = text.strip().lower()
    try:
        parsed_rfc = parsedate_to_datetime(text.strip())
        if parsed_rfc:
            return parsed_rfc.date().isoformat()
    except (TypeError, ValueError, OverflowError):
        pass
    # "昨天", "前天", "X天前", "X小时前"
    m = re.search(r'(\d+)\s*(?:天前|天以前|days?\s*ago)', t)
    if m:
        return (now - datetime.timedelta(days=int(m.group(1)))).isoformat()
    # "今天" = today; "昨天"/"前天" handled below
    if '今天' in t or 'today' in t:
        return now.isoformat()
    if '昨天' in t or 'yesterday' in t:
        return (now - datetime.timedelta(days=1)).isoformat()
    if '前天' in t:
        return (now - datetime.timedelta(days=2)).isoformat()
    m = re.search(r'(\d+)\s*(?:小时前|hours?\s*ago)', t)
    if m:
        return now.isoformat()
    # "刚刚" / "just now" — published moments ago, still today
    if '刚刚' in t or 'just now' in t:
        return now.isoformat()
    # minutes/seconds ago — still today (handle both "30分钟前" and "几分钟前")
    if '几分钟前' in t or '几分钟' in t or '几秒钟' in t or '几秒前' in t:
        return now.isoformat()
    m = re.search(r'(\d+)\s*(?:分钟前|秒钟前|秒前|小时前|天前)', t)
    if m:
        return now.isoformat()
    m = re.search(r'(\d+)\s*(?:seconds?\s*ago|minutes?\s*ago)', t)
    if m:
        return now.isoformat()
    # Explicit ISO / YYYY-MM-DD / YYYY.MM.DD / YYYY/MM/DD — try before generic digit-date
    # regex at the end, so multi-character delimiters (e.g. "·") and non-digits after the
    # month/day don't force us into the YYYYMMDD fallback.
    m = re.search(r'(20\d{2})[./\-年](\d{1,2})[./\-月](\d{1,2})', t)
    if m:
        return f'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'
    m = re.search(r'(20\d{2})[.\/\-](\d{1,2})[.\/\-](\d{1,2})', t)
    if m:
        return f'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'
    # YYYY年MM月DD日
    m = re.search(r'(20\d{2})年(\d{1,2})月(\d{1,2})日?', t)
    if m:
        return f'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'
    # YYYY年 (only year, no month)
    m = re.search(r'(20\d{2})年', t)
    if m:
        return f'{m.group(1)}-01-01'
    # MM月DD日 without explicit year — Weibo widget / feed snippets omit the
    # year because it's implicit. Assume the current year, but if MM-DD is in
    # the future relative to *now*, roll back to the prior year (Dec content
    # collected in Jan). Past-only guard keeps this honest.
    m = re.search(r'(?:^|[^\d])(\d{1,2})月(\d{1,2})日(?:\s+\d{1,2}:\d{2})?', t)
    if m:
        mo, da = int(m.group(1)), int(m.group(2))
        try:
            cand = datetime.date(now.year, mo, da)
            if cand <= now:
                return cand.isoformat()
            return datetime.date(now.year - 1, mo, da).isoformat()
        except ValueError:
            pass
    return ''


def _looks_like_platform_id(raw: str) -> bool:
    """True when a bare digit run is a platform identifier, not an epoch stamp.

    Weibo uid / wechat biz-mid / bilibili aid are 9-11 digit runs that fall
    inside a plausible epoch range once read as seconds, so the timestamp
    branch would silently mint a publication date out of an account id.
    Epoch seconds for the content window we care about are 10 digits starting
    with '1' and below the 2^31 wrap; uids share that shape, so the only
    reliable discriminator is that a *seconds* stamp must land in the past.
    Callers apply the past-only guard; this helper rejects the shapes that are
    never timestamps at all (13-digit ms stamps are handled separately).
    """
    s = (raw or '').strip()
    if not s.isdigit():
        return False
    # 10-digit epoch seconds and 13-digit epoch millis are the only widths a
    # real platform timestamp uses. Anything else that is a pure digit run is
    # an identifier (uid, mid, aid, article id).
    return len(s) not in (10, 13)


def _yymmdd_segment_is_datelike(text: str, match: re.Match) -> bool:
    """Guard the weak YYMMDD fallback against id-bearing segments.

    Accept only when the 6-digit run is its own path/file token, e.g.
    `/a/b/ARTIx260726.shtml` or `/260726.html`. Reject when the run is glued
    to an id-style segment such as `space.bilibili.com/<uid>/article/251231.html`
    or Chinese ordinal text like `第251231号`, both of which previously minted a
    publication date out of an identifier.
    """
    start, end = match.start(), match.end()
    prefix = text[:start]
    # Reject when the run is the whole value of an id/article path slot, i.e.
    # the immediately preceding path segment names an identifier space
    # (".../article/251231.html", ".../detail/260726", "?id=251231").
    if re.search(r'(?:article|articles|item|items|detail|details|status|topic|id|no|num|p)[/=_\-]$', prefix, re.I):
        return False
    # Reject Chinese ordinal / numbering context ("第251231号", "编号251231").
    if re.search(r'(?:第|编号|序号|No\.?|#)\s*$', prefix, re.I):
        return False
    # Require the run to be delimited by a non-alphanumeric boundary or a
    # letter-led filename token (ARTIx260726), not by another digit run.
    boundary = prefix[-1:] if prefix else ''
    if boundary and boundary.isdigit():
        return False
    suffix = text[end:end + 1]
    if suffix and suffix.isdigit():
        return False
    return True


def extract_publication_date(item: dict, today: datetime.date | None = None) -> str:
    """Extract explicit publication evidence without inventing a collection date."""
    reference_date = today or datetime.date.today()
    candidates = [
        item.get('published_at'), item.get('created_at'), item.get('pubdate'),
        item.get('publish_time'), item.get('date'), item.get('url'),
        # Search/reader routes often carry the publication date only in excerpt/body.
        # This is still explicit source text; do not fall back to collection time.
        item.get('body'), item.get('text'), item.get('excerpt'), item.get('summary'),
        item.get('evidence'), item.get('title'),
    ]
    for raw in candidates:
        if raw is None or raw == '':
            continue
        if isinstance(raw, (int, float)) or (
            isinstance(raw, str) and raw.strip().isdigit()
            and len(raw.strip()) >= 10 and not _looks_like_platform_id(raw)
        ):
            try:
                stamp = int(raw)
                if stamp > 10_000_000_000:
                    stamp //= 1000
                parsed_dt = datetime.datetime.fromtimestamp(stamp, tz=datetime.timezone.utc).date()
                # A publication date can never be in the future. Weibo uids and
                # wechat mids are 10-digit runs that decode to plausible-looking
                # future dates (e.g. uid 1793892941 -> 2026-11-05), so the
                # past-only guard is what keeps an account id out of published_at.
                if 2000 <= parsed_dt.year and parsed_dt <= reference_date + datetime.timedelta(days=1):
                    return parsed_dt.isoformat()
            except (ValueError, TypeError, OverflowError, OSError):
                pass
        parsed = _parse_relative_date(str(raw), today=reference_date)
        if parsed:
            try:
                parsed_date = datetime.date.fromisoformat(parsed)
                if parsed_date <= reference_date + datetime.timedelta(days=1):
                    return parsed
            except ValueError:
                pass
        text = str(raw)
        m = re.search(r'(?<!\d)(20\d{2})[/_-](\d{1,2})[/_-](\d{1,2})(?!\d)', text)
        if m:
            try:
                return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
            except ValueError:
                pass
        m = re.search(r'(?<!\d)(\d{2})(\d{2})(\d{2})(?=\D*(?:s?html?|$))', text, re.I)
        if m:
            try:
                year = 2000 + int(m.group(1))
                parsed_date = datetime.date(year, int(m.group(2)), int(m.group(3)))
                # YYMMDD is a weak signal: only trust it when the run is a
                # date-shaped path/file segment, never when it sits inside an
                # id-bearing segment (space.bilibili.com/<uid>/article/251231.html
                # decoded to 2025-12-31, and "第251231号" to the same date).
                # Require a non-digit delimiter before the run AND that the run
                # is not preceded by an id-ish path segment marker.
                if year <= reference_date.year and parsed_date <= reference_date and _yymmdd_segment_is_datelike(text, m):
                    return parsed_date.isoformat()
            except ValueError:
                pass
    return ''


def fetch_publication_date(url: str, platform: str, timeout: int = 15) -> str:
    """Fetch explicit platform publication metadata; never use collection time."""
    if not url:
        return ''
    try:
        import urllib.request
        if platform == 'wechat' and 'mp.weixin.qq.com' in url:
            wechat_url = url + ('&scene=1' if '?' in url else '?scene=1')
            req = urllib.request.Request(wechat_url, headers={
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; WeChat) AppleWebKit/537.36 MicroMessenger/8.0',
            })
            raw = urllib.request.urlopen(req, timeout=timeout).read(4_000_000).decode('utf-8', 'ignore')
            m = re.search(r"ori_create_time:\s*['\"]?(\d{10,13})", raw)
            if m:
                return extract_publication_date({'created_at': m.group(1)})
            m = re.search(r"create_time:\s*['\"](20\d{2}-\d{2}-\d{2})", raw)
            if m:
                return m.group(1)
            # var ct = "1755000000" — epoch timestamp embedded as page var
            m = re.search(r'var\s+ct\s*=\s*["\']?(\d{10})', raw)
            if m:
                got = extract_publication_date({'created_at': m.group(1)})
                if got:
                    return got
            # <em id="publish_time">2026-01-01</em> — rendered publish time span
            m = re.search(r'id="publish_time"[^>]*>\s*(20\d{2}-\d{2}-\d{2})', raw)
            if m:
                return m.group(1)
            # og:article:published_time meta (WeChat sometimes carries this)
            m = re.search(r'property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)', raw, re.I)
            if m:
                parsed = extract_publication_date({'date': m.group(1)})
                if parsed:
                    return parsed
        if platform == 'bilibili' and 'bilibili.com' in url:
            bv_match = re.search(r'(BV[a-zA-Z0-9]+)', url)
            if bv_match:
                api_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bv_match.group(1)}'
                req = urllib.request.Request(api_url, headers={
                    'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com/',
                })
                data = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'ignore'))
                pubdate = data.get('data', {}).get('pubdate') or data.get('data', {}).get('ctime')
                if pubdate:
                    return extract_publication_date({'created_at': pubdate})
        if platform == 'weibo':
            status_id = ''
            for pattern in (
                r'm\.weibo\.cn/(?:detail|status)/([0-9A-Za-z]+)',
                r'weibo\.com/[^/\s]+/(?:status/)?([0-9A-Za-z]+)$',
            ):
                m = re.search(pattern, url.rstrip('/'))
                if m:
                    status_id = m.group(1)
                    break
            if status_id:
                cookies = {}
                cookie_file = Path('/root/.hermes/weibo_cookies.txt')
                if cookie_file.exists():
                    for line in cookie_file.read_text(encoding='utf-8', errors='ignore').splitlines():
                        line = line.strip()
                        if line.startswith('#HttpOnly_'):
                            line = line[10:]
                        parts = line.split('\t')
                        if len(parts) >= 7:
                            cookies[parts[5]] = parts[6]
                headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://weibo.com/'}
                if cookies:
                    headers['Cookie'] = '; '.join(f'{k}={v}' for k, v in cookies.items())
                try:
                    req = urllib.request.Request(f'https://weibo.com/ajax/statuses/show?id={status_id}', headers=headers)
                    data = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'ignore'))
                    post = data.get('data', data)
                    got = extract_publication_date({'created_at': post.get('created_at', '')})
                    if got:
                        return got
                except Exception:
                    pass
                # Fallback: m.weibo.cn detail page embeds a JSON blob with created_at
                # (Sina Visitor System may block, but try once without cookie too).
                try:
                    detail_req = urllib.request.Request(
                        f'https://m.weibo.cn/detail/{status_id}',
                        headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'},
                    )
                    dr = urllib.request.urlopen(detail_req, timeout=timeout).read(200000).decode('utf-8', 'ignore')
                    m = re.search(r'"created_at"\s*:\s*"([^"]+)"', dr)
                    if m:
                        got = extract_publication_date({'created_at': m.group(1)})
                        if got:
                            return got
                except Exception:
                    pass
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        raw = urllib.request.urlopen(req, timeout=timeout).read(512000).decode('utf-8', 'ignore')
        for pattern in (
            r'property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)',
            r'name=["\']pubdate["\'][^>]+content=["\']([^"\']+)',
            r'itemprop=["\']datePublished["\'][^>]+content=["\']([^"\']+)',
            # JSON-LD structured data: "datePublished": "2026-01-01..."
            r'"datePublished"\s*:\s*"([^"]+)"',
            # <time datetime="2026-01-01..."> HTML5 element
            r'<time[^>]+datetime=["\']([^"\']+)',
            r'(20\d{2}[.\-/年]\d{1,2}[.\-/月]\d{1,2})',
            # MM月DD日 without year (Chinese feed snippets) — via _parse_relative_date
            r'(\d{1,2}月\d{1,2}日)',
        ):
            m = re.search(pattern, raw, re.I)
            if m:
                parsed = extract_publication_date({'date': m.group(1)})
                if parsed:
                    return parsed
    except Exception:
        pass
    return ''


# Freshness windows per material policy. A KOL *viewpoint* radar is not a
# breaking-news feed: a commentary piece keeps reference value across the
# current content cycle, so a single 7/30-day cutoff evicted every dated item
# and produced NO_FRESH_DATED while genuinely expired 2022/2023 material still
# has to be dropped. Tunable via KEWU_KOL_FRESHNESS_DAYS_<POLICY>.
KOL_FRESHNESS_WINDOW_DAYS = {
    'PLATFORM_SIGNAL': 365,
    'DISCOVERY_ONLY': 270,
}
KOL_FRESHNESS_DEFAULT_DAYS = 270


def kol_freshness_window_days(policy: str) -> int:
    """Resolve the freshness window for a material policy (env-overridable)."""
    key = (policy or '').strip().upper()
    env = os.getenv(f'KEWU_KOL_FRESHNESS_DAYS_{key}') if key else None
    if env and env.strip().isdigit():
        return int(env.strip())
    return KOL_FRESHNESS_WINDOW_DAYS.get(key, KOL_FRESHNESS_DEFAULT_DAYS)


def is_stale_kol_item(
    item: dict,
    max_age_days: int | None = None,
    today: datetime.date | None = None,
) -> tuple[bool, str]:
    """Check freshness. Returns (is_stale, reason_tag).

    Rules:
      1. Has published_at → year at least 2 behind → DATE_OLD_YEAR;
         else age > policy window → STALE_KOL_ARTICLE.
         PLATFORM_SIGNAL from the prior calendar year stays in the approved
         content-cycle window (date_sense TF-3) even when day-count is large.
      2. No published_at but evidence has year clue (e.g. "2024年", "2025年")
         and year is at least 2 years behind → DATE_OLD_YEAR
      3. No date at all → DATE_UNKNOWN (not stale, but lower confidence)

    max_age_days defaults to the policy-derived viewpoint window
    (see KOL_FRESHNESS_WINDOW_DAYS); pass an explicit value to override.
    """
    pub = (item.get('published_at') or '').strip()
    evidence = (item.get('evidence') or '') + ' ' + (item.get('title') or '')
    reference_date = today or datetime.date.today()
    policy = (item.get('material_policy') or '').strip().upper()
    if max_age_days is None:
        max_age_days = kol_freshness_window_days(policy)

    # Try published_at first
    if pub:
        parsed = _parse_relative_date(pub, today=reference_date)
        if not parsed:
            # try raw ISO
            parsed = pub[:10] if re.match(r'20\d{2}-\d{2}-\d{2}', pub) else ''
        if parsed:
            try:
                pub_date = datetime.date.fromisoformat(parsed)
                # Truly old calendar years first (2023 in 2026). Ordering age
                # before the year guard previously marked in-cycle 2025 material
                # STALE_KOL_ARTICLE and produced NO_FRESH_DATED.
                if pub_date.year < reference_date.year - 1:
                    return True, 'DATE_OLD_YEAR'
                # Approved viewpoint cycle: prior-year eligible policies stay.
                if policy in ('PLATFORM_SIGNAL', 'DISCOVERY_ONLY') and pub_date.year == reference_date.year - 1:
                    return False, ''
                age = (reference_date - pub_date).days
                if age > max_age_days:
                    return True, 'STALE_KOL_ARTICLE'
            except (ValueError, TypeError):
                pass

    # Scan evidence/title for year clues
    year_matches = re.findall(r'(20\d{2})年', evidence)
    if year_matches:
        max_old_year = max(int(y) for y in year_matches)
        # P0 fix (2026-08-10): only mark DATE_OLD_YEAR when year is at least 2 years behind today.
        # A 2025 item collected in 2026 is still within the current content-cycle window.
        if max_old_year < reference_date.year - 1:
            return True, 'DATE_OLD_YEAR'

    # No date info at all
    if not pub:
        return False, 'DATE_UNKNOWN'

    return False, ''


# Weibo hot/aggregator shells are event roll-up pages, not single posts, so they
# carry no single publication timestamp by construction. They must leave the
# eligible pool (ARCHIVE_WITH_REASON / WEIBO_AGGREGATOR_PAGE) rather than inflate
# DATE_UNKNOWN_RATIO as fake metadata misses.
WEIBO_AGGREGATOR_URL_PATTERNS = (
    r'weibo\.com/a/hot/',
    r'm\.s\.weibo\.com/zhisou',
    r's\.weibo\.com/(?:top|weibo|hot)',
)
AGGREGATOR_FAILURE_TAG = 'WEIBO_AGGREGATOR_PAGE'


def is_aggregator_url(url: str) -> bool:
    """True for platform roll-up/search shells that have no single pub date."""
    u = (url or '').strip().lower()
    if not u:
        return False
    return any(re.search(p, u) for p in WEIBO_AGGREGATOR_URL_PATTERNS)


def date_unknown_failure_tag(item: dict) -> str:
    """Classify *why* a date is missing so diagnostics stay actionable.

    Aggregator URLs are handled by apply_kol_item_gates (demoted out of
    eligible) and must not reach this helper as an eligible DATE_UNKNOWN.
    """
    body_status = (item.get('body_status') or '').strip()
    if is_aggregator_url(item.get('url', '')):
        return AGGREGATOR_FAILURE_TAG
    if body_status == 'truncated_by_budget':
        return 'DATE_UNKNOWN_BODY_TRUNCATED'
    if body_status in ('fetch_fail', 'skipped_domain_mismatch'):
        return 'DATE_UNKNOWN_BODY_FETCH_FAIL'
    if body_status == 'skipped_non_article':
        return 'DATE_UNKNOWN_NON_ARTICLE'
    if body_status in ('fetched', 'excerpt_only'):
        return 'DATE_UNKNOWN_NO_METADATA'
    return 'DATE_UNKNOWN'


def backfill_platform_metadata_date(item: dict, timeout: int = 8) -> str:
    """Bounded metadata-only date fetch for budget-truncated bodies.

    Pulls only explicit platform metadata (wechat ori_create_time / create_time,
    weibo created_at). Never uses collection/run timestamps. Returns '' when
    metadata is inaccessible — callers must leave published_at empty rather than invent.
    """
    if (item.get('published_at') or '').strip():
        return ''
    platform = (item.get('platform') or '').strip()
    url = (item.get('url') or '').strip()
    body_status = (item.get('body_status') or '').strip()
    # Only when body capture was interrupted or never produced evidence for
    # extract_publication_date — full 'fetched' already ran fetch_publication_date.
    if body_status not in ('truncated_by_budget', 'excerpt_only', 'fetch_fail'):
        return ''
    # WeChat: ori_create_time / create_time / var ct / publish_time
    if platform == 'wechat' and 'mp.weixin.qq.com' in url:
        # Normalize scheme; WeChat search hits often arrive as http:// and some
        # edges reset those while https serves ori_create_time reliably.
        if url.startswith('http://mp.weixin.qq.com'):
            url = 'https://' + url[len('http://'):]
        got = fetch_publication_date(url, 'wechat', timeout=timeout)
        if got:
            return got
        # One bounded retry for transient resets; still never invent a date.
        return fetch_publication_date(url, 'wechat', timeout=timeout)
    # Weibo: ajax statuses/show / m.weibo.cn detail created_at
    if platform == 'weibo' and ('weibo.com' in url or 'weibo.cn' in url):
        if is_aggregator_url(url):
            return ''
        got = fetch_publication_date(url, 'weibo', timeout=timeout)
        if got:
            return got
        return fetch_publication_date(url, 'weibo', timeout=timeout)
    return ''


def run_cmd(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'TIMEOUT'
    except Exception as e:
        return -2, '', repr(e)


def score_item(account: str, platform: str, hit: dict) -> int:
    text = (hit.get('title', '') + ' ' + hit.get('body', '') + ' ' + hit.get('url', '')).lower()
    s = 0
    if account.lower() in text:
        s += 3
    if platform in hit.get('url', ''):
        s += 1
    if any(k in text for k in SIGNAL_KW):
        s += 2
    if any(t in text for t in NOISE_TERMS):
        s -= 5
    return s


# ══════════════════════════════════════════
#  A. URL Discovery — 多路由
# ══════════════════════════════════════════

def discover_anysearch(query: str, max_results: int = 3, timeout: int = 20) -> list[dict]:
    """AnySearch CLI — 本地API, ~1-3s, 最稳定。"""
    if not ANYSEARCH_CLI.exists():
        return []
    rc, out, err = run_cmd(
        [sys.executable, str(ANYSEARCH_CLI), 'search', query, '--max_results', str(max_results)],
        timeout=timeout,
    )
    if rc != 0 or not out.strip():
        return []
    hits = []
    # parse CLI text output: each result has ### N. title + - **URL**: ... + - > excerpt
    blocks = re.split(r'### \d+\.', out)
    for blk in blocks[1:]:
        lines = blk.strip().splitlines()
        title = lines[0].strip() if lines else ''
        url_m = re.search(r'\*\*URL\*\*:\s*(\S+)', blk)
        url = url_m.group(1) if url_m else ''
        body_lines = [l.lstrip('- > ').strip() for l in lines if l.strip().startswith('- >')]
        body = ' '.join(body_lines)[:300]
        if url:
            hits.append({'title': title, 'url': url, 'body': body})
    return hits


def discover_collect_web_search(query: str, platform: str, max_items: int = 3, timeout: int = 30) -> list[dict]:
    """collect_web --source <platform>_search / anysearch 路由。"""
    source_map = {
        'wechat': 'wechat_search',
        'bilibili': 'anysearch',   # bili API需cookie，先用anysearch site:
        'weibo': 'anysearch',      # weibo同理
        'zhihu': 'anysearch',
    }
    source = source_map.get(platform, 'anysearch')
    url_arg = query  # collect_web --url 接受query字符串
    if platform in ('bilibili', 'weibo', 'zhihu'):
        site_map = {'bilibili': 'bilibili.com', 'weibo': 'weibo.com', 'zhihu': 'zhihu.com'}
        url_arg = f'site:{site_map[platform]} {query}'
    cmd = [sys.executable, str(COLLECT_WEB), '--source', source, '--url', url_arg, '--max-items', str(max_items)]
    rc, out, err = run_cmd(cmd, timeout=timeout)
    if rc != 0 or not out.strip():
        return []
    try:
        data = json.loads(out.strip())
    except json.JSONDecodeError:
        return []
    hits = []
    for item in data.get('data', []):
        url = item.get('url', '')
        title = item.get('title', item.get('source', ''))
        body = item.get('body', item.get('excerpt', ''))
        if url:
            hits.append({'title': title or '', 'url': url, 'body': body or ''})
    return hits


def discover_bilibili_site_search(query: str, max_results: int = 3, timeout: int = 20) -> list[dict]:
    """B站站内搜索fallback。用于KOL标题热点，弥补AnySearch/ddgs不稳定。"""
    import urllib.parse, urllib.request, re as _re
    url = 'https://search.bilibili.com/all?keyword=' + urllib.parse.quote(query)
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com/',
        })
        html = urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'ignore')
    except Exception:
        return []
    hits = []
    seen = set()
    # Prefer direct video links embedded in search HTML.
    for m in _re.finditer(r'(?:https?:)?//www\.bilibili\.com/video/(BV[0-9A-Za-z]+)', html):
        bvid = m.group(1)
        if bvid in seen:
            continue
        seen.add(bvid)
        hits.append({'title': query, 'url': f'https://www.bilibili.com/video/{bvid}/', 'body': ''})
        if len(hits) >= max_results:
            break
    return hits


def discover_ddgs(query: str, max_results: int = 3, timeout: int = 8) -> list[dict]:
    """ddgs fallback — 从进程内直接调用，不spawn子进程。"""
    try:
        from ddgs import DDGS
        hits = []
        with DDGS(timeout=timeout) as d:
            for r in d.text(query, max_results=max_results):
                hits.append({
                    'title': r.get('title', ''),
                    'url': r.get('href') or r.get('url', ''),
                    'body': r.get('body', ''),
                })
        return hits
    except Exception:
        return []





def _resolve_weibo_uid(name: str, cookie_str: str) -> str:
    """Resolve weibo username to UID via s.weibo.com user search."""
    import urllib.request, urllib.parse
    UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    q = urllib.parse.quote(name)
    url = f'https://s.weibo.com/user?q={q}&Refer=weibo_user'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': UA, 'Cookie': cookie_str,
            'Accept': 'text/html', 'Referer': 'https://weibo.com/',
        })
        resp = urllib.request.urlopen(req, timeout=15)
        raw = resp.read().decode('utf-8', 'ignore')
        uids = re.findall(r'/u/(\d{8,12})', raw)
        if uids:
            for uid in dict.fromkeys(uids):
                api = f'https://weibo.com/ajax/profile/info?uid={uid}'
                req2 = urllib.request.Request(api, headers={
                    'User-Agent': UA, 'Cookie': cookie_str,
                    'Referer': f'https://weibo.com/u/{uid}',
                })
                try:
                    resp2 = urllib.request.urlopen(req2, timeout=8)
                    data = json.loads(resp2.read().decode('utf-8', 'ignore'))
                    user = data.get('data', {}).get('user', {})
                    screen_name = user.get('screen_name', '')
                    followers = user.get('followers_count', 0)
                    if (name in screen_name or screen_name in name) and followers > 10000:
                        return uid
                except Exception:
                    continue
    except Exception:
        pass
    return ''

def discover_weibo_mobile(query: str, max_results: int = 3, timeout: int = 20) -> list[dict]:
    """Weibo desktop API (weibo.com/ajax) with cookie. Returns actual post URLs."""
    import urllib.request, urllib.parse
    cookie_file = Path('/root/.hermes/weibo_cookies.txt')
    if not cookie_file.exists():
        return []
    cookies = {}
    for line in cookie_file.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = line.strip()
        if not line or (line.startswith('#') and not line.startswith('#HttpOnly_')):
            continue
        if line.startswith('#HttpOnly_'):
            line = line[10:]
        parts = line.split('\t')
        if len(parts) >= 7:
            cookies[parts[5]] = parts[6]
    if not cookies:
        return []
    cookie_str = '; '.join(f'{k}={v}' for k, v in cookies.items())
    # Known UIDs for watchlist accounts
    uid_map = {
        '沈逸': '1157864602', '差评君': '5734325998',
        '高志凯': '7795630224',
    }
    uid = ''
    for name, id_ in uid_map.items():
        if name in query:
            uid = id_
            break
    if not uid:
        m = re.search(r'(\d{8,12})', query)
        if m:
            uid = m.group(1)
    if not uid:
        name_match = re.match(r'(\S+?)(?:\s|$)', query)
        if name_match:
            uid = _resolve_weibo_uid(name_match.group(1), cookie_str)
    if not uid:
        return []
    api = f'https://weibo.com/ajax/statuses/mymblog?uid={uid}&page=1&feature=0'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie_str,
        'Referer': f'https://weibo.com/u/{uid}',
    }
    try:
        req = urllib.request.Request(api, headers=headers)
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw = resp.read().decode('utf-8', 'ignore')
        data = json.loads(raw)
    except Exception:
        return []
    hits = []
    for post in (data.get('data', {}).get('list', [])):
        mid = post.get('mid', '')
        if not mid:
            continue
        text = post.get('text_raw', '') or re.sub(r'<[^>]+>', '', post.get('text', ''))
        url = f'https://m.weibo.cn/detail/{mid}'
        hits.append({
            'title': text[:120], 'url': url, 'body': text[:500],
            'published_at': post.get('created_at', ''),
        })
        if len(hits) >= max_results:
            break
    return hits


def discover_for_account(account: dict, platform: str, timeout_sec: int, limit_per_platform: int = 3) -> list[dict]:
    """对单个account+platform，多路由发现URL。"""
    name = account['name']
    raw_kws = account.get('keywords', [])
    # 2026-06-28: KOL漏抓纠偏。B站/微博热点常由新增关键词命中，不能只取前2个老关键词。
    # 仍限制总数，避免query过宽/过长。
    kw_limit = 8 if platform in ('bilibili', 'weibo') else 4
    kws = raw_kws[:kw_limit]
    # 清理query：去重复词、特殊字符
    kw_str = ' '.join(dict.fromkeys(kws))  # 去重保序
    site_map = {
        'wechat': 'mp.weixin.qq.com',
        'bilibili': 'bilibili.com',
        'weibo': 'weibo.com',
        'zhihu': 'zhihu.com',
    }
    site = site_map.get(platform, '')
    base_q = f'site:{site} {name} {kw_str} {TODAY[:4]}' if site else f'{name} {kw_str} {TODAY[:4]}'
    base_q = re.sub(r'[/／]', ' ', base_q).strip()  # 去斜杠
    base_q = re.sub(r'\s+', ' ', base_q)  # 合并空格

    all_hits = []
    seen_urls = set()

    def _add(hits: list[dict], route: str):
        for h in hits:
            u = h.get('url', '')
            if u and u not in seen_urls:
                seen_urls.add(u)
                h['_route'] = route
                all_hits.append(h)

    # Route 0: explicit Bilibili space from watchlist (most reliable for fixed UP)
    if platform == 'bilibili' and account.get('bilibili_space'):
        try:
            space_url = account['bilibili_space'].rstrip('/') + '/video'
            rc, out, err = run_cmd([
                'yt-dlp', '--no-update', '--cookies', '/root/.hermes/bilibili_cookies.txt',
                '--user-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
                '--referer', account['bilibili_space'].rstrip('/') + '/',
                '--flat-playlist', '--dump-json', '--playlist-end', str(limit_per_platform), space_url
            ], timeout=60)
            if rc == 0 and out.strip():
                space_hits = []
                for line in out.splitlines():
                    try:
                        meta = json.loads(line)
                    except Exception:
                        continue
                    bv = meta.get('id') or ''
                    if bv.startswith('BV'):
                        space_hits.append({'title': meta.get('title') or f'{name} B站视频 {bv}', 'url': f'https://www.bilibili.com/video/{bv}/', 'body': ''})
                _add(space_hits, 'bilibili_space_yt_dlp')
        except Exception:
            pass

    # Route 1: collect_web platform-aware (wechat_search最优先)
    if platform == 'wechat':
        cw_hits = discover_collect_web_search(f'{name} {" ".join(kws)}', 'wechat', limit_per_platform, 30)
        _add(cw_hits, 'collect_web_wechat_search')

    # Route 1b: Weibo mobile search API (weibo only, needs cookie)
    if platform == 'weibo':
        wb_hits = discover_weibo_mobile(f'{name} {" ".join(kws)}', limit_per_platform, 20)
        _add(wb_hits, 'weibo_mobile_api')

    # Route 2: AnySearch
    as_query = f'site:{site} {name} {" ".join(kws)}' if site else f'{name} {" ".join(kws)}'
    as_query = re.sub(r'[/／]', ' ', as_query).strip()
    as_hits = discover_anysearch(as_query, limit_per_platform, 20)
    _add(as_hits, 'anysearch')

    # Route 2a: Bilibili site search for each high-value keyword. AnySearch often misses fresh B站 videos.
    if platform == 'bilibili' and kws:
        for kw in kws[:8]:
            bq = f'{name} {kw}'
            bi_hits = discover_bilibili_site_search(bq, limit_per_platform, 20)
            _add(bi_hits, 'bilibili_site_search')

    # Route 2b: Filter out off-domain URLs (anysearch may return cross-platform results)
    weibo_domains = ('weibo.com', 'm.weibo.cn', 'weibo.cn', 'h5.video.weibo.com')
    if platform == 'weibo':
        all_hits = [h for h in all_hits if any(d in h.get('url', '') for d in weibo_domains)]
    elif site:
        site_clean = site.replace('www.', '')
        all_hits = [h for h in all_hits if site_clean in h.get('url', '')]

    # Route 3: ddgs fallback (only if still < 1 result)
    if len(all_hits) < 1:
        ddgs_hits = discover_ddgs(base_q, limit_per_platform, timeout_sec)
        _add(ddgs_hits, 'ddgs')

    return all_hits[:limit_per_platform]


# ══════════════════════════════════════════
#  B. Body Fetch — 平台感知正文抓取
# ══════════════════════════════════════════

# ── 微博公开正文（游客态，无需登录 Cookie）──
# 根因（2026-08-13 sidecar PARTIAL）：weibo.com/ajax/statuses/show 必须登录态，
# 无 Cookie 或 Cookie 过期时回 {"ok":-100, url: login.php}；裸请 m.weibo.cn 会 302 到
# visitor.passport.weibo.cn 的 Sina Visitor System 壳页。修复路线：先走 passport
# genvisitor/incarnate 换游客 SUB/SUBP，再打 m.weibo.cn 公开 JSON 接口。
_WEIBO_GUEST_UA = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 '
    '(KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
)
_WEIBO_GUEST_TTL = 1800
_weibo_guest_cache: dict = {'opener': None, 'ts': 0.0}
# 视觉壳/提示文本，命中即判非正文（不得当正文回传）
_WEIBO_SHELL_MARKERS = (
    'Sina Visitor System', '新浪通行证', '微博登录', '展开全文c', 'Weibo.com',
)


def _weibo_guest_opener(force: bool = False):
    """返回带游客 Cookie 的 urllib opener；失败返回 None。不落盘、不读用户凭据。"""
    import http.cookiejar, urllib.request, urllib.parse
    now = time.time()
    if (not force and _weibo_guest_cache['opener'] is not None
            and now - _weibo_guest_cache['ts'] < _WEIBO_GUEST_TTL):
        return _weibo_guest_cache['opener']
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    fp = json.dumps({
        'os': '1', 'browser': 'Safari16,0,0,0', 'fonts': 'undefined',
        'screenInfo': '390*844*24', 'plugins': '',
    })
    try:
        req = urllib.request.Request(
            'https://passport.weibo.com/visitor/genvisitor',
            data=urllib.parse.urlencode({'cb': 'gen_callback', 'fp': fp}).encode(),
            headers={
                'User-Agent': _WEIBO_GUEST_UA,
                'Referer': 'https://passport.weibo.com/visitor/visitor',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        )
        raw = opener.open(req, timeout=15).read().decode('utf-8', 'ignore')
        tid_m = re.search(r'"tid":"([^"]+)"', raw)
        if not tid_m:
            return None
        inc = (
            'https://passport.weibo.com/visitor/visitor?a=incarnate&t='
            + urllib.parse.quote(tid_m.group(1))
            + '&w=2&c=095&gc=&cb=cross_domain&from=weibo&_rand=' + str(time.time())
        )
        opener.open(urllib.request.Request(inc, headers={
            'User-Agent': _WEIBO_GUEST_UA,
            'Referer': 'https://passport.weibo.com/visitor/visitor',
        }), timeout=15).read()
    except Exception:
        return None
    if not any(c.name in ('SUB', 'SUBP') for c in jar):
        return None
    _weibo_guest_cache['opener'] = opener
    _weibo_guest_cache['ts'] = now
    return opener


def _weibo_clean_text(raw_html: str) -> str:
    """微博 text 字段（含 <a>/<br>/表情 img）转纯文本。"""
    import html as html_mod
    t = re.sub(r'<br\s*/?>', '\n', raw_html or '')
    t = re.sub(r'<img[^>]*alt=["\']?([^"\'>\s]*)["\']?[^>]*>', r'\1', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = html_mod.unescape(t)
    t = re.sub(r'[ \t\u3000]+', ' ', t)
    return re.sub(r'\n{3,}', '\n\n', t).strip()


def _weibo_extract_mid(url: str) -> str:
    """从各种微博 URL 形态提取 base62 mid / 数字 id；取不到返回 ''。"""
    for pat in (
        r'h5\.video\.weibo\.com/show/\d+:([0-9A-Za-z]+)',
        r'm\.weibo\.cn/(?:detail|status)/([0-9A-Za-z]+)',
        r'weibo\.com/(?:\d+|u/\d+|[A-Za-z0-9_\-]+)/status(?:es)?/([0-9A-Za-z]+)',
        r'weibo\.com/\d+/([0-9A-Za-z]{9,})(?:[/?#]|$)',
        r'weibo\.com/[A-Za-z0-9_\-]+/([0-9A-Za-z]{9,})(?:[/?#]|$)',
    ):
        m = re.search(pat, url)
        if m:
            return m.group(1)
    tail = url.split('?')[0].split('#')[0].rstrip('/').split('/')[-1]
    if re.fullmatch(r'[0-9A-Za-z]{9,}', tail) and not tail.isdigit():
        return tail
    if re.fullmatch(r'\d{16,}', tail):
        return tail
    return ''


def _weibo_guest_body(mid: str, timeout: int = 20) -> tuple[str, str]:
    """m.weibo.cn 游客态取公开微博正文。返回 (text, failure_tag)。

    失败分类精确到原因：作者设置不可见 / 已删除 / 需登录 / 接口异常 / 正文过短。
    """
    import urllib.request
    if not mid:
        return '', 'WEIBO_NO_STATUS_ID'
    opener = _weibo_guest_opener()
    if opener is None:
        return '', 'WEIBO_GUEST_TOKEN_FAIL'

    def _api(path: str) -> tuple[dict, str]:
        req = urllib.request.Request(
            f'https://m.weibo.cn{path}',
            headers={
                'User-Agent': _WEIBO_GUEST_UA,
                'Referer': 'https://m.weibo.cn/',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'X-Requested-With': 'XMLHttpRequest',
                'MWeibo-Pwa': '1',
            },
        )
        try:
            resp = opener.open(req, timeout=min(timeout, 20))
            raw = resp.read(400000).decode('utf-8', 'ignore')
        except Exception as exc:
            return {}, 'WEIBO_HTTP_ERROR|' + type(exc).__name__
        if 'Sina Visitor System' in raw or '<html' in raw[:200].lower():
            return {}, 'WEIBO_GUEST_REDIRECT_LOGIN'
        try:
            return json.loads(raw), ''
        except json.JSONDecodeError:
            return {}, 'WEIBO_JSON_DECODE_FAIL'

    data, tag = _api(f'/statuses/show?id={mid}')
    if tag:
        return '', tag
    if not data.get('ok'):
        errno = str(data.get('errno') or '')
        if errno == '20170':
            return '', 'WEIBO_AUTHOR_RESTRICTED'
        if errno in ('20101', '20003'):
            return '', 'WEIBO_POST_DELETED'
        return '', 'WEIBO_API_NOT_OK|errno=' + (errno or 'unknown')
    d = data.get('data') or {}
    text = _weibo_clean_text(d.get('text', ''))
    if d.get('isLongText') and d.get('id'):
        ext, ext_tag = _api(f'/statuses/extend?id={d["id"]}')
        if not ext_tag and ext.get('ok'):
            long_text = _weibo_clean_text(
                (ext.get('data') or {}).get('longTextContent', ''))
            if len(long_text) > len(text):
                text = long_text
    # 转发微博：原文才是正文主体，拼接后一起判定
    rt = d.get('retweeted_status') or {}
    if rt:
        rt_text = _weibo_clean_text(rt.get('text', ''))
        if rt_text:
            text = (text + '\n【转发原文】' + rt_text).strip()
    if not text:
        return '', 'WEIBO_EMPTY_TEXT'
    if any(mk in text for mk in _WEIBO_SHELL_MARKERS):
        return '', 'WEIBO_SHELL_TEXT_ONLY'
    if not evidence_is_body(text):
        return '', f'WEIBO_BODY_TOO_SHORT|len={len(text)}'
    return text, ''


def fetch_body(url: str, platform: str, timeout: int = 30) -> tuple[str, str]:
    """返回 (body_snippet[:500], failure_tag or '')."""
    if not url:
        return '', 'NO_URL'

    # ── 微信铁律：collect_web --source wechat + light_crawler fallback ──
    if 'mp.weixin.qq.com' in url:
        rc, out, err = run_cmd(
            [sys.executable, str(COLLECT_WEB), '--source', 'wechat', '--url', url],
            timeout=timeout,
        )
        if rc == 0 and out.strip():
            try:
                data = json.loads(out.strip())
                _item = data.get('data', [{}])[0] if data.get('data') else {}
                body = _item.get('body', '') or _item.get('text', '')
                if body and len(body) > 50:
                    return body[:500], ''
                # partial: got metadata but body restricted
                if data.get('status') == 'partial':
                    meta_title = data.get('meta', {}).get('title', '')
                    if meta_title and meta_title != '微信文章':
                        return meta_title[:500], 'BODY_RESTRICTED_META_ONLY'
            except (json.JSONDecodeError, IndexError):
                pass
        # Fallback: light_crawler with browser mode
        try:
            script = Path('/root/.hermes/skills/research/web-data-collection-suite/scripts/light_crawler.py')
            if script.exists():
                rc2, out2, err2 = run_cmd(
                    [sys.executable, str(script), url, '--mode', 'browser'],
                    timeout=25,
                )
                if rc2 == 0 and out2.strip():
                    try:
                        data2 = json.loads(out2.strip())
                    except json.JSONDecodeError:
                        data2 = {}
                    if data2.get('data'):
                        _d = data2['data']
                        _d0 = _d[0] if isinstance(_d, list) and _d else (_d if isinstance(_d, dict) else {})
                        body2 = _d0.get('body', '') or _d0.get('text', '') or data2.get('body', '') or data2.get('text', '')
                    else:
                        body2 = data2.get('body', '') or data2.get('text', '')
                    if body2 and len(body2) > 50:
                        return body2[:500], ''
        except Exception:
            pass
        return '', 'WECHAT_FETCH_FAIL'

    # ── B站视频：API → yt-dlp → urllib ──
    bv_match = re.search(r'(BV[a-zA-Z0-9]+)', url)
    if bv_match and 'bilibili.com' in url:
        bvid = bv_match.group(1)
        # Route 1: B站公开API（快，<1s）
        try:
            import urllib.request, json as _json
            api_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
            req = urllib.request.Request(api_url, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com/',
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                api_data = _json.loads(resp.read())
                if api_data.get('code') == 0:
                    d = api_data['data']
                    parts = []
                    if d.get('title'):
                        parts.append(d['title'])
                    if d.get('desc'):
                        parts.append(d['desc'])
                    # tag API for richer context
                    try:
                        tag_url = f'https://api.bilibili.com/x/tag/archive/tags?bvid={bvid}'
                        tag_req = urllib.request.Request(tag_url, headers={
                            'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com/',
                        })
                        with urllib.request.urlopen(tag_req, timeout=8) as tag_resp:
                            tag_data = _json.loads(tag_resp.read())
                            if tag_data.get('code') == 0:
                                tags = [t.get('tag_name', '') for t in tag_data.get('data', [])[:5]]
                                if tags:
                                    parts.append('标签: ' + '、'.join(tags))
                    except Exception:
                        pass
                    body = ' '.join(parts)
                    if len(body) > 30:
                        return body[:500], ''
        except Exception:
            pass
        # Route 2: yt-dlp metadata（中速，5-15s）
        try:
            rc, out, err = run_cmd(
                ['yt-dlp', '--dump-json', '--no-download', '--socket-timeout', '10', url],
                timeout=25,
            )
            if rc == 0 and out.strip():
                meta = json.loads(out.splitlines()[0])
                parts = []
                if meta.get('title'):
                    parts.append(meta['title'])
                if meta.get('description'):
                    parts.append(meta['description'][:400])
                if meta.get('tags'):
                    parts.append('标签: ' + ', '.join(meta['tags'][:5]))
                body = ' '.join(parts)
                if len(body) > 30:
                    return body[:500], ''
        except Exception:
            pass
        # Route 3: urllib HTML scrape (B站SPA，可能只拿到壳)
        try:
            import urllib.request, html as html_mod
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read(512000).decode('utf-8', errors='ignore')
                # 尝试从 __INITIAL_STATE__ JSON 提取
                m = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*\(function', raw, re.S)
                if m:
                    try:
                        state = json.loads(m.group(1))
                        vid = state.get('videoData', {})
                        parts = []
                        if vid.get('title'):
                            parts.append(vid['title'])
                        if vid.get('desc'):
                            parts.append(vid['desc'])
                        body = ' '.join(parts)
                        if len(body) > 30:
                            return body[:500], ''
                    except Exception:
                        pass
                # fallback: strip tags
                text = re.sub(r'<script[^>]*>.*?</script>', '', raw, flags=re.S|re.I)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.S|re.I)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = html_mod.unescape(text)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 80:
                    return text[:500], ''
        except Exception:
            pass
        cdp_body, cdp_err = social_cdp_visible_text_for_url(url)
        if cdp_body and evidence_is_body(cdp_body):
            return cdp_body[:500], ''
        return '', f'BILIBILI_FETCH_FAIL|{cdp_err}'

    # ── YouTube：yt-dlp → urllib ──
    if 'youtube.com' in url or 'youtu.be' in url:
        try:
            rc, out, err = run_cmd(
                ['yt-dlp', '--dump-json', '--no-download', '--socket-timeout', '10', url],
                timeout=25,
            )
            if rc == 0 and out.strip():
                meta = json.loads(out.splitlines()[0])
                parts = []
                if meta.get('title'):
                    parts.append(meta['title'])
                if meta.get('description'):
                    parts.append(meta['description'][:400])
                body = ' '.join(parts)
                if len(body) > 30:
                    return body[:500], ''
        except Exception:
            pass
        return '', 'YOUTUBE_FETCH_FAIL'

    cdp_platform = _platform_from_url(url)
    if cdp_platform in {'xiaohongshu', 'douyin', 'kuaishou', 'tiktok'}:
        cdp_body, cdp_err = social_cdp_visible_text_for_url(url)
        if cdp_body and evidence_is_body(cdp_body):
            return cdp_body[:500], ''
        return '', cdp_err

    # ── 微博：游客态 m.weibo.cn JSON → cookie 桌面 API → collect_web ──
    # 该分支自闭环：不再落到通用 urllib，避免把 Sina Visitor System 壳页
    # (~3.7KB HTML，strip 后 >50 字符) 误当正文回传。
    if 'weibo.com' in url or 'm.weibo.cn' in url or 'h5.video.weibo.com' in url:
        import urllib.request, urllib.parse
        # 聚合页（weibo.com/a/hot/…）没有单条正文，按既有契约直接给聚合标签
        if is_aggregator_url(url):
            return '', AGGREGATOR_FAILURE_TAG
        _status_id = _weibo_extract_mid(url)
        # Route 0: 游客态公开接口（无需登录 Cookie，优先）
        # 主页/名片页（weibo.com/casc?lpage=…）不含单条 mid，给专用标签便于发现层修 URL
        _wb_tag = 'WEIBO_PROFILE_PAGE_NO_STATUS' if re.search(
            r'weibo\.com/(?:u/\d+|[A-Za-z0-9_\-]+)(?:/)?(?:\?|$)', url) else 'WEIBO_NO_STATUS_ID'
        if _status_id:
            _wb_body, _wb_tag = _weibo_guest_body(_status_id, timeout=min(timeout, 20))
            if _wb_body:
                return _wb_body[:500], ''
        if _status_id:
            # Read cookies
            _cookie_file = Path('/root/.hermes/weibo_cookies.txt')
            _cookies = {}
            if _cookie_file.exists():
                for _line in _cookie_file.read_text(encoding='utf-8', errors='ignore').splitlines():
                    _line = _line.strip()
                    if not _line or (_line.startswith('#') and not _line.startswith('#HttpOnly_')):
                        continue
                    if _line.startswith('#HttpOnly_'):
                        _line = _line[10:]
                    _parts = _line.split('\t')
                    if len(_parts) >= 7:
                        _cookies[_parts[5]] = _parts[6]
            if _cookies:
                _cookie_str = '; '.join(f'{k}={v}' for k, v in _cookies.items())
                # Desktop API: try status detail endpoint
                _api = f'https://weibo.com/ajax/statuses/show?id={_status_id}'
                _headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Cookie': _cookie_str,
                    'Referer': f'https://weibo.com/',
                }
                try:
                    _req = urllib.request.Request(_api, headers=_headers)
                    _resp = urllib.request.urlopen(_req, timeout=20)
                    _raw = _resp.read().decode('utf-8', 'ignore')
                    if '<html' not in _raw.lower():
                        _data = json.loads(_raw)
                        _text = _data.get('data', {}).get('text_raw', '') or re.sub(r'<[^>]+>', '', _data.get('data', {}).get('text', ''))
                        if _text and len(_text) > 30:
                            return _text[:500], ''
                except Exception:
                    pass
        # collect_web fallback
        rc, out, err = run_cmd(
            [sys.executable, str(COLLECT_WEB), '--source', 'weibo', '--url', url],
            timeout=timeout,
        )
        if rc == 0 and out.strip():
            try:
                data = json.loads(out.strip())
                if data.get('data'):
                    _item = data['data'][0] if isinstance(data['data'], list) else data['data']
                    _wb = _weibo_clean_text(_item.get('text', '') or _item.get('body', ''))
                    if (_wb and evidence_is_body(_wb)
                            and not any(mk in _wb for mk in _WEIBO_SHELL_MARKERS)):
                        return _wb[:500], ''
            except (json.JSONDecodeError, IndexError):
                pass
        # 微博分支到此终止：通用 urllib 只会拿到访客壳页，不得冒充正文。
        return '', (_wb_tag or 'BODY_FETCH_FAIL')

    # ── 通用网页：collect_web light → urllib ──
    try:
        rc, out, err = run_cmd(
            [sys.executable, str(COLLECT_WEB), '--source', 'light', '--url', url],
            timeout=timeout,
        )
        if rc == 0 and out.strip():
            data = json.loads(out.strip())
            body = ''
            if data.get('data'):
                body = data['data'][0].get('body', '') if isinstance(data['data'], list) else data['data'].get('body', '')
            if body and len(body) > 30:
                return body[:500], ''
    except Exception:
        pass

    # urllib fallback
    try:
        import urllib.request, html as html_mod
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(512000)
            text = raw.decode('utf-8', errors='ignore')
            # 提取 <article> 或 <main> 内容（优先）
            article = re.search(r'<article[^>]*>(.*?)</article>', text, re.S|re.I)
            if article:
                text = article.group(1)
            else:
                main = re.search(r'<main[^>]*>(.*?)</main>', text, re.S|re.I)
                if main:
                    text = main.group(1)
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.S|re.I)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.S|re.I)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = html_mod.unescape(text)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 50:
                return text[:500], ''
    except Exception:
        pass

    return '', 'BODY_FETCH_FAIL'


# ══════════════════════════════════════════
#  C. 观点推演 / 筛噪（规则层，不调模型）
# ══════════════════════════════════════════

def infer_viewpoint(item: dict) -> str:
    """规则推演：从body+title提取关键词匹配的初步观点标签。"""
    text = (item.get('title', '') + ' ' + item.get('evidence', '')).lower()
    tags = []
    topic_map = {
        'ai': 'AI治理', '人工智能': 'AI治理', '芯片': '半导体产业链',
        '半导体': '半导体产业链', '中美': '中美博弈', '地缘': '地缘政治',
        '科技': '科技前沿', '量子': '量子科技', '航天': '航天探索',
        '出口管制': '贸易管制', '产业链': '产业链重构', '数据安全': '数据安全',
        # P0: 科技突破/航天扩展
        '手术': '科技突破', '机器人': '具身智能/机器人', '首飞': '航天探索',
        '回收': '航天探索', '长征': '航天探索', '运载火箭': '航天探索',
        '商业航天': '航天探索', '重复使用': '航天探索', '活体': '科技突破',
        '精准': '科技突破', '微创': '科技突破', '外骨骼': '具身智能/机器人',
        '仿生': '具身智能/机器人', '具身智能': '具身智能/机器人',
        '可控回收': '航天探索', '垂直返回': '航天探索', '可复用': '航天探索',
        # Domain expansion: 生物
        '基因编辑': '生物科技', '脑机接口': '生物科技', '生物技术': '生物科技',
        '生命科学': '生物科技', '合成生物学': '生物科技', '神经科学': '生物科技',
        # Domain expansion: 航空
        '战斗机': '航空工业', '航空发动机': '航空工业', '六代机': '航空工业',
        'C919': '航空工业', '运20': '航空工业', '无人机': '航空/军事',
        # Domain expansion: 材料
        '超导': '材料科学', '新材料': '材料科学', '碳纤维': '材料科学',
        '纳米': '材料科学', '稀土': '材料科学', '碳基材料': '材料科学',
        # Domain expansion: 能源
        '可控核聚变': '能源前沿', '核聚变': '能源前沿', 'ITER': '能源前沿',
        '储能': '能源前沿', '光伏': '能源前沿', '氢能': '能源前沿', '碳中和': '能源前沿',
        # Domain expansion: 军事
        '导弹': '军事装备', '国防': '军事装备', '军备': '军事装备',
        '航母': '军事装备', '潜艇': '军事装备',
    }
    for kw, tag in topic_map.items():
        if kw in text and tag not in tags:
            tags.append(tag)
    return '|'.join(tags) if tags else '待模型审'


def apply_dyson_archive_gate(it: dict, domain_score: dict) -> None:
    """Dyson relevance gate for platform-commentary discovery items (radar-local).

    This radar only feeds the scorer secondary '*_platform_commentary' items;
    primary-fact cards never pass through here, so this gate cannot weaken them.

    Explicit contract for the no-Dyson-match path:
    - Eligible policy (PLATFORM_SIGNAL/DISCOVERY_ONLY) + no Dyson match →
      ARCHIVE_WITH_REASON with the scorer's explicit reason (default
      NO_DYSON_TREE_MATCH). Dyson matching doubles as the domain-relevance
      gate: viewpoint items that hit no capability node are archived, not
      eligible.
    - Any other re-gate outcome → drop legacy archive_reason. Replayed sidecar
      items can carry a stale reason from a previous run; without the clear, a
      NOISE/DATE_OLD_YEAR item kept 'NO_DYSON_TREE_MATCH' and reported
      contradictory state.
    """
    if it.get('material_policy') in ('PLATFORM_SIGNAL', 'DISCOVERY_ONLY') and not it.get('dyson_tree_matches'):
        it['material_policy'] = 'ARCHIVE_WITH_REASON'
        it['archive_reason'] = domain_score.get('archive_reason') or 'NO_DYSON_TREE_MATCH'
    else:
        it.pop('archive_reason', None)


def material_policy_tag(item: dict) -> str:
    """素材政策：signal强→可入素材池，弱→只留线索。"""
    score = 0
    text = (item.get('title', '') + ' ' + item.get('evidence', '')).lower()
    if item['account'].lower() in text:
        score += 2
    # P0: count keyword hits, not just presence — 2+ hits = strong signal
    kw_hits = sum(1 for k in SIGNAL_KW if k in text)
    if kw_hits >= 2:
        score += 3
    elif kw_hits >= 1:
        score += 2
    if any(t in text for t in NOISE_TERMS):
        score -= 3
    if score >= 3:
        return 'PLATFORM_SIGNAL'
    elif score >= 1:
        return 'DISCOVERY_ONLY'
    else:
        return 'NOISE'


# ══════════════════════════════════════════
#  D. MiroFish Feed Package
# ══════════════════════════════════════════

def _infer_chapter_target(it: dict) -> str:
    text = (it.get('title', '') + ' ' + it.get('evidence', '') + ' ' + it.get('viewpoint_inference', '')).lower()
    if any(k in text for k in ['芯片', '半导体', '出口管制', 'gpu', 'a100', 'h100', '算力']):
        return '芯片/算力封锁线；贸易管制；工业链压力素材'
    if any(k in text for k in ['ai', '人工智能', '数据集', '治理']):
        return 'AI治理与数据资源；智能体/算法基础设施素材'
    if any(k in text for k in ['中美', '关税', '反制', '制裁', '特朗普']):
        return '中美博弈；外部压力与产业动员素材'
    if any(k in text for k in ['航天', '月球', 'space', 'nasa']):
        return '航天/空间工程素材'
    return 'CHAPTER_PREP_ONLY；待G1/G2人工映射'


def _infer_confidence_score(it: dict) -> float:
    # P0: stale items get 0.0
    if it.get('failure_tag') in ('STALE_KOL_ARTICLE', 'DATE_OLD_YEAR'):
        return 0.0
    score = 0.35
    if it.get('body_status') == 'fetched':
        score += 0.25
    if it.get('material_policy') == 'PLATFORM_SIGNAL':
        score += 0.2
    if it.get('published_at'):
        score += 0.1
    if it.get('platform') in ('wechat', 'bilibili', 'weibo', 'zhihu'):
        score += 0.05
    # P0: DATE_UNKNOWN → lower ceiling
    if is_date_unknown_tag(it.get('failure_tag')):
        score = min(score, 0.55)
    return round(min(score, 0.9), 2)


def build_mirofish_package(items: list[dict]) -> dict:
    """将discovery items转为MiroFish入口格式。

    Feed纳入条件：body_status 为 'fetched' 或有 excerpt 的条目
    （evidence >= 15 chars），排除主页/空间页/搜索页和 NOISE。
    """
    cards = []
    for it in items:
        if it.get('material_policy') in ('NOISE', 'ARCHIVE_WITH_REASON'):
            continue
        if not it.get('dyson_tree_matches'):
            continue
        # Feed纳入：body_fetched 或有 excerpt
        _bs = it.get('body_status', '')
        _has_excerpt = bool(it.get('evidence', '') and len(it['evidence']) > 15)
        if _bs == 'fetched':
            pass
        elif _bs == 'excerpt_only' and _has_excerpt:
            pass
        else:
            continue
        # 排除非文章URL（主页/空间/搜索页）
        if is_non_article_url(it.get('url', '')):
            continue
        # Platform-URL domain consistency
        _url = it.get('url', '').lower()
        _plat = it.get('platform', '')
        if _plat == 'weibo' and not any(d in _url for d in ('weibo.com', 'm.weibo.cn')):
            continue
        if _plat == 'wechat' and 'mp.weixin.qq.com' not in _url:
            continue
        if _plat == 'bilibili' and 'bilibili.com' not in _url:
            continue
        if _plat == 'zhihu' and 'zhihu.com' not in _url:
            continue
        cards.append({
            'source_expert': f"{it['account']}@{it['platform']}",
            'source_reference': it.get('url', ''),
            # ── 显式顶层字段（从 discovery item 补齐）──
            'url': it.get('url', ''),
            'source': it.get('account', ''),
            'platform': it.get('platform', ''),
            'title': it.get('title', ''),
            'content_excerpt': it.get('evidence', '')[:300],
            'analysis_angle': it.get('viewpoint_inference', ''),
            'chapter_target': _infer_chapter_target(it),
            'confidence_score': _infer_confidence_score(it),
            'published_at': it.get('published_at', ''),
            'source_route': it.get('source_route', ''),
            'discovery_status': it.get('discovery_status', ''),
            'body_status': _bs,
            'source_nature': it.get('source_nature', 'platform_commentary_discovery_not_primary_fact'),
            'official_crosscheck_required': True,
            'official_crosscheck_status': it.get('official_crosscheck_status', 'REQUIRED_BEFORE_FORMAL_FACT_CARD'),
            'outline_chapter_hits': it.get('outline_chapter_hits', []),
            'dyson_tree_matches': it.get('dyson_tree_matches', []),
        })
    return {
        'created_at': now_iso(),
        'schema_version': 'mirofish_feed_v2',
        'total_cards': len(cards),
        'cards': cards,
    }


# ══════════════════════════════════════════
#  Main
# ══════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description='KOL/平台号观点雷达 v2 — 多路由采集')
    ap.add_argument('--resume', action='store_true', help='从已有discovery.json续跑')
    ap.add_argument('--discovery-json', type=str, default='', help='指定已有discovery json路径')
    ap.add_argument('--timeout-sec', type=int, default=8, help='ddgs单条超时秒数')
    ap.add_argument('--platform', type=str, default='', help='只跑指定平台: wechat/bilibili/weibo/zhihu')
    ap.add_argument('--limit', type=int, default=0, help='只跑前N个account')
    ap.add_argument('--coverage-sweep', action='store_true', help='按九域轮转，每账户优先查询一个平台')
    ap.add_argument('--max-queries', type=int, default=0, help='本轮最大查询骨架数，0为不限制')
    ap.add_argument('--max-runtime-sec', type=int, default=0, help='总运行预算秒数；到点截断后续查询/正文抓取并落盘，0为不限制')
    ap.add_argument('--dry-run-mirofish', action='store_true', help='只产出discovery，不跑MiroFish后段')
    ap.add_argument('--out-dir', type=str, default='', help='输出目录')
    ap.add_argument('--disable-social-cdp', action='store_true', help='禁用本机社媒助手CDP探测/只读补充')
    args = ap.parse_args()
    run_started_monotonic = time.monotonic()
    runtime_truncated = False

    def runtime_budget_exhausted() -> bool:
        return bool(args.max_runtime_sec > 0 and time.monotonic() - run_started_monotonic >= args.max_runtime_sec)
    if args.disable_social_cdp:
        os.environ['KEWU_DISABLE_SOCIAL_CDP'] = '1'

    out_dir = Path(args.out_dir) if args.out_dir else RUN_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    discovery_path = Path(args.discovery_json) if args.discovery_json else out_dir / 'platform_discovery.json'
    mirofish_path = out_dir / 'platform_mirofish_feed_package.json'
    body_report_path = out_dir / 'body_fetch_report.json'
    social_cdp_path = out_dir / 'social_cdp_probe.json'

    social_cdp_report = {'status': 'DISABLED_BY_FLAG'} if args.disable_social_cdp else probe_social_cdp()
    social_cdp_path.write_text(json.dumps(social_cdp_report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # load watchlist (domain-slot v1 or legacy flat format)
    if not WATCH.exists():
        print(f'ERROR: watchlist not found: {WATCH}', file=sys.stderr)
        sys.exit(1)
    watch = json.loads(WATCH.read_text(encoding='utf-8'))

    # Flatten domain-slot format → accounts list with domain_id tag
    if 'domains' in watch:
        accounts = []
        domain_map = {}  # domain_id → list of account names
        for dom in watch['domains']:
            did = dom['domain_id']
            domain_map[did] = []
            for acc in dom['accounts']:
                acc_flat = dict(acc)
                acc_flat['domain_id'] = did
                acc_flat['domain_name'] = dom['domain_name']
                accounts.append(acc_flat)
                domain_map[did].append(acc['name'])
    else:
        # Legacy flat format fallback
        accounts = watch['accounts']
        domain_map = {}

    configured_accounts = list(accounts)
    configured_account_count = len(configured_accounts)
    configured_domain_count = len(domain_map)

    if args.limit > 0:
        accounts = accounts[:args.limit]

    # platform filter
    plat_filter = set()
    if args.platform:
        plat_map = {'wechat': '微信公众号', 'bilibili': 'B站', 'weibo': '微博', 'zhihu': '知乎'}
        plat_filter.add(plat_map.get(args.platform, args.platform))

    # resume / post-segment: load existing items.
    # --discovery-json alone = deterministic post-segment replay (no live
    # discovery). --resume = load then continue collecting.
    existing_items: list[dict] = []
    existing_urls: set[str] = set()
    post_segment = bool(args.discovery_json) and discovery_path.exists() and not args.resume
    if (args.resume or post_segment) and discovery_path.exists():
        try:
            old = json.loads(discovery_path.read_text(encoding='utf-8'))
            existing_items = old.get('items', [])
            existing_urls = {it['url'] for it in existing_items if it.get('url')}
            mode = 'post-segment' if post_segment else 'resume'
            print(f'[{mode}] loaded {len(existing_items)} existing items from {discovery_path}')
        except Exception:
            pass

    # ── A. URL Discovery ──
    all_items: list[dict] = list(existing_items)
    errors: list[dict] = []
    total_queries = 0
    domain_query_counts: dict[str, int] = {}

    query_plan = build_account_query_plan(
        accounts,
        platform_filter=plat_filter,
        coverage_sweep=args.coverage_sweep,
        max_queries=args.max_queries,
    )
    queried_account_names: set[str] = set()
    queried_domain_ids: set[str] = set()

    if post_segment:
        print(f'[post-segment] skip live discovery; re-gate {len(all_items)} items')
        query_plan = []

    for acc, plat_raw, plat in query_plan:
        if runtime_budget_exhausted():
            runtime_truncated = True
            errors.append({'account': '', 'platform': '', 'error': 'RUNTIME_BUDGET_EXHAUSTED_BEFORE_QUERY'})
            break
        name = acc['name']
        total_queries += 1
        queried_account_names.add(name)
        if acc.get('domain_id'):
            queried_domain_ids.add(acc['domain_id'])
            domain_query_counts[acc['domain_id']] = domain_query_counts.get(acc['domain_id'], 0) + 1
        print(f'  [{total_queries}] {name} · {plat} ...', end=' ', flush=True)
        t0 = time.time()
        hits = discover_for_account(acc, plat, args.timeout_sec)
        elapsed = time.time() - t0
        if not hits:
            errors.append({'account': name, 'platform': plat, 'error': 'NO_HITS',
                           'fallback_tried': ['collect_web', 'anysearch', 'ddgs']})
            print(f'0 hits ({elapsed:.1f}s)')
            continue

        found = 0
        for hit in hits:
            url = hit.get('url', '')
            if not url or url in existing_urls:
                continue
            existing_urls.add(url)
            item = dict(EMPTY_ITEM)
            item['account'] = name
            item['platform'] = plat
            item['query'] = hit.get('_route', '')
            item['url'] = url
            item['title'] = hit.get('title', '')
            item['published_at'] = extract_publication_date(hit)
            item['source_route'] = hit.get('_route', 'unknown')
            item['discovery_status'] = 'discovered'
            item['failure_tag'] = ''
            item['domain_id'] = acc.get('domain_id', '')
            item['domain_name'] = acc.get('domain_name', '')
            item['body_status'] = 'pending'
            discovery_body = hit.get('body', '') or ''
            discovery_title = hit.get('title', '') or ''
            if discovery_body and len(discovery_body) > 5:
                item['evidence'] = discovery_body[:500]
            elif discovery_title and 'candidate' not in discovery_title.lower() and len(discovery_title) > 10:
                item['evidence'] = discovery_title[:500]
            else:
                item['evidence'] = ''
            all_items.append(item)
            found += 1
        print(f'{found} new ({elapsed:.1f}s)')

    # ── B. Body Fetch — 所有 pending 项都必须尝试抓正文 ──
    body_report = {
        'created_at': now_iso(),
        'attempts': 0, 'success': 0, 'fail': 0, 'skipped_non_article': 0,
        'by_platform': {}, 'by_failure_tag': {}, 'details': [],
    }
    for it in all_items:
        if it.get('body_status') != 'pending':
            continue
        url = it.get('url', '')
        plat = it.get('platform', '')
        detail = {'url': url, 'platform': plat, 'account': it.get('account', '')}

        # P0 fix (2026-08-10): post-check runtime budget at item start.
        # If budget ran out between items, mark the item explicitly so it
        # never stays in 'pending' — a stale 'pending' body_status is what
        # caused 9 domains-of-results to collapse to 3 in the prior run.
        if runtime_budget_exhausted():
            runtime_truncated = True
            it['body_status'] = 'truncated_by_budget'
            it['failure_tag'] = 'BUDGET_TRUNCATED'
            detail['result'] = 'truncated_by_budget'
            detail['failure_tag'] = 'BUDGET_TRUNCATED'
            body_report['details'].append(detail)
            continue

        # Platform-URL domain consistency
        _url_lower = url.lower()
        _domain_mismatch = False
        if plat == 'weibo' and not any(d in _url_lower for d in ('weibo.com', 'm.weibo.cn')):
            _domain_mismatch = True
        elif plat == 'wechat' and 'mp.weixin.qq.com' not in _url_lower:
            _domain_mismatch = True
        elif plat == 'bilibili' and 'bilibili.com' not in _url_lower:
            _domain_mismatch = True
        elif plat == 'zhihu' and 'zhihu.com' not in _url_lower:
            _domain_mismatch = True
        if _domain_mismatch:
            it['body_status'] = 'skipped_domain_mismatch'
            it['failure_tag'] = 'DOMAIN_MISMATCH'
            detail['result'] = 'skipped_domain_mismatch'
            body_report['details'].append(detail)
            continue

        # 跳过非文章URL（主页/空间/搜索页），但仍标记而非静默吞掉
        if is_non_article_url(url):
            it['body_status'] = 'skipped_non_article'
            it['failure_tag'] = 'NON_ARTICLE_URL'
            body_report['skipped_non_article'] += 1
            detail['result'] = 'skipped_non_article'
            body_report['details'].append(detail)
            continue

        body_report['attempts'] += 1
        body, ftag = fetch_body(url, plat, 25)

        if body and evidence_is_body(body):
            it['evidence'] = body
            it['body_status'] = 'fetched'
            if not it.get('published_at'):
                it['published_at'] = fetch_publication_date(url, plat)
            body_report['success'] += 1
            detail['result'] = 'fetched'
            detail['body_len'] = len(body)
        else:
            # fetch失败：保留已有snippet，但不冒充body_fetched
            if it.get('evidence') and len(it['evidence']) > 15:
                it['body_status'] = 'excerpt_only'
            else:
                it['body_status'] = 'fetch_fail'
            if ftag:
                it['failure_tag'] = ftag
            body_report['fail'] += 1
            detail['result'] = it['body_status']
            detail['failure_tag'] = ftag or ''

        # 聚合 by_platform
        pp = body_report['by_platform'].setdefault(plat, {'attempts': 0, 'success': 0, 'fail': 0})
        pp['attempts'] += 1
        if detail['result'] == 'fetched':
            pp['success'] += 1
        else:
            pp['fail'] += 1
        # 聚合 by_failure_tag
        if ftag:
            body_report['by_failure_tag'][ftag] = body_report['by_failure_tag'].get(ftag, 0) + 1
        body_report['details'].append(detail)

    # ── C. 观点推演 + 筛噪 ──
    for it in all_items:
        if it.get('viewpoint_inference', '') in ('', '待模型审'):
            it['viewpoint_inference'] = infer_viewpoint(it)
        # Aggregator/hot shells and non-article profile/search URLs are not
        # single dated posts: demote out of eligible before date/freshness
        # gates so they cannot inflate DATE_UNKNOWN_RATIO. Never invent a date.
        if is_aggregator_url(it.get('url', '')):
            it['material_policy'] = 'ARCHIVE_WITH_REASON'
            it['failure_tag'] = AGGREGATOR_FAILURE_TAG
            it['published_at'] = (it.get('published_at') or '').strip()
        elif it.get('body_status') == 'skipped_non_article' or is_non_article_url(it.get('url', '')):
            it['material_policy'] = 'ARCHIVE_WITH_REASON'
            it['failure_tag'] = 'NON_ARTICLE_URL'
            it['published_at'] = (it.get('published_at') or '').strip()
        else:
            # Date backfill pass. The body loop only calls fetch_publication_date on
            # the 'fetched' branch, so every item that hit a budget/domain/non-article
            # continue kept published_at empty and reported DATE_UNKNOWN even when the
            # date sat in plain sight in the title/excerpt/url. Re-derive from the
            # item's own explicit fields here (no collection time, no invention),
            # then optionally a bounded metadata-only platform fetch for WeChat
            # items interrupted by body budget.
            if not it.get('published_at'):
                backfilled = extract_publication_date(it)
                if backfilled:
                    it['published_at'] = backfilled
                    it['published_at_source'] = 'backfill_item_fields'
                else:
                    meta = backfill_platform_metadata_date(it, timeout=10)
                    if meta:
                        it['published_at'] = meta
                        it['published_at_source'] = 'backfill_platform_metadata'
            # Freshness gate. The viewpoint window is policy-dependent, so the
            # provisional policy must be known first; a stale verdict then demotes
            # the item to NOISE. Ordering it the other way round forced a single
            # global cutoff and evicted every dated item (NO_FRESH_DATED).
            provisional_policy = material_policy_tag(it)
            it['material_policy'] = provisional_policy
            stale, reason = is_stale_kol_item(it)
            if stale:
                it['material_policy'] = 'NOISE'
                it['failure_tag'] = reason
                it['stale_evicted_from_policy'] = provisional_policy
            else:
                if is_date_unknown_tag(reason):
                    it['failure_tag'] = date_unknown_failure_tag(it)
                else:
                    # Re-gate cleared the defect: drop obsolete unknown/stale/budget tags.
                    prev = it.get('failure_tag') or ''
                    if (
                        is_date_unknown_tag(prev)
                        or prev in (
                            'BUDGET_TRUNCATED',
                            AGGREGATOR_FAILURE_TAG,
                            'STALE_KOL_ARTICLE',
                            'DATE_OLD_YEAR',
                            'NON_ARTICLE_URL',
                        )
                    ):
                        it['failure_tag'] = ''
                    it.pop('stale_evicted_from_policy', None)
        it['source_nature'] = 'platform_commentary_discovery_not_primary_fact'
        it['official_crosscheck_required'] = True
        it['official_crosscheck_status'] = 'REQUIRED_BEFORE_FORMAL_FACT_CARD'
        if _HAS_DOMAIN_SCORER:
            scorer_item = {
                'title': it.get('title', ''),
                'summary': it.get('evidence', ''),
                'url': it.get('url', ''),
                'source_group_key': f"{it.get('platform', '')}_platform_commentary",
                'source_role': 'secondary',
                'published_at': it.get('published_at', ''),
            }
            domain_score = score_and_classify_item(scorer_item)
            it['domain_score'] = domain_score
            if domain_score.get('domain_scores'):
                it['domain_id_scored'] = domain_score['domain_scores'][0][0]
            it['outline_chapter_hits'] = domain_score.get('outline_chapter_hits', [])
            it['dyson_tree_matches'] = domain_score.get('dyson_tree_matches', [])
            it['dyson_gate_status'] = domain_score.get('dyson_gate_status', '')
            apply_dyson_archive_gate(it, domain_score)

    # ── D. Save platform_discovery.json ──
    stats = {
        'total_queries': total_queries,
        'configured_accounts': configured_account_count,
        'selected_accounts': len(accounts),
        'queried_accounts': len(queried_account_names),
        'queried_account_names': sorted(queried_account_names),
        'configured_domains': configured_domain_count,
        'queried_domains': len(queried_domain_ids),
        'queried_domain_ids': sorted(queried_domain_ids),
        'coverage_sweep': bool(args.coverage_sweep),
        'max_queries': args.max_queries,
        'max_runtime_sec': args.max_runtime_sec,
        'runtime_elapsed_sec': round(time.monotonic() - run_started_monotonic, 3),
        'runtime_truncated': runtime_truncated,
        'discovered': sum(1 for i in all_items if i.get('discovery_status') == 'discovered'),
        'body_fetched': sum(1 for i in all_items if i.get('body_status') == 'fetched'),
        'excerpt_only': sum(1 for i in all_items if i.get('body_status') == 'excerpt_only'),
        'fetch_fail': sum(1 for i in all_items if i.get('body_status') == 'fetch_fail'),
        'skipped_non_article': sum(1 for i in all_items if i.get('body_status') == 'skipped_non_article'),
        'errors': len(errors),
        'platform_signal': sum(1 for i in all_items if i.get('material_policy') == 'PLATFORM_SIGNAL'),
        'discovery_only': sum(1 for i in all_items if i.get('material_policy') == 'DISCOVERY_ONLY'),
        'noise': sum(1 for i in all_items if i.get('material_policy') == 'NOISE'),
        'archive_with_reason': sum(1 for i in all_items if i.get('material_policy') == 'ARCHIVE_WITH_REASON'),
        'dyson_tree_matched': sum(1 for i in all_items if i.get('dyson_tree_matches')),
        'outline_mapped': sum(1 for i in all_items if i.get('outline_chapter_hits')),
        'outline_latest': outline_parse_stats() if _HAS_DOMAIN_SCORER else {},
        'social_cdp_status': social_cdp_report.get('status', 'UNKNOWN'),
        'social_cdp_extension_capability': social_cdp_report.get('extension_capability', ''),
        'social_cdp_platform_pages': len(social_cdp_report.get('platform_pages', [])),
        # P0: freshness stats
        'stale_filtered': sum(1 for i in all_items if i.get('failure_tag') in ('STALE_KOL_ARTICLE', 'DATE_OLD_YEAR')),
        'date_unknown': sum(1 for i in all_items if is_date_unknown_tag(i.get('failure_tag'))),
    }

    discovery_doc = {
        'created_at': now_iso(),
        'run_id': f'radar_v2_{TODAY.replace("-", "")}',
        'watchlist_source': str(WATCH),
        'discovery_method': 'multi_route_v2',
        'items': all_items,
        'errors': errors,
        'stats': stats,
    }
    discovery_path.parent.mkdir(parents=True, exist_ok=True)
    discovery_path.write_text(json.dumps(discovery_doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'\n[discovery] saved {len(all_items)} items → {discovery_path}')
    print(f'[stats] {json.dumps(stats, ensure_ascii=False)}')

    # ── D2. Save body_fetch_report.json ──
    body_report_path.parent.mkdir(parents=True, exist_ok=True)
    body_report_path.write_text(json.dumps(body_report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'[body_report] attempts={body_report["attempts"]} success={body_report["success"]} fail={body_report["fail"]} skipped={body_report["skipped_non_article"]} → {body_report_path}')

    # ── E. Domain Coverage Gate (replaces old sidecar health gate) ──
    # 2026-08-11 P0: each domain MUST emit per-domain diagnostics + failure_reason;
    # strict success counts body_fetched_strict (real body, not excerpt, not stale/unknown, not NOISE/ARCHIVE).
    domain_results = {}  # domain_id → set of account names with strict results
    domain_body_success_raw = {}
    domain_body_success_strict = {}
    accounts_with_results = set()
    for it in all_items:
        if it.get('material_policy') in ('PLATFORM_SIGNAL', 'DISCOVERY_ONLY'):
            acc_name = it.get('account', '')
            accounts_with_results.add(acc_name)
            did = it.get('domain_id', '')
            if did:
                domain_results.setdefault(did, set()).add(acc_name)
            else:
                for d_id, acc_names in domain_map.items():
                    if acc_name in acc_names:
                        domain_results.setdefault(d_id, set()).add(acc_name)
        # Raw body success: any fetched, regardless of policy/tag
        if it.get('body_status') == 'fetched':
            did = it.get('domain_id', '')
            if did:
                domain_body_success_raw[did] = domain_body_success_raw.get(did, 0) + 1
        # Strict body success: real body, not stale/unknown, not noise/archive
        if it.get('body_status') == 'fetched' \
           and it.get('failure_tag') not in _STRICT_FAILURE_TAGS \
           and it.get('material_policy') not in _NO_RESULT_POLICIES:
            did = it.get('domain_id', '')
            if did:
                domain_body_success_strict[did] = domain_body_success_strict.get(did, 0) + 1

    cdp_available = social_cdp_report.get('status') == 'CDP_AVAILABLE'
    items_by_domain: dict[str, list[dict]] = {did: [] for did in domain_map}
    for it in all_items:
        did = it.get('domain_id', '')
        if did in items_by_domain:
            items_by_domain[did].append(it)

    total_accounts = configured_account_count
    domains_with_strict_results = sum(
        1 for did in domain_map
        if domain_body_success_strict.get(did, 0) > 0
        or domain_results.get(did) is not None
    )
    domains_with_results = len(domain_results)
    total_domains = len(domain_map) if domain_map else 1

    stale_platform = sum(
        1 for i in all_items
        if i.get('material_policy') == 'PLATFORM_SIGNAL'
        and i.get('failure_tag') in ('STALE_KOL_ARTICLE', 'DATE_OLD_YEAR')
    )

    domain_health = {}
    for did, acc_names in domain_map.items():
        configured_accounts = len(acc_names)
        output_accounts = len(domain_results.get(did, set()) or set())
        diag = compute_domain_diagnostics(did, items_by_domain.get(did, []), cdp_available=cdp_available)
        domain_health[did] = {
            'domain_name': next((d.get('domain_name', '') for d in watch.get('domains', []) if d.get('domain_id') == did), ''),
            'configured_accounts': configured_accounts,
            'queries': domain_query_counts.get(did, 0),
            'output_accounts': output_accounts,
            'body_success_raw': domain_body_success_raw.get(did, 0),
            'body_success_strict': domain_body_success_strict.get(did, 0),
            'fresh_dated': diag['fresh_dated_count'],
            'excerpt_only': diag['excerpt_only'],
            'date_unknown': diag['date_unknown_count'],
            'stale': diag['stale_count'],
            'noise': diag['noise_count'],
            'archive': diag['archive_count'],
            'fetch_fail': diag['fetch_fail'],
            'missing': output_accounts == 0 and diag['body_fetched_strict'] == 0,
            'failure_reason': diag['failure_reason'],
        }

    # Domain coverage gate: all nine domains must have strict results to be HEALTHY.
    coverage_gate = watch.get('ingest_rules', {}).get('domain_coverage_gate', {})
    min_domains = total_domains
    min_accounts_total = coverage_gate.get('min_accounts_with_results_total', 3)
    min_strict_body_domains = min_domains  # strict gate: 9/9 must have real body or signal

    domains_with_strict_body_or_signal = sum(
        1 for did in domain_map
        if domain_body_success_strict.get(did, 0) > 0
        or domain_results.get(did) is not None
    )

    # Determine health status
    failure_tags = []
    if len(queried_domain_ids) < total_domains:
        failure_tags.append(f'DOMAINS_QUERIED_{len(queried_domain_ids)}_of_{total_domains}')
    if len(queried_account_names) < min(total_accounts, total_domains):
        failure_tags.append(f'ACCOUNTS_QUERIED_{len(queried_account_names)}_of_{total_accounts}')
    # Strict gate: require real body OR signal in every domain; excerpt+unknown does NOT count
    if domains_with_strict_body_or_signal < min_strict_body_domains:
        failure_tags.append(f'STRICT_DOMAINS_ONLY_{domains_with_strict_body_or_signal}_of_{total_domains}')
    if domains_with_results < min_domains:
        failure_tags.append(f'POLICY_DOMAINS_ONLY_{domains_with_results}_of_{total_domains}')
    if len(accounts_with_results) < min_accounts_total:
        failure_tags.append(f'ACCOUNTS_ONLY_{len(accounts_with_results)}_WITH_RESULTS')
    if stale_platform > 0:
        failure_tags.append(f'STALE_PLATFORM={stale_platform}')
    # 2026-08-12: socialext-cft profile 无 Default/Extensions、Cookies 仅 20KB，
    # 社媒助手扩展与五平台登录态实际不存在，CDP 补采链路无资产可用。
    # KEWU_DISABLE_SOCIAL_CDP=1 时视为「按设计关闭」，不计入 failure_tags，
    # 避免 sidecar_health 恒为 PARTIAL 导致哨兵每轮空弹。
    # 重建登录态后清掉该环境变量即可恢复原判定。
    if not cdp_available and os.getenv('KEWU_DISABLE_SOCIAL_CDP') != '1':
        failure_tags.append('CDP_UNAVAILABLE_SOCIAL_SUPPLEMENT_OFF')

    # Per-domain failure reasons: any domain without strict body or signal
    failed_domains_detail = []
    for did in domain_map:
        dh = domain_health[did]
        if dh['body_success_strict'] == 0 and dh['output_accounts'] == 0:
            failed_domains_detail.append(f"{did}:{dh['failure_reason']}")
    if failed_domains_detail:
        failure_tags.append('DOMAIN_FAILURE_DETAILS=' + ';'.join(failed_domains_detail))

    hotspot_metrics = kol_hotspot_health_metrics(all_items)
    if hotspot_metrics['date_unknown_ratio'] > 0.5:
        failure_tags.append(f'DATE_UNKNOWN_RATIO_{hotspot_metrics["date_unknown_ratio"]:.2f}')
    if hotspot_metrics['fresh_dated_count'] < 1:
        failure_tags.append('NO_FRESH_DATED_KOL_RESULT')
    if hotspot_metrics['ai_science_hotspot_count'] < 1:
        failure_tags.append('AI_SCIENCE_HOTSPOT_RECALL_ZERO')
    if hotspot_metrics['dynamic_entity_count'] < 1:
        failure_tags.append('DYNAMIC_ENTITY_ZERO')

    silent_domains = [did for did in domain_map if did not in domain_results]

    if failure_tags:
        sidecar_health = 'PARTIAL'
        sidecar_health_reason = '; '.join(failure_tags)
        # Inject into ACTION_QUEUE
        action_queue_entry = {
            'type': 'KOL_DOMAIN_COVERAGE_GAP',
            'created_at': now_iso(),
            'failure_tags': failure_tags,
            'silent_domains': silent_domains,
            'domains_with_results': list(domain_results.keys()),
            'accounts_with_results': list(accounts_with_results),
        }
        action_queue_path = out_dir / 'action_queue.jsonl'
        with open(action_queue_path, 'a', encoding='utf-8') as aqf:
            aqf.write(json.dumps(action_queue_entry, ensure_ascii=False) + '\n')
        print(f'[ACTION_QUEUE] {sidecar_health_reason}')
    else:
        sidecar_health = 'HEALTHY'
        sidecar_health_reason = ''

    stats['coverage_pct'] = round(100 * len(accounts_with_results) / total_accounts) if total_accounts else 0
    stats['stale_platform'] = stale_platform
    stats['accounts_with_results'] = len(accounts_with_results)
    stats['domains_total'] = total_domains
    stats['domains_with_results'] = domains_with_results
    stats['domains_with_strict_body_or_signal'] = domains_with_strict_body_or_signal
    stats['silent_domains'] = silent_domains
    stats['domain_coverage_detail'] = {did: len(accs) for did, accs in domain_results.items()}
    stats['domain_health'] = domain_health
    stats['domain_queries'] = domain_query_counts
    stats['sidecar_health'] = sidecar_health
    stats['sidecar_health_reason'] = sidecar_health_reason
    stats['hotspot_recall'] = hotspot_metrics
    stats['health_policy'] = {
        'cache_requires': ['fresh_dated_result', 'domain_coverage', 'ai_science_hotspot_recall', 'dynamic_entity', 'body_or_excerpt'],
        'mapping_baseline': 'stable_nine_domains_dyson_tree_latest_outline_post_discovery_filter',
        'full_list_health_claim': len(queried_account_names) == total_accounts,
    }
    discovery_doc['stats'] = stats
    discovery_path.write_text(json.dumps(discovery_doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'[health_gate] domains={domains_with_results}/{total_domains} accounts={len(accounts_with_results)}/{total_accounts} stale_PLATFORM={stale_platform} → {sidecar_health}')

    # ── E2. MiroFish Feed Package ──
    if not args.dry_run_mirofish:
        mf = build_mirofish_package(all_items)
        mirofish_path.parent.mkdir(parents=True, exist_ok=True)
        mirofish_path.write_text(json.dumps(mf, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'[mirofish] {mf["total_cards"]} cards → {mirofish_path}')
    else:
        print('[dry-run] skipped MiroFish package generation')

    # ── F. Summary ──
    summary_path = out_dir / 'radar_v2_summary.md'
    md = [
        f'# 平台号观点雷达 v2 — {TODAY}',
        '',
        f'- queries: {stats["total_queries"]}',
        f'- configured_accounts: {stats.get("configured_accounts", 0)}',
        f'- queried_accounts: {stats.get("queried_accounts", 0)}',
        f'- queried_domains: {stats.get("queried_domains", 0)}/{stats.get("configured_domains", 0)}',
        f'- full_list_health_claim: {stats.get("health_policy", {}).get("full_list_health_claim", False)}',
        f'- discovered: {stats["discovered"]}',
        f'- body_fetched: {stats["body_fetched"]}',
        f'- excerpt_only: {stats["excerpt_only"]}',
        f'- fetch_fail: {stats["fetch_fail"]}',
        f'- skipped_non_article: {stats["skipped_non_article"]}',
        f'- platform_signal: {stats["platform_signal"]}',
        f'- discovery_only: {stats["discovery_only"]}',
        f'- noise: {stats["noise"]}',
        f'- archive_with_reason: {stats["archive_with_reason"]}',
        f'- dyson_tree_matched: {stats["dyson_tree_matched"]}',
        f'- outline_latest_path: {stats.get("outline_latest", {}).get("outline_path", "")}',
        f'- outline_latest_chapter_count: {stats.get("outline_latest", {}).get("chapter_count", 0)}',
        f'- outline_mapping_rate: {round(stats["outline_mapped"] / max(1, len(all_items)), 3)}',
        f'- social_cdp_status: {stats.get("social_cdp_status", "UNKNOWN")}',
        f'- social_cdp_extension_capability: {stats.get("social_cdp_extension_capability", "")}',
        f'- social_cdp_platform_pages: {stats.get("social_cdp_platform_pages", 0)}',
        f'- errors: {stats["errors"]}',
        f'- stale_filtered: {stats.get("stale_filtered", 0)}',
        f'- date_unknown: {stats.get("date_unknown", 0)}',
        f'- date_unknown_ratio: {stats.get("hotspot_recall", {}).get("date_unknown_ratio", 0)}',
        f'- fresh_dated_count: {stats.get("hotspot_recall", {}).get("fresh_dated_count", 0)}',
        f'- ai_science_hotspot_count: {stats.get("hotspot_recall", {}).get("ai_science_hotspot_count", 0)}',
        f'- dynamic_entity_count: {stats.get("hotspot_recall", {}).get("dynamic_entity_count", 0)}',
        f'- coverage_pct: {stats.get("coverage_pct", 0)}%',
        f'- domains_with_results: {stats.get("domains_with_results", 0)}/{stats.get("domains_total", 0)}',
        f'- domains_with_strict_body_or_signal: {stats.get("domains_with_strict_body_or_signal", 0)}/{stats.get("domains_total", 0)}',
        f'- silent_domains: {", ".join(stats.get("silent_domains", [])) or "none"}',
        f'- sidecar_health: **{stats.get("sidecar_health", "N/A")}**',
        f'- sidecar_health_reason: {stats.get("sidecar_health_reason", "")}',
        '',
        '## 九域健康矩阵（严格计数：正文strict=已抓到正文且非日期未知/非stale/非NOISE/非ARCHIVE）',
        '',
        '| domain | 账户 | 查询 | strict产出账户 | 正文raw | 正文strict | fresh_dated | excerpt_only | date_unknown | stale | noise | archive | failure_reason |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|',
    ]
    for did, row in stats.get('domain_health', {}).items():
        md.append(
            f"| {did}/{row.get('domain_name', '')} "
            f"| {row.get('configured_accounts', 0)} "
            f"| {row.get('queries', 0)} "
            f"| {row.get('output_accounts', 0)} "
            f"| {row.get('body_success_raw', 0)} "
            f"| {row.get('body_success_strict', 0)} "
            f"| {row.get('fresh_dated', 0)} "
            f"| {row.get('excerpt_only', 0)} "
            f"| {row.get('date_unknown', 0)} "
            f"| {row.get('stale', 0)} "
            f"| {row.get('noise', 0)} "
            f"| {row.get('archive', 0)} "
            f"| {row.get('failure_reason', 'OK')} |"
        )
    md += [
        '',
        '## 平台信号',
    ]
    for it in sorted(all_items, key=lambda x: x.get('material_policy', ''), reverse=True):
        if it.get('material_policy') in ('PLATFORM_SIGNAL', 'DISCOVERY_ONLY'):
            md.append(f"- [{it['material_policy']}] {it['account']}@{it['platform']} | {it['title'][:60]}")
            md.append(f"  {it['url']}")
            if it.get('viewpoint_inference'):
                md.append(f"  → {it['viewpoint_inference']}")
    if errors:
        md += ['', '## 失败']
        for e in errors:
            md.append(f"- {e['account']}@{e['platform']}: {e['error']}")
    summary_path.write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(f'[summary] → {summary_path}')

    # final json output
    print(json.dumps({
        'status': 'ok',
        'discovery_json': str(discovery_path),
        'mirofish_json': str(mirofish_path) if not args.dry_run_mirofish else None,
        'summary': str(summary_path),
        'social_cdp_probe': str(social_cdp_path),
        'stats': stats,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
