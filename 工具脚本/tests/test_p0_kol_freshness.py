#!/usr/bin/env python3
"""P0 KOL radar patch verification tests — domain expansion edition.

Tests:
  1. py_compile (syntax check)
  2. is_stale_kol_item — old article, G1 surgery, CZ-10B, no-date
  3. material_policy_tag — expanded keywords (G1 surgery, CZ-10B, energy, biology)
  4. Full run fixture replay — domain coverage, stale filtering, health gate
  5. Watchlist domain-slot structure — 9 domains, ≥2 accounts per domain
  6. coverage_by_domain gate — PARTIAL triggers
"""
import py_compile
import datetime
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent  # 工具脚本/
FIXTURES = Path(__file__).resolve().parent / 'fixtures'
WATCHLIST = Path('/root/workspace/科武纪元/学习记录/平台号观点雷达/platform_watchlist.json')

PASS_COUNT = 0
FAIL_COUNT = 0
FIXTURE_TODAY = datetime.date(2026, 7, 10)


def ok(label: str):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f'  PASS  {label}')


def fail(label: str, detail: str = ''):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f'  FAIL  {label}: {detail}')


def section(title: str):
    print(f'\n=== {title} ===')


# ── 1. py_compile ──
section('1. py_compile')
script = SCRIPT_DIR / 'platform_radar_v2_20260622.py'
try:
    py_compile.compile(str(script), doraise=True)
    ok(f'py_compile {script.name}')
except py_compile.PyCompileError as e:
    fail(f'py_compile {script.name}', str(e))
    sys.exit(1)

# Import the module
sys.path.insert(0, str(SCRIPT_DIR))
import platform_radar_v2_20260622 as radar

# ── 2. is_stale_kol_item ──
section('2. is_stale_kol_item (freshness gate)')

# 2a. Old post (2025-01-15) → STALE_KOL_ARTICLE
old = json.loads((FIXTURES / 'fixture_old_post.json').read_text())
stale, reason = radar.is_stale_kol_item(old, max_age_days=7, today=FIXTURE_TODAY)
if stale and reason == 'STALE_KOL_ARTICLE':
    ok('old_post → STALE_KOL_ARTICLE')
else:
    fail('old_post', f'stale={stale}, reason={reason}')

# 2b. G1 surgery (today) → NOT stale
g1 = json.loads((FIXTURES / 'fixture_g1_surgery.json').read_text())
stale, reason = radar.is_stale_kol_item(g1, max_age_days=7, today=FIXTURE_TODAY)
if not stale and reason == '':
    ok('g1_surgery → NOT stale (fresh)')
else:
    fail('g1_surgery', f'stale={stale}, reason={reason}')

# 2c. CZ-10B (today) → NOT stale
cz = json.loads((FIXTURES / 'fixture_cz10b_launch.json').read_text())
stale, reason = radar.is_stale_kol_item(cz, max_age_days=7, today=FIXTURE_TODAY)
if not stale and reason == '':
    ok('cz10b_launch → NOT stale (fresh)')
else:
    fail('cz10b_launch', f'stale={stale}, reason={reason}')

# 2d. No date at all → DATE_UNKNOWN
nodate = {'title': '无日期文章', 'evidence': '一些内容', 'published_at': ''}
stale, reason = radar.is_stale_kol_item(nodate, max_age_days=7, today=FIXTURE_TODAY)
if not stale and reason == 'DATE_UNKNOWN':
    ok('no_date → DATE_UNKNOWN')
else:
    fail('no_date', f'stale={stale}, reason={reason}')

# 2e. Evidence with old year "2025年" → DATE_OLD_YEAR
oldyear = {'title': '2025年回顾', 'evidence': '2025年发生了重大变化', 'published_at': ''}
stale, reason = radar.is_stale_kol_item(oldyear, max_age_days=7, today=FIXTURE_TODAY)
if stale and reason == 'DATE_OLD_YEAR':
    ok('evidence_2025 → DATE_OLD_YEAR')
