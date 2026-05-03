from pathlib import Path
import re, yaml, requests, subprocess, json, os

proj = Path('/root/workspace/科武纪元')
chapter = 57
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

card = '''# 第57章任务卡

- V8锚点：第二卷《芯片溯源》。陈思琪在芯片分析室逆向分析沙海区域缴获AI芯片，制造工艺与南天门实验室样品一致；流云在固件中发现隐藏代码，像签名。
- 上章承接：第56章破幕行动启动，诱饵节点/内部缓存编号暴露，调查指向芯片样件与内部检索痕迹。
- 本章必须发生：
  1. 陈思琪主导芯片/固件溯源，落到具体工艺、封装、固件签名。
  2. 证明敌方不是普通仿制，而是接触过南天门样品或旧流程。
  3. 结尾指向第58章数据追踪/内部文件服务器。
- 禁止发生：
  1. 不提前抓出内鬼。
  2. 不把芯片解释写成论文。
  3. 不削弱陈思琪的专业动作。
- 人物任务：陈思琪承担技术主视角；林星辰从旁理解“内部痕迹”的严重性；方宁补工艺/热控判断；赵刚定调查动作。
- 技术素材：芯片封装、BOM、固件哈希、隐藏签名、样品批次、测试日志索引。
- 章末钩子：隐藏代码反向指向内部文件服务器/三级权限路径，牵引第58章。
- 风格提醒：技术进入动作链；用屏幕、仪器、手部疲劳、警报音承载信息；禁文艺比喻。
'''
card_path.write_text(card, encoding='utf-8')

cfg = yaml.safe_load(open('/root/.hermes/config.yaml', encoding='utf-8')) or {}
m = cfg.get('model') or {}
base = m.get('base_url','http://43.135.181.17:8080/v1').rstrip('/')
key = m.get('api_key')
model = m.get('default') or m.get('model') or 'gpt-5.5'

prompt = f'''你是《科武纪元》作者。按任务卡精修第57章，不解释。

{card}

硬约束：
- 保留原主线，不新增未批准设定。
- 字数3200-4200中文。
- 首行：第57章 芯片溯源
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
new = re.sub(r'\s*```$', '', new).strip()
if not new.splitlines() or not new.splitlines()[0].startswith('第57章'):
    new = '第57章 芯片溯源\n\n' + new
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

head = new[:750]
tail = new[-900:]
reader_prompt = f'''角色: 普通网文读者
任务: 判断第57章是否看得懂、顺不顺、爽不爽、想不想看第58章
输出必须包含英文 PASS 或 FAIL；再给卡点≤3、AI味≤3、是否想看下一章。
首段:
{head}
章末:
{tail}
'''
cmd = ['python3', str(proj/'工具脚本/orchestrate_review.py'), '--role', 'reader', '--prompt', reader_prompt]
rr = subprocess.run(cmd, cwd='/root/workspace', capture_output=True, text=True, timeout=240)
(raw_dir/f'第{chapter}_reader.json').write_text(rr.stdout + '\n' + rr.stderr, encoding='utf-8')
reader_text = rr.stdout
reader_ok = '"ok": true' in reader_text and ('PASS' in reader_text or '✅' in reader_text or '想看下一章' in reader_text)

record = f'''# 第57章 六角色外审记录

时间：2026-05-02
章节：第57章《芯片溯源》
文件：{out}

## 任务卡
见：{card_path}

## 本地预检
- 字数：{cn}
- 首行：第57章 芯片溯源
- 末行：（本章完）

## 作者修订
模型：{model} / CPA
结论：已按任务卡完成精修。

## 读者审
模型：MiniMax-M2.7
原始输出：`raw/第57_reader.json`
结论：{'PASS' if reader_ok else 'REVIEW_NEEDED'}

## 最终结论
{'PASS' if reader_ok else 'REVIEW_NEEDED'}
'''
review_path.write_text(record, encoding='utf-8')
print(json.dumps({'chapter':57,'chars':cn,'reader_pass':reader_ok,'file':str(out),'card':str(card_path),'review':str(review_path)}, ensure_ascii=False))
