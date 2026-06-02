#!/usr/bin/env python3
"""Stage2.5 self-loop bridge for 科武纪元 — P0 recovery.
Scope: smoke/gate bridge only. Never writes 新版/ 已投稿/ 大纲/STATUS/WAL/草稿箱.
P0 additions: three-color gate, schema 1.1, retry/backoff, chapter PID lock, cost tracking.
"""
import argparse, json, os, re, sys, fcntl
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / '审核记录' / '自循环落地_20260528'
STATE = OUT / 'state.json'
EVENTS = OUT / 'events.jsonl'
QUEUE = OUT / 'queue.json'
LOCK = OUT / '.runner.lock'
CHAPTER_LOCKS = OUT / 'chapter_locks'
RULES = OUT / 'rules.yaml'
COST_LOG = OUT / 'cost_daily.jsonl'
SRC = BASE / '新版'

# Gate thresholds
GATE_RED_MAX = 2499       # <2500 → RED
GATE_YELLOW_MAX = 2999    # 2500-2999 → YELLOW
GATE_GREEN_MIN = 3000     # >=3000 → GREEN

MAX_RETRIES = 3

def now(): return datetime.now().isoformat(timespec='seconds')

# ── Events ──────────────────────────────────────────────────────────────────
def emit(event, status='INFO', chapter=None, msg='', **kw):
    OUT.mkdir(parents=True, exist_ok=True)
    rec={'ts':now(),'event':event,'status':status,'chapter':chapter,'msg':msg}
    rec.update(kw)
    with EVENTS.open('a',encoding='utf-8') as f:
        f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    print(json.dumps(rec,ensure_ascii=False), flush=True)
    return rec

# ── JSON helpers ────────────────────────────────────────────────────────────
def load_json(path, default):
    if path.exists():
        try: return json.loads(path.read_text(encoding='utf-8'))
        except Exception: return default
    return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    data['updated_at']=now()
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

# ── Cost tracking ───────────────────────────────────────────────────────────
def record_cost(stage='', model='', status='', chapter=None, detail=None):
    COST_LOG.parent.mkdir(parents=True, exist_ok=True)
    rec={'ts':now(),'stage':stage,'model':model,'status':status,'chapter':chapter}
    if detail: rec['detail']=detail
    with COST_LOG.open('a',encoding='utf-8') as f:
        f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    # Also update state.daily_cost
    st=load_state()
    today=datetime.now().strftime('%Y-%m-%d')
    if 'daily_cost' not in st: st['daily_cost']={}
    if today not in st['daily_cost']: st['daily_cost'][today]=[]
    st['daily_cost'][today].append(rec)
    save_state(st)

# ── State (schema 1.1) ─────────────────────────────────────────────────────
SCHEMA='1.1'

def load_state():
    st=load_json(STATE, {})
    if st.get('version')!=SCHEMA:
        st=upgrade_state(st)
    st.setdefault('blocked_chapters',[])
    st.setdefault('gate_history',[])
    st.setdefault('prep_cache',{})
    st.setdefault('dream_last_run',None)
    st.setdefault('daily_cost',{})
    return st

def upgrade_state(old):
    old_version=old.get('version','1.0')
    if old_version==SCHEMA: return old
    st=dict(old)
    st['version']=SCHEMA
    st.setdefault('blocked_chapters',[])
    st.setdefault('gate_history',[])
    st.setdefault('prep_cache',{})
    st.setdefault('dream_last_run',None)
    st.setdefault('daily_cost',{})
    emit('STATE_UPGRADED','PASS',msg=f'{old_version}→{SCHEMA}')
    return st

def save_state(st):
    save_json(STATE, st)

# ── Queue ───────────────────────────────────────────────────────────────────
def init_queue():
    q=load_json(QUEUE, {'version':'stage2.5-p0','stage':'init','pid':None,'chapters':[]})
    if not q.get('chapters'):
        q['chapters']=[
            {'chapter':117,'status':'pending','test_only':True},
            {'chapter':118,'status':'pending','test_only':True}
        ]
        emit('QUEUE_INIT','PASS',chapters=[117,118])
    return q

