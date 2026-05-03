#!/usr/bin/env python3
from pathlib import Path
import subprocess, json
base=Path('/root/workspace/科武纪元')
chapter=(base/'新版/第231章.md').read_text(encoding='utf-8')
lines=chapter.splitlines()
excerpt='\n'.join(lines[:120]+['\n...[中段略]...\n']+lines[120:260]+['\n...[末段]...\n']+lines[-80:])
common=f"第231章修订后摘录:\n{excerpt[:1700]}"
prompts={
 'editor': '角色:编辑。任务:复审第231章是否已修复结构拖沓、产线/供应链断点、时间锁、章末行动指令。输出 PASS/FAIL；未解决必改≤3。\n'+common,
 'military': '角色:军事/安全顾问。任务:复审第231章IT取证/VPN日志/证据链是否可信。重点看哈希、封签、只读导出、管理员审计、DHCP租约+MAC+主机名。输出 PASS/FAIL；硬伤≤3。\n'+common,
 'science': '角色:科学/技术顾问。任务:复审VPN、DHCP、MAC、主机名、时间戳、调度日志交叉比对是否合理可懂。输出 PASS/FAIL；硬伤≤3；读不懂≤3。\n'+common,
}
out=[]
for role,prompt in prompts.items():
    r=subprocess.run(['python3', str(base/'工具脚本/orchestrate_review.py'), '--role', role, '--chapter','231','--prompt', prompt], capture_output=True, text=True, timeout=260)
    try: data=json.loads(r.stdout)
    except Exception: data={'role':role,'ok':False,'content':'BAD_JSON '+r.stdout[:500]+' ERR '+r.stderr[:300]}
    out.append(data)
    print(json.dumps(data, ensure_ascii=False)[:1400])
review_dir=base/'审核记录/六角色外审/tmp'
(review_dir/'第231章_recheck.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('RAW', review_dir/'第231章_recheck.json')
