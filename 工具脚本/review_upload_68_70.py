import os, re, json, time, pathlib, urllib.request, urllib.error, yaml, datetime
BASE=pathlib.Path('/root/workspace/科武纪元')
HERMES=pathlib.Path('/root/.hermes')
# load env
for line in (HERMES/'.env').read_text().splitlines():
    if '=' in line and not line.strip().startswith('#'):
        k,v=line.split('=',1); os.environ.setdefault(k,v)
cfg=yaml.safe_load((HERMES/'config.yaml').read_text())
PROVIDERS=cfg.get('providers',{})
ROLES={
 'editor':('cpa','gpt-5.5','编辑：审上传前结构、大纲对齐、章末钩子、投稿风险。'),
 'reader':('minimax-cn','MiniMax-M2.7','读者：只审看懂、顺不顺、爽点、AI味、是否想追下一章。'),
 'military':('zai','glm-5.1','军事顾问：审行动链、组织、战术、装备可信度。'),
 'science':('alibaba','qwen3.6-plus','科学顾问：审技术设定、科普表达、硬科技可信度。')
}
CHS=[68,69,70]
OUT_RAW=BASE/'审核记录/六角色外审/raw'; OUT_RAW.mkdir(parents=True, exist_ok=True)
OUT_DIR=BASE/'审核记录/六角色外审'; OUT_DIR.mkdir(parents=True, exist_ok=True)

def provider_conf(name):
    p=PROVIDERS[name]
    key=p.get('api_key') or os.environ.get(p.get('key_env',''))
    return p['base_url'].rstrip('/'), key

def call(provider, model, prompt, max_tokens=1200):
    base,key=provider_conf(provider)
    payload={'model':model,'messages':[{'role':'user','content':prompt}], 'max_tokens':max_tokens}
    data=json.dumps(payload, ensure_ascii=False).encode()
    req=urllib.request.Request(base+'/chat/completions', data=data, headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode())

def strip_think(s):
    s=re.sub(r'<think>.*?</think>','',s,flags=re.S)
    s=re.sub(r'<[^>]+>','',s)
    return s.strip()

def verdict(text):
    t=strip_think(text)
    first=t.splitlines()[0].strip().upper() if t.splitlines() else ''
    if 'FAIL' in first: return 'FAIL'
    if 'PASS' in first:
        if re.search(r'必改|硬伤|不宜上传|不能上传|重写', t): return 'FAIL'
        return 'PASS'
    if re.search(r'不宜上传|不能上传|硬伤|重写|FAIL', t): return 'FAIL'
    if re.search(r'可以上传|可上传|PASS|通过', t): return 'PASS'
    return 'REVIEW'

def brief_evidence(ch):
    p=BASE/f'审核记录/证据包/第{ch}章_evidence.json'
    d=json.loads(p.read_text())
    # prefer title/head/tail/evidence names; cap length
    parts=[f"章节:{ch}", f"文件:{d['file']}", f"首行:{d['first_line']}", f"末行:{d['last_nonempty_line']}", "任务卡:"+d.get('task_card','')[:500], "尾段:\n"+d.get('tail_lines','')[-1800:]]
    ev=[]
    for name,hits in d.get('evidence',{}).items():
        if hits:
            ev.append(f"[{name}]\n"+hits[-1]['chunk'][-700:])
    parts.append('\n'.join(ev)[:1800])
    return '\n\n'.join(parts)[:5200]

summary=[]
for ch in CHS:
    chapter_results=[]
    evidence=brief_evidence(ch)
    for role,(provider,model,role_desc) in ROLES.items():
        prompt=f"""{role_desc}\n任务: 第{ch}章上传前审核。只做审核，不改文，不续写。\n硬格式: 第一行只写 PASS 或 FAIL。若有必改/硬伤/不宜上传，第一行必须 FAIL。第二行起列理由≤3条，小修≤3条。\n关注: 字数/标题/末行已本地通过，重点审内容质量、连续性、投稿风险、AI味、技术/军事可信度。\n\n证据包:\n{evidence}\n"""
        try:
            data=call(provider, model, prompt, max_tokens=1600 if provider!='zai' else 4096)
            content=data.get('choices',[{}])[0].get('message',{}).get('content','') or ''
            ok=True; err=''
        except Exception as e:
            content=''; ok=False; err=repr(e)
            data={'error':err}
        raw_path=OUT_RAW/f'第{ch}_{role}_{provider}_{int(time.time())}.json'
        raw_path.write_text(json.dumps({'chapter':ch,'role':role,'provider':provider,'model':model,'ok':ok,'error':err,'content':content,'raw':data}, ensure_ascii=False, indent=2))
        v=verdict(content) if ok else 'ERROR'
        chapter_results.append({'role':role,'provider':provider,'model':model,'ok':ok,'verdict':v,'content':strip_think(content)[:800],'raw':str(raw_path)})
        print(f'CH{ch} {role} {provider}/{model} {v}', flush=True)
        time.sleep(2)
    final='PASS' if all(r['verdict']=='PASS' for r in chapter_results) else 'FAIL'
    rec=OUT_DIR/f'第{ch}章.md'
    old=rec.read_text(errors='ignore') if rec.exists() else ''
    now=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    block=[f'\n\n## 上传前六角色复审 {now}', f'最终结论: {final}', '', '|角色|模型|结论|', '|---|---|---|']
    for r in chapter_results:
        block.append(f"|{r['role']}|{r['provider']}/{r['model']}|{r['verdict']}|")
    for r in chapter_results:
        block += ['', f"### {r['role']} ({r['provider']}/{r['model']})", r['content'] or r.get('error','')]
    rec.write_text(old+'\n'.join(block))
    summary.append({'chapter':ch,'final':final,'results':chapter_results,'record':str(rec)})
(OUT_DIR/'upload_review_68_70_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print('SUMMARY', json.dumps([{'ch':s['chapter'],'final':s['final']} for s in summary], ensure_ascii=False))
