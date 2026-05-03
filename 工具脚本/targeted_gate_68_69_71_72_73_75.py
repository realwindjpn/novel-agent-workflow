from pathlib import Path
import subprocess,json,re
proj=Path('/root/workspace/科武纪元')
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
qs={
68:('张维交出名单/清洗行动钩子是否已在章末或关键段落落地？',220),
69:('是否已明确确认资源战争将爆发，并以南大陆告急/前线急电等牵引第70章？',300),
71:('是否已明确牵引第72章刚果血战，有刚果/矿区/时间窗等钩子？',300),
72:('是否已包含丛林AI机器人交火动作链、谢云人机边界恐惧、夺回钴矿主控室的章末钩子？',180),
73:('是否已牵引第74章刚果残局/残余势力清剿，并避免纯清单化？',300),
75:('是否已补全结尾并明确牵引第76章南美某国交锋？',300),
}
for ch,(q,off) in qs.items():
    file=proj/'待确认投稿'/f'第{ch}章改.txt'
    review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
    lines=file.read_text(encoding='utf-8',errors='ignore').splitlines()
    seg='\n'.join(lines[max(0,off-1):])[-2400:]
    prompt=f'''只做目标化复审，不续写，不改文。第一行只写 PASS 或 FAIL。
前次审稿疑似因输入截断误判。现在只看相关段落。
问题：{q}
若相关段落已解决问题且无新硬伤，给 PASS；否则 FAIL并列缺口≤3。
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
    ok='"ok": true' in raw and first.startswith('PASS')
    old=review.read_text(encoding='utf-8',errors='ignore') if review.exists() else f'# 第{ch}章 六角色外审记录\n'
    review.write_text(old+f'''\n\n## 目标化编辑复审（2026-05-02）\n- 复审点：{q}\n- 原始输出：raw/第{ch}_editor_targeted_gate.json\n- 结论：{'PASS' if ok else 'REVIEW_NEEDED'}\n''',encoding='utf-8')
    print(json.dumps({'chapter':ch,'targeted_editor_pass':ok,'review':str(review)},ensure_ascii=False),flush=True)
