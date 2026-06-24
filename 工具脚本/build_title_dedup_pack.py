from pathlib import Path
import json,re,datetime
root=Path('/root/workspace/科武纪元')
audit=Path('/root/workspace/科武纪元/审核记录/章节标题问题清单_20260605_1159.json')
data=json.loads(audit.read_text(encoding='utf-8'))
out=Path('/root/workspace/科武纪元/审核记录/章节标题改名证据包_20260605.md')

def read_excerpt(ch):
    p=root/'新版'/f'第{ch}章.md'
    if not p.exists():
        # avoid backups unless no normal file
        cand=sorted((root/'新版').glob(f'第{ch}章*.md'))
        p=cand[0] if cand else None
    if not p or not p.exists(): return '', '', ''
    txt=p.read_text(encoding='utf-8', errors='ignore')
    lines=[x for x in txt.splitlines() if x.strip()]
    title=lines[0] if lines else ''
    body='\n'.join(lines[1:])
    head=body[:450].replace('\n',' ')
    tail=body[-450:].replace('\n',' ')
    return str(p), head, tail

parts=['# 科武纪元章节标题改名证据包（只读）','', '## 任务','- 为重复章节名/内部流程名提供正式外显标题候选。','- 保留章节功能，不改正文。','- 优先处理已投稿/上传线章节与用户点名问题。','']
parts.append('## 重复标题组')
for d in data['duplicates']:
    title=d['title']; chs=d['chapters']
    parts.append(f'\n### 「{title}」→ 章节 {", ".join(map(str,chs))}')
    for ch in chs:
        p,head,tail=read_excerpt(ch)
        parts.append(f'#### 第{ch}章')
        parts.append(f'- 源稿：`{p}`')
        parts.append(f'- 开头摘录：{head}')
        parts.append(f'- 结尾摘录：{tail}')
# true internal hits from 新版/已投稿/wiki only; skip outline parser noise
parts.append('\n## 内部流程名/不宜外显（正文源/上传镜像/Wiki）')
for it in data['internal_name_hits']:
    if it['source'] in ('新版','已投稿','wiki'):
        parts.append(f'- 第{it["chapter"]}章｜{it["source"]}｜{it["title"]}｜`{it["path"]}`｜raw={it["raw"][:100]}')
parts.append('\n## 输出要求')
parts.append('给表格：章号｜旧标题｜建议新标题A｜建议新标题B｜推荐｜理由｜同步范围｜风险。')
parts.append('重点：第133章不能继续叫算力危机；第105/106不能叫卷二终章。')
out.write_text('\n'.join(parts), encoding='utf-8')
print(out)
print(out.stat().st_size)
