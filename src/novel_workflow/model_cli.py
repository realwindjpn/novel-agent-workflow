"""CLI subcommands for the provider-neutral model routing layer.

These subcommands are opt-in. The core ``novel-workflow`` CLI exposes them
under ``novel-workflow model ...`` but the core workflow itself never
imports :mod:`novel_workflow.model_adapter`, so the repo stays runnable with
no model or network dependency.

Subcommands:

- ``model init-config [path]``: write a starter ``model_routing.toml`` and a
  ``.env.example`` next to it. The starter uses placeholders only - no real
  keys, no absolute private paths.
- ``model smoke [--config PATH] [--role ROLE ...] [--no-skip-missing-env]``:
  run a preflight smoke against every configured candidate and print the
  fresh results as JSON. Exits non-zero if any *core* role has no current
  PASS candidate.
- ``model route-plan [--config PATH] --genre GENRE [--risk TAG ...]``:
  select consultants dynamically, smoke, allocate roles, and print the
  route plan as JSON.
- ``model model-ledger [--config PATH] --genre GENRE [--risk TAG ...]
  [-o PATH]``: build a route plan and render it as a JSON-lines ledger.
- ``model route-task [--config PATH] --task TEXT --role ROLE``: run the
  lightweight C0-C3 router and print one HUD trace without calling a provider.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

from . import model_adapter as ma


def _emit(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


#: The starter config written by ``model init-config``. Every value is a
#: placeholder: no real keys, no absolute private paths, no provider branding
#: that would couple the public repo to a specific vendor. Users edit this
#: file to point at their own OpenAI-compatible endpoint or command adapter.
STARTER_CONFIG = """\
# Provider-neutral model routing for novel-agent-workflow.
#
# This file stores ONLY the NAMES of environment variables that hold API
# keys, never the key values themselves. A literal secret value here is a
# release blocker and will be rejected at parse time.
#
# Edit the providers, models, base_urls, and api_key_env names to match your
# own setup. Remove consultants you do not need; add others from the known
# set: military, science, history, law, medicine, linguistics.
# The repository does not prescribe a model roster. You may reuse one model
# across several roles or configure different models per role. When recording
# evidence, use distinct execution/provenance identifiers for independent
# author/editor/reader passes even if their underlying model is the same.
# For unattended runs, configure at least two candidates per required role.
# route-plan reports a single current-PASS candidate as READY_SINGLE_ROUTE.
# Optional input/output prices are user-supplied estimates per million tokens;
# omit them when unknown and the budget command will not invent a cost.
# Capabilities are promises used as hard filters. Declare "tools" only when
# the configured adapter can actually execute tools for that candidate.

smoke_prompt = "Reply with one original, self-contained sentence about a remote relay station."
default_timeout = 20.0
min_semantic_len = 8

[author]
candidates = [
  { provider = "provider-a", model = "author-model", api_key_env = "NOVEL_AUTHOR_KEY", base_url = "https://api.example.test/v1", timeout = 20.0, capabilities = ["text", "reasoning", "long_context", "tools"], max_context_tokens = 128000, health = "healthy", confidence = 0.8, daily_quota_remaining = 20 },
  { provider = "provider-b", model = "author-model-fb", api_key_env = "NOVEL_AUTHOR_FB_KEY", base_url = "https://api.example.test/v1", capabilities = ["text", "reasoning"], max_context_tokens = 64000, health = "rate_limited", confidence = 0.6, daily_quota_remaining = 5 },
]

[editor]
candidates = [
  { provider = "provider-a", model = "editor-model", api_key_env = "NOVEL_EDITOR_KEY", base_url = "https://api.example.test/v1", capabilities = ["text"] },
]

[reader]
candidates = [
  { provider = "provider-a", model = "reader-model", api_key_env = "NOVEL_READER_KEY", base_url = "https://api.example.test/v1", capabilities = ["text"] },
]

# Consultants are OPTIONAL. They are included in a plan only when the
# genre/outline risk asks for them (see `model route-plan --risk`). Military
# and science are never global defaults. Uncomment and edit to enable.

# [military]
# candidates = [
#   { provider = "provider-a", model = "mil-model", api_key_env = "NOVEL_MIL_KEY", command = "scripts/mil_adapter.sh" },
# ]

