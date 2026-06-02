#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.2 sequential six-role refinement.
Route: TKX gpt-5.5 author, WF claude-opus-4-7-high-fast editor.
One chapter per run; no parallelism; no git; no upload TXT.
"""
from pathlib import Path
import os, json, time, re, sys, shutil, subprocess, urllib.request, urllib.error

BASE = Path('/root/workspace/科武纪元')
RAW = BASE/'审核记录/六角色外审/raw'
REV = BASE/'审核记录/六角色外审'
TASK = BASE/'审核记录/任务卡'
TMP = BASE/'审核记录/临时精修'
BACK = BASE/'审核记录/备份/V8122_顺序精修_20260515'
for d in [RAW, REV, TASK, TMP, BACK]: d.mkdir(parents=True, exist_ok=True)

ROLES = {
    'author':  {'provider':'TKX','base':'https://tokenx24.com/v1','key_env':'TOKENX_API_KEY','model':'gpt-5.5'},
    'editor':  {'provider':'WF','base':'http://43.135.181.17:8081/v1','key_env':'WF_API_KEY','model':'claude-opus-4-7-high-fast'},
    'reader':  {'provider':'MiniMaxCN','base':'https://api.minimaxi.com/v1','key_env':'MINIMAX_CN_API_KEY','model':'MiniMax-M2.7'},
    'military':{'provider':'DashScope','base':'https://coding.dashscope.aliyuncs.com/v1','key_env':'DASHSCOPE_API_KEY','model':'qwen3.6-plus'},
    'science': {'provider':'ZAI','base':'https://open.bigmodel.cn/api/coding/paas/v4','key_env':'ZAI_API_KEY','model':'glm-5.1'},
}

CHAPTERS = {
    110: {
        'title':'天门封锁',
        'level':'中大改',
        'must':['红线表：叫停权/许可冻结/保险上浮/热线延迟，不写正式协议', '延迟表：港口排队、保险停保、备件许可、证书续期拖慢行动', '物理咽喉+数字锁死双绞杀', '保留既有V8.9天门封锁/MATCH控制器/医疗船误击链', '不触碰第95，不把峰会新闻硬塞正文'],
        'hook':'内鬼调查/审计权限/导师技术特征',
        'next':'内鬼调查',
    },
    221: {
        'title':'共管协议','level':'中大改',
        'must':['共管争夺从所有权升级到训练接口/调度协议/月面中继/救援规则', '交换表：芯片、稀土、能源、云接口、日志留存权', '规则权争夺落到会议条款和工程接口', '不重写第95'],
        'hook':'来客代号/暗线浮现','next':'暗线浮现'
    },
    189: {
        'title':'方舟真相','level':'中大改',
        'must':['方舟协议不是纯信息揭示，要受芯片、电力、接口、许可证、供应链窗口牵制', '文明级备份也有现实账单', '保留父亲/女娲/戴森球全链路主线'],
        'hook':'火星线索','next':'火星线索'
    },
    223: {
        'title':'内战爆发','level':'中改',
        'must':['白盾/铁幕内战补AI视频众包机制：任务池、模板、水印、付款链、转发时间戳', '审计冻结、证书轮换造成城市封控与抓捕延迟/误伤', '不写现实国名对骂'],
        'hook':'公司真相','next':'公司真相'
    },
    226: {
        'title':'政治联盟','level':'中改',
        'must':['联盟不是表态，补执法权、拘押权、日志留存权、AI透明度审计框架', '交换表落到条款、接口、审计权限', '火星探索权与技术节点控制权分歧保留'],
        'hook':'火星计划','next':'火星计划'
    },
}


def load_env():
    p=Path('/root/.hermes/.env')
    if p.exists():
        for line in p.read_text(encoding='utf-8',errors='ignore').splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                k,v=line.split('=',1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def call(role, prompt, max_tokens=1800, temp=0.15, tag='call', timeout=240):
    cfg=ROLES[role]; key=os.environ.get(cfg['key_env'],'')
    rec={'role':role,'provider':cfg['provider'],'requested_model':cfg['model'],'base':cfg['base'],'ok':False,'tag':tag}
    if not key:
        rec['error']='missing '+cfg['key_env']; return rec
    # TKX gpt-5.5 长文输出需要更大 max_tokens；允许用环境变量单独覆盖。
    if role == 'author':
        try:
            max_tokens = int(os.environ.get('TOKENX_AUTHOR_MAX_TOKENS', str(max_tokens)))
        except Exception:
            pass
    data={'model':cfg['model'],'messages':[{'role':'user','content':prompt}], 'max_tokens':max_tokens, 'temperature':temp}
    req=urllib.request.Request(cfg['base'].rstrip()+'/chat/completions', data=json.dumps(data,ensure_ascii=False).encode(), headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    t=time.time()
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            body=r.read().decode('utf-8','ignore'); js=json.loads(body)
            msg=(js.get('choices') or [{}])[0].get('message',{})
            content=(msg.get('content') or msg.get('reasoning_content') or '').strip()
            rec.update(ok=bool(content),status=r.status,latency=round(time.time()-t,2),returned_model=js.get('model'),content=content,usage=js.get('usage',{}))
    except urllib.error.HTTPError as e:
        rec.update(status=e.code,latency=round(time.time()-t,2),error=e.read().decode('utf-8','ignore')[:800])
    except Exception as e:
        rec.update(status='EXC',latency=round(time.time()-t,2),error=repr(e))
    return rec

def save_raw(ch, name, rec):
    p=RAW/f'第{ch}_{name}_v8122.json'
    p.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8')
    return p

def clean_text(s):
    s=re.sub(r'^```(?:md|txt)?\s*','',s.strip())
    s=re.sub(r'\s*```$','',s.strip())
    return s.strip()

def fanqie_count(text):
    lines=[x for x in text.splitlines() if x.strip()]
    title=lines[0] if lines else ''
    return len(re.sub(r'\s+','',text))-len(re.sub(r'\s+','',title))

def passish(rec):
    c=(rec.get('content') or '')
    c=re.sub(r'<think>.*?</think>','',c,flags=re.S).strip()
    first=next((x.strip() for x in c.splitlines() if x.strip()),'')
    neg=['FAIL','不通过','不能进入','重写全文','硬伤未修','严重跑偏','无追读']
    pos=['PASS','通过','可进入下一章','可以进入下一章','整体可用','想继续看','合格']
    return rec.get('ok') and any(x in c for x in pos) and not any(x in c[:600] for x in neg)

def read_style():
    paths=[
        '/root/workspace/写作角色OS/writer_role_core.md',
        '/root/workspace/写作角色OS/experience_distillation_rules.md',
        '/root/workspace/科武纪元/参考资料/作家风格OS/author_prompt_patch.md',
        '/root/workspace/写作角色OS/小说写作学习_Dashen_20260510.md',
    ]
    out=[]
    for p in paths:
        q=Path(p)
        if q.exists(): out.append(f'## {q.name}\n'+q.read_text(encoding='utf-8',errors='ignore')[:1800])
    return '\n'.join(out)

def outline_context():
    outline=(BASE/'wiki/raw/outline/科武纪元大纲_latest.md').read_text(encoding='utf-8',errors='ignore')
    m=re.search(r'> \*\*V8\.12\.2[\s\S]+?(?=\n> \*\*V8\.12\.1)',outline)
    v8122=m.group(0) if m else outline[:3500]
    chaos=(BASE/'wiki/concepts/chaos-model.md').read_text(encoding='utf-8',errors='ignore')
    i=chaos.find('## V8.12.2 现实变量四表')
    return v8122+'\n\n'+(chaos[i:i+2200] if i>=0 else '')

def refine(ch):
    if ch not in CHAPTERS: raise SystemExit('unsupported chapter')
    meta=CHAPTERS[ch]
    src=BASE/'新版'/f'第{ch}章.md'
    if not src.exists(): raise SystemExit(f'SOURCE_MISSING {src}')
    orig=src.read_text(encoding='utf-8',errors='ignore')
    if fanqie_count(orig)<1500: raise SystemExit(f'SOURCE_TOO_SHORT {fanqie_count(orig)}')
    bak=BACK/f'第{ch}章_精修前.md'; shutil.copy2(src,bak)

    ctx=outline_context()
    style=read_style()
    task=f"""# 第{ch}章 V8.12.2 六角色精修任务卡
