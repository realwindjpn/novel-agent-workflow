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
from pathlib import Path

# ── paths ──
BASE = Path('/root/workspace/科武纪元')
TOOL = BASE / '工具脚本'
OUT_BASE = BASE / '学习记录/平台号观点雷达/runs'
WATCH = BASE / '学习记录/平台号观点雷达/platform_watchlist.json'
COLLECT_WEB = Path('/root/.hermes/skills/research/web-data-collection-suite/scripts/collect_web.py')
ANYSEARCH_CLI = Path('/root/workspace/IMA素材/external_skills/anysearch-skill_20260604/repo/scripts/anysearch_cli.py')

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


# ── P0 freshness gate ──
def _parse_relative_date(text: str) -> str:
    """Parse Weibo/Chinese relative time strings to ISO date.
    Returns '' if unparseable.
    """
    now = datetime.date.today()
    if not text:
        return ''
    t = text.strip().lower()
    # "昨天", "前天", "X天前", "X小时前"
    m = re.search(r'(\d+)\s*(?:天前|天以前|days?\s*ago)', t)
    if m:
        return (now - datetime.timedelta(days=int(m.group(1)))).isoformat()
    if '昨天' in t or 'yesterday' in t:
        return (now - datetime.timedelta(days=1)).isoformat()
    if '前天' in t:
        return (now - datetime.timedelta(days=2)).isoformat()
    m = re.search(r'(\d+)\s*(?:小时前|hours?\s*ago)', t)
    if m:
        return now.isoformat()
    # Explicit ISO / YYYY-MM-DD / YYYY.MM.DD / YYYY/MM/DD
    m = re.search(r'(20\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})', t)
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
    return ''


def is_stale_kol_item(item: dict, max_age_days: int = 7) -> tuple[bool, str]:
    """Check freshness. Returns (is_stale, reason_tag).

    Rules:
      1. Has published_at → parse; >max_age_days → STALE_KOL_ARTICLE
      2. No published_at but evidence has year clue (e.g. "2024年", "2025年")
         and year < current year → DATE_OLD_YEAR
      3. No date at all → DATE_UNKNOWN (not stale, but lower confidence)
    """
    pub = (item.get('published_at') or '').strip()
    evidence = (item.get('evidence') or '') + ' ' + (item.get('title') or '')

    # Try published_at first
    if pub:
        parsed = _parse_relative_date(pub)
        if not parsed:
            # try raw ISO
            parsed = pub[:10] if re.match(r'20\d{2}-\d{2}-\d{2}', pub) else ''
        if parsed:
            try:
                pub_date = datetime.date.fromisoformat(parsed)
                age = (datetime.date.today() - pub_date).days
                if age > max_age_days:
                    return True, 'STALE_KOL_ARTICLE'
                if pub_date.year < datetime.date.today().year:
                    return True, 'DATE_OLD_YEAR'
            except (ValueError, TypeError):
                pass

    # Scan evidence/title for year clues
    year_matches = re.findall(r'(20\d{2})年', evidence)
    if year_matches:
        max_old_year = max(int(y) for y in year_matches)
        if max_old_year < datetime.date.today().year:
            return True, 'DATE_OLD_YEAR'

    # No date info at all
    if not pub:
        return False, 'DATE_UNKNOWN'

    return False, ''


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
        hits.append({'title': text[:120], 'url': url, 'body': text[:500]})
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
        return '', 'BILIBILI_FETCH_FAIL'

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

    # ── 微博：mobile API with cookie → collect_web → urllib ──
    if 'weibo.com' in url or 'm.weibo.cn' in url or 'h5.video.weibo.com' in url:
        import urllib.request, urllib.parse
        # Extract status_id from URL
        _status_id = ''
        for _sp in [
            r'h5\.video\.weibo\.com/show/\d+:([0-9A-Za-z]+)',
            r'm\.weibo\.cn/detail/([0-9A-Za-z]+)',
            r'm\.weibo\.cn/status/([0-9A-Za-z]+)',
            r'weibo\.com/[^/\s]+/status/([0-9A-Za-z]+)',
        ]:
            _sm = re.search(_sp, url)
            if _sm:
                _status_id = _sm.group(1)
                break
        if not _status_id:
            # Try last path segment as status_id (for weibo.com/uid/mid format)
            _parts = url.rstrip('/').split('/')
            if len(_parts) >= 2 and re.fullmatch(r'[0-9A-Za-z]+', _parts[-1]):
                _status_id = _parts[-1]
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
                    _wb = _item.get('text', '') or _item.get('body', '')
                    if _wb and len(_wb) > 30:
                        return _wb[:500], ''
            except (json.JSONDecodeError, IndexError):
                pass

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
    if it.get('failure_tag') == 'DATE_UNKNOWN':
        score = min(score, 0.55)
    return round(min(score, 0.9), 2)


