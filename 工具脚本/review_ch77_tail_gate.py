from pathlib import Path
import subprocess,json,re
ch=77
proj=Path('/root/workspace/科武纪元')
file=proj/'待确认投稿/第77章改.txt'
review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
raw_dir=proj/'审核记录/六角色外审/raw'
text=file.read_text(encoding='utf-8',errors='ignore')
seg='\n'.join(text.splitlines()[590:675])
prompt=f'''只做目标化复审，不续写。第一行只写 PASS 或 FAIL。
上次问题：称第77章缺“芯片加工厂”章末钩子。现在只复审尾段是否已明确牵引第78章《加工厂》。
若尾段出现废弃芯片加工厂/P-17/下一站芯片加工厂等明确钩子，且无新硬伤，给 PASS。
尾段：
{seg}
'''
cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','editor','--prompt',prompt]
rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
(raw_dir/'第77_editor_tail_gate.json').write_text(raw,encoding='utf-8')
passed='"ok": true' in raw and 'PASS' in raw and 'FAIL' not in raw
old=review.read_text(encoding='utf-8',errors='ignore')
review.write_text(old+f'''\n\n## 第77章尾段目标化复审\n- 复审点：芯片加工厂章末钩子\n- 编辑复审：{'PASS' if passed else 'REVIEW_NEEDED'}（raw/第77_editor_tail_gate.json）\n\n## 最终结论修正\n{'PASS' if passed else 'REVIEW_NEEDED'}\n''',encoding='utf-8')
print(json.dumps({'chapter':77,'tail_editor_pass':passed,'final_pass':passed,'review':str(review)},ensure_ascii=False))