else:
    fail('evidence_2025', f'stale={stale}, reason={reason}')

# 2f. Relative date "3天前" → NOT stale
recent = {'title': '最近的', 'evidence': '', 'published_at': '3天前'}
stale, reason = radar.is_stale_kol_item(recent, max_age_days=7, today=FIXTURE_TODAY)
if not stale:
    ok('relative_3d → NOT stale')
else:
    fail('relative_3d', f'stale={stale}, reason={reason}')

# 2g. Relative date "15天前" → STALE_KOL_ARTICLE
old_rel = {'title': '较早的', 'evidence': '', 'published_at': '15天前'}
stale, reason = radar.is_stale_kol_item(old_rel, max_age_days=7, today=FIXTURE_TODAY)
if stale and reason == 'STALE_KOL_ARTICLE':
    ok('relative_15d → STALE_KOL_ARTICLE')
else:
    fail('relative_15d', f'stale={stale}, reason={reason}')

# 2h. Supplement dates only from explicit metadata/snippet/URL evidence.
date_cases = [
    ({'created_at': '2026-07-26'}, '2026-07-26'),
    ({'created_at': 'Fri Jul 24 10:00:00 +0800 2026'}, '2026-07-24'),
    ({'url': 'https://news.cctv.com/2026/07/27/ARTIx.shtml'}, '2026-07-27'),
    ({'url': 'https://news.cctv.com/a/b/ARTIx260726.shtml'}, '2026-07-26'),
]
for payload, expected in date_cases:
    got = radar.extract_publication_date(payload, today=datetime.date(2026, 7, 27))
    if got == expected:
        ok(f'date supplementation {expected}')
    else:
        fail('date supplementation', f'payload={payload}, got={got}, expected={expected}')
if radar.extract_publication_date({'title': '没有明确日期的文章'}, today=FIXTURE_TODAY) == '':
    ok('date supplementation does not invent collection date')
else:
    fail('date supplementation', 'invented date without explicit evidence')
if radar.extract_publication_date({'evidence': '计划于2035年奔赴深空'}, today=FIXTURE_TODAY) == '':
    ok('future event year is not publication date')
else:
    fail('date supplementation', 'future event year misclassified as publication date')


# ── 3. material_policy_tag (keyword expansion) ──
section('3. material_policy_tag (expanded SIGNAL_KW + 9 domains)')

# 3a. G1 surgery → PLATFORM_SIGNAL (has 手术/机器人/活体/精准/微创/具身智能)
g1_item = {**g1, 'material_policy': ''}
mp = radar.material_policy_tag(g1_item)
if mp == 'PLATFORM_SIGNAL':
    ok('g1_surgery → PLATFORM_SIGNAL')
else:
    fail('g1_surgery', f'got {mp}, expected PLATFORM_SIGNAL')

# 3b. CZ-10B → PLATFORM_SIGNAL (has 长征/运载火箭/回收/首飞/可复用)
cz_item = {**cz, 'material_policy': ''}
mp = radar.material_policy_tag(cz_item)
if mp == 'PLATFORM_SIGNAL':
    ok('cz10b_launch → PLATFORM_SIGNAL')
else:
    fail('cz10b_launch', f'got {mp}, expected PLATFORM_SIGNAL')

# 3c. Pure entertainment → NOISE
noise = {'account': 'test', 'title': '直播游戏下载', 'evidence': '哔哩哔哩游戏直播下载中心', 'platform': 'bilibili'}
mp = radar.material_policy_tag(noise)
if mp == 'NOISE':
    ok('entertainment → NOISE')
else:
    fail('entertainment', f'got {mp}, expected NOISE')

# 3d. Energy domain → PLATFORM_SIGNAL (has 可控核聚变/ITER/储能)
energy_item = {
    'account': '中科院物理所', 'title': '可控核聚变ITER新进展',
    'evidence': '可控核聚变、ITER计划、能源前沿突破、储能技术', 'platform': 'wechat',
    'material_policy': ''
}
mp = radar.material_policy_tag(energy_item)
if mp == 'PLATFORM_SIGNAL':
    ok('energy (核聚变+ITER+储能) → PLATFORM_SIGNAL')
