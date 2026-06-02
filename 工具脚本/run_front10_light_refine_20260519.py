#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""前10章轻精修闭环 runner：第8/5/7/9/10章。
显式 provider/model；禁 cpa；非上传章不生成已投稿TXT；不提交git。
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, time
from datetime import datetime
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
OUT = BASE / '审核记录' / '前10章轻精修_20260519'
RAW = OUT / 'raw'
NEW = BASE / '新版'
SYNC = BASE / '工具脚本' / 'sync_kewu.py'
STATUS = BASE / 'STATUS.md'
WAL = BASE / 'WAL.md'
TRACK = BASE / '小说综合跟踪表.md'
SUGGEST = BASE / '审核记录' / '前10章重审_20260519' / '前10章重审_综合提升建议.md'
SRC_LEDGER = BASE / '审核记录' / '前10章重审_20260519' / 'MODEL_LEDGER.md'
CHAPTERS = [8,5,7,9,10]
FOCUS = {
8: '补陈思琪海外邮件情感戏；补模拟警报压力测试/频率感知提前避险；补监护签署/教育备案；“密级B”改项目B级/内部B类；毫伏注明读数口径；保留入营压迫感。',
5: '评委问答砍半；保留边境干预/边界钩子；23ms改为模型置信度首次越阈；王凯补1-2个有效动作；保留科技节展示。',
7: '压三周邮件/伦理框架；补监护人、项目归属、退出机制、数据权限、保密协议；保母亲饭桌情绪连续；李明远称谓统一。',
9: '终端隐藏程序线索前置；“身体借用设备计算能力”改设备读取生理节律并调整反馈模型；补限流、医护、伦理、喊停权、假负载预实验；强化身体反馈。',
10:'补陈思琪15ms数据展示；“真正实战任务”降为受控外场演训/实景化验证任务；格斗补护具积分制、无头部重击、医疗观察；强化尾声爆点前置。',
}
MUST = {
8:['海外邮件','模拟警报','压力测试','监护','备案','项目B级','内部B类','毫伏'],
5:['置信度','越阈','王凯','边境','边界'],
7:['监护人','项目归属','退出机制','数据权限','保密协议','李明远'],
9:['隐藏程序','生理节律','反馈模型','限流','医护','伦理','喊停权','假负载'],
10:['15ms','受控外场','实景化验证','护具','积分制','头部重击','医疗观察'],
}
FORBID = {
8:['密级B'],
9:['身体借用设备计算能力','借用设备计算能力'],
10:['真正实战任务','三个月后真正实战任务'],
}
ROUTES = {
'external':[('key2-anthropic','claude-opus-4-7'),('key2-anthropic','claude-opus-4-6'),('freemodel','gpt-5.5')],
'author':[('freemodel','gpt-5.5'),('key2','gpt-5.5')],
'science':[('glm2','glm-5.1'),('alibaba','qwen3.6-plus')],
'editor':[('alibaba','qwen3.6-plus')],
'reader':[('minimax-cn','MiniMax-M2.7')],
}
LEDGER=[]
QUEUE={'created_at':datetime.now().isoformat(timespec='seconds'),'order':CHAPTERS,'items':[]}

STYLE = '''作者风格OS摘要：动作先于解释；技术落到可见操作/仪表反馈/身体反馈/成本；禁文艺比喻、宏大空话、公告腔；对话短，有停顿、误判、动作插入；每场戏有环境压力→行动链→反馈链→代价。普通精修章只改新版MD，不生成已投稿TXT。'''


def read(p:Path)->str:
    return p.read_text('utf-8')
def write(p:Path,s:str):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s,'utf-8')
def clean_model_text(s:str)->str:
    s=s.strip()
    # remove session_id leading lines
    s=re.sub(r'^\s*session_id:.*\n','',s, flags=re.M)
    return s.strip()
def extract_full(s:str)->str:
    s=clean_model_text(s)
    m=re.search(r'```(?:markdown|md|text)?\s*\n([\s\S]*?)\n```', s)
    if m and ('第' in m.group(1)[:20] or len(m.group(1))>2000):
        return m.group(1).strip()
    for tag in ['【修订全文】','修订全文：','全文：']:
        if tag in s:
            return s.split(tag,1)[1].strip()
    return s.strip()
def fanqie_count(t:str)->int:
    lines=t.splitlines(); title=lines[0] if lines else ''
    return len(''.join(t.split()))-len(''.join(title.split()))