# [science]
# candidates = [
#   { provider = "provider-a", model = "sci-model", api_key_env = "NOVEL_SCI_KEY", base_url = "https://api.example.test/v1" },
# ]
"""

#: The starter .env.example written alongside the config. Lists only the env
#: var NAMES the starter config references; the user fills in real values
#: locally and the file is gitignored.
STARTER_ENV_EXAMPLE = """\
# Copy to .env and fill in real values. .env is gitignored; never commit keys.
NOVEL_AUTHOR_KEY=
NOVEL_AUTHOR_FB_KEY=
NOVEL_EDITOR_KEY=
NOVEL_READER_KEY=
# NOVEL_MIL_KEY=
# NOVEL_SCI_KEY=
"""


def _default_config_path(ns: argparse.Namespace) -> Path:
    if getattr(ns, "config", None):
        return Path(ns.config)
    return Path("model_routing.toml")


def _load_config(path: Path) -> ma.RoutingConfig:
    if not path.exists():
        raise FileNotFoundError(f"routing config not found: {path}")
    return ma.parse_config(path.read_text(encoding="utf-8"))


# --- subcommand handlers ---------------------------------------------------


def cmd_init_config(ns: argparse.Namespace) -> int:
    dest = Path(ns.path) if ns.path else Path("model_routing.toml")
    if dest.exists() and not ns.force:
        _emit({"error": f"refusing to overwrite existing {dest}; use --force"})
        return 2
    dest.write_text(STARTER_CONFIG, encoding="utf-8")
    env_example = dest.parent / ".env.example"
    env_example.write_text(STARTER_ENV_EXAMPLE, encoding="utf-8")
    _emit(
        {
            "written": [str(dest), str(env_example)],
            "note": "edit the file to point at your own providers; keys stay in .env",
        }
    )
    return 0


def cmd_smoke(ns: argparse.Namespace) -> int:
    config = _load_config(_default_config_path(ns))
    roles = list(ns.role) if ns.role else list(config.roles_configured())
    smoke = ma.preflight_smoke(
        config,
        roles=roles,
        skip_missing_env=not ns.no_skip_missing_env,
    )
    out: dict[str, Any] = {}
    core_ok = True
    for role, results in smoke.items():
        out[role] = [r.to_dict() for r in results]
        if role in ma.CORE_ROLES and not any(
            r.status == ma.SMOKE_PASS and r.fresh for r in results
        ):
            core_ok = False
    _emit({"smoke": out, "core_roles_ok": core_ok})
    return 0 if core_ok else 1


def cmd_route_plan(ns: argparse.Namespace) -> int:
    config = _load_config(_default_config_path(ns))
    risk = ma.GenreRisk(
        genre=ns.genre,
        risk_tags=frozenset(t.lower() for t in (ns.risk or [])),
    )
    plan = ma.build_route_plan(
        config,
        risk,
        skip_missing_env=not ns.no_skip_missing_env,
    )
    payload = plan.to_dict()
    payload["continuity"] = ma.build_continuity_report(plan)
    _emit(payload)
    core_unallocated = [r for r in ma.CORE_ROLES if r in plan.unallocated]
    return 0 if not core_unallocated else 1


def cmd_budget(ns: argparse.Namespace) -> int:
    config = _load_config(_default_config_path(ns))
    risk = ma.GenreRisk(
        genre=ns.genre,
        risk_tags=frozenset(t.lower() for t in (ns.risk or [])),
    )
    estimate = ma.estimate_budget(
        config,
        risk,
        revision_rounds=ns.revision_rounds,
        input_tokens_per_call=ns.input_tokens_per_call,
        output_tokens_per_call=ns.output_tokens_per_call,
    )
    payload = estimate.to_dict()
    payload["warning"] = (
        "Estimate assumes every selected role runs once per round. Actual usage "
        "may be lower for targeted re-review or higher when external retries occur."
    )
    if not estimate.pricing_complete:
        payload["cost_note"] = (
            "Cost is unknown because one or more selected roles lack user-supplied "
            "input/output prices; token totals remain valid estimates."
        )
    _emit(payload)
    return 0


def cmd_model_ledger(ns: argparse.Namespace) -> int:
    config = _load_config(_default_config_path(ns))
    risk = ma.GenreRisk(
        genre=ns.genre,
        risk_tags=frozenset(t.lower() for t in (ns.risk or [])),
    )
    plan = ma.build_route_plan(
        config,
        risk,
        skip_missing_env=not ns.no_skip_missing_env,
    )
    ledger = ma.render_model_ledger(plan)
    if ns.output:
        out_path = Path(ns.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(ledger, encoding="utf-8")
        _emit({"written": str(out_path), "lines": ledger.count("\n")})
    else:
        sys.stdout.write(ledger)
    core_unallocated = [r for r in ma.CORE_ROLES if r in plan.unallocated]
    return 0 if not core_unallocated else 1


def cmd_route_task(ns: argparse.Namespace) -> int:
    config = _load_config(_default_config_path(ns))
    tier = ns.tier or ma.infer_complexity_tier(ns.task, risk_count=len(ns.risk or []))
    task = ma.TaskSpec(
        task=ns.task,
        role=ns.role,
        tier=tier,
        required_capabilities=frozenset(ns.capability or []),
        min_context_tokens=ns.min_context_tokens,
        provider=ns.provider,
        model=ns.model,
        allow_unhealthy_locked=ns.allow_unhealthy_locked,
        attempt=ns.attempt,
    )
    takeover_state = {}
    for item in ns.failed_route or []:
        name, _, count = item.partition(":")
        if "/" not in name or not name.split("/", 1)[0] or not name.split("/", 1)[1]:
            raise ValueError("--failed-route must be provider/model[:count]")
        try:
            failures = int(count or "1")
        except ValueError as exc:
            raise ValueError("--failed-route count must be an integer") from exc
        if failures < 1:
            raise ValueError("--failed-route count must be positive")
        takeover_state[name] = takeover_state.get(name, 0) + failures
    decision = ma.route_task(config, task, takeover_state=takeover_state)
    _emit(decision.to_dict())
    return 0 if decision.candidate is not None else 1


# --- subparser registration ------------------------------------------------


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register ``model`` subcommands on an existing subparsers action."""
    p = subparsers.add_parser(
        "model",
        help="provider-neutral model routing (opt-in; core stays no-network)",
    )
    model_sub = p.add_subparsers(dest="model_command", required=True)

    init = model_sub.add_parser(
        "init-config",
        help="write a starter model_routing.toml and .env.example",
    )
    init.add_argument("path", nargs="?", default=None)
    init.add_argument("--force", action="store_true")
    init.set_defaults(_model_handler=cmd_init_config)

    smoke = model_sub.add_parser(
        "smoke",
        help="preflight smoke every configured candidate",
    )
    smoke.add_argument("--config", default=None)
    smoke.add_argument("--role", action="append", default=None)
    smoke.add_argument(
        "--no-skip-missing-env",
        action="store_true",
        help="FAIL instead of SKIP candidates whose api_key_env is unset",
    )
    smoke.set_defaults(_model_handler=cmd_smoke)

    rp = model_sub.add_parser(
        "route-plan",
        help="select consultants by genre/risk, smoke, and allocate roles",
    )
    rp.add_argument("--config", default=None)
    rp.add_argument("--genre", required=True)
    rp.add_argument("--risk", action="append", default=None)
    rp.add_argument("--no-skip-missing-env", action="store_true")
    rp.set_defaults(_model_handler=cmd_route_plan)

    budget = model_sub.add_parser(
        "budget",
        help="estimate role calls, tokens, and optional user-supplied cost range",
    )
    budget.add_argument("--config", default=None)
    budget.add_argument("--genre", required=True)
    budget.add_argument("--risk", action="append", default=None)
    budget.add_argument("--revision-rounds", type=int, default=2)
    budget.add_argument("--input-tokens-per-call", type=int, default=12000)
    budget.add_argument("--output-tokens-per-call", type=int, default=2500)
    budget.set_defaults(_model_handler=cmd_budget)

    ml = model_sub.add_parser(
        "model-ledger",
        help="build a route plan and render a JSON-lines model ledger",
    )
    ml.add_argument("--config", default=None)
    ml.add_argument("--genre", required=True)
    ml.add_argument("--risk", action="append", default=None)
    ml.add_argument("--no-skip-missing-env", action="store_true")
    ml.add_argument("-o", "--output", default=None)
    ml.set_defaults(_model_handler=cmd_model_ledger)

    rt = model_sub.add_parser(
        "route-task",
        help="run C0-C3 capability/health/cost router and print HUD trace",
    )
    rt.add_argument("--config", default=None)
    rt.add_argument("--task", required=True)
    rt.add_argument("--role", required=True)
    rt.add_argument("--tier", choices=ma.COMPLEXITY_TIERS, default=None)
    rt.add_argument("--risk", action="append", default=None)
    rt.add_argument("--capability", action="append", default=None)
    rt.add_argument("--min-context-tokens", type=int, default=None)
    rt.add_argument("--provider", default=None)
    rt.add_argument("--model", default=None)
    rt.add_argument("--allow-unhealthy-locked", action="store_true")
    rt.add_argument("--attempt", type=int, default=1)
    rt.add_argument(
        "--failed-route",
        action="append",
        default=None,
        help="provider/model[:count] repeated failure state for repair HUD",
    )
    rt.set_defaults(_model_handler=cmd_route_task)


def run(ns: argparse.Namespace) -> int:
    """Dispatch a parsed ``model`` namespace to its handler."""
    handler = getattr(ns, "_model_handler", None)
    if handler is None:
        print(json.dumps({"error": "no model subcommand given"}))
        return 2
    try:
        return handler(ns)
    except (ma.ConfigError, FileNotFoundError, ValueError) as exc:
        _emit({"error": str(exc)})
        return 2