def build_mirofish_package(items: list[dict]) -> dict:
    """将discovery items转为MiroFish入口格式。

    Feed纳入条件：body_status 为 'fetched' 或有 excerpt 的条目
    （evidence >= 15 chars），排除主页/空间页/搜索页和 NOISE。
    """
    cards = []
    for it in items:
        if it.get('material_policy') == 'NOISE':
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
    ap.add_argument('--dry-run-mirofish', action='store_true', help='只产出discovery，不跑MiroFish后段')
    ap.add_argument('--out-dir', type=str, default='', help='输出目录')
    args = ap.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else RUN_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    discovery_path = Path(args.discovery_json) if args.discovery_json else out_dir / 'platform_discovery.json'
    mirofish_path = out_dir / 'platform_mirofish_feed_package.json'
    body_report_path = out_dir / 'body_fetch_report.json'

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

    if args.limit > 0:
        accounts = accounts[:args.limit]

    # platform filter
    plat_filter = set()
    if args.platform:
        plat_map = {'wechat': '微信公众号', 'bilibili': 'B站', 'weibo': '微博', 'zhihu': '知乎'}
        plat_filter.add(plat_map.get(args.platform, args.platform))

    # resume: load existing items
    existing_items: list[dict] = []
    existing_urls: set[str] = set()
    if args.resume and discovery_path.exists():
        try:
            old = json.loads(discovery_path.read_text(encoding='utf-8'))
            existing_items = old.get('items', [])
            existing_urls = {it['url'] for it in existing_items if it.get('url')}
            print(f'[resume] loaded {len(existing_items)} existing items from {discovery_path}')
        except Exception:
            pass

    # ── A. URL Discovery ──
    all_items: list[dict] = list(existing_items)
    errors: list[dict] = []
    total_queries = 0

    platform_aliases = {
        '微信公众号': 'wechat', '公众号': 'wechat',
        'B站': 'bilibili', '微博': 'weibo', '知乎': 'zhihu', '网站': 'generic',
    }

    for acc in accounts:
        name = acc['name']
        platforms = acc.get('platform_candidates', [])
        for plat_raw in platforms:
            plat: str = platform_aliases.get(plat_raw, plat_raw) or plat_raw
            if plat == 'generic':
                continue
            if plat_filter and plat_raw not in plat_filter and plat not in plat_filter:
                continue
            total_queries += 1
            print(f'  [{total_queries}] {name} · {plat} ...', end=' ', flush=True)
            t0 = time.time()
            hits = discover_for_account(acc, plat, args.timeout_sec)
            dt = time.time() - t0
            if not hits:
                err_tag = 'NO_HITS'
                errors.append({'account': name, 'platform': plat, 'error': err_tag,
                               'fallback_tried': ['collect_web', 'anysearch', 'ddgs']})
                print(f'0 hits ({dt:.1f}s)')
                continue

            found = 0
            for h in hits:
                url = h.get('url', '')
                if not url or url in existing_urls:
                    continue
                existing_urls.add(url)
                item = dict(EMPTY_ITEM)
                item['account'] = name
                item['platform'] = plat
                item['query'] = h.get('_route', '')
                item['url'] = url
                item['title'] = h.get('title', '')
                item['source_route'] = h.get('_route', 'unknown')
                item['discovery_status'] = 'discovered'
                item['failure_tag'] = ''
                # Tag with domain_id from watchlist
                item['domain_id'] = acc.get('domain_id', '')
                item['domain_name'] = acc.get('domain_name', '')

                # score for noise filter
                sc = score_item(name, plat, h)
                item['body_status'] = 'pending'
                disc_body = h.get('body', '') or ''
                disc_title = h.get('title', '') or ''
                # 优先用body，其次用真实title（排除占位符）
                if disc_body and len(disc_body) > 5:
                    item['evidence'] = disc_body[:500]
                elif disc_title and 'candidate' not in disc_title.lower() and len(disc_title) > 10:
                    item['evidence'] = disc_title[:500]
                else:
                    item['evidence'] = ''

                all_items.append(item)
                found += 1
            print(f'{found} new ({dt:.1f}s)')

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
        # P0: freshness gate — must run BEFORE material_policy_tag
        stale, reason = is_stale_kol_item(it, max_age_days=7)
        if stale:
            it['material_policy'] = 'NOISE'
            it['failure_tag'] = reason
        else:
            if reason == 'DATE_UNKNOWN':
                it['failure_tag'] = 'DATE_UNKNOWN'
            it['material_policy'] = material_policy_tag(it)

    # ── D. Save platform_discovery.json ──
    stats = {
        'total_queries': total_queries,
        'discovered': sum(1 for i in all_items if i.get('discovery_status') == 'discovered'),
        'body_fetched': sum(1 for i in all_items if i.get('body_status') == 'fetched'),
        'excerpt_only': sum(1 for i in all_items if i.get('body_status') == 'excerpt_only'),
        'fetch_fail': sum(1 for i in all_items if i.get('body_status') == 'fetch_fail'),
        'skipped_non_article': sum(1 for i in all_items if i.get('body_status') == 'skipped_non_article'),
        'errors': len(errors),
        'platform_signal': sum(1 for i in all_items if i.get('material_policy') == 'PLATFORM_SIGNAL'),
        'discovery_only': sum(1 for i in all_items if i.get('material_policy') == 'DISCOVERY_ONLY'),
        'noise': sum(1 for i in all_items if i.get('material_policy') == 'NOISE'),
        # P0: freshness stats
        'stale_filtered': sum(1 for i in all_items if i.get('failure_tag') in ('STALE_KOL_ARTICLE', 'DATE_OLD_YEAR')),
        'date_unknown': sum(1 for i in all_items if i.get('failure_tag') == 'DATE_UNKNOWN'),
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
    # Track results per domain
    domain_results = {}  # domain_id → set of account names with results
    accounts_with_results = set()
    for it in all_items:
        if it.get('material_policy') in ('PLATFORM_SIGNAL', 'DISCOVERY_ONLY'):
            acc_name = it.get('account', '')
            accounts_with_results.add(acc_name)
            did = it.get('domain_id', '')
            if did:
                domain_results.setdefault(did, set()).add(acc_name)
            else:
                # Legacy: infer domain from account→domain_map
                for d_id, acc_names in domain_map.items():
                    if acc_name in acc_names:
                        domain_results.setdefault(d_id, set()).add(acc_name)

    total_accounts = len(accounts)
    domains_with_results = len(domain_results)
    total_domains = len(domain_map) if domain_map else 1

    stale_platform = sum(
        1 for i in all_items
        if i.get('material_policy') == 'PLATFORM_SIGNAL'
        and i.get('failure_tag') in ('STALE_KOL_ARTICLE', 'DATE_OLD_YEAR')
    )

    # Domain coverage gate: 9-domain Dyson tree
    coverage_gate = watch.get('ingest_rules', {}).get('domain_coverage_gate', {})
    min_domains = coverage_gate.get('min_domains_with_results', 2)
    min_accounts_total = coverage_gate.get('min_accounts_with_results_total', 3)

    # Determine health status
    failure_tags = []
    if domains_with_results < min_domains:
        failure_tags.append(f'DOMAINS_ONLY_{domains_with_results}_of_{total_domains}')
    if len(accounts_with_results) < min_accounts_total:
        failure_tags.append(f'ACCOUNTS_ONLY_{len(accounts_with_results)}_WITH_RESULTS')
    if stale_platform > 0:
        failure_tags.append(f'STALE_PLATFORM={stale_platform}')

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
    elif stale_platform > 0:
        sidecar_health = 'ACTION'
        sidecar_health_reason = f'stale_PLATFORM={stale_platform} > 0'
    else:
        sidecar_health = 'HEALTHY'
        sidecar_health_reason = ''

    stats['coverage_pct'] = round(100 * len(accounts_with_results) / total_accounts) if total_accounts else 0
    stats['stale_platform'] = stale_platform
    stats['accounts_with_results'] = len(accounts_with_results)
    stats['domains_total'] = total_domains
    stats['domains_with_results'] = domains_with_results
    stats['silent_domains'] = silent_domains
    stats['domain_coverage_detail'] = {did: len(accs) for did, accs in domain_results.items()}
    stats['sidecar_health'] = sidecar_health
    stats['sidecar_health_reason'] = sidecar_health_reason
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
        f'- discovered: {stats["discovered"]}',
        f'- body_fetched: {stats["body_fetched"]}',
        f'- excerpt_only: {stats["excerpt_only"]}',
        f'- fetch_fail: {stats["fetch_fail"]}',
        f'- skipped_non_article: {stats["skipped_non_article"]}',
        f'- platform_signal: {stats["platform_signal"]}',
        f'- discovery_only: {stats["discovery_only"]}',
        f'- noise: {stats["noise"]}',
        f'- errors: {stats["errors"]}',
        f'- stale_filtered: {stats.get("stale_filtered", 0)}',
        f'- date_unknown: {stats.get("date_unknown", 0)}',
        f'- coverage_pct: {stats.get("coverage_pct", 0)}%',
        f'- domains_with_results: {stats.get("domains_with_results", 0)}/{stats.get("domains_total", 0)}',
        f'- silent_domains: {", ".join(stats.get("silent_domains", [])) or "none"}',
        f'- sidecar_health: **{stats.get("sidecar_health", "N/A")}**',
        f'- sidecar_health_reason: {stats.get("sidecar_health_reason", "")}',
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
        'stats': stats,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
