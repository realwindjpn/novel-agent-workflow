#!/usr/bin/env python3
"""G4 逐章签发器的红绿与反空壳测试。

覆盖：成功、缺 G1/G2/G3、错章、前章链缺失/B 提前、submitter 缺失、
幂等、输入变更重建、G4 dispatcher 验证，以及 control tick 的白名单单次自动签发。
所有 case 使用临时项目；绝不触碰生产 task、正文、草稿箱或 cron。
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path('/root/.hermes/scripts')
G4 = SCRIPTS / 'kewu_daily_g4_release.py'
PROMPT = SCRIPTS / 'kewu_daily_author_prompt.py'
DISPATCHER = SCRIPTS / 'kewu_daily_transition_dispatcher.py'
TICK = SCRIPTS / 'kewu_daily_control_tick.py'

A, B, FRONTIER = 421, 422, 420


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Fixture:
    def __init__(self, root: Path):
        self.root = root
        self.project = root / 'project'
        self.tasks = root / 'tasks'
        self.output = self.tasks / '20260906_kewu_selfcycle_daily' / 'output'
        self.task = self.output.parent
        self.new = self.project / '新版'
        self.sub = self.project / '已投稿'
        for d in (self.output, self.new, self.sub):
            d.mkdir(parents=True, exist_ok=True)
        prev = '第420章 前沿\n' + '前沿证据。' * 20 + '\n'
        (self.new / f'第{FRONTIER}章.md').write_text(prev, encoding='utf-8')
        (self.sub / f'第{FRONTIER}章.txt').write_text(prev, encoding='utf-8')
        self.outline = self.project / 'outline.md'
        self.outline.write_text(
            '第421章 | 测试卷 | 甲章 | 甲种子 | 甲伏笔 | 3200\n'
            '第422章 | 测试卷 | 乙章 | 乙种子 | 乙伏笔 | 3200\n', encoding='utf-8')
        (self.output / 'G1_material_match.json').write_text(json.dumps({
            'verdict': 'ALLOW_G2', 'target_chapters': [A, B]}, ensure_ascii=False), encoding='utf-8')
        (self.output / 'G2_verdict.json').write_text(json.dumps({
            'verdict': 'NOTE_LAYER', 'target_chapters': [A, B]}, ensure_ascii=False), encoding='utf-8')
        prev_sha = sha(self.new / f'第{FRONTIER}章.md')
        for ch, title in ((A, '甲章'), (B, '乙章')):
            payload = {
                'chapter': ch, 'title': title, 'state': 'G3_READY',
                'plot_seed': f'{title}种子', 'entry_interface': [f'{title}接口'],
                'locked_constraints': [f'{title}约束'],
                'outline_ref': f'outline#{ch}',
                'prev_chapter': FRONTIER if ch == A else A,
                'prev_sha256': prev_sha if ch == A else 'PENDING_421_FINALIZE',
                'prev_state': 'PUBLISHED_FRONTIER' if ch == A else 'PENDING_DEPENDENCY',
            }
            (self.output / f'G3_PREP_{ch}.json').write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        self.submitter = root / 'qwen_submit_chapter.py'
        self.submitter.write_text('#!/usr/bin/env python3\nprint("submitter")\n', encoding='utf-8')

    def env(self, **extra):
        e = os.environ.copy()
        e.update({
            'KEWU_DAILY_PROJECT_ROOT': str(self.project),
            'KEWU_DAILY_TASK_ROOT': str(self.tasks),
            'KEWU_DAILY_OUTLINE': str(self.outline),
            'KEWU_DAILY_NEWTEXT_DIR': str(self.new),
            'KEWU_DAILY_SUBMITTED_DIR': str(self.sub),
            'KEWU_DAILY_SUBMITTER': str(self.submitter),
            'KEWU_DAILY_NOW': '2026-09-06T20:05:00+08:00',
            'KEWU_DAILY_ACTION_QUEUE': str(self.root / 'queue.jsonl'),
            'KEWU_DAILY_STALL_MINUTES': '0',
        })
        e.update(extra)
        return e

    def load(self, name: str):
        for key, val in self.env().items():
            os.environ[key] = val
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        for mod in ('kewu_daily_g4_release', 'kewu_daily_author_prompt',
                    'kewu_daily_transition_dispatcher', 'kewu_daily_control_tick'):
            sys.modules.pop(mod, None)
        return importlib.import_module(name)


@pytest.fixture()
def fx(tmp_path):
    return Fixture(tmp_path)


def test_01_success_binds_all_required_inputs_and_dispatcher_verifies(fx):
    g4 = fx.load('kewu_daily_g4_release')
    out = g4.issue(fx.task, A)
    data = json.loads(out.read_text(encoding='utf-8'))
    assert out.name == f'G4_RELEASE_{A}.json'
    assert data['state'] == 'SIGNED'
    assert data['author_route'] == 'web_qwen'
    assert data['author_project_url'] == 'https://chat.qwen.ai/p/18dab9a0-fea0-490f-abc2-aff83b85ee04'
    assert data['preferred_model'] == 'qwen3.8-max'
    assert set(data['binding']) == {'g1', 'g2', 'g3', 'outline', 'prev', 'submitter', 'prompt'}
    assert data['binding']['prev']['newtext_sha256'] == sha(fx.new / '第420章.md')
    assert data['binding']['prev']['submitted_sha256'] == sha(fx.sub / '第420章.txt')
    dispatcher = fx.load('kewu_daily_transition_dispatcher')
    verdict = dispatcher.dispatch({'transition': 'G4A', 'chapter': A}, fx.task)
    assert verdict.status == dispatcher.VERIFIED, verdict.to_dict()
    data['binding']['g1']['sha256'] = '0' * 64
    out.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    tampered = dispatcher.dispatch({'transition': 'G4A', 'chapter': A}, fx.task)
    assert tampered.status == dispatcher.INVALID and 'G4_binding_invalid' in tampered.detail


@pytest.mark.parametrize('name', ['G1_material_match.json', 'G2_verdict.json', 'G3_PREP_421.json'])
def test_02_missing_gate_refuses_without_release(fx, name):
    (fx.output / name).unlink()
    g4 = fx.load('kewu_daily_g4_release')
    with pytest.raises(g4.G4Refusal):
        g4.issue(fx.task, A)
    assert not (fx.output / f'G4_RELEASE_{A}.json').exists()


def test_03_wrong_chapter_and_prev_chain_refuse(fx):
    g4 = fx.load('kewu_daily_g4_release')
    with pytest.raises(g4.G4Refusal):
        g4.issue(fx.task, 999)
    (fx.new / '第420章.md').unlink()
    with pytest.raises(g4.G4Refusal):
        g4.issue(fx.task, A)


def test_04_b_refuses_before_a_closed(fx):
    g4 = fx.load('kewu_daily_g4_release')
    with pytest.raises(g4.G4Refusal, match='B_requires_A_close'):
        g4.issue(fx.task, B)


def test_05_submitter_missing_refuses(fx):
    fx.submitter.unlink()
    g4 = fx.load('kewu_daily_g4_release')
    with pytest.raises(g4.G4Refusal, match='submitter_missing'):
        g4.issue(fx.task, A)


def test_06_idempotent_and_input_change_rebuild(fx):
    g4 = fx.load('kewu_daily_g4_release')
    out = g4.issue(fx.task, A)
    before = (out.read_bytes(), out.stat().st_mtime_ns)
    same = g4.issue(fx.task, A)
    assert same == out and (out.read_bytes(), out.stat().st_mtime_ns) == before
    g1 = json.loads((fx.output / 'G1_material_match.json').read_text(encoding='utf-8'))
    g1['input_change'] = True
    (fx.output / 'G1_material_match.json').write_text(json.dumps(g1), encoding='utf-8')
    g4.issue(fx.task, A)
    assert out.read_bytes() != before[0]


def test_07_prompt_contains_g3_hard_content_without_body_generation(fx):
    prompt = fx.load('kewu_daily_author_prompt')
    path = prompt.build(fx.task, A)
    text = path.read_text(encoding='utf-8')
    assert '硬闸' in text and '甲章种子' in text and '甲章接口' in text and '甲章约束' in text
    assert '输出：仅候选正文文件；勿附解释、审稿或执行日志。' in text


def test_08_control_tick_auto_signs_only_exact_waiting_g4_once(fx, monkeypatch):
    tick = fx.load('kewu_daily_control_tick')
    dispatcher = importlib.import_module('kewu_daily_transition_dispatcher')
    dispatcher.append_ledger(fx.task, {'type': 'DAILY_SEED', 'day': '2026-09-06',
                                      'chapters': [A, B], 'frontier': FRONTIER,
                                      'frontier_source': 'fixture',
                                      'outline_anchors': [{}, {}]})
    for transition in ('seed', 'G1', 'G2', 'G3'):
        dispatcher.append_ledger(fx.task, {'type': 'TRANSITION_ACK', 'transition': transition})
    dispatcher.append_ledger(fx.task, {'type': 'CHAPTER_SLOT', 'slot': 'A', 'chapter': A})
    dispatcher.append_ledger(fx.task, {'type': 'CHAPTER_SLOT', 'slot': 'B', 'chapter': B})
    calls = []
    original = tick.run_g4_issuer
    def spy(*args, **kwargs):
        calls.append(args)
        return original(*args, **kwargs)
    monkeypatch.setattr(tick, 'run_g4_issuer', spy)
    assert tick.tick() == 0
    rows = dispatcher.read_ledger(fx.task)
    assert len(calls) == 1
    assert [r['transition'] for r in rows if r.get('type') == 'TRANSITION_ACK'][-1] == 'G4A'
    assert [r['transition'] for r in rows if r.get('type') == 'TRANSITION_PENDING'][-1] == 'authorA'
    assert tick.tick() == 0
    assert len(calls) == 1


def test_09_mutation_disabling_g4_autorun_keeps_g4_unacked(fx, monkeypatch):
    tick = fx.load('kewu_daily_control_tick')
    dispatcher = importlib.import_module('kewu_daily_transition_dispatcher')
    dispatcher.append_ledger(fx.task, {'type': 'DAILY_SEED', 'day': '2026-09-06',
                                      'chapters': [A, B], 'frontier': FRONTIER,
                                      'frontier_source': 'fixture', 'outline_anchors': [{}, {}]})
    for transition in ('seed', 'G1', 'G2', 'G3'):
        dispatcher.append_ledger(fx.task, {'type': 'TRANSITION_ACK', 'transition': transition})
    dispatcher.append_ledger(fx.task, {'type': 'CHAPTER_SLOT', 'slot': 'A', 'chapter': A})
    dispatcher.append_ledger(fx.task, {'type': 'CHAPTER_SLOT', 'slot': 'B', 'chapter': B})
    monkeypatch.setattr(tick, 'G4_AUTORUN_OWNER', 'wrong_owner')
    tick.tick()
    rows = dispatcher.read_ledger(fx.task)
    assert 'G4A' not in [r.get('transition') for r in rows if r.get('type') == 'TRANSITION_ACK']
    assert not (fx.output / f'G4_RELEASE_{A}.json').exists()
