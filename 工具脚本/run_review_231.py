#!/usr/bin/env python3
from pathlib import Path
import subprocess, json
base=Path('/root/workspace/科武纪元')
chapter=(base/'新版/第231章.md').read_text(encoding='utf-8')
context=(base/'审核记录/上下文包/第231章_context.md').read_text(encoding='utf-8')
# 控制输入长度：首尾+关键中段
lines=chapter.splitlines()
excerpt='\n'.join(lines[:90]+['\n...[中段略]...\n']+lines[120:210]+['\n...[末段]...\n']+lines[-60:])
common=f"上下文:\n{context[:900]}\n\n章节摘录:\n{excerpt[:1600]}"
prompts={
 'editor': '角色:编辑。任务:审第231章结构/大纲/商业节奏。输出 PASS/FAIL；必改≤5；小修≤3。禁止重写正文。\n'+common,
 'reader': '角色:普通网文读者。任务:判断第231章是否想追232且不跳戏。输出 PASS/FAIL；想追原因≤2；卡点≤3；AI味≤3。\n'+common,
 'military': '角色:军事/安全顾问。任务:审IT取证、VPN日志、现场调查安排是否可信。输出 PASS/FAIL；硬伤≤3；改法≤3。\n'+common,
 'science': '角色:科学/技术顾问。任务:审VPN日志、DHCP、IP、时间戳、调度日志交叉比对是否技术合理且读者能懂。输出 PASS/FAIL；硬伤≤3；读不懂≤3；改法≤3。\n'+common,
}
out=[]
for role,prompt in prompts.items():
    r=subprocess.run(['python3', str(base/'工具脚本/orchestrate_review.py'), '--role', role, '--chapter','231','--prompt', prompt], capture_output=True, text=True, timeout=260)
    try:
        data=json.loads(r.stdout)
    except Exception:
        data={'role':role,'ok':False,'content':'BAD_JSON '+r.stdout[:500]+' ERR '+r.stderr[:300]}
    out.append(data)
    print(json.dumps(data, ensure_ascii=False)[:1200])
review_dir=base/'审核记录/六角色外审/tmp'
review_dir.mkdir(parents=True, exist_ok=True)
(review_dir/'第231章_raw.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('RAW', review_dir/'第231章_raw.json')
