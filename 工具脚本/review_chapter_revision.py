#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess, json, datetime, argparse, re
ROOT=Path('/root/workspace/科武纪元')
ap=argparse.ArgumentParser()
ap.add_argument('chapter', type=int)
ap.add_argument('--military', action='store_true')
args=ap.parse_args()
n=args.chapter
CH=ROOT/'待确认投稿'/f'第{n}章改.txt'
OUT=ROOT/'审核记录'/'第一二卷格式修补'/f'第{n}章改_六角色外审.md'
text=CH.read_text(encoding='utf-8',errors='ignore')
lines=[x.strip() for x in text.splitlines() if x.strip()]
first='\n'.join(lines[:45])
last='\n'.join(lines[-55:])
cn=len(re.findall(r'[\u4e00-\u9fff]', text))
summary=f'第{n}章改：已投稿改版候选。目标：精品小说质量，不掺水；主角立住，节奏有效，章节钩子成立。字数{cn}。'
roles=[
 ('editor','角色: 编辑\n任务: 审本章结构/商业节奏/章节功能/钩子。\n输出: PASS或FAIL；必改≤5；小修≤5。\n禁止: 重写正文。'),
 ('reader','角色: 普通网文读者\n任务: 判断是否想追读，是否有AI味/水字数。\n输出: PASS或FAIL；追读点；卡点≤5；水感≤3。\n禁止: 文学化长评。'),
 ('science','角色: 科学顾问\n任务: 审技术/科学/数据设定是否可信，科普是否好懂。\n输出: PASS或FAIL；硬伤≤5；改法≤5。'),
]
if args.military:
    roles.append(('military','角色: 军事顾问\n任务: 审战术/装备/组织逻辑是否可信。\n输出: PASS或FAIL；硬伤≤5；改法≤5。'))
reports=[]
for role,inst in roles:
    prompt=f"{inst}\n\n{summary}\n\n【首段】\n{first}\n\n【末段】\n{last}\n"
    cmd=['python3',str(ROOT/'工具脚本'/'orchestrate_review.py'),'--role',role,'--prompt',prompt]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=180,cwd='/root/workspace')
    reports.append({'role':role,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
now=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
md=[f'# 第{n}章改 六角色外审', '', f'时间：{now}', '', '## 调用说明', '- 主控/作者：gpt-5.5', '- 编辑：qwen3.6-plus', '- 读者：MiniMax-M2.7', '- 科学顾问：mimo-v2.5', ('- 军事顾问：GLM-5.1' if args.military else '- 军事顾问：本章无军事冲突，跳过'), '']
for r in reports:
    md += [f"## {r['role']}", '', '```', r['stdout'] or '', r['stderr'] or '', '```', '']
OUT.write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'report':str(OUT),'roles':[r['role'] for r in reports],'ok':all(r['returncode']==0 for r in reports)},ensure_ascii=False))
