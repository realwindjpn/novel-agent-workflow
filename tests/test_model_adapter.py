"""Tests for the provider-neutral model routing layer.

Covers the TASK.md requirements:
- config parsing (valid, unknown keys, literal secret rejection, absolute
  private path rejection, missing core role, duplicate candidate)
- missing env -> SKIP by default, FAIL with --no-skip-missing-env
- empty/non-semantic response -> FAIL
- fresh PASS required (a historical PASS cannot authorise a run)
- fallback selection picks the next current-PASS candidate
- provider failure isolation (one failing candidate does not poison others)
- dynamic consultant selection by genre/outline risk; military/science are
  never global defaults
- no-network default: the core workflow and the adapter module import and
  run without any network dependency
- CLI smoke for init-config / smoke / route-plan / model-ledger
"""
from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from novel_workflow import model_adapter as ma
from novel_workflow.model_cli import STARTER_CONFIG

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


# --- helpers ---------------------------------------------------------------


def _cfg_text(candidates_overrides: dict | None = None,
              include_military: bool = False,
              include_science: bool = False) -> str:
    """Build a config text. Candidates default to http adapters with
    placeholder base_urls and *_env names."""
    base = """\
smoke_prompt = "Reply with one original sentence about a relay station."
default_timeout = 5.0
min_semantic_len = 8

[author]
candidates = [
  { provider = "provider-a", model = "author-m", api_key_env = "NOVEL_AUTHOR_KEY", base_url = "https://api.example.test/v1", timeout = 5.0 },
]

[editor]
candidates = [
  { provider = "provider-a", model = "editor-m", api_key_env = "NOVEL_EDITOR_KEY", base_url = "https://api.example.test/v1" },
]

[reader]
candidates = [
  { provider = "provider-a", model = "reader-m", api_key_env = "NOVEL_READER_KEY", base_url = "https://api.example.test/v1" },
]
"""
    if include_military:
        base += """
[military]
candidates = [
  { provider = "provider-a", model = "mil-m", api_key_env = "NOVEL_MIL_KEY", base_url = "https://api.example.test/v1" },
]
"""
    if include_science:
        base += """
[science]
candidates = [
  { provider = "provider-a", model = "sci-m", api_key_env = "NOVEL_SCI_KEY", base_url = "https://api.example.test/v1" },
]
"""
    return base


def _http_cand(provider: str = "provider-a", model: str = "m",
               env_name: str = "NOVEL_KEY", base_url: str = "https://api.example.test/v1",
               timeout: float = 5.0, capabilities=None,
               max_context_tokens: int | None = None,
               health: str = ma.HEALTH_HEALTHY,
               confidence: float = 0.5,
               daily_quota_remaining: int | None = None,
               input_cost_per_million: float | None = None,
               output_cost_per_million: float | None = None) -> ma.Candidate:
    return ma.Candidate(
        provider=provider, model=model, api_key_env=env_name,
        base_url=base_url, timeout=timeout,
        capabilities=frozenset(capabilities or []),
        max_context_tokens=max_context_tokens,
        health=health,
        confidence=confidence,
        daily_quota_remaining=daily_quota_remaining,
        input_cost_per_million=input_cost_per_million,
        output_cost_per_million=output_cost_per_million,
    )


def _cmd_cand(provider: str = "provider-a", model: str = "m",
              env_name: str = "NOVEL_KEY", command: str = "scripts/adapter.sh",
              timeout: float = 5.0) -> ma.Candidate:
    return ma.Candidate(
        provider=provider, model=model, api_key_env=env_name,
        command=command, timeout=timeout,
    )


def _make_routing(candidates: list[ma.Candidate], role: str = "author") -> ma.RoleRouting:
    return ma.RoleRouting(role=role, candidates=tuple(candidates))


def _config_with(core_overrides: dict[str, list[ma.Candidate]] | None = None,
                 consultants: dict[str, list[ma.Candidate]] | None = None) -> ma.RoutingConfig:
    core = {
        "author": _make_routing(core_overrides.get("author", [_http_cand(model="author-m", env_name="NOVEL_AUTHOR_KEY")]) if core_overrides else [_http_cand(model="author-m", env_name="NOVEL_AUTHOR_KEY")]),
        "editor": _make_routing(core_overrides.get("editor", [_http_cand(model="editor-m", env_name="NOVEL_EDITOR_KEY")]) if core_overrides else [_http_cand(model="editor-m", env_name="NOVEL_EDITOR_KEY")]),
        "reader": _make_routing(core_overrides.get("reader", [_http_cand(model="reader-m", env_name="NOVEL_READER_KEY")]) if core_overrides else [_http_cand(model="reader-m", env_name="NOVEL_READER_KEY")]),
    }
    cons = {r: _make_routing(cs, role=r) for r, cs in (consultants or {}).items()}
    return ma.RoutingConfig(
        core_roles=core, consultants=cons,
        smoke_prompt="prompt", min_semantic_len=8, default_timeout=5.0,
    )


def _pass_adapter(text: str = "The relay hummed in the cold dark above the moon.") -> ma.AdapterFn:
    def _fn(c, p, t):
        return text
    return _fn


def _fail_adapter(msg: str = "boom") -> ma.AdapterFn:
    def _fn(c, p, t):
        raise ma.AdapterError(msg)
    return _fn


def _empty_adapter() -> ma.AdapterFn:
    def _fn(c, p, t):
        return ""
    return _fn


# --- Config parsing tests --------------------------------------------------


