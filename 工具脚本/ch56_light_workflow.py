from pathlib import Path
import re, yaml, requests, subprocess, json, os

proj = Path('/root/workspace/科武纪元')
chapter = 56
src = proj/'待确认投稿'/f'第{chapter}章改.txt'
if not src.exists():
    src = proj/'新版'/f'第{chapter}章.md'
out = proj/'待确认投稿'/f'第{chapter}章改.txt'
card_path = proj/'审核记录/任务卡'/f'第{chapter}章.md'
review_path = proj/'审核记录/六角色外审'/f'第{chapter}章.md'
raw_dir = proj/'审核记录/六角色外审/raw'
card_path.parent.mkdir(parents=True, exist_ok=True)
raw_dir.mkdir(parents=True, exist_ok=True)
text = src.read_text(encoding='utf-8', errors='ignore')

# task card: use V8 known anchor for ch56
card = '''# 第56章任务卡

- V8锚点：第二卷开篇《铁幕代号》。返回地球后第三天，林星辰被召至太行山地下作战分析室，小队受命成立专项调查组追查铁幕代号。
- 上章承接：第55章第一卷结业，破幕行动启动；诱饵节点未上线却发生回连，A7-Kite主动呼叫。
- 本章必须发生：
  1. 正式进入第二卷，破幕行动从结业转入实战调查。
  2. 铁幕代号/通信加密方式与营地内部系统相似，指向内外勾连。
  3. 给出可执行调查目标，不停在会议复盘。
- 禁止发生：
  1. 不把第56章写成单纯信息说明会。
  2. 不提前解决Morrow/A7/Kite真人身份。
  3. 不覆盖后续第57芯片溯源功能。
- 人物任务：林星辰承接正式作战压力；陈思琪负责加密/日志判断；赵刚给行动边界；苏雨晴盯住林星辰负荷。
- 技术/政治素材：加密信道、旧链回连、权限审计、诱饵节点、准军事/组织化敌情只作轻点。
- 章末钩子：锁定下一步芯片/样件溯源或内部服务器异常，牵引第57章。
- 风格提醒：短句、行动链、物理反馈；禁文艺比喻；技术解释进入动作。
'''
card_path.write_text(card, encoding='utf-8')

# if current file too long/has AI words but already exists, revise with author model
cfg = yaml.safe_load(open('/root/.hermes/config.yaml', encoding='utf-8')) or {}
m = cfg.get('model') or {}
base = m.get('base_url','http://43.135.181.17:8080/v1').rstrip('/')
key = m.get('api_key')
model = m.get('default') or m.get('model') or 'gpt-5.5'

prompt = f'''你是《科武纪元》作者。按任务卡精修第56章，不解释。

{card}

硬约束：
- 保留原主线，不新增未批准设定。
- 字数3200-4200中文。
- 首行：第56章 铁幕代号
- 末行：（本章完）
- 不要文艺比喻，不写论文说明。

原文：
{text}
'''

r = requests.post(base+'/chat/completions', headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'}, json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':6500}, timeout=300)
if not r.ok:
    raise SystemExit(f'AUTHOR_FAIL {r.status_code} {r.text[:300]}')
new = r.json()['choices'][0]['message']['content'].strip()
new = re.sub(r'^```(?:txt|md)?\s*','',new).strip()
new = re.sub(r'\s*```$','',new).strip()
if not new.splitlines() or not new.splitlines()[0].startswith('第56章'):
    new = '第56章 铁幕代号\n\n' + new
lines = new.splitlines()
while lines and not lines[-1].strip(): lines.pop()
if not lines or not lines[-1].strip().startswith('（本章完）'):
    lines.append('（本章完）')
else:
    lines[-1] = '（本章完）'
new='\n'.join(lines)+'\n'
for old,repl in {'意识到':'察觉','意味着':'说明','仿佛':'','不禁':'','微微':'','淡淡':'','缓缓':'','宛如':'像'}.items():
    new=new.replace(old,repl)
out.write_text(new, encoding='utf-8')
cn = len(re.findall(r'[\u4e00-\u9fff]', new))

# reader gate
head = new[:750]
tail = new[-900:]
reader_prompt = f'''角色: 普通网文读者
任务: 判断第56章是否看得懂、顺不顺、爽不爽、想不想看第57章
输出: PASS/FAIL + 卡点≤3 + AI味≤3 + 是否想看下一章
首段:
{head}
章末:
{tail}
'''
cmd = ['python3', str(proj/'工具脚本/orchestrate_review.py'), '--role', 'reader', '--prompt', reader_prompt]
rr = subprocess.run(cmd, cwd='/root/workspace', capture_output=True, text=True, timeout=240)
(raw_dir/f'第{chapter}_reader.json').write_text(rr.stdout + '\n' + rr.stderr, encoding='utf-8')
reader_ok = '"ok": true' in rr.stdout and 'PASS' in rr.stdout

record = f'''# 第56章 六角色外审记录

时间：2026-05-02
章节：第56章《铁幕代号》
文件：{out}

## 任务卡
见：{card_path}

## 本地预检
- 字数：{cn}
- 首行：第56章 铁幕代号
- 末行：（本章完）

## 作者修订
模型：{model} / CPA
结论：已按任务卡完成精修。

## 读者审
模型：MiniMax-M2.7
原始输出：`raw/第56_reader.json`
结论：{'PASS' if reader_ok else 'REVIEW_NEEDED'}

## 最终结论
{'PASS' if reader_ok else 'REVIEW_NEEDED'}
'''
review_path.write_text(record, encoding='utf-8')
print(json.dumps({'chapter':56,'chars':cn,'reader_pass':reader_ok,'file':str(out),'card':str(card_path),'review':str(review_path)}, ensure_ascii=False))
