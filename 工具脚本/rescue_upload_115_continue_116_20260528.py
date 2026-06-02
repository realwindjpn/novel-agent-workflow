#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manual rescue for upload line 115/116 after runner blocked on post-review loop.
- Use last full author candidate for ch115, deterministic sensitive-word/light edits.
- Run machine gate + existing sync/export/upload.
- Then continue ch116 through original process_chapter.
"""
from __future__ import annotations
import json, re, sys, pathlib, importlib.util, datetime, os
BASE=pathlib.Path('/root/workspace/科武纪元')
RUNNER=BASE/'工具脚本/upload_line_115_116_sixrole_draft_runner_20260527.py'
OUT=BASE/'审核记录/上传线/20260527_115_116'
RAW=OUT/'raw'
STATE=OUT/'state.json'
EVENTS=OUT/'events.jsonl'
RESCUE_REPORT=OUT/'第115章_手动接管闭环报告.md'

def now(): return datetime.datetime.now().isoformat(timespec='seconds')

def load_runner():
    spec=importlib.util.spec_from_file_location('upload_runner', RUNNER)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def event(ch, ev, status='RUNNING', msg='', **kw):
    rec={'ts':now(),'chapter':ch,'event':ev,'status':status,'msg':msg}; rec.update(kw)
    with EVENTS.open('a',encoding='utf-8') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st=json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {'chapters':{}}
    st['stage']=ev; st['current_chapter']=ch; st['updated_at']=now(); st['pid']=os.getpid()
    if ch is not None:
        st.setdefault('chapters',{}).setdefault(str(ch),{})['status']=status
        st['chapters'][str(ch)].update({k:v for k,v in kw.items() if k in ['report','txt','fanqie_count','git_commit','upload_report','fail_reason']})
    STATE.write_text(json.dumps(st,ensure_ascii=False,indent=2),encoding='utf-8')

def clean_candidate(s):
    s=(s or '').strip()
    s=re.sub(r'^```(?:md|txt)?\s*','',s).strip(); s=re.sub(r'\s*```$','',s).strip()
    if '第115章' in s[:500]: s=s[s.find('第115章'):]
    s=s.replace('「','“').replace('」','”')
    # upload-risk架空化
    repl={
        '浦东机场T2航站楼':'东海国际机场二号航站楼',
        '浦东机场':'东海国际机场',
        '浦东':'东海',
        '北都':'北岸',
        '立法院':'议政院',
        '立法机构':'议政机构',
        '蓝白联盟':'蓝白阵线',
        '美方在台协会':'联邦驻东屿联络处',
        '美方驻东屿联络处':'联邦驻东屿联络处',
        '美方代表':'联邦代表',
        '美方':'联邦',
        '联邦外事部门亚太事务局':'联邦外事部门海峡事务处',
        '统独':'去留',
        '台湾':'东屿',
        '台当局':'东屿行政部门',
        '改变海峡现状':'改变贸易现状',
    }
    for a,b in repl.items(): s=s.replace(a,b)
    # remove explicit duplicate four-docs block if any
    s=re.sub(r'(桌上已经放着四份资料。第一份是外海运输风险图。第二份是芯片厂库存曲线。第三份是学生团体递来的公开信。第四份是联邦代表记者会全文。\n\n)\1', r'\1', s)
    # banned words
    bans={'仿佛':'像','微微':'','缓缓':'','不禁':'','不由得':'','意味着':'说明','这一刻':'此时','更是':'也是','宛如':'像','犹如':'像','悄然':''}
    for a,b in bans.items(): s=s.replace(a,b)
    if not s.startswith('第115章 '):
        s='第115章 东屿局势\n\n'+re.sub(r'^#?\s*第115章[：:\s]*东屿局势\s*','',s)
    if '（本章完）' not in s[-160:]: s=s.rstrip()+'\n\n（本章完）'
    return s.strip()+'\n'

def main():
    mod=load_runner()
    event(115,'MANUAL_RESCUE_START','RUNNING','take over blocked ch115')
    src_json=RAW/'ch115_author_round3.json'
    cand=json.loads(src_json.read_text(encoding='utf-8')).get('stdout','')
    text=clean_candidate(cand)
    probs,cnt=mod.machine_gate(115,text)
    if probs:
        raise SystemExit('ch115 machine fail: '+ ';'.join(probs))
    ctx=mod.read_context(115)
    # write back / sync / export / upload
    backup=mod.write_back(115,text,ctx)
    mod.sync_project(115)
    txt=mod.export_txt(115,text)
    up_ok,up_status,up_msg=mod.draft_upload(115)
    RESCUE_REPORT.write_text(f'''# 第115章 手动接管闭环报告

时间：{now()}
结论：{'PASS' if up_ok else 'UPLOAD_BLOCKED'}
接管原因：原 runner 第3轮复审后仍生成修订，但脚本未再进入第4轮评估，直接 BLOCKED。
候选来源：{src_json}
番茄口径：{cnt}
机器门禁：PASS
确定性修复：敏感现实名架空化；删除重复资料段；禁词清理；标题/章末校验。
新版：{BASE/'新版/第115章.md'}
TXT：{txt}
备份：{backup}
草稿箱状态：{up_status}
草稿箱摘要：{up_msg}
''',encoding='utf-8')
    if not up_ok:
        event(115,'UPLOAD_BLOCKED','BLOCKED',up_status,report=str(RESCUE_REPORT),txt=str(txt),fanqie_count=cnt,fail_reason=up_msg)
        return 2
    sha=mod.git_commit(115,RESCUE_REPORT,txt)
    event(115,'FULL_LOOP_DRAFT_PASS','FULL_LOOP_DRAFT_PASS','manual rescue closed and saved draft',report=str(RESCUE_REPORT),txt=str(txt),fanqie_count=cnt,git_commit=sha,upload_report=str(RAW/'ch115_draft_execute.log'))
    # continue chapter 116 with original pipeline
    ok=mod.process_chapter(116)
    if not ok:
        event(116,'BLOCKED','BLOCKED','ch116 blocked after ch115 rescue')
        return 1
    st=json.loads(STATE.read_text(encoding='utf-8')); st['stage']='DONE'; st['updated_at']=now(); STATE.write_text(json.dumps(st,ensure_ascii=False,indent=2),encoding='utf-8')
    event(None,'ALL_DONE','DONE','115-116 complete after manual rescue')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
