#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""weibo_search_collector.py — 《科武纪元》微博搜索采集器（零成本自采集路线）。

用 socialext-cft cookie 访问 s.weibo.com 搜索，提取正文摘要，打分过滤后写入素材卡。
不依赖任何付费 API。

用法：
    python3 weibo_search_collector.py --check-mode
    python3 weibo_search_collector.py --execute --query "碳纤维 复合材料" --max-items 10
    python3 weibo_search_collector.py --execute --domain materials --max-items 15
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any

TOOLS_DIR = Path('/root/workspace/科武纪元/工具脚本')
RADAR_DIR = Path('/root/workspace/科武纪元/学习记录/平台号观点雷达')
MATERIAL_CARDS_PATH = Path('/root/workspace/素材总线/kewu/material_cards.jsonl')
SEEN_UUIDS_PATH = RADAR_DIR / 'runs' / 'weibo_seen_uuids.json'
COOKIE_FILE = Path('/root/.hermes/weibo_cookies.txt')

DOMAIN_TAG = 'kewu'
PLATFORM_TAG = 'weibo'
ROUTE_TAG = 'weibo_search'
SOURCE_RUN_TYPE = 'weibo_search_kol'

KEWU_CORE_DOMAINS: set[str] = {
    'frontier_tech', 'geopolitics', 'biology', 'space', 'aviation',
    'ai', 'military', 'materials', 'energy',
    'material_science', 'orbital_mechanics', 'energy_harvesting',
    'quantum_computing', 'dyson_construction', 'strategic_materials',
}
MIN_TOTAL_SCORE: float = 3.0

# Quality classification thresholds (2026-08-26: raised from 50→200, add stock-noise filter)
_STOCK_NOISE_PATTERNS: tuple[str, ...] = (
    '涨停', '跌停', '龙头', '标的', '盘前', '盘后', '收盘', '开盘',
    'A股', '港股', '美股', '加仓', '减仓', '持仓', '止损', '止盈',
    '十倍', '百倍', '妖股', '打板', '接力', '首板',
)
_STOCK_NOISE_THRESHOLD: int = 3  # 3+ 个股市词 = 股评噪声


def _classify_quality(text: str) -> str:
    """Classify card quality: usable / thin / stocktalk_noise.

    - usable: clean_text >= 200 chars AND not stock-talk noise
    - stocktalk_noise: >= 3 stock-market keywords (regardless of length)
    - thin: everything else (short text, reposts, etc.)
    """
    if not text:
        return 'thin'
    hits = sum(1 for kw in _STOCK_NOISE_PATTERNS if kw in text)
    if hits >= _STOCK_NOISE_THRESHOLD:
        return 'stocktalk_noise'
    if len(text.strip()) >= 200:
        return 'usable'
    return 'thin'

# Per-domain search keywords
DOMAIN_QUERIES: dict[str, list[str]] = {
    'biology': ['合成生物学 基因编辑', '细胞治疗 基因治疗', 'CRISPR 基因编辑'],
    'materials': ['碳纤维 复合材料', '超导材料 突破', '稀土 半导体材料', '纳米材料 进展'],
    'ai': ['AI芯片 大模型', '具身智能 机器人', '算力 国产替代'],
    'energy': ['可控核聚变 EAST', '储能 电池突破', '核电 小型堆'],
    'frontier_tech': ['量子计算 突破', '脑机接口 进展', '核聚变 亿度'],
    'space': ['商业航天 火箭回收', '载人航天 空间站', '深空探测 月球'],
    'aviation': ['无人机 集群', '航空发动机 国产', '战斗机 六代机'],
    'military': ['国防 军事装备', '导弹防御 系统', '军演 实兵对抗'],
    'geopolitics': ['出口管制 实体清单', '中美科技 博弈', '芯片封锁 制裁'],
}

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

# Load scorer
score_and_classify_item = None
get_domain_for_keywords = None
STABLE_DOMAINS: dict[str, Any] = {}
try:
    from kewu_domain_scorer import score_and_classify_item as _sci, get_domain_for_keywords as _gdk
    score_and_classify_item = _sci
    get_domain_for_keywords = _gdk
except Exception:
    pass
try:
    from kewu_domain_ontology import STABLE_DOMAINS as _SD
    STABLE_DOMAINS = _SD
except Exception:
    pass

SCORER_MODE = 'score_and_classify_item' if score_and_classify_item else 'fallback_keyword'

WEIBO_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


def now_iso() -> str:
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def sha12(text: str) -> str:
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]


