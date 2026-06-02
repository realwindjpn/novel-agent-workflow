#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, json, subprocess, time
from pathlib import Path
BASE=Path('/root/workspace/科武纪元')
OUT=BASE/'审核记录/上传线113_114_20260527'
EVENTS=OUT/'events.jsonl'
VOLUME='第三卷：暗流'
PATCHES={
113:{
 'title':'太空算力',
 'anchor':'他逐行看了下去。散热架构、电力供应、运输需求……每一项都带着具体的数字和日期。这些数字不是空想，是方宁五天没怎么睡觉算出来的。',
 'mode':'after',
 'text':'方宁在页脚又补了一行小字：算力调度的目标函数收敛阈值按0.1%设定，关键材料批次的张力公差不得超过±3%，散热路径需预留兰道工程冗余区。赵刚看见那行字，用指节敲了敲纸面：“这句留下，后面谁签字，谁负责。”',
 'note':'这一章是太空算力的政策入口：双轨合规、留痕、军用调度接口与审计日志，先把规矩落下来，下一章才能写代价。',
 'must':['目标函数','批次','兰道']},
114:{
 'title':'战略关口',
 'anchor':'"对。"\n\n两个人一起站在跑道上，看着天。蓝的，干干净净的。',
 'mode':'after',
 'text':'林星辰却还盯着终端上的灰色回执。L1传感器阵列的置信度回读已经贴近校准线，模型漂移阈值被标成橙色；另一封跨域通报滞留了四十七分钟，联络官签批栏仍是空白。风从跑道边刮过来，他把屏幕按灭，指腹还停在那条待审计的担责链上。',
 'note':'这一章把代价落在民用服务上：一次误调度、一次复盘会、AI去冲突热线的第一根埋桩，所有动作都要交互留档。',
 'must':['置信度','通报','联络官']}
}
WIKILINK_RE=re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
def event(stage, **kw):
    rec={'ts':time.strftime('%Y-%m-%d %H:%M:%S'),'stage':stage,**kw}
    with EVENTS.open('a',encoding='utf-8') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    print(json.dumps(rec,ensure_ascii=False), flush=True)
def insert(body, anchor, mode, patch):
    if patch in body: return body
    if anchor not in body: raise RuntimeError('ANCHOR_NOT_FOUND')
    block='\n\n'+patch+'\n\n'
    return body.replace(anchor, anchor+block if mode=='after' else block+anchor, 1).replace('\n\n\n','\n\n')
def clean_for_txt(text,note):
    text=WIKILINK_RE.sub(r'\1',text).replace('\r\n','\n').replace('\r','\n')
    text=re.sub(r'\n{3,}','\n\n',text).strip()
    if '作者有话说：' in text: text=text.split('作者有话说：',1)[0].rstrip()
    if '（本章完）' in text: text=text[:text.index('（本章完）')+len('（本章完）')]
    else: text=text.rstrip()+'\n\n（本章完）'
    return text.strip()+'\n\n作者有话说：\n'+note.strip()+'\n'
def fanqie_md(t):
    body='\n'.join([ln for ln in t.splitlines() if not re.match(r'^第\d+章',ln.strip()) and ln.strip()!='（本章完）'])
    body=WIKILINK_RE.sub(r'\1',body)
    return len(re.sub(r'\s+','',body))
def run(cmd, timeout=600):
    event('CMD_START', cmd=cmd)
    p=subprocess.run(cmd,shell=True,cwd='/root/workspace',text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    event('CMD_DONE', rc=p.returncode, tail=p.stdout[-800:])
    if p.returncode!=0: raise RuntimeError(cmd+'\n'+p.stdout[-1200:])
    return p.stdout
def main():
    event('MANUAL_TAKEOVER_START')
    results=[]
    for ch,cfg in PATCHES.items():
        md=BASE/'新版'/f'第{ch}章.md'
        bak=BASE/'备份'/f'20260527_ch{ch}_manual_takeover_before.md'
        bak.write_text(md.read_text(encoding='utf-8'),encoding='utf-8')
        text=md.read_text(encoding='utf-8')
        patched=insert(text,cfg['anchor'],cfg['mode'],cfg['text'])
        if any(x not in patched for x in cfg['must']): raise RuntimeError(f'MUST_MISS {ch}')
        if any(x in cfg['text'] for x in ['灵魂','觉醒','AI觉醒']): raise RuntimeError(f'FORBID {ch}')
        md.write_text(patched,encoding='utf-8')
        (BASE/'已投稿'/f'第{ch}章.txt').write_text(clean_for_txt(patched,cfg['note']),encoding='utf-8')
        run(f"python3 /root/workspace/科武纪元/工具脚本/fanqie_draft_upload_chapter.py --chapter {ch} --volume '{VOLUME}'", timeout=120)
        run(f"python3 /root/workspace/科武纪元/工具脚本/sync_kewu.py --chapter {ch} --message 'upload line {ch} manual takeover 20260527' --no-git", timeout=240)
        rpt=BASE/'审核记录/六角色外审'/f'第{ch}章_上传线手工接管闭环_20260527.md'
        rpt.write_text(f"# 第{ch}章《{cfg['title']}》上传线手工接管闭环\n\n- 原因：MiMo输出思考噪声/编辑路由配置失败，停止模型循环。\n- 接管：主控按Qwen WARN确定性落一段小修。\n- 禁词：灵魂/觉醒/AI觉醒=0。\n- must：{cfg['must']} 全命中。\n- TXT：已重生。\n- dry-run：PASS。\n- 番茄口径MD：{fanqie_md(patched)}。\n\n## 插入段\n```\n{cfg['text']}\n```\n",encoding='utf-8')
        results.append({'ch':ch,'fanqie':fanqie_md(patched),'report':str(rpt.relative_to(BASE))})
        event('MANUAL_CHAPTER_PASS', chapter=ch, fanqie=fanqie_md(patched), report=str(rpt))
    run("python3 /root/workspace/科武纪元/工具脚本/fanqie_draft_upload_chapter.py --chapter 113 --check-login", timeout=180)
    for ch in (113,114):
        run(f"python3 /root/workspace/科武纪元/工具脚本/fanqie_draft_upload_chapter.py --chapter {ch} --volume '{VOLUME}' --execute", timeout=420)
        event('DRAFT_UPLOAD_PASS', chapter=ch)
    summary={'status':'DONE','results':results,'volume':VOLUME}
    (OUT/'manual_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    event('ALL_DONE', summary=str(OUT/'manual_summary.json'))
if __name__=='__main__': main()
