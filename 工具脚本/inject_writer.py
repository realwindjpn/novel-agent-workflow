#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 Cascade 本体(claude-opus-4-7-max-fast)写在 local_writer/seg{N}.md 的作家发言
注入到 raw + 重生成 segment_{N}_讨论记录.md(合并所有 raw 文件)。

用法:
  python3 inject_writer.py --segment 1
  python3 inject_writer.py --segment 2
  python3 inject_writer.py --segment 3
"""
from __future__ import annotations
import argparse, json, re, sys, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from meeting_v812_0513 import SEGMENTS, DATE, OUT, RAW  # noqa: E402

# 角色显示顺序(作家在首位)
ROLE_ORDER = ['writer', 'editor', 'reader', 'science', 'military']
ROLE_DISPLAY = {
    'writer':   '作家',
    'editor':   '编辑/结构',
    'reader':   '读者',
    'science':  '科学/技术',
    'military': '军事/制度',
}
WRITER_MODEL = 'claude-opus-4-7-max-fast (Cascade本体, 本地写入)'


def inject_writer(seg_id: int):
    local_path = OUT / 'local_writer' / f'seg{seg_id}.md'
    if not local_path.exists():
        raise SystemExit(f'缺少本地作家发言文件: {local_path}')
    content = local_path.read_text(encoding='utf-8').strip()
    cn = len(re.findall(r'[\u4e00-\u9fff]', content))
    res = {
        'ok': True, 'role': 'writer', 'display': '作家',
        'model': WRITER_MODEL,
        'elapsed': 0, 'content': content,
        'cn_chars': cn, 'tokens': 0,
        'source': 'local_writer',
        'written_at': datetime.datetime.now().isoformat(timespec='seconds'),
    }
    # 清掉旧 writer raw(避免重复)
    for old in RAW.glob(f'seg{seg_id}_writer_*.json'):
        old.unlink()
    out_raw = RAW / f'seg{seg_id}_writer_local.json'
    out_raw.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[seg{seg_id}] writer raw -> {out_raw} ({cn}中文字)')
    return res


def regen_segment_md(seg_id: int):
    """扫 raw/seg{N}_*.json 合并所有角色,按 ROLE_ORDER 排列,重写 segment_{N}_讨论记录.md"""
    seg = SEGMENTS[seg_id]
    # 收集每个角色最新的 raw
    by_role: dict[str, dict] = {}
    for fp in RAW.glob(f'seg{seg_id}_*.json'):
        try:
            d = json.loads(fp.read_text(encoding='utf-8'))
        except Exception as e:
            print(f'WARN: 解析失败 {fp.name}: {e}')
            continue
        rk = d.get('role')
        if not rk:
            continue
        # 取最新(按文件mtime)
        if rk not in by_role or fp.stat().st_mtime > by_role[rk].get('_mtime', 0):
            d['_mtime'] = fp.stat().st_mtime
            d['_src'] = fp.name
            by_role[rk] = d

    md = [
        f'# {seg["title"]} 讨论记录',
        '',
        f'时间: {datetime.datetime.now().isoformat(timespec="seconds")}',
        f'素材日期: {DATE}',
        f'聚焦: {seg["focus"]}',
        f'锚点章节: {seg["anchor_chapters"]}',
        '',
        '## 各模型发言',
        '',
    ]
    missing = []
    for rk in ROLE_ORDER:
        if rk not in by_role:
            missing.append(rk)
            md.append(f'### {ROLE_DISPLAY[rk]} · `(缺席)`')
            md.append('_未参与本段讨论_')
            md.append('')
            continue
        res = by_role[rk]
        display = res.get('display', ROLE_DISPLAY[rk])
        model = res.get('model', '?')
        md.append(f'### {display} · `{model}`')
        if res.get('ok'):
            elapsed = res.get('elapsed', 0)
            cn = res.get('cn_chars', 0)
            tokens = res.get('tokens', 0)
            src_hint = ' · 本地写入' if res.get('source') == 'local_writer' else ''
            md.append(f'_耗时 {elapsed}s · {cn}中文字 · {tokens} tokens{src_hint}_')
            md.append('')
            md.append(res.get('content', '').strip())
        else:
            md.append(f'**FAIL**: {res.get("error")}')
        md.append('')

    out_md = OUT / f'segment_{seg_id}_讨论记录.md'
    out_md.write_text('\n'.join(md), encoding='utf-8')
    print(f'[seg{seg_id}] regen -> {out_md} ({len(by_role)}/5 角色, 缺席: {missing})')
    return out_md, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True, help='1 | 2 | 3 | all')
    ap.add_argument('--regen-only', action='store_true', help='只重生成 md, 不重写 writer raw')
    args = ap.parse_args()
    todo = [1, 2, 3] if args.segment == 'all' else [int(args.segment)]
    for s in todo:
        if not args.regen_only:
            inject_writer(s)
        regen_segment_md(s)


if __name__ == '__main__':
    main()