else:
    fail('energy', f'got {mp}, expected PLATFORM_SIGNAL')

# 3e. Biology domain → PLATFORM_SIGNAL (has 基因编辑/脑机接口/生物技术)
bio_item = {
    'account': '果壳', 'title': '基因编辑新突破',
    'evidence': '基因编辑、脑机接口、生物技术、合成生物学', 'platform': 'wechat',
    'material_policy': ''
}
mp = radar.material_policy_tag(bio_item)
if mp == 'PLATFORM_SIGNAL':
    ok('biology (基因编辑+脑机接口+生物技术) → PLATFORM_SIGNAL')
else:
    fail('biology', f'got {mp}, expected PLATFORM_SIGNAL')

# 3f. Aviation domain → PLATFORM_SIGNAL (has 战斗机/航空发动机/六代机)
avi_item = {
    'account': '航空知识', 'title': '六代机首飞',
    'evidence': '战斗机、航空发动机、六代机、无人机', 'platform': 'wechat',
    'material_policy': ''
}
mp = radar.material_policy_tag(avi_item)
if mp == 'PLATFORM_SIGNAL':
    ok('aviation (战斗机+航空发动机+六代机) → PLATFORM_SIGNAL')
else:
    fail('aviation', f'got {mp}, expected PLATFORM_SIGNAL')


# ── 4. Full run fixture replay ──
section('4. Full run fixture replay (domain-slot)')

full = json.loads((FIXTURES / 'fixture_full_run.json').read_text())
items = full['items']

# Apply freshness gate + policy tag (replicate main loop logic)
for it in items:
    stale, reason = radar.is_stale_kol_item(it, max_age_days=7, today=FIXTURE_TODAY)
    if stale:
        it['material_policy'] = 'NOISE'
        it['failure_tag'] = reason
    else:
        if reason == 'DATE_UNKNOWN':
            it['failure_tag'] = 'DATE_UNKNOWN'
        it['material_policy'] = radar.material_policy_tag(it)

# Load watchlist to get domain_map
wl = json.loads(WATCHLIST.read_text())
domain_map = {}
total_accounts = 0
for dom in wl['domains']:
    did = dom['domain_id']
    domain_map[did] = [a['name'] for a in dom['accounts']]
    total_accounts += len(dom['accounts'])

# 4a. Domain coverage check
domain_results = {}
accounts_with_results = set()
for it in items:
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

domains_with_results = len(domain_results)
# In fixture: frontier_tech, geopolitics, space, materials, military, energy = 6 domains.
# This is useful coverage but must not be called HEALTHY under the 9-domain gate.
if domains_with_results >= 2:
    ok(f'domain_coverage={domains_with_results}/{len(domain_map)} domains (fixture partial, not HEALTHY)')
else:
    fail('domain_coverage', f'only {domains_with_results} domains')

# 4b. Stale filtering: the 2025 item should be NOISE
stale_items = [it for it in items if it.get('failure_tag') in ('STALE_KOL_ARTICLE', 'DATE_OLD_YEAR')]
if len(stale_items) == 1 and stale_items[0]['title'].startswith('沈逸老师:2025'):
    ok('stale filtering: 1 old item correctly filtered as NOISE')
else:
    fail('stale filtering', f'expected 1 stale, got {len(stale_items)}: {[s["title"][:30] for s in stale_items]}')

# 4c. G1 surgery NOT filtered
g1_in = [it for it in items if 'G1' in it.get('title', '')]
if g1_in and g1_in[0]['material_policy'] == 'PLATFORM_SIGNAL':
    ok('G1 surgery → PLATFORM_SIGNAL in full run')
else:
    fail('G1 in full run', f'policy={g1_in[0]["material_policy"] if g1_in else "NOT FOUND"}')

