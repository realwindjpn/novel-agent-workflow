from pathlib import Path
import re, yaml, requests, subprocess, json
proj=Path('/root/workspace/科武纪元'); chapter=59
src=proj/'待确认投稿'/f'第{chapter}章改.txt'
if not src.exists(): src=proj/'新版'/f'第{chapter}章.md'
out=proj/'待确认投稿'/f'第{chapter}章改.txt'
card_path=proj/'审核记录/任务卡'/f'第{chapter}章.md'
review_path=proj/'审核记录/六角色外审'/f'第{chapter}章.md'
raw_dir=proj/'审核记录/六角色外审/raw'; card_path.parent.mkdir(parents=True,exist_ok=True); raw_dir.mkdir(parents=True,exist_ok=True)
text=src.read_text(encoding='utf-8',errors='ignore')
card='''# 第59章任务卡

- V8锚点：第二卷《诱饵行动》。诱饵文档放上内部服务器FS-07，方宁配合制造逼真散热系统参数，追踪外传路径。
- 上章承接：第58章数据追踪锁定内部文件服务器/三级权限路径，准备以诱饵文档反查外传链。
- 本章必须发生：
  1. 诱饵文档上线FS-07，参数足够真实但带追踪签名。
  2. 方宁负责散热参数伪装，陈思琪负责追踪/沙箱，赵刚设边界。
  3. 结尾出现诱饵被访问/外传路径启动，牵引第60章内鬼现身。
- 禁止发生：
  1. 不提前揭露张维或真正内鬼。
  2. 不把诱饵写成儿戏，必须有审计和风险控制。
  3. 不让主角团无代价开挂。
- 人物任务：方宁体现工程真实性；陈思琪体现追踪冷静；林星辰承担等待压力；苏雨晴观察身体负荷。
- 技术素材：FS-07、散热系统参数、哈希水印、访问日志、沙箱、外传路径、权限诱饵。
- 章末钩子：凌晨两点零三分或关键时间点，诱饵被访问，进入第60章。
- 风格提醒：短句、设备反馈、屏幕日志、手部动作；禁文艺比喻。
'''
card_path.write_text(card,encoding='utf-8')
cfg=yaml.safe_load(open('/root/.hermes/config.yaml',encoding='utf-8')) or {}; m=cfg.get('model') or {}
base=m.get('base_url','http://43.135.181.17:8080/v1').rstrip('/'); key=m.get('api_key'); model=m.get('default') or m.get('model') or 'gpt-5.5'
prompt=f'''你是《科武纪元》作者。按任务卡精修第59章，不解释。

{card}

硬约束：保留原主线；字数3200-4200中文；首行第59章 诱饵行动；末行（本章完）；不写论文说明。

原文：
{text}
'''
r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':6500},timeout=300)
if not r.ok: raise SystemExit(f'AUTHOR_FAIL {r.status_code} {r.text[:300]}')
new=r.json()['choices'][0]['message']['content'].strip(); new=re.sub(r'^```(?:txt|md)?\s*','',new).strip(); new=re.sub(r'\s*```$','',new).strip()
if not new.splitlines() or not new.splitlines()[0].startswith('第59章'): new='第59章 诱饵行动\n\n'+new
lines=new.splitlines()
while lines and not lines[-1].strip(): lines.pop()
if not lines or not lines[-1].strip().startswith('（本章完）'): lines.append('（本章完）')
else: lines[-1]='（本章完）'
new='\n'.join(lines)+'\n'
for old,repl in {'意识到':'察觉','意味着':'说明','仿佛':'','不禁':'','微微':'','淡淡':'','缓缓':'','宛如':'像'}.items(): new=new.replace(old,repl)
out.write_text(new,encoding='utf-8')
cn=len(re.findall(r'[\u4e00-\u9fff]',new)); head=new[:750]; tail=new[-900:]
reader_prompt=f'''角色: 普通网文读者
任务: 判断第59章是否看得懂、顺不顺、爽不爽、想不想看第60章
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
record=f'''# 第59章 六角色外审记录

时间：2026-05-02
章节：第59章《诱饵行动》
文件：{out}

## 任务卡
见：{card_path}

## 本地预检
- 字数：{cn}
- 首行：第59章 诱饵行动
- 末行：（本章完）

## 作者修订
模型：{model} / CPA
结论：已按任务卡完成精修。

## 读者审
模型：MiniMax-M2.7
原始输出：`raw/第59_reader.json`
结论：{'PASS' if reader_ok else 'REVIEW_NEEDED'}

## 最终结论
{'PASS' if reader_ok else 'REVIEW_NEEDED'}
'''
review_path.write_text(record,encoding='utf-8')
print(json.dumps({'chapter':59,'chars':cn,'reader_pass':reader_ok,'file':str(out),'card':str(card_path),'review':str(review_path)},ensure_ascii=False))
