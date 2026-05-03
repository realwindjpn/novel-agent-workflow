import pathlib, subprocess
p=pathlib.Path('/root/workspace/科武纪元/待确认投稿/第54章改.txt')
t=p.read_text(encoding='utf-8')
head=t[:800]
tail=t[-1200:]
tech=[]
for k in ['热控','ARK-X-001','分段签名','回执','权限','Morrow','审计','轨道防御']:
    i=t.find(k)
    if i!=-1:
        tech.append(t[max(0,i-180):i+360])
tech_excerpt='\n---\n'.join(tech)[:1600]

def run(role,prompt):
    cmd=['python3','/root/workspace/科武纪元/工具脚本/orchestrate_review.py','--role',role,'--prompt',prompt]
    r=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
    print('ROLE',role)
    print(r.stdout)
    print(r.stderr)

reader_prompt=f'''角色: 普通网文读者
任务: 判断第54章是否想看第55章
输出: PASS/FAIL + 卡点≤3 + AI味≤3 + 是否想看下一章
首段:
{head}
章末:
{tail}
'''
science_prompt=f'''角色: 科学/工程顾问
任务: 审第54章技术审计表达是否可信、读者能否读懂
关注: 热控临界点、ARK-X-001索引、分段签名、旧回执格式、权限/审计链
输出: PASS/FAIL + 硬伤≤5 + 读不懂处≤3 + 小修≤3
片段:
{tech_excerpt}
'''
run('reader', reader_prompt)
run('science', science_prompt)
