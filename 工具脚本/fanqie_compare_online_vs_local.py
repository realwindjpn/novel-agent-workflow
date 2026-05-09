#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare Fanqie online edit-page chapter text with local submitted TXT.
No LLM. Read-only browser automation. Requires agent-browser session fanqie.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re, subprocess, time
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher

PROJECT = Path('/root/workspace/科武纪元')
URLMAP = PROJECT / '审核记录/fanqie_chapter_url_map_20260507.json'
LOCAL_DIR = PROJECT / '已投稿'
OUT_BASE = PROJECT / '审核记录' / '线上正文对比'
BOOK_ID = '7628216044850531352'


def run_ab(args: list[str], timeout: int = 180) -> str:
    p = subprocess.run(['agent-browser', '--session-name', 'fanqie', *args], text=True, capture_output=True, timeout=timeout)
    out = (p.stdout + p.stderr).strip()
    return out


def ab_json(js: str, timeout: int = 180):
    out = run_ab(['eval', js], timeout=timeout)
    try:
        return json.loads(out)
    except Exception:
        return {'_raw': out}


def load_urlmap() -> dict[int, str]:
    data = json.loads(URLMAP.read_text(encoding='utf-8'))
    return {int(k): v for k, v in data.items()}


def local_path(ch: int) -> Path:
    return LOCAL_DIR / f'第{ch}章.txt'


def read_local(ch: int) -> str:
    p = local_path(ch)
    if not p.exists():
        return ''
    return p.read_text(encoding='utf-8-sig', errors='replace')


def split_local_title_body(text: str, ch: int) -> tuple[str, str]:
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and re.match(rf'^第\s*{ch}\s*章', lines[0].strip()):
        return lines[0].strip(), '\n'.join(lines[1:]).strip()
    return '', text.strip()


def clean_online_body(text: str) -> str:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Fanqie editor often appends this helper prompt inside edit DOM; it is not chapter text.
    text = re.sub(r'\n*暂时没有思路，使用AI续写试试？\s*$', '', text.strip())
    return text.strip()


def compact(text: str) -> str:
    text = clean_online_body(text)
    # Normalize quotes minimally; keep punctuation/content differences.
    text = text.replace('\ufeff', '')
    return re.sub(r'\s+', '', text)


def sha(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]


def fanqie_count(text: str, title: str = '') -> int:
    body = re.sub(r'\s+', '', text)
    t = re.sub(r'\s+', '', title)
    return max(0, len(body) - len(t))


def first_diff(a: str, b: str, width: int = 80) -> str:
    ca, cb = compact(a), compact(b)
    if ca == cb:
        return ''
    n = min(len(ca), len(cb))
    idx = 0
    while idx < n and ca[idx] == cb[idx]:
        idx += 1
    la = ca[max(0, idx-25): idx+width]
    lb = cb[max(0, idx-25): idx+width]
    return f'pos={idx}\nlocal: {la}\nonline:{lb}'


def fetch_online(ch: int, url: str) -> dict:
    run_ab(['open', url], timeout=240)
    run_ab(['wait', '3500'], timeout=30)
    # Old chapters may show continue-edit modal.
    ab_json("(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.innerText.includes('继续编辑')&&!b.disabled); if(b){b.click(); return true;} return false;})()", timeout=60)
    time.sleep(1.0)
    run_ab(['wait', '[contenteditable=true]'], timeout=120)
    data = ab_json(r"""
(()=>{
  const editables=[...document.querySelectorAll('[contenteditable=true]')].map((e,i)=>({i,text:e.innerText||'', html:(e.innerHTML||'').slice(0,500), cls:String(e.className)}));
  const inputs=[...document.querySelectorAll('input')].map((e,i)=>({i,value:e.value||'', cls:String(e.className)}));
  const buttons=[...document.querySelectorAll('button')].map((b,i)=>({i,text:b.innerText, disabled:b.disabled, visible:!!(b.offsetWidth||b.offsetHeight)})).filter(x=>x.visible).slice(0,30);
  const chapterNo = inputs.map(x=>x.value).find(v=>/^\d+$/.test(v||'')) || '';
  const titleInput = inputs.find(x=>x.value && !/^\d+$/.test(x.value) && x.value.length < 80)?.value || '';
  const body = editables[0]?.text || '';
  return {url:location.href, title:document.title, chapterNo, titleInput, body, bodyLen:body.length, editables:editables.slice(0,6), inputs:inputs.slice(0,12), buttons};
})()
""", timeout=120)
    if not isinstance(data, dict):
        data = {'_bad': str(data)}
    data['body'] = clean_online_body(data.get('body', '') or '')
    return data


