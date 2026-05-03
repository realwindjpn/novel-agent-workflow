#!/usr/bin/env python3
from pathlib import Path
import subprocess,json
base=Path('/root/workspace/科武纪元')
s=(base/'新版/第233章.md').read_text(encoding='utf-8')
lines=s.splitlines()
excerpt='\n'.join(lines[:80]+['\n...[中段略]...\n']+lines[130:230]+['\n...[末段]...\n']+lines[-80:])
common=f"第233章修订后摘录:\n{excerpt[:1700]}"
prompts={
 'editor':'角色:编辑。任务:复审第233章是否完成供应链保卫收束、南天门认证闭环，并自然转向234归途坐标暗线。输出 PASS/FAIL；未解决≤3。\n'+common,
 'military':'角色:军事/安全顾问。任务:复审内部调查会、证据固定、仓库轮守、经侦衔接OPSEC是否可信。输出 PASS/FAIL；硬伤≤3。\n'+common,
 'reader':'角色:普通网文读者。任务:复审第233章是否想追234且不跳戏，归途暗线是否突兀。输出 PASS/FAIL；卡点≤3；AI味≤3。\n'+common,
}
out=[]
for role,prompt in prompts.items():
    r=subprocess.run(['python3',str(base/'工具脚本/orchestrate_review.py'),'--role',role,'--chapter','233','--prompt',prompt],capture_output=True,text=True,timeout=260)
    try:data=json.loads(r.stdout)
    except Exception:data={'role':role,'ok':False,'content':'BAD_JSON '+r.stdout[:500]+' ERR '+r.stderr[:300]}
    out.append(data); print(json.dumps(data,ensure_ascii=False)[:1300])
review_dir=base/'审核记录/六角色外审/tmp'; review_dir.mkdir(parents=True,exist_ok=True)
(review_dir/'第233章_recheck.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('RAW',review_dir/'第233章_recheck.json')
