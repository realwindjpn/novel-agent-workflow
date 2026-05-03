from pathlib import Path
import subprocess,json,re
proj=Path('/root/workspace/科武纪元')
path=proj/'待确认投稿/第75章改.txt'
review=proj/'审核记录/六角色外审/第75章.md'
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
lines=path.read_text(encoding='utf-8',errors='ignore').splitlines()
seg='\n'.join(lines[-110:])
prompt=f'''只做目标化复审，不续写，不改文。第一行只写 PASS 或 FAIL。
问题：第75章是否已完成战斗收束、获得权限箱/证据链，并以第76号站/无人单位接管/资源战升级牵引第76章？
若已解决且无新硬伤，给 PASS；否则 FAIL并列缺口≤3。
最后110行：
{seg}
'''
cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','editor','--prompt',prompt]
rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
(raw_dir/'第75_editor_final_tail_gate.json').write_text(raw,encoding='utf-8')
m=re.search(r'"content"\s*:\s*"(.*?)"\s*,\s*"tokens_used"',raw,re.S)
s=(m.group(1) if m else raw).replace('\\n','\n')
first=next((x.strip() for x in s.splitlines() if x.strip() and not x.strip().startswith('<think>')),'')
ok='"ok": true' in raw and first.startswith('PASS')
old=review.read_text(encoding='utf-8',errors='ignore')
review.write_text(old+f'''\n\n## 第75章最终尾段编辑复审（2026-05-02）\n- 修正：删除“丹田算力”，改为缺氧+外骨骼液压超频。\n- 原始输出：raw/第75_editor_final_tail_gate.json\n- 结论：{'PASS' if ok else 'REVIEW_NEEDED'}\n\n## 最终结论修正\n{'PASS' if ok else 'REVIEW_NEEDED'}\n''',encoding='utf-8')
print(json.dumps({'chapter':75,'editor_final_pass':ok,'review':str(review)},ensure_ascii=False))
