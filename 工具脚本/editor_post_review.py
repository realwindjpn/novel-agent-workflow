from pathlib import Path
import subprocess, json, re, sys
ch=int(sys.argv[1])
proj=Path('/root/workspace/科武纪元')
file=proj/'待确认投稿'/f'第{ch}章改.txt'
card=proj/'审核记录/任务卡'/f'第{ch}章.md'
review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
text=file.read_text(encoding='utf-8',errors='ignore')
card_text=card.read_text(encoding='utf-8',errors='ignore') if card.exists() else ''
head=text[:900]; tail=text[-1100:]
prompt=f'''角色: 网文编辑
任务: 写后审核第{ch}章是否符合任务卡、V8锚点、结构节奏、章末钩子、投稿风险。
输出必须含英文 PASS 或 FAIL。
若有“必改/硬伤/不宜进入下一章”，判 FAIL。
必改≤3，小修≤3。

任务卡:
{card_text[:900]}

首段:
{head}

章末:
{tail}
'''
cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','editor','--prompt',prompt]
rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
(raw_dir/f'第{ch}_editor_post.json').write_text(raw,encoding='utf-8')
low=raw.lower()
ok='"ok": true' in raw and 'PASS' in raw and 'FAIL' not in raw
bad_words=['必改','硬伤','不宜进入下一章','不能进入下一章','重写']
if any(w in raw for w in bad_words):
    ok=False
append=f'''

## 编辑后审补录
模型：editor / orchestrate_review
原始输出：`raw/第{ch}_editor_post.json`
结论：{'PASS' if ok else 'REVIEW_NEEDED'}

## 双门禁结论
编辑：{'PASS' if ok else 'REVIEW_NEEDED'}
读者：见原记录
最终：{'PASS' if ok else 'REVIEW_NEEDED'}
'''
old=review.read_text(encoding='utf-8',errors='ignore') if review.exists() else ''
if '## 编辑后审补录' not in old:
    review.write_text(old.rstrip()+append+'\n',encoding='utf-8')
print(json.dumps({'chapter':ch,'editor_pass':ok,'raw':str(raw_dir/f'第{ch}_editor_post.json'),'review':str(review)},ensure_ascii=False))
