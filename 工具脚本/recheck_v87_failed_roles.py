#!/usr/bin/env python3
from __future__ import annotations
import json, re, subprocess, time
from pathlib import Path
from datetime import datetime
BASE=Path('/root/workspace/科武纪元')
ORCH=BASE/'工具脚本/orchestrate_review.py'
EVID=BASE/'工具脚本/build_review_evidence.py'
RAW=BASE/'审核记录/六角色外审/raw'
REC=BASE/'审核记录/六角色外审'
FAILED={86:['editor','science'],95:['editor','military','science'],184:['editor','military'],217:['editor'],233:['editor']}
RAW.mkdir(parents=True,exist_ok=True)

def sh(cmd,timeout=260):
 p=subprocess.run(cmd,text=True,capture_output=True,timeout=timeout); return p.returncode,p.stdout.strip(),p.stderr.strip()
def strip(s):
 s=re.sub(r'<think>.*?</think>','',s,flags=re.S); s=re.sub(r'<[^>]+>','',s); return s.strip()
def verdict(s):
 h=' '.join([x.strip() for x in strip(s).splitlines() if x.strip()][:4]).upper()
 if any(w in h for w in ['FAIL','硬伤','必改','不宜进入','不能进入','重写','不通过']): return 'FAIL'
 if any(w in h for w in ['PASS','通过','可进入','无硬伤']): return 'PASS'
 return 'UNKNOWN'
def evidence(ch,limit=3000):
 txt=(BASE/'审核记录/证据包'/f'第{ch}章_证据包.md').read_text(encoding='utf-8',errors='ignore')
 parts=[]
 for sec in ['## 本地预检','## 尾段行号','## 证据地图：章末钩子','## 证据地图：大纲锚点','## 证据地图：技术动作','## 证据地图：军事动作','## 证据地图：投稿风险','## 首段行号']:
  m=re.search(r'(^'+re.escape(sec)+r'.*?)(?=^## |\Z)',txt,flags=re.S|re.M)
  if m: parts.append(m.group(1).strip())
 return '\n\n'.join(parts)[:limit]
def prompt(role,ch,ev):
 base=f'只做复审，不续写，不改文。对象:《科武纪元》第{ch}章V8.7修复稿。此前你或同角色指出的问题已小修，请只判断这些问题是否已解决。第一行只写 PASS 或 FAIL；若仍有硬伤/必改，第一行必须 FAIL。理由≤3条。\n\n'
 focus={
  86:'重点：首行章节编号已删除；第490行论文腔已动作化；叶启明证据强度已降低；熵增口号已压缩。',
  95:'重点：正文中“第86章”已删除；湍急河流/浮木比喻已删除；密钥来源改为欧陆分支局部授权缺口；芯片段改为推理芯片动作化。',
  184:'重点：核对完整尾段；OODA/边缘AI说明已压缩为动作；死循环改为看门狗超时/安全降级；补了战区电子侦察与网络渗透动作。',
  217:'重点：首行章节编号已删除；尾段补公司内部接口/内鬼钩子；报告化解释已压成终端授权和拘押通道动作。',
  233:'重点：统一“未进立案主材料/异常附录单列”；补物流网出现深空导航字段的合理性；强化下午三点经侦行动钩子。'
 }[ch]
 return base+focus+'\n\n'+ev

def call(role,ch):
 rc,out,err=sh(['python3',str(ORCH),'--role',role,'--chapter',str(ch),'--prompt',prompt(role,ch,evidence(ch))])
 try: data=json.loads(out) if rc==0 else {'role':role,'ok':False,'content':err or out}
 except Exception as e: data={'role':role,'ok':False,'content':f'parse {e}: '+out[:300]}
 ts=datetime.now().strftime('%Y%m%d_%H%M%S')
 p=RAW/f'第{ch}_{role}_v87_recheck_{ts}.json'
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 return data,p,verdict(data.get('content','')) if data.get('ok') else 'FAIL'
summary=[]
for ch,roles in FAILED.items():
 sh(['python3',str(EVID),str(ch)],timeout=120)
 rows=[]; final='PASS'
 for role in roles:
  print('RECHECK',ch,role,flush=True)
  data,path,v=call(role,ch); rows.append((role,data,path,v))
  if v!='PASS': final='FAIL'
  time.sleep(1)
 rec=REC/f'第{ch}章.md'
 old=rec.read_text(encoding='utf-8',errors='ignore') if rec.exists() else f'# 第{ch}章 六角色外审记录\n'
 md=['',f'## V8.7修复后复审 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}','','|角色|provider/model|ok|结论|raw|','|---|---|---|---|---|']
 for role,data,path,v in rows:
  md.append(f'|{role}|{data.get("provider","?")}/{data.get("model","?")}|{data.get("ok",False)}|{v}|{path}|')
 md+=['',f'## V8.7复审结论\n{final}','']
 rec.write_text(old.rstrip()+'\n'+'\n'.join(md),encoding='utf-8')
 summary.append({'chapter':ch,'final':final,'roles':{r:{'ok':d.get('ok'), 'verdict':v, 'model':d.get('model'), 'raw':str(p)} for r,d,p,v in rows}})
out=BASE/'审核记录/V87_MiMoPro_正文修改准备包_20260508/外审修复复审汇总.json'
out.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'summary_file':str(out),'summary':summary},ensure_ascii=False,indent=2))
