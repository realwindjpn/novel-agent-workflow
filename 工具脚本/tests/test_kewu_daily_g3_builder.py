#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用 G3 builder + control tick 自动执行的 TDD 门禁。

覆盖 TASK.md §TDD HARD 十一项：
  1  双章成功，字段与 SHA 正确
  2  少一章/错章号/空 plot_seed 会被 dispatcher 判 FAIL
  3  G1/G2 缺失或 target mismatch 硬失败且不留半成品
  4  大纲章缺失/重复硬失败
  5  前章缺失硬失败
  6  G2 章级强制约束不得被丢弃
  7  幂等：第二次运行字节与 mtime 全同
  8  输入 SHA 变后重建
  9  control tick fixture：G3 PENDING 一次 tick 即 builder→VERIFY→ACK→G4A PENDING
  10 变异自证：monkeypatch 禁用 auto-run 后 #9 必须 FAIL
  11 历史回归：fixture 形状驱动，产物不含 313/314 硬编码

运行：
  python3 -m pytest /root/workspace/科武纪元/工具脚本/tests/test_kewu_daily_g3_builder.py -q
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path('/root/.hermes/scripts')
BUILDER = SCRIPTS / 'kewu_daily_g3_builder.py'
DISPATCHER = SCRIPTS / 'kewu_daily_transition_dispatcher.py'
TICK = SCRIPTS / 'kewu_daily_control_tick.py'
SEED = SCRIPTS / 'kewu_daily_seed.py'

PY = sys.executable
CST_NOW = '2026-09-06T20:05:00+08:00'

# ── fixture 素材：与生产章号解耦，故意用 4xx 段避开 313/314/317/318 ──
FIX_FRONTIER = 420          # 已定稿前沿
FIX_A, FIX_B = 421, 422     # 目标双章
VOLUME = '第九卷·测试卷'

OUTLINE_ROWS = {
    418: '第418章 | 第九卷·测试卷 | 旧章甲 | 甲的主体事件。 | 甲的伏笔。 | 3100',
    419: '第419章 | 第九卷·测试卷 | 旧章乙 | 乙的主体事件。 | 乙的伏笔。 | 3110',
    420: '第420章 | 第九卷·测试卷 | 前沿章 | 前沿章主体事件。 | 前沿章伏笔。 | 3120',
    421: ('第421章 | 第九卷·测试卷 | 甲级对决 | 甲方在测试层接管被夺走的机组，每压回一台便丢一段旧记忆。 | '
          '甲方把丢失画面记进纸带，翻面看见陌生笔迹。；对手延长静默试出他仍能靠手势接管。 | 3240'),
    # 目标字数刻意避开 3130/3140 这类含 '313'/'314' 子串的值: #01 断言
    # target_chars 与 outline_raw 原样落盘, 而 #11b 禁产物出现 '313'/'314',
    # 两者在 3130 上会互相否定。此处只调 fixture 数值, 不放宽任何断言。
    422: ('第422章 | 第九卷·测试卷 | 乙级遗迹 | 乙方带记录组进入地下石室，沿墙槽凝结物追查温度来源。 | '
          '乙方发现刻度有一格被凿平。；记录组翻出一枚反向嵌入的铜片。 | 3260'),
    423: '第423章 | 第九卷·测试卷 | 后章丙 | 丙的主体事件。 | 丙的伏笔。 | 3140',
}

PREV_BODY = '\n'.join([
    f'第{FIX_FRONTIER}章 前沿章',
    '前沿章第一段，交代人物在检修位上的处境。',
    '前沿章第二段，给出温度与功率的具体读数。',
    '前沿章第三段，制度侧的签批链被卡在换班之后。',
    '前沿章第四段，主角把记录拖进删除区。',
    '前沿章第五段，隔离柜升级三级警戒。',
    '前沿章第六段，人员侧关联检索令未开立。',
    '前沿章第七段，接驳深度被强制清零。',
    '前沿章第八段，校准窗还剩四十小时。',
    '前沿章第九段，两条暗线仍悬而未决。',
    '前沿章第十段，章末钩子落在未断开的连接上。',
    '（本章完）',
])

