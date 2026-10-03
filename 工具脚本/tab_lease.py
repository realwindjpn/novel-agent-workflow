#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tab_lease.py — 共享 CDP Chrome（9223）上的「显式借用 + 归还」协议层。

背景
----
小说管线里有两个浏览器席共用同一个常驻 Chrome profile（CDP 9223）：
  - 作者席（qwen）：qwen_submit_chapter.py，单 tab 路由
  - 番茄席（fanqie）：agent-browser --session-name fanqie
两个席互不知情，且 agent-browser 的 session 文件只存 cookie、不绑 tab，
所以番茄席每次都是「抓当前活跃 tab」——谁先抢到谁用，容易把对方正在
用的页面导航走。

这一层不替换底层驱动，只在两个席外面加一层 tab 归属登记：
  - 每个席注册一个 seat 名，声明自己认领哪些 URL 前缀
  - 借用前先登记 (seat → targetId)，并检查目标 tab 是否被别的席持有
  - 归还时注销；进程被杀留下的陈旧租约按 TTL 自动过期
  - 越界借用（目标 tab 属于别人的前缀）默认拒绝，可用 --force 覆盖并留痕

用法
----
  # 借用：作者席要一个 qwen 会话页
  python3 tab_lease.py acquire --seat qwen --prefix https://chat.qwen.ai/
  # → 打印 JSON: {"ok": true, "targetId": "...", "url": "...", "lease_id": "..."}

  # 归还
  python3 tab_lease.py release --seat qwen --lease-id <id>

  # 查看当前租约
  python3 tab_lease.py status

  # 清理全部（慎用）
  python3 tab_lease.py release --seat qwen --all

作为库使用
----------
  from tab_lease import lease, release
  with lease('fanqie', 'https://fanqienovel.com/') as L:
      # L.target_id / L.url 可用
      ...
  # 退出自动归还

设计约束（与 BrowserSkill 的关键差异）
--------------------------------------
BrowserSkill 的「借用」要人工点确认弹窗。这一层是无人值守的 cron 管线，
不能等人点确认，所以把「请求确认」降级为「前缀归属校验 + 冲突即拒绝」：
同席可重入，跨席冲突默认拒绝，越界强制借用必须显式 --force 且写日志。
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

CDP = os.environ.get('KEWU_CDP_URL', 'http://127.0.0.1:9223')
STATE = Path(os.environ.get('TAB_LEASE_STATE',
                            '/root/workspace/科武纪元/工具脚本/.tab_leases.json'))
LOG = Path(os.environ.get('TAB_LEASE_LOG',
                          '/root/workspace/科武纪元/工具脚本/.tab_lease.log'))
TTL = int(os.environ.get('TAB_LEASE_TTL', '5400'))  # 90 分钟；长任务作者席约 15 分钟

# seat → 该席认领的 URL 前缀。留空表示不限前缀。
SEAT_PREFIX = {
    'qwen': ['https://chat.qwen.ai/'],
    'fanqie': ['https://fanqienovel.com/'],
}


def _log(msg):
    try:
        with LOG.open('a', encoding='utf-8') as f:
            f.write('%s %s\n' % (time.strftime('%Y-%m-%dT%H:%M:%S%z'), msg))
    except Exception:
        pass


def _tabs():
    with urllib.request.urlopen(CDP + '/json/list', timeout=10) as r:
        return json.loads(r.read().decode('utf-8', 'ignore'))


