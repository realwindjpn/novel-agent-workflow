#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, json, time, yaml, requests
from pathlib import Path
BASE=Path('/root/workspace/科武纪元'); CH=93
ENV=Path('/root/.hermes/.env'); CONFIG=Path('/root/.hermes/config.yaml'); RAW=BASE/'审核记录/六角色外审/raw'
if ENV.exists():
    for line in ENV.read_text(encoding='utf-8',errors='ignore').splitlines():
        line=line.strip()
        if line and not line.startswith('#') and '=' in line:
            k,v=line.split('=',1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
cfg=yaml.safe_load(CONFIG.read_text(encoding='utf-8')) or {}
def call(provider,prompt,max_tokens=1800,timeout=240):
    p=(cfg.get('providers') or {}).get(provider,{})
    base=(p.get('base_url') or '').rstrip('/'); model=p.get('default_model') or p.get('model')
    key=p.get('api_key') or os.environ.get(p.get('key_env') or '', '')
    t=time.time()
    try:
        r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':max_tokens,'temperature':0.1},timeout=timeout)
        data=r.json(); msg=((data.get('choices') or [{}])[0].get('message') or {})
        content=(msg.get('content') or msg.get('reasoning_content') or '').strip()
        return {'ok':bool(content) and r.status_code<500,'provider':provider,'model':model,'returned_model':data.get('model') or model,'status':r.status_code,'latency_s':round(time.time()-t,2),'content':content}
    except Exception as e:
        return {'ok':False,'provider':provider,'model':model,'returned_model':None,'status':0,'latency_s':round(time.time()-t,2),'content':repr(e)}
text=(BASE/'新版/第93章.md').read_text(encoding='utf-8')
task=(BASE/'审核记录/六角色外审/第93章_V8121任务卡_20260515.md').read_text(encoding='utf-8')
frag='''主屏右下角同时弹出一张交换表。表格没有标题，只有三列灰字：算力配额从4800降到2100，接应架次从六次缩到两次，行动窗口压缩到19小时。底部一行小字几乎贴着背景色：配额调整与信任指数挂钩。

赵刚的手指停在触控板上方，没有按下去。

林星辰看了那行字两秒，关掉弹窗。盐滩路线重新铺满主屏。他知道这不是建议，是桌下条件。要保住南大陆那边的支援，就得接受这份配额。够打，但不够体面。'''
head='\n'.join(text.splitlines()[:130]); tail='\n'.join(text.splitlines()[-130:])
ev=f'''任务卡:
{task}

新增片段:
{frag}

改后首段:
{head}

改后尾段:
{tail}
机器证据：关键词 交换表/配额/信任/窗口压缩 已存在；林星辰代词已统一为他；非上传章不生成TXT。'''
prompts={
 'alibaba':'你是Qwen编辑终复审。审实际改后第93章摘录和新增片段。标准：章节功能完成、G2屈辱配额轻触够用、不破坏南大陆牵制主线、无投稿污染。最终第一行必须 PASS 或 FAIL。\n'+ev,
 'minimax-cn':'你是MiniMax读者终复审。看是否顺、是否想追第94章、是否AI味、屈辱配额是否突兀；注意：首尾摘录重复是审稿输入重叠，不是正文重复。最终第一行必须 PASS 或 FAIL。\n'+ev,
 'zai':'你是GLM技术终复审。只审交换表/配额/战术窗口压缩/接应架次设定是否有硬伤。最终第一行必须 PASS 或 FAIL。\n'+ev,
}
res={}
for p,pr in prompts.items():
    r=call(p,pr); res[p]=r; (RAW/f'第{CH}_post_review2_{p}_20260515.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({p:{'ok':r['ok'],'status':r['status'],'first':re.sub(r'<think>.*?</think>','',r['content'],flags=re.S|re.I).strip().splitlines()[:2]} for p,r in res.items()},ensure_ascii=False,indent=2))
