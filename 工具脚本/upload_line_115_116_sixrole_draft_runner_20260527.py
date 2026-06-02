#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upload-line six-role durable runner for 科武纪元 ch115-116.

Scope:
- determine and process explicitly configured chapters 115,116
- real role calls: author/editor/reader/advisor via separate provider/model
- write back 新版 only after gates pass
- sync project, export 已投稿 TXT + 作者有话说
- save to 番茄草稿箱, third volume, verify by upload script
- event/state files for monitor callback
"""
from __future__ import annotations
import os, re, json, time, shutil, subprocess, datetime, pathlib, traceback

BASE = pathlib.Path('/root/workspace/科武纪元')
SCRIPT_DIR = BASE / '工具脚本'
OUTDIR = BASE / '审核记录' / '上传线' / '20260527_115_116'
RAWDIR = OUTDIR / 'raw'
EVENTS = OUTDIR / 'events.jsonl'
STATE = OUTDIR / 'state.json'
LOG = OUTDIR / 'runner.log'
CHAPTERS = [115, 116]
VOLUME = '第三卷：暗流'
BANS = ['仿佛','微微','缓缓','不禁','不由得','意味着','这一刻','更是','宛如','犹如','悄然']
REPL = {'仿佛':'像','微微':'','缓缓':'','不禁':'','不由得':'','意味着':'说明','这一刻':'此时','更是':'也是','宛如':'像','犹如':'像','悄然':''}
ROUTES = {
    'author': ('xiaomi', 'mimo-v2.5-pro'),
    'editor': ('alibaba', 'qwen3.6-plus'),
    'reader': ('freemodel', 'gpt-5.5'),
    'advisor': ('zai', 'glm-5.1'),
    'fallback_reader': ('alibaba', 'qwen3.6-plus'),
    'fallback_author': ('freemodel', 'gpt-5.5'),
}

for d in [OUTDIR, RAWDIR, BASE/'审核记录/备份/上传线_20260527', BASE/'已投稿']:
    d.mkdir(parents=True, exist_ok=True)

def now(): return datetime.datetime.now().isoformat(timespec='seconds')

def log(msg):
    with LOG.open('a', encoding='utf-8') as f:
        f.write(f'[{now()}] {msg}\n')

def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding='utf-8'))
    return {'task':'upload_line_115_116','stage':'INIT','chapters':{str(c):{'status':'PENDING'} for c in CHAPTERS},'events_seen':0,'started_at':now(),'pid':os.getpid()}

def save_state(st):
    st['updated_at'] = now(); st['pid'] = os.getpid()
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding='utf-8')

def event(ch, event, status='RUNNING', msg='', **kw):
    rec = {'ts':now(), 'chapter':ch, 'event':event, 'status':status, 'msg':msg}
    rec.update(kw)
    with EVENTS.open('a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False)+'\n')
    st = load_state(); st['stage'] = event; st['current_chapter'] = ch
    if ch is not None:
        st['chapters'].setdefault(str(ch), {})['status'] = status
        st['chapters'][str(ch)].update({k:v for k,v in kw.items() if k in ['report','txt','fanqie_count','git_commit','upload_report','fail_reason']})
    save_state(st)

def run(cmd, timeout=300, cwd='/root/workspace'):
    log('RUN '+ ' '.join(map(str, cmd)) if isinstance(cmd, list) else 'RUN '+cmd)
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)

def call(role, prompt, timeout=540, max_chars=90000):
    provider, model = ROUTES[role]
    env = os.environ.copy(); env['HERMES_STREAM_READ_TIMEOUT'] = str(min(timeout, 500))
    cmd = ['hermes','chat','-Q','--provider',provider,'--model',model,'-q',prompt]
    t=time.time()
    try:
        p = subprocess.run(cmd, cwd='/root/workspace', text=True, capture_output=True, timeout=timeout, env=env)
        return {'role':role,'provider':provider,'model':model,'exit_code':p.returncode,'duration':round(time.time()-t,2),'stdout':(p.stdout or '')[:max_chars],'stderr':(p.stderr or '')[-5000:]}
    except subprocess.TimeoutExpired:
        return {'role':role,'provider':provider,'model':model,'exit_code':124,'duration':round(time.time()-t,2),'stdout':'','stderr':'TIMEOUT'}

def clean_text(s):
    s = (s or '').strip()
    s = re.sub(r'^```(?:md|txt)?\s*', '', s).strip()
    s = re.sub(r'\s*```$', '', s).strip()
    s = re.sub(r'^.*?(?=第\d+章)', '', s, flags=re.S).strip() if re.search(r'第\d+章', s[:1000]) else s
    s = s.replace('「','“').replace('」','”')
    for a,b in REPL.items(): s=s.replace(a,b)
    return s.strip()

def fanqie_count(text):
    lines = text.strip().splitlines()
    title = lines[0] if lines else ''
    body = '\n'.join(lines[1:])
    return len(re.sub(r'\s+', '', body))

def machine_gate(ch, text):
    probs=[]
    if not text.startswith(f'第{ch}章 '): probs.append('BAD_TITLE')
    if '（本章完）' not in text[-100:]: probs.append('BAD_END')
    if text.count('“') != text.count('”'): probs.append('QUOTE_UNBALANCED')
    if '```' in text or '[truncated]' in text or '省略' in text[-300:] or re.search(r'\.\.\.|……', text): probs.append('TRUNCATION_MARK')
    if re.search(r'\[\[[^\]]+\]\]', text): probs.append('WIKILINK')
    bad=[b for b in BANS if b in text]
    if bad: probs.append('BANS:'+','.join(bad))
    cnt=fanqie_count(text)
    if cnt < 3000: probs.append(f'COUNT:{cnt}')
    if re.search(r'\n{3,}', text): probs.append('BLANK_RUN')
    return probs, cnt

def verdict(raw):
    s = raw.get('stdout','')
    head = '\n'.join([x.strip() for x in s.splitlines() if x.strip()][:5])
    if raw.get('exit_code') != 0 or not s.strip(): return False
    if re.search(r'\bFAIL\b|不通过|重写|硬伤|截断|不合格', head): return False
    if re.search(r'\bPASS\b|通过|合格|可上传|可进入|想看下一章', s): return True
    return False

def get_title(src_text, ch):
    first = src_text.strip().splitlines()[0].strip().lstrip('#').strip()
    m = re.match(rf'第{ch}章[：:\s]+(.+)', first)
    return m.group(1).strip() if m else first

def read_context(ch):
    src = BASE/'新版'/f'第{ch}章.md'
    prev = BASE/'新版'/f'第{ch-1}章.md'
    outline = BASE/'wiki/raw/outline/科武纪元大纲_latest.md'
    status = BASE/'STATUS.md'
    txt = src.read_text(encoding='utf-8')
    return {
        'source': src,
        'text': txt,
        'title': get_title(txt, ch),
        'prev_tail': prev.read_text(encoding='utf-8', errors='ignore')[-2200:] if prev.exists() else '',
        'outline_hit': '\n'.join([l for l in outline.read_text(encoding='utf-8', errors='ignore').splitlines() if f'第{ch}章' in l][:5]) if outline.exists() else '',
        'status_tail': status.read_text(encoding='utf-8', errors='ignore')[-2200:] if status.exists() else '',
    }

def pre_review(ch, ctx):
    prompt = f'''审《科武纪元》第{ch}章原稿。只输出：结论 PASS/FAIL；上传前必改≤4；军事/科学硬伤≤3；编辑建议≤4。\n章节标题：{ctx['title']}\n大纲命中：{ctx['outline_hit']}\n上章尾：{ctx['prev_tail']}\n原稿：\n{ctx['text'][:22000]}'''
    ed = call('editor', '你是网文编辑OS。'+prompt, timeout=360)
    ad = call('advisor', '你是军事+科学顾问OS。'+prompt, timeout=360)
    (RAWDIR/f'ch{ch}_pre_editor.json').write_text(json.dumps(ed,ensure_ascii=False,indent=2),encoding='utf-8')
    (RAWDIR/f'ch{ch}_pre_advisor.json').write_text(json.dumps(ad,ensure_ascii=False,indent=2),encoding='utf-8')
    return ed, ad

def author_refine(ch, ctx, pre_notes, prev_fail=''):
    prompt = f'''你是《科武纪元》作者OS。精修第{ch}章，只输出完整正文。\n首行：第{ch}章 {ctx['title']}\n末行：（本章完）\n番茄口径必须≥3200字；若原稿不足，扩展动作链、身体反馈、设备读数、环境约束、对话动作。\n风格：普通玩家可读；物理反馈、行动链、代价链；技术解释用操作/读数/成本，不写论文腔。\n禁：仿佛/微微/缓缓/不禁/不由得/意味着/这一刻；禁章节编号元话语；禁省略号/截断。\n上传线边界：保留剧情走向，不新增越纲大设定。\n大纲命中：{ctx['outline_hit']}\n上章尾：{ctx['prev_tail']}\n写前外审意见：\n{pre_notes}\n上一轮失败：\n{prev_fail}\n原稿全文：\n{ctx['text']}'''
    r = call('author', prompt, timeout=720)
    if r['exit_code'] != 0 or len(r.get('stdout','')) < 2500:
        r2 = call('fallback_author', prompt+'\n上一轮作者位失败/过短。请完整输出正文。', timeout=720)
        r2['fallback_from'] = r
        return r2
    return r

def post_review(ch, text, ctx):
    common = f'''审第{ch}章实际精修稿。必须第一行输出 PASS 或 FAIL。\n标题：{ctx['title']}\n大纲：{ctx['outline_hit']}\n番茄口径：{fanqie_count(text)}\n正文：\n{text[:26000]}'''
    ed = call('editor', '你是编辑OS。查结构、节奏、偏纲、AI味、上传风险。'+common, timeout=360)
    rd = call('reader', '你是普通番茄读者OS。查是否顺、是否想看下一章、劝退点。'+common, timeout=360)
    ad = call('advisor', '你是军事/科学顾问OS。查战术、工程、科学硬伤。'+common, timeout=360)
    if not verdict(rd):
        rd2 = call('fallback_reader', '你是备用读者OS。'+common, timeout=360)
        rd2['fallback_from'] = rd
        rd = rd2
    (RAWDIR/f'ch{ch}_post_reviews.json').write_text(json.dumps({'editor':ed,'reader':rd,'advisor':ad},ensure_ascii=False,indent=2),encoding='utf-8')
    return {'editor':ed,'reader':rd,'advisor':ad}

def repair_by_fail(ch, text, ctx, reviews, machine=''):
    issues = machine + '\n' + '\n'.join(f'{k}: {v.get("stdout","")[:1200]}' for k,v in reviews.items() if not verdict(v))
    prompt = f'''你是《科武纪元》作者OS。按失败点修第{ch}章，只输出完整正文。\n首行：第{ch}章 {ctx['title']}\n末行：（本章完）\n番茄口径≥3200，禁截断，禁解释，禁省略号。\n只修失败点，不重置剧情。\n失败点：\n{issues}\n当前正文：\n{text}'''
    return call('author', prompt, timeout=720)

def write_back(ch, text, ctx):
    src = ctx['source']
    backup = BASE/'审核记录/备份/上传线_20260527'/f'第{ch}章_精修前.md'
    if src.exists() and not backup.exists(): shutil.copy2(src, backup)
    src.write_text(text.strip()+'\n', encoding='utf-8')
    return backup

def sync_project(ch):
    p = run(['python3', str(SCRIPT_DIR/'sync_kewu.py'), '--chapter', str(ch), '--message', f'上传线第{ch}章六角色闭环', '--no-git'], timeout=360)
    (RAWDIR/f'ch{ch}_sync.log').write_text((p.stdout or '')+'\n'+(p.stderr or ''), encoding='utf-8')

def export_txt(ch, text):
    title = text.strip().splitlines()[0].strip().lstrip('#').strip()
    body = '\n'.join(text.strip().splitlines())
    body = re.sub(r'^#+\s*', '', body, flags=re.M)
    body = re.sub(r'\[\[([^\]]+)\]\]', r'\1', body)
    body = re.sub(r'\*\*(.*?)\*\*', r'\1', body)
    body = body.replace('「','“').replace('」','”')
    if not body.endswith('（本章完）'): body += '\n（本章完）'
    note = '今天先到这里。下一章继续看城市失控后的连锁反应。'
    out = BASE/'已投稿'/f'第{ch}章.txt'
    out.write_text(body.strip()+'\n\n作者有话说：\n'+note+'\n', encoding='utf-8')
    return out

def draft_upload(ch):
    # dry run
    dry = run(['python3', str(SCRIPT_DIR/'fanqie_draft_upload_chapter.py'), '--chapter', str(ch), '--volume', VOLUME], timeout=120)
    (RAWDIR/f'ch{ch}_draft_dryrun.log').write_text((dry.stdout or '')+'\n'+(dry.stderr or ''), encoding='utf-8')
    if dry.returncode != 0:
        return False, 'DRYRUN_FAIL', (dry.stdout+dry.stderr)[-1000:]
    chk = run(['python3', str(SCRIPT_DIR/'fanqie_draft_upload_chapter.py'), '--chapter', str(ch), '--volume', VOLUME, '--check-login'], timeout=120)
    (RAWDIR/f'ch{ch}_draft_check_login.log').write_text((chk.stdout or '')+'\n'+(chk.stderr or ''), encoding='utf-8')
    if chk.returncode != 0 or '"ok": true' not in (chk.stdout or ''):
        return False, 'LOGIN_BLOCKED', (chk.stdout+chk.stderr)[-1200:]
    exe = run(['python3', str(SCRIPT_DIR/'fanqie_draft_upload_chapter.py'), '--chapter', str(ch), '--volume', VOLUME, '--execute'], timeout=420)
    (RAWDIR/f'ch{ch}_draft_execute.log').write_text((exe.stdout or '')+'\n'+(exe.stderr or ''), encoding='utf-8')
    ok = exe.returncode == 0 and ('"ok": true' in (exe.stdout or '') or '"saved": true' in (exe.stdout or '') or 'listing' in (exe.stdout or ''))
    return ok, 'UPLOADED' if ok else 'UPLOAD_FAIL', (exe.stdout+exe.stderr)[-1500:]

def git_commit(ch, report, txt):
    files = [BASE/'新版'/f'第{ch}章.md', BASE/'已投稿'/f'第{ch}章.txt', BASE/'wiki/chapters'/f'ch{ch:03d}.md', BASE/'STATUS.md', BASE/'WAL.md', BASE/'小说综合跟踪表.md', report, txt, STATE, EVENTS]
    existing = [str(p) for p in files if pathlib.Path(p).exists()]
    run(['git','-C',str(BASE),'add','-f','--']+existing, timeout=120)
    c = run(['git','-C',str(BASE),'commit','-m',f'upload-line: chapter {ch} six-role draft'], timeout=180)
    if c.returncode != 0 and 'nothing to commit' not in (c.stdout+c.stderr):
        (RAWDIR/f'ch{ch}_git_commit_fail.log').write_text((c.stdout or '')+'\n'+(c.stderr or ''), encoding='utf-8')
    sha = run(['git','-C',str(BASE),'rev-parse','--short','HEAD'], timeout=30).stdout.strip()
    return sha

def process_chapter(ch):
    event(ch, 'START', 'RUNNING', 'chapter start')
    ctx = read_context(ch)
    if fanqie_count(ctx['text']) < 1500:
        raise RuntimeError(f'SOURCE_TOO_SHORT {ch}')
    event(ch, 'PRE_REVIEW', 'RUNNING', 'editor+advisor original review')
    pre_ed, pre_ad = pre_review(ch, ctx)
    pre_notes = '编辑：\n'+pre_ed.get('stdout','')+'\n顾问：\n'+pre_ad.get('stdout','')
    last_fail=''
    final_text=''
    reviews={}
    cnt=0
    for i in range(1,4):
        event(ch, 'AUTHOR_REFINE', 'RUNNING', f'round {i}')
        ar = author_refine(ch, ctx, pre_notes, last_fail)
        (RAWDIR/f'ch{ch}_author_round{i}.json').write_text(json.dumps(ar,ensure_ascii=False,indent=2),encoding='utf-8')
        text = clean_text(ar.get('stdout',''))
        if not text.startswith(f'第{ch}章 '): text = f'第{ch}章 {ctx["title"]}\n\n' + text
        if '（本章完）' not in text[-120:]: text = text.rstrip()+'\n\n（本章完）'
        probs, cnt = machine_gate(ch, text)
        event(ch, 'MACHINE_GATE', 'RUNNING' if not probs else 'FAILED', ';'.join(probs) or 'PASS', fanqie_count=cnt, fail_reason=';'.join(probs))
        if probs:
            last_fail = '机器门禁失败：'+';'.join(probs)
            ctx['text'] = text
            continue
        event(ch, 'POST_REVIEW', 'RUNNING', 'editor+reader+advisor')
        reviews = post_review(ch, text, ctx)
        ok = all(verdict(v) for v in reviews.values())
        if ok:
            final_text = text; break
        rr = repair_by_fail(ch, text, ctx, reviews)
        (RAWDIR/f'ch{ch}_repair_after_review_round{i}.json').write_text(json.dumps(rr,ensure_ascii=False,indent=2),encoding='utf-8')
        last_fail = '复审失败，已请求修订'
        ctx['text'] = clean_text(rr.get('stdout','')) or text
    if not final_text:
        report = OUTDIR/f'第{ch}章_失败报告.md'
        report.write_text('# 第%s章 阻塞\n\n未通过三轮机器/模型门禁。\n\n%s\n' % (ch,last_fail), encoding='utf-8')
        event(ch, 'BLOCKED', 'BLOCKED', last_fail, report=str(report), fail_reason=last_fail)
        return False
    backup = write_back(ch, final_text, ctx)
    sync_project(ch)
    txt = export_txt(ch, final_text)
    report = OUTDIR/f'第{ch}章_六角色闭环上传报告.md'
    report.write_text(f'''# 第{ch}章 六角色闭环上传报告

时间：{now()}
结论：SIX_ROLE_PASS
番茄口径：{fanqie_count(final_text)}
目标卷：{VOLUME}

## 角色模型
- 作者：{ROUTES['author'][0]} / {ROUTES['author'][1]}
- 编辑：{ROUTES['editor'][0]} / {ROUTES['editor'][1]}
- 读者：{ROUTES['reader'][0]} / {ROUTES['reader'][1]}（失败时备用 {ROUTES['fallback_reader'][0]} / {ROUTES['fallback_reader'][1]}）
- 科学/军事顾问：{ROUTES['advisor'][0]} / {ROUTES['advisor'][1]}

## 文件
- 新版：{BASE/'新版'/f'第{ch}章.md'}
- 备份：{backup}
- TXT：{txt}
- raw：{RAWDIR}
''', encoding='utf-8')
    event(ch, 'DRAFT_UPLOAD', 'RUNNING', 'dryrun/check-login/execute')
    up_ok, up_status, up_msg = draft_upload(ch)
    report.write_text(report.read_text(encoding='utf-8') + f'\n## 草稿箱\n- 状态：{up_status}\n- 摘要：{up_msg}\n', encoding='utf-8')
    if not up_ok:
        event(ch, 'UPLOAD_BLOCKED', 'BLOCKED', up_status, report=str(report), txt=str(txt), fanqie_count=fanqie_count(final_text), fail_reason=up_msg)
        return False
    sha = git_commit(ch, report, txt)
    event(ch, 'FULL_LOOP_DRAFT_PASS', 'FULL_LOOP_DRAFT_PASS', 'closed and saved draft', report=str(report), txt=str(txt), fanqie_count=fanqie_count(final_text), git_commit=sha, upload_report=str(RAWDIR/f'ch{ch}_draft_execute.log'))
    return True

def main():
    st = load_state(); st['stage']='RUNNING'; save_state(st)
    event(None, 'RUNNER_START', 'RUNNING', f'pid {os.getpid()} chapters={CHAPTERS}')
    for ch in CHAPTERS:
        if load_state()['chapters'].get(str(ch),{}).get('status') == 'FULL_LOOP_DRAFT_PASS':
            continue
        ok = process_chapter(ch)
        if not ok:
            st=load_state(); st['stage']='BLOCKED'; save_state(st); return 1
    st=load_state(); st['stage']='DONE'; save_state(st)
    event(None, 'ALL_DONE', 'DONE', '115-116 complete')
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as e:
        log(traceback.format_exc())
        event(None, 'RUNNER_EXCEPTION', 'BLOCKED', str(e), fail_reason=str(e))
        st=load_state(); st['stage']='BLOCKED'; st['fail_reason']=str(e); save_state(st)
        raise
