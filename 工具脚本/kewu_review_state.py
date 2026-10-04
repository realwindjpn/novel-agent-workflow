#!/usr/bin/env python3
"""Canonical review state for a 科武 candidate.

Creates/validates one binding + seat ledger without changing正文 or reports.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path

SEATS = ('editor','reader','science','military','structure','fact')
PASS = {'PASS','PASS_WITH_NOTES'}
INVALID = {'MALFORMED','NO_OUTPUT','TIMEOUT','INVALID','ROUTE_FAIL','ORCHESTRATION_FAIL'}

def sha(p: Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def cjk(s): return len(re.findall(r'[\u3400-\u9fff]', s))
def split_chapters(s):
    ms=list(re.finditer(r'(?m)^第(\d+)章\s+',s))
    out={}
    for i,m in enumerate(ms): out[int(m.group(1))]=s[m.start():ms[i+1].start() if i+1<len(ms) else len(s)]
    return out

def make(task, candidate):
    text=candidate.read_text(encoding='utf-8'); chapters=split_chapters(text)
    if set(chapters) != {367,368}: raise SystemExit(f'candidate_chapters={sorted(chapters)}')
    bind={
      'schema':'kewu.review-binding.v1','candidate_path':str(candidate),'candidate_sha256':sha(candidate),
      'candidate_bytes':candidate.stat().st_size,'first_line':text.splitlines()[0], 'last_line':text.splitlines()[-1],
      'created_at':datetime.now(timezone.utc).isoformat(), 'reviewed_fulltext_required':True,
      'chapters':{str(n):{'path':str(candidate),'sha256':hashlib.sha256(body.encode()).hexdigest(),'cjk':cjk(body),'first_line':body.splitlines()[0],'last_line':body.splitlines()[-1]} for n,body in chapters.items()}
    }
    (task/'REVIEW_BINDING.json').write_text(json.dumps(bind,ensure_ascii=False,indent=2)+'\n')
    seats={s:{'status':'PENDING','candidate_sha256':bind['candidate_sha256'],'report':None,'provider':None,'model':None,'raw_sha256':None,'reviewed_fulltext':False} for s in SEATS}
    ledger={'schema':'kewu.review-ledger.v1','candidate':bind,'seats':seats,'repair_round':0,'next_action':'DISPATCH_SINGLE_SEAT','total_review':'PENDING','g4':'BLOCKED_UNTIL_ALL_SINGLE_SEATS_PASS','deai_gate':'REQUIRES_RESCAN','wiki_context':'REQUIRES_READBACK','task_pack':'REQUIRES_PROVENANCE','updated_at':bind['created_at']}
    (task/'REVIEW_STATE.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
    return bind

def validate(task):
    b=json.loads((task/'REVIEW_BINDING.json').read_text()); l=json.loads((task/'REVIEW_STATE.json').read_text()); errors=[]
    p=Path(b['candidate_path'])
    if not p.is_file(): errors.append('candidate_missing')
    else:
      text=p.read_text(encoding='utf-8')
      if sha(p)!=b['candidate_sha256']: errors.append('candidate_sha_mismatch')
      if p.stat().st_size != b.get('candidate_bytes'): errors.append('candidate_bytes_mismatch')
      if text.splitlines()[0] != b.get('first_line'): errors.append('candidate_first_line_mismatch')
      if text.rstrip('\\n').splitlines()[-1] != b.get('last_line'): errors.append('candidate_last_line_mismatch')
    chapters=split_chapters(p.read_text(encoding='utf-8')) if p.is_file() else {}
    for n,x in b.get('chapters',{}).items():
      body=chapters.get(int(n))
      if body is None:
        errors.append(f'chapter_{n}_missing')
        continue
      if x['sha256']!=hashlib.sha256(body.encode()).hexdigest(): errors.append(f'chapter_{n}_sha_mismatch')
      if x.get('cjk') != cjk(body): errors.append(f'chapter_{n}_cjk_mismatch')
      if x.get('first_line') != body.splitlines()[0]: errors.append(f'chapter_{n}_first_line_mismatch')
      if x.get('last_line') != body.rstrip('\\n').splitlines()[-1]: errors.append(f'chapter_{n}_last_line_mismatch')
    if set(l.get('seats',{})) != set(SEATS): errors.append('seat_set_mismatch')
    if l.get('candidate',{}).get('candidate_sha256')!=b['candidate_sha256']: errors.append('ledger_binding_mismatch')
    if l.get('candidate',{}).get('candidate_bytes')!=b.get('candidate_bytes'): errors.append('ledger_candidate_bytes_mismatch')
    if l.get('total_review')=='PASS' and any(l.get('seats',{}).get(s,{}).get('status') not in PASS for s in SEATS): errors.append('total_review_false_pass')
    if l.get('g4') not in {'BLOCKED_UNTIL_ALL_SINGLE_SEATS_PASS','READY_FOR_G4'}: errors.append('g4_state_invalid')
    for seat in SEATS:
      x=l.get('seats',{}).get(seat,{})
      if x.get('status') in PASS and (x.get('candidate_sha256')!=b['candidate_sha256'] or not x.get('reviewed_fulltext') or not x.get('report')): errors.append(f'{seat}_pass_missing_provenance')
    if any(x.get('status') not in PASS for x in l.get('seats',{}).values()):
      if l.get('total_review')=='PASS': errors.append('total_review_false_pass')
    print(json.dumps({'ok':not errors,'errors':errors,'candidate_sha256':b['candidate_sha256'],'seats':{k:v.get('status') for k,v in l['seats'].items()}},ensure_ascii=False))
    return 0 if not errors else 2

ap=argparse.ArgumentParser(); ap.add_argument('--task-dir',required=True); ap.add_argument('--candidate',required=True); ap.add_argument('--init',action='store_true'); ap.add_argument('--check',action='store_true'); a=ap.parse_args(); t=Path(a.task_dir)
if a.init: make(t,Path(a.candidate))
if a.check: raise SystemExit(validate(t))
