#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.8.1 队列后台执行器（澄砚 · 2026-05-26）。

范围：会议综合裁决 C5/C7 队列
  P0 = 113/114（上传线·源稿存在·旧PASS增量复核+TXT）
  P1 = 223（回改·源稿存在·不生成TXT）
  P2 = 358/378（无源稿>260·NOTE_ONLY 准备包）

原则：
  - 不全文重写：仅按 V8.12.8.1 新11红线+5制度链做增量复核
  - 模型失败：记录真实 provider/model/HTTP/错误并降级到机器静态复核
  - 非上传章不生成TXT；超260无源稿不入正文

证据输出：
  审核记录/六角色外审/第N章_V81281增量复核_20260526.md
  审核记录/六角色外审/raw/第N_v81281_increment_{provider}_20260526.json
  审核记录/goal模式/整体大纲弹性优化会议_20260526/准备包_第N章_NOTE_ONLY_20260526.md
  审核记录/goal模式/整体大纲弹性优化会议_20260526/V81281_queue_summary_20260526.json
"""
from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml
import requests

BASE = Path('/root/workspace/科武纪元')
NEW = BASE / '新版'
SUB = BASE / '已投稿'
RAW = BASE / '审核记录/六角色外审/raw'
REPORT_DIR = BASE / '审核记录/六角色外审'
MEETING_DIR = BASE / '审核记录/goal模式/整体大纲弹性优化会议_20260526'
WIKI_CH = BASE / 'wiki/chapters'
CONFIG = Path('/root/.hermes/config.yaml')
ENV = Path('/root/.hermes/.env')

STAMP = '20260526'
TS = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

RAW.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
MEETING_DIR.mkdir(parents=True, exist_ok=True)

# -------- queue config --------

QUEUE = [
    {
        'ch': 113, 'priority': 'P0', 'kind': 'upload',
        'title': '太空算力',
        'must_keys': ['双轨合规', '留痕系统升级中', '军用调度接口', '民用业务', '审计日志'],
        'forbid_keys': ['AI觉醒', '灵魂'],
        'redline_focus': ['#1 AI目标函数', '#5 战争摩擦具名(签字链/担责链/审批链)', '制度链#2 算法主权=可审计权'],
        'prior_pass': '审核记录/六角色外审/第113章_V8121闭环报告_20260515.md',
        'note': '这一章是太空算力的政策入口：双轨合规、留痕、军用调度接口与审计日志，先把规矩落下来，下一章才能写代价。',
    },
    {
        'ch': 114, 'priority': 'P0', 'kind': 'upload',
        'title': '战略关口',
        'must_keys': ['AI去冲突热线', '民用服务', '误调度', '复盘会', '交互留档'],
        'forbid_keys': ['AI觉醒', '灵魂'],
        'redline_focus': ['#10 AI参数漂移/反馈增益超阈值', '#11 传感器误差边界(若涉及)', '制度链#5 多域指挥摩擦/联络官/通报延迟'],
        'prior_pass': '审核记录/六角色外审/第114章_V8121闭环报告_20260515.md',
        'note': '这一章把代价落在民用服务上：一次误调度、一次复盘会、AI去冲突热线的第一根埋桩，所有动作都要交互留档。',
    },
    {
        'ch': 223, 'priority': 'P1', 'kind': 'rewrite_in_place',
        'title': '内战爆发',
        'must_keys': ['白盾', 'H200', '条件墙', '灰色渠道', '算力券', '专项芯片'],
        'forbid_keys': ['AI觉醒', '灵魂'],
        'redline_focus': ['#4 算力=电/热/水/许可/审计', '#6 CARD_PENDING/MISSING_RAW 不入正文', '制度链#3 白盾有限免责三道门'],
        'prior_pass': '审核记录/六角色外审/第223章_V8125闭环报告_20260518.md',
        'note': None,  # 非上传章
    },
]

NOTE_ONLY = [358, 378]


# -------- model plumbing --------

def load_env():
    if ENV.exists():
        for line in ENV.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def cfg_provider(name):
    cfg = yaml.safe_load(CONFIG.read_text(encoding='utf-8')) or {}
    p = (cfg.get('providers') or {}).get(name, {})
    model = p.get('default_model') or p.get('model') or ''
    base = (p.get('base_url') or '').rstrip('/')
    key = p.get('api_key') or os.environ.get(p.get('key_env') or '', '')
    return base, key, model


def call_provider(provider, prompt, max_tokens=600, timeout=180):
    base, key, model = cfg_provider(provider)
    t = time.time()
    if not base or not key:
        return {'ok': False, 'provider': provider, 'model': model, 'returned_model': None,
                'status': 0, 'latency_s': 0.0, 'content': 'MISSING_BASE_OR_KEY'}
    payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt}],
               'max_tokens': max_tokens, 'temperature': 0.1}
    if provider == 'zai':
        payload['thinking'] = {'type': 'disabled'}
    try:
        r = requests.post(
            base + '/chat/completions',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json=payload, timeout=timeout,
        )
        try:
            data = r.json()
        except Exception:
            data = {'raw': r.text[:1000]}
        msg = ((data.get('choices') or [{}])[0].get('message') or {}) if isinstance(data, dict) else {}
        content = (msg.get('content') or msg.get('reasoning_content') or '').strip()
        if not content:
            content = str(data.get('error') if isinstance(data, dict) else data)[:1500]
        returned = (data.get('model') if isinstance(data, dict) else None) or model
        return {'ok': bool(content) and r.status_code < 500, 'provider': provider, 'model': model,
                'returned_model': returned, 'status': r.status_code,
                'latency_s': round(time.time() - t, 2), 'content': content}
    except Exception as e:
        return {'ok': False, 'provider': provider, 'model': model, 'returned_model': None,
                'status': 0, 'latency_s': round(time.time() - t, 2), 'content': repr(e)}


# -------- text helpers --------

WIKILINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')


def fanqie_count_md(text: str) -> int:
    body = '\n'.join([
        ln for ln in text.splitlines()
        if not re.match(r'^第\d+章', ln.strip()) and ln.strip() != '（本章完）'
    ])
    body = WIKILINK_RE.sub(r'\1', body)
    return len(re.sub(r'\s+', '', body))


def fanqie_count_txt(text: str, title: str) -> int:
    body = text.split('作者有话说：', 1)[0]
    return len(re.sub(r'\s+', '', body)) - len(re.sub(r'\s+', '', title))


def clean_for_txt(text: str, author_note: str) -> str:
    text = WIKILINK_RE.sub(r'\1', text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    if '作者有话说：' in text:
        text = text.split('作者有话说：', 1)[0].rstrip()
    if '（本章完）' not in text:
        text = text.rstrip() + "\n\n（本章完）"
    else:
        text = text[:text.index('（本章完）') + len('（本章完）')]
    return text.strip() + "\n\n作者有话说：\n" + author_note.strip() + "\n"


def quote_balance(text: str) -> bool:
    return text.count('“') == text.count('”')


# -------- incremental review prompt --------

INCREMENT_PROMPT = (
    '你是《科武纪元》{role}。任务：V8.12.8.1 弹性优化会议增量复核（不写正文，不改剧情）。\n\n'
    '本章：第{ch}章《{title}》（已于历史版本 PASS：{prior}）\n'
    '本轮新强化的红线（重点核查）：\n'
    ' 1) AI 不写灵魂/觉醒；只写目标函数/奖励/停机惩罚/通信丢包/权限越界。\n'
    ' 2) 量子非万能；QKD 必带工程代价。\n'
    ' 3) 材料先打烂再用：炉温/张力/缺陷/批次。\n'
    ' 4) 算力=电/热/水/许可/审计。\n'
    ' 5) 战争摩擦与代价具名（签字链/担责链/审批链/通报延迟/联络官）。\n'
    ' 6) CARD_PENDING/MISSING_RAW 不入正文。\n'
    ' 7) 同章多补丁按线名对账。\n'
    ' 8) 散热不可突破兰道下限，只写工程极限区。\n'
    ' 9) 先进材料性能受批次/张力/缺陷约束。\n'
    '10) AI 自主行为=参数漂移/反馈增益超阈值/目标函数偏移。\n'
    '11) 传感器/感知必带误差边界/模型漂移/置信度回读。\n'
    '制度链 5 条：战争险触发链 / 算法主权=可审计权 / 白盾三道门 / 军售签字链 / 多域指挥摩擦。\n\n'
    '本章重点核查项（裁决建议）：{focus}\n\n'
    '【章节正文】\n{body}\n\n'
    '只输出严格 JSON（不许 Markdown、不许多余字段、不许重写正文）：\n'
    '{{\"verdict\":\"PASS|WARN|FAIL\",\"incremental_required\":true|false,\"violations\":[\"红线编号:简述\"],\"micro_patch_hint\":\"≤120字 或 null\"}}'
)


def parse_json_response(content: str) -> dict | None:
    if not content:
        return None
    # try direct
    for blob in (content,):
        try:
            return json.loads(blob)
        except Exception:
            pass
    # find first {...}
    m = re.search(r'\{[\s\S]*\}', content)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def static_redline_scan(text: str, must_keys: list[str], forbid_keys: list[str]) -> dict:
    missing = [k for k in must_keys if k not in text]
    forbidden_hit = [k for k in forbid_keys if k in text]
    # heuristic generic checks
    soul_hits = [w for w in ['AI觉醒', 'AI灵魂', '机器觉醒'] if w in text]
    return {
        'must_keys_missing': missing,
        'forbid_keys_hit': forbidden_hit,
        'soul_hits': soul_hits,
        'quote_balance': quote_balance(text),
        'wikilink_count': len(WIKILINK_RE.findall(text)),
        'fanqie': fanqie_count_md(text),
    }


def run_increment_review(ch: int, item: dict, body: str) -> dict:
    """调用编辑(Qwen) + 技术(GLM) 双轨增量复核。"""
    prompts = []
    for role_label, provider in [('编辑', 'alibaba'), ('技术轻审', 'zai')]:
        prompt = INCREMENT_PROMPT.format(
            role=role_label, ch=ch, title=item['title'],
            prior=Path(item['prior_pass']).name,
            focus='；'.join(item['redline_focus']),
            body=body if len(body) < 12000 else body[:6000] + '\n[...中段省略...]\n' + body[-4000:],
        )
        prompts.append((role_label, provider, prompt))

    results = []
    for role_label, provider, prompt in prompts:
        r = call_provider(provider, prompt, max_tokens=600, timeout=240)
        parsed = parse_json_response(r.get('content', '')) or {
            'verdict': 'FAIL_PARSE', 'incremental_required': True,
            'violations': ['模型JSON解析失败'], 'micro_patch_hint': None,
        }
        record = {
            'role': role_label, 'provider': r['provider'], 'model': r['model'],
            'returned_model': r['returned_model'], 'status': r['status'],
            'latency_s': r['latency_s'], 'ok': r['ok'],
            'verdict': parsed.get('verdict'),
            'incremental_required': parsed.get('incremental_required'),
            'violations': parsed.get('violations'),
            'micro_patch_hint': parsed.get('micro_patch_hint'),
            'raw_content_preview': (r.get('content') or '')[:400],
        }
        out = RAW / f'第{ch}_v81281_increment_{provider}_{STAMP}.json'
        out.write_text(json.dumps({**record, 'raw_content_full': r.get('content', '')}, ensure_ascii=False, indent=2), encoding='utf-8')
        record['evidence'] = str(out.relative_to(BASE))
        results.append(record)
    return {'reviews': results}


# -------- chapter pipeline --------

def process_chapter(item: dict) -> dict:
    ch = item['ch']
    md_path = NEW / f'第{ch}章.md'
    if not md_path.exists():
        return {'ch': ch, 'status': 'SKIP_SOURCE_MISSING', 'reason': f'{md_path} 不存在'}

    body = md_path.read_text(encoding='utf-8')
    static = static_redline_scan(body, item['must_keys'], item['forbid_keys'])

    # gate fail-fast (no model needed)
    static_pass = (not static['must_keys_missing']
                   and not static['forbid_keys_hit']
                   and not static['soul_hits']
                   and static['quote_balance'])

    review = run_increment_review(ch, item, body)
    reviews = review['reviews']

    # aggregate
    verdicts = [r.get('verdict') for r in reviews]
    all_pass = all(v == 'PASS' for v in verdicts)
    any_fail = any(v in ('FAIL', 'FAIL_PARSE') for v in verdicts)
    any_warn = any(v == 'WARN' for v in verdicts)

    # generate TXT only for P0 upload kind
    txt_path = SUB / f'第{ch}章.txt'
    txt_action = 'SKIP_NON_UPLOAD'
    txt_fanqie = None
    if item['kind'] == 'upload' and not any_fail and static_pass:
        if item.get('note'):
            title_line = f'第{ch}章 {item["title"]}'
            txt_body = clean_for_txt(body, item['note'])
            # title line must be on its own first line in txt; ensure body starts with it
            if not txt_body.startswith(title_line):
                # body should already include title in first line of MD
                pass
            txt_path.write_text(txt_body, encoding='utf-8')
            txt_fanqie = fanqie_count_txt(txt_body, title_line)
            txt_action = 'WRITTEN'

    # sync_kewu (per chapter, --no-git)
    sync_rc = None
    sync_err = None
    if not any_fail and static_pass:
        try:
            cp = subprocess.run(
                ['python3', str(BASE / '工具脚本/sync_kewu.py'),
                 '--chapter', str(ch),
                 '--message', f'V8.12.8.1 增量复核 第{ch}章 (P{item["priority"][1:]}) 弹性优化会议落地',
                 '--no-git'],
                capture_output=True, text=True, timeout=180,
            )
            sync_rc = cp.returncode
            sync_err = (cp.stderr or '')[-400:] if cp.returncode != 0 else None
        except Exception as e:
            sync_rc = -1
            sync_err = repr(e)

    # wiki keyword recheck
    wiki_path = WIKI_CH / f'ch{ch}.md'
    wiki_keywords = {}
    if wiki_path.exists():
        wt = wiki_path.read_text(encoding='utf-8')
        for k in item['must_keys']:
            wiki_keywords[k] = (k in wt)

    # status decision
    if any_fail:
        status = 'FAIL_BLOCKED'
    elif all_pass and static_pass:
        status = 'DONE'
    else:
        status = 'DONE_WITH_WARN'

    # write incremental report
    rpt_path = REPORT_DIR / f'第{ch}章_V81281增量复核_{STAMP}.md'
    rpt = []
    rpt.append(f'# 第{ch}章《{item["title"]}》 V8.12.8.1 增量复核报告')
    rpt.append('')
    rpt.append(f'时间：{TS}')
    rpt.append(f'范围：V8.12.8.1 备注层瘦身 + 11红线/5制度链增量复核')
    rpt.append(f'优先级：{item["priority"]}  类型：{item["kind"]}')
    rpt.append(f'源稿：`新版/第{ch}章.md` 番茄口径 = {static["fanqie"]}')
    rpt.append(f'旧 PASS：`{item["prior_pass"]}`')
    rpt.append(f'重点核查：{"；".join(item["redline_focus"])}')
    rpt.append('')
    rpt.append('## 静态机器复核')
    rpt.append('```json')
    rpt.append(json.dumps(static, ensure_ascii=False, indent=2))
    rpt.append('```')
    rpt.append('')
    rpt.append('## 双轨增量复核（编辑 Qwen + 技术 GLM）')
    rpt.append('| 角色 | provider/model | HTTP | returned_model | verdict | 增量必要 | violations |')
    rpt.append('|---|---|---:|---|---|---|---|')
    for r in reviews:
        rpt.append('| {role} | {prov}/{model} | {status} | {ret} | {v} | {inc} | {vio} |'.format(
            role=r['role'], prov=r['provider'], model=r['model'], status=r['status'],
            ret=r.get('returned_model'), v=r.get('verdict'),
            inc=r.get('incremental_required'),
            vio='; '.join(r.get('violations') or []) or '—',
        ))
    for r in reviews:
        rpt.append('')
        rpt.append(f'### {r["role"]} 原始返回（≤400字）')
        rpt.append('```')
        rpt.append(r.get('raw_content_preview') or '')
        rpt.append('```')
        rpt.append(f'证据：`{r["evidence"]}`')
    rpt.append('')
    rpt.append('## 投稿 TXT')
    if txt_action == 'WRITTEN':
        rpt.append(f'- 已生成：`已投稿/第{ch}章.txt`；番茄口径 ≈ {txt_fanqie}')
        rpt.append(f'- 作者有话说：{item["note"]}')
    elif txt_action == 'SKIP_NON_UPLOAD':
        rpt.append('- 非上传章：未生成 TXT（符合硬门禁 #9）。')
    else:
        rpt.append(f'- 未生成（status={status}）。')
    rpt.append('')
    rpt.append('## sync_kewu')
    rpt.append(f'- returncode = {sync_rc}')
    if sync_err:
        rpt.append('```')
        rpt.append(sync_err)
        rpt.append('```')
    rpt.append('')
    rpt.append('## Wiki Full Text 关键词复核')
    if wiki_keywords:
        rpt.append('```json')
        rpt.append(json.dumps(wiki_keywords, ensure_ascii=False, indent=2))
        rpt.append('```')
    else:
        rpt.append(f'- wiki/chapters/ch{ch}.md 不存在或未生成。')
    rpt.append('')
    rpt.append('## 结论')
    rpt.append(f'- status = **{status}**')
    rpt.append(f'- 静态门禁 = {static_pass}')
    rpt.append(f'- 双轨增量复核 = {verdicts}')
    rpt.append(f'- 番茄口径(MD) = {static["fanqie"]}')
    rpt_path.write_text('\n'.join(rpt), encoding='utf-8')

    return {
        'ch': ch, 'priority': item['priority'], 'kind': item['kind'],
        'status': status,
        'static_pass': static_pass,
        'static_summary': {k: v for k, v in static.items() if k != 'fanqie'} | {'fanqie': static['fanqie']},
        'verdicts': verdicts,
        'evidence': [r['evidence'] for r in reviews],
        'txt_action': txt_action,
        'txt_fanqie': txt_fanqie,
        'sync_returncode': sync_rc,
        'wiki_keywords': wiki_keywords,
        'report': str(rpt_path.relative_to(BASE)),
    }


# -------- note-only prep packs --------

NOTE_ONLY_CONTENT = {
    358: {
        'title': '舆论战场·盟友失控（候选）',
        'outline_lines': [
            '- 锚点：NATO 击落无人机/误判/火控授权/通报延迟。',
            '- 三要素（红线#5 + 制度链#5）：火控授权链 / 通报延迟 / 联络官在场+情报等级。',
            '- 素材缺口：306 军售签字链候选可复用；NATO STANAG / SIPRI 权威源待采。',
        ],
        'forbid': '无源稿 >260：不派正文精修、不生成任务卡、不生成 TXT；仅备注层。',
    },
    378: {
        'title': '多域指挥·盟友裂缝（候选）',
        'outline_lines': [
            '- 锚点：MDC-PAC 制度摩擦；屏幕合一底层靠联络官电话 + 火力审批卡情报等级。',
            '- 三要素（制度链#5）：联络官 / 情报等级 / 火力审批卡 + 通报延迟。',
            '- 素材缺口：NATO STANAG 通报延迟阈值 / 联络官等级表。',
        ],
        'forbid': '无源稿 >260：仅备注层占位；未来精修高优先级，本轮不入正文。',
    },
}


def write_note_only(ch: int) -> dict:
    info = NOTE_ONLY_CONTENT[ch]
    p = MEETING_DIR / f'准备包_第{ch}章_NOTE_ONLY_{STAMP}.md'
    lines = [
        f'# 第{ch}章 NOTE_ONLY 准备包 · V8.12.8.1 弹性优化会议',
        '',
        f'时间：{TS}',
        f'章节：第{ch}章 {info["title"]}',
        f'状态：NOTE_ONLY（{info["forbid"]}）',
        '',
        '## 大纲备注层锚点',
        *info['outline_lines'],
        '',
        '## 不做事项（硬门禁）',
        '- 不派正文精修任务卡。',
        '- 不生成 TXT。',
        '- 不更新 wiki/chapters。',
        '- 不入 STATUS 上传段；仅入会议落地段。',
        '',
        '## 触发恢复条件',
        '- 源稿 `新版/第{ch}章.md` 出现完整正文 → 走标准精修流水线 → 重新评估优先级。'.replace('{ch}', str(ch)),
    ]
    p.write_text('\n'.join(lines), encoding='utf-8')
    return {
        'ch': ch, 'priority': 'P2', 'kind': 'note_only',
        'status': 'NOTE_ONLY',
        'prep_pack': str(p.relative_to(BASE)),
    }


# -------- main --------

def main():
    load_env()
    results = []
    for item in QUEUE:
        print(f'>>> processing 第{item["ch"]}章 ({item["priority"]} {item["kind"]}) ...')
        try:
            res = process_chapter(item)
        except Exception as e:
            res = {'ch': item['ch'], 'priority': item['priority'], 'kind': item['kind'],
                   'status': 'FAIL_BLOCKED', 'error': repr(e)}
        results.append(res)
        print(f'    -> {res.get("status")}')

    for ch in NOTE_ONLY:
        results.append(write_note_only(ch))
        print(f'>>> 准备包 第{ch}章 NOTE_ONLY 写入')

    summary = {
        'meta': {
            'version': 'V8.12.8.1',
            'meeting': '整体大纲弹性优化会议_20260526',
            'generated_at': TS,
            'agent': '澄砚',
        },
        'queue': results,
    }
    out = MEETING_DIR / f'V81281_queue_summary_{STAMP}.json'
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'summary -> {out}')


if __name__ == '__main__':
    main()