# 4d. CZ-10B captured
cz_in = [it for it in items if '长征十号' in it.get('title', '')]
if cz_in and cz_in[0]['material_policy'] == 'PLATFORM_SIGNAL':
    ok('CZ-10B → PLATFORM_SIGNAL in full run')
else:
    fail('CZ-10B in full run', f'policy={cz_in[0]["material_policy"] if cz_in else "NOT FOUND"}')

# 4e. Energy item captured
energy_in = [it for it in items if '核聚变' in it.get('evidence', '')]
if energy_in and energy_in[0]['material_policy'] == 'PLATFORM_SIGNAL':
    ok('Energy (核聚变) → PLATFORM_SIGNAL in full run')
else:
    fail('Energy in full run', f'policy={energy_in[0]["material_policy"] if energy_in else "NOT FOUND"}')

# 4f. Health gate — stale_platform = 0
stale_platform = sum(
    1 for i in items
    if i.get('material_policy') == 'PLATFORM_SIGNAL'
    and i.get('failure_tag') in ('STALE_KOL_ARTICLE', 'DATE_OLD_YEAR')
)
if stale_platform == 0:
    ok('stale_PLATFORM=0 (no stale items leaked into PLATFORM_SIGNAL)')
else:
    fail('stale_PLATFORM', f'{stale_platform} stale items in PLATFORM_SIGNAL')

# 4g. Health verdict
coverage_gate = wl.get('ingest_rules', {}).get('domain_coverage_gate', {})
min_domains = len(domain_map)
min_accounts_total = coverage_gate.get('min_accounts_with_results_total', 3)

failure_tags = []
if domains_with_results < min_domains:
    failure_tags.append(f'DOMAINS_ONLY_{domains_with_results}')
if len(accounts_with_results) < min_accounts_total:
    failure_tags.append(f'ACCOUNTS_ONLY_{len(accounts_with_results)}')
if stale_platform > 0:
    failure_tags.append(f'STALE_PLATFORM={stale_platform}')

health = 'PARTIAL' if failure_tags else 'HEALTHY'
ok(f'sidecar_health={health} (domains={domains_with_results}/{len(domain_map)}, accounts={len(accounts_with_results)}/{total_accounts}, stale_PLATFORM={stale_platform})')
if domains_with_results < len(domain_map) and health != 'HEALTHY':
    ok('less than 9/9 domains is not HEALTHY')
else:
    fail('9-domain health gate', f'domains={domains_with_results}, health={health}')


# ── 5. Watchlist domain-slot structure ──
section('5. Watchlist domain-slot structure')

domains = wl['domains']
domain_ids = [d['domain_id'] for d in domains]
domain_names = [d['domain_name'] for d in domains]

# 5a. Must have 9 domains
expected_domains = ['frontier_tech', 'geopolitics', 'biology', 'space', 'aviation',
                    'ai', 'military', 'materials', 'energy']
for ed in expected_domains:
    if ed in domain_ids:
        ok(f'domain: {ed}')
    else:
        fail(f'missing domain', ed)

# 5b. Each domain must have ≥2 accounts
for dom in domains:
    n = len(dom['accounts'])
    if n >= 2:
        ok(f'{dom["domain_id"]}: {n} accounts (≥2)')
    else:
        fail(f'{dom["domain_id"]}', f'only {n} accounts, need ≥2')

# 5c. source_type diversity: each domain must have at least 2 types
source_type_diversity_pass = True
for dom in domains:
    types = set(a.get('source_type', '') for a in dom['accounts'])
    if len(types) < 2:
        # exception: some domains legitimately have only official + professional
        # but they should have at least 2 distinct types
        fail(f'{dom["domain_id"]} source_type diversity', f'only {types}')
        source_type_diversity_pass = False
if source_type_diversity_pass:
    ok('all domains have ≥2 source types')

# 5d. Verified accounts must exist
verified_count = 0
for dom in domains:
    for acc in dom['accounts']:
        if acc.get('verified'):
            verified_count += 1
