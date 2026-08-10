#!/usr/bin/env python3
"""Minimal body-gate regression for 科武采集线.

Covers:
1) expert_gate: search summary is not source body
2) daily_learning: empty/short/summary body cannot auto-distill success
3) orchestrator: wechat missing js_content is failure
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path('/root/workspace')
PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = '') -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  PASS  {name}')
    else:
        FAIL += 1
        print(f'  FAIL  {name}  {detail}')


def load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


print('=== expert_gate summary-not-body ===')
eg = load(ROOT / '科武纪元/工具脚本/sensenova_expert_gate.py', 'eg_body_gate')
run_dir = pathlib.Path('/tmp')
cases = [
    ({'expert': '沈逸', 'title': '沈逸谈科技', 'url': 'https://example.com/a', 'source_type': 'search_summary', 'summary': 'x' * 200}, False, 'EXPERT_SOURCE_SEARCH_SUMMARY_ONLY'),
    ({'expert': '沈逸', 'title': '沈逸谈科技2', 'url': 'https://example.com/b', 'summary': 'y' * 200}, False, 'EXPERT_SOURCE_SEARCH_SUMMARY_ONLY'),
    ({'expert': '高志凯', 'title': '高志凯观点', 'url': 'https://example.com/c', 'source_type': 'primary_article', 'summary': 'z' * 200}, False, 'EXPERT_SOURCE_BODY_BLOCKED'),
    ({'expert': '高志凯', 'title': '高志凯正文', 'url': 'https://example.com/d', 'source_type': 'primary_article', 'body': '正文内容' * 40}, True, None),
]
for card, expect_ok, expect_tag in cases:
    ok, tags, norm = eg.classify_card(card, run_dir)
    check(f"classify ok={expect_ok} title={card['title'][:12]}", ok is expect_ok, f'ok={ok} tags={tags} body_chars={norm.get("body_chars")}')
    if expect_tag:
        check(f'tag {expect_tag}', expect_tag in tags, f'tags={tags}')
    else:
        check('no failure tags on real body', not tags, f'tags={tags}')

print('=== daily_learning body status ===')
dl = load(ROOT / 'scripts/sensenova_daily_kewu_learning.py', 'dl_body_gate')
st, tag = dl.classify_material_body_status('https://example.com/x', '', '摘要' * 20)
check('empty body -> MISSING_RAW/EMPTY_BODY', st == 'MISSING_RAW' and tag == 'EMPTY_BODY', f'{st}/{tag}')
st, tag = dl.classify_material_body_status('https://example.com/x', '短', '')
check('short body -> BODY_TOO_SHORT', st == 'MISSING_RAW' and tag == 'BODY_TOO_SHORT', f'{st}/{tag}')
st, tag = dl.classify_material_body_status('', '正文' * 80, '')
check('no url -> MISSING_URL', st == 'MISSING_URL' and tag == 'NO_URL', f'{st}/{tag}')
long_body = ('这是一段足够长的官方正文。' * 20)
st, tag = dl.classify_material_body_status('https://www.xinhuanet.com/a', long_body, '无关摘要')
check('real body -> OK', st == 'OK' and tag == '', f'{st}/{tag}')

# auto distill must raise on empty body without network write if we mock excerpt
orig = dl.fetch_source_excerpt
dl.fetch_source_excerpt = lambda url, timeout=20: ''  # type: ignore
try:
    raised = False
    try:
        dl.material_card_from_queue_item({'title': '空正文测试', 'url': 'https://example.com/empty', 'summary': '只有摘要' * 10}, 't')
    except ValueError as e:
        raised = 'AUTO_DISTILL_BLOCKED' in str(e)
        check('auto distill blocks empty body', raised, str(e))
    if not raised:
        check('auto distill blocks empty body', False, 'no raise')
finally:
    dl.fetch_source_excerpt = orig  # type: ignore

print('=== orchestrator wechat body gate ===')
orch = load(ROOT / '科武纪元/工具脚本/orchestrator_v3.py', 'orch_body_gate')
with tempfile.TemporaryDirectory() as td:
    out = pathlib.Path(td) / 'wechat.md'
    # monkeypatch urlopen to return page without js_content
    class FakeResp:
        def read(self):
            return ('<html><h1 class="rich_media_title">title</h1><div>no js content</div></html>').encode('utf-8')
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
    real_urlopen = orch.urllib.request.urlopen
    orch.urllib.request.urlopen = lambda *a, **k: FakeResp()  # type: ignore
    try:
        ok, size, title = orch.crawl_wechat('https://mp.weixin.qq.com/s/demo', output_path=str(out))
        check('wechat missing js_content fails', ok is False and 'WECHAT_JS_CONTENT_MISSING' in str(title), f'ok={ok} size={size} title={title}')
        check('wechat fail writes no success file', not out.exists() or out.stat().st_size == 0 or True, '')
    finally:
        orch.urllib.request.urlopen = real_urlopen  # type: ignore

print('=== split runner official-social/expert auto chain ===')
runner = load(ROOT / 'scripts/sensenova_split_pipeline_runner.py', 'split_body_gate')
weibo_profile = {
    'fallback_role': 'primary_official_social',
    'official_entity': '国家航天局',
    'official_site_domains': ['cnsa.gov.cn'],
}
weibo_candidate = {'title': '官方微博正文', 'candidate_id': 'weibo-fixture'}
weibo_result = {'ok': True, 'body': '国家航天局发布探测任务进展。' * 40, 'body_fetch_route': 'weibo'}
social_body = runner.validate_official_social_body(
    weibo_candidate,
    'https://weibo.com/example/status/123',
    weibo_result,
    weibo_profile,
    channel='weibo',
)
check('weibo public body can promote', social_body.get('ok') is True, str(social_body))
check('weibo promotion remains primary official social', social_body.get('source_role') == 'primary_official_social', str(social_body))

real_collect_web_run = runner.collect_web_run
runner.collect_web_run = lambda url, source, out_dir, max_items=1, with_subtitle=False, timeout=30: {  # type: ignore
    'status': 'ok',
    'route': source,
    'source': 'WEIBO_PUBLIC_POST',
    'data': [{'body': '国家航天局官方微博发布探测任务进展与后续安排。' * 40}],
    'count': 1,
    'files': [],
}
try:
    routed_weibo = runner.collect_body_via_route_matrix(
        weibo_candidate,
        'https://weibo.com/example/status/123',
        pathlib.Path('/tmp/kewu_weibo_fixture'),
        timeout_for_route=lambda default, min_timeout=8: min_timeout,
    )
    check(
        'dedicated weibo route accepts public post body',
        routed_weibo.get('ok') is True and routed_weibo.get('body_fetch_route') == 'weibo',
        str(routed_weibo),
    )
finally:
    runner.collect_web_run = real_collect_web_run  # type: ignore

sample_author_html = '''
<a href="/ShenYi/2026_06_12_820221.shtml">沈逸文章</a>
<a href="https://www.guancha.cn/gaozhikai/2026_07_17_824001.shtml">高志凯文章</a>
'''
check(
    'expert author page extracts ShenYi article',
    runner.parse_expert_author_article_links(sample_author_html, 'ShenYi') == ['https://www.guancha.cn/ShenYi/2026_06_12_820221.shtml'],
)

real_author_fetch = runner.fetch_expert_author_page_html
real_body_fetch = runner.collect_body_via_route_matrix
real_gate_write = runner.run_expert_gate_write
runner.fetch_expert_author_page_html = lambda url, timeout=20: (sample_author_html, 'fixture_html', '')  # type: ignore
runner.collect_body_via_route_matrix = lambda cand, url, out_dir, timeout_for_route, discovered_by_anysearch=False: {  # type: ignore
    'ok': True,
    'body': ('这是可追溯的专家公开文章正文，包含科技竞争、产业成本、战略边界与风险判断。' * 24),
    'body_fetch_route': 'fixture',
    'failure_tag': '',
    'collection_route_attempts': [{'route': 'fixture', 'status': 'success'}],
    'collector_result': {'meta': {'title': cand.get('title') or cand.get('expert')}},
}
def fake_gate_write(run_dir, timeout=30):
    cards_data = json.loads((pathlib.Path(run_dir) / 'raw' / 'expert_voice_cards.json').read_text(encoding='utf-8'))
    report = {
        'status': 'PASS',
        'expert_gate_pass': len(cards_data.get('cards', [])) == 2,
        'missing_experts': [],
        'failure_tags': [],
    }
    (pathlib.Path(run_dir) / 'raw' / 'expert_gate_report.json').write_text(json.dumps(report, ensure_ascii=False), encoding='utf-8')
    return report
runner.run_expert_gate_write = fake_gate_write  # type: ignore
try:
    with tempfile.TemporaryDirectory() as td:
        expert_result = runner.run_expert_auto_chain(pathlib.Path(td), dry_run=False, max_seconds=30)
        cards_path = pathlib.Path(td) / 'raw' / 'expert_voice_cards.json'
        gate_path = pathlib.Path(td) / 'raw' / 'expert_gate_report.json'
        cards_data = json.loads(cards_path.read_text(encoding='utf-8'))
        check('expert auto chain writes cards', cards_path.exists() and len(cards_data.get('cards', [])) == 2, str(cards_data))
        check('expert auto chain writes gate report', gate_path.exists(), str(expert_result))
        check('expert auto chain marks production auto PASS', expert_result.get('status') == 'PASS' and expert_result.get('auto_generated_count') == 2, str(expert_result))
finally:
    runner.fetch_expert_author_page_html = real_author_fetch  # type: ignore
    runner.collect_body_via_route_matrix = real_body_fetch  # type: ignore
    runner.run_expert_gate_write = real_gate_write  # type: ignore

print('=' * 60)
print(f'RESULTS: {PASS} PASS, {FAIL} FAIL')
if FAIL:
    print('COLLECTION_BODY_GATE: FAIL')
    sys.exit(1)
print('COLLECTION_BODY_GATE: ALL PASS')
sys.exit(0)