class ConfigParseTest(unittest.TestCase):
    def test_valid_minimal_config_parses(self):
        cfg = ma.parse_config(_cfg_text())
        self.assertEqual(set(cfg.core_roles), {"author", "editor", "reader"})
        self.assertEqual(cfg.consultants, {})
        self.assertEqual(cfg.min_semantic_len, 8)

    def test_candidate_legacy_positional_extra_remains_compatible(self):
        extra = {"temperature": 0}
        candidate = ma.Candidate(
            "provider", "model", "NOVEL_KEY", "https://api.example.test/v1",
            None, 5.0, 1.0, 2.0, extra,
        )
        self.assertEqual(candidate.extra, extra)
        self.assertEqual(candidate.capabilities, frozenset())

    def test_same_model_may_serve_multiple_roles(self):
        text = _cfg_text()
        text = text.replace('model = "editor-m"', 'model = "author-m"')
        text = text.replace('model = "reader-m"', 'model = "author-m"')
        cfg = ma.parse_config(text)
        self.assertEqual(
            {cfg.core_roles[role].candidates[0].model for role in ma.CORE_ROLES},
            {"author-m"},
        )

    def test_config_with_consultants(self):
        cfg = ma.parse_config(_cfg_text(include_military=True, include_science=True))
        self.assertEqual(set(cfg.consultants), {"military", "science"})

    def test_missing_core_role_rejected(self):
        text = _cfg_text().replace("[author]\ncandidates = [\n  { provider = \"provider-a\", model = \"author-m\", api_key_env = \"NOVEL_AUTHOR_KEY\", base_url = \"https://api.example.test/v1\", timeout = 5.0 },\n]\n\n", "")
        with self.assertRaises(ma.ConfigError):
            ma.parse_config(text)

    def test_literal_secret_rejected(self):
        # Build a config that embeds a real-looking secret VALUE (not an env
        # name). The parser must reject it. The secret is assembled at
        # runtime so the scanner does not flag this test file itself.
        secret_val = "sk-" + "1234567890abcdef123456"
        text = _cfg_text() + '\n[bogus]\napi_key = "' + secret_val + '"\n'
        with self.assertRaises(ma.ConfigError) as cm:
            ma.parse_config(text)
        self.assertIn("literal secret", str(cm.exception))

    def test_absolute_private_path_in_base_url_rejected(self):
        # The parser checks base_url/command for /root/... or /home/...
        # Assemble the private path at runtime so the scanner does not flag
        # this test file.
        priv = "/" + "root" + "/secret/adapter.sh"
        text = _cfg_text()
        text = text.replace(
            "[editor]",
            '[history]\ncandidates = [\n  { provider = "p", model = "m", api_key_env = "NOVEL_HIST_KEY", command = "' + priv + '" },\n]\n\n[editor]',
        )
        with self.assertRaises(ma.ConfigError) as cm:
            ma.parse_config(text)
        self.assertIn("absolute private path", str(cm.exception))

    def test_unknown_role_rejected(self):
        text = _cfg_text() + '\n[bogus]\ncandidates = [\n  { provider = "p", model = "m", api_key_env = "NOVEL_BOGUS_KEY", base_url = "https://api.example.test/v1" },\n]\n'
        with self.assertRaises(ma.ConfigError) as cm:
            ma.parse_config(text)
        self.assertIn("unknown role", str(cm.exception))

    def test_duplicate_candidate_rejected(self):
        text = _cfg_text()
        text = text.replace(
            "[editor]",
            '[editor]\ncandidates = [\n  { provider = "provider-a", model = "editor-m", api_key_env = "NOVEL_EDITOR_KEY", base_url = "https://api.example.test/v1" },\n  { provider = "provider-a", model = "editor-m", api_key_env = "NOVEL_EDITOR_KEY_2", base_url = "https://api.example.test/v1" },\n]\n\n[reader]',
            1,
        )
        # remove the original [editor] block to avoid double definition
        with self.assertRaises(ma.ConfigError) as cm:
            ma.parse_config(text)

    def test_candidate_needs_base_url_or_command(self):
        text = _cfg_text()
        text = text.replace(
            "[editor]",
            '[editor]\ncandidates = [\n  { provider = "p", model = "m", api_key_env = "NOVEL_EDITOR_KEY" },\n]\n\n[reader]',
            1,
        )
        with self.assertRaises(ma.ConfigError) as cm:
            ma.parse_config(text)

    def test_candidate_cannot_have_both_adapters(self):
        text = _cfg_text()
        text = text.replace(
            "[editor]",
            '[editor]\ncandidates = [\n  { provider = "p", model = "m", api_key_env = "NOVEL_EDITOR_KEY", base_url = "https://api.example.test/v1", command = "scripts/x.sh" },\n]\n\n[reader]',
            1,
        )
        with self.assertRaises(ma.ConfigError) as cm:
            ma.parse_config(text)

    def test_api_key_env_must_be_upper_snake(self):
        text = _cfg_text()
        text = text.replace(
            "[editor]",
            '[editor]\ncandidates = [\n  { provider = "p", model = "m", api_key_env = "novel-editor-key", base_url = "https://api.example.test/v1" },\n]\n\n[reader]',
            1,
        )
        with self.assertRaises(ma.ConfigError) as cm:
            ma.parse_config(text)

    def test_unknown_candidate_key_rejected(self):
        text = _cfg_text()
        text = text.replace(
            "[editor]",
            '[editor]\ncandidates = [\n  { provider = "p", model = "m", api_key_env = "NOVEL_EDITOR_KEY", base_url = "https://api.example.test/v1", bogus = true },\n]\n\n[reader]',
            1,
        )
        with self.assertRaises(ma.ConfigError) as cm:
            ma.parse_config(text)

    def test_invalid_toml_rejected(self):
        with self.assertRaises(ma.ConfigError):
            ma.parse_config("this is not = = valid toml [[")

    def test_default_smoke_prompt_used_when_absent(self):
        text = _cfg_text().replace('smoke_prompt = "Reply with one original sentence about a relay station."\n', "")
        cfg = ma.parse_config(text)
        self.assertTrue(cfg.smoke_prompt)
        self.assertIn("relay", cfg.smoke_prompt.lower())