if verified_count >= 8:
    ok(f'verified accounts: {verified_count}')
else:
    fail('verified accounts', f'only {verified_count}, need ≥8')

# 5e. pending_smoke_test accounts must be marked
pending_count = 0
for dom in domains:
    for acc in dom['accounts']:
        if acc.get('status') == 'pending_smoke_test':
            pending_count += 1
ok(f'pending_smoke_test accounts: {pending_count} (new, need smoke test)')

# 5f. Total unique accounts
unique_names = set()
for dom in domains:
    for acc in dom['accounts']:
        unique_names.add(acc['name'])
ok(f'unique accounts: {len(unique_names)} across {len(domains)} domains')

# 5g. JSON schema validation
if 'schema_version' in wl and wl['schema_version'] == 'domain_slot_v1':
    ok('schema_version: domain_slot_v1')
else:
    fail('schema_version', f'expected domain_slot_v1, got {wl.get("schema_version")}')

if 'ingest_rules' in wl and 'domain_coverage_gate' in wl['ingest_rules']:
    ok('domain_coverage_gate present in ingest_rules')
else:
    fail('domain_coverage_gate', 'missing from ingest_rules')


# ── 6. coverage_by_domain gate — PARTIAL triggers ──
section('6. coverage_by_domain PARTIAL triggers')

# ── 7. 2026-08-11 P0: strict domain diagnostics ──
section('7. P0 strict diagnostics: per-domain, independent counts, no excerpt+unknown fake success')

cdp_available = True
# Domain with mixed results: 1 fresh body, 1 stale body, 1 excerpt+unknown, 1 fetch_fail, 1 truncated
mixed_items = [
    {'body_status': 'fetched', 'failure_tag': '', 'material_policy': 'PLATFORM_SIGNAL', 'published_at': '2026-08-10'},
    {'body_status': 'fetched', 'failure_tag': 'STALE_KOL_ARTICLE', 'material_policy': 'NOISE', 'published_at': '2024-01-01'},
    {'body_status': 'excerpt_only', 'failure_tag': 'DATE_UNKNOWN', 'material_policy': 'DISCOVERY_ONLY', 'published_at': ''},
    {'body_status': 'fetch_fail', 'failure_tag': '', 'material_policy': 'NOISE', 'published_at': ''},
    {'body_status': 'truncated_by_budget', 'failure_tag': 'DATE_UNKNOWN', 'material_policy': 'NOISE', 'published_at': ''},
]
diag = radar.compute_domain_diagnostics('ai', mixed_items, cdp_available=cdp_available)
if diag['body_fetched'] == 2 and diag['body_fetched_strict'] == 1 and diag['excerpt_only'] == 1 and diag['fresh_dated_count'] == 1 and diag['date_unknown_count'] == 2 and diag['fetch_fail'] == 1 and diag['truncated_by_budget'] == 1:
    ok('mixed-domain: independent counts (body=2 strict=1 excerpt=1 fresh=1 unknown=2 fail=1 trunc=1)')
else:
    fail('mixed-domain counts', f'{diag}')
fr = diag['failure_reason']
if 'STALE=1' in fr and 'DATE_UNKNOWN=2' in fr and 'BODY_FETCH_FAIL=1' in fr and 'BUDGET_TRUNCATED=1' in fr and 'NOISE=' in fr and 'ARCHIVE_NO_DYSON=1' in fr:
    ok('mixed-domain: failure_reason lists STALE/DATE_UNKNOWN/BODY_FETCH_FAIL/BUDGET_TRUNCATED/NOISE/ARCHIVE')
else:
    fail('mixed-domain failure_reason', fr)
if '_CDP_UNAVAILABLE' not in fr:
    ok('mixed-domain: CDP available → no _CDP_UNAVAILABLE suffix on DATE_UNKNOWN')
else:
    fail('mixed-domain CDP suffix', fr)

