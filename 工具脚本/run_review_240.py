#!/usr/bin/env python3
from pathlib import Path
import subprocess,json
base=Path('/root/workspace/科武纪元')
chapter=(base/'新版/第240章.md').read_text(encoding='utf-8')
context=(base/'审核记录/上下文包/第240章_context.md').read_text(encoding='utf-8')
lines=chapter.splitlines()
excerpt='\n'.join(lines[:90]+['\n...[中段略]...\n']+lines[90:135])
common=f"上下文:\n{context[:800]}\n\n第240章摘录:\n{excerpt[:1700]}"
prompts={
 'editor':'角色:编辑。任务:审第240章结构/大纲对齐/商业节奏。234-244归途坐标暗线区间。输出 PASS/FAIL；必改≤5；小修≤3。\n'+common,
 'reader':'角色:普通网文读者。任务:判断第240章是否想追241且不跳戏。输出 PASS/FAIL；想追原因≤2；卡点≤3；AI味≤3。\n'+common,
 'science':'角色:技术/取证顾问。任务:审APK逆向/DNS隧道/DGA/APK混淆/Base64解码/蜜罐思路是否合理可懂。输出 PASS/FAIL；硬伤≤3；读不懂≤3；改法≤3。\n'+common,
 'military':'角色:安全顾问。任务:审安全屋选择/APK逆向隔离环境/蜜罐搭建/离线操作OPSEC是否可信。输出 PASS/FAIL；硬伤≤3；改法≤3。\n'+common,
}
out=[]
for role,prompt in prompts.items():
    r=subprocess.run(['python3',str(base/'工具脚本/orchestrate_review.py'),'--role',role,'--chapter','240','--prompt',prompt],capture_output=True,text=True,timeout=260)
    try:data=json.loads(r.stdout)
    except Exception:data={'role':role,'ok':False,'content':'BAD_JSON '+r.stdout[:500]+' ERR '+r.stderr[:300]}
    out.append(data); print(json.dumps(data,ensure_ascii=False)[:1300])
review_dir=base/'审核记录/六角色外审/tmp'; review_dir.mkdir(parents=True,exist_ok=True)
(review_dir/'第240章_raw.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('RAW',review_dir/'第240章_raw.json')
