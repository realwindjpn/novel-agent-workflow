#!/usr/bin/env python3
import os, requests, json, time
from pathlib import Path
ROOT=Path('/root/workspace/科武纪元')
OUT=ROOT/'写作技巧/番茄作家课堂'
editor=OUT/'adaptation_trend_7639993606463307838_editor_opus47fast.md'
writer=OUT/'adaptation_trend_7639993606463307838_writer_tkx_gpt55.md'
state=OUT/'state.json'
report=OUT/'阶段报告.md'
idx=OUT/'番茄作家课堂学习索引.md'
author=Path('/root/workspace/写作角色OS/fanqie_writer_classroom_patch_20260516.md')
kewu=ROOT/'参考资料/作家风格OS/fanqie_classroom_author_patch.md'
text=editor.read_text(encoding='utf-8')
base=os.environ.get('TOKENX_BASE_URL','https://tokenx24.com/v1').rstrip('/')
key=os.environ['TOKENX_API_KEY']
model=os.environ.get('TOKENX_MODEL','gpt-5.5')
# 降粒度：编辑稿只取核心规则，要求短输出，避免524
prompt=f'''你是《科武纪元》作家角色训练官。基于以下WF编辑稿，输出短版作家OS补丁，控制在2500字内。
必须包含：
1 动作链规则
2 物理反馈规则
3 代价规则
4 章末钩子规则
5 短故事/狼人篇可借点
6 科武长篇可借点
禁止长篇理论。

WF编辑稿：
{text[:9000]}
'''
r=requests.post(base+'/chat/completions',headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}],'temperature':0.25,'max_tokens':5000},timeout=300)
r.raise_for_status()
data=r.json(); returned=data.get('model',model); content=data['choices'][0]['message']['content']
writer.write_text(f'# 5月改编风向标｜短剧×漫剧爆款题材与人设｜作家OS转译稿\n\nmodel: {returned}\n\n{content}\n',encoding='utf-8')
for p in [author,kewu]:
    old=p.read_text(encoding='utf-8') if p.exists() else '# 番茄作家课堂 → 作家角色OS补丁\n'
    if '5月改编风向标｜短剧×漫剧爆款题材与人设' not in old:
        p.write_text(old.rstrip()+f'\n\n## 5月改编风向标｜短剧×漫剧爆款题材与人设\n\n来源：`{writer}`\n\n{content}\n',encoding='utf-8')
old=report.read_text(encoding='utf-8') if report.exists() else ''
report.write_text(old.rstrip()+f'\n\n## {time.strftime("%F %T")}｜5月改编风向标｜短剧×漫剧爆款题材与人设\n\n- 状态：PASS（TKX降粒度续跑）\n- TKX作家模型：{returned}\n- 编辑稿：`{editor}`\n- 作家稿：`{writer}`\n',encoding='utf-8')
old=idx.read_text(encoding='utf-8') if idx.exists() else '# 番茄作家课堂学习索引\n'
if 'adaptation_trend_7639993606463307838_writer_tkx_gpt55.md' not in old:
    idx.write_text(old.rstrip()+f'\n- [5月改编风向标｜短剧×漫剧爆款题材与人设](https://fanqienovel.com/writer/zone/article/7639993606463307838)：编辑稿 `{editor.name}`；作家稿 `{writer.name}`。\n',encoding='utf-8')
state.write_text(json.dumps({'status':'completed','total':3,'completed':3,'current':'','last_completed':'adaptation_trend_7639993606463307838','last_title':'5月改编风向标｜短剧×漫剧爆款题材与人设','last_report':str(writer),'updated_at':time.strftime('%F %T')},ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',writer)
