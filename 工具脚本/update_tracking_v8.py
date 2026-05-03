from pathlib import Path
import re

proj = Path('/root/workspace/科武纪元')
track = proj / '小说综合跟踪表.md'
text = track.read_text(encoding='utf-8')
text = re.sub(r'更新时间：[^\n]+', '更新时间：2026-05-02', text, count=1)

insert = '''
## 0.1 V8同步与改版对照状态（2026-05-02）

- 当前生效大纲：`科武纪元大纲 V8_完整版.md`。
- 白盾部队暗线已同步至V8：第217/223/226/233/243章；定位为第五卷政治撕裂阶段的制度裂缝推演产物，不替代铁幕/星穹/来客主线。
- 1-52章：修改版统一保留在 `待确认投稿/第N章改.txt`，不自动转正，不覆盖 `新版/` 或 `已投稿/`。
- 53-105章：进入六角色外审精修流程；过关后保留在 `待确认投稿/第N章改.txt`，供人工上传前检查。
- 已外审PASS：第53章、第54章。
- 改版对照表：`审核记录/正常版_修改版对照表.md`。

'''
if '## 0.1 V8同步与改版对照状态（2026-05-02）' not in text:
    text = text.replace('## 0、当前基准状态（2026-05-01）\n', '## 0、当前基准状态（2026-05-01）\n' + insert, 1)

text = text.replace('| 五·归途 | 209-258 | 写至226 | 进行中 | 进行中 | 209-226已完成逐章评审闭环；下一章227 |', '| 五·归途 | 206-255/209-258工作稿 | 写至237 | 进行中 | 进行中 | V8已同步白盾部队暗线；正文后续写作需按217/223/226/233/243锚点对齐 |')
track.write_text(text, encoding='utf-8')

base_new = proj / '新版'
base_mod = proj / '待确认投稿'
base_pub = proj / '已投稿'
review_dir = proj / '审核记录' / '六角色外审'

def cn(p):
    if not p.exists():
        return ''
    return str(len(re.findall(r'[\u4e00-\u9fff]', p.read_text(encoding='utf-8', errors='ignore'))))

rows = []
for n in range(1, 106):
    newp = base_new / f'第{n}章.md'
    modp = base_mod / f'第{n}章改.txt'
    pubp = base_pub / f'第{n}章.txt'
    status = '原稿'
    review = ''
    if modp.exists():
        status = '已精修待确认'
    rp = review_dir / f'第{n}章.md'
    if rp.exists():
        rt = rp.read_text(encoding='utf-8', errors='ignore')
        if '最终结论\nPASS' in rt or '## 最终结论\nPASS' in rt:
            review = 'PASS'
            status = '已外审PASS'
        else:
            review = '待复审'
    rows.append([n, cn(newp), cn(modp), '有' if pubp.exists() else '无', status, review, str(newp) if newp.exists() else '', str(modp) if modp.exists() else ''])

md = [
    '# 正常版_修改版对照表',
    '',
    '更新时间：2026-05-02',
    '',
    '用途：上传前人工核对。正常版为 `新版/第N章.md`；修改版为 `待确认投稿/第N章改.txt`；不自动转正。',
    '',
    '| 章 | 正常版字数 | 修改版字数 | 已投稿TXT | 状态 | 外审 | 正常版路径 | 修改版路径 |',
    '|---|---:|---:|---|---|---|---|---|'
]
for r in rows:
    md.append('| {} | {} | {} | {} | {} | {} | {} | {} |'.format(*r))

out = proj / '审核记录' / '正常版_修改版对照表.md'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text('\n'.join(md) + '\n', encoding='utf-8')
print('tracking updated')
