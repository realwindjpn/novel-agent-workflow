#!/usr/bin/env python3
from pathlib import Path
import json, os, re, subprocess, sys, datetime

BASE = Path('/root/workspace/科武纪元')
SCRIPT = BASE / '工具脚本' / 'orchestrate_review.py'
OUTDIR = BASE / '审核记录' / '六角色外审'
RAW = OUTDIR / 'raw'
RAW.mkdir(parents=True, exist_ok=True)

ROLES = [
    ('editor', '编辑', '审结构/商业节奏/大纲对齐/章末钩子/投稿风险'),
    ('military', '军事顾问', '审战术动作/清剿边界/装备使用/交火可信度'),
    ('science', '科学顾问', '审技术动作/取证链/数据盘/哈希/权限/服务器可信度与科普可读性'),
    ('reader', '读者', '审看懂/顺/爽/AI味/是否想看下一章'),
]

NEG = ['FAIL','REVIEW_NEEDED','必改','硬伤','不宜进入','不能进入','重修','重写','不通过']
POS = ['PASS','通过','可上传','可以上传','想继续看','能进入下一章']


def fanqie_count(text):
    lines = [x for x in text.splitlines() if x.strip()]
    title = lines[0] if lines else ''
    return len(re.sub(r'\s+', '', text)) - len(re.sub(r'\s+', '', title))


def compact_evidence(ch):
    ev = BASE / '审核记录' / '证据包' / f'第{ch}章_证据包.md'
    if not ev.exists():
        subprocess.run(['python3', str(BASE/'工具脚本'/'build_review_evidence.py'), str(ch)], check=True, cwd='/root/workspace')
    txt = ev.read_text(encoding='utf-8', errors='ignore')
    # keep local preflight, task card, and tail/hook first
    parts = []
    for marker in ['## 本地预检', '## 任务卡摘录', '## 尾段行号', '## 证据地图：章末钩子', '## 证据地图：大纲锚点', '## 证据地图：技术动作', '## 证据地图：军事动作', '## 证据地图：投稿风险']:
        i = txt.find(marker)
        if i >= 0:
            j = txt.find('\n## ', i+4)
            if j < 0: j = len(txt)
            parts.append(txt[i:j])
    return ('\n\n'.join(parts))[:2600]


def judge(content):
    s = re.sub(r'<[^>]+>', '', content or '').strip()
    first = s.splitlines()[0].strip() if s.splitlines() else ''
    if any(x in s for x in NEG): return 'FAIL'
    if first.startswith('PASS') or any(x in s for x in POS): return 'PASS'
    return 'UNKNOWN'


def call(role, ch, prompt):
    p = subprocess.run(['python3', str(SCRIPT), '--role', role, '--chapter', str(ch), '--prompt', prompt], capture_output=True, text=True, timeout=260, cwd='/root/workspace')
    try:
        data = json.loads(p.stdout)
    except Exception:
        data = {'role': role, 'ok': False, 'content': p.stdout[-1000:] + p.stderr[-1000:]}
    return data


def main():
    chapters = [73, 74]
    summary = []
    for ch in chapters:
        file = BASE / '新版' / f'第{ch}章.md'
        text = file.read_text(encoding='utf-8')
        lines = [x for x in text.splitlines() if x.strip()]
        title = lines[0] if lines else ''
        last = lines[-1] if lines else ''
        fq = fanqie_count(text)
        evidence = compact_evidence(ch)
        chapter_results = []
        for role, zh, focus in ROLES:
            prompt = f'''角色:{zh}
任务:上传前复审第{ch}章《{title}》。只审核，不改文，不续写。
关注:{focus}
硬格式:第一行只写 PASS 或 FAIL。若有必改/硬伤/不宜上传，第一行必须 FAIL。第二行起:理由≤3条，小修≤3条。

本地硬检:
- 文件:{file}
- 番茄口径字数:{fq}
- 首行:{title}
- 末行:{last}

RTK证据包摘录:
{evidence}
'''
            data = call(role, ch, prompt)
            data['judgement'] = judge(data.get('content','')) if data.get('ok') else 'FAIL'
            raw_path = RAW / f'第{ch}_{role}_upload_recheck_{int(datetime.datetime.now().timestamp())}.json'
            raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            chapter_results.append((role, zh, data, raw_path))
        final = 'PASS' if all(d.get('ok') and d.get('judgement') == 'PASS' for _,_,d,_ in chapter_results) else 'FAIL'
        # append review record
        rec = OUTDIR / f'第{ch}章.md'
        old = rec.read_text(encoding='utf-8', errors='ignore') if rec.exists() else f'# 第{ch}章 六角色外审记录\n'
        block = ['','## 上传前6角色复审（2026-05-08）',f'- 文件：{file}',f'- 番茄口径字数：{fq}',f'- 首行：{title}',f'- 末行：{last}']
        for role, zh, data, raw_path in chapter_results:
            block.append(f'- {zh}：{data.get("provider")}/{data.get("model")} ok={data.get("ok")} 结论={data.get("judgement")} raw={raw_path.name}')
        block += ['', '## 上传前最终结论', final]
        rec.write_text(old.rstrip() + '\n' + '\n'.join(block) + '\n', encoding='utf-8')
        summary.append({'chapter': ch, 'file': str(file), 'fanqie_count': fq, 'title': title, 'last': last, 'final': final, 'roles': [{'role':r,'zh':z,'ok':d.get('ok'), 'provider':d.get('provider'), 'model':d.get('model'), 'judgement':d.get('judgement'), 'raw':str(raw)} for r,z,d,raw in chapter_results]})
    out = BASE / '审核记录' / '六角色外审' / '上传前复审_73_74_20260508.json'
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'summary': summary, 'summary_file': str(out)}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