# G2 章级约束：#6 要求原样保留可追溯
G2_CHAPTER_POINT_A = (
    f'{FIX_A}章：接管与手势命令须在权限日志留带主体身份与时间戳的可审计记录；'
    'BLOCKING_FOR_G3：不得写成无条件超能力操作。'
)
G2_CHAPTER_POINT_B = (
    f'第{FIX_B}章 → 不注入今日素材；遗迹刻度与温度异常仍由既有考古—工程缺口因果驱动。'
)
G2_RANGE_POINT = f'{FIX_A}-{FIX_B+3}章通用备注：外部管制类素材仅作背景质感，正文禁贴现实国别。'
G2_GLOBAL_POINT = '远端备注：能源类卡只入工程代价词表，不改既有冻结硬数。'


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def net_cjk(text: str) -> int:
    import re
    return len(re.findall(r'[\u4e00-\u9fff]', text))


class Fixture:
    """一套完整的隔离项目 + 任务包，全部走 env 覆盖，不碰生产目录。"""

    def __init__(self, root: Path, *, outline_chapters=None, write_prev=True,
                 g1_targets=None, g2_targets=None, drop_g1=False, drop_g2=False,
                 duplicate_outline_chapter=None):
        self.root = root
        self.proj = root / 'proj'
        self.tasks = root / 'tasks'
        self.sub = self.proj / '已投稿'
        self.new = self.proj / '新版'
        for d in (self.sub, self.new, self.tasks):
            d.mkdir(parents=True, exist_ok=True)

        for i in range(1, FIX_FRONTIER + 1):
            (self.sub / f'第{i}章.txt').write_text('正文' * 600, encoding='utf-8')

        chapters = outline_chapters if outline_chapters is not None else sorted(OUTLINE_ROWS)
        rows = [OUTLINE_ROWS[c] for c in chapters if c in OUTLINE_ROWS]
        if duplicate_outline_chapter is not None:
            rows.append(OUTLINE_ROWS[duplicate_outline_chapter])
        self.outline = self.proj / 'outline_latest.md'
        self.outline.write_text('\n'.join(rows) + '\n', encoding='utf-8')

        self.prev = self.new / f'第{FIX_FRONTIER}章.md'
        if write_prev:
            self.prev.write_text(PREV_BODY + '\n', encoding='utf-8')

        self.task = self.tasks / '20260906_kewu_selfcycle_daily'
        self.out = self.task / 'output'
        self.out.mkdir(parents=True, exist_ok=True)

        if not drop_g1:
            self.g1 = self.out / 'G1_material_match.json'
            self.g1.write_text(json.dumps({
                'run_id': 'fixture_g1',
                'verdict': 'ALLOW_G2',
                'state': 'DONE',
                'target_chapters': g1_targets or [FIX_A, FIX_B],
                'total_cards': 40,
                'chapters': {
                    str(FIX_A): {'matched_cards': 12, 'strong_matches': 1,
                                 'p0_or_target_band_hits': 0},
                    str(FIX_B): {'matched_cards': 7, 'strong_matches': 0,
                                 'p0_or_target_band_hits': 0},
                },
            }, ensure_ascii=False, indent=2), encoding='utf-8')
        if not drop_g2:
            self.g2 = self.out / 'G2_verdict.json'
            self.g2.write_text(json.dumps({
                'run_id': 'fixture_g2',
                'verdict': 'NOTE_LAYER',
                'final_verdict': 'NOTE_LAYER',
                'target_chapters': g2_targets or [FIX_A, FIX_B],
                'outline_patch_allowed': False,
                'material_summary': {'bridged_cards': 40, 'fresh_24h': 4},
                'note_layer_points': [
                    {'seat': '军事制度', 'point': G2_CHAPTER_POINT_A},
                    {'seat': '读者视角', 'point': G2_CHAPTER_POINT_B},
                    {'seat': '军事制度', 'point': G2_RANGE_POINT},
                    {'seat': '主席/结构', 'point': G2_GLOBAL_POINT},
                ],
                'seats': [
                    {'seat': '主席/结构', 'provider': 'p1', 'model': 'm1', 'verdict': 'NOTE_LAYER'},
                    {'seat': '军事制度', 'provider': 'p2', 'model': 'm2', 'verdict': 'NOTE_LAYER'},
                ],
                'boundary': '会议只产备注层建议；未改大纲主体。',
            }, ensure_ascii=False, indent=2), encoding='utf-8')

    # ── env ──
    def env(self, **extra) -> dict:
        e = os.environ.copy()
        e.update({
            'KEWU_DAILY_PROJECT_ROOT': str(self.proj),
            'KEWU_DAILY_TASK_ROOT': str(self.tasks),
            'KEWU_DAILY_OUTLINE': str(self.outline),
            'KEWU_DAILY_SUBMITTED_DIR': str(self.sub),
            'KEWU_DAILY_NEWTEXT_DIR': str(self.new),
            'KEWU_DAILY_DRAFT_LISTING': str(self.root / 'draft_listing.json'),
            'KEWU_DAILY_ACTION_QUEUE': str(self.root / 'queue.jsonl'),
            'KEWU_DAILY_EXEC_DB': str(self.root / 'executions.db'),
            'KEWU_DAILY_NOW': CST_NOW,
            'KEWU_DAILY_STALL_MINUTES': '0',
        })
        e.update(extra)
        return e

    # ── 运行 builder ──
    def run_builder(self, *args, expect_rc=None) -> tuple[int, dict, str]:
        # 反空壳：builder 缺失时 rc 恒非 0，会让 "硬失败" 类断言假绿。
        assert BUILDER.is_file(), f'builder 不存在，无法判定硬失败语义: {BUILDER}'
        cmd = [PY, str(BUILDER), '--task-dir', str(self.task),
               '--chapters', str(FIX_A), str(FIX_B), *args]
        cp = subprocess.run(cmd, env=self.env(), text=True, capture_output=True, timeout=180)
        payload = {}
        out = (cp.stdout or '').strip()
        if out:
            try:
                payload = json.loads(out.splitlines()[-1])
            except Exception:
                payload = {'raw': out[-800:]}
        if expect_rc is not None:
            assert cp.returncode == expect_rc, (cp.returncode, out, cp.stderr[-800:])
        return cp.returncode, payload, (cp.stderr or '')

    def prep_path(self, ch: int) -> Path:
        return self.out / f'G3_PREP_{ch}.json'

    def prep(self, ch: int) -> dict:
        return json.loads(self.prep_path(ch).read_text(encoding='utf-8'))

    def prep_files(self) -> list[Path]:
        return sorted(self.out.glob('G3_PREP_*.json'))

    def seed(self) -> None:
        cp = subprocess.run([PY, str(SEED)], env=self.env(), text=True,
                            capture_output=True, timeout=120)
        assert cp.returncode == 0, (cp.stdout, cp.stderr)

    def ledger(self) -> list[dict]:
        p = self.task / 'transitions.jsonl'
        if not p.exists():
            return []
        return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]

    def dispatch_g3(self) -> dict:
        item = {'transition': 'G3', 'task': str(self.task), 'chapters': [FIX_A, FIX_B]}
        cp = subprocess.run([PY, str(DISPATCHER), '--item-json', '-',
                             '--task-dir', str(self.task)],
                            input=json.dumps(item), env=self.env(), text=True,
                            capture_output=True, timeout=120)
        return json.loads(cp.stdout)


