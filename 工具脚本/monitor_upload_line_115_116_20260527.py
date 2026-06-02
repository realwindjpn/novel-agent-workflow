#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""No-agent monitor for upload_line_115_116 runner.
Prints only terminal callback events: FULL_LOOP_DRAFT_PASS / BLOCKED / DONE.
State cursor prevents repeat spam.
"""
from pathlib import Path
import json, os, time, subprocess
OUT=Path('/root/workspace/科武纪元/审核记录/上传线/20260527_115_116')
EVENTS=OUT/'events.jsonl'
STATE=OUT/'monitor_state.json'
RUNSTATE=OUT/'state.json'

def load(p, default):
    if p.exists():
        try: return json.loads(p.read_text(encoding='utf-8'))
        except Exception: return default
    return default

def alive(pid):
    if not pid: return False
    try:
        os.kill(int(pid),0); return True
    except Exception:
        return False

st=load(STATE, {'offset':0})
lines=[]
if EVENTS.exists():
    all_lines=EVENTS.read_text(encoding='utf-8').splitlines()
    start=int(st.get('offset',0))
    for line in all_lines[start:]:
        try: rec=json.loads(line)
        except Exception: continue
        ev=rec.get('event'); status=rec.get('status')
        if ev in ['FULL_LOOP_DRAFT_PASS','UPLOAD_BLOCKED','BLOCKED','RUNNER_EXCEPTION','ALL_DONE'] or status in ['BLOCKED','DONE']:
            ch=rec.get('chapter')
            if ev=='FULL_LOOP_DRAFT_PASS':
                lines.append(f"小哥，第{ch}章已闭环并存草稿箱。字数：{rec.get('fanqie_count')}。报告：{rec.get('report')}")
            elif ev=='ALL_DONE':
                lines.append('小哥，115、116两章已全部闭环并保存草稿箱。')
            else:
                lines.append(f"小哥，上传线阻塞：{ev}｜第{ch}章｜{rec.get('msg','')}。报告：{rec.get('report','')}。")
    st['offset']=len(all_lines)
rs=load(RUNSTATE,{})
if rs.get('stage')=='RUNNING' and rs.get('pid') and not alive(rs.get('pid')):
    lines.append(f"小哥，上传线进程已退出但未DONE。pid={rs.get('pid')}，请主控接管。状态：{RUNSTATE}")
STATE.write_text(json.dumps(st,ensure_ascii=False,indent=2),encoding='utf-8')
print('\n'.join(dict.fromkeys([x for x in lines if x])))
