#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""旧章比对包装脚本。
按章节列表调用现有番茄线上/本地只读对比脚本，抽取目标章节生成差异表。
"""
from pathlib import Path
import argparse,subprocess,json,csv,re,shutil,datetime
BASE=Path('/root/workspace/科武纪元')
COMPARE=BASE/'工具脚本/fanqie_compare_online_vs_local.py'
def expand(s):
 out=[]
 for part in s.split(','):
  part=part.strip()
  if '-' in part:
   a,b=map(int,part.split('-',1)); out.extend(range(a,b+1))
  elif part: out.append(int(part))
 return sorted(set(out))
def latest_report_dir():
 root=BASE/'审核记录/线上正文对比'
 ds=[p for p in root.glob('*') if p.is_dir()]
 return max(ds,key=lambda p:p.stat().st_mtime) if ds else None
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--chapters',required=True)
 ap.add_argument('--output',default=str(BASE/'待修改'))
 args=ap.parse_args()
 chapters=expand(args.chapters); outdir=Path(args.output); outdir.mkdir(parents=True,exist_ok=True)
 # 当前底层脚本只支持连续区间，先跑min-max，后抽目标章节
 subprocess.run(['python3',str(COMPARE),'--start',str(min(chapters)),'--end',str(max(chapters))],cwd='/root/workspace',check=False)
 d=latest_report_dir(); rows=[]
 if d:
  csvs=sorted(d.glob('compare_*_*.csv'))
  if csvs:
   with csvs[0].open(encoding='utf-8') as f:
    for r in csv.DictReader(f):
     if int(r.get('chapter',0)) in chapters: rows.append(r)
 md=outdir/'旧章差异表_20260511.md'
 lines=['# 旧章差异表 2026-05-11','',f'- 章节：{args.chapters}',f'- 来源报告：`{d}`' if d else '- 来源报告：未生成','- 方法：番茄线上修改页正文 vs 本地已投稿TXT，去空白SHA对比。','- 未调用大模型。','','## 仍需处理']
 diffs=[r for r in rows if r.get('status')!='same']
 lines.append('、'.join(f"第{r['chapter']}章" for r in diffs) if diffs else '无。')
 lines += ['','## 明细','|章|状态|相似度|本地字数|线上字数|首处差异|','|---:|---|---:|---:|---:|---|']
 for r in rows:
  fd=(r.get('first_diff') or '').replace('\n','<br>').replace('|','｜')[:240]
  sim=r.get('similarity','')
  lines.append(f"|{r.get('chapter')}|{r.get('status')}|{sim}|{r.get('local_chars_compact','')}|{r.get('online_chars_compact','')}|{fd}|")
 md.write_text('\n'.join(lines),encoding='utf-8')
 print(json.dumps({'output':str(md),'chapters':chapters,'diffs':[int(r['chapter']) for r in diffs]},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