# ── Runner lock (process-level) ─────────────────────────────────────────────
def acquire_lock():
    OUT.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        old=LOCK.read_text(encoding='utf-8',errors='ignore').strip()
        pid=None
        try: pid=int(old.split()[0])
        except Exception: pid=None
        if pid and Path(f'/proc/{pid}').exists():
            emit('RUNNER_ALREADY_ACTIVE','BLOCKED',msg='live lock exists',existing_pid=pid,new_pid=os.getpid())
            return False
        emit('STALE_LOCK_CLEARED','WARN',msg=old)
        LOCK.unlink(missing_ok=True)
    LOCK.write_text(f'{os.getpid()} {now()}\n',encoding='utf-8')
    emit('LOCK_ACQUIRED','PASS',pid=os.getpid(),runner='self_loop_runner_20260528')
    return True

def release_lock():
    if LOCK.exists():
        LOCK.unlink()
    emit('LOCK_RELEASED','PASS',pid=os.getpid())

# ── Chapter PID lock ────────────────────────────────────────────────────────
def _chapter_lock_path(ch):
    CHAPTER_LOCKS.mkdir(parents=True, exist_ok=True)
    return CHAPTER_LOCKS / f'ch{ch}.lock'

def acquire_chapter_lock(ch):
    lp=_chapter_lock_path(ch)
    if lp.exists():
        try:
            data=json.loads(lp.read_text(encoding='utf-8'))
            pid=data.get('pid')
            if pid and Path(f'/proc/{pid}').exists():
                emit('CHAPTER_LOCK_ACTIVE','BLOCKED',chapter=ch,pid=pid,
                     started_at=data.get('started_at'),msg='live chapter PID')
                return False
            emit('CHAPTER_STALE_LOCK','WARN',chapter=ch,dead_pid=pid)
            lp.unlink()
        except Exception:
            lp.unlink(missing_ok=True)
    lock_data={'chapter':ch,'pid':os.getpid(),'started_at':now()}
    lp.write_text(json.dumps(lock_data,ensure_ascii=False),encoding='utf-8')
    emit('CHAPTER_LOCK_ACQUIRED','PASS',chapter=ch,pid=os.getpid())
    return True

def release_chapter_lock(ch):
    lp=_chapter_lock_path(ch)
    if lp.exists():
        lp.unlink()
    emit('CHAPTER_LOCK_RELEASED','PASS',chapter=ch,pid=os.getpid())

# ── Retry / backoff ────────────────────────────────────────────────────────
def record_chapter_failure(ch, detail=None):
    st=load_state()
    blocked=st.get('blocked_chapters',[])
    entry=None
    for b in blocked:
        if b.get('chapter')==ch:
            entry=b
            break
    if entry is None:
        entry={'chapter':ch,'fail_count':0,'last_failure':None,'details':[]}
        blocked.append(entry)
    entry['fail_count']+=1
    entry['last_failure']=now()
    if detail: entry['details'].append(detail)
    st['blocked_chapters']=blocked
    save_state(st)

    rc=entry['fail_count']
    if rc>=MAX_RETRIES:
        emit('TAKEOVER','BLOCKED',chapter=ch,retry_count=rc,
             msg=f'Chapter {ch} failed {rc} times → TAKEOVER; blocked from auto-pick')
        record_cost(stage='retry',model='',status=f'TAKEOVER_retry={rc}',chapter=ch)
    else:
        emit('CHAPTER_RETRY','WARN',chapter=ch,retry_count=rc,msg=f'Will retry (attempt {rc}/{MAX_RETRIES})')
        record_cost(stage='retry',model='',status=f'retry_{rc}',chapter=ch)
    return rc

def is_blocked(ch):
    st=load_state()
    for b in st.get('blocked_chapters',[]):
        if b.get('chapter')==ch and b.get('fail_count',0)>=MAX_RETRIES:
            return True
    return False

# ── Three-color gate ────────────────────────────────────────────────────────
def compact_count(text): return len(re.sub(r'\s+','',text or ''))