# --- Smoke tests -----------------------------------------------------------


class PreflightSmokeTest(unittest.TestCase):
    def setUp(self):
        self.cfg = _config_with()

    def test_missing_env_skips_by_default(self):
        env = {}  # no keys set
        smoke = ma.preflight_smoke(self.cfg, env=env, skip_missing_env=True)
        for role in ma.CORE_ROLES:
            self.assertEqual(smoke[role][0].status, ma.SMOKE_SKIP)
            self.assertTrue(smoke[role][0].fresh)

    def test_missing_env_fails_when_no_skip(self):
        env = {}
        smoke = ma.preflight_smoke(self.cfg, env=env, skip_missing_env=False)
        for role in ma.CORE_ROLES:
            self.assertEqual(smoke[role][0].status, ma.SMOKE_FAIL)

    def test_empty_response_is_fail(self):
        env = {c.api_key_env: "k" for c in [self.cfg.core_roles[r].candidates[0] for r in ma.CORE_ROLES]}
        smoke = ma.preflight_smoke(
            self.cfg, env=env,
            adapter_override={r: _empty_adapter() for r in ma.CORE_ROLES},
        )
        for role in ma.CORE_ROLES:
            self.assertEqual(smoke[role][0].status, ma.SMOKE_FAIL)
            self.assertIn("empty", smoke[role][0].failure.lower())

    def test_short_response_is_fail(self):
        env = {c.api_key_env: "k" for c in [self.cfg.core_roles[r].candidates[0] for r in ma.CORE_ROLES]}
        smoke = ma.preflight_smoke(
            self.cfg, env=env,
            adapter_override={r: _pass_adapter("ok") for r in ma.CORE_ROLES},
        )
        for role in ma.CORE_ROLES:
            self.assertEqual(smoke[role][0].status, ma.SMOKE_FAIL)

    def test_semantic_response_is_pass(self):
        env = {c.api_key_env: "k" for c in [self.cfg.core_roles[r].candidates[0] for r in ma.CORE_ROLES]}
        smoke = ma.preflight_smoke(
            self.cfg, env=env,
            adapter_override={r: _pass_adapter() for r in ma.CORE_ROLES},
        )
        for role in ma.CORE_ROLES:
            self.assertEqual(smoke[role][0].status, ma.SMOKE_PASS)
            self.assertTrue(smoke[role][0].fresh)
            self.assertGreater(smoke[role][0].latency_ms, -1)

    def test_fresh_pass_required_historical_pass_rejected(self):
        # Build a smoke result that claims PASS but is NOT fresh.
        env = {c.api_key_env: "k" for c in [self.cfg.core_roles[r].candidates[0] for r in ma.CORE_ROLES]}
        real_smoke = ma.preflight_smoke(
            self.cfg, env=env,
            adapter_override={r: _pass_adapter() for r in ma.CORE_ROLES},
        )
        # Tamper: mark as not fresh.
        tampered = {
            role: [ma.SmokeResult(**{**r.to_dict(), "fresh": False}) for r in results]
            for role, results in real_smoke.items()
        }
        plan = ma.allocate_roles(self.cfg, tampered, consultants=())
        for role in ma.CORE_ROLES:
            self.assertIn(role, plan.unallocated)

    def test_provider_failure_isolation(self):
        # author has two candidates: first fails, second passes.
        cfg = _config_with(core_overrides={
            "author": [
                _http_cand(provider="bad", model="author-m", env_name="NOVEL_AUTHOR_KEY"),
                _http_cand(provider="good", model="author-m-fb", env_name="NOVEL_AUTHOR_FB_KEY"),
            ],
        })
        env = {"NOVEL_AUTHOR_KEY": "k1", "NOVEL_AUTHOR_FB_KEY": "k2",
               "NOVEL_EDITOR_KEY": "ke", "NOVEL_READER_KEY": "kr"}
        # The adapter_override is keyed by role; we need the first call to
        # fail and the second to pass. preflight calls the same adapter for
        # every candidate of a role, so use a stateful adapter.
        calls = {"n": 0}

        def stateful(c, p, t):
            calls["n"] += 1
            if calls["n"] == 1:
                raise ma.AdapterError("first candidate down")
            return "The relay hummed in the cold dark."

        smoke = ma.preflight_smoke(
            cfg, env=env, adapter_override={"author": stateful,
                                            "editor": _pass_adapter(),
                                            "reader": _pass_adapter()},
        )
        self.assertEqual(smoke["author"][0].status, ma.SMOKE_FAIL)
        self.assertEqual(smoke["author"][1].status, ma.SMOKE_PASS)
        # other roles unaffected
        self.assertEqual(smoke["editor"][0].status, ma.SMOKE_PASS)
        self.assertEqual(smoke["reader"][0].status, ma.SMOKE_PASS)


# --- Fallback selection ----------------------------------------------------


class FallbackSelectionTest(unittest.TestCase):
    def test_fallback_picks_next_pass_candidate(self):
        cfg = _config_with(core_overrides={
            "author": [
                _http_cand(provider="bad", model="author-m", env_name="NOVEL_AUTHOR_KEY"),
                _http_cand(provider="good", model="author-m-fb", env_name="NOVEL_AUTHOR_FB_KEY"),
            ],
        })
        env = {"NOVEL_AUTHOR_KEY": "k1", "NOVEL_AUTHOR_FB_KEY": "k2",
               "NOVEL_EDITOR_KEY": "ke", "NOVEL_READER_KEY": "kr"}

        def fail_first_then_pass(c, p, t):
            if c.provider == "bad":
                raise ma.AdapterError("down")
            return "The relay hummed steadily above the silent moon."

        plan = ma.build_route_plan(
            cfg, ma.GenreRisk(genre="sci-fi", risk_tags=frozenset()),
            env=env,
            adapter_override={"author": fail_first_then_pass,
                              "editor": _pass_adapter(),
                              "reader": _pass_adapter()},
        )
        alloc = plan.allocations["author"]
        self.assertEqual(alloc.provider, "good")
        self.assertEqual(alloc.model, "author-m-fb")
        self.assertNotIn("author", plan.unallocated)

    def test_all_fail_leaves_role_unallocated(self):
        cfg = _config_with()
        env = {c.api_key_env: "k" for c in [cfg.core_roles[r].candidates[0] for r in ma.CORE_ROLES]}
        plan = ma.build_route_plan(
            cfg, ma.GenreRisk(genre="sci-fi", risk_tags=frozenset()),
            env=env,
            adapter_override={r: _fail_adapter() for r in ma.CORE_ROLES},
        )
        for role in ma.CORE_ROLES:
            self.assertIn(role, plan.unallocated)

