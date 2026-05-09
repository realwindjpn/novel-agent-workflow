#!/usr/bin/env python3
"""科武纪元修改闭环检查：正文/大纲修改后，复核 Wiki/RAG/跟踪/状态是否同步。"""
from pathlib import Path
import argparse, json, re, sys

BASE = Path('/root/workspace/科武纪元')

def exists(p):
    return Path(p).exists()

def read(p):
    return Path(p).read_text(encoding='utf-8', errors='ignore') if Path(p).exists() else ''

def check_chapter(ch:int):
    res=[]
    src=BASE/'新版'/f'第{ch}章.md'
    wiki=BASE/'wiki/chapters'/f'ch{ch:03d}.md'
    review=BASE/'审核记录/六角色外审'/f'第{ch}章.md'
    memory=BASE/'审核记录/章节记忆卡'/f'第{ch}章.md'
    evidence=BASE/'审核记录/证据包'/f'第{ch}章_证据包.md'
    kgfile=BASE/'wiki/kg'/f'ch{ch:03d}_20260508_sync.json'
    txt_dirs=[BASE/f'待上传TXT_73_74_20260508', BASE/'已投稿']
    res.append(('正文存在', src.exists(), str(src)))
    wt=read(wiki)
    res.append(('Wiki章节页存在', wiki.exists(), str(wiki)))
    res.append(('Wiki更新时间含2026-05-08', 'updated: 2026-05-08' in wt, str(wiki)))
    res.append(('Wiki含章节功能', '## Chapter Function' in wt and 'TODO' not in wt[:800], str(wiki)))
    if review.exists():
        res.append(('六角色记录存在', True, str(review)))
    if memory.exists():
        res.append(('章节记忆卡存在', True, str(memory)))
    if evidence.exists():
        res.append(('证据包存在', True, str(evidence)))
    res.append(('KG同步文件存在', kgfile.exists(), str(kgfile)))
    for d in txt_dirs:
        p=d/f'第{ch}章.txt'
        if p.exists():
            t=read(p)
            res.append((f'TXT无wikilink:{p}', '[[' not in t and ']]' not in t, str(p)))
    return res

def check_v86():
    files=[
        BASE/'科武纪元大纲 V8_完整版.md',
        BASE/'wiki/raw/outline/科武纪元大纲V8.6_20260508.md',
        BASE/'wiki/plot-threads/v8.6-current-events.md',
        BASE/'wiki/kg/ch000_20260508_sync.json',
        BASE/'wiki/kg/relations.md',
        BASE/'wiki/concepts/chaos-model.md',
        BASE/'小说综合跟踪表.md',
        BASE/'STATUS.md',
        BASE/'WAL.md',
        BASE/'rag_kb/science/cards/science_cards.jsonl',
        BASE/'rag_kb/science/index/index_meta.json',
    ]
    keys=['国产算力训练主权','地月规则竞赛','军事AI蜂群','量子先存后解']
    res=[]
    for p in files:
        res.append((f'文件存在:{p.name}', p.exists(), str(p)))
    for key in keys:
        hits=[]
        for p in files:
            if p.exists() and key in read(p): hits.append(str(p))
        res.append((f'关键词同步:{key}', bool(hits), ', '.join(hits[:3])))
    return res

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--chapters', default='')
    ap.add_argument('--v86', action='store_true')
    args=ap.parse_args()
    allres=[]
    if args.chapters:
        for part in args.chapters.split(','):
            part=part.strip()
            if '-' in part:
                a,b=map(int,part.split('-',1))
                nums=range(a,b+1)
            else:
                nums=[int(part)]
            for ch in nums:
                allres += [(f'第{ch}章::{name}', ok, detail) for name,ok,detail in check_chapter(ch)]
    if args.v86:
        allres += [(f'V8.6::{name}', ok, detail) for name,ok,detail in check_v86()]
    bad=[x for x in allres if not x[1]]
    for name,ok,detail in allres:
        print(('PASS' if ok else 'FAIL')+'\t'+name+'\t'+detail)
    print(json.dumps({'total':len(allres),'fail':len(bad)},ensure_ascii=False))
    sys.exit(1 if bad else 0)
if __name__=='__main__': main()
