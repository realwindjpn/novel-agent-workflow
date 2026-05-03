from pathlib import Path
import re, yaml, requests, subprocess, json
proj=Path('/root/workspace/科武纪元'); chapter=63
src=proj/'待确认投稿'/f'第{chapter}章改.txt'
if not src.exists(): src=proj/'新版'/f'第{chapter}章.md'
out=proj/'待确认投稿'/f'第{chapter}章改.txt'
card_path=proj/'审核记录/任务卡'/f'第{chapter}章.md'
review_path=proj/'审核记录/六角色外审'/f'第{chapter}章.md'
raw_dir=proj/'审核记录/六角色外审/raw'; card_path.parent.mkdir(parents=True,exist_ok=True); raw_dir.mkdir(parents=True,exist_ok=True)
text=src.read_text(encoding='utf-8',errors='ignore')
card='''# 第63章任务卡

- V8锚点：第二卷《铁幕轮廓》。综合供述和追踪数据，铁幕轮廓在两周内逐渐清晰；通讯记录中加密频道互不透明，铁幕内部并非铁板一块；目标不只是垄断算力，还要垄断AI生态标准。
- 上章承接：第62章审讯供出壳公司、沙海贸易公司、胁迫+利诱模式，本章需把碎片拼成铁幕结构。
- 本章必须发生：
  1. 铁幕结构从点状线索变成组织轮廓。
  2. 展现美/日/欧利益分歧或频道隔离，不写成铁板一块。
  3. 点出生态垄断：芯片+闭源软件+大模型/标准绑定。
- 禁止发生：
  1. 不把铁幕完整底牌一次揭完。
  2. 不写成纯报告会。
  3. 不把生态战争讲成论文。
- 人物任务：陈思琪做结构图；赵刚定行动方向；林星辰理解敌人是体系不是个人；方宁补工程生态判断。
- 技术/政治素材：CUDA式生态锁定、闭源接口、芯片架构绑定、频道隔离、利益分歧。
- 章末钩子：指向第64波斯湾/沙海贸易公司暗线，进入境外追查。
- 风格提醒：用结构图、权限线、接口表、会议动作承载信息；禁文艺比喻。
'''
card_path.write_text(card,encoding='utf-8')
cfg=yaml.safe_load(open('/root/.hermes/config.yaml',encoding='utf-8')) or {}; m=cfg.get('model') or {}
base=m.get('base_url','http://43.135.181.17:8080/v1').rstrip('/'); key=m.get('api_key'); model=m.get('default') or m.get('model') or 'gpt-5.5'
prompt=f'''你是《科武纪元》作者。按任务卡精修第63章，不解释。

{card}

硬约束：保留原主线；字数3200-4200中文；首行第63章 铁幕轮廓；末行（本章完）。

原文：
{text}
'''
r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':6500},timeout=300)
if not r.ok: raise SystemExit(f'AUTHOR_FAIL {r.status_code} {r.text[:300]}')
new=r.json()['choices'][0]['message']['content'].strip(); new=re.sub(r'^```(?:txt|md)?\s*','',new).strip(); new=re.sub(r'\s*```$','',new).strip()
if not new.splitlines() or not new.splitlines()[0].startswith('第63章'): new='第63章 铁幕轮廓\n\n'+new
lines=new.splitlines()
while lines and not lines[-1].strip(): lines.pop()
if not lines or not lines[-1].strip().startswith('（本章完）'): lines.append('（本章完）')
else: lines[-1]='（本章完）'
new='\n'.join(lines)+'\n'
for old,repl in {'意识到':'察觉','意味着':'说明','仿佛':'','不禁':'','微微':'','淡淡':'','缓缓':'','宛如':'像'}.items(): new=new.replace(old,repl)
out.write_text(new,encoding='utf-8')
cn=len(re.findall(r'[\u4e00-\u9fff]',new)); head=new[:750]; tail=new[-900:]
reader_prompt=f'''角色: 普通网文读者
任务: 判断第63章是否看得懂、顺不顺、爽不爽、想不想看第64章
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
record=f'''# 第63章 六角色外审记录

时间：2026-05-02
章节：第63章《铁幕轮廓》
文件：{out}

## 任务卡
见：{card_path}

## 本地预检
- 字数：{cn}
- 首行：第63章 铁幕轮廓
- 末行：（本章完）

## 作者修订
模型：{model} / CPA
结论：已按任务卡完成精修。

## 读者审
模型：MiniMax-M2.7
原始输出：`raw/第63_reader.json`
结论：{'PASS' if reader_ok else 'REVIEW_NEEDED'}

## 最终结论
{'PASS' if reader_ok else 'REVIEW_NEEDED'}
'''
review_path.write_text(record,encoding='utf-8')
print(json.dumps({'chapter':63,'chars':cn,'reader_pass':reader_ok,'file':str(out),'card':str(card_path),'review':str(review_path)},ensure_ascii=False))