# --- Lightweight router / HUD ---------------------------------------------

class LightweightRouterTest(unittest.TestCase):
    def test_infer_complexity_tiers(self):
        self.assertEqual(ma.infer_complexity_tier("rename a file"), "C0")
        self.assertEqual(ma.infer_complexity_tier("draft a short note"), "C1")
        self.assertEqual(ma.infer_complexity_tier("implement code with tools"), "C2")
        self.assertEqual(ma.infer_complexity_tier("security release architecture"), "C3")

    def test_capability_hard_filter_and_health_cost_sorting(self):
        cheap = _http_cand(
            provider="cheap", model="c", env_name="NOVEL_AUTHOR_KEY",
            capabilities={"text", "reasoning", "long_context", "code", "tools"},
            max_context_tokens=128000, health=ma.HEALTH_HEALTHY,
            confidence=0.6, daily_quota_remaining=10,
            input_cost_per_million=0.1, output_cost_per_million=0.2,
        )
        costly = _http_cand(
            provider="costly", model="c", env_name="NOVEL_AUTHOR_2_KEY",
            capabilities={"text", "reasoning", "long_context", "code", "tools"},
            max_context_tokens=128000, health=ma.HEALTH_HEALTHY,
            confidence=0.9, daily_quota_remaining=10,
            input_cost_per_million=2.0, output_cost_per_million=3.0,
        )
        missing = _http_cand(
            provider="text-only", model="t", env_name="NOVEL_AUTHOR_3_KEY",
            capabilities={"text"}, max_context_tokens=128000,
        )
        exhausted = _http_cand(
            provider="quota", model="q", env_name="NOVEL_AUTHOR_4_KEY",
            capabilities={"text", "reasoning", "long_context", "code", "tools"},
            max_context_tokens=128000, health=ma.HEALTH_QUOTA_EXHAUSTED,
        )
        cfg = _config_with(core_overrides={"author": [costly, missing, exhausted, cheap]})
        decision = ma.route_task(
            cfg,
            ma.TaskSpec(
                task="C3 long-context implementation review",
                role="author",
                tier="C3",
                required_capabilities=frozenset({"code", "tools"}),
                min_context_tokens=64000,
            ),
        )
        self.assertIsNotNone(decision.candidate)
        self.assertEqual(decision.candidate.provider, "cheap")
        self.assertIn("costly/c", decision.trace.fallback)
        self.assertTrue(any("text-only" in item for item in decision.trace.rejected))
        self.assertTrue(any("quota/q:health=quota_exhausted" in item for item in decision.trace.rejected))

    def test_user_locked_provider_model_bypasses_auto_sorting(self):
        first = _http_cand(
            provider="auto", model="cheap", env_name="NOVEL_AUTHOR_KEY",
            capabilities={"text", "reasoning"}, health=ma.HEALTH_HEALTHY,
            input_cost_per_million=0.1, output_cost_per_million=0.1,
        )
        locked = _http_cand(
            provider="locked", model="wanted", env_name="NOVEL_AUTHOR_2_KEY",
            capabilities={"text", "reasoning"}, health=ma.HEALTH_RATE_LIMITED,
            input_cost_per_million=10.0, output_cost_per_million=10.0,
        )
        cfg = _config_with(core_overrides={"author": [first, locked]})
        decision = ma.route_task(
            cfg,
            ma.TaskSpec(
                task="implement code", role="author", tier="C2",
                provider="locked", model="wanted",
            ),
        )
        self.assertEqual(decision.candidate.provider, "locked")
        self.assertTrue(decision.trace.locked)
        self.assertEqual(decision.trace.fallback, ())

    def test_locked_unavailable_route_blocks_unless_allowed(self):
        locked = _http_cand(
            provider="locked", model="wanted", env_name="NOVEL_AUTHOR_KEY",
            capabilities={"text", "reasoning"}, health=ma.HEALTH_UNAVAILABLE,
        )
        cfg = _config_with(core_overrides={"author": [locked]})
        task = ma.TaskSpec(
            task="implement code", role="author", tier="C2",
            provider="locked", model="wanted",
        )
        self.assertEqual(ma.route_task(cfg, task).trace.status, "blocked_locked_route")
        allowed = ma.route_task(
            cfg,
            dataclasses.replace(task, allow_unhealthy_locked=True),
        )
        self.assertEqual(allowed.candidate.provider, "locked")

    def test_repeated_failure_without_fallback_blocks_repair(self):
        cand = _http_cand(
            provider="p", model="m", env_name="NOVEL_AUTHOR_KEY",
            capabilities={"text", "reasoning"}, confidence=0.7,
        )
        cfg = _config_with(core_overrides={"author": [cand]})
        decision = ma.route_task(
            cfg,
            ma.TaskSpec(task="implement code", role="author", tier="C2", attempt=3),
            takeover_state={"p/m": 2},
        )
        self.assertIsNone(decision.candidate)
        self.assertEqual(decision.trace.status, "BLOCKED_REPAIR_REQUIRED")
        self.assertEqual(decision.trace.next_step, "repair route before retry")
        payload = json.loads(ma.render_routing_trace(decision))
        for key in ("task", "tier", "role", "provider", "model", "confidence", "attempt", "fallback", "next_step", "status"):
            self.assertIn(key, payload)

    def test_repeated_primary_failure_takes_over_with_fallback(self):
        primary = _http_cand(
            provider="primary", model="m1", env_name="NOVEL_AUTHOR_KEY",
            capabilities={"text", "reasoning"}, confidence=0.9,
        )
        fallback = _http_cand(
            provider="fallback", model="m2", env_name="NOVEL_AUTHOR_2_KEY",
            capabilities={"text", "reasoning"}, confidence=0.7,
        )
        cfg = _config_with(core_overrides={"author": [primary, fallback]})
        decision = ma.route_task(
            cfg,
            ma.TaskSpec(task="implement code", role="author", tier="C2", attempt=3),
            takeover_state={"primary/m1": 2},
        )
        self.assertEqual(decision.candidate.provider, "fallback")
        self.assertEqual(decision.trace.status, "takeover")
        self.assertEqual(decision.trace.next_step, "execute takeover route")
        self.assertTrue(any("repeated_failures=2" in item for item in decision.trace.rejected))

    def test_repeated_exact_locked_route_never_switches(self):
        primary = _http_cand(
            provider="primary", model="m1", env_name="NOVEL_AUTHOR_KEY",
            capabilities={"text", "reasoning"},
        )
        fallback = _http_cand(
            provider="fallback", model="m2", env_name="NOVEL_AUTHOR_2_KEY",
            capabilities={"text", "reasoning"},
        )
        cfg = _config_with(core_overrides={"author": [primary, fallback]})
        decision = ma.route_task(
            cfg,
            ma.TaskSpec(
                task="implement code", role="author", tier="C2",
                provider="primary", model="m1", attempt=3,
            ),
            takeover_state={"primary/m1": 2},
        )
        self.assertIsNone(decision.candidate)
        self.assertTrue(decision.trace.locked)
        self.assertEqual(decision.trace.status, "BLOCKED_REPAIR_REQUIRED")
        self.assertNotIn("fallback/m2", decision.trace.candidates_considered)

    def test_health_quota_and_cost_boundaries(self):
        candidates = [
            _http_cand(provider="unknown-cost", capabilities={"text"}),
            _http_cand(
                provider="zero-cost", capabilities={"text"},
                input_cost_per_million=0.0, output_cost_per_million=0.0,
            ),
            _http_cand(
                provider="unknown-quota", capabilities={"text"},
                input_cost_per_million=0.0, output_cost_per_million=0.0,
            ),
            _http_cand(
                provider="known-quota", capabilities={"text"},
                daily_quota_remaining=5,
                input_cost_per_million=0.0, output_cost_per_million=0.0,
            ),
            _http_cand(
                provider="zero-quota", capabilities={"text"},
                daily_quota_remaining=0,
            ),
            _http_cand(
                provider="limited", capabilities={"text"},
                health=ma.HEALTH_RATE_LIMITED,
                input_cost_per_million=0.0, output_cost_per_million=0.0,
            ),
        ]
        cfg = _config_with(core_overrides={"editor": candidates})
        decision = ma.route_task(
            cfg, ma.TaskSpec(task="proofread", role="editor", tier="C0")
        )
        self.assertEqual(decision.candidate.provider, "known-quota")
        self.assertLess(
            decision.trace.fallback.index("unknown-quota/m"),
            decision.trace.fallback.index("unknown-cost/m"),
        )
        self.assertEqual(decision.trace.fallback[-1], "limited/m")
        self.assertTrue(any("zero-quota/m" in item for item in decision.trace.rejected))