def clean_md(text):
    text=re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text=re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    text=re.sub(r'\[\[([^\\]|]+)\|([^\]]+)\]\]', r'\2', text)
    text=re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    text=re.sub(r'`([^`]*)`', r'\1', text)
    text=re.sub(r'^\s{0,3}#{1,6}\s*', '', text, flags=re.M)
    text=re.sub(r'^\s{0,3}>\s?', '', text, flags=re.M)
    text=re.sub(r'^\s*[-*+]\s+', '', text, flags=re.M)
    text=re.sub(r'^\s*\d+[.)、]\s+', '', text, flags=re.M)
    text=re.sub(r'[*_~]+', '', text)
    text=re.sub(r'^\s*-{3,}\s*$', '', text, flags=re.M)
    return text

def tomato_count(text):
    cleaned=clean_md(text)
    lines=[x.strip() for x in cleaned.splitlines() if x.strip()]
    title=lines[0] if lines else ''
    return max(0, compact_count(cleaned)-compact_count(title))

def three_color_gate(ch):
    """Returns (color, char_count, ok_for_production, ok_for_test)
    color: 'RED' | 'YELLOW' | 'GREEN'
    ok_for_production: only GREEN passes
    ok_for_test: GREEN or YELLOW passes (test-only mode)
    """
    path=SRC / f'第{ch}章.md'
    if not path.exists():
        return 'RED', None, False, False, {'source_md_exists':False,'source_tomato_chars':None,'failed_check':'source_md_missing'}
    text=path.read_text(encoding='utf-8',errors='ignore')
    cnt=tomato_count(text)
    if cnt>=GATE_GREEN_MIN:
        color='GREEN'
    elif cnt>=2500:
        color='YELLOW'
    else:
        color='RED'
    ok_prod = color=='GREEN'
    ok_test = color in ('GREEN','YELLOW')
    return color, cnt, ok_prod, ok_test, {
        'source_md_exists':True,
        'source_tomato_chars':cnt,
        'gate_color':color,
        'failed_check': None if ok_test else f'source_tomato_chars<{2500 if color=="RED" else 3000}'
    }

# ── Record gate history in state ───────────────────────────────────────────
def record_gate_history(ch, color, chars, test_only=False):
    st=load_state()
    hist=st.get('gate_history',[])
    hist.append({'chapter':ch,'color':color,'chars':chars,'test_only':test_only,'ts':now()})
    st['gate_history']=hist
    save_state(st)

# ── Smoke ───────────────────────────────────────────────────────────────────
def smoke_only():
    cfg=Path('/root/.hermes/config.yaml')
    env=Path('/root/.hermes/.env')
    detail={'config_exists':cfg.exists(),'env_exists':env.exists(),'rules_exists':RULES.exists()}
    if cfg.exists():
        txt=cfg.read_text(encoding='utf-8',errors='ignore')
        providers=[]
        for name in ['zai','alibaba','xiaomi','glm1','glm2','kimi1','freemodel']:
            if re.search(rf'^\s*{re.escape(name)}\s*:', txt, re.M): providers.append(name)
        detail['providers_seen']=providers
    # Init cost log if missing. Smoke-only is read-only for production novel assets;
    # it may write only engine audit/cost artifacts under OUT.
    COST_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not COST_LOG.exists():
        COST_LOG.touch()
    emit('SMOKE_PASS_READONLY','PASS',msg='smoke-only verified config/rules presence; no external model call; no production asset writes',detail=detail)
    record_cost(stage='smoke',model='',status='read_only_pass')
    return 0

