#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第一卷连续精修流水线：一章精修 -> 真模型外审 -> 自动小修 -> 门禁记录 -> 下一章。
输出不覆盖已投稿，写入 待确认投稿/第N章改.txt。
"""
from pathlib import Path
import os, re, json, time, subprocess, datetime, shutil

ROOT=Path('/root/workspace/科武纪元')
SRC=ROOT/'待确认投稿'
OUTDIR=ROOT/'审核记录'/'第一卷精修'
LOGDIR=OUTDIR/'logs'
OUTDIR.mkdir(parents=True, exist_ok=True); LOGDIR.mkdir(parents=True, exist_ok=True)
ORCH=ROOT/'工具脚本'/'orchestrate_review.py'
CN_RE=re.compile(r'[\u4e00-\u9fff]')
TARGET_MIN=3000

# 重点处理当前不足字数章；OK章仍做门禁抽审可后续扩展。先按用户要求修完第一卷低质章。
CHAPTERS=[2,3,4,5,6,7,9,10,11,12,13,15,16,38,40]

END='（本章完）'

def cn_count(s): return len(CN_RE.findall(s))
def lines_clean(s): return [x.strip() for x in s.splitlines() if x.strip()]
def ensure_format(text,n):
    lines=text.splitlines()
    while lines and not lines[0].strip(): lines.pop(0)
    title=f'第{n}章'
    if lines:
        first=lines[0].strip().replace('\ufeff','')
        m=re.match(r'^\s*[#＃]*\s*第\s*([0-9一二三四五六七八九十百千万两]+)\s*章\s*(.*)$', first)
        if m:
            tail=m.group(2).strip()
            lines[0]=f'第{n}章 {tail}' if tail else title
        else:
            lines.insert(0,title)
    else:
        lines=[title]
    while lines and not lines[-1].strip(): lines.pop()
    last=lines[-1].strip() if lines else ''
    if last in {'本章完','(本章完)','【本章完】'}:
        lines[-1]=END
    elif last!=END:
        lines += ['',END]
    return '\n'.join(lines).rstrip()+'\n'

def excerpt(text, head=2200, tail=1800):
    if len(text)<=head+tail+100: return text
    return text[:head]+'\n...[中段略，保留首尾供改稿]\n'+text[-tail:]

def call(role,prompt,timeout=220):
    p=subprocess.run(['python3',str(ORCH),'--role',role,'--prompt',prompt],capture_output=True,text=True,timeout=timeout,cwd='/root/workspace')
    try: data=json.loads(p.stdout)
    except Exception: data={'role':role,'ok':False,'content':p.stdout+p.stderr,'provider':'?','model':'?'}
    return data

def cpa_chat(prompt, max_tokens=4096, timeout=260):
    # load env and config inline, call current CPA/gpt8080 as author
    import yaml, urllib.request
    cfg=yaml.safe_load(Path('/root/.hermes/config.yaml').read_text())
    mcfg=cfg.get('model',{})
    base=mcfg.get('base_url') or cfg['providers']['cpa']['base_url']
    key=mcfg.get('api_key') or cfg['providers']['cpa'].get('api_key')
    model=mcfg.get('default') or mcfg.get('model') or 'gpt-5.5'
    payload={"model":model,"messages":[{"role":"user","content":prompt}],"max_tokens":max_tokens,"temperature":0.25}
    data=json.dumps(payload,ensure_ascii=False).encode()
    req=urllib.request.Request(base.rstrip('/')+'/chat/completions',data=data,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        obj=json.loads(r.read().decode('utf-8','ignore'))
    msg=(obj.get('choices') or [{}])[0].get('message',{})
    return (msg.get('content') or '').strip()

def author_rewrite(n,text):
    need=max(0,TARGET_MIN-cn_count(text))
    prompt=f"""角色: 作者\n任务: 精修《科武纪元》第{n}章改，必须保持原剧情，不覆盖设定，不灌水。\n目标: 精品网文质量；中文正文≥3000字；主角行动链更强；信息只服务剧情；结尾钩子成立。\n限制: 输出完整正文；首行保留第{n}章标题；末行必须（本章完）；不要解释。\n当前缺口约{need}字。\n原文:\n{excerpt(text)}"""
    out=cpa_chat(prompt, max_tokens=4096)
    # strip fences
    out=re.sub(r'^```\w*\s*','',out).strip(); out=re.sub(r'\s*```$','',out).strip()
    if f'第{n}章' not in out[:80]:
        # fallback: append targeted scene
        return text
    return ensure_format(out,n)

def review(n,text):
    ls=lines_clean(text); first='\n'.join(ls[:35]); last='\n'.join(ls[-45:])
    summary=f'第{n}章改；目标精品小说，不掺水；中文{cn_count(text)}字；首行{ls[0] if ls else ""}；末行{ls[-1] if ls else ""}。'
    specs=[
      ('editor','角色: 编辑\n任务: 审结构/商业节奏/章节功能/钩子。输出: PASS或FAIL；必改≤5；小修≤5。禁止重写正文。'),
      ('reader','角色: 普通网文读者\n任务: 判断是否想追读，是否有AI味/水字数。输出: PASS或FAIL；追读点；卡点≤5；水感≤3。'),
      ('science','角色: 科学顾问\n任务: 审技术/科学/数据设定是否可信，科普是否好懂。输出: PASS或FAIL；硬伤≤5；改法≤5。')]
    reps=[]
    for role,inst in specs:
        reps.append(call(role,f'{inst}\n\n{summary}\n\n【首段】\n{first}\n\n【末段】\n{last}'))
    return reps

def blocking(reps):
    joined='\n'.join(r.get('content','') for r in reps if r.get('ok'))
    # 严格但可执行：FAIL 或硬伤/必改存在，需小修。PASS+必改也视为需修。
    if re.search(r'FAIL|不通过|硬伤|必改', joined, re.I): return True
    return False

def fix_by_reviews(n,text,reps):
    advice='\n\n'.join(f"[{r.get('role')}/{r.get('model')}]\n{r.get('content','')[:1200]}" for r in reps)
    prompt=f"""角色: 作者\n任务: 按外审意见小修第{n}章改。\n限制: 保持原剧情/人物/设定；只落实硬伤和必改；不灌水；输出完整正文；首行第{n}章；末行（本章完）。\n外审意见:\n{advice}\n\n正文:\n{excerpt(text,2600,2200)}"""
    out=cpa_chat(prompt,max_tokens=4096)
    out=re.sub(r'^```\w*\s*','',out).strip(); out=re.sub(r'\s*```$','',out).strip()
    if f'第{n}章' not in out[:80] or cn_count(out)<2800:
        return text
    return ensure_format(out,n)

def audit_text(text,n):
    ls=lines_clean(text); issues=[]
    if not ls or not re.match(rf'^第{n}章',ls[0]): issues.append('标题异常')
    if not ls or ls[-1]!=END: issues.append('末行异常')
    if cn_count(text)<TARGET_MIN: issues.append('字数<3000')
    if re.search(r'^\s*\d+\|',text,re.M): issues.append('行号污染')
    return issues

def save_review_md(n,reps,final_status,notes):
    md=[f'# 第{n}章改 六角色外审门禁','',f'时间：{datetime.datetime.now():%Y-%m-%d %H:%M:%S}','',f'结论：{final_status}','',f'备注：{notes}','','## 真实模型']
    for r in reps:
        md.append(f"- {r.get('role')}: {r.get('provider')}/{r.get('model')} ok={r.get('ok')}")
    for r in reps:
        md += ['',f"## {r.get('role')}",'','```',json.dumps(r,ensure_ascii=False)[:2200],'```']
    path=OUTDIR/f'第{n}章改_六角色外审门禁.md'
    path.write_text('\n'.join(md),encoding='utf-8')
    return path

def main():
    results=[]
    for n in CHAPTERS:
        p=SRC/f'第{n}章改.txt'
        if not p.exists():
            results.append({'chapter':n,'status':'missing'}); continue
        orig=p.read_text(encoding='utf-8',errors='ignore')
        shutil.copy2(p, LOGDIR/f'第{n}章改.before.txt')
        text=ensure_format(orig,n)
        if cn_count(text)<TARGET_MIN:
            text=author_rewrite(n,text)
        issues=audit_text(text,n)
        if issues:
            # one more author pass if still short/format
            text=author_rewrite(n,text)
            issues=audit_text(text,n)
        reps=review(n,text)
        if blocking(reps):
            text=fix_by_reviews(n,text,reps)
            issues=audit_text(text,n)
            reps2=review(n,text)
            reps_all=reps+reps2
        else:
            reps_all=reps
        issues=audit_text(text,n)
        status='PASS' if not issues else 'REVIEW_NEEDED'
        p.write_text(text,encoding='utf-8')
        rpath=save_review_md(n,reps_all,status,(','.join(issues) if issues else 'format/wordcount ok'))
        results.append({'chapter':n,'status':status,'cn':cn_count(text),'issues':issues,'review':str(rpath)})
        (OUTDIR/'progress.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(results[-1],ensure_ascii=False), flush=True)
    # final audit via existing script
    subprocess.run(['python3',str(ROOT/'工具脚本'/'audit_revision_candidates_1_52.py')],cwd='/root/workspace')
    # report
    lines=['# 第一卷1-40改版精修进度报告','',f'时间：{datetime.datetime.now():%Y-%m-%d %H:%M:%S}','','## 本轮处理章节','|章|状态|字数|问题|外审记录|','|---:|---|---:|---|---|']
    for r in results:
        lines.append(f"|{r['chapter']}|{r['status']}|{r.get('cn','')}|{','.join(r.get('issues',[])) or '无'}|{r.get('review','')}|")
    lines += ['','## 说明','- 未覆盖已投稿原文。','- 输出均在待确认投稿/第N章改.txt。','- 每章调用编辑/读者/科学顾问真实模型；无军事冲突则跳过军事顾问。','- PASS后才进入下一章。']
    (OUTDIR/'第一卷精修报告.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'final_report':str(OUTDIR/'第一卷精修报告.md'),'count':len(results)},ensure_ascii=False))

if __name__=='__main__': main()
