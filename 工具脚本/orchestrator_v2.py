#!/usr/bin/env python3
"""科武纪元·素材采集调度器 v2

职责：按源头清单批量采集 → 爬取正文 → 生成素材卡 → 归档 RAG
只做调度，不调用 LLM 分析。

用法：python3 orchestrator_v2.py [模式]
  模式: all(默认) / cas / bilisoso / cpj / iop

RTK压缩：所有爬取结果写文件，只返回统计摘要。
"""

import json, os, re, sys, time
from pathlib import Path
from datetime import datetime

# 路径
BASE = Path("/root/workspace/科武纪元/硬科学素材")
TODAY = datetime.now().strftime("%Y%m%d")
OUT_DIR = BASE / f"采集_{TODAY}"
OUT_DIR.mkdir(exist_ok=True)

CARDS_OUT = OUT_DIR / "素材卡"
CARDS_OUT.mkdir(exist_ok=True)

RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(exist_ok=True)

# 源头清单（精简版，从源头清单.md提取）
SOURCES = {
    "cas": {
        "name": "中科院官网",
        "urls": [
            "https://www.cas.cn/kyjz/",  # 科研进展
        ],
        "keywords": ["量子计算", "核聚变", "人造太阳", "FAST", "外骨骼", "AI芯片", "存算一体"],
        "method": "crawl4ai",
    },
    "bilisoso": {
        "name": "B站搜索",
        "keywords": [
            "量子计算 科普",
            "核聚变 EAST",
            "FAST 天眼 新发现",
            "存算一体芯片",
            "外骨骼 机器人",
            "差评君 科技",
        ],
        "method": "bilibili_api",
    },
    "cpj": {
        "name": "差评君",
        "urls": [
            "https://www.chaping.cn/news",
        ],
        "method": "crawl4ai",
    },
    "iop": {
        "name": "中科院物理所",
        "urls": [
            "https://www.iop.cas.cn/kxcb/",
        ],
        "method": "crawl4ai",
    },
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def crawl_crawl4ai(url, output_path):
    """用 crawl4ai 爬取单页，结果写文件"""
    try:
        cmd = f'crawl4ai crawl "{url}" --format fit_markdown 2>/dev/null'
        result = os.popen(cmd).read()
        if len(result) > 100:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
            return True, len(result)
        return False, 0
    except Exception as e:
        return False, str(e)

def crawl_cas_list(base_url):
    """爬中科院科研进展列表，提取文章链接"""
    try:
        import crawl4ai
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
        
        import asyncio
        md = asyncio.run(_crawl())
        
        # 提取链接
        links = []
        for line in md.split('\n'):
            if 'cas.cn' in line and 'http' in line:
                m = re.search(r'https://www\.cas\.cn/[^)\s]+', line)
                if m:
                    url = m.group(0)
                    title = line.replace(url, '').strip().strip('[]()')
                    if title and len(title) > 5:
                        links.append({"title": title[:80], "url": url})
        
        return links
    except Exception as e:
        log(f"  crawl4ai error: {e}")
        return []

def crawl_cas_articles(links):
    """批量爬中科院文章正文（浏览器方式，因为正文是JS渲染）"""
    import subprocess
    
    # 用 browser_navigate 读正文（JS渲染）
    # 这里生成脚本，后续由 agent 执行
    script_path = OUT_DIR / "read_cas_articles.sh"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write("#!/bin/bash\n# 中科院文章正文读取脚本\n")
        f.write("# 因正文为JS渲染，需用浏览器方式读取\n")
        f.write(f"# 共 {len(links)} 篇文章待爬\n\n")
        
        for i, link in enumerate(links[:10]):  # 限10篇
            url = link['url']
            out = RAW_DIR / f"cas_article_{i:03d}.md"
            f.write(f'echo "爬取第{i+1}篇: {link["title"][:50]}"\n')
            f.write(f'crawl4ai crawl "{url}" --format fit_markdown > "{out}" 2>/dev/null\n')
            f.write(f'sleep 1\n\n')
    
    os.chmod(script_path, 0o755)
    log(f"  生成脚本: {script_path} ({len(links)}篇文章)")
    return len(links)

def search_bilibili(keywords):
    """搜索B站视频，提取BV号"""
    from urllib.parse import quote
    cookie_path = "/root/.hermes/bilibili_cookies.txt"
    if not os.path.exists(cookie_path):
        log("  B站cookie不存在，跳过")
        return []
    
    # 解析Netscape格式cookie，提取关键字段
    cookies = {}
    with open(cookie_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 7:
                cookies[parts[5]] = parts[6]
    
    # 构建Cookie header
    cookie_str = '; '.join(f"{k}={v}" for k, v in cookies.items())
    
    results = []
    for kw in keywords:
        try:
            url = f"https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={quote(kw)}&page=1"
            import urllib.request
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
            time.sleep(1)  # 防封
        except Exception as e:
            log(f"  B站搜索失败 [{kw}]: {e}")
    
    return results

def generate_bili_download_script(videos):
    """生成yt-dlp下载字幕脚本"""
    if not videos:
        return 0
    
    script_path = OUT_DIR / "download_bili_subtitles.sh"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write("#!/bin/bash\n# B站字幕下载脚本\n")
        f.write(f"# 共 {len(videos)} 个视频\n")
        f.write(f'COOKIE="/root/.hermes/bilibili_cookies.txt"\n')
        f.write(f'OUTDIR="{RAW_DIR / "bili_subtitles"}"\n')
        f.write(f'mkdir -p "$OUTDIR"\n\n')
        
        for i, v in enumerate(videos[:10]):  # 限10个
            f.write(f'echo "下载 {i+1}: {v["title"][:50]}"\n')
            f.write(f'yt-dlp --write-sub --sub-lang ai-zh --skip-download \\\n')
            f.write(f'  --cookies "$COOKIE" \\\n')
            f.write(f'  -o "$OUTDIR/{v["bvid"]}_%(title)s" \\\n')
            f.write(f'  "https://www.bilibili.com/video/{v["bvid"]}" 2>/dev/null\n')
            f.write(f'sleep 2\n\n')
    
    os.chmod(script_path, 0o755)
    log(f"  生成字幕下载脚本: {script_path}")
    return len(videos)

def crawl_wechat(url, output_path=None):
    """用微信文章正则直抓（wechat-article-spider方案）"""
    try:
        r = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }, timeout=30)
        r.encoding = 'utf-8'
        raw = r.text
        
        # 提取标题
        m = re.search(r'<h1[^>]*class="[^"]*rich_media_title[^"]*"[^>]*>(.*?)</h1>', raw, re.S)
        title = html.unescape(re.sub('<.*?>', '', m.group(1))).strip() if m else '微信文章'
        
        # 提取正文
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
            out = RAW_DIR / f"wechat_{title[:30]}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f'# {title}\n\n原文：{url}\n\n---\n\n{text}', encoding='utf-8')
        
        return True, len(text), title
    except Exception as e:
        return False, 0, str(e)

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
        
        # 提取文章链接（绝对路径格式）
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

