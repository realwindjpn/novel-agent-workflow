from pathlib import Path
import shutil, json, datetime
root=Path('/root/workspace/科武纪元')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
restore_report=[]
# Restore all content/title files from the first pre-change backup, excluding STATUS/WAL so correction history remains.
backup_dirs=[
    root/'审核记录/备份/章节标题落地_20260605_120751',
    root/'审核记录/备份/章节标题副本补丁_20260605_120942',
    root/'审核记录/备份/章节标题索引补漏_20260605_121034',
]
exclude={'STATUS.md','WAL.md'}
for b in backup_dirs:
    if not b.exists():
        continue
    for src in sorted(x for x in b.rglob('*') if x.is_file()):
        rel=src.relative_to(b)
        if str(rel) in exclude:
            continue
        dest=root/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src,dest)
        restore_report.append({'from':str(src),'to':str(dest)})
# Append correction note
note=f"\n\n### {stamp} 标题越界改动回滚\n- 已按用户纠偏回滚已写/已上传章节标题改动，恢复到标题落地前备份。\n- 原因：已写/已上传章节标题应冻结；后续只审大纲未来章，避免牵动番茄线上/已投稿镜像。\n- 本次仅恢复本地文件，不触碰番茄后台，不提交 Git。\n"
for name in ['STATUS.md','WAL.md']:
    p=root/name
    if p.exists():
        p.write_text(p.read_text(encoding='utf-8',errors='ignore')+note, encoding='utf-8')
report_path=root/'审核记录'/f'章节标题越界回滚报告_{stamp}.json'
report_path.write_text(json.dumps({'stamp':stamp,'restored_count':len(restore_report),'restored':restore_report},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'stamp':stamp,'report':str(report_path),'restored_count':len(restore_report)},ensure_ascii=False,indent=2))
