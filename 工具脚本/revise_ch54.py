import os, re, yaml, requests, pathlib
proj=pathlib.Path('/root/workspace/科武纪元')
p=proj/'待确认投稿/第54章改.txt'
t=p.read_text(encoding='utf-8')
cfg=yaml.safe_load(open('/root/.hermes/config.yaml',encoding='utf-8')) or {}
m=cfg.get('model') or {}
base=m.get('base_url','http://43.135.181.17:8080/v1').rstrip('/')
key=m.get('api_key')
model=m.get('default') or m.get('model') or 'gpt-5.5'
prompt=f'''你是《科武纪元》作者。只修第54章，不解释。
编辑必改:
1 章末补商业钩子: 新预警/内鬼特征/行动代号之一，牵引第55章。
2 补热控临界点到ARK-X-001索引的审计过渡。
3 李梦瑶出场前补审批流/通讯审计面板锚点。
4 修“月十七日”缺月份。
5 内鬼定性加限定: 结合权限层级和操作痕迹，初步排除外部撞库，高度指向内部流程劫持。
小修:
- 范霍夫奇点补工程化解释。
- 胸口闷痛改专业微动作。
- 修末句截断。
硬约束: 保留剧情；3500-4500中文；硬派工业党风格；首行第54章 南天门技术泄露调查；末行（本章完）。
原文:
{t}
'''
r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':6500},timeout=300)
if not r.ok: raise SystemExit(r.text[:500])
new=r.json()['choices'][0]['message']['content'].strip()
new=re.sub(r'^```(?:txt|md)?\s*','',new).strip(); new=re.sub(r'\s*```$','',new).strip()
if not new.splitlines()[0].startswith('第54章'):
    new='第54章 南天门技术泄露调查\n\n'+new
lines=new.splitlines()
while lines and not lines[-1].strip(): lines.pop()
if not lines[-1].strip().startswith('（本章完）'):
    lines.append('（本章完）')
else:
    lines[-1]='（本章完）'
new='\n'.join(lines)+'\n'
for old,repl in {'意识到':'察觉','意味着':'说明','仿佛':'','不禁':'','微微':'','淡淡':'','缓缓':'','宛如':'像'}.items():
    new=new.replace(old,repl)
p.write_text(new,encoding='utf-8')
print('REVISED ch54 chars',len(re.findall(r'[\u4e00-\u9fff]',new)))
