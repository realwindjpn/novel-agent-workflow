import sys, re, pathlib, subprocess, json
ch = int(sys.argv[1])
base = pathlib.Path('/root/workspace/科武纪元')
p = base / '待确认投稿' / f'第{ch}章改.txt'
if not p.exists():
    raise SystemExit(f'MISSING {p}')
t = p.read_text(encoding='utf-8')
cn = len(re.findall(r'[\u4e00-\u9fff]', t))
first = next((l.strip() for l in t.splitlines() if l.strip()), '')
last = next((l.strip() for l in reversed(t.splitlines()) if l.strip()), '')
flags=[]
if cn < 3000: flags.append('字数不足')
if not first.startswith(f'第{ch}章'): flags.append('首行异常')
if last != '（本章完）': flags.append('末行异常')
if any(w in t for w in ['意识到','意味着','仿佛','不禁','微微','淡淡','缓缓','宛如']): flags.append('AI词残留')
head = t[:700]
tail = t[-900:]
mid = t[len(t)//2:len(t)//2+700]
prompt = f'''角色: 编辑
任务: 审第{ch}章结构/商业节奏/大纲承接
输出: PASS/FAIL + 必改不超过5条 + 小修不超过3条
禁止重写正文。
本地预检: 字数{cn}; 首行{first}; 末行{last}; 异常{flags}
首段:
{head}
中段:
{mid}
章末:
{tail}
'''
cmd=['python3', str(base/'工具脚本/orchestrate_review.py'), '--role','editor','--prompt',prompt]
r=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
print('LOCAL', json.dumps({'chapter':ch,'chars':cn,'first':first,'last':last,'flags':flags}, ensure_ascii=False))
print(r.stdout)
print(r.stderr)
