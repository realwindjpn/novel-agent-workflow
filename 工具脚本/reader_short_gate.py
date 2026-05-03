from pathlib import Path
import subprocess,json,re,sys
ch=int(sys.argv[1])
proj=Path('/root/workspace/科武纪元')
file=proj/'待确认投稿'/f'第{ch}章改.txt'
review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
text=file.read_text(encoding='utf-8',errors='ignore')
lines=text.splitlines()
# reader needs enough story: first 80 + last 120, but hard output short.
seg='\n'.join(lines[:80])+'\n---TAIL---\n'+'\n'.join(lines[-130:])
prompt=f'''只做读者门禁。严禁思考过程，严禁英文解释。
第一行必须只写 PASS 或 FAIL。
第二行：看懂/顺/爽/AI味/追读，各用一个词。
第三行：卡点≤2；无则写无。

正文片段：
{seg[:5200]}
'''
cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','reader','--prompt',prompt]
rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
(raw_dir/f'第{ch}_reader_short_gate.json').write_text(raw,encoding='utf-8')
m=re.search(r'"content"\s*:\s*"(.*?)"\s*,\s*"tokens_used"',raw,re.S)
s=(m.group(1) if m else raw).replace('\\n','\n')
s=re.sub(r'<think>.*?</think>','',s,flags=re.S).strip()
first=next((x.strip() for x in s.splitlines() if x.strip()),'')
ok='"ok": true' in raw and first.startswith('PASS')
old=review.read_text(encoding='utf-8',errors='ignore') if review.exists() else f'# 第{ch}章 六角色外审记录\n'
review.write_text(old+f'''\n\n## 读者短评门禁（2026-05-02）\n- 原始输出：raw/第{ch}_reader_short_gate.json\n- 结论：{'PASS' if ok else 'REVIEW_NEEDED'}\n''',encoding='utf-8')
print(json.dumps({'chapter':ch,'reader_short_pass':ok,'review':str(review)},ensure_ascii=False))
