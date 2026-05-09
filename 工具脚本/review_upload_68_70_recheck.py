import os,re,json,time,pathlib,urllib.request,yaml,datetime
BASE=pathlib.Path('/root/workspace/科武纪元'); H=pathlib.Path('/root/.hermes')
for line in (H/'.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        k,v=line.split('=',1); os.environ.setdefault(k,v)
PROVIDERS=yaml.safe_load((H/'config.yaml').read_text())['providers']
ROLES={
 'editor':('cpa','gpt-5.5','编辑复审：只看上次FAIL项是否修复，结构/投稿风险是否可上传。'),
 'reader':('minimax-cn','MiniMax-M2.7','读者复审：只看读感、AI味、是否想追读，上次卡点是否修复。'),
 'science':('alibaba','qwen3.6-plus','科学顾问复审：只看技术硬伤是否修复。')
}
RAW=BASE/'审核记录/六角色外审/raw'; RAW.mkdir(parents=True,exist_ok=True)
OUT=BASE/'审核记录/六角色外审'

def conf(n):
    p=PROVIDERS[n]; return p['base_url'].rstrip('/'), p.get('api_key') or os.environ.get(p.get('key_env',''))
def call(provider,model,prompt,max_tokens=1200):
    base,key=conf(provider)
    payload={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':max_tokens}
    req=urllib.request.Request(base+'/chat/completions',data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180) as r: return json.loads(r.read().decode())
def clean(s):
    return re.sub(r'<think>.*?</think>','',s,flags=re.S).strip()
def verdict(s):
    t=clean(s); first=t.splitlines()[0].upper() if t.splitlines() else ''
    if 'FAIL' in first or re.search(r'硬伤|必改|不能上传|不宜上传|重写',t): return 'FAIL'
    if 'PASS' in first or re.search(r'可上传|可以上传|通过',t): return 'PASS'
    return 'REVIEW'
def ev(ch):
    d=json.loads((BASE/f'审核记录/证据包/第{ch}章_evidence.json').read_text())
    return ('文件:'+d['file']+'\n首行:'+d['first_line']+'\n末行:'+d['last_nonempty_line']+'\n尾段:\n'+d['tail_lines'][-3000:]+'\n证据:\n'+json.dumps(d['evidence'],ensure_ascii=False)[:1800])[:5200]
issues={68:'已修：羁押掏卡改为证物箱提取；存储卡改屏蔽壳金属模块；补哈希校验、只读、镜像；去文艺比喻；动态跳频/一次性认证种子。请复核是否可上传。',70:'已修：医院电力系统改医院内网电子病历/安防日志；秒级注销改预设清盘脚本/队列/预签；拆报告排比；补数据盘物理恢复、林星辰伤痛动作。请复核是否可上传。'}
summary=[]
for ch in [68,70]:
    rs=[]; evidence=ev(ch)
    for role,(provider,model,desc) in ROLES.items():
        prompt=f'''{desc}\n任务: 第{ch}章上传前定向复审。只做审核，不改文。\n第一行只写 PASS 或 FAIL；若仍有硬伤/必改/不宜上传，第一行必须 FAIL。\n上次FAIL修复说明: {issues[ch]}\n\n证据包:\n{evidence}'''
        try:
            data=call(provider,model,prompt,1600 if provider!='zai' else 4096); content=data['choices'][0]['message'].get('content','') or ''; ok=True; err=''
        except Exception as e:
            data={'error':repr(e)}; content=''; ok=False; err=repr(e)
        v=verdict(content) if ok else 'ERROR'
        raw=RAW/f'第{ch}_{role}_recheck_{provider}_{int(time.time())}.json'; raw.write_text(json.dumps({'ok':ok,'error':err,'content':content,'raw':data},ensure_ascii=False,indent=2))
        rs.append((role,provider,model,v,clean(content)[:800],str(raw)))
        print(f'CH{ch} {role} {v}',flush=True)
        time.sleep(2)
    final='PASS' if all(r[3]=='PASS' for r in rs) else 'FAIL'
    rec=OUT/f'第{ch}章.md'; old=rec.read_text(errors='ignore') if rec.exists() else ''
    now=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    block=[f'\n\n## 上传前定向复审 {now}',f'最终结论: {final}','','|角色|模型|结论|','|---|---|---|']
    for role,provider,model,v,content,rawp in rs: block.append(f'|{role}|{provider}/{model}|{v}|')
    for role,provider,model,v,content,rawp in rs: block += ['',f'### {role} ({provider}/{model})',content]
    rec.write_text(old+'\n'.join(block))
    summary.append({'ch':ch,'final':final})
print('SUMMARY',json.dumps(summary,ensure_ascii=False))