def load_cookie_string() -> str:
    """Read Netscape cookie file → 'k=v; k=v' string."""
    if not COOKIE_FILE.exists():
        return ''
    pairs: list[str] = []
    with open(COOKIE_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('# Netscape') or line.startswith('# https'):
                continue
            # Netscape 格式: HttpOnly cookie 行以 #HttpOnly_ 开头，不能跳过
            parts = line.split('\t')
            if len(parts) >= 7:
                pairs.append(f'{parts[5]}={parts[6]}')
    return '; '.join(pairs)


def domain_label(domain_id: str) -> str:
    meta = STABLE_DOMAINS.get(domain_id) if isinstance(STABLE_DOMAINS, dict) else None
    if isinstance(meta, dict):
        for key in ('name', 'domain_name', 'label', 'cn_name'):
            val = meta.get(key)
            if isinstance(val, str) and val:
                return val
    return domain_id


def passes_domain_filter(score: dict[str, Any]) -> tuple[bool, str]:
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


def search_weibo(query: str, cookie_str: str, max_pages: int = 2) -> list[dict[str, Any]]:
    """Search s.weibo.com, return list of {nick, text, mid, clean_text}."""
    results: list[dict[str, Any]] = []
    import subprocess
    
    for page in range(1, max_pages + 1):
        url = f'https://s.weibo.com/weibo?q={urllib.parse.quote(query)}&typeall=1&suball=1&page={page}'
        try:
            r = subprocess.run([
                'curl', '-sS', '--max-time', '15',
                '-H', f'Cookie: {cookie_str}',
                '-H', f'User-Agent: {WEIBO_UA}',
                url,
            ], capture_output=True, text=True, timeout=20)
        except Exception:
            break
        
        html = r.stdout
        if not html or 'passport.weibo' in html[:500]:
            break
        
        nicks = re.findall(r'nick-name="([^"]+)"', html)
        contents_raw = re.findall(r'<p class="txt"[^>]*>(.*?)</p>', html, re.DOTALL)
        mids = re.findall(r'mid="(\d+)"', html)
        
        for i, (nick, content) in enumerate(zip(nicks, contents_raw)):
            clean = re.sub(r'<[^>]+>', '', content).strip()
            clean = re.sub(r'\s+', ' ', clean)
            if len(clean) < 20:
                continue
            mid = mids[i] if i < len(mids) else sha12(nick + clean)
            results.append({
                'nick': nick,
                'text': clean,
                'mid': mid,
                'clean_text': clean,
            })
        
        time.sleep(1)
        if len(results) >= 30:
            break
    
    # Dedupe by mid
    seen_mids: set[str] = set()
    unique: list[dict[str, Any]] = []
    for r in results:
        if r['mid'] not in seen_mids:
            seen_mids.add(r['mid'])
            unique.append(r)
    return unique


def score_post(post: dict[str, Any], domain_hint: str) -> dict[str, Any]:
    item = {
        'title': post['nick'] + ': ' + post['clean_text'][:60],
        'summary': post['clean_text'][:200],
        'body': post['clean_text'],
        'url': f"https://weibo.com/detail/{post['mid']}",
        'published_at': now_iso()[:10],
        'source_group_key': 'domestic_kol',
        'source_role': 'secondary',
    }
    if score_and_classify_item is not None:
        try:
            res = score_and_classify_item(item, None, set())
            if isinstance(res, dict):
                res['_scorer'] = 'score_and_classify_item'
                return res
        except Exception:
            pass
    
    blob = f"{item['title']} {item['summary']} {post['clean_text'][:4000]}"
    domain_scores: list[tuple[str, float]] = []
    if callable(get_domain_for_keywords):
        try:
            domain_scores = list(get_domain_for_keywords(blob))[:3]
        except Exception:
            domain_scores = []
    if not domain_scores:
        domain_scores = [(domain_hint, 1.0)]
    return {
        'total_score': max(s for _, s in domain_scores) if domain_scores else 1.0,
        'domain_scores': domain_scores,
        'title_used': item['title'],
    }


def build_card(post: dict[str, Any], score: dict[str, Any], domain_hint: str) -> dict[str, Any]:
    mid = post['mid']
    title = f"@{post['nick']}: {post['clean_text'][:50]}"
    
    labels: list[str] = []
    for entry in score.get('domain_scores') or []:
        did = entry[0] if isinstance(entry, (list, tuple)) else entry
        lab = domain_label(str(did))
        if lab and lab not in labels:
            labels.append(lab)
    if not labels:
        labels = [domain_hint]
    
    total = score.get('total_score') or 0.0
    conf = min(total / 10.0, 0.99) if total > 0 else 0.3
    
    return {
        'id': f'kewu_wb_{sha12(mid)}',
        'domain': DOMAIN_TAG,
        'created_at': now_iso(),
        'source_run_type': SOURCE_RUN_TYPE,
        'source_run': 'weibo_search',
        'candidate_id': mid,
        'source': post['nick'],
        'platform': PLATFORM_TAG,
        'title': title,
        'url': f"https://weibo.com/detail/{mid}",
        'content_excerpt': post['clean_text'][:600],
        'analysis_angle': '|'.join(labels[:3]),
        'confidence_score': round(conf, 2),
        'quality': _classify_quality(post['clean_text']),
    }


def run_check_mode(args):
    print('=' * 78)
    print('微博搜索采集器 — CHECK MODE')
    print('=' * 78)
    cookie = load_cookie_string()
    print(f'cookie: {COOKIE_FILE} ({len(cookie)} chars)')
    if args.domain:
        queries = DOMAIN_QUERIES.get(args.domain, [args.query or '量子计算'])
        print(f'目标域: {args.domain}')
    elif args.query:
        queries = [args.query]
        print(f'自定义查询: {args.query}')
    else:
        queries = [q for qlist in DOMAIN_QUERIES.values() for q in qlist]
        print(f'全域扫描 ({len(queries)} 个查询)')
    print(f'每查询最多: {args.max_items} 条')
    print(f'预估查询次数: {len(queries)}')
    print(f'打分模块: {SCORER_MODE}')
    print('CHECK MODE 结束：未调用任何接口。')
    return {'mode': 'check', 'queries': len(queries)}


def run_execute(args):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = RADAR_DIR / 'runs' / f'weibo_{ts}'
    (out_dir / 'cards').mkdir(parents=True, exist_ok=True)
    events_path = out_dir / 'events.jsonl'
    
    cookie = load_cookie_string()
    if not cookie:
        print('[FATAL] 无微博 cookie')
        return {'status': 'FAILED'}
    
    if args.domain:
        queries = DOMAIN_QUERIES.get(args.domain, [])
    elif args.query:
        queries = [args.query]
    else:
        queries = [q for qlist in DOMAIN_QUERIES.values() for q in qlist]
    
    domain_hint = args.domain or 'kewu'
    
    # Load seen
    seen: set[str] = set()
    if SEEN_UUIDS_PATH.exists():
        seen = set(json.loads(SEEN_UUIDS_PATH.read_text()).get('mids', []))
    
    totals = {'posts_found': 0, 'posts_filtered': 0, 'cards_written': 0}
    
    for qi, query in enumerate(queries, 1):
        print(f'\n[{qi}/{len(queries)}] 搜索: {query}')
        posts = search_weibo(query, cookie, max_pages=2)
        
        ev = {
            'ts': now_iso(), 'query': query, 'domain_hint': domain_hint,
            'posts_found': len(posts), 'filtered_out': [], 'cards': [],
        }
        
        kept = 0
        for post in posts[:args.max_items]:
            totals['posts_found'] += 1
            
            if post['mid'] in seen:
                continue
            
            score = score_post(post, domain_hint)
            ok, reason = passes_domain_filter(score)
            
            if not ok:
                ev['filtered_out'].append({
                    'nick': post['nick'],
                    'text': post['clean_text'][:50],
                    'reason': reason,
                })
                totals['posts_filtered'] += 1
                seen.add(post['mid'])
                continue
            
            card = build_card(post, score, domain_hint)
            
            # Write md
            slug = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]', '_', card['title'])[:40]
            md_path = out_dir / 'cards' / f'{slug}_{sha12(post["mid"])}.md'
            md_path.write_text(
                f'---\nid: {card["id"]}\nsource: {card["source"]}\nplatform: weibo\n'
                f'angle: {card["analysis_angle"]}\nscore: {card["confidence_score"]}\n'
                f'url: {card["url"]}\n---\n\n{card["content_excerpt"]}\n',
                encoding='utf-8'
            )
            card['card_md'] = str(md_path)
            
            # Append to material_cards
            with open(MATERIAL_CARDS_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(card, ensure_ascii=False) + '\n')
            
            seen.add(post['mid'])
            totals['cards_written'] += 1
            kept += 1
            ev['cards'].append({'nick': post['nick'], 'title': card['title'][:40], 'score': card['confidence_score']})
            print(f'  ✅ @{post["nick"]}: {post["clean_text"][:60]}... score={card["confidence_score"]}')
        
        print(f'  保留 {kept}｜过滤 {len(ev["filtered_out"])}')
        append_jsonl(events_path, ev)
        time.sleep(2)
    
    # Save seen
    SEEN_UUIDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEN_UUIDS_PATH.write_text(json.dumps({'mids': list(seen)}, ensure_ascii=False))
    
    status = 'OK' if totals['cards_written'] > 0 else 'NO_RESULTS'
    summary = {
        'mode': 'execute', 'status': status, 'ts': now_iso(),
        'out_dir': str(out_dir), 'scorer': SCORER_MODE,
        **totals, 'seen_mids': len(seen),
    }
    (out_dir / 'run_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding='utf-8')
    
    print(f'\n{"=" * 78}')
    print(f'RUN {status}: 搜索 {len(queries)} 查询 | '
          f'帖子 {totals["posts_found"]} | 过滤 {totals["posts_filtered"]} | '
          f'卡 {totals["cards_written"]}')
    print(f'summary: {out_dir / "run_summary.json"}')
    print(f'{"=" * 78}')
    return summary


def append_jsonl(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')


def main():
    p = argparse.ArgumentParser(description='微博搜索采集器')
    p.add_argument('--check-mode', action='store_true')
    p.add_argument('--execute', action='store_true')
    p.add_argument('--query', type=str, default=None, help='自定义搜索词')
    p.add_argument('--domain', type=str, default=None, help='指定域(biology/materials/ai/...)用预设关键词')
    p.add_argument('--max-items', type=int, default=10, help='每查询最多保留几条')
    args = p.parse_args()
    
    if args.check_mode:
        run_check_mode(args)
    elif args.execute:
        run_execute(args)
    else:
        p.print_help()


if __name__ == '__main__':
    main()
