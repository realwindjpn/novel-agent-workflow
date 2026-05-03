import pathlib, subprocess
p = pathlib.Path('/root/workspace/科武纪元/待确认投稿/第53章改.txt')
t = p.read_text(encoding='utf-8')
head = t[:800]
tail = t[-1000:]
prompt = f'''角色: 普通网文读者
任务: 判断第53章修订后是否想继续看第54章
只看首尾与关键钩子。
输出: PASS/FAIL + 卡点≤3 + AI味≤3 + 是否想看下一章
禁止长评。
首段:
{head}
章末:
{tail}
'''
cmd = ['python3','/root/workspace/科武纪元/工具脚本/orchestrate_review.py','--role','reader','--prompt',prompt]
r = subprocess.run(cmd, cwd='/root/workspace', capture_output=True, text=True, timeout=240)
print(r.stdout)
print(r.stderr)
