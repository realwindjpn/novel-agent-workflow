import pathlib, subprocess
p=pathlib.Path('/root/workspace/科武纪元/待确认投稿/第55章改.txt')
t=p.read_text(encoding='utf-8')
tail=t[-1700:]
prompt=f'''角色: 编辑定向复审
任务: 只看第55章章末。
核查:
1 是否出现破幕行动/诱饵节点/南天门二阶段
2 负荷限制是否转化为战斗压力
3 是否有异常警报/A7-Kite主动呼叫
4 是否完整到（本章完）
输出: PASS/FAIL + 未落实≤4
章末全文:
{tail}
'''
cmd=['python3','/root/workspace/科武纪元/工具脚本/orchestrate_review.py','--role','editor','--prompt',prompt]
r=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
print(r.stdout)
print(r.stderr)
