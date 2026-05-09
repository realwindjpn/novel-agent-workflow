#!/usr/bin/env python3
"""科武纪元·素材采集调度器 v3

整合全部采集技能，按平台特性调用专用工具。
不再只用一种方式，而是：
  微信 → wechat-article-spider 正则直抓
  B站  → API搜索 + 字幕下载（cookie已配）
  观察者网 → crawl4ai 专栏爬取
  中科院 → crawl4ai列表 + 浏览器正文
  物理所 → crawl4ai 列表+正文
  热点   → 百度热搜 + B站热门
  英文RSS→ urllib 并行抓取

RTK压缩：所有结果写文件，只返回统计摘要。

用法：python3 orchestrator_v3.py [模式]
  模式: all / wechat / bili / guancha / cas / iop / hot / rss / cpj

采集源配置：微信URL从配置文件读取，其他按关键词自动搜。
"""

import json, os, re, sys, time, html, subprocess, shutil
import urllib.request
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

# 路径
BASE = Path("/root/workspace/科武纪元/硬科学素材")
TODAY = datetime.now().strftime("%Y%m%d")
OUT_DIR = BASE / f"采集_{TODAY}"
OUT_DIR.mkdir(exist_ok=True)

RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(exist_ok=True)

CARDS_OUT = OUT_DIR / "素材卡"
CARDS_OUT.mkdir(exist_ok=True)

# 配置
BILI_COOKIE = "/root/.hermes/bilibili_cookies.txt"

# 采集源配置（用户可在此添加微信链接）
CONFIG = {
    "cpj_wechat": [],  # 差评君微信文章URL，用户转发后填入
    "bili_keywords": [
        "量子计算 科普",
        "核聚变 EAST",
        "FAST 天眼 新发现",
        "存算一体芯片",
        "外骨骼 机器人",
        "差评君 科技",
    ],
    "guancha_authors": {
        "沈逸": "https://www.guancha.cn/ShenYi",
        "高志凯": "https://www.guancha.cn/gaozhikai",
    },
    "cas_keywords": ["量子计算", "核聚变", "人造太阳", "FAST", "外骨骼", "AI芯片"],
    "rss_feeds": {
        "ArsTechnica": "https://feeds.arstechnica.com/arstechnica/index",
        "TechCrunch": "https://techcrunch.com/feed/",
        "NewScientist": "https://www.newscientist.com/subject/technology/feed/",
        "DefenseNews": "https://www.defensenews.com/arc/outboundfeeds/rss/",
    },
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def filter_crawl4ai_logs(text):
    prefixes = ('[INIT]', '[FETCH]', '[SCRAPE]', '[COMPLETE]', '| ✓')
    return '\n'.join(l for l in text.splitlines() if not l.startswith(prefixes))

def run_crawl4ai(url, timeout=60):
    """安全调用 crawl4ai-skill，避免 shell 注入并保留错误信息。"""
    if not shutil.which("crawl4ai-skill"):
        return False, "crawl4ai-skill 不存在"
    try:
        result = subprocess.run(
            ["crawl4ai-skill", "crawl", url, "--format", "fit_markdown"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, "crawl4ai超时"
    if result.returncode != 0:
        err = (result.stderr.strip() or result.stdout.strip())[:300]
        return False, f"crawl4ai失败: {err}"
    return True, filter_crawl4ai_logs(result.stdout)

def clean_xml_text(s):
    """清理 RSS/Atom 文本：CDATA、HTML 实体、标签、多余空白。"""
    if not s:
        return ""
    s = re.sub(r'^\s*<!\[CDATA\[(.*?)\]\]>\s*$', r'\1', s, flags=re.S)
    s = html.unescape(s)
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def extract_first(pattern, text, flags=re.S | re.I):
    m = re.search(pattern, text, flags)
    return clean_xml_text(m.group(1)) if m else ""

def extract_rss_items(xml, limit=4):
    """按 item/entry 解析 RSS/Atom，避免 channel/feed 标题混入。"""
    articles = []
    items = re.findall(r'<item\b[^>]*>(.*?)</item>', xml, flags=re.S | re.I)
    if items:
        for item in items[:limit]:
            title = extract_first(r'<title[^>]*>(.*?)</title>', item)
            link = extract_first(r'<link[^>]*>(.*?)</link>', item)
            if not link:
                link = extract_first(r'<guid[^>]*isPermaLink=["\']true["\'][^>]*>(.*?)</guid>', item)
            date = extract_first(r'<pubDate[^>]*>(.*?)</pubDate>', item)
            if title:
                articles.append({"title": title, "link": link, "date": date})
        return articles
    entries = re.findall(r'<entry\b[^>]*>(.*?)</entry>', xml, flags=re.S | re.I)
    for entry in entries[:limit]:
        title = extract_first(r'<title[^>]*>(.*?)</title>', entry)
        link = ""
        m = re.search(r'<link[^>]*href=["\']([^"\']+)["\']', entry, flags=re.S | re.I)
        if m:
            link = html.unescape(m.group(1)).strip()
        if not link:
            link = extract_first(r'<link[^>]*>(.*?)</link>', entry)
        date = extract_first(r'<(?:updated|published)[^>]*>(.*?)</(?:updated|published)>', entry)
        if title:
            articles.append({"title": title, "link": link, "date": date})
    return articles

def md_cell(s):
    return str(s or "").replace("|", "\\|").replace("\n", " ")

# ========== 微信采集（wechat-article-spider）==========

def crawl_wechat(url, output_path=None):
    """微信公众号文章正则直抓"""
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
                'Accept-Language': 'zh-CN,zh;q=0.9'
            }),
            timeout=30
        )
        raw = r.read().decode('utf-8')
        
        # 提取标题
        m = re.search(r'<h1[^>]*class="[^"]*rich_media_title[^"]*"[^>]*>(.*?)</h1>', raw, re.S)
        title = html.unescape(re.sub('<.*?>', '', m.group(1))).strip() if m else '微信文章'
        
        # 提取正文 js_content
        mc = re.search(r'<div[^>]*id="js_content"[^>]*>(.*?)(?:<script nonce=|<script type="text/javascript")', raw, re.S)
        body = mc.group(1) if mc else raw
        
        # 清洗
        body = re.sub(r'<br\s*/?>', '\n', body, flags=re.I)
        body = re.sub(r'</(p|section|div|h\d|li)>', '\n', body, flags=re.I)
        body = re.sub(r'<script.*?</script>|<style.*?</style>', '', body, flags=re.S|re.I)
        body = html.unescape(re.sub(r'<[^>]+>', '', body))
        lines = [x.strip() for x in body.splitlines() if x.strip()]
        text = '\n'.join(lines)
        
        if output_path:
            out = Path(output_path)
        else:
            safe_title = title[:30].replace('/','_').replace('\\','_')
            out = RAW_DIR / f"wechat_{safe_title}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f'# {title}\n\n原文：{url}\n\n---\n\n{text}', encoding='utf-8')
        
        return True, len(text), title
    except Exception as e:
        return False, 0, str(e)