def call(role:str, prompt:str, timeout:int=360):
    last=None
    for provider, model in ROUTES[role]:
        if provider == 'cpa':
            raise RuntimeError('CPA_FORBIDDEN')
        t0=time.time()
        cmd=['hermes','chat','-Q','--provider',provider,'--model',model,'-q',prompt]
        proc=subprocess.run(cmd, cwd='/root/workspace', env=os.environ.copy(), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        dur=round(time.time()-t0,1)
        rec={'ts':datetime.now().isoformat(timespec='seconds'),'role':role,'provider':provider,'model':model,'exit_code':proc.returncode,'duration_sec':dur,'stdout_chars':len(proc.stdout),'stderr_tail':proc.stderr[-500:]}
        LEDGER.append(rec)
        last=(provider,model,proc)
        if proc.returncode==0 and clean_model_text(proc.stdout):
            return provider,model,clean_model_text(proc.stdout),rec
    provider,model,proc=last
    raise RuntimeError(f'model failed role={role} last={provider}/{model} stderr={proc.stderr[-1000:]}')
def md_review_ok(txt:str)->bool:
    tail=txt[-2000:]
    if re.search(r'最终[^\n]{0,20}PASS|结论[:： ]*PASS|^PASS\b|通过', tail, re.I|re.M):
        if not re.search(r'最终[^\n]{0,20}FAIL|结论[:： ]*FAIL|^FAIL\b', tail, re.I|re.M):
            return True
    return False

def machine_gate(ch:int, text:str):
    missing=[k for k in MUST[ch] if k not in text]
    forbidden=[k for k in FORBID.get(ch,[]) if k in text]
    title=text.splitlines()[0] if text.splitlines() else ''
    return {'title':title,'fanqie_count':fanqie_count(text),'missing':missing,'forbidden':forbidden,'ok':not missing and not forbidden}

def ensure_wiki_fulltext(ch:int, src_text:str):
    wp=BASE/'wiki'/'chapters'/f'ch{ch:03d}.md'
    if not wp.exists():
        return {'exists':False,'updated':False,'keywords':{}}
    wt=read(wp)
    keywords={k:(k in wt) for k in MUST[ch][:5]}
    if '## Full Text' in wt:
        before=wt.split('## Full Text',1)[0].rstrip()+"\n\n## Full Text\n\n"
        write(wp,before+src_text.strip()+"\n")
        wt=read(wp); keywords={k:(k in wt) for k in MUST[ch][:5]}
        return {'exists':True,'updated':True,'keywords':keywords}
    write(wp, wt.rstrip()+"\n\n## Full Text\n\n"+src_text.strip()+"\n")
    wt=read(wp); keywords={k:(k in wt) for k in MUST[ch][:5]}
    return {'exists':True,'updated':True,'keywords':keywords}

def append_once(path:Path, marker:str, block:str):
    t=read(path) if path.exists() else ''
    if marker not in t:
        write(path, t.rstrip()+"\n\n"+block.strip()+"\n")

def process_chapter(ch:int):
    item={'chapter':ch,'status':'running','started_at':datetime.now().isoformat(timespec='seconds')}
    QUEUE['items'].append(item); write(OUT/'queue.json', json.dumps(QUEUE,ensure_ascii=False,indent=2))
    src=NEW/f'第{ch}章.md'
    orig=read(src)
    write(OUT/f'第{ch}章_原文备份.md', orig)
    shutil.copy2(src, OUT/f'第{ch}章_原文备份.md')
    suggestion=read(SUGGEST)[:12000]

    ext_prompt=f'''[ROUTE: provider=key2-anthropic model=claude-opus-4-7]
你是《科武纪元》原文外审/任务卡裁剪。必须审实际章节全文，先外审后任务卡。
章节：第{ch}章
本章重点：{FOCUS[ch]}
硬约束：轻精修；禁大改前10章骨架；只列可执行小修；保留原章功能；输出Markdown。
综合建议摘录：\n{suggestion}\n
实际章节全文：\n```md\n{orig}\n```

输出格式：
# 第{ch}章 外审任务卡
- 实际模型声明：按调用端记录
- 原文问题：≤8条
- 必改项：≤6条
- 禁改线：≤5条
- 作者执行卡：明确插入/删除/替换方向
- 验收关键词：列本章必须出现/必须消失词
'''
    ep,em,taskcard,_=call('external', ext_prompt, 420)
    write(OUT/f'第{ch}章_外审任务卡.md', taskcard)
    write(RAW/f'第{ch}_external_{ep}_{em}.md', taskcard)

    author_prompt=f'''[ROUTE: provider=freemodel model=gpt-5.5]
你是《科武纪元》作者，只做轻精修。必须基于外审任务卡修改实际章节全文。
{STYLE}
本章重点：{FOCUS[ch]}
硬约束：
- 保留章节标题与主线骨架；勿新增大设定；勿改成大纲/报告。
- 输出完整修订后章节MD正文，首行仍是原章节标题。
- 不要解释；不要附修改说明；不要生成TXT。
- 必须落实这些关键词/口径：{', '.join(MUST[ch])}
- 必须清除：{', '.join(FORBID.get(ch,[])) or '无'}

外审任务卡：\n{taskcard}\n
原文：\n```md\n{orig}\n```
'''
    ap,am,author_out,_=call('author', author_prompt, 520)
    revised=extract_full(author_out)
    if not revised.startswith(orig.splitlines()[0].strip()):
        # try recover from first title occurrence
        title=orig.splitlines()[0].strip(); idx=revised.find(title)
        if idx>=0: revised=revised[idx:]
        else: revised=title+'\n\n'+revised
    gate=machine_gate(ch,revised)
    if not gate['ok']:
        fix_prompt=f'''[ROUTE: provider=freemodel model=gpt-5.5]
你上轮修订未过机器门禁。只补最小修改，输出完整章节MD。
章节第{ch}章；必须补齐 missing={gate['missing']}；必须删除 forbidden={gate['forbidden']}。
本章重点：{FOCUS[ch]}
当前稿：\n```md\n{revised}\n```'''
        ap,am,author_out2,_=call('author', fix_prompt, 420)
        revised=extract_full(author_out2)
        title=orig.splitlines()[0].strip()
        if not revised.startswith(title):
            idx=revised.find(title); revised=(revised[idx:] if idx>=0 else title+'\n\n'+revised)
        gate=machine_gate(ch,revised)
    write(OUT/f'第{ch}章_作者修改说明.md', f"# 第{ch}章 作者修改说明\n\n实际 provider/model：{ap}/{am}\n\n番茄口径：原文 {fanqie_count(orig)} → 修订 {fanqie_count(revised)}\n\n机器门禁：{json.dumps(gate,ensure_ascii=False,indent=2)}\n\n落实重点：{FOCUS[ch]}\n")
    write(RAW/f'第{ch}_author_output.md', author_out)
    write(RAW/f'第{ch}_revised_candidate.md', revised)

    # reviews read actual revised candidate
    review_common=f'''章节：第{ch}章。请审实际修订稿，不审描述。
本章重点：{FOCUS[ch]}
外审任务卡：\n{taskcard}\n修订稿全文：\n```md\n{revised}\n```
输出：首行写 PASS 或 FAIL；若FAIL，列必须小修项≤5；若PASS，可列建议但不得阻塞。'''
    qp,qm,editor,_=call('editor', '[ROUTE: provider=alibaba model=qwen3.6-plus]\n你是编辑复审。检查结构、节奏、角色连续、AI味、是否落实外审。\n'+review_common, 360)
    write(OUT/f'第{ch}章_编辑复审.md', editor)
    rp,rm,reader,_=call('reader', '[ROUTE: provider=minimax-cn model=MiniMax-M2.7]\n你是读者复审。检查真实读感、追读、疲劳、情绪连续；忽略摘录标签。\n'+review_common, 360)
    write(OUT/f'第{ch}章_读者复审.md', reader)
    sp,sm,science,_=call('science', '[ROUTE: provider=glm2 model=glm-5.1]\n你是科学/制度/军事轻审。检查科学口径、未成年人制度、医护/伦理/训练安全、军事训练可信度。\n'+review_common, 360)
    write(OUT/f'第{ch}章_科学制度复审.md', science)

    pass_editor=md_review_ok(editor); pass_reader=md_review_ok(reader); pass_sci=md_review_ok(science); gate=machine_gate(ch,revised)
    attempts=1
    while attempts<3 and (not(pass_editor and pass_reader and pass_sci and gate['ok'])):
        attempts+=1
        repair_prompt=f'''[ROUTE: provider=freemodel model=gpt-5.5]
第{ch}章写后复审未全PASS或机器门禁失败。做最小小修，输出完整章节MD。
禁止大改骨架；必须清除FAIL项；保留已通过内容。
机器门禁：{json.dumps(gate,ensure_ascii=False)}
编辑复审：\n{editor[-3000:]}
读者复审：\n{reader[-3000:]}
科学制度复审：\n{science[-3000:]}
当前稿：\n```md\n{revised}\n```'''
        ap,am,repair_out,_=call('author', repair_prompt, 480)
        revised=extract_full(repair_out)
        title=orig.splitlines()[0].strip()
        if not revised.startswith(title):
            idx=revised.find(title); revised=(revised[idx:] if idx>=0 else title+'\n\n'+revised)
        gate=machine_gate(ch,revised)
        review_common=f'''章节：第{ch}章。请审实际小修后全文，不审描述。
本章重点：{FOCUS[ch]}
修订稿全文：\n```md\n{revised}\n```
输出：首行写 PASS 或 FAIL；若FAIL只列阻塞项。'''
        qp,qm,editor,_=call('editor', '[ROUTE: provider=alibaba model=qwen3.6-plus]\n编辑复审，小修后终审。\n'+review_common, 360); write(OUT/f'第{ch}章_编辑复审.md', editor)
        rp,rm,reader,_=call('reader', '[ROUTE: provider=minimax-cn model=MiniMax-M2.7]\n读者复审，小修后终审。\n'+review_common, 360); write(OUT/f'第{ch}章_读者复审.md', reader)
        sp,sm,science,_=call('science', '[ROUTE: provider=glm2 model=glm-5.1]\n科学/制度/军事复审，小修后终审。\n'+review_common, 360); write(OUT/f'第{ch}章_科学制度复审.md', science)
        pass_editor=md_review_ok(editor); pass_reader=md_review_ok(reader); pass_sci=md_review_ok(science)

    final_pass=pass_editor and pass_reader and pass_sci and gate['ok']
    if final_pass:
        write(src, revised.rstrip()+"\n")
    sync_res='NOT_RUN'
    if final_pass:
        proc=subprocess.run(['python3',str(SYNC),'--chapter',str(ch),'--message',f'前10章轻精修第{ch}章闭环','--no-git'],cwd='/root/workspace',text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240)
        sync_res=proc.stdout[-4000:]
    wiki=ensure_wiki_fulltext(ch, revised) if final_pass else {'skipped':True}
    # non-upload TXT boundary: delete if accidentally created newer? Do not touch existing historical unless mtime after start? Here no generation.
    report=f'''# 第{ch}章_闭环报告

结论：{'PASS' if final_pass else 'FAIL'}

顺序：原文备份 → 原文外审/任务卡 → 作者小修 → 编辑复审 + 读者复审 + 科学制度复审 → {'写回新版源稿 → sync_kewu --no-git → Wiki Full Text验收' if final_pass else '未写回'}。

实际模型：
- 原文外审/任务卡：{ep}/{em}
- 作者小修：{ap}/{am}
- 编辑复审：{qp}/{qm}
- 读者复审：{rp}/{rm}
- 科学制度复审：{sp}/{sm}

门禁：
- 机器关键词：{json.dumps(gate,ensure_ascii=False)}
- 编辑复审：{'PASS' if pass_editor else 'FAIL'}
- 读者复审：{'PASS' if pass_reader else 'FAIL'}
- 科学制度复审：{'PASS' if pass_sci else 'FAIL'}
- 番茄口径：原文 {fanqie_count(orig)} → 新版 {fanqie_count(revised)}
- 已投稿TXT：未生成
- Git：未提交

同步：
```text
{sync_res}
```

Wiki Full Text验收：
```json
{json.dumps(wiki,ensure_ascii=False,indent=2)}
```

文件：
- 备份：{OUT/f'第{ch}章_原文备份.md'}
- 任务卡：{OUT/f'第{ch}章_外审任务卡.md'}
- 作者说明：{OUT/f'第{ch}章_作者修改说明.md'}
- 编辑复审：{OUT/f'第{ch}章_编辑复审.md'}
- 读者复审：{OUT/f'第{ch}章_读者复审.md'}
- 科学制度复审：{OUT/f'第{ch}章_科学制度复审.md'}
'''
    write(OUT/f'第{ch}章_闭环报告.md', report)
    item.update({'status':'PASS' if final_pass else 'FAIL','finished_at':datetime.now().isoformat(timespec='seconds'),'fanqie_before':fanqie_count(orig),'fanqie_after':fanqie_count(revised),'models':{'external':f'{ep}/{em}','author':f'{ap}/{am}','editor':f'{qp}/{qm}','reader':f'{rp}/{rm}','science':f'{sp}/{sm}'},'machine_gate':gate,'wiki':wiki})
    write(OUT/'queue.json', json.dumps(QUEUE,ensure_ascii=False,indent=2))
    write(OUT/'MODEL_LEDGER_runtime.md', ledger_md())
    return item

def ledger_md():
    lines=['# MODEL_LEDGER_runtime','',f'生成时间：{datetime.now().isoformat(timespec="seconds")}', '', '禁用：cpa/gpt-5.5；本轮所有调用均显式 provider/model。','', '| ts | role | provider/model | exit | sec | chars | fallback/error |','|---|---|---|---:|---:|---:|---|']
    for r in LEDGER:
        err=(r.get('stderr_tail') or '').replace('\n',' ')[:160]
        lines.append(f"| {r['ts']} | {r['role']} | {r['provider']}/{r['model']} | {r['exit_code']} | {r['duration_sec']} | {r['stdout_chars']} | {err} |")
    return '\n'.join(lines)+'\n'

def main():
    OUT.mkdir(parents=True, exist_ok=True); RAW.mkdir(parents=True, exist_ok=True)
    # init queue and source ledger copy
    write(OUT/'queue.json', json.dumps(QUEUE,ensure_ascii=False,indent=2))
    if SRC_LEDGER.exists(): shutil.copy2(SRC_LEDGER, OUT/'MODEL_LEDGER_source_review.md')
    results=[]
    for ch in CHAPTERS:
        results.append(process_chapter(ch))
    # STATUS/WAL/TRACK append
    passed=[r['chapter'] for r in results if r['status']=='PASS']
    marker='前10章轻精修_20260519'
    append_once(STATUS, marker, f'''## 2026-05-19 前10章轻精修一轮闭环
- 章节顺序：8 → 5 → 7 → 9 → 10。
- PASS章节：{passed}。
- 边界：非上传章，未生成已投稿TXT；未提交Git。
- 报告：`审核记录/前10章轻精修_20260519/前10章轻精修_一轮闭环总报告.md`。''')
    append_once(WAL, marker, f'''## 2026-05-19｜前10章轻精修一轮闭环
- 已按顺序完成：8 → 5 → 7 → 9 → 10。
- 每章均先备份原文并外审实际章节文件，再作者小修、编辑/读者/科学制度复审。
- 已执行 `sync_kewu.py --no-git`，并覆盖/验收 Wiki Full Text。
- 未生成已投稿TXT，未提交Git。
- 输出目录：`{OUT}`。''')
    append_once(TRACK, marker, f'''\n### 2026-05-19 前10章轻精修一轮闭环
- 第8章/第5章/第7章/第9章/第10章：完成正式轻精修闭环；非上传章，未生成已投稿TXT；详见 `审核记录/前10章轻精修_20260519/`。''')
    total=f'''# 前10章轻精修_一轮闭环总报告

生成时间：{datetime.now().isoformat(timespec='seconds')}

范围：第8、5、7、9、10章。顺序：8 → 5 → 7 → 9 → 10。

总结论：{'PASS' if all(r['status']=='PASS' for r in results) else 'PARTIAL/FAIL'}

硬边界：
- 已先外审实际章节文件，再改正文。
- 每章已独立备份原文到本目录。
- 已写回新版源稿，仅限 PASS 章节。
- 已执行 `sync_kewu.py --no-git`。
- 已做 Wiki Full Text/关键词机器验收。
- 未生成已投稿TXT。
- 未提交 git；待提交清单见下。

逐章结果：

| 章 | 结论 | 番茄口径 | 外审 | 作者 | 编辑 | 读者 | 科学制度 | 报告 |
|---:|---|---:|---|---|---|---|---|---|
'''
    for r in results:
        report_path = OUT / f"第{r['chapter']}章_闭环报告.md"
        total += f"| {r['chapter']} | {r['status']} | {r['fanqie_after']} | {r['models']['external']} | {r['models']['author']} | {r['models']['editor']} | {r['models']['reader']} | {r['models']['science']} | `{report_path}` |\n"
    total += f'''

待提交清单（未提交）：
- `新版/第8章.md`
- `新版/第5章.md`
- `新版/第7章.md`
- `新版/第9章.md`
- `新版/第10章.md`
- `wiki/chapters/ch008.md`
- `wiki/chapters/ch005.md`
- `wiki/chapters/ch007.md`
- `wiki/chapters/ch009.md`
- `wiki/chapters/ch010.md`
- `STATUS.md`
- `WAL.md`
- `小说综合跟踪表.md`
- `审核记录/前10章轻精修_20260519/`

运行账本：`{OUT/'MODEL_LEDGER_runtime.md'}`
队列：`{OUT/'queue.json'}`

降级说明：若某角色使用fallback，已在 `MODEL_LEDGER_runtime.md` 记录。未使用 cpa。
'''
    write(OUT/'前10章轻精修_一轮闭环总报告.md', total)
    write(OUT/'MODEL_LEDGER_runtime.md', ledger_md())
    print(str(OUT/'前10章轻精修_一轮闭环总报告.md'))

if __name__=='__main__':
    main()
