import pathlib, subprocess
p=pathlib.Path('/root/workspace/科武纪元/待确认投稿/第55章改.txt')
t=p.read_text(encoding='utf-8')
head=t[:750]
tail=t[-850:]
tech=t[:1000] + '\n---\n' + t[2500:3400]

def run(role,prompt):
    cmd=['python3','/root/workspace/科武纪元/工具脚本/orchestrate_review.py','--role',role,'--prompt',prompt]
    r=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
    print('ROLE',role)
    print(r.stdout)
    print(r.stderr)

run('reader', f'''角色: 普通网文读者
任务: 判断第55章是否想看第56章
输出: PASS/FAIL + 卡点≤3 + AI味≤3 + 是否想看下一章
首段:
{head}
章末:
{tail}
''')
run('science', f'''角色: 科学/医学顾问
任务: 查第55章经络算力负荷、肌电/骨膜应力、神经接口实验描写是否有硬伤
输出: PASS/FAIL + 硬伤≤5 + 小修≤3
片段:
{tech}
''')
