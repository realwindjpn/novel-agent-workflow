#!/usr/bin/env python3
"""SenseNova source route doctor.

Read-only health check inspired by Agent-Reach's channel doctor pattern.
It does not install third-party packages and does not use cookies unless only checking file existence.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import sys
import urllib.request
from pathlib import Path

ROUTE_MAP = Path(__file__).with_name('sensenova_source_route_map.json')


def check_url(url: str, timeout: int = 8) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 SenseNovaDoctor/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read(512)
            return 200 <= getattr(r, 'status', 0) < 400 and bool(data), f'HTTP_{getattr(r, "status", "NA")}'
    except Exception as e:
        return False, f'{type(e).__name__}: {str(e)[:120]}'


def main() -> int:
    checks = []

    def add(name: str, status: str, detail: str = '', next_action: str = ''):
        checks.append({'name': name, 'status': status, 'detail': detail, 'next_action': next_action})

    for cmd in ['python3', 'yt-dlp', 'gh']:
        path = shutil.which(cmd)
        add(f'cmd:{cmd}', 'OK' if path else 'WARN', path or 'not found', '' if path else f'install/configure {cmd} only if route needs it')

    env_files = [Path('/root/.hermes/.env'), Path('/root/workspace/.env')]
    env_text = ''
    for p in env_files:
        if p.exists():
            try:
                env_text += p.read_text(encoding='utf-8', errors='ignore') + '\n'
            except Exception:
                pass
    tavily = bool(os.environ.get('TAVILY_API_KEY')) or ('TAVILY_API_KEY=' in env_text)
    add('env:TAVILY_API_KEY', 'OK' if tavily else 'WARN', 'present(env or .env)' if tavily else 'missing', 'domestic article_search fallback will degrade without Tavily')

    bili_cookie = Path('/root/.hermes/bilibili_cookies.txt')
    add('cookie:bilibili', 'OK' if bili_cookie.exists() else 'WARN', str(bili_cookie) if bili_cookie.exists() else 'missing', 'needed for B站 subtitle route; metadata-only fallback still possible')

    for host in ['r.jina.ai', 'api.github.com', 'www.nasa.gov', 'www.xinhuanet.com']:
        try:
            socket.gethostbyname(host)
            add(f'dns:{host}', 'OK', 'resolved')
        except Exception as e:
            add(f'dns:{host}', 'FAIL', str(e), 'network/DNS issue')

    sample_urls = {
        'jina_reader': 'https://r.jina.ai/http://example.com',
        'github_api': 'https://api.github.com/repos/Panniantong/Agent-Reach',
        'nasa_rss': 'https://www.nasa.gov/rss/dyn/breaking_news.rss',
    }
    for name, url in sample_urls.items():
        ok, detail = check_url(url)
        add(f'fetch:{name}', 'OK' if ok else 'WARN', detail, '' if ok else 'try web_extract/browser fallback')

    route_map_ok = ROUTE_MAP.exists()
    add('route_map', 'OK' if route_map_ok else 'FAIL', str(ROUTE_MAP), 'restore sensenova_source_route_map.json')

    report = {
        'status': 'OK' if all(c['status'] != 'FAIL' for c in checks) else 'PARTIAL',
        'checks': checks,
        'route_map': str(ROUTE_MAP),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'OK' else 2


if __name__ == '__main__':
    raise SystemExit(main())
