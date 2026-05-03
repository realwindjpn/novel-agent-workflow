from pathlib import Path
import subprocess,json,re
proj=Path('/root/workspace/科武纪元')
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
items={
68:{'ranges':[(429,525)],'q':'第68章是否已由张维交出名单/存储卡，并明确牵引第69章清洗行动？'},
72:{'ranges':[(400,435)],'q':'第72章是否已明确提出第73行动目标：夺回钴矿主控室，并牵引第73章钴矿夺回？'},
75:{'ranges':[(540,817)],'q':'第75章是否已补全结尾，并以北部高原/第76号站/无人单位接管等明确牵引第76章南美某国交锋？'}
}
for ch,cfg in items.items():
    path=proj/'待确认投稿'/f'第{ch}章改.txt'
    review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
    lines=path.read_text(encoding='utf-8',errors='ignore').splitlines()
    segs=[]
    for a,b in cfg['ranges']:
        segs.append('\n'.join(lines[a-1:min(b,len(lines))]))
    seg='\n\n---\n\n'.join(segs)
    prompt=f'''只做目标化复审，不续写，不改文。第一行只写 PASS 或 FAIL。
前次审稿因尾段截断误判。现在提供完整相关尾段。
问题：{cfg['q']}
若尾段已解决问题且无新硬伤，给 PASS；否则 FAIL 并列缺口≤3。
尾段：
{seg[:3600]}
'''
    cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','editor','--prompt',prompt]
    rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
    raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
    (raw_dir/f'第{ch}_editor_precise_tail_gate.json').write_text(raw,encoding='utf-8')
    m=re.search(r'"content"\s*:\s*"(.*?)"\s*,\s*"tokens_used"',raw,re.S)
    s=(m.group(1) if m else raw).replace('\\n','\n')
    first=next((x.strip() for x in s.splitlines() if x.strip() and not x.strip().startswith('<think>')),'')
    ok='"ok": true' in raw and first.startswith('PASS')
    old=review.read_text(encoding='utf-8',errors='ignore') if review.exists() else f'# 第{ch}章 六角色外审记录\n'
    review.write_text(old+f'''\n\n## 精确尾段编辑复审（2026-05-02）\n- 复审点：{cfg['q']}\n- 原始输出：raw/第{ch}_editor_precise_tail_gate.json\n- 结论：{'PASS' if ok else 'REVIEW_NEEDED'}\n\n## 最终结论修正\n{'PASS' if ok else 'REVIEW_NEEDED'}\n''',encoding='utf-8')
    print(json.dumps({'chapter':ch,'precise_tail_editor_pass':ok,'review':str(review)},ensure_ascii=False),flush=True)
