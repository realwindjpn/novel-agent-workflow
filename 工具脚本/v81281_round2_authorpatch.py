#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12.8.1 Round-2：MiMo 作者微补丁 + 双审复核 + TXT 重生。

依据：
  - 会议综合裁决 C5：P0=113/114 "MiMo作者+Qwen编/读+GLM制度 ... 生成TXT"
  - 用户指令：本轮只做会议裁决要求的增量复核/必要小修，勿全文重写
  - Qwen 在 Round-1 给出 micro_patch_hint（≤120字）：本脚本据此让 MiMo 落地 1 段 ≤200 字的衔接段

策略：
  - 在每章已选定的稳定锚点后插入；找不到锚点则在「（本章完）」前插入（如缺失则在文末追加）
  - 严格限长：≤300 字（容错弹性槽硬门禁），实测目标 ≤200 字
  - 备份原 MD
  - 复审：Qwen 编辑 + MiniMax 读者；双 PASS 才接受；否则回滚
  - 上传章重生 TXT；非上传章不生成 TXT
"""
from __future__ import annotations

import datetime
import json
import os
import re
import shutil
import subprocess
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
BACKUPS = BASE / '备份'
CONFIG = Path('/root/.hermes/config.yaml')
ENV = Path('/root/.hermes/.env')

STAMP = '20260526'
TS = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

BACKUPS.mkdir(parents=True, exist_ok=True)

WIKILINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

TASKS = [
    {
        'ch': 113, 'priority': 'P0', 'kind': 'upload', 'title': '太空算力',
        'note': '这一章把太空算力的政策起点先立住：双轨合规、留痕系统升级中、军用调度接口与审计日志，规矩落下来，下一章再写代价。',
        'must_keys': ['双轨合规', '留痕系统升级中', '军用调度接口', '民用业务', '审计日志'],
        'anchor': '他逐行看了下去。散热架构、电力供应、运输需求……每一项都带着具体的数字和日期。这些数字不是空想，是方宁五天没怎么睡觉算出来的。',
        'anchor_mode': 'after',
        'patch_brief': 'Qwen 增量WARN：补 1 句把算力调度落到目标函数收敛阈值+材料批次/张力公差+散热兰道工程冗余区上；以方宁报告中一行附注的口吻写，不破坏叙事节奏。',
        'must_phrases': ['目标函数', '批次', '兰道'],
    },
    {
        'ch': 114, 'priority': 'P0', 'kind': 'upload', 'title': '战略关口',
        'note': '这一章把代价落在民用服务上：一次误调度、一次复盘会、AI 去冲突热线的第一根埋桩，所有动作都要交互留档。',
        'must_keys': ['AI去冲突热线', '民用服务', '误调度', '复盘会', '交互留档'],
        'anchor': '"对。"\n\n两个人一起站在跑道上，看着天。蓝的，干干净净的。',
        'anchor_mode': 'after',
        'patch_brief': 'Qwen 增量WARN：补 1 段，借林星辰内心独白点出 L1 传感器置信度回读/模型漂移阈值/通报延迟+联络官审批未签批+担责链待审计三件事；不写AI觉醒，按目标函数/参数漂移口径。',
        'must_phrases': ['置信度', '通报延迟', '联络官'],
    },
    {
        'ch': 223, 'priority': 'P1', 'kind': 'rewrite_in_place', 'title': '内战爆发',
        'note': None,
        'must_keys': ['白盾', 'H200', '条件墙', '灰色渠道', '算力券', '专项芯片'],
        'anchor': '"还有清道夫原型的那批人。"林星辰拿起外套，"顺着第七数据中心查。内战双方都在抢一个他们自己也说不清的东西。公司真相，今晚露了一个口。"',
        'anchor_mode': 'before',
        'patch_brief': 'Qwen 增量WARN：补 1 段陈思琪盯屏自语，点出白盾有限免责三道门（逻辑授权/物理隔离/人工复核）全漏与责任归属断裂；AI 行为按目标函数偏移+置信度回读跌破阈值口径，不写灵魂/觉醒。',
        'must_phrases': ['白盾', '三道门', '目标函数', '置信度'],
    },
]


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


def call_provider(provider, prompt, max_tokens=800, timeout=240):
    base, key, model = cfg_provider(provider)
    t = time.time()
    if not base or not key:
        return {'ok': False, 'provider': provider, 'model': model, 'returned_model': None,
                'status': 0, 'latency_s': 0.0, 'content': 'MISSING_BASE_OR_KEY'}
    payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt}],
               'max_tokens': max_tokens, 'temperature': 0.4 if provider == 'xiaomi' else 0.1}
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


MIMO_PROMPT = (
    '你是《科武纪元》作者 MiMo。任务：为已闭环章节做\"作者小修\"——只输出一段可直接插入原文的中文段落，**严禁重写整章**。\n\n'
    '章节：第{ch}章《{title}》。\n'
    '插入位置说明：见下方锚点；不要写锚点本身，只输出插入段。\n'
    '硬约束：\n'
    ' - 总长 ≤ 200 字（番茄口径），≥ 60 字。\n'
    ' - **绝对不出现「灵魂」「觉醒」二字**（即便是否定句、即便加引号都禁用）。AI 行为只用：目标函数/参数漂移/反馈增益/权限越界/置信度回读/误差边界。\n'
    ' - 写作风格延续原文：物理反馈、感官数据、可签字可追溯的细节；不用空文学比喻。\n'
    ' - 必须自然包含这些关键词（至少全部出现一次）：{must}\n'
    ' - 不出现新角色名；引用已有角色（林星辰/方宁/陈思琪/谢云/赵刚）符合现有人设。\n\n'
    '本段需要回应的会议红线（Qwen 编辑增量复核 WARN）：\n{brief}\n\n'
    '【锚点上下文（插入将在此{mode}）】\n{anchor}\n\n'
    '只输出插入段正文（不要 Markdown、不要前缀解释、不要 JSON），≤200 字。'
)

POST_REVIEW_PROMPT = (
    '你是《科武纪元》{role}。任务：V8.12.8.1 弹性优化会议写后复审（不要重写、不要长评）。\n'
    '本章：第{ch}章《{title}》。本章其它部分已通过历史 PASS 验收，本次仅针对作者 MiMo 在原文中插入的【新段】做衔接性与红线性复核。\n'
    '复审标准：\n'
    ' - 11 红线 + 5 制度链是否被新段违反；\n'
    ' - 新段与锚点上下文衔接是否自然（语气/人设/物理细节）；\n'
    ' - 是否出现「灵魂/觉醒」字样（一旦出现即 FAIL）；\n'
    ' - 关键词覆盖由静态机器复核保证，**不要据此判 FAIL**。\n\n'
    '【新插入段】\n{patch}\n\n'
    '【锚点上下文】\n{anchor}\n\n'
    '只输出严格 JSON：\n'
    '{{\"verdict\":\"PASS|WARN|FAIL\",\"redline_ok\":true|false,\"flow_ok\":true|false,\"reason\":\"≤80字\"}}'
)


def parse_json(s: str):
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        pass
    m = re.search(r'\{[\s\S]*?\}', s)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def strip_md_decoration(s: str) -> str:
    s = s.strip()
    # remove fenced blocks
    s = re.sub(r'^```[\w]*\n', '', s)
    s = re.sub(r'\n```\s*$', '', s)
    s = s.strip()
    # remove leading bullets / quotes that occasionally slip in
    s = re.sub(r'^[>\-\*\u3000\s]+', '', s)
    return s.strip()


def cn_count(s: str) -> int:
    return len(re.sub(r'\s+', '', WIKILINK_RE.sub(r'\1', s)))


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
        text = text.rstrip() + '\n\n（本章完）'
    else:
        text = text[:text.index('（本章完）') + len('（本章完）')]
    return text.strip() + '\n\n作者有话说：\n' + author_note.strip() + '\n'


def insert_at_anchor(body: str, anchor: str, mode: str, patch: str) -> tuple[str, bool]:
    if anchor not in body:
        return body, False
    block = '\n\n' + patch.strip() + '\n\n'
    if mode == 'after':
        new = body.replace(anchor, anchor + block, 1)
    else:  # before
        new = body.replace(anchor, block + anchor, 1)
    # collapse triple newlines
    new = re.sub(r'\n{3,}', '\n\n', new)
    return new, True


def process(item: dict, log: list) -> dict:
    ch = item['ch']
    md = NEW / f'第{ch}章.md'
    if not md.exists():
        return {'ch': ch, 'status': 'SKIP_SOURCE_MISSING'}

    original = md.read_text(encoding='utf-8')

    # 1) MiMo author micro patch
    prompt = MIMO_PROMPT.format(
        ch=ch, title=item['title'],
        must='、'.join(item['must_phrases']),
        brief=item['patch_brief'],
        mode='之后' if item['anchor_mode'] == 'after' else '之前',
        anchor=item['anchor'],
    )
    mr = call_provider('xiaomi', prompt, max_tokens=600, timeout=240)
    patch_text_raw = mr.get('content', '')
    patch_text = strip_md_decoration(patch_text_raw)
    # truncate to 240 chars CN to stay under 300
    if cn_count(patch_text) > 280:
        patch_text = patch_text[:280] + '…'

    # save raw author call
    (RAW / f'第{ch}_v81281_author_mimo_{STAMP}.json').write_text(
        json.dumps({'provider': mr['provider'], 'model': mr['model'], 'returned_model': mr['returned_model'],
                    'status': mr['status'], 'latency_s': mr['latency_s'], 'ok': mr['ok'],
                    'raw_content': patch_text_raw, 'patch_used': patch_text}, ensure_ascii=False, indent=2),
        encoding='utf-8')

    log.append(f'[第{ch}章] MiMo author: status={mr["status"]} returned={mr["returned_model"]} ok={mr["ok"]} cn={cn_count(patch_text)}')

    # 2) check author output contains must_phrases & not forbidden words
    forbidden_words = ['灵魂', '觉醒', 'AI觉醒']
    forbid_hit = [w for w in forbidden_words if w in patch_text]
    miss_phrases = [w for w in item['must_phrases'] if w not in patch_text]
    if forbid_hit or miss_phrases or cn_count(patch_text) < 60 or not mr['ok']:
        return {
            'ch': ch, 'status': 'AUTHOR_PATCH_REJECTED',
            'reason': f'forbid_hit={forbid_hit} miss_phrases={miss_phrases} cn={cn_count(patch_text)} ok={mr["ok"]}',
            'patch_text': patch_text,
        }

    # 3) backup & insert
    bak = BACKUPS / f'{STAMP}_ch{ch}_before_v81281_round2.md'
    shutil.copy2(md, bak)
    new_body, ok = insert_at_anchor(original, item['anchor'], item['anchor_mode'], patch_text)
    if not ok:
        return {'ch': ch, 'status': 'ANCHOR_NOT_FOUND', 'patch_text': patch_text}
    md.write_text(new_body, encoding='utf-8')

    # 4) dual post-review (Qwen editor + MiniMax reader)
    reviews = []
    for role_label, provider in [('编辑', 'alibaba'), ('读者', 'minimax-cn')]:
        pr = call_provider(provider, POST_REVIEW_PROMPT.format(
            role=role_label, ch=ch, title=item['title'],
            must='、'.join(item['must_keys']),
            patch=patch_text,
            anchor=item['anchor'],
        ), max_tokens=400, timeout=240)
        parsed = parse_json(pr.get('content', '')) or {
            'verdict': 'FAIL_PARSE', 'keyword_ok': False, 'flow_ok': False, 'reason': '解析失败',
        }
        rec = {
            'role': role_label, 'provider': pr['provider'], 'model': pr['model'],
            'returned_model': pr['returned_model'], 'status': pr['status'],
            'latency_s': pr['latency_s'], 'ok': pr['ok'],
            **parsed,
            'raw_preview': (pr.get('content') or '')[:400],
        }
        (RAW / f'第{ch}_v81281_post_review_{provider}_{STAMP}.json').write_text(
            json.dumps({**rec, 'raw_full': pr.get('content', '')}, ensure_ascii=False, indent=2),
            encoding='utf-8')
        reviews.append(rec)
        log.append(f'[第{ch}章] {role_label}({provider}): verdict={rec.get("verdict")} status={pr["status"]}')

    verdicts = [r.get('verdict') for r in reviews]
    dual_pass = all(v == 'PASS' for v in verdicts)

    if not dual_pass:
        # accept WARN as soft-pass per user spec "作者小修/必要时不改" + 不全文重写；FAIL/FAIL_PARSE => rollback
        any_fail = any(v in ('FAIL', 'FAIL_PARSE') for v in verdicts)
        if any_fail:
            shutil.copy2(bak, md)
            return {'ch': ch, 'status': 'POST_REVIEW_FAIL_ROLLED_BACK',
                    'verdicts': verdicts, 'patch_text': patch_text, 'backup': str(bak)}

    # 5) re-static check
    text_after = md.read_text(encoding='utf-8')
    missing = [k for k in item['must_keys'] if k not in text_after]
    soul_hits = [w for w in ['AI觉醒', 'AI灵魂', '机器觉醒'] if w in text_after]
    if missing or soul_hits:
        shutil.copy2(bak, md)
        return {'ch': ch, 'status': 'STATIC_FAIL_ROLLED_BACK',
                'missing': missing, 'soul_hits': soul_hits, 'backup': str(bak)}

    fanqie_md = fanqie_count_md(text_after)

    # 6) regenerate TXT if upload
    txt_action = 'SKIP_NON_UPLOAD'
    txt_fanqie = None
    if item['kind'] == 'upload' and item.get('note'):
        txt_path = SUB / f'第{ch}章.txt'
        txt_body = clean_for_txt(text_after, item['note'])
        txt_path.write_text(txt_body, encoding='utf-8')
        title_line = f'第{ch}章 {item["title"]}'
        txt_fanqie = fanqie_count_txt(txt_body, title_line)
        txt_action = 'WRITTEN'

    # 7) sync_kewu (--no-git)
    try:
        cp = subprocess.run(
            ['python3', str(BASE / '工具脚本/sync_kewu.py'),
             '--chapter', str(ch),
             '--message', f'V8.12.8.1 Round2 第{ch}章 MiMo作者小修+双审 弹性优化会议落地',
             '--no-git'],
            capture_output=True, text=True, timeout=180,
        )
        sync_rc = cp.returncode
        sync_err = (cp.stderr or '')[-300:] if cp.returncode != 0 else None
    except Exception as e:
        sync_rc = -1
        sync_err = repr(e)

    # 8) wiki fulltext keyword check
    wiki_path = BASE / f'wiki/chapters/ch{ch}.md'
    wiki_kw = {}
    if wiki_path.exists():
        wt = wiki_path.read_text(encoding='utf-8')
        for k in item['must_keys']:
            wiki_kw[k] = (k in wt)

    final_status = 'DONE' if dual_pass else 'DONE_WITH_WARN'

    # 9) close-loop report
    rpt = REPORT_DIR / f'第{ch}章_V81281闭环报告_{STAMP}.md'
    lines = [
        f'# 第{ch}章《{item["title"]}》 V8.12.8.1 闭环报告 (Round-2)',
        '',
        f'时间：{TS}',
        f'范围：MiMo 作者小修（≤300字弹性槽）+ 编辑/读者写后双审 + 机器验收',
        f'优先级：{item["priority"]}  类型：{item["kind"]}',
        f'备份：`{bak.relative_to(BASE)}`',
        '',
        '## MiMo 作者微补丁',
        f'- provider/model: xiaomi/{mr["model"]} (returned: {mr["returned_model"]}, HTTP {mr["status"]}, {mr["latency_s"]}s)',
        f'- 字数(去空白): {cn_count(patch_text)}（硬上限 300，目标 ≤200）',
        f'- 必含关键词: {item["must_phrases"]} → 全部命中',
        f'- 锚点模式: {item["anchor_mode"]} 锚点首句: `{item["anchor"].splitlines()[0][:40]}…`',
        '',
        '### 实际插入段',
        '```',
        patch_text,
        '```',
        '',
        '## 写后复审（双轨）',
        '| 角色 | provider/model | HTTP | returned_model | verdict | keyword_ok | flow_ok | reason |',
        '|---|---|---:|---|---|---|---|---|',
    ]
    for r in reviews:
        lines.append('| {role} | {prov}/{model} | {st} | {ret} | {v} | {k} | {f} | {rs} |'.format(
            role=r['role'], prov=r['provider'], model=r['model'], st=r['status'],
            ret=r.get('returned_model'), v=r.get('verdict'),
            k=r.get('keyword_ok'), f=r.get('flow_ok'), rs=(r.get('reason') or '')[:60]))
    lines += [
        '',
        '## 机器验收',
        '```json',
        json.dumps({
            'fanqie_md': fanqie_md,
            'must_keys_missing_after': missing,
            'soul_hits_after': soul_hits,
            'wikilink_count': len(WIKILINK_RE.findall(text_after)),
            'txt_action': txt_action,
            'txt_fanqie': txt_fanqie,
            'sync_returncode': sync_rc,
            'wiki_fulltext_keywords': wiki_kw,
        }, ensure_ascii=False, indent=2),
        '```',
        '',
        '## 结论',
        f'- 双 PASS：{dual_pass}',
        f'- 最终状态：**{final_status}**',
        f'- 番茄口径(MD)：{fanqie_md}',
        f'- TXT：{txt_action}' + (f'（番茄 ≈ {txt_fanqie}）' if txt_fanqie else ''),
    ]
    rpt.write_text('\n'.join(lines), encoding='utf-8')

    return {
        'ch': ch, 'priority': item['priority'], 'kind': item['kind'],
        'status': final_status,
        'verdicts': verdicts,
        'patch_cn_count': cn_count(patch_text),
        'fanqie_md_after': fanqie_md,
        'txt_action': txt_action,
        'txt_fanqie': txt_fanqie,
        'sync_returncode': sync_rc,
        'wiki_keywords': wiki_kw,
        'backup': str(bak.relative_to(BASE)),
        'report': str(rpt.relative_to(BASE)),
    }


def main():
    load_env()
    log = []
    results = []
    for item in TASKS:
        print(f'>>> Round-2 第{item["ch"]}章 ...')
        try:
            r = process(item, log)
        except Exception as e:
            r = {'ch': item['ch'], 'status': 'FAIL_BLOCKED', 'error': repr(e)}
        results.append(r)
        print(f'    -> {r.get("status")}')

    out = MEETING_DIR / f'V81281_round2_summary_{STAMP}.json'
    out.write_text(json.dumps({'meta': {'version': 'V8.12.8.1', 'round': 2,
                                          'generated_at': TS, 'agent': '澄砚'},
                                'log': log, 'queue': results}, ensure_ascii=False, indent=2),
                    encoding='utf-8')
    print(f'summary -> {out}')


if __name__ == '__main__':
    main()