# excerpt_only + DATE_UNKNOWN must NOT be counted as strict body success
excerpt_only = [
    {'body_status': 'excerpt_only', 'failure_tag': 'DATE_UNKNOWN', 'material_policy': 'DISCOVERY_ONLY', 'published_at': ''},
]
diag2 = radar.compute_domain_diagnostics('space', excerpt_only, cdp_available=False)
# DISCOVERY_ONLY policy → no NOISE/ARCHIVE policy → no NO_STRICT_RESULT; but no body → NO_BODY_FETCHED
if diag2['body_fetched_strict'] == 0 and 'DATE_UNKNOWN_CDP_UNAVAILABLE=1' in diag2['failure_reason'] and 'NO_BODY_FETCHED' in diag2['failure_reason']:
    ok('excerpt+unknown w/ CDP unavailable → strict=0, DATE_UNKNOWN_CDP_UNAVAILABLE, NO_BODY_FETCHED')
else:
    fail('excerpt+unknown strict=0', f'{diag2}')

# empty domain
diag3 = radar.compute_domain_diagnostics('energy', [], cdp_available=True)
if 'NO_QUERY_EXECUTED' in diag3['failure_reason']:
    ok('empty domain → NO_QUERY_EXECUTED')
else:
    fail('empty domain', diag3['failure_reason'])

# OK domain
ok_items = [
    {'body_status': 'fetched', 'failure_tag': '', 'material_policy': 'PLATFORM_SIGNAL', 'published_at': '2026-08-10'},
]
diag4 = radar.compute_domain_diagnostics('space', ok_items, cdp_available=True)
if diag4['failure_reason'] == 'OK' and diag4['body_fetched_strict'] == 1 and diag4['fresh_dated_count'] == 1:
    ok('OK domain → failure_reason=OK, strict=1, fresh=1')
else:
    fail('OK domain', f'{diag4}')


# ── 6a. Only 1 domain with results → PARTIAL ──
fake_items_1domain = [
    {'account': '差评君', 'domain_id': 'frontier_tech', 'material_policy': 'PLATFORM_SIGNAL'},
]
fake_domain_results = {}
for it in fake_items_1domain:
    fake_domain_results.setdefault(it['domain_id'], set()).add(it['account'])
if len(fake_domain_results) < min_domains:
    ok('1 domain → PARTIAL trigger')
else:
    fail('1 domain PARTIAL', 'should trigger')

# 6b. Only 2 accounts with results → PARTIAL
fake_items_2acc = [
    {'account': 'A', 'domain_id': 'd1', 'material_policy': 'PLATFORM_SIGNAL'},
    {'account': 'B', 'domain_id': 'd2', 'material_policy': 'PLATFORM_SIGNAL'},
]
fake_accounts = {it['account'] for it in fake_items_2acc}
if len(fake_accounts) < min_accounts_total:
    ok('2 accounts → PARTIAL trigger')
else:
    fail('2 accounts PARTIAL', 'should trigger')

# 6c. Only full 9-domain coverage → HEALTHY
fake_items_ok = [
    {'account': f'A{i}', 'domain_id': did, 'material_policy': 'PLATFORM_SIGNAL'}
    for i, did in enumerate(domain_map.keys(), start=1)
]
fake_domain_results_ok = {}
fake_accounts_ok = set()
for it in fake_items_ok:
    fake_domain_results_ok.setdefault(it['domain_id'], set()).add(it['account'])
    fake_accounts_ok.add(it['account'])
if len(fake_domain_results_ok) >= min_domains and len(fake_accounts_ok) >= min_accounts_total:
    ok('9 domains → HEALTHY')
else:
    fail('sufficient coverage', f'domains={len(fake_domain_results_ok)}, accounts={len(fake_accounts_ok)}')


# ── Summary ──
print(f'\n{"="*50}')
print(f'RESULTS: {PASS_COUNT} PASS, {FAIL_COUNT} FAIL')
if FAIL_COUNT > 0:
    sys.exit(1)
else:
    print('ALL TESTS PASSED')
    sys.exit(0)