# ========== B站采集（chinese-expert-research）==========

def parse_bili_cookies():
    """解析Netscape格式B站cookie"""
    if not os.path.exists(BILI_COOKIE):
        return {}
    cookies = {}
    with open(BILI_COOKIE) as f:
        for line in f:
            line = line.strip()
            if not line or (line.startswith('#') and not line.startswith('#HttpOnly_')):
                continue
            if line.startswith('#HttpOnly_'):
                line = line[10:]
            parts = line.split('\t')
            if len(parts) >= 7:
                cookies[parts[5]] = parts[6]
    return cookies

def search_bilibili(keywords):
    """B站API搜索视频"""
    cookies = parse_bili_cookies()
    if not cookies:
        log("  B站cookie不存在")
        return []
    
    cookie_str = '; '.join(f"{k}={v}" for k, v in cookies.items())
    results = []
    
    for kw in keywords:
        try:
            url = f"https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={quote(kw)}&page=1"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Cookie', cookie_str)
            req.add_header('Referer', 'https://www.bilibili.com')
            
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            
            if data.get('code') == 0:
                videos = data['data'].get('result', [])[:5]
                for v in videos:
                    results.append({
                        "title": re.sub(r'<[^>]+>', '', v.get('title', '')),
                        "bvid": v.get('bvid', ''),
                        "author": v.get('author', ''),
                        "keyword": kw,
                    })
            time.sleep(1)
        except Exception as e:
            log(f"  B站搜索失败 [{kw}]: {e}")
    
    return results

