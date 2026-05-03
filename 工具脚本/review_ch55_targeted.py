import pathlib, subprocess
p=pathlib.Path('/root/workspace/科武纪元/待确认投稿/第55章改.txt')
t=p.read_text(encoding='utf-8')
# include start/middle/tail exact no truncation markers
excerpt = t[:1000] + '\n---MIDDLE---\n' + t[2100:3600] + '\n---TAIL---\n' + t[-1400:]
prompt=f'''角色: 编辑定向复审
任务: 只判断第55章此前必改是否已落实。若片段完整，不得误判截断。
核查:
1 训练场到会议室是否有明确过渡
2 结业/卷一结束是否有代价感情绪锚点
3 破幕行动是否指向卷二任务和诱饵节点
4 负荷限制是否与任务形成战术压力
5 章末是否有异常警报/A7-Kite主动呼叫钩子并完整到（本章完）
输出: PASS/FAIL + 未落实≤5 + 小修≤3
片段:
{excerpt[:3800]}
'''
cmd=['python3','/root/workspace/科武纪元/工具脚本/orchestrate_review.py','--role','editor','--prompt',prompt]
r=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
print(r.stdout)
print(r.stderr)
