import pathlib, subprocess
p=pathlib.Path('/root/workspace/科武纪元/待确认投稿/第54章改.txt')
t=p.read_text(encoding='utf-8')
tail=t[-1600:]
prompt=f'''角色: 编辑定向复审
任务: 只看第54章章末。
核查:
1 章末是否完整到（本章完）
2 是否有总体目录/轨道防御泄露落点
3 是否有新预警/行动代号/下一章钩子
输出: PASS/FAIL + 未落实≤3
章末全文:
{tail}
'''
cmd=['python3','/root/workspace/科武纪元/工具脚本/orchestrate_review.py','--role','editor','--prompt',prompt]
r=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
print(r.stdout)
print(r.stderr)
