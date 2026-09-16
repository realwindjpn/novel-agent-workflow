#!/usr/bin/env python3
"""kewu_g4_release_gate.py G4 签发器加固的 TDD 测试（CLI 公共接口）。

既有背景（r2）：issue 无候选可签发 PRE_AUTHOR_RELEASE（放行早于作者），
候选 SHA 校验推迟到 post-author 的 check/discover 显式 --candidate。

r5 加固目标（两席异构审计 OPUS/QWEN38 确认的残余缺陷）：
1. 假通过封堵：check/discover 输出暴露 phase 与 candidate_checked；
   已绑定候选（artifacts.candidate 或 phase=POST_AUTHOR_BINDING）而调用未传
   --candidate 时判 candidate_not_supplied FAIL（test_02 原断言锁定漏洞，已改）。
2. 必需字段 fail-closed：phase ∈ {PRE,POST}、issued_at 带时区 ISO8601、
   phase 与 artifacts.candidate 一致性、传 --candidate 时 phase 必须 POST；
   旧版无 phase 凭证判 release_schema_too_old。
3. issue 禁静默覆盖：目标存在即拒绝，除非 --rebind；失败自验只删本次新建文件。
4. discover 收敛：显式与扫描路径必须位于 --task-root 之下（resolve 后判定）。
5. _validate_multi author_route 无条件；issue 章号锚点 JSON 精确比较（解析失败回退子串+warning）。

所有用例走 CLI 公共接口 + 临时目录，绝不触碰生产任务包/正文/草稿箱。
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path('/root/.hermes/scripts')
G4 = SCRIPTS / 'kewu_g4_release_gate.py'
CHAPTER = 320


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_cli(*args: str, cwd: Path | None = None,
            env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(
        [sys.executable, str(G4), *args],
        text=True, capture_output=True, timeout=30, cwd=str(cwd) if cwd else None,
        env=e,
    )


def run_cli_env(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess:
    return run_cli(*args, env=env)


class Fixture:
    def __init__(self, root: Path):
        self.root = root
        self.task = root / 'task'
        self.task.mkdir(parents=True, exist_ok=True)
        # G2 必须含 issue() 白名单裁决 marker；G3 必须含目标章号。
        self.g2 = self.task / 'G2_FINAL_VERDICT.md'
        self.g2.write_text('VERDICT: NOTE_ONLY\n\n- 备注层裁决，无正文注入。\n', encoding='utf-8')
        self.g3 = self.task / 'G3_CHAPTER_PREP_PACKAGE.md'
        self.g3.write_text(f'# G3 准备包（含第{CHAPTER}章条目）\n\n- 章号锚点：{CHAPTER}\n', encoding='utf-8')
        self.g1 = self.task / 'G1_TODAY_MATERIAL_POOL_RECONCILE.md'
        self.g1.write_text('# G1 当日素材池核定\n\n- 结论：ALLOW_G2\n- 卡数：1\n', encoding='utf-8')

    def make_candidate(self, name: str = 'candidate.md', body: str | None = None) -> Path:
        p = self.task / name
        p.write_text(body or f'第{CHAPTER}章 候选正文\n' + '正文内容。' * 40 + '\n', encoding='utf-8')
        return p

    def make_g3_json(self, chapter: int, note: str = '') -> Path:
        p = self.task / f'G3_PREP_{chapter}.json'
        p.write_text(json.dumps({'chapter': chapter, 'note': note or f'第{chapter}章 准备包'}, ensure_ascii=False),
                     encoding='utf-8')
        return p

    def make_multi_release(self, route: str = 'web_qwen', path: str = 'G4_RELEASE_MULTI.json') -> Path:
        """构造多章 schema 凭证（chapters/release/binding），用于 _validate_multi 路径。"""
        mg1 = self.task / 'mg1.json'
        mg1.write_text(json.dumps({'src': 'G1', 'k': 'v' * 60}, ensure_ascii=False), encoding='utf-8')
        mg2 = self.task / 'mg2.json'
        mg2.write_text(json.dumps({'verdict': 'NOTE_ONLY'}, ensure_ascii=False), encoding='utf-8')
        mg3 = self.task / 'mg3.json'
        mg3.write_text(json.dumps({'chapter': CHAPTER, 'prep': 'x' * 60}, ensure_ascii=False), encoding='utf-8')
        data = {
            'schema': 'kewu.g4-release.v1',
            'chapters': [CHAPTER],
            'release': True,
            'author_route': route,
            'binding': {
                'g1': {'json': str(mg1), 'json_sha256': sha(mg1)},
                'g2': {'verdict': str(mg2), 'verdict_sha256': sha(mg2)},
                'g3': {f'prep_{CHAPTER}': str(mg3), f'prep_{CHAPTER}_sha256': sha(mg3)},
            },
        }
        p = self.task / path
        p.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        return p

    @property
    def release(self) -> Path:
        return self.task / 'G4_RELEASE.json'

    def load_release(self) -> dict:
        return json.loads(self.release.read_text(encoding='utf-8'))

    def save_release(self, data: dict) -> None:
        self.release.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')


@pytest.fixture()
def fx(tmp_path: Path) -> Fixture:
    return Fixture(tmp_path)


def _issue_no_candidate(fx: Fixture) -> subprocess.CompletedProcess:
    return run_cli(
        'issue', '--task-dir', str(fx.task), '--chapter', str(CHAPTER),
        '--g1', str(fx.g1), '--g2', str(fx.g2), '--g3', str(fx.g3),
        '--author-route-kind', 'web_qwen',
    )


def test_01_issue_without_candidate_succeeds_and_check_ok(fx: Fixture) -> None:
    """红测：无 --candidate 也能签发 PRE_AUTHOR_RELEASE，随后 check ok=true 且输出暴露 phase/candidate_checked。"""
    cp = _issue_no_candidate(fx)
    assert cp.returncode == 0, f'issue refused without candidate:\n{cp.stderr}\n{cp.stdout}'
    assert fx.release.exists(), 'G4_RELEASE.json not written'

    data = fx.load_release()
    assert data['chapter'] == CHAPTER
    assert data['g1_verified'] is True and data['g2_verified'] is True and data['g3_verified'] is True
    assert data['author_route_kind'] == 'web_qwen'
    assert data['phase'] == 'PRE_AUTHOR_RELEASE'
    issued = datetime.datetime.fromisoformat(data['issued_at'])
    assert issued.tzinfo is not None and issued.tzinfo.utcoffset(issued) is not None, \
        'issued_at 必须是带时区 ISO8601'
    assert 'candidate' not in (data.get('artifacts') or {}), \
        'PRE_AUTHOR_RELEASE 不得绑定候选'

    check = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER))
    assert check.returncode == 0, f'check failed after pre-author issue:\n{check.stdout}\n{check.stderr}'
    payload = json.loads(check.stdout)
    assert payload['ok'] is True
    assert payload.get('phase') == 'PRE_AUTHOR_RELEASE', \
        'check 输出必须暴露 phase（假通过封堵）'
    assert payload.get('candidate_checked') is False, \
        'PRE 凭证未传候选时 candidate_checked 必须为 false'


def test_02_explicit_candidate_binds_and_check_verifies_sha(fx: Fixture) -> None:
    """post-author 绑定：显式 --candidate 后 release 绑定候选 SHA，check 同候选 ok；
    已绑定候选的凭证在不传 --candidate 时必须 candidate_not_supplied FAIL（原断言锁定漏洞，已改）。"""
    cand = fx.make_candidate()
    cp = run_cli(
        'issue', '--task-dir', str(fx.task), '--chapter', str(CHAPTER),
        '--g1', str(fx.g1), '--g2', str(fx.g2), '--g3', str(fx.g3),
        '--candidate', str(cand), '--author-route-kind', 'web_qwen',
    )
    assert cp.returncode == 0, f'issue with candidate refused:\n{cp.stderr}\n{cp.stdout}'
    data = fx.load_release()
    assert data['phase'] == 'POST_AUTHOR_BINDING'
    spec = data['artifacts']['candidate']
    assert spec['path'] == str(cand.resolve())
    assert spec['sha256'] == sha(cand), 'release 候选 SHA 未绑定真实文件'
    assert data['issued_at']  # 显式 candidate 也要 issued_at

    check = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER),
                    '--candidate', str(cand))
    assert check.returncode == 0 and json.loads(check.stdout)['ok'] is True, check.stdout

    check_plain = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER))
    assert check_plain.returncode != 0, \
        '已绑定候选的 POST 凭证不传 --candidate 必须 FAIL（假通过封堵）'
    plain_errors = json.loads(check_plain.stdout)['errors']
    assert 'candidate_not_supplied' in plain_errors, plain_errors
    assert json.loads(check_plain.stdout).get('candidate_checked') is False


def test_03_tampered_candidate_refused_by_check(fx: Fixture) -> None:
    """篡改候选文件后 post-author check 必须 FAIL。"""
    cand = fx.make_candidate()
    cp = run_cli(
        'issue', '--task-dir', str(fx.task), '--chapter', str(CHAPTER),
        '--g1', str(fx.g1), '--g2', str(fx.g2), '--g3', str(fx.g3),
        '--candidate', str(cand), '--author-route-kind', 'web_qwen',
    )
    assert cp.returncode == 0
    cand.write_text(cand.read_text(encoding='utf-8') + '篡改', encoding='utf-8')
    check = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER),
                    '--candidate', str(cand))
    assert check.returncode != 0, '篡改后的候选不得通过 check'
    errors = json.loads(check.stdout)['errors']
    assert 'candidate_hash_mismatch' in errors, errors
    assert json.loads(check.stdout).get('candidate_checked') is False


@pytest.mark.parametrize('key', ['g1', 'g2', 'g3'])
def test_04_tampered_upstream_refused_by_check(fx: Fixture, key: str) -> None:
    """篡改任一上游 G1/G2/G3 文件后，无候选 check 必须 FAIL。"""
    cp = run_cli(
        'issue', '--task-dir', str(fx.task), '--chapter', str(CHAPTER),
        '--g1', str(fx.g1), '--g2', str(fx.g2), '--g3', str(fx.g3),
        '--author-route-kind', 'web_qwen',
    )
    assert cp.returncode == 0
    upstream = {'g1': fx.g1, 'g2': fx.g2, 'g3': fx.g3}[key]
    upstream.write_text(upstream.read_text(encoding='utf-8') + '篡改', encoding='utf-8')
    check = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER))
    assert check.returncode != 0, f'{key} 篡改后不得通过 check'
    assert any(e.startswith(f'{key}_hash_mismatch') or e.startswith(f'{key}_')
               for e in json.loads(check.stdout)['errors']), json.loads(check.stdout)['errors']


def test_05_chapter_and_route_mismatch_refused(fx: Fixture) -> None:
    """错章 / 路由不匹配均不得放行。"""
    cp = run_cli(
        'issue', '--task-dir', str(fx.task), '--chapter', str(CHAPTER),
        '--g1', str(fx.g1), '--g2', str(fx.g2), '--g3', str(fx.g3),
        '--author-route-kind', 'web_qwen',
    )
    assert cp.returncode == 0

    wrong_chapter = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER + 1))
    assert wrong_chapter.returncode != 0
    assert 'chapter_mismatch' in json.loads(wrong_chapter.stdout)['errors']

    wrong_route = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER),
                          '--author-route-kind', 'api_qwen37_trial')
    assert wrong_route.returncode != 0
    assert any(e.startswith('author_route_mismatch') for e in json.loads(wrong_route.stdout)['errors'])


def test_06_discover_output_exposes_phase_and_candidate_checked(fx: Fixture) -> None:
    """discover 输出同样暴露 phase/candidate_checked；POST 命中需显式候选。"""
    cp = _issue_no_candidate(fx)
    assert cp.returncode == 0
    disc = run_cli('discover', '--task-root', str(fx.task), '--chapter', str(CHAPTER))
    payload = json.loads(disc.stdout)
    assert disc.returncode == 0 and payload['ok'] is True, payload
    assert payload.get('phase') == 'PRE_AUTHOR_RELEASE'
    assert payload.get('candidate_checked') is False

    # POST 凭证 + 显式候选 → discover 命中且 candidate_checked=true
    cand = fx.make_candidate()
    run_cli(
        'issue', '--task-dir', str(fx.task), '--chapter', str(CHAPTER),
        '--g1', str(fx.g1), '--g2', str(fx.g2), '--g3', str(fx.g3),
        '--candidate', str(cand), '--author-route-kind', 'web_qwen', '--rebind',
    )
    disc2 = run_cli('discover', '--task-root', str(fx.task), '--chapter', str(CHAPTER),
                    '--candidate', str(cand))
    payload2 = json.loads(disc2.stdout)
    assert disc2.returncode == 0, payload2
    assert payload2.get('phase') == 'POST_AUTHOR_BINDING'
    assert payload2.get('candidate_checked') is True


def test_07_required_fields_fail_closed(fx: Fixture) -> None:
    """必需字段 fail-closed：phase/issued_at/一致性；缺 phase 判 release_schema_too_old。"""
    cp = _issue_no_candidate(fx)
    assert cp.returncode == 0

    # a) 删 phase → release_schema_too_old（旧版凭证一次性判死）
    d = fx.load_release()
    d.pop('phase')
    fx.save_release(d)
    r = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER))
    assert r.returncode != 0
    assert 'release_schema_too_old' in json.loads(r.stdout)['errors']

    # b) phase 未知值 → invalid_phase
    d = fx.load_release()
    d['phase'] = 'UNKNOWN_PHASE'
    fx.save_release(d)
    r = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER))
    assert r.returncode != 0
    assert any(e.startswith('invalid_phase') for e in json.loads(r.stdout)['errors'])

    # c) issued_at 无时区 → issued_at_no_tz
    d = fx.load_release()
    d['phase'] = 'PRE_AUTHOR_RELEASE'
    d['issued_at'] = '2026-09-09T14:27:50'
    fx.save_release(d)
    r = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER))
    assert r.returncode != 0
    assert 'issued_at_no_tz' in json.loads(r.stdout)['errors']

    # d) issued_at 非法 → issued_at_invalid
    d = fx.load_release()
    d['issued_at'] = 'not-a-date'
    fx.save_release(d)
    r = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER))
    assert r.returncode != 0
    assert 'issued_at_invalid' in json.loads(r.stdout)['errors']

    # e) PRE + artifacts.candidate → pre_auth_with_candidate
    d = fx.load_release()
    d['issued_at'] = '2026-09-09T14:27:50+08:00'
    cand = fx.make_candidate('cand_e.md')
    d['artifacts']['candidate'] = {'path': str(cand), 'sha256': sha(cand)}
    fx.save_release(d)
    r = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER))
    assert r.returncode != 0
    assert 'pre_auth_with_candidate' in json.loads(r.stdout)['errors']

    # f) POST + 缺 candidate 条目 → post_auth_without_candidate
    d = fx.load_release()
    d['phase'] = 'POST_AUTHOR_BINDING'
    d.pop('artifacts', None)
    fx.save_release(d)
    r = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER),
                '--candidate', str(cand))
    assert r.returncode != 0
    errs = json.loads(r.stdout)['errors']
    assert 'post_auth_without_candidate' in errs, errs

    # g) PRE 凭证 + --candidate → candidate_requires_post_phase
    cp = run_cli(
        'issue', '--task-dir', str(fx.task), '--chapter', str(CHAPTER),
        '--g1', str(fx.g1), '--g2', str(fx.g2), '--g3', str(fx.g3),
        '--author-route-kind', 'web_qwen', '--rebind',
    )
    assert cp.returncode == 0
    r = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER),
                '--candidate', str(fx.make_candidate('cand_g.md')))
    assert r.returncode != 0
    errs = json.loads(r.stdout)['errors']
    assert any(e.startswith('candidate_requires_post_phase') for e in errs), errs


def test_08_issue_no_silent_overwrite(fx: Fixture) -> None:
    """issue 禁静默覆盖：已存在即 REFUSE，除非 --rebind；失败 rebind 不销毁旧凭证。"""
    cp = _issue_no_candidate(fx)
    assert cp.returncode == 0
    old_sha = sha(fx.release)
    old_data = fx.load_release()

    # a) 重复 issue 无 --rebind → REFUSE:release_already_exists，旧凭证原样
    r = run_cli(
        'issue', '--task-dir', str(fx.task), '--chapter', str(CHAPTER),
        '--g1', str(fx.g1), '--g2', str(fx.g2), '--g3', str(fx.g3),
        '--author-route-kind', 'web_qwen',
    )
    assert r.returncode != 0
    assert 'release_already_exists' in (r.stdout + r.stderr), (r.stdout, r.stderr)
    assert sha(fx.release) == old_sha, '无 --rebind 的重复 issue 不得动旧凭证'
    assert fx.load_release() == old_data

    # b) --rebind + 合法候选 → POST_AUTHOR_BINDING 成功
    cand = fx.make_candidate()
    r = run_cli(
        'issue', '--task-dir', str(fx.task), '--chapter', str(CHAPTER),
        '--g1', str(fx.g1), '--g2', str(fx.g2), '--g3', str(fx.g3),
        '--candidate', str(cand), '--author-route-kind', 'web_qwen', '--rebind',
    )
    assert r.returncode == 0, f'rebind refused:\n{r.stdout}\n{r.stderr}'
    assert fx.load_release()['phase'] == 'POST_AUTHOR_BINDING'
    check = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER),
                    '--candidate', str(cand))
    assert check.returncode == 0 and json.loads(check.stdout)['ok'] is True, check.stdout

    # c) 失败 rebind 不销毁旧凭证（坏 g2 无裁决 marker → 自验 REFUSE）
    bad_g2 = fx.task / 'G2_BAD.md'
    bad_g2.write_text('# 无裁决 marker 的坏 G2\n', encoding='utf-8')
    r = run_cli(
        'issue', '--task-dir', str(fx.task), '--chapter', str(CHAPTER),
        '--g1', str(fx.g1), '--g2', str(bad_g2), '--g3', str(fx.g3),
        '--author-route-kind', 'web_qwen', '--rebind',
    )
    assert r.returncode != 0, '坏 G2 的 rebind 必须 REFUSE'
    assert fx.release.exists(), '失败 rebind 不得删除既有凭证'
    assert fx.load_release()['phase'] == 'POST_AUTHOR_BINDING', \
        '失败 rebind 后凭证仍须是 rebind 前的 POST 版本'
    check2 = run_cli('check', '--release', str(fx.release), '--chapter', str(CHAPTER),
                     '--candidate', str(cand))
    assert check2.returncode == 0 and json.loads(check2.stdout)['ok'] is True, check2.stdout


def test_09_discover_confinement_to_task_root(fx: Fixture) -> None:
    """discover 收敛：显式 KEWU_G4_RELEASE 与扫描路径必须位于 --task-root 之下。"""
    # task-root 内正常 PRE 凭证 → discover ok
    cp = _issue_no_candidate(fx)
    assert cp.returncode == 0
    disc = run_cli('discover', '--task-root', str(fx.task), '--chapter', str(CHAPTER))
    assert disc.returncode == 0 and json.loads(disc.stdout)['ok'] is True

    # task-root 外合法凭证 + 显式 env → release_outside_task_root FAIL
    outside = fx.root / 'outside'
    outside.mkdir(parents=True, exist_ok=True)
    ofx = Fixture(fx.root / 'outside_holder')
    _issue_no_candidate(ofx)
    ext_release = ofx.release
    assert ext_release.exists()
    disc2 = run_cli('discover', '--task-root', str(fx.task), '--chapter', str(CHAPTER),
                    env={'KEWU_G4_RELEASE': str(ext_release)})
    payload2 = json.loads(disc2.stdout)
    assert disc2.returncode != 0, 'task-root 外的凭证不得放行'
    assert any('release_outside_task_root' in e for e in payload2['errors']), payload2['errors']


def test_10_multi_route_unconditional_and_g3_exact_chapter(fx: Fixture) -> None:
    """_validate_multi 的 author_route 无条件检查；issue 章号锚点 JSON 精确比较。"""
    # a) 多章凭证路由为空 / trial 校验 → author_route_mismatch（不再仅默认路由）
    mel = fx.make_multi_release(route='')
    r = run_cli('check', '--release', str(mel), '--chapter', str(CHAPTER),
                '--author-route-kind', 'api_qwen37_trial')
    assert r.returncode != 0
    assert any(e.startswith('author_route_mismatch') for e in json.loads(r.stdout)['errors'])

    mel2 = fx.make_multi_release(route='web_qwen', path='G4_RELEASE_MULTI2.json')
    r2 = run_cli('check', '--release', str(mel2), '--chapter', str(CHAPTER),
                 '--author-route-kind', 'api_qwen37_trial')
    assert r2.returncode != 0
    assert any(e.startswith('author_route_mismatch') for e in json.loads(r2.stdout)['errors'])

    # b) G3 为 JSON 且精确命中章号 → issue 成功
    g3j = fx.make_g3_json(CHAPTER, note='纯 JSON 准备包')
    r = run_cli(
        'issue', '--task-dir', str(fx.task), '--chapter', str(CHAPTER),
        '--g1', str(fx.g1), '--g2', str(fx.g2), '--g3', str(g3j),
        '--author-route-kind', 'web_qwen', '--rebind',
    )
    assert r.returncode == 0, f'JSON G3 精确命中应签发:\n{r.stdout}\n{r.stderr}'

    # c) G3 JSON 章号 1320 但文本含 "320" 子串 → 必须拒绝（子串匹配会误放行）
    g3trap = fx.make_g3_json(1320, note=f'参考第{CHAPTER}章内容，避免子串误判')
    assert '320' in g3trap.read_text(encoding='utf-8')  # 陷阱成立：子串存在
    r = run_cli(
        'issue', '--task-dir', str(fx.task), '--chapter', str(CHAPTER),
        '--g1', str(fx.g1), '--g2', str(fx.g2), '--g3', str(g3trap),
        '--author-route-kind', 'web_qwen', '--rebind',
    )
    assert r.returncode != 0, 'JSON 章号精确不匹配时必须拒绝（g3_chapter_marker_missing）'
    assert 'g3_chapter_marker_missing' in (r.stdout + r.stderr), (r.stdout, r.stderr)

    # d) G3 非 JSON（md）→ 回退子串匹配 + stderr WARNING（独立目录，避开前面 rebind 占用）
    md_fx = Fixture(fx.root / 'md_sub')
    cp = _issue_no_candidate(md_fx)
    assert cp.returncode == 0, f'md G3 子串回退应可签发:\n{cp.stdout}\n{cp.stderr}'
    assert 'WARNING' in cp.stderr, '非 JSON G3 须输出 warning 说明回退子串匹配'