@pytest.fixture()
def fx(tmp_path):
    return Fixture(tmp_path)


# ─────────────────────── 1. 双章成功 ───────────────────────
def test_01_dual_chapter_success_fields_and_sha(fx: Fixture):
    rc, payload, _ = fx.run_builder(expect_rc=0)
    assert payload.get('status') == 'G3_BUILT', payload
    assert payload.get('chapters') == [FIX_A, FIX_B]

    prev_sha = sha256_file(fx.prev)
    prev_cjk = net_cjk(fx.prev.read_text(encoding='utf-8'))
    g1_sha, g2_sha = sha256_file(fx.g1), sha256_file(fx.g2)
    outline_sha = sha256_file(fx.outline)

    for ch in (FIX_A, FIX_B):
        d = fx.prep(ch)
        assert d['chapter'] == ch
        assert d['state'] == 'G3_READY'
        assert d['schema_version']
        assert d['generated_at']
        assert d['title'] == OUTLINE_ROWS[ch].split('|')[2].strip()
        assert d['volume'].replace('：', '·') == VOLUME
        assert d['outline_ref']
        assert d['outline_raw'].startswith(f'第{ch}章')
        assert d['target_chars'] == int(OUTLINE_ROWS[ch].rsplit('|', 1)[1].strip())
        # plot_seed 必须来自大纲主体，不得脑补
        body = OUTLINE_ROWS[ch].split('|')[3].strip()
        assert d['plot_seed'] == body
        assert d['foreshadow'] == OUTLINE_ROWS[ch].split('|')[4].strip()
        # 前章链
        assert d['entry_interface'] and isinstance(d['entry_interface'], list)
        # G1 / G2 引用
        assert d['g1_ref']['verdict'] == 'ALLOW_G2'
        assert d['g1_ref']['target_chapters'] == [FIX_A, FIX_B]
        assert 'G1_material_match.json' in d['g1_ref']['artifact']
        assert d['g2_ref']['verdict'] in ('NOTE_LAYER',)
        assert 'G2_verdict.json' in d['g2_ref']['artifact']
        assert d['g2_ref']['material_summary']['bridged_cards'] == 40
        # hard gates
        hg = d['hard_gates']
        assert hg['first_line'] == f'第{ch}章 {d["title"]}'
        assert hg['last_line'] == '（本章完）'
        assert hg['cjk_min'] == 3200
        assert hg['cjk_max'] == 10000
        assert hg['numeral_style']
        # provenance
        pv = d['provenance_sha256']
        assert pv['g1'] == g1_sha and pv['g2'] == g2_sha and pv['outline'] == outline_sha
        assert pv['prev'] == prev_sha

    a, b = fx.prep(FIX_A), fx.prep(FIX_B)
    assert a['prev_chapter'] == FIX_FRONTIER
    assert a['prev_sha256'] == prev_sha
    assert a['prev_net_cjk'] == prev_cjk
    # 第二章的前章是本轮第一章：串行依赖，须显式标注而非伪造 SHA
    assert b['prev_chapter'] == FIX_A
    assert b['prev_sha256'] in (None, '')
    assert b['prev_pending'] is True

    agg = json.loads((fx.out / 'G3_prep.json').read_text(encoding='utf-8'))
    assert [c['chapter'] for c in agg['chapters']] == [FIX_A, FIX_B]
    for c in agg['chapters']:
        assert c['sha256'] == sha256_file(fx.prep_path(c['chapter']))

    v = fx.dispatch_g3()
    assert v['status'] == 'VERIFIED', v


