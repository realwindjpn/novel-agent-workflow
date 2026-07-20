#!/usr/bin/env python3
"""Public release gate for novel-agent-workflow.

The gate checks the files that would be published: git-tracked files plus
untracked, non-ignored files. It also verifies that internal working artifacts
stay ignored and untracked, that required public files exist, that the test
suite passes, and that the CLI smoke blocks chapter issuance before outline
lock.

The deny-list and scanner self-exclusion live in
``src/novel_workflow/_security.py`` and are shared with
``novel_workflow.core.security_scan`` so the two surfaces cannot drift. The
scanner self-excludes its own source files by *path relative to the project
root*, never by bare filename, so a contributor's same-named file elsewhere is
still scanned.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from novel_workflow._security import (  # noqa: E402
    SELF_EXCLUDE_RELS,
    TEXT_EXT,
    deny_list_findings,
)

INTERNAL_PATHS = {"WAL.md", "SECURITY_RELEASE_CHECKLIST.md"}
INTERNAL_DIRS = {"output"}

issues: list[str] = []


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)


def _tracked() -> set[str]:
    proc = _git("ls-files")
    if proc.returncode != 0:
        issues.append("git ls-files failed; cannot enumerate tracked files")
        return set()
    return {line for line in proc.stdout.splitlines() if line}


def _untracked_public() -> set[str]:
    proc = _git("ls-files", "--others", "--exclude-standard")
    if proc.returncode != 0:
        issues.append("git ls-files --others failed; cannot enumerate untracked public files")
        return set()
    return {line for line in proc.stdout.splitlines() if line}


def _is_internal(rel: str) -> bool:
    parts = Path(rel).parts
    return rel in INTERNAL_PATHS or any(
        part in INTERNAL_DIRS or part == ".novel-workflow" for part in parts
    )


tracked = _tracked()
public_candidates = tracked | _untracked_public()

for rel in sorted(public_candidates):
    if _is_internal(rel):
        issues.append(f"internal working file is publishable: {rel}")
        continue
    p = ROOT / rel
    if not p.is_file():
        continue
    # Self-exclusion by path relative to root, not bare filename.
    if rel in SELF_EXCLUDE_RELS:
        continue
    # License files reference the forbidden strings as license text.
    if rel in {".gitignore", "LICENSE", "NOTICE"}:
        continue
    if p.suffix.lower() not in TEXT_EXT and p.name not in {"LICENSE", "NOTICE"}:
        continue
    text = p.read_text(encoding="utf-8", errors="ignore")
    for finding in deny_list_findings(rel, text):
        issues.append(finding)

required = [
    "README.md",
    "docs/README.zh-CN.md",
    "docs/BEGINNER_GUIDE.md",
    "docs/BEGINNER_GUIDE.zh-CN.md",
    "LICENSE",
    "NOTICE",
    "THIRD_PARTY_NOTICES.md",
    "pyproject.toml",
    "src/novel_workflow/core.py",
    "src/novel_workflow/cli.py",
    "src/novel_workflow/_security.py",
    "src/novel_workflow/model_adapter.py",
    "src/novel_workflow/model_cli.py",
    "skills/long-fiction-workflow/SKILL.md",
    "skills/author-role-os/SKILL.md",
    "skills/editor-deai-review/SKILL.md",
    "skills/reader-experience-review/SKILL.md",
    "skills/domain-consultant/SKILL.md",
    "templates/idea_interview.md",
    "templates/story_bible.md",
    "templates/outline_master.md",
    "templates/outline_volume.md",
    "templates/outline_chapter.md",
    "templates/chapter_contract.json",
    "templates/author_role_os_prewrite.md",
    "templates/deai_checklist.md",
    "templates/review_report.md",
    "templates/reader_review.md",
    "templates/domain_review.md",
    "templates/character_card.md",
    "templates/scene_card.md",
    "templates/reader_review.md",
    "templates/domain_review.md",
    "templates/character_card.md",
    "templates/scene_card.md",
    "templates/object_card.md",
    "templates/concept_card.md",
    "templates/model_routing.example.toml",
    "templates/env.example",
    "examples/demo_novel/README.md",
    "examples/demo_novel/run_full_demo.sh",
    "docs/ARCHITECTURE.md",
    "tests/test_workflow.py",
    "tests/test_illegal_transitions.py",
    "tests/test_cli_smoke.py",
    "tests/test_chapter_ledger.py",
    "tests/test_model_adapter.py",
]
for rel in required:
    if not (ROOT / rel).exists():
        issues.append(f"missing required file: {rel}")
    elif rel not in public_candidates:
        issues.append(f"required file is ignored and would not publish: {rel}")

for rel in sorted(INTERNAL_PATHS):
    if rel in tracked:
        issues.append(f"internal file is tracked: {rel}")
for rel in sorted(INTERNAL_DIRS):
    if any(item == rel or item.startswith(rel + "/") for item in tracked):
        issues.append(f"internal directory has tracked files: {rel}/")

_internal_probe_paths = [
    "WAL.md",
    "SECURITY_RELEASE_CHECKLIST.md",
    "output/example.txt",
    ".novel-workflow/example.json",
]
_not_ignored = []
for _probe in _internal_probe_paths:
    _r = _git("check-ignore", "-q", _probe)
    if _r.returncode != 0:
        _not_ignored.append(_probe)
if _not_ignored:
    issues.append(f"internal working patterns not fully ignored: {_not_ignored}")

env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
proc = subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"],
    cwd=ROOT,
    env=env,
    capture_output=True,
    text=True,
)
if proc.returncode:
    issues.append("tests failed")
    sys.stderr.write(proc.stdout + proc.stderr)

smoke_dir = ROOT / ".smoke-tmp"
if smoke_dir.exists():
    shutil.rmtree(smoke_dir)
smoke = subprocess.run(
    [sys.executable, "-m", "novel_workflow.cli", "init", str(smoke_dir), "--title", "Smoke"],
    cwd=ROOT,
    env=env,
    capture_output=True,
    text=True,
)
if smoke.returncode != 0:
    issues.append("CLI smoke init failed")
else:
    smoke2 = subprocess.run(
        [sys.executable, "-m", "novel_workflow.cli", "issue", str(smoke_dir), "1", "--title", "T", "--goal", "G"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if smoke2.returncode == 0 or "must be LOCKED" not in (smoke2.stdout + smoke2.stderr):
        issues.append("CLI smoke did not block chapter issuance before outline lock")
if smoke_dir.exists():
    shutil.rmtree(smoke_dir)

# Security-scan consistency: the CLI scanner and this release gate share the
# deny-list, so they must agree on the working tree. Compare only the files
# both surfaces scan: exclude the release gate's explicit license/gitignore
# skips and the scanner's own source files.
from novel_workflow.core import security_scan  # noqa: E402

cli_findings = security_scan(ROOT)
_consistency_skip = SELF_EXCLUDE_RELS | {".gitignore", "LICENSE", "NOTICE"}
cli_public = sorted(
    f for f in cli_findings
    if f.split(": ", 1)[-1] in public_candidates
    and f.split(": ", 1)[-1] not in _consistency_skip
)
if cli_public:
    issues.append("security_scan reports publishable findings: " + "; ".join(cli_public))

if issues:
    print("RELEASE_CHECK_FAIL")
    for issue in sorted(set(issues)):
        print("-", issue)
    raise SystemExit(1)
print("RELEASE_CHECK_PASS")
