from pathlib import Path
import subprocess, json, sys, re
ch=int(sys.argv[1])
proj=Path('/root/workspace/科武纪元')
file=proj/'待确认投稿'/f'第{ch}章改.txt'
card=proj/'审核记录/任务卡'/f'第{ch}章.md'
review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
text=file.read_text(encoding='utf-8',errors='ignore')
ct=card.read_text(encoding='utf-8',errors='ignore') if card.exists() else ''
head=text[:700]; tail=text[-900:]
cn=len(re.findall(r'[\u4e00-\u9fff]',text))

def call(role, prompt):
    cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role',role,'--prompt',prompt]
    rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
    raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
    (raw_dir/f'第{ch}_{role}_gate_v2.json').write_text(raw,encoding='utf-8')
    return raw
base=f'''只做审核，不续写，不改文，不输出正文。
必须第一行只写 PASS 或 FAIL。
若有“必改/硬伤/不宜进入下一章”，第一行必须 FAIL。
第二行起：理由≤3条，小修≤3条。

任务卡摘录：
{ct[:900]}

正文首段：
{head}

正文章末：
{tail}
'''
ed=call('editor','角色: 网文编辑。查大纲/结构/钩子/投稿风险。'+base)
rd=call('reader','角色: 普通网文读者。查看懂/顺/爽/AI味/追读。'+base)
def ok(raw):
    if '"ok": true' not in raw: return False
    m=re.search(r'"content"\s*:\s*"(.*?)"\s*,\s*"tokens_used"',raw,re.S)
    s=m.group(1) if m else raw
    s=s.replace('\\n','\n')
    first=next((x.strip() for x in s.splitlines() if x.strip()),'')
    if not first.startswith('PASS'): return False
    bad=['FAIL','必改','硬伤','不宜进入下一章','不能进入下一章','重写']
    return not any(b in s for b in bad)
ep=ok(ed); rp=ok(rd); final=ep and rp and cn>=3000
append=f'''\n\n## V2硬格式复审\n- 编辑：{'PASS' if ep else 'REVIEW_NEEDED'}（raw/第{ch}_editor_gate_v2.json）\n- 读者：{'PASS' if rp else 'REVIEW_NEEDED'}（raw/第{ch}_reader_gate_v2.json）\n\n## 最终结论\n{'PASS' if final else 'REVIEW_NEEDED'}\n'''
old=review.read_text(encoding='utf-8',errors='ignore') if review.exists() else ''
review.write_text(old+append,encoding='utf-8')
print(json.dumps({'chapter':ch,'chars':cn,'editor_pass':ep,'reader_pass':rp,'final_pass':final,'review':str(review)},ensure_ascii=False))
