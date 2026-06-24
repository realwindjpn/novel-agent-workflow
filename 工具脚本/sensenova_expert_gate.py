#!/usr/bin/env python3
"""SenseNova expert-view gate before MiroFish.

This script validates that public expert viewpoints for Shen Yi and Gao Zhikai
have been collected as traceable source cards before a SenseNova run is fed into
MiroFish. It does not search the web by itself and never treats search snippets
as source text.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

PROJECT = Path('/root/workspace/科武纪元')
DEFAULT_RUNS_BASE = PROJECT / '学习记录' / 'SenseNova分段任务化'
REQUIRED_EXPERTS = {
    'shenyi': {
        'display_name': '沈逸',
        'aliases': ['沈逸', '复旦沈逸', 'Shen Yi'],
        'query_hints': [
            '沈逸 人工智能 科技竞争 公开观点',
            '沈逸 中美 科技 博弈 公开演讲',
            '复旦 沈逸 国际关系 科技安全',
        ],
    },
    'gaozhikai': {
        'display_name': '高志凯',
        'aliases': ['高志凯', 'Victor Gao', 'Gao Zhikai'],
        'query_hints': [
            '高志凯 科技竞争 公开观点',
            '高志凯 中美关系 科技 博弈',
            'Victor Gao China US technology public remarks',
        ],
    },
}
VALID_SOURCE_TYPES = {
    'primary_article',
    'primary_video',
    'primary_transcript',
    'public_interview',
    'official_social',
    'authority_repost',
}
SEARCH_SUMMARY_TYPES = {'search_summary', 'search_snippet', 'search_result_only', 'discovery_only'}
FAILURE_TAGS = {
    'no_primary': 'EXPERT_SOURCE_NO_PRIMARY_HIT',
    'body_blocked': 'EXPERT_SOURCE_BODY_BLOCKED',
    'insufficient': 'EXPERT_GATE_INSUFFICIENT',
    'summary_only': 'EXPERT_SOURCE_SEARCH_SUMMARY_ONLY',
}


def now() -> str:
    return dt.datetime.now().isoformat(timespec='seconds')


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def latest_run_dir(base: Path) -> Path:
    dirs = [p for p in base.iterdir() if p.is_dir() and (p / 'pipeline_state.json').exists()]
    if not dirs:
        raise SystemExit(f'no SenseNova run_dir with pipeline_state under {base}')
    return sorted(dirs, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def norm_text(value: Any) -> str:
    return str(value or '').strip()


def normalize_expert(value: Any) -> str:
    text = norm_text(value)
    for key, spec in REQUIRED_EXPERTS.items():
        if text == key:
            return key
        for alias in spec['aliases']:
            if alias.lower() in text.lower():
                return key
    return ''


def load_cards(run_dir: Path, cards_file: Path | None) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    paths: list[Path] = []
    if cards_file:
        paths.append(cards_file)
    paths.extend([
        run_dir / 'raw' / 'expert_voice_cards.json',
        run_dir / 'raw' / 'expert_voice_cards.jsonl',
        run_dir / 'cards' / 'expert_voice_cards.json',
        run_dir / 'expert_voice_cards.json',
    ])
    for path in paths:
        if not path.exists():
            continue
        if path.suffix == '.jsonl':
            for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                if isinstance(item, dict):
                    candidates.append(item)
        else:
            data = load_json(path, [])
            if isinstance(data, dict):
                items = data.get('expert_voice_cards') or data.get('cards') or data.get('items') or []
            else:
                items = data
            if isinstance(items, list):
                candidates.extend([item for item in items if isinstance(item, dict)])
    return candidates


def body_text(card: dict[str, Any], run_dir: Path) -> str:
    direct = '\n'.join(
        norm_text(card.get(k))
        for k in ('body_text', 'body', 'transcript', 'source_excerpt', 'excerpt', 'summary')
        if norm_text(card.get(k))
    )
    path_value = norm_text(card.get('body_path') or card.get('raw_path') or card.get('source_body_path'))
    if path_value:
        path = Path(path_value)
        if not path.is_absolute():
            path = run_dir / path
        try:
            direct += '\n' + path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            pass
    return direct.strip()


def has_public_trace(card: dict[str, Any]) -> bool:
    url = norm_text(card.get('url') or card.get('source_url'))
    title = norm_text(card.get('title'))
    return bool(url.startswith(('http://', 'https://')) and title)


def classify_card(card: dict[str, Any], run_dir: Path) -> tuple[bool, list[str], dict[str, Any]]:
    source_type = norm_text(card.get('source_type') or card.get('source_kind') or card.get('type'))
    body = body_text(card, run_dir)
    tags: list[str] = []

    if source_type in SEARCH_SUMMARY_TYPES or card.get('search_summary_only') is True:
        tags.append(FAILURE_TAGS['summary_only'])
    if not has_public_trace(card):
        tags.append(FAILURE_TAGS['no_primary'])
    if source_type and source_type not in VALID_SOURCE_TYPES and source_type not in SEARCH_SUMMARY_TYPES:
        tags.append(FAILURE_TAGS['no_primary'])
    if not body or len(re.sub(r'\s+', '', body)) < 120:
        tags.append(FAILURE_TAGS['body_blocked'])

    ok = not tags
    # 2026-06-22 增量：来源含观察者网（guancha.cn / 观察者）且评论员为沈逸/高志凯时，
    # 在卡 metadata 标 commentator 字段，供下游 G2 / 编辑快速识别"评论员 → 站点"配对。
    _url_for_commentator = norm_text(card.get('url') or card.get('source_url'))
    _title_for_commentator = norm_text(card.get('title'))
    _expert_key_for_commentator = normalize_expert(
        card.get('expert') or card.get('expert_name') or card.get('author') or _title_for_commentator
    )
    _is_guancha_source = ('guancha' in _url_for_commentator.lower()) or ('观察者' in _url_for_commentator) or ('观察者' in _title_for_commentator)
    _commentator = REQUIRED_EXPERTS[_expert_key_for_commentator]['display_name'] if (
        _is_guancha_source and _expert_key_for_commentator in REQUIRED_EXPERTS
    ) else ''
    normalized = {
        'expert': normalize_expert(card.get('expert') or card.get('expert_name') or card.get('author')),
        'expert_name': norm_text(card.get('expert_name') or card.get('expert') or card.get('author')),
        'title': norm_text(card.get('title')),
        'url': norm_text(card.get('url') or card.get('source_url')),
        'commentator': _commentator,
        'published_at': norm_text(card.get('published_at') or card.get('date')),
        'captured_at': norm_text(card.get('captured_at')) or now(),
        'source_type': source_type or 'unknown',
        'body_chars': len(body),
        'summary': norm_text(card.get('summary'))[:500],
        'material_axis': norm_text(card.get('material_axis') or card.get('axis') or 'expert_voice'),
        'g2_g3_hint': norm_text(card.get('g2_g3_hint') or card.get('mirofish_hint')),
        'usable_for_mirofish': ok,
        'failure_tags': sorted(set(tags)),
    }
    return ok, sorted(set(tags)), normalized


def build_rescue_item(key: str, tags: list[str]) -> dict[str, Any]:
    spec = REQUIRED_EXPERTS[key]
    return {
        'expert': key,
        'expert_name': spec['display_name'],
        'failure_tags': sorted(set(tags or [FAILURE_TAGS['insufficient']])),
        'required_stage': [
            'discovery',
            'body_fetch',
            'summary_distill',
            'expert_voice_card',
            'mirofish_input_gate',
            'G2_G3_review',
        ],
        'query_hints': spec['query_hints'],
        'rules': [
            'do not call no search result no advice',
            'do not treat search snippet as original source',
            'keep URL, publish/capture time, source type, and body/excerpt evidence',
        ],
    }


def evaluate(run_dir: Path, cards: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in REQUIRED_EXPERTS}
    rejected: list[dict[str, Any]] = []
    for card in cards:
        expert = normalize_expert(card.get('expert') or card.get('expert_name') or card.get('author') or card.get('title'))
        if not expert:
            continue
        ok, tags, normalized = classify_card(card, run_dir)
        if ok:
            grouped[expert].append(normalized)
        else:
            rejected.append(normalized)

    missing: list[str] = []
    rescue_queue: list[dict[str, Any]] = []
    per_expert: dict[str, Any] = {}
    for key, spec in REQUIRED_EXPERTS.items():
        usable = grouped[key]
        expert_rejected = [r for r in rejected if r.get('expert') == key]
        tags: list[str] = []
        if not usable:
            if expert_rejected:
                for item in expert_rejected:
                    tags.extend(item.get('failure_tags') or [])
            else:
                tags.append(FAILURE_TAGS['no_primary'])
            tags.append(FAILURE_TAGS['insufficient'])
            missing.append(key)
            rescue_queue.append(build_rescue_item(key, tags))
        per_expert[key] = {
            'expert_name': spec['display_name'],
            'usable_count': len(usable),
            'usable_cards': usable,
            'rejected_count': len(expert_rejected),
            'rejected_cards': expert_rejected,
            'pass': bool(usable),
            'failure_tags': sorted(set(tags)),
        }

    expert_voice_cards = [card for cards_for_expert in grouped.values() for card in cards_for_expert]
    p0_p1_expert_cards = [
        card for card in expert_voice_cards
        if re.search(r'\bP[01]\b|p0|p1|高|中美|科技|安全|芯片|AI|人工智能|地缘|国际关系', json.dumps(card, ensure_ascii=False), re.I)
    ]
    expert_gate_pass = not missing
    gate_tags = [] if expert_gate_pass else [FAILURE_TAGS['insufficient']]
    return {
        'schema': 'sensenova_expert_gate_v1',
        'created_at': now(),
        'status': 'PASS' if expert_gate_pass else 'BLOCKED',
        'expert_gate_pass': expert_gate_pass,
        'required_experts': [spec['display_name'] for spec in REQUIRED_EXPERTS.values()],
        'missing_experts': missing,
        'failure_tags': gate_tags,
        'fields': {
            'expert_voice_cards': expert_voice_cards,
            'p0_p1_expert_cards': p0_p1_expert_cards,
            'expert_gate_pass': expert_gate_pass,
        },
        'per_expert': per_expert,
        'rescue_queue': rescue_queue,
        'policy': {
            'search_summary_is_not_source_body': True,
            'no_search_result_is_not_no_advice': True,
            'does_not_modify_novel_text': True,
            'mirofish_must_block_when_expert_gate_pass_false': True,
        },
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        '# SenseNova Expert Gate Report',
        '',
        f"- created_at: {report['created_at']}",
        f"- status: {report['status']}",
        f"- expert_gate_pass: {report['expert_gate_pass']}",
        f"- failure_tags: {', '.join(report['failure_tags']) or 'NONE'}",
        '',
        '## Experts',
        '',
        '| expert | pass | usable | rejected | failure_tags |',
        '|---|---:|---:|---:|---|',
    ]
    for item in report['per_expert'].values():
        lines.append(
            f"| {item['expert_name']} | {item['pass']} | {item['usable_count']} | "
            f"{item['rejected_count']} | {', '.join(item['failure_tags']) or 'NONE'} |"
        )
    lines += [
        '',
        '## Gate Rules',
        '',
        '- 搜索摘要不得冒充原文。',
        '- 无搜索结果不得表述为无建议。',
        '- MiroFish 只消费可追溯公开观点摘要，不直接改正文。',
        '',
        '## Rescue Queue',
        '',
    ]
    for item in report['rescue_queue']:
        lines.append(f"- {item['expert_name']}: {', '.join(item['failure_tags'])}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Validate Shen Yi / Gao Zhikai expert-view cards before MiroFish.')
    parser.add_argument('--run-dir', default='', help='SenseNova run dir. Default: latest run under SenseNova分段任务化.')
    parser.add_argument('--runs-base', default=str(DEFAULT_RUNS_BASE), help='Base directory for SenseNova runs.')
    parser.add_argument('--cards-file', default='', help='Optional JSON/JSONL file containing expert_voice_cards.')
    parser.add_argument('--write', action='store_true', help='Write raw/expert_gate_report.json and related reports into run_dir.')
    parser.add_argument('--json', action='store_true', help='Print JSON report.')
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_dir = Path(args.run_dir) if args.run_dir else latest_run_dir(Path(args.runs_base))
    cards_file = Path(args.cards_file) if args.cards_file else None
    cards = load_cards(run_dir, cards_file)
    report = evaluate(run_dir, cards)
    report['source_run_dir'] = str(run_dir)
    report['input_cards_file'] = str(cards_file) if cards_file else ''

    if args.write:
        raw = run_dir / 'raw'
        write_json(raw / 'expert_gate_report.json', report)
        write_json(raw / 'expert_source_rescue_queue.json', report['rescue_queue'])
        write_json(raw / 'expert_voice_cards.validated.json', report['fields']['expert_voice_cards'])
        write_markdown(raw / 'expert_gate_report.md', report)

    if args.json or not args.write:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({
            'status': report['status'],
            'expert_gate_pass': report['expert_gate_pass'],
            'source_run_dir': str(run_dir),
            'expert_gate_report': str(run_dir / 'raw' / 'expert_gate_report.json'),
        }, ensure_ascii=False, indent=2))
    return 0 if report['expert_gate_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
