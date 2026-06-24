#!/usr/bin/env python3
from pathlib import Path
import json, datetime, subprocess, sys, os, textwrap, time

BASE = Path('/root/workspace/科武纪元')
OUT = BASE/'学习记录/平台号观点雷达/runs/run_20260622_联合小样'
OUT.mkdir(parents=True, exist_ok=True)
WATCH = BASE/'学习记录/平台号观点雷达/platform_watchlist.json'
watch = json.loads(WATCH.read_text(encoding='utf-8'))

queries = []
for acc in watch['accounts'][:6]:
    name = acc['name']; kws = acc.get('keywords', [])[:2]; platforms = acc.get('platform_candidates', [])
    if '微信公众号' in platforms or '公众号' in platforms:
        queries.append({'account': name, 'platform': 'wechat', 'query': 'site:mp.weixin.qq.com ' + name + ' ' + ' '.join(kws) + ' 2026'})
    if 'B站' in platforms:
        queries.append({'account': name, 'platform': 'bilibili', 'query': 'site:bilibili.com ' + name + ' ' + ' '.join(kws) + ' 2026'})
    if '微博' in platforms:
        queries.append({'account': name, 'platform': 'weibo', 'query': 'site:weibo.com ' + name + ' ' + ' '.join(kws) + ' 2026'})
    if '知乎' in platforms:
        queries.append({'account': name, 'platform': 'zhihu', 'query': 'site:zhihu.com ' + name + ' ' + ' '.join(kws) + ' 2026'})
queries = queries[:18]

worker = r'''
import json, sys
q=json.loads(sys.argv[1])
try:
 from ddgs import DDGS
 hits=[]
 with DDGS(timeout=8) as ddgs:
  for r in ddgs.text(q['query'], max_results=3):
   hits.append({'title':r.get('title',''), 'url':r.get('href') or r.get('url',''), 'body':r.get('body','')})
 q['hits']=hits
except Exception as e:
 q['error']=repr(e); q['hits']=[]
print(json.dumps(q, ensure_ascii=False))
'''
results=[]
for q in queries:
    try:
        cp=subprocess.run([sys.executable,'-c',worker,json.dumps(q,ensure_ascii=False)], text=True, capture_output=True, timeout=15)
        if cp.stdout.strip():
            results.append(json.loads(cp.stdout.strip().splitlines()[-1]))
        else:
            q['error']='NO_STDOUT:'+cp.stderr[-200:]; q['hits']=[]; results.append(q)
    except subprocess.TimeoutExpired:
        q['error']='QUERY_TIMEOUT_15S'; q['hits']=[]; results.append(q)

noise_terms=['BW2026','哔哩哔哩游戏','直播','下载中心','微信公众平台接口调试','miniprogram/landing_page','客服服务']
signals=[]
for q in results:
    for h in q.get('hits',[]):
        text=(h.get('title','')+' '+h.get('body','')+' '+h.get('url','')).lower()
        score=0
        if q['account'].lower() in text: score+=3
        if q['platform'] in h.get('url',''): score+=1
        if any(k in text for k in ['ai','人工智能','芯片','半导体','中美','地缘','科技','量子','航天','出口管制','产业链']): score+=2
        if any(t.lower() in text for t in noise_terms): score-=5
        status='platform_signal' if score>=2 else 'discovery_only'
        if score<0: status='noise'
        signals.append({'account':q['account'],'platform':q['platform'],'query':q['query'],'hit':h,'score':score,'status':status})
counts={s:sum(1 for x in signals if x['status']==s) for s in ['platform_signal','discovery_only','noise']}
payload={'created_at':datetime.datetime.now().isoformat(timespec='seconds'),'watchlist':str(WATCH),'query_count':len(queries),'raw_results':results,'signals':signals,'signal_counts':counts,'policy':watch['ingest_rules']}
(OUT/'platform_radar_raw.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
md=['# 平台号观点雷达联跑小样 2026-06-22','',f'- query_count: {len(queries)}',f'- signal_counts: {counts}','', '## 可复核线索']
for s in sorted(signals,key=lambda x:x['score'],reverse=True)[:30]:
 h=s['hit']; md.append(f"- [{s['status']}/score={s['score']}] {s['account']} · {s['platform']}｜{h.get('title','')}｜{h.get('url','')}")
 if h.get('body'): md.append('  - '+h.get('body')[:160])
md += ['','## 失败查询']
for r in results:
 if r.get('error'): md.append(f"- {r['account']} · {r['platform']}: {r['error']}")
md += ['','## 下一步','- platform_signal 只作观点/线索；正式素材卡须反查官方/论文/权威源。','- 微信走 collect_web --source wechat；B站走空间/API；微博/知乎需账号与正文核验。']
(OUT/'platform_radar_summary.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'out_dir':str(OUT),'raw':str(OUT/'platform_radar_raw.json'),'summary':str(OUT/'platform_radar_summary.md'),'signal_counts':counts,'query_count':len(queries)},ensure_ascii=False,indent=2))