# ─────────────── 2. 缺章 / 错章号 / 空 plot_seed → dispatcher FAIL ───────────────
def test_02a_missing_one_chapter_not_verified(fx: Fixture):
    fx.run_builder(expect_rc=0)
    fx.prep_path(FIX_B).unlink()
    v = fx.dispatch_g3()
    assert v['status'] != 'VERIFIED' and v['ok'] is False, v


def test_02b_wrong_chapter_number_invalid(fx: Fixture):
    fx.run_builder(expect_rc=0)
    d = fx.prep(FIX_B)
    d['chapter'] = 999
    fx.prep_path(FIX_B).write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
    v = fx.dispatch_g3()
    assert v['status'] == 'INVALID', v


def test_02c_empty_plot_seed_invalid(fx: Fixture):
    fx.run_builder(expect_rc=0)
    d = fx.prep(FIX_A)
    d['plot_seed'] = ''
    fx.prep_path(FIX_A).write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
    v = fx.dispatch_g3()
    assert v['status'] == 'INVALID', v


# ─────────── 3. G1/G2 缺失或 target mismatch 硬失败且不留半成品 ───────────
def test_03a_g1_missing_hard_fail_no_partial(tmp_path):
    fx = Fixture(tmp_path, drop_g1=True)
    rc, payload, _ = fx.run_builder()
    assert rc != 0
    assert 'G1' in json.dumps(payload, ensure_ascii=False)
    assert fx.prep_files() == []
    assert not (fx.out / 'G3_prep.json').exists()


