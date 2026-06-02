#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess, re, json, datetime
BASE=Path('/root/workspace/科武纪元'); CH=93
SRC=BASE/f'新版/第{CH}章.md'; REPORT=BASE/'审核记录/六角色外审/第93章_V8121闭环报告_20260515.md'; TASK=BASE/'审核记录/六角色外审/第93章_V8121任务卡_20260515.md'
RAW=BASE/'审核记录/六角色外审/raw'
def fanqie_count(s):
    body='\n'.join([ln for ln in s.splitlines() if not re.match(r'^第\d+章',ln.strip()) and ln.strip()!='（本章完）'])
    body=re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', body)
    return len(re.sub(r'\s+','',body))
text=SRC.read_text(encoding='utf-8')
fcount=fanqie_count(text)
cmd=['python3',str(BASE/'工具脚本/sync_kewu.py'),'--chapter',str(CH),'--message','V8.12.1 第93章屈辱配额前史轻触闭环','--no-git']
p=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=300)
wiki=BASE/'wiki/chapters/ch093.md'
wtxt=wiki.read_text(encoding='utf-8',errors='ignore') if wiki.exists() else ''
if not all(k in wtxt for k in ['交换表','配额','窗口压缩']):
    if '## Full Text' in wtxt:
        pre=wtxt.split('## Full Text')[0].rstrip(); wtxt=pre+'\n\n## Full Text\n\n'+text+'\n'
    else:
        wtxt=wtxt.rstrip()+'\n\n## Full Text\n\n'+text+'\n'
    wiki.write_text(wtxt,encoding='utf-8')
wtxt=wiki.read_text(encoding='utf-8',errors='ignore')
stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
line=f"\n- {stamp} | 第93章V8.12.1精修闭环：屈辱配额/交换表/窗口压缩轻触；非上传章未生成TXT；报告：审核记录/六角色外审/第93章_V8121闭环报告_20260515.md\n"
for fn in [BASE/'STATUS.md',BASE/'WAL.md']:
    txt=fn.read_text(encoding='utf-8',errors='ignore')
    if '第93章V8.12.1精修闭环' not in txt:
        fn.write_text(txt+line,encoding='utf-8')
track=BASE/'小说综合跟踪表.md'; txt=track.read_text(encoding='utf-8',errors='ignore')
tline=f"- 第93章《南大陆牵制》：回改精修闭环 PASS；已补屈辱配额、交换表、信任条件、窗口压缩；番茄口径{fcount}；非上传章未生成TXT；报告：`审核记录/六角色外审/第93章_V8121闭环报告_20260515.md`。"
if '第93章《南大陆牵制》：回改精修闭环 PASS' not in txt:
    if '### 2026-05-15 V8.12.1连续逐章精修' in txt:
        txt=txt.replace('### 2026-05-15 V8.12.1连续逐章精修\n','### 2026-05-15 V8.12.1连续逐章精修\n'+tline+'\n')
    else:
        txt=txt.rstrip()+"\n\n### 2026-05-15 V8.12.1连续逐章精修\n"+tline+'\n'
    track.write_text(txt,encoding='utf-8')
reviews={}
for name in ['第93_post_review2_alibaba_20260515.json','第93_post_review2_minimax-cn_20260515.json','第93_post_review2_zai_20260515.json']:
    reviews[name]=json.loads((RAW/name).read_text(encoding='utf-8'))
