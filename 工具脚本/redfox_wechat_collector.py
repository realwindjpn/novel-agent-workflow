#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""redfox_wechat_collector.py — 《科武纪元》RedFox 微信公众号正文采集器。

把 platform_watchlist.json 中 route == 'redfox_wechat' 的公众号（87 个）批量采成素材卡：

    列表调用  client.wechat.get_user_works(account=<redfox_account>, offset=0)
    正文调用  client.wechat.get_work(work_uuid=<uuid>)      # 唯一可用的全文接口

产物：
    <out-dir>/cards/*.md            每篇一个 md（含 front-matter）
    <out-dir>/raw/bodies/*.txt      正文原文
    <out-dir>/events.jsonl          每账号一条采集事件（成功/失败/failure_tags）
    <out-dir>/run_summary.json      整轮汇总
    追加 material_cards.jsonl       append 模式，绝不覆盖

已知坑（硬编码遵守，勿改）：
    * get_article_detail(url=...) 会超时 → 只用 get_work(work_uuid=...)
    * 错误码 3203 = 优质库未收录，不扣积分 → 跳过该账号，不重试
    * get_work 单篇 30~120s → 每次调用套线程超时，超时不拖垮整轮
    * 列表/搜索类调用间隔 >= 0.3s

用法：
    python3 redfox_wechat_collector.py --check-mode
    python3 redfox_wechat_collector.py --execute --max-accounts 2 --max-articles-per-account 1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ═══════════════════════════════════════════════
# 0. 常量 / 路径
# ═══════════════════════════════════════════════

TOOLS_DIR = Path('/root/workspace/科武纪元/工具脚本')
RADAR_DIR = Path('/root/workspace/科武纪元/学习记录/平台号观点雷达')
WATCHLIST_PATH = RADAR_DIR / 'platform_watchlist.json'
RUNS_ROOT = RADAR_DIR / 'runs'
MATERIAL_CARDS_PATH = Path('/root/workspace/素材总线/kewu/material_cards.jsonl')
SEEN_UUIDS_PATH = RUNS_ROOT / 'redfox_seen_uuids.json'

ROUTE_TAG = 'redfox_wechat'          # watchlist 路由值 + 素材卡 route 值
PLATFORM_TAG = 'wechat'              # 与现有素材卡口径一致
SOURCE_RUN_TYPE = 'redfox_wechat_kol'
DOMAIN_TAG = 'kewu'

LIST_CALL_INTERVAL_S = 0.35          # 列表调用最小间隔（坑：搜索类 >= 0.3s）
GET_WORK_TIMEOUT_S = 150             # 单篇正文超时（坑：30~120s）
GET_LIST_TIMEOUT_S = 90              # 列表调用超时
MIN_BODY_LEN_USABLE = 300            # 正文达此长度算 usable
EXCERPT_LEN = 600                    # content_excerpt 截断长度

# 科武九域 ID 集合 —— 命中其中之一才入总线，其余过滤
KEWU_CORE_DOMAINS: set[str] = {
    'frontier_tech', 'geopolitics', 'biology', 'space', 'aviation',
    'ai', 'military', 'materials', 'energy',
    # 戴森果子域也允许（scorer 偶尔分到这些子域）
    'material_science', 'orbital_mechanics', 'energy_harvesting',
    'quantum_computing', 'dyson_construction', 'strategic_materials',
}
# 最低入卡分数（score_and_classify_item 的 total_score 口径）
MIN_TOTAL_SCORE: float = 3.0

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

# 域打分：复用现有模块，失败则降级为 ontology 关键词打分
SCORER_MODE = 'none'
try:
    from kewu_domain_scorer import score_and_classify_item  # type: ignore
    SCORER_MODE = 'score_and_classify_item'
except Exception as _scorer_err:  # pragma: no cover
    score_and_classify_item = None  # type: ignore
    _SCORER_IMPORT_ERROR = repr(_scorer_err)
try:
    from kewu_domain_ontology import STABLE_DOMAINS, get_domain_for_keywords  # type: ignore
    if SCORER_MODE == 'none':
        SCORER_MODE = 'ontology_only'
except Exception as _onto_err:  # pragma: no cover
    STABLE_DOMAINS = {}  # type: ignore
    get_domain_for_keywords = None  # type: ignore


# ═══════════════════════════════════════════════
# 1. 小工具
# ═══════════════════════════════════════════════

def now_iso() -> str:
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def now_stamp() -> str:
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def sha12(text: str) -> str:
    return hashlib.sha1(text.encode('utf-8', 'ignore')).hexdigest()[:12]


_SLUG_RE = re.compile(r'[^0-9A-Za-z\u4e00-\u9fff]+')


def slugify(text: str, limit: int = 48) -> str:
    """文件名安全化：保留中英数字，其余折叠为下划线。"""
    s = _SLUG_RE.sub('_', str(text or '')).strip('_')
    return (s[:limit] or 'untitled')


def call_with_timeout(fn, timeout_s: float, *args, **kwargs):
    """在 daemon 线程里跑 fn，超时抛 TimeoutError（线程可能泄漏但不阻塞退出）。"""
    box: dict[str, Any] = {}

    def _runner() -> None:
        try:
            box['result'] = fn(*args, **kwargs)
        except BaseException as exc:  # noqa: BLE001 - 需要原样回传
            box['error'] = exc

    th = threading.Thread(target=_runner, daemon=True)
    th.start()
    th.join(timeout_s)
    if th.is_alive():
        raise TimeoutError(f'call {getattr(fn, "__name__", fn)} timeout after {timeout_s}s')
    if 'error' in box:
        raise box['error']
    return box.get('result')


def is_not_indexed_error(payload: Any, exc: BaseException | None = None) -> bool:
    """错误码 3203 = 优质库未收录（不扣积分）→ 跳过账号，不重试。"""
    blob = ''
    if exc is not None:
        blob += f'{type(exc).__name__}:{exc}'
    if isinstance(payload, dict):
        code = payload.get('code', payload.get('errcode'))
        if str(code) == '3203':
            return True
        blob += json.dumps(payload, ensure_ascii=False)[:600]
    return '3203' in blob


def normalize_url(url: Any) -> str:
    return str(url or '').strip().rstrip('/').lower()


# ═══════════════════════════════════════════════
# 2. watchlist 载入
# ═══════════════════════════════════════════════

def load_watchlist_accounts(watchlist_path: Path) -> list[dict[str, Any]]:
    """读 domain-slot 格式 watchlist，抽出 route == redfox_wechat 的账号。"""
    data = json.loads(watchlist_path.read_text(encoding='utf-8'))
    out: list[dict[str, Any]] = []
    for dom in data.get('domains', []) or []:
        domain_id = dom.get('domain_id') or ''
        domain_name = dom.get('domain_name') or domain_id
        for acct in dom.get('accounts', []) or []:
            if (acct.get('route') or '') != ROUTE_TAG:
                continue
            rf_account = (acct.get('redfox_account') or '').strip()
            if not rf_account:
                continue
            out.append({
                'domain_id': domain_id,
                'domain_name': domain_name,
                'name': acct.get('name') or rf_account,
                'redfox_account': rf_account,
                'redfox_index': float(acct.get('redfox_index') or 0.0),
                'last_publish': acct.get('last_publish') or '',
                'keywords': acct.get('keywords') or [],
                'use': acct.get('use') or '',
            })
    return out


def order_accounts(accounts: list[dict[str, Any]], order: str) -> list[dict[str, Any]]:
    if order == 'index':
        return sorted(accounts, key=lambda a: -a['redfox_index'])
    if order == 'name':
        return sorted(accounts, key=lambda a: a['name'])
    if order == 'watchlist':
        return list(accounts)
    # default: fresh —— 最近发文优先，其次影响力指数
    return sorted(accounts, key=lambda a: (a['last_publish'], a['redfox_index']), reverse=True)


# ═══════════════════════════════════════════════
# 3. 幂等：seen uuids + 已有素材卡 url
# ═══════════════════════════════════════════════

def load_seen(seen_path: Path) -> dict[str, Any]:
    if seen_path.exists():
        try:
            data = json.loads(seen_path.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                data.setdefault('uuids', [])
                data.setdefault('urls', [])
                return data
        except Exception:
            pass
    return {'uuids': [], 'urls': [], 'updated_at': ''}


def save_seen(seen_path: Path, uuids: set[str], urls: set[str]) -> None:
    seen_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'schema': 'redfox_wechat_seen/v1',
        'updated_at': now_iso(),
        'uuid_count': len(uuids),
        'url_count': len(urls),
        'uuids': sorted(uuids),
        'urls': sorted(urls),
    }
    tmp = seen_path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding='utf-8')
    tmp.replace(seen_path)


def load_existing_card_keys(cards_path: Path) -> tuple[set[str], set[str]]:
    """从 material_cards.jsonl 读已有 url / candidate_id（=workUuid）做二次去重。"""
    urls: set[str] = set()
    uuids: set[str] = set()
    if not cards_path.exists():
        return urls, uuids
    with cards_path.open('r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            u = normalize_url(row.get('url'))
            if u:
                urls.add(u)
            cid = str(row.get('candidate_id') or '').strip()
            if cid and (row.get('route') == ROUTE_TAG or len(cid) >= 16):
                uuids.add(cid)
    return urls, uuids


# ═══════════════════════════════════════════════
# 4. 域打分（复用 kewu_domain_scorer）
# ═══════════════════════════════════════════════

def domain_label(domain_id: str) -> str:
    meta = STABLE_DOMAINS.get(domain_id) if isinstance(STABLE_DOMAINS, dict) else None
    if isinstance(meta, dict):
        for key in ('name', 'domain_name', 'label', 'cn_name'):
            val = meta.get(key)
            if isinstance(val, str) and val:
                return val
    return domain_id


def passes_domain_filter(score: dict[str, Any]) -> tuple[bool, str]:
    """判断打分结果是否命中科武九域。返回 (通过, 原因)。"""
    domain_scores = score.get('domain_scores') or []
    hit_ids: set[str] = set()
    for entry in domain_scores:
        did = entry[0] if isinstance(entry, (list, tuple)) else entry
        if isinstance(did, str):
            hit_ids.add(did)
    matched = hit_ids & KEWU_CORE_DOMAINS
    if not matched:
        return False, f'DOMAIN_MISS hit={hit_ids or {"none"}}'
    total = score.get('total_score') or 0.0
    if total < MIN_TOTAL_SCORE:
        return False, f'SCORE_TOO_LOW total={total:.1f} < {MIN_TOTAL_SCORE}'
    return True, f'OK domains={matched}'


def score_article(article: dict[str, Any], body: str, account: dict[str, Any],
                  seen_urls: set[str]) -> dict[str, Any]:
    """复用 score_and_classify_item；不可用时降级为 ontology 关键词打分。"""
    item = {
        'title': article.get('title') or '',
        'summary': article.get('summary') or '',
        'body': body,
        'url': article.get('workUrl') or '',
        'published_at': article.get('publishTime') or '',
        'source_group_key': 'domestic_kol',
        'source_role': 'secondary',
    }
    if SCORER_MODE == 'score_and_classify_item' and score_and_classify_item is not None:
        try:
            res = call_with_timeout(score_and_classify_item, 120, item, None, seen_urls)
            if isinstance(res, dict):
                res['_scorer'] = 'score_and_classify_item'
                return res
        except Exception as exc:
            fallback_reason = f'SCORER_FAILED:{type(exc).__name__}'
        else:
            fallback_reason = 'SCORER_EMPTY'
    else:
        fallback_reason = f'SCORER_UNAVAILABLE:{SCORER_MODE}'

    blob = f"{item['title']} {item['summary']} {body[:4000]}"
    domain_scores: list[tuple[str, float]] = []
    if callable(get_domain_for_keywords):
        try:
            domain_scores = list(get_domain_for_keywords(blob))[:3]
        except Exception:
            domain_scores = []
    if not domain_scores and account.get('domain_id'):
        domain_scores = [(account['domain_id'], 1.0)]
    return {
        'total_score': round(2.0 + min(3.0, len(domain_scores) * 1.0), 2),
        'domain_scores': domain_scores,
        'breakdown': {},
        'noise_flag': False,
        'noise_reason': '',
        'outline_chapter_hits': [],
        'dyson_tree_matches': [],
        'dyson_gate_status': 'UNKNOWN_FALLBACK_SCORER',
        'entities': {},
        'dedup_flag': normalize_url(item['url']) in seen_urls,
        '_scorer': f'fallback({fallback_reason})',
    }


def build_analysis_angle(score: dict[str, Any], account: dict[str, Any]) -> str:
    labels: list[str] = []
    for entry in score.get('domain_scores') or []:
        did = entry[0] if isinstance(entry, (list, tuple)) else entry
        lab = domain_label(str(did))
        if lab and lab not in labels:
            labels.append(lab)
    if not labels:
        labels = [account.get('domain_name') or account.get('domain_id') or 'kewu']
    return '|'.join(labels[:3])


def build_chapter_target(score: dict[str, Any]) -> str:
    hits = [int(c) for c in (score.get('outline_chapter_hits') or []) if str(c).isdigit()]
    if hits:
        return '|'.join(f'第{c}章' for c in hits[:4])
    return 'MiroFish/G1候选'


def confidence_from_score(total: float, body_len: int) -> float:
    base = 0.45 + min(0.40, max(0.0, float(total)) / 25.0)
    if body_len >= MIN_BODY_LEN_USABLE:
        base += 0.08
    return round(min(0.95, max(0.30, base)), 2)


def quality_from(score: dict[str, Any], body_len: int) -> str:
    if score.get('noise_flag'):
        return 'discovery_only'
    if body_len >= MIN_BODY_LEN_USABLE:
        return 'usable'
    if body_len > 0:
        return 'candidate'
    return 'discovery_only'


# ═══════════════════════════════════════════════
# 5. 落盘：md 卡 / 正文 / 素材卡
# ═══════════════════════════════════════════════

def yaml_escape(val: Any) -> str:
    s = str(val if val is not None else '')
    s = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
    return f'"{s}"'


def write_body_file(out_dir: Path, account: dict[str, Any], uuid: str, body: str) -> Path:
    bodies_dir = out_dir / 'raw' / 'bodies'
    bodies_dir.mkdir(parents=True, exist_ok=True)
    path = bodies_dir / f"{slugify(account['redfox_account'], 32)}_{sha12(uuid)}.txt"
    path.write_text(body, encoding='utf-8')
    return path


def write_card_md(out_dir: Path, card: dict[str, Any], article: dict[str, Any],
                  account: dict[str, Any], score: dict[str, Any], body: str) -> Path:
    cards_dir = out_dir / 'cards'
    cards_dir.mkdir(parents=True, exist_ok=True)
    path = cards_dir / f"{slugify(card['title'], 40)}_{card['id'][-8:]}.md"
    fm = [
        '---',
        f'id: {yaml_escape(card["id"])}',
        f'domain: {yaml_escape(card["domain"])}',
        f'created_at: {yaml_escape(card["created_at"])}',
        f'source_run_type: {yaml_escape(card["source_run_type"])}',
        f'source_run: {yaml_escape(card["source_run"])}',
        f'source: {yaml_escape(card["source"])}',
        f'platform: {yaml_escape(card["platform"])}',
        f'route: {yaml_escape(card["route"])}',
        f'title: {yaml_escape(card["title"])}',
        f'url: {yaml_escape(card["url"])}',
        f'work_uuid: {yaml_escape(card["candidate_id"])}',
        f'publish_time: {yaml_escape(article.get("publishTime") or "")}',
        f'read_count: {yaml_escape(article.get("readCount") or "")}',
        f'like_count: {yaml_escape(article.get("likeCount") or "")}',
        f'redfox_account: {yaml_escape(account["redfox_account"])}',
        f'watchlist_domain: {yaml_escape(account.get("domain_id") or "")}',
        f'analysis_angle: {yaml_escape(card["analysis_angle"])}',
        f'chapter_target: {yaml_escape(card["chapter_target"])}',
        f'domain_score: {score.get("total_score", 0)}',
        f'dyson_gate_status: {yaml_escape(score.get("dyson_gate_status") or "")}',
        f'scorer: {yaml_escape(score.get("_scorer") or SCORER_MODE)}',
        f'confidence_score: {card["confidence_score"]}',
        f'quality: {yaml_escape(card["quality"])}',
        f'body_status: {yaml_escape(card["body_status"])}',
        f'body_len: {card["body_len"]}',
        f'body_path: {yaml_escape(card["body_path"])}',
        f'consumer_status: {yaml_escape(card["consumer_status"])}',
        '---',
        '',
        f'# {card["title"]}',
        '',
        f'- 公众号：{account["name"]}（redfox_account: `{account["redfox_account"]}`）',
        f'- 发布时间：{article.get("publishTime") or "N/A"}　阅读：{article.get("readCount", "N/A")}　点赞：{article.get("likeCount", "N/A")}',
        f'- 原文：{card["url"]}',
        f'- 域标签：{card["analysis_angle"]}　命中章节：{card["chapter_target"]}',
        f'- 域评分：{score.get("total_score", 0)}　实体：{json.dumps(score.get("entities") or {}, ensure_ascii=False)[:400]}',
        '',
        '## 正文',
        '',
        body.strip() if body.strip() else '(正文为空)',
        '',
    ]
    path.write_text('\n'.join(fm), encoding='utf-8')
    return path


_APPEND_LOCK = threading.Lock()


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    """append 模式追加一行 JSON（绝不覆盖）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row, ensure_ascii=False) + '\n'
    with _APPEND_LOCK:
        with path.open('a', encoding='utf-8') as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())


def build_card(article: dict[str, Any], body: str, account: dict[str, Any],
               score: dict[str, Any], out_dir: Path, body_path: Path | None) -> dict[str, Any]:
    """构造素材卡，字段严格对齐 material_cards.jsonl 现有口径。"""
    uuid = str(article.get('workUuid') or '')
    url = str(article.get('workUrl') or '')
    title = str(score.get('title_used') or article.get('title') or '').strip() or '(untitled)'
    body_len = len(body or '')
    excerpt_src = (body or '').strip() or str(article.get('summary') or '').strip()
    return {
        'id': f'kewu_rfwx_{sha12(uuid or url or title)}',
        'domain': DOMAIN_TAG,
        'created_at': now_iso(),
        'source_run_type': SOURCE_RUN_TYPE,
        'source_run': str(out_dir),
        'candidate_id': uuid,
        'source': account['name'],
        'platform': PLATFORM_TAG,
        'title': title,
        'url': url,
        'content_excerpt': excerpt_src[:EXCERPT_LEN],
        'analysis_angle': build_analysis_angle(score, account),
        'chapter_target': build_chapter_target(score),
        'confidence_score': confidence_from_score(score.get('total_score') or 0.0, body_len),
        'quality': quality_from(score, body_len),
        'body_status': 'fetched' if body_len >= 1 else 'excerpt_only',
        'body_len': body_len,
        'body_path': str(body_path) if body_path else '',
        'card_md': '',  # 写 md 后回填
        'route': ROUTE_TAG,
        'consumer_status': 'NEW',
    }


# ═══════════════════════════════════════════════
# 6. RedFox 调用封装
# ═══════════════════════════════════════════════

class RedFoxWechat:
    def __init__(self) -> None:
        from redfox import RedFoxClient  # 延迟导入，check-mode 无需依赖
        self.client = RedFoxClient()
        self._last_call = 0.0

    def _throttle(self, interval: float = LIST_CALL_INTERVAL_S) -> None:
        gap = time.time() - self._last_call
        if gap < interval:
            time.sleep(interval - gap)
        self._last_call = time.time()

    def list_works(self, account_id: str, offset: int = 0) -> list[dict[str, Any]]:
        self._throttle()
        try:
            resp = call_with_timeout(
                self.client.wechat.get_user_works, GET_LIST_TIMEOUT_S,
                account=account_id, offset=offset,
            )
        except TimeoutError:
            raise
        except Exception as exc:
            # 3203 可能以异常形式抛出（RedFoxAPIError），归类为未收录而非失败
            if is_not_indexed_error(None, exc):
                raise NotIndexedError(f'3203 not indexed: {account_id}: {exc}') from exc
            raise
        if isinstance(resp, dict):
            if is_not_indexed_error(resp):
                raise NotIndexedError(f'3203 not indexed: {account_id}')
            items = resp.get('list')
            if isinstance(items, list):
                return items
            raise RuntimeError(f'unexpected list payload keys={sorted(resp.keys())[:8]}')
        raise RuntimeError(f'unexpected list response type={type(resp).__name__}')

    def fetch_body(self, work_uuid: str) -> tuple[str, dict[str, Any]]:
        self._throttle()
        try:
            detail = call_with_timeout(
                self.client.wechat.get_work, GET_WORK_TIMEOUT_S, work_uuid=work_uuid,
            )
        except TimeoutError:
            raise
        except Exception as exc:
            if is_not_indexed_error(None, exc):
                raise NotIndexedError(f'3203 not indexed: work {work_uuid}: {exc}') from exc
            raise
        if isinstance(detail, dict):
            if is_not_indexed_error(detail):
                raise NotIndexedError(f'3203 not indexed: work {work_uuid}')
            content = detail.get('content')
            if content is None:
                content = detail.get('contentText') or detail.get('body') or ''
            return str(content or ''), detail
        raise RuntimeError(f'unexpected work response type={type(detail).__name__}')


class NotIndexedError(RuntimeError):
    """错误码 3203：优质库未收录，不扣积分，跳过不重试。"""


# ═══════════════════════════════════════════════
# 7. 主流程
# ═══════════════════════════════════════════════

def run_check_mode(accounts_all: list[dict[str, Any]], planned: list[dict[str, Any]],
                   args: argparse.Namespace, seen: dict[str, Any],
                   existing_urls: set[str], existing_uuids: set[str]) -> dict[str, Any]:
    est_list_calls = len(planned)
    est_work_calls = len(planned) * args.max_articles_per_account
    print('=' * 78)
    print('RedFox 微信公众号采集器 — CHECK MODE（不发生任何抓取）')
    print('=' * 78)
    print(f'watchlist          : {WATCHLIST_PATH}')
    print(f'route==redfox_wechat 账号总数 : {len(accounts_all)}')
    print(f'本轮计划处理       : {len(planned)}  (--max-accounts {args.max_accounts}, --order {args.order}, --start-index {args.start_index})')
    print(f'每账号最多抓取     : {args.max_articles_per_account} 篇')
    print(f'预估 API 调用      : 列表 {est_list_calls} 次 + 正文 {est_work_calls} 次 = {est_list_calls + est_work_calls} 次')
    print(f'预估耗时(正文30~120s): {est_work_calls * 30 / 60:.1f} ~ {est_work_calls * 120 / 60:.1f} 分钟')
    print(f'打分模块           : SCORER_MODE={SCORER_MODE}')
    print(f'seen_uuids.json    : {SEEN_UUIDS_PATH} (已记录 uuid {len(seen.get("uuids") or [])} / url {len(seen.get("urls") or [])})')
    print(f'material_cards     : {MATERIAL_CARDS_PATH} (已有 url {len(existing_urls)} / uuid {len(existing_uuids)})')
    print(f'产物目录(若 execute): {args.out_dir}')
    print('-' * 78)
    print(f'{"#":>3}  {"domain":<14} {"redfox_account":<24} {"last_publish":<20} {"idx":>8}  name')
    for i, acct in enumerate(planned, 1):
        print(f'{i:>3}  {acct["domain_id"]:<14} {acct["redfox_account"]:<24} '
              f'{acct["last_publish"]:<20} {acct["redfox_index"]:>8.1f}  {acct["name"]}')
    print('-' * 78)
    by_domain: dict[str, int] = {}
    for acct in accounts_all:
        by_domain[acct['domain_id']] = by_domain.get(acct['domain_id'], 0) + 1
    print('全量账号按域分布   : ' + ', '.join(f'{k}={v}' for k, v in sorted(by_domain.items(), key=lambda x: -x[1])))
    print('CHECK MODE 结束：未调用任何 RedFox 接口，未写任何产物。')
    return {
        'mode': 'check',
        'accounts_total': len(accounts_all),
        'accounts_planned': len(planned),
        'est_list_calls': est_list_calls,
        'est_work_calls': est_work_calls,
        'by_domain': by_domain,
    }


def run_execute(planned: list[dict[str, Any]], args: argparse.Namespace,
                seen_uuids: set[str], seen_urls: set[str]) -> dict[str, Any]:
    out_dir = Path(args.out_dir)
    (out_dir / 'cards').mkdir(parents=True, exist_ok=True)
    (out_dir / 'raw' / 'bodies').mkdir(parents=True, exist_ok=True)
    events_path = out_dir / 'events.jsonl'

    print(f'[execute] out_dir={out_dir}')
    print(f'[execute] accounts={len(planned)} max_articles_per_account={args.max_articles_per_account}')

    try:
        api = RedFoxWechat()
    except Exception as exc:
        err = f'REDFOX_CLIENT_INIT_FAILED: {type(exc).__name__}: {exc}'
        print(f'[FATAL] {err}')
        append_jsonl(events_path, {
            'ts': now_iso(), 'level': 'fatal', 'status': 'failed',
            'failure_tags': ['REDFOX_CLIENT_INIT_FAILED'], 'error': str(exc),
        })
        return {'mode': 'execute', 'status': 'FAILED', 'error': err,
                'cards_written': 0, 'accounts_processed': 0, 'out_dir': str(out_dir)}

    totals = {
        'accounts_processed': 0, 'accounts_ok': 0, 'accounts_partial': 0,
        'accounts_failed': 0, 'accounts_skipped_not_indexed': 0,
        'articles_listed': 0, 'articles_fetched': 0, 'articles_skipped_seen': 0,
        'cards_written': 0, 'md_written': 0,
    }
    card_paths: list[str] = []

    for idx, acct in enumerate(planned, 1):
        t0 = time.time()
        acct_id = acct['redfox_account']
        ev: dict[str, Any] = {
            'ts': now_iso(), 'seq': idx, 'account': acct_id, 'account_name': acct['name'],
            'domain_id': acct['domain_id'], 'route': ROUTE_TAG,
            'articles_listed': 0, 'articles_selected': 0, 'articles_fetched': 0,
            'articles_skipped_seen': 0, 'cards_written': 0,
            'status': 'unknown', 'failure_tags': [], 'errors': [], 'card_files': [],
        }
        print(f'\n[{idx}/{len(planned)}] {acct["name"]} ({acct_id}) domain={acct["domain_id"]}')

        # --- 1) 列表 ---
        try:
            works = api.list_works(acct_id, offset=0)
        except NotIndexedError as exc:
            ev.update(status='skipped', failure_tags=['NOT_INDEXED_3203'], errors=[str(exc)])
            totals['accounts_skipped_not_indexed'] += 1
            totals['accounts_processed'] += 1
            ev['duration_s'] = round(time.time() - t0, 1)
            append_jsonl(events_path, ev)
            print('    -> SKIP 3203 优质库未收录（不扣积分，不重试）')
            continue
        except TimeoutError as exc:
            ev.update(status='failed', failure_tags=['LIST_TIMEOUT'], errors=[str(exc)])
            totals['accounts_failed'] += 1
            totals['accounts_processed'] += 1
            ev['duration_s'] = round(time.time() - t0, 1)
            append_jsonl(events_path, ev)
            print(f'    -> FAIL 列表超时: {exc}')
            continue
        except Exception as exc:
            ev.update(status='failed', failure_tags=['LIST_ERROR'],
                      errors=[f'{type(exc).__name__}: {exc}'],
                      traceback=traceback.format_exc(limit=3))
            totals['accounts_failed'] += 1
            totals['accounts_processed'] += 1
            ev['duration_s'] = round(time.time() - t0, 1)
            append_jsonl(events_path, ev)
            print(f'    -> FAIL 列表异常: {type(exc).__name__}: {exc}')
            continue

        ev['articles_listed'] = len(works)
        totals['articles_listed'] += len(works)
        print(f'    列表返回 {len(works)} 篇')

        # --- 2) 幂等筛选 ---
        selected: list[dict[str, Any]] = []
        for w in works:
            if len(selected) >= args.max_articles_per_account:
                break
            uuid = str(w.get('workUuid') or '')
            url = normalize_url(w.get('workUrl'))
            if not uuid:
                continue
            if uuid in seen_uuids or (url and url in seen_urls):
                ev['articles_skipped_seen'] += 1
                totals['articles_skipped_seen'] += 1
                continue
            selected.append(w)
        ev['articles_selected'] = len(selected)
        print(f'    去重后待抓 {len(selected)} 篇（跳过已采 {ev["articles_skipped_seen"]} 篇）')

        if not selected:
            ev['status'] = 'ok_nothing_new'
            totals['accounts_ok'] += 1
            totals['accounts_processed'] += 1
            ev['duration_s'] = round(time.time() - t0, 1)
            append_jsonl(events_path, ev)
            continue

        # --- 3) 逐篇拉正文 ---
        for w in selected:
            uuid = str(w.get('workUuid') or '')
            title_preview = str(w.get('title') or '')[:40]
            print(f'    · get_work {uuid[:16]}… {title_preview}', flush=True)
            tw = time.time()
            try:
                body, _detail = api.fetch_body(uuid)
            except NotIndexedError as exc:
                ev['failure_tags'].append('NOT_INDEXED_3203')
                ev['errors'].append(f'{uuid}: {exc}')
                print('      -> 3203 未收录，跳过')
                continue
            except TimeoutError as exc:
                ev['failure_tags'].append('GET_WORK_TIMEOUT')
                ev['errors'].append(f'{uuid}: {exc}')
                print(f'      -> 超时 {time.time() - tw:.0f}s: {exc}')
                continue
            except Exception as exc:
                ev['failure_tags'].append('GET_WORK_ERROR')
                ev['errors'].append(f'{uuid}: {type(exc).__name__}: {exc}')
                print(f'      -> 异常 {type(exc).__name__}: {exc}')
                continue

            body = (body or '').strip()
            if not body:
                ev['failure_tags'].append('EMPTY_BODY')
                ev['errors'].append(f'{uuid}: empty content')
                print('      -> 正文为空')
                continue

            ev['articles_fetched'] += 1
            totals['articles_fetched'] += 1
            print(f'      -> 正文 {len(body)} 字，用时 {time.time() - tw:.0f}s')

            # --- 4) 打分 + 域过滤 + 落盘 ---
            try:
                score = score_article(w, body, acct, seen_urls)

                # 域相关性过滤：不命中九域 → 跳过写卡，记审计
                ok, reason = passes_domain_filter(score)
                if not ok:
                    ev.setdefault('filtered_out', []).append({
                        'uuid': uuid,
                        'title': str(w.get('title') or '')[:60],
                        'reason': reason,
                        'total_score': score.get('total_score', 0),
                    })
                    ev['failure_tags'].append('DOMAIN_FILTERED')
                    print(f'      -> 过滤 {reason} | {str(w.get("title") or "")[:40]}')
                    # 仍记 seen 避免重复抓
                    seen_uuids.add(uuid)
                    url_norm = normalize_url(w.get('workUrl'))
                    if url_norm:
                        seen_urls.add(url_norm)
                    save_seen(SEEN_UUIDS_PATH, seen_uuids, seen_urls)
                    continue

                body_path = write_body_file(out_dir, acct, uuid, body)
                card = build_card(w, body, acct, score, out_dir, body_path)
                md_path = write_card_md(out_dir, card, w, acct, score, body)
                card['card_md'] = str(md_path)
                totals['md_written'] += 1
                append_jsonl(MATERIAL_CARDS_PATH, card)
                totals['cards_written'] += 1
                ev['cards_written'] += 1
                ev['card_files'].append(str(md_path))
                card_paths.append(str(md_path))
                seen_uuids.add(uuid)
                if card['url']:
                    seen_urls.add(normalize_url(card['url']))
                save_seen(SEEN_UUIDS_PATH, seen_uuids, seen_urls)
                print(f'      -> 卡 {card["id"]} score={score.get("total_score")} '
                      f'angle={card["analysis_angle"]} quality={card["quality"]}')
                print(f'         md={md_path}')
            except Exception as exc:
                ev['failure_tags'].append('CARD_WRITE_ERROR')
                ev['errors'].append(f'{uuid}: {type(exc).__name__}: {exc}')
                print(f'      -> 落盘失败 {type(exc).__name__}: {exc}')

        # --- 5) 账号级状态 ---
        if ev['cards_written'] == ev['articles_selected'] and not ev['failure_tags']:
            ev['status'] = 'ok'
            totals['accounts_ok'] += 1
        elif ev['cards_written'] > 0:
            ev['status'] = 'partial'
            totals['accounts_partial'] += 1
        else:
            ev['status'] = 'failed'
            totals['accounts_failed'] += 1
        ev['failure_tags'] = sorted(set(ev['failure_tags']))
        ev['duration_s'] = round(time.time() - t0, 1)
        totals['accounts_processed'] += 1
        append_jsonl(events_path, ev)
        print(f'    账号状态={ev["status"]} 卡={ev["cards_written"]} tags={ev["failure_tags"]} {ev["duration_s"]}s')

    status = 'OK'
    if totals['cards_written'] == 0:
        status = 'FAILED'
    elif totals['accounts_failed'] or totals['accounts_partial']:
        status = 'PARTIAL'

    summary = {
        'mode': 'execute', 'status': status, 'ts': now_iso(),
        'out_dir': str(out_dir), 'events': str(events_path),
        'material_cards': str(MATERIAL_CARDS_PATH),
        'seen_uuids': str(SEEN_UUIDS_PATH),
        'scorer_mode': SCORER_MODE,
        'args': {
            'max_accounts': args.max_accounts,
            'max_articles_per_account': args.max_articles_per_account,
            'order': args.order, 'start_index': args.start_index,
        },
        **totals,
        'card_files': card_paths,
    }
    (out_dir / 'run_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding='utf-8')
    print('\n' + '=' * 78)
    print(f'RUN {status}: 账号 {totals["accounts_processed"]} (ok={totals["accounts_ok"]} '
          f'partial={totals["accounts_partial"]} failed={totals["accounts_failed"]} '
          f'skip3203={totals["accounts_skipped_not_indexed"]}) | '
          f'正文 {totals["articles_fetched"]} | 卡 {totals["cards_written"]}')
    print(f'summary: {out_dir / "run_summary.json"}')
    print('=' * 78)
    return summary


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description='RedFox 微信公众号 → 《科武纪元》素材卡采集器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check-mode', action='store_true',
                      help='只列计划采哪些账号 + 预估调用数，不抓取')
    mode.add_argument('--execute', action='store_true', help='真跑采集')
    p.add_argument('--max-accounts', type=int, default=10, help='单轮最多处理账号数（默认 10）')
    p.add_argument('--max-articles-per-account', type=int, default=3,
                   help='每账号最多抓几篇（默认 3）')
    p.add_argument('--out-dir', default='', help='产物目录（默认 runs/redfox_<timestamp>）')
    p.add_argument('--watchlist', default=str(WATCHLIST_PATH), help='watchlist 路径')
    p.add_argument('--order', choices=['fresh', 'index', 'name', 'watchlist'], default='fresh',
                   help='账号排序：fresh=最近发文优先(默认) / index=影响力 / name / watchlist 原序')
    p.add_argument('--start-index', type=int, default=0, help='从排序后第 N 个账号开始（分批续采）')
    p.add_argument('--only-account', action='append', default=[],
                   help='只处理指定 redfox_account（可重复）')
    p.add_argument('--only-domain', action='append', default=[],
                   help='只处理指定 domain_id（可重复）')
    p.add_argument('--no-seed-from-cards', action='store_true',
                   help='不用 material_cards.jsonl 的已有 url/uuid 做去重种子')
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)
    if not args.out_dir:
        args.out_dir = str(RUNS_ROOT / f'redfox_{now_stamp()}')

    watchlist_path = Path(args.watchlist)
    if not watchlist_path.exists():
        print(f'[FATAL] watchlist 不存在: {watchlist_path}', file=sys.stderr)
        return 2

    accounts_all = load_watchlist_accounts(watchlist_path)
    if not accounts_all:
        print(f'[FATAL] watchlist 中没有 route=={ROUTE_TAG} 的账号', file=sys.stderr)
        return 2

    pool = order_accounts(accounts_all, args.order)
    if args.only_domain:
        pool = [a for a in pool if a['domain_id'] in set(args.only_domain)]
    if args.only_account:
        want = set(args.only_account)
        pool = [a for a in pool if a['redfox_account'] in want]
    pool = pool[max(0, args.start_index):]
    planned = pool[:max(0, args.max_accounts)]

    seen = load_seen(SEEN_UUIDS_PATH)
    seen_uuids: set[str] = set(seen.get('uuids') or [])
    seen_urls: set[str] = {normalize_url(u) for u in (seen.get('urls') or []) if u}
    existing_urls, existing_uuids = (set(), set())
    if not args.no_seed_from_cards:
        existing_urls, existing_uuids = load_existing_card_keys(MATERIAL_CARDS_PATH)
        seen_urls |= existing_urls
        seen_uuids |= existing_uuids

    if args.check_mode:
        run_check_mode(accounts_all, planned, args, seen, existing_urls, existing_uuids)
        return 0

    if not planned:
        print('[WARN] 过滤后没有可处理账号，退出。')
        return 1

    summary = run_execute(planned, args, seen_uuids, seen_urls)
    save_seen(SEEN_UUIDS_PATH, seen_uuids, seen_urls)
    return 0 if summary.get('status') in ('OK', 'PARTIAL') else 1


if __name__ == '__main__':
    sys.exit(main())