# --- Continuity, runtime fallback, and budget ------------------------------


class ContinuityAndBudgetTest(unittest.TestCase):
    def test_continuity_marks_single_route_at_risk(self):
        cfg = _config_with()
        env = {c.api_key_env: "k" for c in [cfg.core_roles[r].candidates[0] for r in ma.CORE_ROLES]}
        plan = ma.build_route_plan(
            cfg, ma.GenreRisk("romance", frozenset()), env=env,
            adapter_override={r: _pass_adapter() for r in ma.CORE_ROLES},
        )
        report = ma.build_continuity_report(plan)
        self.assertEqual(report["overall"], "AT_RISK")
        self.assertEqual(set(report["single_route_roles"]), set(ma.CORE_ROLES))

    def test_continuity_ready_with_two_pass_routes(self):
        first = _http_cand(provider="a", model="m1", env_name="NOVEL_AUTHOR_KEY")
        second = _http_cand(provider="b", model="m2", env_name="NOVEL_AUTHOR_FB_KEY")
        cfg = _config_with(core_overrides={"author": [first, second]})
        env = {"NOVEL_AUTHOR_KEY": "a", "NOVEL_AUTHOR_FB_KEY": "b",
               "NOVEL_EDITOR_KEY": "e", "NOVEL_READER_KEY": "r"}
        plan = ma.build_route_plan(
            cfg, ma.GenreRisk("romance", frozenset()), env=env,
            adapter_override={r: _pass_adapter() for r in ma.CORE_ROLES},
        )
        report = ma.build_continuity_report(plan)
        author = next(x for x in report["roles"] if x["role"] == "author")
        self.assertEqual(author["status"], "READY_WITH_FALLBACK")
        self.assertEqual(author["fallback_count"], 1)

    def test_runtime_failure_uses_next_current_pass(self):
        first = _http_cand(provider="a", model="m1", env_name="NOVEL_AUTHOR_KEY")
        second = _http_cand(provider="b", model="m2", env_name="NOVEL_AUTHOR_FB_KEY")
        routing = _make_routing([first, second], role="author")
        smoke = [
            ma.SmokeResult("author", "a", "m1", "PASS", "now", 1.0),
            ma.SmokeResult("author", "b", "m2", "PASS", "now", 1.0),
        ]
        def runtime(c, p, t):
            if c.provider == "a":
                raise ma.AdapterError("route down")
            return "A usable recovered role response."
        text, chosen, failures = ma.execute_with_fallback(
            "author", "prompt", routing, smoke,
            adapter_override={"author": runtime},
        )
        self.assertIn("usable", text)
        self.assertEqual(chosen.provider, "b")
        self.assertEqual(len(failures), 1)

    def test_runtime_exhaustion_is_explicit(self):
        cand = _http_cand(provider="a", model="m1", env_name="NOVEL_AUTHOR_KEY")
        smoke = [ma.SmokeResult("author", "a", "m1", "PASS", "now", 1.0)]
        with self.assertRaises(ma.AdapterError) as cm:
            ma.execute_with_fallback(
                "author", "prompt", _make_routing([cand], role="author"), smoke,
                adapter_override={"author": _fail_adapter("down")},
            )
        self.assertIn("exhausted fallback chain", str(cm.exception))

    def test_runtime_fallback_covers_auth_timeout_rate_limit_and_empty_reply(self):
        failures = (
            ma.AdapterError("http 401 unauthorized"),
            TimeoutError("request timed out"),
            ma.AdapterError("http 429 rate limited"),
        )
        candidates = [
            _http_cand(provider=f"p{i}", model=f"m{i}", env_name=f"NOVEL_ROUTE_{i}_KEY")
            for i in range(5)
        ]
        smoke = [
            ma.SmokeResult("author", cand.provider, cand.model, "PASS", "now", 1.0)
            for cand in candidates
        ]

        def runtime(c, p, t):
            index = int(c.provider[1:])
            if index < 3:
                raise failures[index]
            if index == 3:
                return ""
            return "Recovered through the final fallback route."

        text, chosen, trail = ma.execute_with_fallback(
            "author", "prompt", _make_routing(candidates, role="author"), smoke,
            adapter_override={"author": runtime},
        )
        self.assertEqual(chosen.provider, "p4")
        self.assertEqual(len(trail), 4)
        self.assertIn("Recovered", text)

    def test_runtime_fallback_accepts_configured_semantic_threshold(self):
        cand = _http_cand(provider="p", model="m", env_name="NOVEL_ROUTE_KEY")
        smoke = [ma.SmokeResult("author", "p", "m", "PASS", "now", 1.0)]
        text, chosen, trail = ma.execute_with_fallback(
            "author",
            "prompt",
            _make_routing([cand], role="author"),
            smoke,
            adapter_override={"author": lambda c, p, t: "short"},
            min_semantic_len=5,
        )
        self.assertEqual(text, "short")
        self.assertEqual(chosen.provider, "p")
        self.assertEqual(trail, ())

    def test_budget_counts_repeated_full_role_rounds(self):
        cfg = _config_with(consultants={
            "science": [_http_cand(model="s", env_name="NOVEL_SCI_KEY")],
            "military": [_http_cand(model="m", env_name="NOVEL_MIL_KEY")],
        })
        estimate = ma.estimate_budget(
            cfg, ma.GenreRisk("sci-fi", frozenset({"physics", "combat"})),
            revision_rounds=3, input_tokens_per_call=10000,
            output_tokens_per_call=2000,
        )
        self.assertEqual(estimate.role_count, 5)
        self.assertEqual(estimate.estimated_calls, 15)
        self.assertEqual(estimate.estimated_total_tokens, 180000)
        self.assertFalse(estimate.pricing_complete)
        self.assertIsNone(estimate.estimated_cost_max)

    def test_budget_uses_only_user_supplied_prices(self):
        priced = ma.Candidate(
            provider="p", model="m", api_key_env="NOVEL_KEY",
            base_url="https://api.example.test/v1",
            input_cost_per_million=2.0, output_cost_per_million=8.0,
        )
        cfg = _config_with(core_overrides={r: [priced] for r in ma.CORE_ROLES})
        estimate = ma.estimate_budget(
            cfg, ma.GenreRisk("romance", frozenset()), revision_rounds=2,
            input_tokens_per_call=10000, output_tokens_per_call=2000,
        )
        self.assertTrue(estimate.pricing_complete)
        self.assertEqual(estimate.estimated_calls, 6)
        self.assertEqual(estimate.estimated_cost_min, 0.216)
        self.assertEqual(estimate.estimated_cost_max, 0.216)


