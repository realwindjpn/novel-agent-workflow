from pathlib import Path
import subprocess
p=Path('/root/workspace/科武纪元/待确认投稿/第63章改.txt')
t=p.read_text(encoding='utf-8')
head=t[:500]
tail=t[-700:]
prompt=f'''角色: 普通网文读者
任务: 给第63章读者门禁结论。必须输出英文 PASS 或 FAIL。
只判断: 看懂? 顺? 有无追读?
首段:
{head}
章末:
{tail}
'''
cmd=['python3','/root/workspace/科武纪元/工具脚本/orchestrate_review.py','--role','reader','--prompt',prompt]
r=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
print(r.stdout)
print(r.stderr)
