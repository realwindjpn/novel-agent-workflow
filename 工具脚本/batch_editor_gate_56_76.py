from pathlib import Path
import subprocess, json, re, sys
proj=Path('/root/workspace/科武纪元')
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
results=[]
for ch in range(56,77):
    file=proj/'待确认投稿'/f'第{ch}章改.txt'
    review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
    card=proj/'审核记录/任务卡'/f'第{ch}章.md'
    if not file.exists():
        results.append({'chapter':ch,'status':'missing_file'}); continue
    text=file.read_text(encoding='utf-8',errors='ignore')
    ct=card.read_text(encoding='utf-8',errors='ignore') if card.exists() else ''
    head=text[:700]; tail=text[-1000:]
    cn=len(re.findall(r'[\u4e00-\u9fff]',text))
    prompt=f'''只做编辑后审，不续写，不改文。
第一行只写 PASS 或 FAIL。
若有偏纲/结构硬伤/章末无钩子/投稿风险/必改，第一行必须 FAIL。
第二行起：理由≤3条，小修≤3条。

章节：第{ch}章
任务卡摘录：
{ct[:900]}

正文首段：
{head}

正文章末：
{tail}
'''
    cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','editor','--prompt',prompt]
    try:
        rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
        raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
    except Exception as e:
        raw='EXCEPTION '+repr(e)
    raw_path=raw_dir/f'第{ch}_editor_backfill_gate.json'
    raw_path.write_text(raw,encoding='utf-8')
    m=re.search(r'"content"\s*:\s*"(.*?)"\s*,\s*"tokens_used"',raw,re.S)
    s=(m.group(1) if m else raw).replace('\\n','\n')
    first=next((x.strip() for x in s.splitlines() if x.strip() and not x.strip().startswith('<think>')),'')
    ok='"ok": true' in raw and first.startswith('PASS') and not any(w in s for w in ['硬伤','必改','不宜进入下一章','不能进入下一章','重写'])
    append=f'''\n\n## 编辑后审补录（2026-05-02）\n- 模型：qwen3.6-plus / editor\n- 原始输出：raw/第{ch}_editor_backfill_gate.json\n- 结论：{'PASS' if ok else 'REVIEW_NEEDED'}\n'''
    old=review.read_text(encoding='utf-8',errors='ignore') if review.exists() else f'# 第{ch}章 六角色外审记录\n'
    review.write_text(old+append,encoding='utf-8')
    results.append({'chapter':ch,'chars':cn,'editor_pass':ok,'review':str(review)})
    print(json.dumps(results[-1],ensure_ascii=False), flush=True)
print('SUMMARY '+json.dumps(results,ensure_ascii=False))