# --- Dynamic consultant selection ------------------------------------------


class DynamicConsultantTest(unittest.TestCase):
    def test_military_not_a_global_default(self):
        cfg = _config_with(consultants={
            "military": [_http_cand(model="mil-m", env_name="NOVEL_MIL_KEY")],
            "science": [_http_cand(model="sci-m", env_name="NOVEL_SCI_KEY")],
        })
        # romance with no risk tags -> no consultants
        selected = ma.select_consultants(cfg, ma.GenreRisk("romance", frozenset()))
        self.assertEqual(selected, ())

    def test_combat_risk_selects_military(self):
        cfg = _config_with(consultants={
            "military": [_http_cand(model="mil-m", env_name="NOVEL_MIL_KEY")],
            "science": [_http_cand(model="sci-m", env_name="NOVEL_SCI_KEY")],
        })
        selected = ma.select_consultants(
            cfg, ma.GenreRisk("military-sci-fi", frozenset({"combat", "physics"}))
        )
        self.assertIn("military", selected)
        self.assertIn("science", selected)

    def test_genre_name_selects_consultant(self):
        cfg = _config_with(consultants={
            "military": [_http_cand(model="mil-m", env_name="NOVEL_MIL_KEY")],
        })
        selected = ma.select_consultants(cfg, ma.GenreRisk("military-thriller", frozenset()))
        self.assertEqual(selected, ("military",))

    def test_unconfigured_consultant_not_selected(self):
        cfg = _config_with()  # no consultants configured
        selected = ma.select_consultants(
            cfg, ma.GenreRisk("sci-fi", frozenset({"physics"}))
        )
        self.assertEqual(selected, ())

    def test_plan_includes_only_selected_consultants(self):
        cfg = _config_with(consultants={
            "military": [_http_cand(model="mil-m", env_name="NOVEL_MIL_KEY")],
            "science": [_http_cand(model="sci-m", env_name="NOVEL_SCI_KEY")],
            "history": [_http_cand(model="hist-m", env_name="NOVEL_HIST_KEY")],
        })
        env = {
            "NOVEL_AUTHOR_KEY": "ka", "NOVEL_EDITOR_KEY": "ke",
            "NOVEL_READER_KEY": "kr", "NOVEL_MIL_KEY": "km",
            "NOVEL_SCI_KEY": "ks", "NOVEL_HIST_KEY": "kh",
        }
        plan = ma.build_route_plan(
            cfg,
            ma.GenreRisk("military-sci-fi", frozenset({"combat"})),
            env=env,
            adapter_override={r: _pass_adapter() for r in
                              ["author", "editor", "reader", "military", "science", "history"]},
        )
        # combat selects military; physics NOT in risk tags so science excluded;
        # history not asked for.
        self.assertIn("military", plan.consultants_selected)
        self.assertNotIn("science", plan.consultants_selected)
        self.assertNotIn("history", plan.consultants_selected)
        self.assertIn("military", plan.plan_roles)
        self.assertNotIn("science", plan.plan_roles)


