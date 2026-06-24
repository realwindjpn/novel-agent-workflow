#!/usr/bin/env python3
"""SenseNova source route doctor.

Read-only health check inspired by Agent-Reach's channel doctor pattern.
It does not install third-party packages and does not use cookies unless only checking file existence.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

ROUTE_MAP = Path(__file__).with_name('sensenova_source_route_map.json')
ANYSEARCH_CLI = Path('/root/workspace/IMA素材/external_skills/anysearch-skill_20260604/repo/scripts/anysearch_cli.py')
DOMESTIC_OFFICIAL_HOSTS = [
    'www.news.cn',
    'www.xinhuanet.com',
    'www.people.com.cn',
    'news.cctv.com',
    'www.cnsa.gov.cn',
    'www.miit.gov.cn',
    'www.most.gov.cn',
    'www.cas.cn',
]
EXPERT_PUBLIC_VIEW_ROUTES = [
    {
        'expert': '沈逸',
        'route': 'public_article_or_video_body_first',
        'query_hints': ['沈逸 人工智能 科技竞争 公开观点', '复旦 沈逸 中美 科技 博弈'],
        'required_failure_tags': [
            'EXPERT_SOURCE_NO_PRIMARY_HIT',
            'EXPERT_SOURCE_BODY_BLOCKED',
            'EXPERT_SOURCE_SEARCH_SUMMARY_ONLY',
            'EXPERT_GATE_INSUFFICIENT',
        ],
    },
    {
        'expert': '高志凯',
        'route': 'public_article_or_video_body_first',
        'query_hints': ['高志凯 科技竞争 公开观点', 'Victor Gao China US technology public remarks'],
        'required_failure_tags': [
            'EXPERT_SOURCE_NO_PRIMARY_HIT',
            'EXPERT_SOURCE_BODY_BLOCKED',
            'EXPERT_SOURCE_SEARCH_SUMMARY_ONLY',
            'EXPERT_GATE_INSUFFICIENT',
        ],
    },
]


def check_url(url: str, timeout: int = 8) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 SenseNovaDoctor/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read(512)
            return 200 <= getattr(r, 'status', 0) < 400 and bool(data), f'HTTP_{getattr(r, "status", "NA")}'
    except Exception as e:
        return False, f'{type(e).__name__}: {str(e)[:120]}'


def check_dns(host: str) -> dict:
    try:
        ip = socket.gethostbyname(host)
        return {'host': host, 'dns': 'OK', 'ip': ip, 'error': ''}
    except Exception as e:
        return {'host': host, 'dns': 'FAIL', 'ip': '', 'error': str(e)[:160]}


def check_anysearch_cli(timeout: int = 8) -> dict:
    if not ANYSEARCH_CLI.exists():
        return {
            'status': 'ANYSEARCH_NOT_INSTALLED',
            'cli': str(ANYSEARCH_CLI),
            'detail': 'CLI not found; restore anysearch-skill repo/scripts/anysearch_cli.py and configure ANYSEARCH_API_KEY if authenticated quota is needed.',
        }
    try:
        proc = subprocess.run(
            [sys.executable, str(ANYSEARCH_CLI), '--help'],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except Exception as e:
        return {'status': 'ANYSEARCH_UNAVAILABLE', 'cli': str(ANYSEARCH_CLI), 'detail': f'{type(e).__name__}: {str(e)[:120]}'}
    ok = proc.returncode == 0 and 'AnySearch CLI' in (proc.stdout or proc.stderr)
    return {
        'status': 'OK' if ok else 'ANYSEARCH_UNAVAILABLE',
        'cli': str(ANYSEARCH_CLI),
        'returncode': proc.returncode,
        'detail': 'help smoke passed' if ok else (proc.stderr or proc.stdout)[-300:],
    }


def check_bing_html(timeout: int = 8) -> dict:
    url = 'https://www.bing.com/search?q=site%3Anews.cn+%E5%AB%A6%E5%A8%A5'
    ok, detail = check_url(url, timeout=timeout)
    return {
        'status': 'OK' if ok else 'WARN',
        'url': url,
        'detail': detail,
        'classification': 'BING_HTML_REACHABLE' if ok else 'BING_HTML_UNREACHABLE',
    }


def classify_domestic_official_routes(timeout: int = 8) -> list[dict]:
    out = []
    for host in DOMESTIC_OFFICIAL_HOSTS:
        dns = check_dns(host)
        url = f'https://{host}/'
        http_ok, http_detail = check_url(url, timeout=timeout) if dns['dns'] == 'OK' else (False, 'DNS_FAIL')
        if dns['dns'] != 'OK':
            status = 'DNS_FAIL'
        elif http_ok:
            status = 'HTTP_OK'
        elif 'HTTP_403' in http_detail:
            status = 'HTTP_FORBIDDEN'
        elif 'Timeout' in http_detail or 'timed out' in http_detail.lower():
            status = 'HTTP_TIMEOUT'
        else:
            status = 'HTTP_FAIL'
        out.append({**dns, 'url': url, 'http': 'OK' if http_ok else 'FAIL', 'http_detail': http_detail, 'classification': status})
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Read-only SenseNova source route health check.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--timeout', type=int, default=8, help='Timeout in seconds for each network or CLI smoke check.')
    parser.add_argument('--json', action='store_true', help='Emit JSON report. Default output remains JSON for compatibility.')
    parser.add_argument('--quick', action='store_true', help='Only check local files, CLI availability, cookies, env, and route map; skip DNS/HTTP probes.')
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    timeout = max(1, args.timeout)
    checks = []

    def add(name: str, status: str, detail: str = '', next_action: str = ''):
        checks.append({'name': name, 'status': status, 'detail': detail, 'next_action': next_action})

    for cmd in ['python3', 'yt-dlp', 'gh']:
        path = shutil.which(cmd)
        add(f'cmd:{cmd}', 'OK' if path else 'WARN', path or 'not found', '' if path else f'install/configure {cmd} only if route needs it')

    anysearch_cli = check_anysearch_cli(timeout)
    add('anysearch:cli_smoke', 'OK' if anysearch_cli['status'] == 'OK' else 'WARN', anysearch_cli.get('detail', ''), 'restore/configure AnySearch CLI only for public-search fallback')

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

    route_map_ok = ROUTE_MAP.exists()
    add('route_map', 'OK' if route_map_ok else 'FAIL', str(ROUTE_MAP), 'restore sensenova_source_route_map.json')

    bing_html_smoke = None
    domestic_official_routes: list[dict] = []
    sample_fetches: list[dict] = []
    if not args.quick:
        bing_html_smoke = check_bing_html(timeout)
        add('bing:html_smoke', 'OK' if bing_html_smoke['status'] == 'OK' else 'WARN', bing_html_smoke.get('detail', ''), 'use AnySearch/Tavily/browser fallback if Bing HTML is blocked')

        for host in ['r.jina.ai', 'api.github.com', 'www.nasa.gov', 'www.xinhuanet.com']:
            dns = check_dns(host)
            add(f'dns:{host}', 'OK' if dns['dns'] == 'OK' else 'FAIL', dns.get('ip') or dns.get('error', ''), 'network/DNS issue' if dns['dns'] != 'OK' else '')

        sample_urls = {
            'jina_reader': 'https://r.jina.ai/http://example.com',
            'github_api': 'https://api.github.com/repos/Panniantong/Agent-Reach',
            'nasa_rss': 'https://www.nasa.gov/rss/dyn/breaking_news.rss',
        }
        for name, url in sample_urls.items():
            ok, detail = check_url(url, timeout=timeout)
            sample_fetches.append({'name': name, 'url': url, 'ok': ok, 'detail': detail})
            add(f'fetch:{name}', 'OK' if ok else 'WARN', detail, '' if ok else 'try web_extract/browser fallback')

        domestic_official_routes = classify_domestic_official_routes(timeout)

    domestic_dns_fail = [r for r in domestic_official_routes if r['classification'] == 'DNS_FAIL']
    domestic_http_ok = [r for r in domestic_official_routes if r['classification'] == 'HTTP_OK']
    if not args.quick:
        add(
            'domestic_official:dns_http',
            'OK' if domestic_http_ok and not domestic_dns_fail else ('WARN' if domestic_http_ok else 'FAIL'),
            f'http_ok={len(domestic_http_ok)} dns_fail={len(domestic_dns_fail)} total={len(domestic_official_routes)}',
            'route through fallback search/body_fetch and keep rescue_queue when official sites are blocked',
        )

    report = {
        'status': 'OK' if all(c['status'] != 'FAIL' for c in checks) else 'PARTIAL',
        'mode': 'quick' if args.quick else 'full',
        'timeout_seconds': timeout,
        'checks': checks,
        'route_map': str(ROUTE_MAP),
        'anysearch_cli': anysearch_cli,
        'bing_html_smoke': bing_html_smoke,
        'sample_fetches': sample_fetches,
        'domestic_official_routes': domestic_official_routes,
        'domestic_official_summary': {
            'total': len(domestic_official_routes),
            'http_ok': len(domestic_http_ok),
            'dns_fail': len(domestic_dns_fail),
            'http_fail': sum(1 for r in domestic_official_routes if r['classification'].startswith('HTTP_') and r['classification'] != 'HTTP_OK'),
        },
        'expert_public_view_routes': EXPERT_PUBLIC_VIEW_ROUTES,
        'expert_gate_contract': {
            'required_experts': ['沈逸', '高志凯'],
            'required_fields': ['expert_voice_cards', 'p0_p1_expert_cards', 'expert_gate_pass'],
            'gate_script': str(Path(__file__).with_name('sensenova_expert_gate.py')),
            'mirofish_block_tag': 'EXPERT_GATE_INSUFFICIENT',
            'search_summary_is_not_source_body': True,
        },
    }
    # Default remains JSON for existing callers; --json is accepted as an explicit contract.
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'OK' else 2


if __name__ == '__main__':
    raise SystemExit(main())
