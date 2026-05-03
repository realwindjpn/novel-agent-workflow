#!/usr/bin/env python3
from pathlib import Path
import subprocess,json
base=Path('/root/workspace/科武纪元')
chapter=(base/'新版/第233章.md').read_text(encoding='utf-8')
context=(base/'审核记录/上下文包/第233章_context.md').read_text(encoding='utf-8')
lines=chapter.splitlines()
excerpt='\n'.join(lines[:90]+['\n...[中段略]...\n']+lines[90:190]+['\n...[末段]...\n']+lines[-60:])
common=f"上下文:\n{context[:800]}\n\n第233章摘录:\n{excerpt[:1700]}"
prompts={
 'editor':'角色:编辑。任务:审第233章是否完成223-233供应链保卫小段收束，并自然转向234-244归途坐标暗线。输出 PASS/FAIL；必改≤5；小修≤3。\n'+common,
 'reader':'角色:普通网文读者。任务:判断第233章是否想追234且不跳戏。输出 PASS/FAIL；想追原因≤2；卡点≤3；AI味≤3。\n'+common,
 'military':'角色:军事/安全顾问。任务:审内部调查会、证据固定、仓库轮守、经侦衔接是否可信。输出 PASS/FAIL；硬伤≤3；改法≤3。\n'+common,
 'science':'角色:技术/取证顾问。任务:审IP/MAC/VPN/哈希/证据链/资产台账/物流定位是否合理可懂。输出 PASS/FAIL；硬伤≤3；读不懂≤3；改法≤3。\n'+common,
}
out=[]
for role,prompt in prompts.items():
    r=subprocess.run(['python3',str(base/'工具脚本/orchestrate_review.py'),'--role',role,'--chapter','233','--prompt',prompt],capture_output=True,text=True,timeout=260)
    try:data=json.loads(r.stdout)
    except Exception:data={'role':role,'ok':False,'content':'BAD_JSON '+r.stdout[:500]+' ERR '+r.stderr[:300]}
    out.append(data); print(json.dumps(data,ensure_ascii=False)[:1300])
review_dir=base/'审核记录/六角色外审/tmp'; review_dir.mkdir(parents=True,exist_ok=True)
(review_dir/'第233章_raw.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('RAW',review_dir/'第233章_raw.json')
