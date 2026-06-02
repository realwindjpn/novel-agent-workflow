#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大纲同步包装脚本。
当前 V8.9 大纲主同步已由 sync_kewu.py/闭环报告完成。本脚本用于生成一次可追溯同步检查报告。
"""
from pathlib import Path
import argparse,datetime,json,re
BASE=Path('/root/workspace/科武纪元')
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--version',default='V8.9')
 ap.add_argument('--target',default='wiki/raw/outline/')
 args=ap.parse_args()
 target=BASE/args.target
 latest=target/'科武纪元大纲_latest.md'
 out=BASE/'审核记录'/f'{args.version.replace(".","")}_大纲同步检查_{datetime.datetime.now():%Y%m%d_%H%M%S}.md'
 text=latest.read_text(encoding='utf-8') if latest.exists() else ''
 keys=['V8.9','MATCH','人在环上','先存后解','量子通信护盾','第184章','第220章','第306章','第381章']
 lines=[f'# {args.version} 大纲同步检查', '', f'- 时间：{datetime.datetime.now():%Y-%m-%d %H:%M:%S}', f'- target：`{target}`', f'- latest：`{latest}`', '', '## 关键词']
 for k in keys: lines.append(f'- {k}: {k in text}')
 lines += ['', '## 结论', '- 本脚本为包装入口；实质同步以 `审核记录/V89闭环验收_20260510.md` 与后续逐章闭环报告为准。']
 out.write_text('\n'.join(lines),encoding='utf-8')
 print(json.dumps({'report':str(out),'latest_exists':latest.exists()},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
