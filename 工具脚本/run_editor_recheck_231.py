#!/usr/bin/env python3
from pathlib import Path
import subprocess,json
base=Path('/root/workspace/科武纪元')
s=(base/'新版/第231章.md').read_text(encoding='utf-8')
lines=s.splitlines()
# 特意保留开头取证、产线时间锁、章末指令三段
excerpt='\n'.join(lines[30:150]+['\n...[中段略]...\n']+lines[285:]+['\n...[结尾已完整]'])
prompt='角色:编辑。任务:二次复审第231章。只看三点是否解决：1时间空窗 2实体产线/供应链断点 3章末行动指令。输出 PASS/FAIL；若FAIL列未解决≤3。禁止要求重写。\n'+excerpt[:2800]
r=subprocess.run(['python3',str(base/'工具脚本/orchestrate_review.py'),'--role','editor','--chapter','231','--prompt',prompt],capture_output=True,text=True,timeout=260)
try:data=json.loads(r.stdout)
except Exception:data={'role':'editor','ok':False,'content':'BAD_JSON '+r.stdout[:500]+' ERR '+r.stderr[:300]}
print(json.dumps(data,ensure_ascii=False,indent=2))
(base/'审核记录/六角色外审/tmp/第231章_editor_recheck2.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