- 标题：{meta['title']}
- 调整程度：{meta['level']}
- 模型路由：作者 TKX/gpt-5.5；编辑 WF/claude-opus-4-7-high-fast；读者 MiniMax；军事 Qwen；科学 GLM。
- 本章必须落实：
"""+'\n'.join('- '+x for x in meta['must'])+f"""
- 章末钩子：{meta['hook']}，牵引“{meta['next']}”。
- 边界：主线不动；不重排章节；第95不再新增负担；非上传章不生成已投稿TXT。
- 风格：动作链、物理反馈、账单/接口/证书/延迟；禁新闻串烧、禁口号、禁AI灵魂、禁量子万能。
"""
    (TASK/f'第{ch}章_V8122.md').write_text(task,encoding='utf-8')

    pre_prompt=f"""你是《科武纪元》{ch}章写前外审。基于实际原文和V8.12.2任务卡，输出≤800字修改清单。必须指出：偏纲风险、必改项、不可动主线。

【V8.12.2上下文】\n{ctx[:3600]}

【任务卡】\n{task}

【原文首段】\n{orig[:1600]}

【原文尾段】\n{orig[-2000:]}
"""
    for role in ['editor','military','science']:
        rec=call(role, pre_prompt, max_tokens=1600, tag='pre')
        save_raw(ch, role+'_pre', rec)
    notes=[]
    for role in ['editor','military','science']:
        p=RAW/f'第{ch}_{role}_pre_v8122.json'
        rec=json.loads(p.read_text(encoding='utf-8'))
        notes.append(f"## {role}\n{(rec.get('content') or rec.get('error',''))[:1200]}")
    notes='\n'.join(notes)

    author_prompt=f"""你是《科武纪元》作者。请精修第{ch}章，输出完整正文。

