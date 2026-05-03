import pathlib, subprocess
p=pathlib.Path('/root/workspace/科武纪元/待确认投稿/第54章改.txt')
t=p.read_text(encoding='utf-8')
# targeted: include suspicious zones + tail
keys=['系统会','Morrow','按流程','总体目录','行动代号']
chunks=[]
for k in keys:
    i=t.find(k)
    if i!=-1: chunks.append(t[max(0,i-250):i+450])
chunks.append(t[-1000:])
excerpt='\n---\n'.join(chunks)[:2600]
prompt=f'''角色: 编辑定向复审
任务: 只判断第54章五个必改是否已落实。
核查项:
1 首段技术推演是否完整，无截断
2 无“应该结束”占位符
3 章末总体目录/全都/钩子是否完整
4 Morrow是否有上下文锚点
5 是否有指挥层定调与行动代号
输出: PASS/FAIL + 未落实≤5。若片段已显示完整，不得凭印象说截断。
片段:
{excerpt}
'''
cmd=['python3','/root/workspace/科武纪元/工具脚本/orchestrate_review.py','--role','editor','--prompt',prompt]
r=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
print(r.stdout)
print(r.stderr)