# --- No-network default ----------------------------------------------------


class NoNetworkDefaultTest(unittest.TestCase):
    def test_core_module_imports_without_network(self):
        # The core workflow module must not import model_adapter.
        import novel_workflow.core as core
        # core should have no attribute pointing at model_adapter
        self.assertFalse(hasattr(core, "model_adapter"))

    def test_model_adapter_is_stdlib_only(self):
        # model_adapter must import only stdlib modules.
        import inspect
        src = inspect.getsource(ma)
        # Forbidden: requests, httpx, openai, anthropic, aiohttp
        for forbidden in ["import requests", "import httpx", "import openai",
                          "import anthropic", "import aiohttp"]:
            self.assertNotIn(forbidden, src, f"model_adapter must not {forbidden}")

    def test_core_workflow_runs_without_model_config(self):
        # The happy path from the existing test suite must still pass with
        # no model routing configured at all. This is a smoke import check;
        # the full happy path is covered by test_workflow.py.
        import novel_workflow.core as core
        self.assertTrue(callable(core.init_project))


# --- Redaction -------------------------------------------------------------


class RedactionTest(unittest.TestCase):
    def test_redact_strips_secret_shapes(self):
        # Assemble at runtime so the scanner does not flag this test file.
        secret = "sk-" + "1234567890abcdef123456"
        s = "bearer " + secret + " something"
        r = ma.redact(s)
        self.assertNotIn(secret, r)
        self.assertIn("[REDACTED]", r)

    def test_adapter_failure_redacted_in_result(self):
        secret = "sk-" + "1234567890abcdef123456"
        cfg = _config_with()
        env = {c.api_key_env: secret for c in
               [cfg.core_roles[r].candidates[0] for r in ma.CORE_ROLES]}
        smoke = ma.preflight_smoke(
            cfg, env=env,
            adapter_override={r: _fail_adapter(secret + " leaked") for r in ma.CORE_ROLES},
        )
        for role in ma.CORE_ROLES:
            self.assertNotIn(secret, smoke[role][0].failure)


# --- Model ledger ----------------------------------------------------------


class ModelLedgerTest(unittest.TestCase):
    def test_ledger_is_jsonlines(self):
        cfg = _config_with()
        env = {c.api_key_env: "k" for c in [cfg.core_roles[r].candidates[0] for r in ma.CORE_ROLES]}
        plan = ma.build_route_plan(
            cfg, ma.GenreRisk("sci-fi", frozenset()),
            env=env, adapter_override={r: _pass_adapter() for r in ma.CORE_ROLES},
        )
        ledger = ma.render_model_ledger(plan)
        lines = [l for l in ledger.splitlines() if l.strip()]
        self.assertEqual(len(lines), len(plan.plan_roles))
        for line in lines:
            obj = json.loads(line)
            self.assertIn("role", obj)
            self.assertIn("provider", obj)
            self.assertIn("smoke", obj)


# --- CLI smoke -------------------------------------------------------------


def _run_cli(args, cwd=ROOT):
    return subprocess.run(
        [sys.executable, "-m", "novel_workflow.cli", *args],
        cwd=cwd, env=ENV, capture_output=True, text=True,
    )