硬约束：
- 保留原章主干和已闭环成果，不推翻重写。
- 只做V8.12.2要求的精细增强。
- 第95章不再新增负担，不把峰会/电网/外交素材回灌到95。
- 正文字数保持在原文±20%内；不要缩写成大纲。
- 首行必须：第{ch}章 {meta['title']}
- 末行必须：（本章完）
- 不输出解释。

【V8.12.2上下文】\n{ctx[:4200]}

【任务卡】\n{task}

【写前外审意见】\n{notes[:3600]}

【作家风格OS】\n{style[:5000]}

【原文全文】\n{orig}
"""
    rec=call('author', author_prompt, max_tokens=12000, temp=0.18, tag='author', timeout=500)
    save_raw(ch,'author',rec)
    if not rec.get('ok'): raise SystemExit('AUTHOR_FAIL '+json.dumps(rec,ensure_ascii=False)[:500])
    new=clean_text(rec['content'])
    if not new.startswith(f'第{ch}章'):
        new=f"第{ch}章 {meta['title']}\n\n"+new
    lines=[x.rstrip() for x in new.splitlines()]
    while lines and not lines[-1].strip(): lines.pop()
    if not lines or lines[-1].strip()!='（本章完）': lines.append('（本章完）')
    new='\n'.join(lines)+'\n'
    for old,repl in {'仿佛':'像','微微':'','缓缓':'','不禁':'','不由得':'','意味着':'说明','意识到':'察觉'}.items(): new=new.replace(old,repl)
    tmp=TMP/f'第{ch}章_V8122_精修稿.tmp.md'; tmp.write_text(new,encoding='utf-8')

    def post_prompt(kind, text):
        return f"""你是《科武纪元》{kind}写后复审。必须基于精修后实际正文判断。
第一行只输出 PASS 或 FAIL。
PASS=可进入项目闭环。FAIL=存在硬伤/跑偏/明显AI味/缺任务卡必打点。
第二行起≤5条理由。

【任务卡】\n{task}
【写后正文首段】\n{text[:2200]}
【写后正文尾段】\n{text[-2600:]}
【V8.12.2上下文】\n{ctx[:2000]}
"""
    ep=call('editor',post_prompt('编辑',new),max_tokens=1600,tag='editor_post',timeout=300); save_raw(ch,'editor_post',ep)
    rp=call('reader',post_prompt('读者',new),max_tokens=1400,tag='reader_post',timeout=300); save_raw(ch,'reader_post',rp)

    # one repair loop if needed
    if not (passish(ep) and passish(rp)):
        repair=f"""你是《科武纪元》作者。以下写后复审未完全通过，请只按意见修复，输出完整正文。
