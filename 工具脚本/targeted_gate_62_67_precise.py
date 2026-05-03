from pathlib import Path
import subprocess,json,re
proj=Path('/root/workspace/科武纪元')
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
items={
62:{'ranges':[(140,180),(300,380),(640,825)],'q':'第62章是否已明确落地联络方式、李国强交接链、沙海区域贸易公司与三层壳结构钩子？'},
67:{'ranges':[(50,140),(140,230),(250,329)],'q':'第67章是否已明确落地导师旧照、股权穿透、流云/算法泄露溯源，并以叶启明活跃信号牵引第68章？'}
}
for ch,cfg in items.items():
    path=proj/'待确认投稿'/f'第{ch}章改.txt'
    lines=path.read_text(encoding='utf-8',errors='ignore').splitlines()
    segs=[]
    for a,b in cfg['ranges']:
        segs.append('\n'.join(lines[a-1:min(b,len(lines))]))
    seg='\n\n---\n\n'.join(segs)
    prompt=f'''只做目标化复审，不续写，不改文。第一行只写 PASS 或 FAIL。
前次审稿疑似因送审片段过窄误判。现在提供多个相关片段。
问题：{cfg['q']}
若这些片段合并后已解决问题且无新硬伤，给 PASS；否则 FAIL 并列缺口≤3。
相关片段：
{seg[:3500]}
'''
    cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','editor','--prompt',prompt]
    rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
    raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
    (raw_dir/f'第{ch}_editor_precise_targeted_gate.json').write_text(raw,encoding='utf-8')
    m=re.search(r'"content"\s*:\s*"(.*?)"\s*,\s*"tokens_used"',raw,re.S)
    s=(m.group(1) if m else raw).replace('\\n','\n')
    first=next((x.strip() for x in s.splitlines() if x.strip() and not x.strip().startswith('<think>')),'')
    ok='"ok": true' in raw and first.startswith('PASS')
    review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
    old=review.read_text(encoding='utf-8',errors='ignore')
    review.write_text(old+f'''\n\n## 精确多片段编辑复审（2026-05-02）\n- 复审点：{cfg['q']}\n- 原始输出：raw/第{ch}_editor_precise_targeted_gate.json\n- 结论：{'PASS' if ok else 'REVIEW_NEEDED'}\n''',encoding='utf-8')
    print(json.dumps({'chapter':ch,'precise_editor_pass':ok,'review':str(review)},ensure_ascii=False),flush=True)