def _load():
    if not STATE.exists():
        return {}
    try:
        return json.loads(STATE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _save(d):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(STATE)


def _gc(leases):
    """丢掉过期租约与已不存在的 tab。"""
    now = time.time()
    try:
        live = {t.get('id') for t in _tabs() if t.get('type') == 'page'}
    except Exception:
        live = None
    out = {}
    for lid, L in leases.items():
        if now - L.get('ts', 0) > TTL:
            _log('EXPIRE lease=%s seat=%s target=%s' % (lid, L.get('seat'), L.get('targetId')))
            continue
        if live is not None and L.get('targetId') not in live:
            _log('GONE_TAB lease=%s seat=%s target=%s' % (lid, L.get('seat'), L.get('targetId')))
            continue
        out[lid] = L
    return out


def _owner_of_prefix(prefix):
    """哪个席认领了这个前缀；没人认领返回 None。"""
    for seat, pref in SEAT_PREFIX.items():
        if any(prefix.startswith(p) for p in pref):
            return seat
    return None


def _prefix_ok(seat, url):
    pref = SEAT_PREFIX.get(seat) or []
    if not pref:
        return True
    return any((url or '').startswith(p) for p in pref)


def acquire(seat, prefer_prefix=None, force=False):
    leases = _gc(_load())

    # 同席已有活租约 → 直接复用（重入）。
    # 但重入不得绕过前缀校验：显式 --prefix 且现有租约页不在该前缀内时，
    # 视为一次新的借用请求，落到下面的选取逻辑去（否则 qwen 拿着
    # chat.qwen.ai 的租约去借 fanqienovel.com 会直接返回旧 tab，
    # 越界检查永远跑不到）。
    tabs = [t for t in _tabs() if t.get('type') == 'page']
    by_id = {t.get('id'): t for t in tabs}
    for lid, L in leases.items():
        if L.get('seat') != seat:
            continue
        tid = L.get('targetId')
        if tid not in by_id:
            continue
        held_url = by_id[tid].get('url', '')
        if prefer_prefix and not held_url.startswith(prefer_prefix):
            break  # 重入不适用，走新借用
        _log('REUSE lease=%s seat=%s target=%s' % (lid, seat, tid))
        return {'ok': True, 'reused': True, 'lease_id': lid,
                'targetId': tid, 'url': held_url}

    want = prefer_prefix or (SEAT_PREFIX.get(seat) or [None])[0]
    held = {L['targetId']: L for L in leases.values()}

    # 越界借用先拦：显式要的前缀不属于本席认领范围时，任何分配逻辑之前就拒绝。
    # 顺序不能放到后面——否则「前缀内恰好有空闲 tab」的分支会先命中，
    # 越界借用一路绿灯，这正是 B2 用例暴露的洞。
    if prefer_prefix and not _prefix_ok(seat, prefer_prefix):
        if not force:
            _log('OUT_OF_SCOPE seat=%s wants=%s owned_by=%s'
                 % (seat, prefer_prefix, _owner_of_prefix(prefer_prefix)))
            return {'ok': False, 'reason': 'OUT_OF_SCOPE_PREFIX',
                    'seat': seat, 'want_prefix': prefer_prefix,
                    'owned_by': _owner_of_prefix(prefer_prefix),
                    'hint': '该前缀属于别的席；确需跨席请显式 --force 并接受留痕'}
        _log('OUT_OF_SCOPE_FORCED seat=%s wants=%s' % (seat, prefer_prefix))

    # 先找本席前缀内、且无人持有的 tab
    for t in tabs:
        u = t.get('url', '')
        if want and not u.startswith(want):
            continue
        if t['id'] in held:
            continue
        lid = '%s-%d' % (seat, int(time.time() * 1000))
        leases[lid] = {'seat': seat, 'targetId': t['id'], 'url': u, 'ts': time.time()}
        _save(leases)
        _log('ACQUIRE lease=%s seat=%s target=%s url=%s' % (lid, seat, t['id'], u))
        return {'ok': True, 'reused': False, 'lease_id': lid,
                'targetId': t['id'], 'url': u}

    # 没有空闲的：看是不是被别的席占着
    for t in tabs:
        u = t.get('url', '')
        if want and not u.startswith(want):
            continue
        if t['id'] in held:
            other = held[t['id']]
            if not force:
                _log('CONFLICT seat=%s wants target=%s held_by=%s' % (seat, t['id'], other.get('seat')))
                return {'ok': False, 'reason': 'TARGET_HELD',
                        'held_by': other.get('seat'), 'targetId': t['id'], 'url': u}
            _log('FORCE_TAKEOVER seat=%s target=%s from=%s' % (seat, t['id'], other.get('seat')))
            lid = '%s-%d' % (seat, int(time.time() * 1000))
            for k, v in list(leases.items()):
                if v.get('targetId') == t['id']:
                    leases.pop(k)
            leases[lid] = {'seat': seat, 'targetId': t['id'], 'url': u, 'ts': time.time()}
            _save(leases)
            return {'ok': True, 'reused': False, 'forced': True, 'lease_id': lid,
                    'targetId': t['id'], 'url': u}

    # 前缀内一个 tab 都没有：允许借一个「不属于任何席前缀」的空白页
    for t in tabs:
        u = t.get('url', '')
        if u.startswith('chrome://') or u.startswith('devtools://') or u.startswith('edge://'):
            continue
        if any(u.startswith(p) for ps in SEAT_PREFIX.values() for p in ps):
            continue  # 属于别人的地盘，不抢
        if t['id'] in held:
            continue
        lid = '%s-%d' % (seat, int(time.time() * 1000))
        leases[lid] = {'seat': seat, 'targetId': t['id'], 'url': u, 'ts': time.time()}
        _save(leases)
        _log('ACQUIRE_BLANK lease=%s seat=%s target=%s url=%s' % (lid, seat, t['id'], u))
        return {'ok': True, 'reused': False, 'blank': True, 'lease_id': lid,
                'targetId': t['id'], 'url': u}

    return {'ok': False, 'reason': 'NO_TAB_AVAILABLE', 'seat': seat, 'want_prefix': want}


def release(seat=None, lease_id=None, all_seat=False):
    leases = _gc(_load())
    if all_seat and seat:
        n = 0
        for lid in [k for k, v in leases.items() if v.get('seat') == seat]:
            _log('RELEASE_ALL lease=%s seat=%s' % (lid, seat))
            leases.pop(lid)
            n += 1
        _save(leases)
        return {'ok': True, 'released': n}
    if lease_id:
        if lease_id in leases:
            _log('RELEASE lease=%s seat=%s' % (lease_id, leases[lease_id].get('seat')))
            leases.pop(lease_id)
            _save(leases)
            return {'ok': True, 'released': 1}
        return {'ok': False, 'reason': 'LEASE_NOT_FOUND', 'lease_id': lease_id}
    return {'ok': False, 'reason': 'NOTHING_TO_RELEASE'}


def status():
    leases = _gc(_load())
    _save(leases)
    return {'ok': True, 'cdp': CDP, 'ttl': TTL, 'leases': leases}


class Lease:
    """上下文管理器：with lease('fanqie') as L: ..."""

    def __init__(self, seat, prefer_prefix=None, force=False):
        self.seat = seat
        self.prefer_prefix = prefer_prefix
        self.force = force
        self.info = {}
        self.target_id = None
        self.url = None

    def __enter__(self):
        self.info = acquire(self.seat, self.prefer_prefix, self.force)
        self.target_id = self.info.get('targetId')
        self.url = self.info.get('url')
        return self

    def __exit__(self, *exc):
        if self.info.get('lease_id'):
            release(lease_id=self.info['lease_id'])
        return False


def lease(seat, prefer_prefix=None, force=False):
    return Lease(seat, prefer_prefix, force)


def _main():
    ap = argparse.ArgumentParser(description='共享 CDP Chrome 的 tab 借用/归还协议层')
    sub = ap.add_subparsers(dest='cmd', required=True)

    a = sub.add_parser('acquire')
    a.add_argument('--seat', required=True)
    a.add_argument('--prefix', default=None)
    a.add_argument('--force', action='store_true')

    r = sub.add_parser('release')
    r.add_argument('--seat')
    r.add_argument('--lease-id')
    r.add_argument('--all', action='store_true')

    sub.add_parser('status')

    args = ap.parse_args()
    if args.cmd == 'acquire':
        print(json.dumps(acquire(args.seat, args.prefix, args.force), ensure_ascii=False, indent=2))
        sys.exit(0 if _load().get('x') is None else 0)
    if args.cmd == 'release':
        print(json.dumps(release(args.seat, args.lease_id, args.all), ensure_ascii=False, indent=2))
    if args.cmd == 'status':
        print(json.dumps(status(), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    _main()
