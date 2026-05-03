import pathlib, subprocess
p = pathlib.Path('/root/workspace/科武纪元/待确认投稿/第53章改.txt')
t = p.read_text(encoding='utf-8')
tail = t[-1800:]
prompt = f'''角色: 编辑复审
任务: 只复审第53章章末是否已修好
核查:
1 是否有即时触发型钩子
2 是否有行动指令/布控落点
3 张维舟/技术泄露/接样是否形成因果桥
输出: PASS/FAIL + 未落实≤3 + 小修≤2
章末片段:
{tail}
'''
cmd = ['python3','/root/workspace/科武纪元/工具脚本/orchestrate_review.py','--role','editor','--prompt',prompt]
r = subprocess.run(cmd, cwd='/root/workspace', capture_output=True, text=True, timeout=240)
print(r.stdout)
print(r.stderr)
