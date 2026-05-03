#!/usr/bin/env python3
from pathlib import Path
import subprocess,json
base=Path('/root/workspace/科武纪元')
s=(base/'新版/第241章.md').read_text(encoding='utf-8')
lines=s.splitlines()
excerpt='\n'.join(lines[1:30]+['\n...[中段]...\n']+lines[30:130]+['\n...[末段]...\n']+lines[-50:])
common=f"第241章修订后摘录:\n{excerpt[:1800]}"
prompts={
 'editor':'角色:编辑。任务:复审第241章是否已解决:1暗线显性化2压缩技术流水3蜜罐标题功能4主线压力背景。输出 PASS/FAIL；未解决≤3。\n'+common,
 'military':'角色:安全顾问。任务:复审第241章SDR已改为HackRF One(支持TX)/预编译镜像/离线操作。输出 PASS/FAIL；硬伤≤3。\n'+common,
 'science':'角色:技术顾问。任务:复审HackRF One+srsRAN做伪基站蜜罐是否可行。输出 PASS/FAIL；硬伤≤3。\n'+common,
}
out=[]
for role,prompt in prompts.items():
    r=subprocess.run(['python3',str(base/'工具脚本/orchestrate_review.py'),'--role',role,'--chapter','241','--prompt',prompt],capture_output=True,text=True,timeout=260)
    try:data=json.loads(r.stdout)
    except Exception:data={'role':role,'ok':False,'content':'BAD_JSON '+r.stdout[:500]+' ERR '+r.stderr[:300]}
    out.append(data); print(json.dumps(data,ensure_ascii=False)[:1300])
review_dir=base/'审核记录/六角色外审/tmp'; review_dir.mkdir(parents=True,exist_ok=True)
(review_dir/'第241章_recheck.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('RAW',review_dir/'第241章_recheck.json')