【编辑】\n{ep.get('content') or ep.get('error','')}
【读者】\n{rp.get('content') or rp.get('error','')}
【任务卡】\n{task}
【当前正文】\n{new}
"""
        rec2=call('author',repair,max_tokens=12000,temp=0.12,tag='author_repair',timeout=500); save_raw(ch,'author_repair',rec2)
        if rec2.get('ok'):
            new=clean_text(rec2['content'])
            if not new.startswith(f'第{ch}章'): new=f"第{ch}章 {meta['title']}\n\n"+new
            if not new.rstrip().endswith('（本章完）'): new=new.rstrip()+'\n（本章完）\n'
            tmp.write_text(new,encoding='utf-8')
            ep=call('editor',post_prompt('编辑',new),max_tokens=1600,tag='editor_repost',timeout=300); save_raw(ch,'editor_repost',ep)
            rp=call('reader',post_prompt('读者',new),max_tokens=1400,tag='reader_repost',timeout=300); save_raw(ch,'reader_repost',rp)

    banned=[w for w in ['仿佛','微微','缓缓','不禁','不由得','意味着','意识到'] if w in new]
    must_hit=sum(1 for x in ['保险','许可证','证书','审计','延迟','锁死','红线','交换','港口','备件'] if x in new)
    fq=fanqie_count(new)
    final=passish(ep) and passish(rp) and fq>=3000 and not banned and must_hit>=4
    if final:
        src.write_text(new,encoding='utf-8')
        # project sync without git/vector if possible
        sync = subprocess.run(['python3', str(BASE/'工具脚本/sync_kewu.py'), '--chapter', str(ch), '--message', f'V8.12.2第{ch}章TKX作者+WF编辑顺序精修闭环', '--no-git'], cwd='/root/workspace', capture_output=True, text=True, timeout=300)
        sync_out=sync.stdout+sync.stderr
        txt=BASE/'已投稿'/f'第{ch}章.txt'
        if txt.exists(): txt.unlink()
    else:
        sync_out='SKIPPED final false'

    report=f"""# 第{ch}章 V8.12.2 顺序六角色精修报告

- 章节：第{ch}章《{meta['title']}》
- 路线：TKX gpt-5.5 作者；WF claude-opus-4-7-high-fast 编辑；MiniMax 读者；Qwen 军事；GLM 科学
- 并发：无，一章串行
- 备份：{bak}
- 临时稿：{tmp}
- 写回：{'是' if final else '否'}
- 番茄口径：{fq}
- 禁词残留：{banned}
- 必打词命中数：{must_hit}
- 编辑复审：{'PASS' if passish(ep) else 'FAIL'}
- 读者复审：{'PASS' if passish(rp) else 'FAIL'}
- 项目同步：{'已执行' if final else '未执行'}

## 原始调用记录
- raw/第{ch}_editor_pre_v8122.json
- raw/第{ch}_military_pre_v8122.json
- raw/第{ch}_science_pre_v8122.json
- raw/第{ch}_author_v8122.json
- raw/第{ch}_editor_post_v8122.json / repost if any
- raw/第{ch}_reader_post_v8122.json / repost if any

## sync输出
```text
{sync_out[:3000]}
```
"""
    (REV/f'第{ch}章_V8122_TKX_WF顺序闭环.md').write_text(report,encoding='utf-8')
    summary={'chapter':ch,'final':final,'fanqie':fq,'editor':passish(ep),'reader':passish(rp),'banned':banned,'must_hit':must_hit,'report':str(REV/f'第{ch}章_V8122_TKX_WF顺序闭环.md'),'source':str(src) if final else str(tmp),'backup':str(bak)}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary

if __name__=='__main__':
    load_env()
    ch=int(sys.argv[1]) if len(sys.argv)>1 else 110
    # tiny smoke
    smoke=[]
    for role in ['author','editor']:
        rec=call(role,'只回复OK',max_tokens=8,tag='smoke',timeout=80)
        save_raw(ch,role+'_smoke',rec); smoke.append(rec)
        if not rec.get('ok'): raise SystemExit('SMOKE_FAIL '+role+' '+json.dumps(rec,ensure_ascii=False))
    refine(ch)
