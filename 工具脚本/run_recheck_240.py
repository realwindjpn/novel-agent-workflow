#!/usr/bin/env python3
from pathlib import Path
import subprocess,json
base=Path('/root/workspace/科武纪元')
s=(base/'新版/第240章.md').read_text(encoding='utf-8')
lines=s.splitlines()
# focus on security/OPSEC parts
excerpt='\n'.join(lines[1:20]+['\n...[逆向中段]...\n']+lines[120:])
common=f"第240章修订后摘录:\n{excerpt[:1700]}"
prompts={
 'editor':'角色:编辑。任务:复审第240章是否已解决:1安全屋入场承接239章2章末行动指令3地球危机绑定。输出 PASS/FAIL；未解决≤3。\n'+common,
 'military':'角色:安全顾问。任务:复审第240章OPSEC。已新增:进屋TSCM扫窃听/拆手机电池/树莓派模拟蜂窝蜜罐。输出 PASS/FAIL；硬伤≤3。\n'+common,
}
out=[]
for role,prompt in prompts.items():
    r=subprocess.run(['python3',str(base/'工具脚本/orchestrate_review.py'),'--role',role,'--chapter','240','--prompt',prompt],capture_output=True,text=True,timeout=260)
    try:data=json.loads(r.stdout)
    except Exception:data={'role':role,'ok':False,'content':'BAD_JSON '+r.stdout[:500]+' ERR '+r.stderr[:300]}
    out.append(data); print(json.dumps(data,ensure_ascii=False)[:1300])
review_dir=base/'审核记录/六角色外审/tmp'; review_dir.mkdir(parents=True,exist_ok=True)
(review_dir/'第240章_recheck.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('RAW',review_dir/'第240章_recheck.json')
