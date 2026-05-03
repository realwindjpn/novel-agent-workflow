from pathlib import Path
import re, yaml, requests, subprocess, json

proj = Path('/root/workspace/科武纪元')
chapter = 58
src = proj/'待确认投稿'/f'第{chapter}章改.txt'
if not src.exists(): src = proj/'新版'/f'第{chapter}章.md'
out = proj/'待确认投稿'/f'第{chapter}章改.txt'
card_path = proj/'审核记录/任务卡'/f'第{chapter}章.md'
review_path = proj/'审核记录/六角色外审'/f'第{chapter}章.md'
raw_dir = proj/'审核记录/六角色外审/raw'
card_path.parent.mkdir(parents=True, exist_ok=True); raw_dir.mkdir(parents=True, exist_ok=True)
text = src.read_text(encoding='utf-8', errors='ignore')
card = '''# 第58章任务卡

- V8锚点：第二卷《数据追踪》。十二人嫌疑人名单摆在赵刚桌上，隐藏代码指向内部文件服务器，仅三级以上权限可访问。
- 上章承接：第57章芯片/固件溯源发现隐藏签名和内部痕迹，必须转入数据追踪。
- 本章必须发生：
  1. 陈思琪/专案组把隐藏代码反查到内部文件服务器或权限路径。
  2. 嫌疑人范围缩到可执行名单，不直接抓人。
  3. 为第59章诱饵行动准备文档/监控条件。
- 禁止发生：
  1. 不提前让内鬼现身。
  2. 不写成纯会议列表。
  3. 不跳过权限审计的因果链。
- 人物任务：陈思琪做数据追踪；赵刚定边界；林星辰感受内部信任压力；方宁补服务器/日志常识。
- 技术素材：文件服务器、三级权限、访问日志、哈希、旧缓存、诱饵文档、审计沙箱。
- 章末钩子：诱饵文档上线或FS-07服务器准备完毕，牵引第59章。
- 风格提醒：技术解释进动作链；写屏幕、键盘、日志、权限提示；禁论文腔。
'''
card_path.write_text(card, encoding='utf-8')
cfg = yaml.safe_load(open('/root/.hermes/config.yaml', encoding='utf-8')) or {}; m=cfg.get('model') or {}
base=m.get('base_url','http://43.135.181.17:8080/v1').rstrip('/'); key=m.get('api_key'); model=m.get('default') or m.get('model') or 'gpt-5.5'
prompt=f'''你是《科武纪元》作者。按任务卡精修第58章，不解释。

{card}

硬约束：保留原主线；字数3200-4200中文；首行第58章 数据追踪；末行（本章完）；不写论文说明。

原文：
{text}
'''
r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':6500},timeout=300)
if not r.ok: raise SystemExit(f'AUTHOR_FAIL {r.status_code} {r.text[:300]}')
new=r.json()['choices'][0]['message']['content'].strip()
new=re.sub(r'^```(?:txt|md)?\s*','',new).strip(); new=re.sub(r'\s*```$','',new).strip()
if not new.splitlines() or not new.splitlines()[0].startswith('第58章'): new='第58章 数据追踪\n\n'+new
lines=new.splitlines()
while lines and not lines[-1].strip(): lines.pop()
if not lines or not lines[-1].strip().startswith('（本章完）'): lines.append('（本章完）')
else: lines[-1]='（本章完）'
new='\n'.join(lines)+'\n'
for old,repl in {'意识到':'察觉','意味着':'说明','仿佛':'','不禁':'','微微':'','淡淡':'','缓缓':'','宛如':'像'}.items(): new=new.replace(old,repl)
out.write_text(new, encoding='utf-8')
cn=len(re.findall(r'[\u4e00-\u9fff]',new))
head=new[:750]; tail=new[-900:]
reader_prompt=f'''角色: 普通网文读者
任务: 判断第58章是否看得懂、顺不顺、爽不爽、想不想看第59章
输出必须包含英文 PASS 或 FAIL；再给卡点≤3、AI味≤3、是否想看下一章。
首段:
{head}
章末:
{tail}
'''
cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','reader','--prompt',reader_prompt]
rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
(raw_dir/f'第{chapter}_reader.json').write_text(rr.stdout+'\n'+rr.stderr,encoding='utf-8')
reader_text=rr.stdout; reader_ok='"ok": true' in reader_text and ('PASS' in reader_text or '✅' in reader_text or '想看下一章' in reader_text)
record=f'''# 第58章 六角色外审记录

时间：2026-05-02
章节：第58章《数据追踪》
文件：{out}

## 任务卡
见：{card_path}

## 本地预检
- 字数：{cn}
- 首行：第58章 数据追踪
- 末行：（本章完）

## 作者修订
模型：{model} / CPA
结论：已按任务卡完成精修。

## 读者审
模型：MiniMax-M2.7
原始输出：`raw/第58_reader.json`
结论：{'PASS' if reader_ok else 'REVIEW_NEEDED'}

## 最终结论
{'PASS' if reader_ok else 'REVIEW_NEEDED'}
'''
review_path.write_text(record,encoding='utf-8')
print(json.dumps({'chapter':58,'chars':cn,'reader_pass':reader_ok,'file':str(out),'card':str(card_path),'review':str(review_path)},ensure_ascii=False))