# ── Gate runner ─────────────────────────────────────────────────────────────
def run_gate(ch, test_only=False, stop_after='gate'):
    st=load_state()

    # Check if chapter is blocked
    if is_blocked(ch):
        emit('CHAPTER_BLOCKED_SKIP','BLOCKED',chapter=ch,msg='retry>=3 → TAKEOVER; skip auto-pick')
        record_cost(stage='gate',model='',status='BLOCKED_TAKEOVER',chapter=ch)
        return 3

    # Init queue
    q=init_queue()
    q['pid']=os.getpid()
    q['stage']='gate'
    save_json(QUEUE,q)
    emit('QUEUE_CHAPTER_PICKED','PASS',chapter=ch,stage='gate',test_only=test_only,stop_after=stop_after)

    # Acquire chapter PID lock
    if not acquire_chapter_lock(ch):
        emit('CHAPTER_LOCK_FAILED','BLOCKED',chapter=ch,msg='another PID holds chapter lock')
        record_cost(stage='gate',model='',status='CHAPTER_LOCK_FAILED',chapter=ch)
        return 4

    try:
        color, chars, ok_prod, ok_test, detail = three_color_gate(ch)
        record_gate_history(ch, color, chars, test_only=test_only)

        if test_only:
            # YELLOW allowed to continue to test-executable state
            if ok_test:
                event_name = 'GATE_GREEN_PASS' if color=='GREEN' else 'GATE_YELLOW_PASS_TEST'
                status = 'PASS'
                emit(event_name, status, chapter=ch, gate_color=color, source_tomato_chars=chars,
                     detail=detail, test_only=test_only)
                record_cost(stage='gate',model='',status=color,chapter=ch)
            else:
                emit('GATE_RED_BLOCK','BLOCKED',chapter=ch, gate_color='RED',
                     source_tomato_chars=chars, detail=detail, test_only=test_only)
                record_chapter_failure(ch, detail)
                record_cost(stage='gate',model='',status='RED',chapter=ch)
        else:
            # Production: only GREEN passes
            if ok_prod:
                emit('GATE_GREEN_PASS','PASS',chapter=ch, gate_color='GREEN',
                     source_tomato_chars=chars, detail=detail)
                record_cost(stage='gate',model='',status='GREEN',chapter=ch)
            else:
                prod_detail=dict(detail)
                prod_detail['failed_check']=prod_detail.get('failed_check') or 'source_tomato_chars<3000_production_requires_GREEN'
                emit(f'GATE_{color}_BLOCK','BLOCKED',chapter=ch, gate_color=color,
                     source_tomato_chars=chars, detail=prod_detail)
                record_chapter_failure(ch, prod_detail)
                record_cost(stage='gate',model='',status=color,chapter=ch)

        # Update queue
        for item in q.get('chapters',[]):
            if int(item.get('chapter'))==ch:
                if test_only and ok_test:
                    item['status']='gate_pass_test'
                elif ok_prod:
                    item['status']='gate_pass'
                else:
                    item['status']='gate_blocked'
                item['test_only']=bool(test_only)
                item['stop_after']=stop_after
                item['gate_color']=color
                item['gate_detail']=detail

        q['stage']='stopped_after_gate' if stop_after=='gate' else 'gate_done'
        save_json(QUEUE,q)
        emit('RUNNER_STOP_AFTER_GATE','PASS' if (test_only and ok_test) or ok_prod else 'BLOCKED',
             chapter=ch, msg='no six-role generation started', test_only=test_only, gate_color=color)

        if test_only and ok_test:
            return 0
        if ok_prod:
            return 0
        return 3
    finally:
        release_chapter_lock(ch)

# ── Main ────────────────────────────────────────────────────────────────────
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--smoke-only',action='store_true')
    ap.add_argument('--chapter',type=int)
    ap.add_argument('--test-only',action='store_true')
    ap.add_argument('--stop-after',choices=['gather','council','gate'],default='gate')
    args=ap.parse_args()
    if not acquire_lock():
        return 4
    try:
        if args.smoke_only:
            return smoke_only()
        if not args.chapter:
            emit('ARGS_ERROR','BLOCKED',msg='--chapter required unless --smoke-only')
            return 2
        if args.stop_after!='gate':
            emit('STOP_AFTER_UNSUPPORTED','BLOCKED',chapter=args.chapter,msg='Stage2.5 bridge supports gate stop only')
            return 2
        return run_gate(args.chapter, args.test_only, args.stop_after)
    finally:
        release_lock()

if __name__=='__main__':
    sys.exit(main())
