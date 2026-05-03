from pathlib import Path
import subprocess,json,re,sys
ch=int(sys.argv[1])
proj=Path('/root/workspace/科武纪元')
file=proj/'待确认投稿'/f'第{ch}章改.txt'
review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
text=file.read_text(encoding='utf-8',errors='ignore')
lines=text.splitlines()
seg='\n'.join(lines[:80])+'\n---TAIL---\n'+'\n'.join(lines[-130:])
prompt=f'''角色: 普通网文读者
任务: 只判读感，不续写。
格式必须三行：
PASS或FAIL
看懂=好/差；顺=好/差；爽=好/差；AI味=低/中/高；追读=想/不想
卡点: 无 或 ≤2条
禁止输出思考过程。
正文片段:
{seg[:5200]}
'''
cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','editor','--prompt',prompt]
rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
(raw_dir/f'第{ch}_reader_short_qwen_gate.json').write_text(raw,encoding='utf-8')
m=re.search(r'"content"\s*:\s*"(.*?)"\s*,\s*"tokens_used"',raw,re.S)
s=(m.group(1) if m else raw).replace('\\n','\n')
s=re.sub(r'<think>.*?</think>','',s,flags=re.S).strip()
first=next((x.strip() for x in s.splitlines() if x.strip()),'')
ok='"ok": true' in raw and first.startswith('PASS')
old=review.read_text(encoding='utf-8',errors='ignore') if review.exists() else f'# 第{ch}章 六角色外审记录\n'
review.write_text(old+f'''\n\n## 读者短评门禁-Qwen补审（2026-05-02）\n- 原始输出：raw/第{ch}_reader_short_qwen_gate.json\n- 结论：{'PASS' if ok else 'REVIEW_NEEDED'}\n''',encoding='utf-8')
print(json.dumps({'chapter':ch,'reader_short_qwen_pass':ok,'review':str(review)},ensure_ascii=False))
