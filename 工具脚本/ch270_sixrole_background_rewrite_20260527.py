#!/usr/bin/env python3
import json, os, re, subprocess, sys, time
from datetime import datetime
from pathlib import Path

ROOT = Path('/root/workspace/科武纪元')
OUT_DIR = ROOT / '审核记录/六角色外审'
QUEUE_DIR = ROOT / '审核记录/新卷写作队列'
RAW_DIR = OUT_DIR / 'raw/ch270_sixrole_rewrite_20260527'
RAW_DIR.mkdir(parents=True, exist_ok=True)
EVENTS = QUEUE_DIR / 'events_270_sixrole_rewrite_20260527.jsonl'
CANDIDATE = OUT_DIR / '第270章_MiMoPro重写候选_20260527.md'
REPORT = OUT_DIR / '第270章_MiMoPro六角色重写报告_20260527.md'

ROUTES = {
    'author': ('xiaomi', 'mimo-v2.5-pro'),
    'editor': ('custom:WF', 'claude-opus-4-7-high-fast'),
    'reader': ('alibaba', 'qwen3.6-plus'),
    'advisor': ('zai', 'glm-5.1'),
    'fallback_repair': ('custom:WF', 'claude-opus-4-7-high-fast'),
}

BAD_WORDS = ['微微', '意味着', '仿佛', '像是某种', '命运', '史诗', '灵魂', '本段完', 'omitted', 'truncated', 'diff --git']

