from pathlib import Path
import subprocess,json,re
proj=Path('/root/workspace/科武纪元')
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
checks={
62:{'offset':640,'question':'第62章是否已明确落地李国强交接链、联络方式、沙海区域贸易公司、三层壳结构章末钩子？'},
63:{'offset':350,'question':'第63章尾段是否已明确落地方宁工程生态判断、频道隔离、暗线追踪和章末钩子？'},
66:{'offset':320,'question':'第66章尾段是否已缝合海上拦截到数据室分析，并明确牵引第67章海外名校往事？'},
67:{'offset':250,'question':'第67章尾段是否已落地导师旧照、股权穿透、流云/算法泄露溯源，并以叶启明活跃信号牵引第68章间谍网络？'}
}
for ch,cfg in checks.items():
    file=proj/'待确认投稿'/f'第{ch}章改.txt'
    review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
    lines=file.read_text(encoding='utf-8',errors='ignore').splitlines()
    seg='\n'.join(lines[max(0,cfg['offset']-1):])[-1800:]
    prompt=f'''只做目标化复审，不续写，不改文。第一行只写 PASS 或 FAIL。
前次审稿疑似因输入截断误判。现在只看以下相关段落。
问题：{cfg['question']}
若相关段落已解决该问题且无新硬伤，给 PASS；否则 FAIL并列缺口≤3。
相关段落：
{seg}
'''
    cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','editor','--prompt',prompt]
    rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
    raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
    (raw_dir/f'第{ch}_editor_targeted_gate.json').write_text(raw,encoding='utf-8')
    m=re.search(r'"content"\s*:\s*"(.*?)"\s*,\s*"tokens_used"',raw,re.S)
    s=(m.group(1) if m else raw).replace('\\n','\n')
    first=next((x.strip() for x in s.splitlines() if x.strip() and not x.strip().startswith('<think>')),'')
    ok='"ok": true' in raw and first.startswith('PASS') and 'FAIL' not in first
    old=review.read_text(encoding='utf-8',errors='ignore') if review.exists() else f'# 第{ch}章 六角色外审记录\n'
    review.write_text(old+f'''\n\n## 目标化编辑复审（2026-05-02）\n- 复审点：{cfg['question']}\n- 原始输出：raw/第{ch}_editor_targeted_gate.json\n- 结论：{'PASS' if ok else 'REVIEW_NEEDED'}\n''',encoding='utf-8')
    print(json.dumps({'chapter':ch,'targeted_editor_pass':ok,'review':str(review)},ensure_ascii=False),flush=True)
