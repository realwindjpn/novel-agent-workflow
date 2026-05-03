#!/usr/bin/env python3
from pathlib import Path
import subprocess,json
base=Path('/root/workspace/科武纪元')
s=(base/'新版/第231章.md').read_text(encoding='utf-8')
lines=s.splitlines()
excerpt='\n'.join(lines[45:70]+['\n...[取证中段省略]...\n']+lines[289:])
prompt='角色:编辑。任务:最终复审第231章章末行动指令与时间空窗。已知前置取证流程合格。只判断：时间空窗是否解释；产线/供应链是否缝合；章末是否有明确行动指令。输出 PASS/FAIL；若FAIL列具体未解决。\n'+excerpt
r=subprocess.run(['python3',str(base/'工具脚本/orchestrate_review.py'),'--role','editor','--chapter','231','--prompt',prompt],capture_output=True,text=True,timeout=260)
try:data=json.loads(r.stdout)
except Exception:data={'role':'editor','ok':False,'content':'BAD_JSON '+r.stdout[:500]+' ERR '+r.stderr[:300]}
print(json.dumps(data,ensure_ascii=False,indent=2))
(base/'审核记录/六角色外审/tmp/第231章_editor_recheck_end.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
