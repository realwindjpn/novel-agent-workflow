#!/usr/bin/env python3
from pathlib import Path
import importlib.util, json
p=Path('/root/workspace/科武纪元/工具脚本/refine_v811_83_84_local.py')
spec=importlib.util.spec_from_file_location('r', p)
r=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
ch=83
text=Path('/root/workspace/科武纪元/审核记录/临时精修/第83章_V811作者轻修稿_20260513.md').read_text(encoding='utf-8')
task=Path('/root/workspace/科武纪元/审核记录/精修准备/第83章_V811上传前任务卡_20260513.md').read_text(encoding='utf-8')
post = (
    '写后复审《科武纪元》第83章小修稿。只基于实际正文。第一行必须 PASS 或 FAIL。'
    'FAIL只列仍存在必改不超过5条。PASS列理由不超过3条。\n'
    '已按上一轮编辑FAIL修复：1 上章改为昨夜那次；2 章末三地名硬塞改为三行红字压缩；3 删除总结腔句子。\n'
    '门禁：大纲锚点完成；无AI味/报告腔；无wikilink；章末钩子成立；番茄上传格式可行。\n'
    '【任务卡】\n' + task + '\n【实际精修正文全文】\n' + text
)
ed=r.call_role('editor','角色：网文编辑。'+post,ch,'v811_editor_repost')
rd=r.call_role('reader','角色：普通追更读者。'+post,ch,'v811_reader_repost')
out={'editor':ed,'reader':rd}
Path('/root/workspace/科武纪元/审核记录/六角色外审/raw/第83_v811_repost_pair.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
