#!/usr/bin/env python3
from pathlib import Path
import subprocess,json
base=Path('/root/workspace/科武纪元')
s=(base/'新版/第241章.md').read_text(encoding='utf-8')
lines=s.splitlines()
excerpt='\n'.join(lines[:60]+['\n...[中段]...\n']+lines[60:140]+['\n...[末段]...\n']+lines[-50:])
common=f"第241章修订后摘录:\n{excerpt[:1800]}"
prompts={
 'editor':'角色:编辑。复审第241章:1编译矛盾已改为解压预编译2暗线/主线已补3蜜罐功能已揭示。PASS/FAIL；未解决≤3。\n'+common,
 'science':'角色:技术顾问。复审第241章:改用WiFi热点+DNS欺骗而非蜂窝TX发射。树莓派开热点，手机连WiFi，DNS指向树莓派。PASS/FAIL；硬伤≤3。\n'+common,
}
out=[]
for role,prompt in prompts.items():
    r=subprocess.run(['python3',str(base/'工具脚本/orchestrate_review.py'),'--role',role,'--chapter','241','--prompt',prompt],capture_output=True,text=True,timeout=260)
    try:data=json.loads(r.stdout)
    except Exception:data={'role':role,'ok':False,'content':'BAD_JSON '+r.stdout[:500]+' ERR '+r.stderr[:300]}
    out.append(data); print(json.dumps(data,ensure_ascii=False)[:1300])
review_dir=base/'审核记录/六角色外审/tmp'; review_dir.mkdir(parents=True,exist_ok=True)
(review_dir/'第241章_recheck2.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('RAW',review_dir/'第241章_recheck2.json')
