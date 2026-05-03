import re, pathlib, subprocess
p = pathlib.Path('/root/workspace/科武纪元/待确认投稿/第53章改.txt')
t = p.read_text(encoding='utf-8')
keys = ['铁幕','张维舟','门禁','权限','警报','倒计时','服务器','资金','频段','跳板']
paras = [x.strip() for x in re.split(r'\n\s*\n', t) if x.strip()]
hit = []
for para in paras:
    if any(k in para for k in keys):
        hit.append(para)
excerpt = '\n\n'.join(hit[:8])[:1800]
prompt = f'''角色: 编辑复审
任务: 复审第53章修订是否落实必改
章节功能: 南美归来，顾问组/张维舟/铁幕线索，国内技术泄露调查落地
重点核查:
1 铁幕是否具象化
2 技术泄露是否有可执行目标
3 张维舟与泄露线是否有因果/时间轴桥
4 章末是否即时触发型钩子
5 是否可进入读者/顾问审
输出: PASS/FAIL + 未落实不超过5条 + 小修不超过3条
片段:
{excerpt}
'''
cmd = ['python3','/root/workspace/科武纪元/工具脚本/orchestrate_review.py','--role','editor','--prompt',prompt]
r = subprocess.run(cmd, cwd='/root/workspace', capture_output=True, text=True, timeout=240)
print(r.stdout)
print(r.stderr)