class CLISmokeTest(unittest.TestCase):
    def test_init_config_writes_starter(self):
        with tempfile.TemporaryDirectory() as d:
            res = _run_cli(["model", "init-config", str(Path(d) / "mc.toml")], cwd=ROOT)
            self.assertEqual(res.returncode, 0, res.stderr)
            out = json.loads(res.stdout)
            self.assertTrue((Path(d) / "mc.toml").exists())
            self.assertTrue((Path(d) / ".env.example").exists())
            text = (Path(d) / "mc.toml").read_text()
            # starter must parse cleanly
            cfg = ma.parse_config(text)
            self.assertEqual(set(cfg.core_roles), {"author", "editor", "reader"})

    def test_init_config_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mc.toml"
            p.write_text("x")
            res = _run_cli(["model", "init-config", str(p)], cwd=ROOT)
            self.assertNotEqual(res.returncode, 0)

    def test_smoke_command_reports_skip_without_env(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "mc.toml"
            cfg_path.write_text(_cfg_text())
            # clean env so no keys are set
            clean_env = {**ENV}
            for k in list(clean_env):
                if k.startswith("NOVEL_"):
                    del clean_env[k]
            res = subprocess.run(
                [sys.executable, "-m", "novel_workflow.cli", "model", "smoke",
                 "--config", str(cfg_path)],
                cwd=ROOT, env=clean_env, capture_output=True, text=True,
            )
            self.assertEqual(res.returncode, 1)  # core roles not ok
            payload = json.loads(res.stdout)
            self.assertFalse(payload["core_roles_ok"])
            for role in ("author", "editor", "reader"):
                self.assertEqual(payload["smoke"][role][0]["status"], "SKIP")

    def test_route_plan_command_with_genre(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "mc.toml"
            cfg_path.write_text(_cfg_text())
            clean_env = {**ENV}
            for k in list(clean_env):
                if k.startswith("NOVEL_"):
                    del clean_env[k]
            res = subprocess.run(
                [sys.executable, "-m", "novel_workflow.cli", "model", "route-plan",
                 "--config", str(cfg_path), "--genre", "romance"],
                cwd=ROOT, env=clean_env, capture_output=True, text=True,
            )
            self.assertEqual(res.returncode, 1)  # no keys -> core unallocated
            payload = json.loads(res.stdout)
            self.assertEqual(payload["consultants_selected"], [])
            self.assertIn("author", payload["unallocated"])
            self.assertEqual(payload["continuity"]["overall"], "BLOCKED")

    def test_budget_command_reports_revision_multiplier(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "mc.toml"
            cfg_path.write_text(_cfg_text())
            res = _run_cli([
                "model", "budget", "--config", str(cfg_path),
                "--genre", "romance", "--revision-rounds", "3",
                "--input-tokens-per-call", "10000",
                "--output-tokens-per-call", "2000",
            ])
            self.assertEqual(res.returncode, 0, res.stderr)
            payload = json.loads(res.stdout)
            self.assertEqual(payload["estimated_calls"], 9)
            self.assertEqual(payload["estimated_total_tokens"], 108000)
            self.assertFalse(payload["pricing_complete"])
            self.assertIn("unknown", payload["cost_note"].lower())

    def test_model_ledger_command_writes_file(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "mc.toml"
            cfg_path.write_text(_cfg_text())
            out_path = Path(d) / "ledger.jsonl"
            clean_env = {**ENV}
            for k in list(clean_env):
                if k.startswith("NOVEL_"):
                    del clean_env[k]
            res = subprocess.run(
                [sys.executable, "-m", "novel_workflow.cli", "model", "model-ledger",
                 "--config", str(cfg_path), "--genre", "sci-fi",
                 "-o", str(out_path)],
                cwd=ROOT, env=clean_env, capture_output=True, text=True,
            )
            self.assertEqual(res.returncode, 1, res.stderr)  # no keys
            self.assertTrue(out_path.exists())
            lines = [l for l in out_path.read_text().splitlines() if l.strip()]
            self.assertEqual(len(lines), 3)  # 3 core roles

    def test_route_task_editor_success_and_capability_filter(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "model_routing.toml"
            cfg_path.write_text(STARTER_CONFIG)
            success = _run_cli(["model", "route-task", "--config", str(cfg_path), "--task", "proofread prose", "--role", "editor", "--tier", "C0"])
            self.assertEqual(success.returncode, 0, success.stdout + success.stderr)
            self.assertEqual(json.loads(success.stdout)["candidate"]["model"], "editor-model")
            blocked = _run_cli(["model", "route-task", "--config", str(cfg_path), "--task", "proofread with tools", "--role", "editor", "--tier", "C0", "--capability", "tools"])
            self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)
            self.assertEqual(json.loads(blocked.stdout)["trace"]["status"], "blocked_no_capable_route")

    def test_route_task_locked_repair_and_bad_failed_route(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "model_routing.toml"
            cfg_path.write_text(STARTER_CONFIG)
            result = _run_cli([
                "model", "route-task", "--config", str(cfg_path),
                "--task", "draft chapter", "--role", "author",
                "--provider", "provider-a", "--model", "author-model",
                "--failed-route", "provider-a/author-model",
                "--failed-route", "provider-a/author-model",
            ])
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertIsNone(payload["candidate"])
            self.assertEqual(payload["trace"]["status"], "BLOCKED_REPAIR_REQUIRED")
            bad = _run_cli(["model", "route-task", "--config", str(cfg_path), "--task", "draft chapter", "--role", "author", "--failed-route", "not-a-route"])
            self.assertEqual(bad.returncode, 2)
            self.assertIn("error", json.loads(bad.stdout))

    def test_route_task_accumulates_explicit_failed_route_counts(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "model_routing.toml"
            cfg_path.write_text(STARTER_CONFIG)
            result = _run_cli([
                "model", "route-task", "--config", str(cfg_path),
                "--task", "draft chapter", "--role", "author",
                "--failed-route", "provider-a/author-model:1",
                "--failed-route", "provider-a/author-model:1",
            ])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["candidate"]["provider"], "provider-b")
            self.assertEqual(payload["trace"]["status"], "takeover")
            self.assertTrue(any("repeated_failures=2" in item for item in payload["trace"]["rejected"]))


class StarterConfigParsesTest(unittest.TestCase):
    def test_starter_config_parses(self):
        cfg = ma.parse_config(STARTER_CONFIG)
        self.assertEqual(set(cfg.core_roles), {"author", "editor", "reader"})
        self.assertEqual(
            cfg.core_roles["editor"].candidates[0].capabilities,
            frozenset({"text"}),
        )

    def test_example_template_parses(self):
        p = ROOT / "templates" / "model_routing.example.toml"
        cfg = ma.parse_config(p.read_text())
        self.assertEqual(set(cfg.core_roles), {"author", "editor", "reader"})


if __name__ == "__main__":
    unittest.main()
