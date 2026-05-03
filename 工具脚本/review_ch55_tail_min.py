import pathlib, subprocess
p=pathlib.Path('/root/workspace/科武纪元/待确认投稿/第55章改.txt')
t=p.read_text(encoding='utf-8')
tail=t[-850:]
prompt=f'''角色: 编辑
任务: 判断章末钩子是否过关
输出: PASS/FAIL + 原因≤3
片段:
{tail}
'''
cmd=['python3','/root/workspace/科武纪元/工具脚本/orchestrate_review.py','--role','editor','--prompt',prompt]
r=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
print(r.stdout)
print(r.stderr)
