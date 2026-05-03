from pathlib import Path
import subprocess,json,re
proj=Path('/root/workspace/科武纪元')
path=proj/'待确认投稿/第67章改.txt'
review=proj/'审核记录/六角色外审/第67章.md'
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
text=path.read_text(encoding='utf-8',errors='ignore')
lines=text.splitlines()
seg='\n'.join(lines[280:329])
prompt=f'''只做目标化复审，不续写，不改文。第一行只写 PASS 或 FAIL。
问题：第67章章末是否已明确出现“叶启明活跃信号”，并牵引第68章间谍网络？
若片段已出现叶启明活跃信号/上线/追他等明确钩子，给 PASS。
尾段：
{seg}
'''
cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','editor','--prompt',prompt]
rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
(raw_dir/'第67_editor_tail_yqm_gate.json').write_text(raw,encoding='utf-8')
m=re.search(r'"content"\s*:\s*"(.*?)"\s*,\s*"tokens_used"',raw,re.S)
s=(m.group(1) if m else raw).replace('\\n','\n')
first=next((x.strip() for x in s.splitlines() if x.strip() and not x.strip().startswith('<think>')),'')
ok='"ok": true' in raw and first.startswith('PASS')
old=review.read_text(encoding='utf-8',errors='ignore')
review.write_text(old+f'''\n\n## 叶启明尾钩目标化编辑复审（2026-05-02）\n- 复审点：叶启明活跃信号是否牵引第68章\n- 原始输出：raw/第67_editor_tail_yqm_gate.json\n- 结论：{'PASS' if ok else 'REVIEW_NEEDED'}\n\n## 最终结论修正\n{'PASS' if ok else 'REVIEW_NEEDED'}\n''',encoding='utf-8')
print(json.dumps({'chapter':67,'tail_yqm_pass':ok,'review':str(review)},ensure_ascii=False))
