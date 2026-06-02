#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""科武素材卡生成器包装脚本。
默认从 SenseNova 每日学习 report.md 提取“进入素材卡”条目，生成素材卡 Markdown。
"""
from pathlib import Path
import argparse,re,datetime,json
BASE=Path('/root/workspace/科武纪元')
DATE='2026-05-11'
REPORT=BASE/f'学习记录/SenseNova每日学习/{DATE}/report.md'
OUT=BASE/f'时事素材/素材卡/{DATE}'
SKIP={'NHS隐藏源代码争议','量子计算机分子模拟','量子计算分子模拟'}
URLS={
'RNA遗传与表观遗传':'https://www.newscientist.com/',
'可移动量子比特制造':'https://www.newscientist.com/',
'xAI与Anthropic合作':'https://techcrunch.com/',
'印度语音AI落地':'https://techcrunch.com/',
'光帆星际推进（Metajets）':'https://www.newscientist.com/',
'Deal Team Six采购队':'https://www.defensenews.com/'
}
TYPES={
'RNA遗传与表观遗传':'科学/生物/遗传',
'可移动量子比特制造':'科学/量子硬件',
'xAI与Anthropic合作':'产业/AI/算力壁垒',
'印度语音AI落地':'产业/AI/边缘计算',
'光帆星际推进（Metajets）':'科学/航天/推进',
'Deal Team Six采购队':'军事/制度/采购'
}
def safe(s):
 return re.sub(r'[\\/:*?"<>|\s]+','_',s).strip('_')
def parse(report):
 text=Path(report).read_text(encoding='utf-8')
 rows=[]
 for line in text.splitlines():
  if '| **' in line and '进入素材卡' in line:
   cols=[c.strip() for c in line.strip('|').split('|')]
   if len(cols)>=5:
    topic=cols[0].strip('* ')
    if topic not in SKIP:
     rows.append({'topic':topic,'trust':cols[1],'detail':cols[2],'mapping':cols[3],'advice':cols[4]})
 # 去重保序
 seen=set(); out=[]
 for r in rows:
  if r['topic'] not in seen:
   seen.add(r['topic']); out.append(r)
 return out
def card(r,date):
 topic=r['topic']
 return f'''# 素材卡：{topic}

日期：{date}
来源：{URLS.get(topic,'待补原文URL')}
类型：{TYPES.get(topic,'科学/时事/产业')}
可信度：secondary（SenseNova RSS映射；需原文复核后升 primary）

## 一句话
{r['detail']}，可映射到《科武纪元》{r['mapping']}。

## 关键事实
- 主题：{topic}。
- 可用细节：{r['detail']}。
- 当前映射：{r['mapping']}。
- 来源链：来自 2026-05-11 RSS/SenseNova 任务A筛选，后续正文使用前需补原文备份。

## 可用细节
- 把技术/制度后果落到可测指标、延迟、成本、权限、风险暴露。
- 场景里优先写操作界面、日志、合同、设备读数、失败回滚。

## 小说映射
- 可映射章节/卷：{r['mapping']}
- 对应变量：算法主权/算法暴力/群体智能/熵增/供应链/能源/太空/军事，按具体章节取用。
- 使用建议：先作为任务卡素材，不直接改正文；需要时补原文备份与硬事实。

## 小黑盒选题
- 标题方向：{topic}背后的现实约束。
- 玩家/普通人口吻切口：别只看概念，真正卡人的是成本、延迟、审计和失败责任。
- 可配图/引用：原文图表或公开机构资料，待补。

## 不可使用
- 不把RSS标题当完整事实。
- 不写超出原文的数字。
- 不与V8.9已闭环章节重复硬塞。
'''
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--input',default=str(REPORT))
 ap.add_argument('--output',default=str(OUT))
 ap.add_argument('--date',default=DATE)
 args=ap.parse_args()
 out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
 rows=parse(args.input)
 made=[]
 for r in rows:
  p=out/f"素材卡_{safe(r['topic'])}.md"
  p.write_text(card(r,args.date),encoding='utf-8')
  made.append(str(p))
 print(json.dumps({'count':len(made),'files':made},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