def download_bili_subtitle(bvid, output_path):
    """下载B站视频字幕（无字幕时降级用弹幕）"""
    cookies = parse_bili_cookies()
    if not cookies:
        return False, "无cookie"
    
    cookie_str = '; '.join(f"{k}={v}" for k, v in cookies.items())
    
    try:
        # 获取CID
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        req.add_header('Cookie', cookie_str)
        req.add_header('Referer', 'https://www.bilibili.com')
        
        resp = urllib.request.urlopen(req, timeout=10)
        view_data = json.loads(resp.read())
        cid = view_data['data']['cid']
        title = view_data['data']['title']
        
        # 获取字幕
        url2 = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
        req2 = urllib.request.Request(url2)
        req2.add_header('User-Agent', 'Mozilla/5.0')
        req2.add_header('Cookie', cookie_str)
        
        resp2 = urllib.request.urlopen(req2, timeout=10)
        player_data = json.loads(resp2.read())
        subs = player_data['data']['subtitle'].get('subtitles', [])
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if subs:
            # 有字幕
            sub_url = subs[0]['subtitle_url']
            if sub_url.startswith('//'):
                sub_url = 'https:' + sub_url
            
            req3 = urllib.request.Request(sub_url)
            req3.add_header('User-Agent', 'Mozilla/5.0')
            resp3 = urllib.request.urlopen(req3, timeout=10)
            sub_data = json.loads(resp3.read())
            body = sub_data.get('body', [])
            full_text = '\n'.join([item.get('content', '') for item in body])
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# BV: {bvid} | {title}\n# 字幕\n\n{full_text}")
            
            return True, len(full_text)
        else:
            # 无字幕 → 降级用弹幕
            try:
                req4 = urllib.request.Request(f'https://comment.bilibili.com/{cid}.xml')
                req4.add_header('User-Agent', 'Mozilla/5.0')
                resp4 = urllib.request.urlopen(req4, timeout=10)
                raw_xml = resp4.read()
                
                # B站弹幕可能是 gzip 压缩或特殊编码
                import gzip
                try:
                    text = gzip.decompress(raw_xml).decode('utf-8', errors='ignore')
                except:
                    text = raw_xml.decode('utf-8', errors='ignore')
                
                danmaku_list = re.findall(r'<d[^>]*>(.*?)</d>', text)
                # 清理弹幕（去HTML实体）
                danmaku_clean = [html.unescape(d) for d in danmaku_list if len(d) > 2]
                
                if danmaku_clean:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(f"# BV: {bvid} | {title}\n# 弹幕（无字幕降级，{len(danmaku_clean)}条）\n\n{''.join(danmaku_clean)}")
                    return True, len(''.join(danmaku_clean))
                else:
                    return False, "无字幕且无弹幕"
            except Exception as e:
                return False, f"弹幕失败: {e}"
    except Exception as e:
        return False, str(e)

# ========== 观察者网（crawl4ai）==========

def crawl_guancha(author_url, author_name):
    """爬取观察者网专栏文章列表"""
    try:
        ok, clean = run_crawl4ai(author_url)
        if not ok:
            return False, clean
        
        # 提取文章链接和标题（格式: #### [标题](URL)）
        links = re.findall(r'#### \[(.+?)\]\((https://www\.guancha\.cn/[^)]+\.shtml)', clean)
        
        if links:
            out = RAW_DIR / f"guancha_{author_name}_list.md"
            with open(out, 'w', encoding='utf-8') as f:
                f.write(f"# {author_name} 专栏文章列表\n\n")
                for title, url in links:
                    f.write(f"- [{title}]({url})\n")
            return True, len(links)
        return False, 0
    except Exception as e:
        return False, str(e)

def crawl_guancha_article(article_url, output_path):
    """爬取观察者网单篇文章全文"""
    try:
        ok, clean = run_crawl4ai(article_url)
        if not ok:
            return False, clean
        
        if len(clean) > 200:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# 观察者网文章\n\n原文：{article_url}\n\n---\n\n{clean}")
            return True, len(clean)
        return False, 0
    except Exception as e:
        return False, str(e)

# ========== 中科院（crawl4ai列表 + 浏览器正文）==========