def test_03b_g2_missing_hard_fail_no_partial(tmp_path):
    fx = Fixture(tmp_path, drop_g2=True)
    rc, payload, _ = fx.run_builder()
    assert rc != 0
    assert 'G2' in json.dumps(payload, ensure_ascii=False)
    assert fx.prep_files() == []


def test_03c_g1_target_mismatch_hard_fail(tmp_path):
    fx = Fixture(tmp_path, g1_targets=[301, 302])
    rc, payload, _ = fx.run_builder()
    assert rc != 0
    assert 'target' in json.dumps(payload, ensure_ascii=False).lower()
    assert fx.prep_files() == []


def test_03d_g2_target_mismatch_hard_fail(tmp_path):
    fx = Fixture(tmp_path, g2_targets=[FIX_A])
    rc, payload, _ = fx.run_builder()
    assert rc != 0
    assert fx.prep_files() == []


def test_03e_g2_blocking_verdict_hard_fail(tmp_path):
    fx = Fixture(tmp_path)
    d = json.loads(fx.g2.read_text(encoding='utf-8'))
    d['verdict'] = 'BLOCK_G3_PENDING_PRIMARY_SOURCE'
    d['final_verdict'] = d['verdict']
    fx.g2.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
    rc, payload, _ = fx.run_builder()
    assert rc != 0
    assert fx.prep_files() == []


# ─────────── 4. 大纲章缺失 / 重复 硬失败 ───────────
def test_04a_outline_chapter_missing_hard_fail(tmp_path):
    fx = Fixture(tmp_path, outline_chapters=[418, 419, 420, 421, 423])  # 缺 422
    rc, payload, _ = fx.run_builder()
    assert rc != 0
    assert str(FIX_B) in json.dumps(payload, ensure_ascii=False)
    assert fx.prep_files() == []


def test_04b_outline_chapter_duplicate_hard_fail(tmp_path):
    fx = Fixture(tmp_path, duplicate_outline_chapter=FIX_A)
    rc, payload, _ = fx.run_builder()
    assert rc != 0
    assert 'duplicate' in json.dumps(payload, ensure_ascii=False).lower()
    assert fx.prep_files() == []


# ─────────── 5. 前章缺失硬失败 ───────────
def test_05a_prev_chapter_missing_hard_fail(tmp_path):
    fx = Fixture(tmp_path, write_prev=False)
    rc, payload, _ = fx.run_builder()
    assert rc != 0
    assert str(FIX_FRONTIER) in json.dumps(payload, ensure_ascii=False)
    assert fx.prep_files() == []


def test_05b_prev_chapter_empty_hard_fail(tmp_path):
    fx = Fixture(tmp_path)
    fx.prev.write_text('', encoding='utf-8')
    rc, payload, _ = fx.run_builder()
    assert rc != 0
    assert fx.prep_files() == []


