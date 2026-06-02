#!/usr/bin/env python3
import importlib.util, pathlib, re, json, datetime, subprocess
BASE=pathlib.Path('/root/workspace/科武纪元')
runner_path=BASE/'工具脚本'/'run_stage1_262_265_queue_20260526.py'
spec=importlib.util.spec_from_file_location('runner', runner_path)
r=importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
ch=265
src=BASE/'新版'/f'第{ch}章.md'
text=src.read_text(encoding='utf-8')
# Strip model meta: keep the real chapter from the last/second chapter title onward, then first 本章完.
title_pat=rf'# 第{ch}章[^\n]*'
ms=list(re.finditer(title_pat, text))
if ms:
    start=ms[-1].start() if len(ms)>1 else ms[0].start()
    text=text[start:]
end=text.find('（本章完）')
if end!=-1:
    text=text[:end+len('（本章完）')]+'\n'
# Mechanical banned-word cleanup, no creative rewrite.
repls={
    '非线性耦合意味着——':'非线性耦合会带来——',
    '意味着':'会带来',
    '缓缓':'慢慢',
    '意识到':'判断出',
}
for a,b in repls.items(): text=text.replace(a,b)
# Normalize duplicate title/end just in case.
title_line=re.search(title_pat, text).group(0)
text=r.normalize_full(ch, title_line.split(' ',1)[1] if ' ' in title_line else title_line.replace(f'# 第{ch}章','').strip(), text)
src.write_text(text,encoding='utf-8')
problems,cnt=r.machine_gate(ch,text)
if problems:
    print(json.dumps({'status':'BLOCKED','problems':problems,'count':cnt},ensure_ascii=False)); raise SystemExit(1)
r.event(ch,'LOCAL_RECOVER_GATE_PASS','RUNNING',f'local cleanup pass count={cnt}')
# Run reviews with existing routes.
card=(BASE/'审核记录'/'六角色外审'/f'第{ch}章_写前任务卡_20260526.md').read_text(encoding='utf-8')
model_logs=[]
editor,elogs=r.review('编辑写后复审',r.EDITOR_ROUTES,ch,text,card); model_logs.extend(elogs)
reader,rlogs=r.review('读者写后复审',r.READER_ROUTES,ch,text,card); model_logs.extend(rlogs)
advisor,alogs=r.review('科学/军事顾问轻审',r.ADVISOR_ROUTES,ch,text,card); model_logs.extend(alogs)
if not (r.pass_review(editor['stdout']) and r.pass_review(reader['stdout'])):
    r.event(ch,'RECOVER_REVIEW_BLOCKED','FAILED','editor/reader not PASS',{'fail_reason':'review not pass','next_action':'manual review'})
    print(json.dumps({'status':'REVIEW_BLOCKED','editor':editor['stdout'][:500],'reader':reader['stdout'][:500]},ensure_ascii=False)); raise SystemExit(2)
report_path=BASE/'审核记录'/'六角色外审'/f'第{ch}章_闭环报告_20260526.md'
routes_md='\n'.join([f"- {x['requested_provider']}/{x['requested_model']} exit={x['exit_code']} dur={x['duration']}s session={x.get('session_id','')} fail={x.get('fail_reason','')}" for x in model_logs])
report_path.write_text(f"""# 第{ch}章 闭环报告

时间：{r.now()}
章节：第{ch}章
结论：FULL_LOOP_PASS

## 修复说明
- 修复脚本误把模型修复说明写入正文的问题。
- 清除模型元信息、重复标题、重复（本章完）。
- 机械替换残留禁词，不改剧情骨架。

## 门禁
- 番茄口径：{cnt}
- 禁词：0
- wikilink：0
- 首行/末尾：PASS
- 非上传章：未生成已投稿TXT，未上传番茄

## 模型调用记录
{routes_md}

## 编辑复审
{editor['stdout']}

## 读者复审
{reader['stdout']}

## 顾问轻审
{advisor['stdout']}
""",encoding='utf-8')
r.append_status_wal(ch,'兰道启示【第六层·拓域】',cnt,report_path)
r.event(ch,'PROJECT_SYNC','RUNNING','sync/wiki/status/wal/git after local recovery')
sync,staged,commit,sha=r.sync_and_commit(ch)
# Update queue item even if commit has nothing to commit.
q=r.loadq(); q['stage']='DONE'; q['current_chapter']=ch; q['current_stage']='FULL_LOOP_PASS'
for item in q.get('chapters',[]):
    if item.get('chapter')==ch:
        item.update({'status':'FULL_LOOP_PASS','report_path':str(report_path),'git_commit':sha or item.get('git_commit',''),'fail_reason':'','next_action':'stage1 complete','updated_at':r.now(),'fanqie_count':cnt})
r.saveq(q)
r.event(ch,'FULL_LOOP_PASS','FULL_LOOP_PASS','chapter recovered and completed',{'report_path':str(report_path),'git_commit':sha,'next_action':'stage1 complete'})
r.final_report([{'chapter':262,'status':'FULL_LOOP_PASS'},{'chapter':263,'status':'FULL_LOOP_PASS'},{'chapter':264,'status':'FULL_LOOP_PASS'},{'chapter':265,'status':'FULL_LOOP_PASS','count':cnt,'report':str(report_path),'commit':sha}])
print(json.dumps({'status':'FULL_LOOP_PASS','count':cnt,'report':str(report_path),'commit':sha,'sync_exit':sync['exit_code'],'commit_exit':commit['exit_code']},ensure_ascii=False))