def crawl_cas_list():
    """爬中科院科研进展列表"""
    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        
        async def _crawl():
            async with AsyncWebCrawler(config=BrowserConfig(headless=True, extra_args=['--no-sandbox'])) as crawler:
                r = await crawler.arun(url="https://www.cas.cn/kyjz/", config=CrawlerRunConfig(cache_mode='bypass'))
                return r.markdown
        
        md = asyncio.run(_crawl())
        
        links = []
        seen = set()
        # 匹配格式: 日期[标题](https://www.cas.cn/syky/xxx.shtml "标题")
        # 或: [标题](https://www.cas.cn/syky/xxx.shtml "标题")
        # 排除图片链接（包含 W0/ ORIGIN.jpg 等）
        for m in re.finditer(r'([\d-]+)?\s*\[(.+?)\]\((https://www\.cas\.cn/(?:syky|cg|kj|cm)/[^)]+\.shtml)', md):
            date = m.group(1) or ''
            title = m.group(2).strip()
            url = m.group(3)
            
            # 过滤图片标题、过短标题、已投稿链接
            if 'W0' in url or 'ORIGIN' in url or '![]' in title or len(title) < 10 or url in seen:
                continue
            
            # 清理日期前缀
            title = re.sub(r'^[\d-]+\s*', '', title).strip()
            
            if title and len(title) > 5:
                seen.add(url)
                links.append({"title": title[:80], "url": url, "date": date})
        
        # 保存链接列表
        if links:
            out = RAW_DIR / "cas_links.json"
            with open(out, 'w', encoding='utf-8') as f:
                json.dump(links, f, ensure_ascii=False, indent=2)
        
        return links
    except Exception as e:
        log(f"  中科院列表爬取失败: {e}")
        return []

# ========== 物理所 ==========

def crawl_iop(base_url):
    """爬取中科院物理所科普页"""
    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        
        async def _crawl():
            async with AsyncWebCrawler(
                config=BrowserConfig(headless=True, extra_args=['--no-sandbox', '--disable-dev-shm-usage'])
            ) as crawler:
                result = await crawler.arun(
                    url=base_url,
                    config=CrawlerRunConfig(cache_mode='bypass')
                )
                return result.markdown
        
        md = asyncio.run(_crawl())
        
        links = []
        seen = set()
        for line in md.split('\n'):
            if 'iop.cas.cn/kxcb/' in line and '.html' in line:
                m = re.search(r'https://www\.iop\.cas\.cn/kxcb/[^)\s\]]+\.html', line)
                if m:
                    url = m.group(0)
                    if url in seen:
                        continue
                    seen.add(url)
                    title = line.replace(url, '').replace('[', '').replace(']', '').strip()[:80]
                    if title and len(title) > 5:
                        links.append({"title": title, "url": url})
        
        out = RAW_DIR / "iop_links.json"
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(links, f, ensure_ascii=False, indent=2)
        
        return len(links)
    except Exception as e:
        log(f"  物理所爬取失败: {e}")
        return 0

# ========== 热点采集 ==========

def fetch_hot_topics():
    """采集百度热搜+B站热门"""
    stats = {}
    
    # 百度热搜（浏览器方式）
    try:
        # 这里由 agent 执行 browser_navigate + snapshot
        stats["baidu_hot"] = "需browser_navigate top.baidu.com/board"
    except:
        stats["baidu_hot"] = "失败"
    
    # B站热门
    try:
        url = "https://api.bilibili.com/x/web-interface/popular?ps=20"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        
        if data.get('code') == 0:
            videos = data['data'].get('list', [])[:20]
            out = RAW_DIR / "bili_hot.json"
            with open(out, 'w', encoding='utf-8') as f:
                json.dump([{"title": v.get('title','')[:60], "view": v.get('stat',{}).get('view',0)} for v in videos], f, ensure_ascii=False, indent=2)
            stats["bili_hot"] = f"{len(videos)}条"
    except Exception as e:
        stats["bili_hot"] = f"失败: {e}"
    
    return stats

# ========== RSS采集 ==========

def fetch_rss_feeds():
    """抓取多个RSS源"""
    results = {}
    for name, url in CONFIG["rss_feeds"].items():
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=10)
            xml = resp.read().decode('utf-8', errors='replace')
            articles = extract_rss_items(xml, limit=4)
            if not articles:
                log(f"  RSS {name}: 0篇，可能不是RSS/XML: {resp.getheader('content-type')}")
            
            results[name] = articles
            log(f"  RSS {name}: {len(articles)}篇")
        except Exception as e:
            results[name] = f"失败: {e}"
            log(f"  RSS {name}: 失败")
    
    out = RAW_DIR / "rss_feeds.json"
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

