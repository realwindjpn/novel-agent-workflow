#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tab_lease 回归测试。真实连 9223，只读 + 只动自己的租约文件。

跑法：python3 test_tab_lease.py
退出码 0 = 全过；非 0 = 有用例失败。
"""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
BIN = [sys.executable, str(HERE / 'tab_lease.py')]


def run(*args):
    r = subprocess.run(BIN + list(args), capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout), r.returncode
    except Exception:
        return {'_raw': r.stdout, '_err': r.stderr}, r.returncode


def cleanup():
    run('release', '--seat', 'qwen', '--all')
    run('release', '--seat', 'fanqie', '--all')


CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


@case('C1 同席重入返回同一 targetId')
def c1():
    a, _ = run('acquire', '--seat', 'qwen')
    b, _ = run('acquire', '--seat', 'qwen')
    ok = a.get('ok') and b.get('reused') and a['targetId'] == b['targetId']
    return ok, 'a=%s b=%s' % (a.get('targetId'), b.get('targetId'))


@case('C2 跨席各拿自己前缀的 tab，互不侵占')
def c2():
    q, _ = run('acquire', '--seat', 'qwen')
    f, _ = run('acquire', '--seat', 'fanqie')
    ok = (q.get('ok') and f.get('ok')
          and q['targetId'] != f['targetId']
          and 'chat.qwen.ai' in q.get('url', '')
          and 'fanqienovel.com' in f.get('url', ''))
    return ok, 'qwen=%s fanqie=%s' % (q.get('url', '')[:40], f.get('url', '')[:40])


@case('C3 越界借用被拒（qwen 要 fanqie 前缀）')
def c3():
    r, _ = run('acquire', '--seat', 'qwen', '--prefix', 'https://fanqienovel.com/')
    ok = (not r.get('ok')) and r.get('reason') == 'OUT_OF_SCOPE_PREFIX'
    return ok, json.dumps(r, ensure_ascii=False)[:200]


@case('C4 --force 越界放行并留痕')
def c4():
    r, _ = run('acquire', '--seat', 'qwen', '--prefix', 'https://fanqienovel.com/', '--force')
    ok = r.get('ok') is True
    log = (HERE / '.tab_lease.log')
    forced = 'OUT_OF_SCOPE_FORCED' in log.read_text(encoding='utf-8') if log.exists() else False
    return ok and forced, 'ok=%s logged=%s' % (ok, forced)


@case('C5 归还后 status 清干净')
def c5():
    run('release', '--seat', 'qwen', '--all')
    run('release', '--seat', 'fanqie', '--all')
    s, _ = run('status')
    return s.get('leases') == {}, json.dumps(s.get('leases'), ensure_ascii=False)[:120]


@case('C6 上下文管理器自动归还')
def c6():
    sys.path.insert(0, str(HERE))
    import tab_lease
    with tab_lease.lease('qwen') as L:
        tid = L.target_id
        mid, _ = run('status')
        held = any(v.get('targetId') == tid for v in mid.get('leases', {}).values())
    after, _ = run('status')
    freed = not any(v.get('targetId') == tid for v in after.get('leases', {}).values())
    return bool(tid) and held and freed, 'tid=%s held=%s freed=%s' % (tid, held, freed)


@case('C7 陈旧租约按 TTL 过期')
def c7():
    sys.path.insert(0, str(HERE))
    import tab_lease
    r, _ = run('acquire', '--seat', 'qwen')
    st = tab_lease._load()
    lid = r.get('lease_id')
    if lid in st:
        st[lid]['ts'] = time.time() - (tab_lease.TTL + 60)
        tab_lease._save(st)
    s, _ = run('status')
    return lid not in s.get('leases', {}), 'lease=%s after_gc=%s' % (lid, lid in s.get('leases', {}))


def main():
    cleanup()
    fails = 0
    for name, fn in CASES:
        cleanup()
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, 'EXC %r' % e
        print('%-4s %s' % ('PASS' if ok else 'FAIL', name))
        if not ok:
            fails += 1
            print('      → %s' % detail)
    cleanup()
    print('\n%d/%d passed' % (len(CASES) - fails, len(CASES)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