# ─────────── 6. G2 章级强制约束不得丢 ───────────
def test_06_g2_chapter_constraints_preserved(fx: Fixture):
    fx.run_builder(expect_rc=0)
    a, b = fx.prep(FIX_A), fx.prep(FIX_B)
    joined_a = '\n'.join(a['locked_constraints'])
    joined_b = '\n'.join(b['locked_constraints'])
    assert G2_CHAPTER_POINT_A in joined_a
    assert G2_CHAPTER_POINT_A not in joined_b
    assert G2_CHAPTER_POINT_B in joined_b
    # 区间备注覆盖两章
    assert G2_RANGE_POINT in joined_a and G2_RANGE_POINT in joined_b
    # 无章号的全局备注不得混进章级约束，但须留引用
    assert G2_GLOBAL_POINT not in joined_a
    assert G2_GLOBAL_POINT in '\n'.join(
        p['point'] for p in a['g2_ref']['note_layer'])
    assert any('BLOCKING' in c for c in a['locked_constraints'])
    assert a['g2_ref']['chapter_note_count'] == len(a['locked_constraints'])


# ─────────── 7. 幂等：字节与 mtime 全同 ───────────
def test_07_idempotent_bytes_and_mtime(fx: Fixture):
    fx.run_builder(expect_rc=0)
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns)
              for p in fx.prep_files() + [fx.out / 'G3_prep.json']}
    rc, payload, _ = fx.run_builder(expect_rc=0)
    assert payload.get('rebuilt') is False, payload
    for p, (data, mtime) in before.items():
        assert p.read_bytes() == data, f'bytes changed: {p}'
        assert p.stat().st_mtime_ns == mtime, f'mtime changed: {p}'


# ─────────── 8. 输入 SHA 变后重建 ───────────
def test_08_input_change_triggers_rebuild(fx: Fixture):
    fx.run_builder(expect_rc=0)
    old = fx.prep_path(FIX_A).read_bytes()
    old_prev_sha = fx.prep(FIX_A)['prev_sha256']
    fx.prev.write_text(PREV_BODY + '\n前沿章追加一段，改变前章 SHA。\n', encoding='utf-8')
    rc, payload, _ = fx.run_builder(expect_rc=0)
    assert payload.get('rebuilt') is True, payload
    assert fx.prep_path(FIX_A).read_bytes() != old
    assert fx.prep(FIX_A)['prev_sha256'] != old_prev_sha
    assert fx.prep(FIX_A)['prev_sha256'] == sha256_file(fx.prev)


# ─────────── 9 / 10. control tick 一次 tick 闭环 + 变异自证 ───────────
def _load_tick(fx: Fixture):
    """在进程内加载 control tick（env 在 import 时被读取，故须清缓存重载）。"""
    for k, v in fx.env().items():
        os.environ[k] = v
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    for mod in ('kewu_daily_control_tick', 'kewu_daily_transition_dispatcher',
                'kewu_daily_seed'):
        sys.modules.pop(mod, None)
    return importlib.import_module('kewu_daily_control_tick')


def _drive_to_g3_pending(fx: Fixture, tick_mod) -> None:
    """seed → G1 ACK → G2 ACK，停在 G3 PENDING。"""
    fx.seed()
    for _ in range(3):
        tick_mod.tick()
    acked = [r['transition'] for r in fx.ledger() if r.get('type') == 'TRANSITION_ACK']
    assert acked == ['seed', 'G1', 'G2'], acked
    pend = [r['transition'] for r in fx.ledger() if r.get('type') == 'TRANSITION_PENDING']
    assert pend[-1] == 'G3', pend
    assert fx.prep_files() == []