def write_manifest(stats):
    """写入采集清单"""
    manifest = OUT_DIR / "MANIFEST.md"
    with open(manifest, 'w', encoding='utf-8') as f:
        f.write(f"# 采集清单 {TODAY}\n\n")
        f.write(f"## 统计\n\n")
        f.write(f"| 来源 | 结果 |\n")
        f.write(f"|------|------|\n")
        for k, v in stats.items():
            f.write(f"| {k} | {v} |\n")
        f.write(f"\n## 输出目录\n\n")
        f.write(f"- 原始素材: `{RAW_DIR}`\n")
        f.write(f"- 素材卡: `{CARDS_OUT}`\n")
        f.write(f"- 脚本: `{OUT_DIR}`/*.sh\n")
    log(f"  清单已写入: {manifest}")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    stats = {}
    
    log(f"科武纪元·素材采集调度器 v2")
    log(f"模式: {mode} | 输出: {OUT_DIR}")
    
    if mode in ("all", "cas"):
        log("\n=== 中科院官网 ===")
        src = SOURCES["cas"]
        for kw in src["keywords"][:3]:  # 每次3个关键词
            log(f"  关键词: {kw}")
            # 搜索需要通过浏览器（JS渲染），生成搜索脚本
            pass
        
        # 爬科研进展列表
        for url in src["urls"]:
            log(f"  列表: {url}")
            links = crawl_cas_list(url)
            stats["cas列表"] = f"{len(links)}条"
            if links:
                n = crawl_cas_articles(links)
                stats["cas文章脚本"] = f"{n}篇"
    
    if mode in ("all", "bilisoso"):
        log("\n=== B站搜索 ===")
        videos = search_bilibili(SOURCES["bilisoso"]["keywords"])
        stats["b站视频"] = f"{len(videos)}个"
        if videos:
            n = generate_bili_download_script(videos)
            stats["字幕脚本"] = f"{n}个"
        
        # 保存视频列表
        if videos:
            with open(OUT_DIR / "bili_videos.json", 'w', encoding='utf-8') as f:
                json.dump(videos[:20], f, ensure_ascii=False, indent=2)
    
    if mode in ("all", "cpj"):
        log("\n=== 差评君（微信）===")
        # 差评君微信公众号文章通过微信链接直采
        # 用户转发微信链接 → 调度器调用 crawl_wechat
        # 示例：如果配置了差评君文章列表，批量采集
        cpj_articles = SOURCES["cpj"].get("wechat_urls", [])
        if cpj_articles:
            for i, url in enumerate(cpj_articles):
                ok, size, title = crawl_wechat(url)
                stats[f"差评君_{i+1}"] = f"{'成功' if ok else '失败'} {title[:20]} ({size}字)"
        else:
            stats["差评君"] = "等待用户提供微信链接"
    
    if mode in ("all", "iop"):
        log("\n=== 中科院物理所 ===")
        n = crawl_iop(SOURCES["iop"]["urls"][0])
        stats["物理所链接"] = f"{n}条"
    
    # 写清单
    write_manifest(stats)
    
    # RTK压缩输出：只报统计
    log("\n=== 采集完成 ===")
    for k, v in stats.items():
        log(f"  {k}: {v}")
    log(f"  目录: {OUT_DIR}")

if __name__ == "__main__":
    main()