def compare_one(ch: int, url: str, outdir: Path) -> dict:
    rec = {'chapter': ch, 'url': url}
    local_raw = read_local(ch)
    local_title, local_body = split_local_title_body(local_raw, ch)
    online = fetch_online(ch, url)
    online_body = online.get('body', '') or ''
    online_title = online.get('titleInput', '') or ''

    (outdir / 'online').mkdir(parents=True, exist_ok=True)
    (outdir / 'local_body').mkdir(parents=True, exist_ok=True)
    (outdir / 'online' / f'第{ch:03d}章_online.txt').write_text(online_body, encoding='utf-8')
    (outdir / 'local_body' / f'第{ch:03d}章_local_body.txt').write_text(local_body, encoding='utf-8')
    (outdir / 'raw' ).mkdir(parents=True, exist_ok=True)
    (outdir / 'raw' / f'第{ch:03d}章_page.json').write_text(json.dumps(online, ensure_ascii=False, indent=2), encoding='utf-8')

    lc, oc = compact(local_body), compact(online_body)
    status = 'same' if lc == oc else 'diff'
    if not local_raw:
        status = 'missing_local'
    if not online_body:
        status = 'missing_online'
    ratio = SequenceMatcher(None, lc, oc).ratio() if lc or oc else 0.0

    rec.update({
        'status': status,
        'local_title': local_title,
        'online_title': online_title,
        'title_ok': (online_title and online_title in local_title) or (local_title and local_title.endswith(online_title)),
        'local_chars_compact': len(lc),
        'online_chars_compact': len(oc),
        'local_fanqie_count': fanqie_count(local_raw, local_title),
        'online_fanqie_count': len(oc),
        'local_sha': sha(lc),
        'online_sha': sha(oc),
        'similarity': round(ratio, 6),
        'first_diff': first_diff(local_body, online_body),
        'page_chapter_no': online.get('chapterNo',''),
        'page_url': online.get('url',''),
    })
    return rec


def write_reports(records: list[dict], outdir: Path):
    json_path = outdir / 'compare_11_70.json'
    csv_path = outdir / 'compare_11_70.csv'
    md_path = outdir / 'compare_11_70_report.md'
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    fields = ['chapter','status','similarity','local_chars_compact','online_chars_compact','local_sha','online_sha','title_ok','local_title','online_title','first_diff','url']
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader(); w.writerows(records)
    diffs = [r for r in records if r['status'] != 'same']
    same = [r for r in records if r['status'] == 'same']
    lines = []
    lines.append('# 番茄线上正文 vs 本地已投稿 11-70 对比报告')
    lines.append('')
    lines.append(f'- 生成时间：{datetime.now().isoformat(timespec="seconds")}')
    lines.append('- 方法：agent-browser 只读打开番茄“修改章节”页，抽取第一个正文编辑器；本地读取 `已投稿/第X章.txt`；去空白后比对 SHA。')
    lines.append('- 未调用大模型。')
    lines.append('')
    lines.append(f'- 相同：{len(same)}章')
    lines.append(f'- 不同/缺失：{len(diffs)}章')
    lines.append('')
    lines.append('## 仍需上传修改（线上 != 本地已投稿）')
    lines.append('')
    if diffs:
        lines.append('、'.join(f"第{r['chapter']}章" for r in diffs))
    else:
        lines.append('无。')
    lines.append('')
    lines.append('## 明细')
    lines.append('')
    lines.append('|章|状态|相似度|本地字数|线上字数|标题|首处差异|')
    lines.append('|---:|---|---:|---:|---:|---|---|')
    for r in records:
        fd = (r.get('first_diff') or '').replace('\n','<br>').replace('|','｜')[:260]
        title = f"{r.get('local_title','')} / {r.get('online_title','')}".replace('|','｜')
        lines.append(f"|{r['chapter']}|{r['status']}|{r['similarity']:.4f}|{r['local_chars_compact']}|{r['online_chars_compact']}|{title}|{fd}|")
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    return {'json': str(json_path), 'csv': str(csv_path), 'md': str(md_path), 'diffs': [r['chapter'] for r in diffs], 'same': [r['chapter'] for r in same]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=11)
    ap.add_argument('--end', type=int, default=70)
    ap.add_argument('--sleep', type=float, default=0.3)
    args = ap.parse_args()
    outdir = OUT_BASE / datetime.now().strftime('%Y%m%d_%H%M%S')
    outdir.mkdir(parents=True, exist_ok=True)
    urls = load_urlmap()
    records = []
    for ch in range(args.start, args.end + 1):
        if ch not in urls:
            records.append({'chapter': ch, 'status': 'missing_url', 'url': ''})
            continue
        try:
            rec = compare_one(ch, urls[ch], outdir)
        except Exception as e:
            rec = {'chapter': ch, 'status': 'error', 'url': urls[ch], 'error': repr(e)}
        records.append(rec)
        print(json.dumps({k: rec.get(k) for k in ['chapter','status','similarity','local_chars_compact','online_chars_compact']}, ensure_ascii=False), flush=True)
        time.sleep(args.sleep)
    summary = write_reports(records, outdir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