def test_09_single_tick_autoruns_builder_then_acks_g3(fx: Fixture, monkeypatch):
    tick_mod = _load_tick(fx)
    _drive_to_g3_pending(fx, tick_mod)

    rc = tick_mod.tick()
    assert rc == 0

    rows = fx.ledger()
    acked = [r['transition'] for r in rows if r.get('type') == 'TRANSITION_ACK']
    assert acked == ['seed', 'G1', 'G2', 'G3'], acked
    # 不得先 WAIT / ATTEMPT 三次
    g3_attempts = [r for r in rows if r.get('type') == 'TRANSITION_ATTEMPT'
                   and r.get('transition') == 'G3']
    assert g3_attempts == [], g3_attempts
    assert not any(r.get('type') == 'REPAIR_LIMIT' for r in rows)
    # auto-run 留痕
    assert any(r.get('type') == 'TRANSITION_AUTO_BUILD' and r.get('transition') == 'G3'
               for r in rows), [r.get('type') for r in rows]
    # 产物真落盘 + 后继唯一
    assert [p.name for p in fx.prep_files()] == [f'G3_PREP_{FIX_A}.json',
                                                 f'G3_PREP_{FIX_B}.json']
    pend = [r['transition'] for r in rows if r.get('type') == 'TRANSITION_PENDING']
    assert pend[-1] == 'G4A', pend
    # 队列不得因 G3 产生噪声
    q = Path(os.environ['KEWU_DAILY_ACTION_QUEUE'])
    qrows = ([json.loads(x) for x in q.read_text(encoding='utf-8').splitlines() if x.strip()]
             if q.exists() else [])
    assert [r for r in qrows if r.get('transition') == 'G3'] == []


def test_10_mutation_disabling_autorun_breaks_test_09(fx: Fixture, monkeypatch):
    """变异自证：禁用 auto-run 分支后，#9 的断言必须失败。"""
    tick_mod = _load_tick(fx)
    _drive_to_g3_pending(fx, tick_mod)

    monkeypatch.setattr(tick_mod, 'AUTO_BUILDERS', {}, raising=True)
    tick_mod.tick()

    rows = fx.ledger()
    acked = [r['transition'] for r in rows if r.get('type') == 'TRANSITION_ACK']
    assert 'G3' not in acked, '禁用 auto-run 后 G3 仍被 ACK，说明 #9 不是 auto-run 挣来的'
    assert fx.prep_files() == []
    assert any(r.get('type') == 'TRANSITION_ATTEMPT' and r.get('transition') == 'G3'
               for r in rows)


# ─────────── 11. 历史回归：无 313/314 硬编码 ───────────
FORBIDDEN_TOKENS = ('313', '314', '谢云', '林星辰', '方宁', '周棠', '铁幕',
                    '八百零九千瓦', '三一九开尔文', '两千四百')


def test_11a_builder_source_has_no_chapter_hardcoding():
    src = BUILDER.read_text(encoding='utf-8')
    for tok in FORBIDDEN_TOKENS:
        assert tok not in src, f'builder 源码含历史硬编码: {tok}'


def test_11b_artifacts_only_contain_fixture_facts(fx: Fixture):
    fx.run_builder(expect_rc=0)
    blob = '\n'.join(p.read_text(encoding='utf-8') for p in fx.prep_files())
    blob += (fx.out / 'G3_prep.json').read_text(encoding='utf-8')
    for tok in FORBIDDEN_TOKENS:
        assert tok not in blob, f'产物含历史硬编码: {tok}'
    assert f'第{FIX_A}章' in blob and f'第{FIX_B}章' in blob


def test_11c_dry_run_writes_nothing(fx: Fixture):
    rc, payload, _ = fx.run_builder('--dry-run', expect_rc=0)
    assert payload.get('status') in ('G3_DRY_RUN',)
    assert fx.prep_files() == []
    assert not (fx.out / 'G3_prep.json').exists()


def test_11d_chapters_resolved_from_seed_when_not_given(fx: Fixture):
    fx.seed()
    cp = subprocess.run([PY, str(BUILDER), '--task-dir', str(fx.task)],
                        env=fx.env(), text=True, capture_output=True, timeout=180)
    assert cp.returncode == 0, (cp.stdout, cp.stderr[-800:])
    payload = json.loads(cp.stdout.strip().splitlines()[-1])
    assert payload['chapters'] == [FIX_A, FIX_B], payload
