#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess, json, re, datetime
ROOT=Path('/root/workspace/科武纪元')
CH=ROOT/'待确认投稿'/'第1章改.txt'
OUT=ROOT/'审核记录'/'第一二卷格式修补'/'第1章改_六角色外审.md'
text=CH.read_text(encoding='utf-8',errors='ignore')
lines=[x.strip() for x in text.splitlines() if x.strip()]
first='\n'.join(lines[:35])
last='\n'.join(lines[-45:])
summary='第1章改：开篇。林星辰修屋顶光伏，发现异常电压；父亲林远三年前电站坠亡，日志留下47秒/12秒/三秒警告；现测得六秒脉冲，触碰日志后消失；学校推双轨教育，苏雨晴/武当进入；母亲透露父亲练过太极且说太极有线路；结尾林星辰按事实/推测/待查分类，准备测波形和观察武学课。目标：精品开篇，不掺水，主角立住，悬念成立。'
roles=[
 ('editor','角色: 编辑\n任务: 审第1章改结构/商业节奏/开篇钩子。\n输出: PASS或FAIL；必改≤5；小修≤5。\n禁止: 重写正文。'),
 ('reader','角色: 普通网文读者\n任务: 判断第1章是否想追读，是否有AI味/水字数。\n输出: PASS或FAIL；追读点；卡点≤5；水感≤3。\n禁止: 文学化长评。'),
 ('science','角色: 科学顾问\n任务: 审光伏/万用表/示波器/脉冲/数据思维是否可信，科普是否好懂。\n输出: PASS或FAIL；硬伤≤5；改法≤5。'),
]
reports=[]
for role,inst in roles:
    prompt=f"{inst}\n\n{summary}\n\n【首段】\n{first}\n\n【末段】\n{last}\n"
    cmd=['python3',str(ROOT/'工具脚本'/'orchestrate_review.py'),'--role',role,'--prompt',prompt]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=180,cwd='/root/workspace')
    reports.append({'role':role,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
now=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
md=[f'# 第1章改 六角色外审补审', '', f'时间：{now}', '', '## 调用说明', '- 主控/作者：gpt-5.5（已完成初改）', '- 编辑：qwen3.6-plus', '- 读者：MiniMax-M2.7', '- 科学顾问：mimo-v2.5', '- 军事顾问：本章无军事冲突，跳过', '']
for r in reports:
    md += [f"## {r['role']}", '', '```', r['stdout'] or '', r['stderr'] or '', '```', '']
OUT.write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'report':str(OUT),'roles':[r['role'] for r in reports],'ok':all(r['returncode']==0 for r in reports)},ensure_ascii=False))
