import os, re, yaml, requests, pathlib
proj=pathlib.Path('/root/workspace/科武纪元')
p=proj/'待确认投稿/第55章改.txt'
t=p.read_text(encoding='utf-8')
cfg=yaml.safe_load(open('/root/.hermes/config.yaml',encoding='utf-8')) or {}
m=cfg.get('model') or {}
base=m.get('base_url','http://43.135.181.17:8080/v1').rstrip('/')
key=m.get('api_key')
model=m.get('default') or m.get('model') or 'gpt-5.5'
prompt=f'''你是《科武纪元》作者。只修第55章《觉醒之终》，不要解释。
目标: 将现稿从过长压缩到3800-4800中文字，同时落实编辑必改。
必改:
1 开篇技术说明压缩到1/3，用站桩体感/赵刚指令承载。
2 结业评估必须指向下一阶段任务/编制归属/敌情动向。
3 “心里沉”改为终端提示、肌肉绷紧等实战压力动作。
4 回忆闪回压缩为3个关键词，评估数据只保留核心3人，其余一笔带过。
5 章末加入异常警报/新坐标/未授权信号，牵引第56章。
小修:
- 第二层通路表述统一为“第二层通路（十二正经）贯通第72小时”。
- 训练伤写具体部位，不写空泛骨膜疼。
硬约束:
- 保留卷一结业、正式编制、铁幕阴影引出卷二。
- 禁止文艺比喻。
- 首行: 第55章 觉醒之终
- 末行: （本章完）
原文:
{t}
'''
r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':7000},timeout=300)
if not r.ok: raise SystemExit(r.text[:500])
new=r.json()['choices'][0]['message']['content'].strip()
new=re.sub(r'^```(?:txt|md)?\s*','',new).strip(); new=re.sub(r'\s*```$','',new).strip()
if not new.splitlines()[0].startswith('第55章'):
    new='第55章 觉醒之终\n\n'+new
lines=new.splitlines()
while lines and not lines[-1].strip(): lines.pop()
if not lines or not lines[-1].strip().startswith('（本章完）'):
    lines.append('（本章完）')
else:
    lines[-1]='（本章完）'
new='\n'.join(lines)+'\n'
for old,repl in {'意识到':'察觉','意味着':'说明','仿佛':'','不禁':'','微微':'','淡淡':'','缓缓':'','宛如':'像'}.items():
    new=new.replace(old,repl)
p.write_text(new,encoding='utf-8')
print('REVISED ch55 chars',len(re.findall(r'[\u4e00-\u9fff]',new)))