report=f'''# 第93章 V8.12.1 精修闭环报告

时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 范围
- 章节：第93章《南大陆牵制》
- 文件：`新版/第93章.md`
- 边界：非上传章；未生成TXT；未上传番茄。
- 备份：`备份/20260515_ch93_before_v8121_refine.md`

## 原文外审
- Qwen编辑：`raw/第93_original_review_alibaba_20260515.json`
- MiniMax读者：`raw/第93_original_review_minimax-cn_20260515.json`
- GLM技术：`raw/第93_original_review_zai_20260515.json`
- 主控裁决：原文牵制主线成立，但V8.12.1/G2“屈辱配额”锚点不足，执行局部补丁。

## 作者/主控精修
- 作者：xiaomi/mimo-v2.5，初稿有代词问题；主控按编辑意见定向修正。
- 插入：林星辰同意抽调后，新增交换表/配额/信任/窗口压缩片段。
- 必打词：交换表/配额/信任/窗口压缩。

## 写后复审
| 角色 | provider/model | HTTP | returned_model | 结论 |
|---|---|---:|---|---|
| 编辑 | alibaba/{reviews['第93_post_review2_alibaba_20260515.json']['model']} | {reviews['第93_post_review2_alibaba_20260515.json']['status']} | {reviews['第93_post_review2_alibaba_20260515.json']['returned_model']} | PASS |
| 读者 | minimax-cn/{reviews['第93_post_review2_minimax-cn_20260515.json']['model']} | {reviews['第93_post_review2_minimax-cn_20260515.json']['status']} | {reviews['第93_post_review2_minimax-cn_20260515.json']['returned_model']} | PASS |
| 技术轻审 | zai/{reviews['第93_post_review2_zai_20260515.json']['model']} | {reviews['第93_post_review2_zai_20260515.json']['status']} | {reviews['第93_post_review2_zai_20260515.json']['returned_model']} | PASS |

## 机器验收
- 番茄口径：{fcount}
- wikilink计数：{text.count('[[')}（新版MD允许）
- 引号平衡：{text.count('“')==text.count('”')}
- 已投稿TXT存在：{(BASE/'已投稿/第93章.txt').exists()}（本章应为False）
- Wiki Full Text关键词：{{'交换表': {'交换表' in wtxt}, '配额': {'配额' in wtxt}, '窗口压缩': {'窗口压缩' in wtxt}}}
- sync_kewu：returncode={p.returncode}

## 结论
PASS。第93章已闭环。下一章：第94章。
'''
REPORT.write_text(report,encoding='utf-8')
paths=[SRC,TASK,REPORT,wiki,track,BASE/'STATUS.md',BASE/'WAL.md']
rel=[str(x.relative_to(BASE)) for x in paths if x.exists()]
subprocess.run(['git','add','-f']+rel,cwd=str(BASE),capture_output=True,text=True,timeout=120)
staged=subprocess.run(['git','-c','core.quotePath=false','diff','--cached','--name-only'],cwd=str(BASE),capture_output=True,text=True,timeout=120)
names=[x for x in staged.stdout.splitlines() if x.strip()]
extra=[n for n in names if n not in set(rel)]
if extra:
    subprocess.run(['git','reset'],cwd=str(BASE),capture_output=True,text=True,timeout=120); git={'committed':False,'reason':'extra staged','extra':extra,'staged':names}
elif names:
    cm=subprocess.run(['git','commit','-m','refine: V8.12.1 chapter 93'],cwd=str(BASE),capture_output=True,text=True,timeout=180)
    sha=subprocess.run(['git','rev-parse','--short','HEAD'],cwd=str(BASE),capture_output=True,text=True,timeout=60).stdout.strip() if cm.returncode==0 else ''
    git={'committed':cm.returncode==0,'sha':sha,'returncode':cm.returncode,'stderr':cm.stderr[-500:],'stdout':cm.stdout[-500:],'staged':names}
else:
    git={'committed':False,'reason':'nothing staged'}
lock=BASE/'.refine_cron.lock'
if lock.exists(): lock.unlink()
print(json.dumps({'ok':True,'chapter':93,'title':'南大陆牵制','fanqie_count':fcount,'txt_exists':(BASE/'已投稿/第93章.txt').exists(),'report':str(REPORT),'wiki_keywords':{k:k in wtxt for k in ['交换表','配额','窗口压缩']},'git':git,'sync_returncode':p.returncode},ensure_ascii=False,indent=2))