# ========== 主调度 ==========

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    stats = {}
    
    log(f"科武纪元·素材采集调度器 v3")
    log(f"模式: {mode} | 输出: {OUT_DIR}")
    
    if mode in ("all", "cpj", "wechat"):
        log("\n=== 差评君/微信文章 ===")
        urls = CONFIG["cpj_wechat"]
        if urls:
            for i, url in enumerate(urls):
                ok, size, title = crawl_wechat(url)
                stats[f"微信_{i+1}"] = f"{'成功' if ok else '失败'} {title[:20]} ({size}字)"
        else:
            stats["微信"] = "等待用户提供链接（转发微信文章即可）"
    
    if mode in ("all", "bili"):
        log("\n=== B站搜索+字幕 ===")
        videos = search_bilibili(CONFIG["bili_keywords"])
        stats["b站视频"] = f"{len(videos)}个"
        if videos:
            # 下载前5个视频的字幕
            sub_count = 0
            for v in videos[:5]:
                if v["bvid"]:
                    out = RAW_DIR / f"bili_{v['bvid']}_subtitle.md"
                    ok, size = download_bili_subtitle(v["bvid"], out)
                    if ok:
                        sub_count += 1
            stats["b站字幕"] = f"{sub_count}个成功"
            
            with open(OUT_DIR / "bili_videos.json", 'w', encoding='utf-8') as f:
                json.dump(videos[:20], f, ensure_ascii=False, indent=2)
    
    if mode in ("all", "guancha"):
        log("\n=== 观察者网专栏 ===")
        for name, url in CONFIG["guancha_authors"].items():
            ok, count = crawl_guancha(url, name)
            stats[f"观察者_{name}"] = f"{'成功' if ok else '失败'} {count}篇"
    
    if mode in ("all", "cas"):
        log("\n=== 中科院官网 ===")
        links = crawl_cas_list()
        stats["cas列表"] = f"{len(links)}条"
        if links:
            # 生成浏览器读取脚本
            script_path = OUT_DIR / "read_cas_articles.sh"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write("#!/bin/bash\n# 中科院文章正文读取脚本（需浏览器执行）\n")
                for i, link in enumerate(links[:10]):
                    f.write(f'echo "爬取第{i+1}篇: {link["title"][:50]}"\n')
            os.chmod(script_path, 0o755)
            stats["cas脚本"] = f"10篇待爬"
    
    if mode in ("all", "iop"):
        log("\n=== 中科院物理所 ===")
        n = crawl_iop("https://www.iop.cas.cn/kxcb/")
        stats["物理所链接"] = f"{n}条"
    
    if mode in ("all", "hot"):
        log("\n=== 热点采集 ===")
        hot = fetch_hot_topics()
        stats.update(hot)
    
    if mode in ("all", "rss"):
        log("\n=== RSS采集 ===")
        rss = fetch_rss_feeds()
        rss_count = sum(1 for v in rss.values() if isinstance(v, list))
        stats["RSS成功"] = f"{rss_count}/{len(rss)}源"
    
    # 写清单
    manifest = OUT_DIR / "MANIFEST.md"
    with open(manifest, 'w', encoding='utf-8') as f:
        f.write(f"# 采集清单 {TODAY}\n\n## 统计\n\n| 来源 | 结果 |\n|------|------|\n")
        for k, v in stats.items():
            f.write(f"| {k} | {v} |\n")
        f.write(f"\n## 输出目录\n\n- 原始素材: `{RAW_DIR}`\n- 素材卡: `{CARDS_OUT}`\n")
        f.write("\n## 输出文件\n\n")
        for p in sorted(OUT_DIR.rglob("*")):
            if p.is_file() and p.name != "MANIFEST.md":
                f.write(f"- `{p.relative_to(OUT_DIR)}`\n")
        rss_file = RAW_DIR / "rss_feeds.json"
        if rss_file.exists():
            try:
                rss_data = json.loads(rss_file.read_text(encoding="utf-8"))
                f.write("\n## RSS明细\n\n| 源 | 标题 | 日期 | 链接 |\n|----|------|------|------|\n")
                for source, items in rss_data.items():
                    if isinstance(items, list):
                        for item in items:
                            f.write(f"| {md_cell(source)} | {md_cell(item.get('title'))} | {md_cell(item.get('date'))} | {md_cell(item.get('link'))} |\n")
                    else:
                        f.write(f"| {md_cell(source)} | 失败 |  | {md_cell(items)} |\n")
            except Exception as e:
                f.write(f"\nRSS明细读取失败：{e}\n")
    
    log("\n=== 采集完成 ===")
    for k, v in stats.items():
        log(f"  {k}: {v}")
    log(f"  目录: {OUT_DIR}")

if __name__ == "__main__":
    main()