def emit(event, status='RUNNING', msg='', **kw):
    rec = {'ts': datetime.now().isoformat(timespec='seconds'), 'chapter': 270, 'event': event, 'status': status, 'msg': msg}
    rec.update(kw)
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open('a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

def read(path, limit=None):
    s = Path(path).read_text(encoding='utf-8', errors='ignore')
    return s if limit is None else s[:limit]

def fanqie_count(text):
    lines = text.strip().splitlines()
    title = lines[0].strip() if lines else ''
    body = re.sub(r'\s+', '', text)
    return len(body) - len(re.sub(r'\s+', '', title))

def run_model(role, prompt, timeout=1800):
    provider, model = ROUTES[role]
    cmd = ['hermes', 'chat', '-Q', '--provider', provider, '-m', model, '-q', prompt, '--max-turns', '40', '--source', 'kewu-sixrole-runner']
    t0 = time.time()
    emit(role.upper() + '_START', msg=f'{provider}/{model}')
    p = subprocess.run(cmd, cwd='/root/workspace', text=True, capture_output=True, timeout=timeout)
    dur = round(time.time() - t0, 2)
    out = (p.stdout or '').strip()
    err = (p.stderr or '').strip()
    (RAW_DIR / f'{role}_stdout.md').write_text(out, encoding='utf-8')
    (RAW_DIR / f'{role}_stderr.txt').write_text(err, encoding='utf-8')
    emit(role.upper() + '_DONE' if p.returncode == 0 else role.upper() + '_FAIL',
         status='RUNNING' if p.returncode == 0 else 'FAILED', msg=f'exit={p.returncode} dur={dur}',
         provider=provider, model=model, duration=dur, raw=str(RAW_DIR / f'{role}_stdout.md'))
    return p.returncode, out, err, dur, provider, model

def extract_chapter(text):
    # Prefer fenced or direct chapter from first occurrence.
    m = re.search(r'(第270章[\s\S]+?（本章完）)', text)
    if m:
        return m.group(1).strip()
    m = re.search(r'(第270章[\s\S]+)', text)
    if m:
        return m.group(1).strip()
    return text.strip()

def verdict(text):
    head = text[:1200]
    if re.search(r'结论[:：]\s*PASS|\bPASS\b|通过', head, re.I) and not re.search(r'结论[:：]\s*FAIL|\bFAIL\b|不通过', head, re.I):
        return 'PASS'
    if re.search(r'结论[:：]\s*FAIL|\bFAIL\b|不通过|必须回炉', head, re.I):
        return 'FAIL'
    return 'UNKNOWN'

emit('INIT', msg='MiMo author + Qwen editor/reader + ZAI advisor six-role rewrite')

prev269 = read(ROOT / '新版/第269章.md', 12000)
old270 = read(ROOT / '新版/第270章.md', 18000)
fail_report = read(OUT_DIR / '第270章_闭环报告_20260526.md', 12000)
writer_core = read('/root/workspace/写作角色OS/writer_role_core.md', 6000)
exp_rules = read('/root/workspace/写作角色OS/experience_distillation_rules.md', 6000)
author_patch = read(ROOT / '参考资料/作家风格OS/author_prompt_patch.md', 6000)

base_constraints = '''
《科武纪元》第270章重写。只输出正文候选，不解释。
标题固定：第270章 第三次校验
番茄口径≥3000，建议4500-6500。非上传章。末尾必须（本章完）。
清洁正文：无wikilink、无Markdown、无“本段完”、无diff/omitted/truncated。
风格：动作链、物理反馈、感官数据、真实压力；禁空泛比喻/咏叹调/解释腔。
必须承接269章，270只完成“第三次校验”，章末引出271，不抢写后续。
三证据链：签名同源、握手语法响应、上下文移动/主动索引或等价第三证。
数值硬约束：400km单程约1.3ms，往返约2.6ms；处理延迟另算。中心温度不可回跳；制冷只压外壁/扩大温差。传输百分比、剩余时间、震动间隔、制冷档位必须可对账。不要写“不到一小时”与“至少45分钟”互相打架。
人物硬约束：林星辰承担签字/窗口压力；方宁有判断不是报数机；赵大山/谭正和有动作和立场。
'''

author_prompt = f'''
你是《科武纪元》作者模型。按作家风格OS重写第270章完整正文。

{base_constraints}

【作家OS】\n{writer_core}\n\n【经验蒸馏】\n{exp_rules}\n\n【科武作家补丁】\n{author_patch}\n
【上一章269】\n{prev269}\n
【旧270失败稿，只作反例/设定来源】\n{old270}\n
【270失败报告，必须规避】\n{fail_report}\n
只输出正文，从“第270章 第三次校验”开始，到“（本章完）”结束。
'''

code, out, err, dur, provider, model = run_model('author', author_prompt, timeout=2400)
if code != 0:
    emit('BLOCKED', status='FAILED', msg='author failed', stderr=err[:500])
    REPORT.write_text(f'# 第270章六角色重写报告\n\n结论：AUTHOR_FAIL\n\nprovider/model：{provider}/{model}\n\n错误：\n```\n{err[-2000:]}\n```\n', encoding='utf-8')
    sys.exit(1)

chapter = extract_chapter(out)
count = fanqie_count(chapter)
bans = [w for w in BAD_WORDS if w in chapter]
bad_end = not chapter.strip().endswith('（本章完）')
if not chapter.startswith('第270章'):
    chapter = '第270章 第三次校验\n\n' + chapter
if bad_end:
    emit('MACHINE_GATE_FAIL', status='FAILED', msg='BAD_END', fanqie_count=count, bans=bans)
else:
    emit('MACHINE_GATE', msg='PASS' if count >= 3000 and not bans else 'FAIL', fanqie_count=count, bans=bans)

CANDIDATE.write_text(chapter, encoding='utf-8')

review_context = f'''
你要审《科武纪元》第270章候选稿。必须给首行“结论：PASS/FAIL”。若FAIL，列必改≤3。
重点：数值链自洽、人物不是报数机、三证据链清楚、无AI味、无截断/格式污染。

【失败报告】\n{fail_report[:8000]}\n
【候选正文】\n{chapter}
'''

editor_prompt = '你是编辑。查结构、商业节奏、大纲对齐、数值链叙事可读性。' + review_context
reader_prompt = '你是普通追读读者。查是否想继续读、疲劳点、AI味、人物是否有真实压力。' + review_context
advisor_prompt = '你是科学+军事顾问。查400km光程、SHA-256论证、温度/制冷/震动/传输数值、三舰轨道/指挥链可信度。' + review_context

_, editor_out, _, ed_dur, ed_provider, ed_model = run_model('editor', editor_prompt, timeout=1200)
_, reader_out, _, rd_dur, rd_provider, rd_model = run_model('reader', reader_prompt, timeout=1200)
_, advisor_out, _, ad_dur, ad_provider, ad_model = run_model('advisor', advisor_prompt, timeout=1200)

v_editor = verdict(editor_out)
v_reader = verdict(reader_out)
v_advisor = verdict(advisor_out)
final = 'FULL_REWRITE_CANDIDATE_PASS' if (count >= 3000 and not bans and not bad_end and v_editor == v_reader == v_advisor == 'PASS') else 'REVIEW_FAIL'

report = f'''# 第270章 MiMoPro六角色重写报告

时间：{datetime.now().isoformat(timespec='seconds')}
结论：{final}
边界：候选稿已生成；未覆盖正式 `新版/第270章.md`；未生成TXT；未上传；未commit。

## 路由
- 作者：{provider}/{model}，duration={dur}s
- 编辑：{ed_provider}/{ed_model}，duration={ed_dur}s，结论={v_editor}
- 读者：{rd_provider}/{rd_model}，duration={rd_dur}s，结论={v_reader}
- 科学/军事顾问：{ad_provider}/{ad_model}，duration={ad_dur}s，结论={v_advisor}

## 机器门禁
- 番茄口径：{count}
- 禁词/坏标记：{bans}
- 末尾格式：{'PASS' if not bad_end else 'FAIL'}
- 候选稿：`{CANDIDATE}`
- raw目录：`{RAW_DIR}`

## 数值链自检表
- 400km光程：单程约1.3ms，往返约2.6ms；处理延迟另算。
- 温度：中心温度不可回跳；制冷压外壁，温差扩大。
- 传输：百分比/剩余时间不可互相打架。
- 震动：间隔变化须显式样本或说明粗估。
- 证据：签名同源 + 握手语法 + 上下文移动/主动索引。

## 编辑复审
{editor_out}

## 读者复审
{reader_out}

## 科学/军事顾问复审
{advisor_out}
'''
REPORT.write_text(report, encoding='utf-8')
emit('DONE' if final.endswith('PASS') else 'REVIEW_FAIL', status=final, msg=final, fanqie_count=count, report_path=str(REPORT), candidate_path=str(CANDIDATE), editor=v_editor, reader=v_reader, advisor=v_advisor)
print(json.dumps({'final': final, 'candidate': str(CANDIDATE), 'report': str(REPORT), 'fanqie_count': count, 'editor': v_editor, 'reader': v_reader, 'advisor': v_advisor}, ensure_ascii=False))
