"""Provider-neutral, user-configurable model routing for novel-agent-workflow.

Design contract
---------------
This module is an *optional* layer. The core workflow
(``novel_workflow.core`` / ``novel_workflow.cli``) never imports it and runs
without any model or network dependency. Users who want to bind AI providers
to the six roles opt in by writing a routing config and running the
``model`` subcommands.

Hard requirements enforced here (from the public release TASK.md):

1. The core workflow stays runnable with no model/network dependency. This
   module imports only the Python standard library.
2. Config stores *only* environment-variable names, never real keys. A config
   that contains a literal secret value is rejected at parse time.
3. Preflight smoke validates every configured candidate with a non-empty
   semantic response, recording timestamp / status / latency / failure. Roles
   are allocated only from *current* PASS candidates. A historical or static
   PASS cannot authorize a run.
4. Role routing is dynamic. ``author`` / ``editor`` / ``reader`` are fixed
   core roles. Consultant roles are selected by genre and outline risk;
   ``military`` and ``science`` must never be globally fixed defaults.
5. Runtime adapters are tool-neutral: an OpenAI-compatible HTTP adapter and a
   custom command adapter, both without provider branding in runtime code.
6. Keys remain env-only; errors are redacted; the release scanner detects
   accidental key values and absolute private paths in tracked fixtures.
7. Provider failure is isolated: a failing candidate does not poison the
   others; fallback selection picks the next current-PASS candidate.
8. The lightweight router supports C0-C3 task tiers, capability hard filters,
   exact user locks, provider health/quota/cost sorting, and a HUD trace for
   each decision. It stores only user-supplied public routing metadata.

Nothing in this module performs a real network call unless an adapter is
explicitly invoked by the user. ``preflight_smoke`` is the only entrypoint
that touches a provider, and it does so through the adapter the user
configured.
"""
from __future__ import annotations

import dataclasses
import json
import os
import re
import shlex
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

# --- Constants -------------------------------------------------------------

#: Fixed core roles that must always be present in any routing plan. The
#: novel workflow's chapter gates require author/editor/reader; consultants
#: are selected dynamically on top of these.
CORE_ROLES: tuple[str, ...] = ("author", "editor", "reader")

#: Consultant roles the workflow recognises. ``military`` and ``science`` are
#: *available* consultants, never global defaults: a plan only includes them
#: when the genre/outline risk asks for them.
CONSULTANT_ROLES: tuple[str, ...] = (
    "military",
    "science",
    "history",
    "law",
    "medicine",
    "linguistics",
)

#: Verdicts a smoke probe can return.
SMOKE_PASS = "PASS"
SMOKE_FAIL = "FAIL"
SMOKE_SKIP = "SKIP"

#: A response must be at least this many non-whitespace characters to count
#: as a non-empty semantic response. Stops a provider that returns "" or "ok"
#: from authorising a role.
MIN_SEMANTIC_LEN = 8

#: Default per-probe timeout in seconds. Overridable per candidate.
DEFAULT_TIMEOUT = 20.0

#: Lightweight task complexity tiers. C0 is deterministic/simple routing;
#: C3 is highest risk and asks for stronger capability coverage.
COMPLEXITY_TIERS: tuple[str, ...] = ("C0", "C1", "C2", "C3")

#: Provider/model health states the router understands. They are sortable but
#: preserved verbatim in traces so users can see why a route was or was not
#: selected.
HEALTH_UNAVAILABLE = "unavailable"
HEALTH_QUOTA_EXHAUSTED = "quota_exhausted"
HEALTH_RATE_LIMITED = "rate_limited"
HEALTH_HEALTHY = "healthy"
HEALTH_STATUSES: tuple[str, ...] = (
    HEALTH_UNAVAILABLE,
    HEALTH_QUOTA_EXHAUSTED,
    HEALTH_RATE_LIMITED,
    HEALTH_HEALTHY,
)
_HEALTH_RANK: dict[str, int] = {
    HEALTH_HEALTHY: 0,
    HEALTH_RATE_LIMITED: 1,
    HEALTH_QUOTA_EXHAUSTED: 2,
    HEALTH_UNAVAILABLE: 3,
}

#: Public capability labels. Unknown future labels are allowed in configs, but
#: these names cover the built-in hard filters and documentation.
KNOWN_CAPABILITIES: tuple[str, ...] = (
    "text",
    "vision",
    "code",
    "tools",
    "long_context",
    "json",
    "reasoning",
)

#: A conservative redaction pattern for error strings. Catches common secret
#: shapes (sk-..., bearer tokens, long hex) so adapter failures never echo a
#: key back to the user or into a tracked ledger.
_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{12,}"
    r"|bearer\s+[A-Za-z0-9_-]{8,}"
    r"|[A-Za-z0-9_-]{32,})"
)


def redact(text: str) -> str:
    """Redact secret-like substrings from an error or response string."""
    return _SECRET_RE.sub("[REDACTED]", text or "")


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Config schema ---------------------------------------------------------


@dataclass(frozen=True)
class Candidate:
    """A single provider/model candidate for a role.

    ``api_key_env`` is the *name* of the environment variable that holds the
    key, never the key itself. ``base_url`` is optional and only used by the
    OpenAI-compatible HTTP adapter. ``command`` is optional and only used by
    the custom command adapter. At least one of ``base_url`` or ``command``
    must be present.
    """

    provider: str
    model: str
    api_key_env: str
    base_url: str | None = None
    command: str | None = None
    timeout: float = DEFAULT_TIMEOUT
    input_cost_per_million: float | None = None
    output_cost_per_million: float | None = None
    # Keep legacy positional construction stable: new routing metadata follows
    # the pre-existing ``extra`` field.
    extra: dict[str, Any] = field(default_factory=dict)
    capabilities: frozenset[str] = field(default_factory=frozenset)
    max_context_tokens: int | None = None
    health: str = HEALTH_HEALTHY
    confidence: float = 0.5
    daily_quota_remaining: int | None = None

    def adapter_kind(self) -> str:
        if self.command:
            return "command"
        if self.base_url:
            return "http"
        return "none"

    def resolve_key(self, env: Mapping[str, str] | None = None) -> str:
        env = env if env is not None else os.environ
        return env.get(self.api_key_env, "")


@dataclass(frozen=True)
class RoleRouting:
    """The configured candidates for one role, in fallback order."""

    role: str
    candidates: tuple[Candidate, ...]

    def is_empty(self) -> bool:
        return not self.candidates


@dataclass(frozen=True)
class RoutingConfig:
    """A fully parsed routing configuration.

    ``core_roles`` always contains author/editor/reader. ``consultants`` is
    the *available* consultant set configured by the user; which of them are
    actually included in a plan is decided dynamically by
    :func:`select_consultants` based on genre and outline risk.
    """

    core_roles: dict[str, RoleRouting]
    consultants: dict[str, RoleRouting]
    smoke_prompt: str
    min_semantic_len: int = MIN_SEMANTIC_LEN
    default_timeout: float = DEFAULT_TIMEOUT

    def all_role_routings(self) -> dict[str, RoleRouting]:
        merged: dict[str, RoleRouting] = {}
        merged.update(self.core_roles)
        merged.update(self.consultants)
        return merged

    def roles_configured(self) -> tuple[str, ...]:
        return tuple(self.all_role_routings().keys())


# --- Config parsing --------------------------------------------------------

#: Regex that catches a literal secret *value* accidentally written into a
#: config: an ``api_key``/``token``/``secret`` field assigned a long string
#: instead of an ``_env`` name. The parser rejects this before anything runs.
_LITERAL_SECRET_RE = re.compile(
    r"(?:api[_-]?key|token|secret|authorization)"
    r"\s*[:=]\s*['\"]?[A-Za-z0-9_+/=-]{16,}",
    re.I,
)


class ConfigError(ValueError):
    """Raised when a routing config is malformed or unsafe."""


def _check_no_literal_secret(raw_text: str) -> None:
    """Reject a config that embeds a real secret value instead of an env name.

    A tracked config must only ever contain the *name* of the environment
    variable (e.g. ``api_key_env = "NOVEL_AUTHOR_KEY"``). A literal value is
    a release blocker.
    """
    if _LITERAL_SECRET_RE.search(raw_text):
        raise ConfigError(
            "config contains a literal secret value; use an *_env variable "
            "name instead (e.g. api_key_env = \"NOVEL_AUTHOR_KEY\")"
        )


def _check_no_absolute_private_path(value: str) -> None:
    """Reject absolute home/private paths in tracked config fixtures.

    A public config template may use a relative path or a placeholder, never
    a real ``/root/...`` or ``/home/...`` working path.
    """
    if re.search(r"/(?:root|home)/[A-Za-z0-9_./-]+", value) or re.search(
        r"[A-Za-z]:\\\\Users\\\\", value
    ):
        raise ConfigError(
            "config contains an absolute private path; use a relative path "
            "or placeholder in tracked fixtures"
        )


def parse_config(raw_text: str) -> RoutingConfig:
    """Parse a TOML-like routing config from text.

    The config is intentionally a small, stdlib-parseable subset so the
    public repo keeps zero runtime dependencies. It is a mapping of role
    names to candidate tables:

    .. code-block:: toml

        smoke_prompt = "Reply with one original sentence about a relay station."
        default_timeout = 20.0

        [author]
        candidates = [
          { provider = "acme", model = "author-m", api_key_env = "NOVEL_AUTHOR_KEY", base_url = "https://api.example.test/v1", timeout = 20.0 },
          { provider = "acme-fb", model = "author-m-fb", api_key_env = "NOVEL_AUTHOR_FB_KEY", base_url = "https://api.example.test/v1" },
        ]

        [military]
        candidates = [
          { provider = "acme", model = "mil-m", api_key_env = "NOVEL_MIL_KEY", command = "scripts/mil_adapter.sh" },
        ]

    Parsing is deliberately strict: unknown keys are rejected so a typo does
    not silently disable a candidate.
    """
    _check_no_literal_secret(raw_text)
    import tomllib  # Python 3.11+ stdlib

    try:
        data = tomllib.loads(raw_text)
    except Exception as exc:  # tomllib.TOMLDecodeError is a subclass of ValueError
        raise ConfigError(f"config is not valid TOML: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("config top level must be a mapping")

    smoke_prompt = str(data.get("smoke_prompt", _DEFAULT_SMOKE_PROMPT)).strip()
    if not smoke_prompt:
        raise ConfigError("smoke_prompt must be a non-empty string")

    try:
        default_timeout = float(data.get("default_timeout", DEFAULT_TIMEOUT))
    except (TypeError, ValueError) as exc:
        raise ConfigError("default_timeout must be a number") from exc
    if default_timeout <= 0:
        raise ConfigError("default_timeout must be positive")

    try:
        min_semantic_len = int(data.get("min_semantic_len", MIN_SEMANTIC_LEN))
    except (TypeError, ValueError) as exc:
        raise ConfigError("min_semantic_len must be an integer") from exc
    if min_semantic_len < 1:
        raise ConfigError("min_semantic_len must be positive")

    core_roles: dict[str, RoleRouting] = {}
    consultants: dict[str, RoleRouting] = {}

    for role in CORE_ROLES:
        if role not in data:
            raise ConfigError(f"core role '{role}' is not configured")
        core_roles[role] = _parse_role(role, data[role], default_timeout)

    for key in data:
        if key in {
            "smoke_prompt",
            "default_timeout",
            "min_semantic_len",
        } or key in CORE_ROLES:
            continue
        if key not in CONSULTANT_ROLES:
            raise ConfigError(
                f"unknown role '{key}'; known consultants: {CONSULTANT_ROLES}"
            )
        consultants[key] = _parse_role(key, data[key], default_timeout)

    return RoutingConfig(
        core_roles=core_roles,
        consultants=consultants,
        smoke_prompt=smoke_prompt,
        min_semantic_len=min_semantic_len,
        default_timeout=default_timeout,
    )


def _parse_role(role: str, table: Any, default_timeout: float) -> RoleRouting:
    if not isinstance(table, dict):
        raise ConfigError(f"role '{role}' must be a mapping")
    raw_candidates = table.get("candidates")
    if not isinstance(raw_candidates, list) or not raw_candidates:
        raise ConfigError(
            f"role '{role}' must have a non-empty 'candidates' list"
        )
    parsed: list[Candidate] = []
    seen: set[tuple[str, str]] = set()
    for idx, item in enumerate(raw_candidates):
        cand = _parse_candidate(role, idx, item, default_timeout)
        key = (cand.provider, cand.model)
        if key in seen:
            raise ConfigError(
                f"role '{role}' has duplicate candidate {key}"
            )
        seen.add(key)
        parsed.append(cand)
    return RoleRouting(role=role, candidates=tuple(parsed))


_CANDIDATE_KEYS = frozenset(
    {
        "provider",
        "model",
        "api_key_env",
        "base_url",
        "command",
        "timeout",
        "input_cost_per_million",
        "output_cost_per_million",
        "capabilities",
        "max_context_tokens",
        "health",
        "confidence",
        "daily_quota_remaining",
        "extra",
    }
)


def _parse_candidate(
    role: str, idx: int, item: Any, default_timeout: float
) -> Candidate:
    if not isinstance(item, dict):
        raise ConfigError(
            f"role '{role}' candidate #{idx} must be a mapping"
        )
    unknown = set(item) - _CANDIDATE_KEYS
    if unknown:
        raise ConfigError(
            f"role '{role}' candidate #{idx} has unknown keys: {sorted(unknown)}"
        )
    provider = str(item.get("provider", "")).strip()
    model = str(item.get("model", "")).strip()
    api_key_env = str(item.get("api_key_env", "")).strip()
    if not provider or not model:
        raise ConfigError(
            f"role '{role}' candidate #{idx} must have provider and model"
        )
    if not api_key_env:
        raise ConfigError(
            f"role '{role}' candidate #{idx} must name an api_key_env "
            "(the env variable name, never the key value)"
        )
    if not re.match(r"^[A-Z_][A-Z0-9_]*$", api_key_env):
        raise ConfigError(
            f"role '{role}' candidate #{idx} api_key_env '{api_key_env}' "
            "must be an UPPER_SNAKE env variable name"
        )
    base_url = item.get("base_url")
    command = item.get("command")
    if base_url is not None:
        base_url = str(base_url).strip()
        if base_url:
            _check_no_absolute_private_path(base_url)
        else:
            base_url = None
    if command is not None:
        command = str(command).strip()
        if command:
            _check_no_absolute_private_path(command)
        else:
            command = None
    if not base_url and not command:
        raise ConfigError(
            f"role '{role}' candidate #{idx} must have base_url or command"
        )
    if base_url and command:
        raise ConfigError(
            f"role '{role}' candidate #{idx} cannot have both base_url and command"
        )
    try:
        timeout = float(item.get("timeout", default_timeout))
    except (TypeError, ValueError) as exc:
        raise ConfigError(
            f"role '{role}' candidate #{idx} timeout must be a number"
        ) from exc
    if timeout <= 0:
        raise ConfigError(
            f"role '{role}' candidate #{idx} timeout must be positive"
        )

    def optional_nonnegative_cost(key: str) -> float | None:
        raw = item.get(key)
        if raw is None:
            return None
        try:
            value = float(raw)
        except (TypeError, ValueError) as exc:
            raise ConfigError(
                f"role '{role}' candidate #{idx} {key} must be a number"
            ) from exc
        if value < 0:
            raise ConfigError(
                f"role '{role}' candidate #{idx} {key} must be non-negative"
            )
        return value

    input_cost_per_million = optional_nonnegative_cost("input_cost_per_million")
    output_cost_per_million = optional_nonnegative_cost("output_cost_per_million")
    capabilities_raw = item.get("capabilities", [])
    if capabilities_raw is None:
        capabilities_raw = []
    if not isinstance(capabilities_raw, list) or not all(
        isinstance(value, str) and value.strip() for value in capabilities_raw
    ):
        raise ConfigError(
            f"role '{role}' candidate #{idx} capabilities must be a list of strings"
        )
    capabilities = frozenset(value.strip().lower() for value in capabilities_raw)
    max_context_raw = item.get("max_context_tokens")
    max_context_tokens = None
    if max_context_raw is not None:
        try:
            max_context_tokens = int(max_context_raw)
        except (TypeError, ValueError) as exc:
            raise ConfigError(
                f"role '{role}' candidate #{idx} max_context_tokens must be an integer"
            ) from exc
        if max_context_tokens < 1:
            raise ConfigError(
                f"role '{role}' candidate #{idx} max_context_tokens must be positive"
            )
    health = str(item.get("health", HEALTH_HEALTHY)).strip().lower()
    if health not in HEALTH_STATUSES:
        raise ConfigError(
            f"role '{role}' candidate #{idx} health must be one of {HEALTH_STATUSES}"
        )
    try:
        confidence = float(item.get("confidence", 0.5))
    except (TypeError, ValueError) as exc:
        raise ConfigError(
            f"role '{role}' candidate #{idx} confidence must be a number"
        ) from exc
    if not 0.0 <= confidence <= 1.0:
        raise ConfigError(
            f"role '{role}' candidate #{idx} confidence must be between 0 and 1"
        )
    quota_raw = item.get("daily_quota_remaining")
    daily_quota_remaining = None
    if quota_raw is not None:
        try:
            daily_quota_remaining = int(quota_raw)
        except (TypeError, ValueError) as exc:
            raise ConfigError(
                f"role '{role}' candidate #{idx} daily_quota_remaining must be an integer"
            ) from exc
        if daily_quota_remaining < 0:
            raise ConfigError(
                f"role '{role}' candidate #{idx} daily_quota_remaining must be non-negative"
            )
    extra_raw = item.get("extra", {})
    if extra_raw is None:
        extra_raw = {}
    if not isinstance(extra_raw, dict):
        raise ConfigError(
            f"role '{role}' candidate #{idx} extra must be a mapping"
        )
    extra = {str(k): v for k, v in extra_raw.items()}
    return Candidate(
        provider=provider,
        model=model,
        api_key_env=api_key_env,
        base_url=base_url,
        command=command,
        timeout=timeout,
        input_cost_per_million=input_cost_per_million,
        output_cost_per_million=output_cost_per_million,
        capabilities=capabilities,
        max_context_tokens=max_context_tokens,
        health=health,
        confidence=confidence,
        daily_quota_remaining=daily_quota_remaining,
        extra=extra,
    )


_DEFAULT_SMOKE_PROMPT = (
    "Reply with one original, self-contained sentence about a remote relay "
    "station. Do not explain yourself."
)


# --- Adapters --------------------------------------------------------------

#: Type alias for a callable that runs a smoke probe against a candidate and
#: returns the raw response text (or raises). Adapters are injected so tests
#: can substitute deterministic fakes without touching the network.
AdapterFn = Callable[[Candidate, str, float], str]


def http_adapter(candidate: Candidate, prompt: str, timeout: float) -> str:
    """OpenAI-compatible chat completions adapter.

    Uses only :mod:`urllib` so the module stays stdlib-only. The request body
    is a minimal chat completion; the response is parsed for ``choices[0]
    .message.content``. Failures raise :class:`AdapterError` with a redacted
    message.
    """
    if not candidate.base_url:
        raise AdapterError("http_adapter requires base_url")
    key = candidate.resolve_key()
    if not key:
        raise AdapterError(
            f"api key env '{candidate.api_key_env}' is not set or empty"
        )
    url = candidate.base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": candidate.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 64,
            "temperature": 0.2,
            **candidate.extra,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise AdapterError(
            f"http {exc.code} from {candidate.provider}: {redact(str(exc.reason))}"
        ) from exc
    except urllib.error.URLError as exc:
        raise AdapterError(
            f"network error for {candidate.provider}: {redact(str(exc.reason))}"
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise AdapterError(
            f"unexpected error for {candidate.provider}: {redact(str(exc))}"
        ) from exc
    latency = time.monotonic() - start
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdapterError(
            f"non-JSON response from {candidate.provider}: {redact(raw[:120])}"
        ) from exc
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AdapterError(
            f"no choices in response from {candidate.provider}"
        )
    content = choices[0].get("message", {}).get("content", "")
    if not isinstance(content, str):
        raise AdapterError(
            f"non-string content from {candidate.provider}"
        )
    return content


def command_adapter(candidate: Candidate, prompt: str, timeout: float) -> str:
    """Custom command adapter.

    Runs the user-configured command with the prompt on stdin and reads the
    response from stdout. The command receives the model name and api key env
    name as arguments so a wrapper script can route to any backend without
    provider branding leaking into runtime code.

    The api key value is passed via the environment (``$NOVEL_ADAPTER_KEY``),
    never on the command line, so it does not appear in process listings.
    """
    if not candidate.command:
        raise AdapterError("command_adapter requires a command")
    key = candidate.resolve_key()
    if not key:
        raise AdapterError(
            f"api key env '{candidate.api_key_env}' is not set or empty"
        )
    try:
        argv = shlex.split(candidate.command)
    except ValueError as exc:
        raise AdapterError(f"invalid command: {exc}") from exc
    argv = [*argv, candidate.model, candidate.api_key_env]
    env = {
        **os.environ,
        "NOVEL_ADAPTER_KEY": key,
        "NOVEL_ADAPTER_PROMPT": prompt,
    }
    try:
        proc = subprocess.run(  # noqa: S603 - argv is user-configured, validated above
            argv,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise AdapterError(
            f"command timeout for {candidate.provider}"
        ) from exc
    except FileNotFoundError as exc:
        raise AdapterError(
            f"command not found for {candidate.provider}: {exc}"
        ) from exc
    if proc.returncode != 0:
        raise AdapterError(
            f"command exit {proc.returncode} for {candidate.provider}: "
            f"{redact((proc.stderr or '').strip()[:200])}"
        )
    return proc.stdout


class AdapterError(RuntimeError):
    """Raised when an adapter fails to return a usable response."""


def select_adapter(candidate: Candidate) -> AdapterFn:
    """Pick the adapter for a candidate by its configured kind."""
    kind = candidate.adapter_kind()
    if kind == "http":
        return http_adapter
    if kind == "command":
        return command_adapter
    raise AdapterError(
        f"candidate {candidate.provider}/{candidate.model} has no usable adapter"
    )


# --- Preflight smoke -------------------------------------------------------


@dataclass(frozen=True)
class SmokeResult:
    """One candidate's smoke probe result.

    ``status`` is ``PASS`` / ``FAIL`` / ``SKIP``. ``SKIP`` means the adapter
    was not run (e.g. the api key env is unset and the user requested
    ``skip_missing_env``). ``failure`` is a redacted error string on FAIL.
    ``timestamp`` is ISO-UTC; ``latency_ms`` is wall time. ``fresh`` is True
    only when the probe was actually run in this call - a historical result
    loaded from a ledger is ``fresh=False`` and cannot authorize a run.
    """

    role: str
    provider: str
    model: str
    status: str
    timestamp: str
    latency_ms: float
    response_preview: str = ""
    failure: str = ""
    fresh: bool = True

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _semantic_ok(text: str, min_len: int) -> bool:
    stripped = re.sub(r"\s+", "", text or "")
    return len(stripped) >= min_len


def _candidate_key(cand: Candidate) -> str:
    return f"{cand.provider}/{cand.model}"


def _candidate_cost(cand: Candidate) -> float:
    """Return a sortable user-supplied total cost estimate.

    Unknown pricing sorts behind known free/cheap routes but ahead of routes
    whose health/quota makes them unusable. The value is only for ordering;
    budget reports still refuse to invent monetary estimates.
    """
    if cand.input_cost_per_million is None or cand.output_cost_per_million is None:
        return float("inf")
    return cand.input_cost_per_million + cand.output_cost_per_million


def _candidate_allowed_by_health(cand: Candidate) -> bool:
    if cand.health in {HEALTH_UNAVAILABLE, HEALTH_QUOTA_EXHAUSTED}:
        return False
    if cand.daily_quota_remaining == 0:
        return False
    return True


@dataclass(frozen=True)
class TaskSpec:
    """A lightweight routing request for one model-backed task."""

    task: str
    role: str
    tier: str = "C1"
    required_capabilities: frozenset[str] = field(default_factory=frozenset)
    min_context_tokens: int | None = None
    provider: str | None = None
    model: str | None = None
    allow_unhealthy_locked: bool = False
    attempt: int = 1

    def __post_init__(self) -> None:
        tier = self.tier.upper()
        if tier not in COMPLEXITY_TIERS:
            raise ValueError(f"tier must be one of {COMPLEXITY_TIERS}")
        object.__setattr__(self, "tier", tier)
        object.__setattr__(
            self,
            "required_capabilities",
            frozenset(value.lower() for value in self.required_capabilities),
        )


@dataclass(frozen=True)
class RoutingTrace:
    """Human/UI-facing HUD trace for a single routing decision."""

    task: str
    tier: str
    role: str
    provider: str | None
    model: str | None
    confidence: float
    attempt: int
    fallback: tuple[str, ...]
    next_step: str
    status: str
    locked: bool = False
    candidates_considered: tuple[str, ...] = ()
    rejected: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = dataclasses.asdict(self)
        data["fallback"] = list(self.fallback)
        data["candidates_considered"] = list(self.candidates_considered)
        data["rejected"] = list(self.rejected)
        return data


@dataclass(frozen=True)
class RouteDecision:
    """Selected candidate plus its trace."""

    candidate: Candidate | None
    trace: RoutingTrace

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": None
            if self.candidate is None
            else {
                "provider": self.candidate.provider,
                "model": self.candidate.model,
            },
            "trace": self.trace.to_dict(),
        }


def infer_complexity_tier(task: str, *, risk_count: int = 0) -> str:
    """Deterministically classify task complexity as C0-C3.

    The heuristic is intentionally small and transparent; callers may always
    pass an explicit tier in :class:`TaskSpec`.
    """
    text = (task or "").casefold()
    if any(word in text for word in ("architect", "architecture", "security", "release", "multi-model", "long context")) or risk_count >= 3:
        return "C3"
    if any(word in text for word in ("code", "implement", "review", "debug", "tool", "vision")) or risk_count == 2:
        return "C2"
    if any(word in text for word in ("summarize", "rewrite", "draft", "classify")) or risk_count == 1:
        return "C1"
    return "C0"


def _tier_required_capabilities(tier: str) -> frozenset[str]:
    if tier == "C0":
        return frozenset({"text"})
    if tier == "C1":
        return frozenset({"text"})
    if tier == "C2":
        return frozenset({"text", "reasoning"})
    return frozenset({"text", "reasoning", "long_context"})


def _candidate_supports(cand: Candidate, task: TaskSpec) -> tuple[bool, str]:
    required = set(_tier_required_capabilities(task.tier)) | set(task.required_capabilities)
    missing = sorted(required - set(cand.capabilities))
    if missing:
        return False, "missing capabilities: " + ",".join(missing)
    if task.min_context_tokens is not None:
        if cand.max_context_tokens is None or cand.max_context_tokens < task.min_context_tokens:
            return False, "context window too small"
    return True, ""


def _sorted_candidates(candidates: Iterable[Candidate]) -> list[Candidate]:
    return sorted(
        candidates,
        key=lambda cand: (
            _HEALTH_RANK.get(cand.health, 99),
            -(cand.daily_quota_remaining if cand.daily_quota_remaining is not None else 1),
            _candidate_cost(cand),
            -cand.confidence,
            cand.provider,
            cand.model,
        ),
    )


def route_task(
    config: RoutingConfig,
    task: TaskSpec,
    *,
    takeover_state: Mapping[str, int] | None = None,
    repair_threshold: int = 2,
) -> RouteDecision:
    """Choose a provider/model for a task and return a HUD trace.

    If ``task.provider`` and/or ``task.model`` are set, the exact lock is
    honored first and automatic health/cost sorting is bypassed. Capability
    filters still apply to locked routes; unhealthy locked routes are refused
    unless ``allow_unhealthy_locked`` is true.
    """
    takeover_state = takeover_state or {}
    routing = config.all_role_routings().get(task.role)
    if routing is None:
        trace = RoutingTrace(
            task=task.task,
            tier=task.tier,
            role=task.role,
            provider=None,
            model=None,
            confidence=0.0,
            attempt=task.attempt,
            fallback=(),
            next_step="configure role route",
            status="blocked_no_role_route",
        )
        return RouteDecision(candidate=None, trace=trace)

    candidates = list(routing.candidates)
    locked = bool(task.provider or task.model)
    if locked:
        candidates = [
            cand
            for cand in candidates
            if (task.provider is None or cand.provider == task.provider)
            and (task.model is None or cand.model == task.model)
        ]

    considered: list[str] = []
    rejected: list[str] = []
    eligible: list[Candidate] = []
    for cand in candidates:
        key = _candidate_key(cand)
        considered.append(key)
        ok, reason = _candidate_supports(cand, task)
        if not ok:
            rejected.append(f"{key}:{reason}")
            continue
        if not _candidate_allowed_by_health(cand) and not (locked and task.allow_unhealthy_locked):
            rejected.append(f"{key}:health={cand.health}")
            continue
        eligible.append(cand)

    if not eligible:
        status = "blocked_locked_route" if locked else "blocked_no_capable_route"
        trace = RoutingTrace(
            task=task.task,
            tier=task.tier,
            role=task.role,
            provider=None,
            model=None,
            confidence=0.0,
            attempt=task.attempt,
            fallback=(),
            next_step="repair route config" if locked else "configure capable fallback",
            status=status,
            locked=locked,
            candidates_considered=tuple(considered),
            rejected=tuple(rejected),
        )
        return RouteDecision(candidate=None, trace=trace)

    ordered = eligible if locked else _sorted_candidates(eligible)
    if locked and takeover_state.get(_candidate_key(ordered[0]), 0) >= repair_threshold:
        rejected.append(
            f"{_candidate_key(ordered[0])}:repeated_failures="
            f"{takeover_state[_candidate_key(ordered[0])]}"
        )
        trace = RoutingTrace(
            task=task.task,
            tier=task.tier,
            role=task.role,
            provider=None,
            model=None,
            confidence=0.0,
            attempt=task.attempt,
            fallback=(),
            next_step="repair route before retry",
            status="BLOCKED_REPAIR_REQUIRED",
            locked=True,
            candidates_considered=tuple(considered),
            rejected=tuple(rejected),
        )
        return RouteDecision(candidate=None, trace=trace)
    takeover = False
    if not locked:
        fresh: list[Candidate] = []
        repeated: list[Candidate] = []
        for cand in ordered:
            failures = takeover_state.get(_candidate_key(cand), 0)
            if failures >= repair_threshold:
                rejected.append(
                    f"{_candidate_key(cand)}:repeated_failures={failures}"
                )
                repeated.append(cand)
            else:
                fresh.append(cand)
        if fresh:
            takeover = bool(repeated)
            ordered = fresh
        elif repeated:
            ordered = repeated

    if not locked and takeover_state.get(_candidate_key(ordered[0]), 0) >= repair_threshold:
        trace = RoutingTrace(
            task=task.task,
            tier=task.tier,
            role=task.role,
            provider=None,
            model=None,
            confidence=0.0,
            attempt=task.attempt,
            fallback=(),
            next_step="repair route before retry",
            status="BLOCKED_REPAIR_REQUIRED",
            locked=False,
            candidates_considered=tuple(considered),
            rejected=tuple(rejected),
        )
        return RouteDecision(candidate=None, trace=trace)

    chosen = ordered[0]
    fallback = tuple(_candidate_key(cand) for cand in ordered[1:])
    if takeover:
        status = "takeover"
        next_step = "execute takeover route"
    else:
        status = "selected"
        next_step = "execute"
    trace = RoutingTrace(
        task=task.task,
        tier=task.tier,
        role=task.role,
        provider=chosen.provider,
        model=chosen.model,
        confidence=chosen.confidence,
        attempt=task.attempt,
        fallback=fallback,
        next_step=next_step,
        status=status,
        locked=locked,
        candidates_considered=tuple(considered),
        rejected=tuple(rejected),
    )
    return RouteDecision(candidate=chosen, trace=trace)


def render_routing_trace(decision: RouteDecision) -> str:
    """Render a routing decision as stable JSON for HUD/log output."""
    return json.dumps(decision.trace.to_dict(), ensure_ascii=False, sort_keys=True)


def preflight_smoke(
    config: RoutingConfig,
    *,
    roles: Iterable[str] | None = None,
    env: Mapping[str, str] | None = None,
    skip_missing_env: bool = True,
    adapter_override: Mapping[str, AdapterFn] | None = None,
    clock: Callable[[], str] | None = None,
) -> dict[str, list[SmokeResult]]:
    """Run a smoke probe against every candidate for the requested roles.

    Returns a mapping ``role -> [SmokeResult, ...]`` in configured fallback
    order. Only candidates with ``status == PASS`` and ``fresh == True`` may
    be used for role allocation; :func:`allocate_roles` enforces this.

    When ``skip_missing_env`` is True (default), a candidate whose
    ``api_key_env`` is unset is recorded as ``SKIP`` rather than ``FAIL``.
    This lets a user run the preflight on a machine that only has some keys
    configured without poisoning the others. A SKIP is never a PASS.
    """
    env = env if env is not None else os.environ
    clock = clock or utcnow
    adapter_override = adapter_override or {}
    target_roles = list(roles) if roles is not None else list(config.roles_configured())
    results: dict[str, list[SmokeResult]] = {}
    for role in target_roles:
        routing = config.all_role_routings().get(role)
        if routing is None:
            raise ConfigError(f"role '{role}' is not configured")
        per_role: list[SmokeResult] = []
        for cand in routing.candidates:
            per_role.append(
                _probe_one(
                    role, cand, config, env, skip_missing_env, adapter_override, clock
                )
            )
        results[role] = per_role
    return results


def _probe_one(
    role: str,
    cand: Candidate,
    config: RoutingConfig,
    env: Mapping[str, str],
    skip_missing_env: bool,
    adapter_override: Mapping[str, AdapterFn],
    clock: Callable[[], str],
) -> SmokeResult:
    ts = clock()
    key_present = bool(env.get(cand.api_key_env))
    if not key_present and skip_missing_env:
        return SmokeResult(
            role=role,
            provider=cand.provider,
            model=cand.model,
            status=SMOKE_SKIP,
            timestamp=ts,
            latency_ms=0.0,
            failure=f"env {cand.api_key_env} not set",
            fresh=True,
        )
    if not key_present:
        return SmokeResult(
            role=role,
            provider=cand.provider,
            model=cand.model,
            status=SMOKE_FAIL,
            timestamp=ts,
            latency_ms=0.0,
            failure=f"env {cand.api_key_env} not set",
            fresh=True,
        )
    adapter = adapter_override.get(role) or select_adapter(cand)
    start = time.monotonic()
    try:
        text = adapter(cand, config.smoke_prompt, cand.timeout)
    except AdapterError as exc:
        return SmokeResult(
            role=role,
            provider=cand.provider,
            model=cand.model,
            status=SMOKE_FAIL,
            timestamp=ts,
            latency_ms=round((time.monotonic() - start) * 1000.0, 2),
            failure=redact(str(exc)),
            fresh=True,
        )
    latency = round((time.monotonic() - start) * 1000.0, 2)
    if not _semantic_ok(text, config.min_semantic_len):
        return SmokeResult(
            role=role,
            provider=cand.provider,
            model=cand.model,
            status=SMOKE_FAIL,
            timestamp=ts,
            latency_ms=latency,
            response_preview=redact(text[:80]),
            failure="empty or non-semantic response",
            fresh=True,
        )
    return SmokeResult(
        role=role,
        provider=cand.provider,
        model=cand.model,
        status=SMOKE_PASS,
        timestamp=ts,
        latency_ms=latency,
        response_preview=redact(text[:80]),
        fresh=True,
    )


# --- Dynamic consultant selection ------------------------------------------


@dataclass(frozen=True)
class GenreRisk:
    """Genre and outline-risk signals used to pick consultants.

    ``genre`` is a free-form label (e.g. ``"military-sci-fi"``, ``"romance"``,
    ``"historical"``). ``risk_tags`` is a set of lowercase risk signals
    extracted from the outline, e.g. ``{"combat", "physics", "legal"}``. The
    selector maps these to consultant roles; a consultant is included only
    when a tag asks for it, so military/science are never global defaults.
    """

    genre: str
    risk_tags: frozenset[str]


#: Mapping from risk tag to consultant role. A consultant is included in a
#: plan when its tag appears in the outline risk set. This table is the only
#: place tag -> consultant coupling is defined, so adding a consultant is a
#: one-line change.
RISK_TAG_TO_CONSULTANT: dict[str, str] = {
    "combat": "military",
    "tactics": "military",
    "force": "military",
    "logistics": "military",
    "weapons": "military",
    "physics": "science",
    "biology": "science",
    "chemistry": "science",
    "numbers": "science",
    "technology": "science",
    "space": "science",
    "history": "history",
    "period": "history",
    "law": "law",
    "crime": "law",
    "medicine": "medicine",
    "disease": "medicine",
    "language": "linguistics",
    "linguistics": "linguistics",
}


def select_consultants(
    config: RoutingConfig, risk: GenreRisk
) -> tuple[str, ...]:
    """Return the consultant roles a plan should include for this genre/risk.

    A consultant is included when:
    - it is configured in the routing config, AND
    - its risk tag appears in the outline risk set, OR the genre literally
      names it (e.g. genre ``"military-sci-fi"`` asks for ``military``).

    Military and science are therefore never global defaults: they appear
    only when the work actually asks for them.
    """
    configured = set(config.consultants.keys())
    wanted: set[str] = set()
    genre_lower = (risk.genre or "").lower()
    for tag in risk.risk_tags:
        role = RISK_TAG_TO_CONSULTANT.get(tag.lower())
        if role:
            wanted.add(role)
    for role in CONSULTANT_ROLES:
        if role in genre_lower:
            wanted.add(role)
    # Only consultants the user actually configured can be selected.
    selected = configured & wanted
    # Stable order for deterministic plans.
    return tuple(r for r in CONSULTANT_ROLES if r in selected)


# --- Role allocation -------------------------------------------------------


@dataclass(frozen=True)
class RoleAllocation:
    role: str
    provider: str
    model: str
    selected_from: tuple[str, ...]
    skipped_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class RoutePlan:
    """A concrete role -> candidate plan built from fresh smoke results.

    ``plan_roles`` is the full ordered role list (core + selected
    consultants). ``allocations`` maps role -> allocation. ``unallocated``
    lists roles with no current-PASS candidate. A plan with any unallocated
    *core* role is not usable; unallocated consultants are acceptable (the
    chapter can still SKIP_WITH_REASON).
    """

    plan_roles: tuple[str, ...]
    allocations: dict[str, RoleAllocation]
    unallocated: tuple[str, ...]
    smoke: dict[str, list[SmokeResult]]
    consultants_selected: tuple[str, ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_roles": list(self.plan_roles),
            "allocations": {r: a.to_dict() for r, a in self.allocations.items()},
            "unallocated": list(self.unallocated),
            "consultants_selected": list(self.consultants_selected),
            "generated_at": self.generated_at,
            "smoke": {r: [s.to_dict() for s in v] for r, v in self.smoke.items()},
        }


def allocate_roles(
    config: RoutingConfig,
    smoke: dict[str, list[SmokeResult]],
    consultants: Sequence[str],
) -> RoutePlan:
    """Allocate each role to its first current-PASS candidate.

    Only ``fresh == True`` and ``status == PASS`` results authorise a role.
    A historical PASS (``fresh == False``) is rejected. If no candidate
    passes, the role is recorded as unallocated with the failure chain.
    """
    allocations: dict[str, RoleAllocation] = {}
    unallocated: list[str] = []
    plan_roles: list[str] = list(CORE_ROLES) + list(consultants)
    for role in plan_roles:
        results = smoke.get(role, [])
        pass_cands = [r for r in results if r.fresh and r.status == SMOKE_PASS]
        if not pass_cands:
            unallocated.append(role)
            tried = [f"{r.provider}/{r.model}:{r.status}" for r in results]
            allocations[role] = RoleAllocation(
                role=role,
                provider="",
                model="",
                selected_from=tuple(tried),
                skipped_reason="no current PASS candidate",
            )
            continue
        chosen = pass_cands[0]
        tried = [f"{r.provider}/{r.model}:{r.status}" for r in results]
        allocations[role] = RoleAllocation(
            role=role,
            provider=chosen.provider,
            model=chosen.model,
            selected_from=tuple(tried),
        )
    return RoutePlan(
        plan_roles=tuple(plan_roles),
        allocations=allocations,
        unallocated=tuple(unallocated),
        smoke=smoke,
        consultants_selected=tuple(consultants),
        generated_at=utcnow(),
    )


@dataclass(frozen=True)
class ContinuityRole:
    """Runtime continuity status for one role."""

    role: str
    ready_candidates: tuple[str, ...]
    fallback_count: int
    can_continue: bool
    status: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_continuity_report(plan: RoutePlan) -> dict[str, Any]:
    """Report whether every planned role can continue after one route loss.

    A current PASS candidate makes a role runnable. Two or more current PASS
    candidates make it resilient to one runtime route failure. The report does
    not invent a fallback when the user configured none: that role is marked
    ``READY_SINGLE_ROUTE`` and the overall report becomes ``AT_RISK``.
    """
    roles: list[ContinuityRole] = []
    for role in plan.plan_roles:
        ready = tuple(
            f"{result.provider}/{result.model}"
            for result in plan.smoke.get(role, [])
            if result.fresh and result.status == SMOKE_PASS
        )
        if not ready:
            status = "BLOCKED_NO_ROUTE"
        elif len(ready) == 1:
            status = "READY_SINGLE_ROUTE"
        else:
            status = "READY_WITH_FALLBACK"
        roles.append(
            ContinuityRole(
                role=role,
                ready_candidates=ready,
                fallback_count=max(0, len(ready) - 1),
                can_continue=bool(ready),
                status=status,
            )
        )
    blocked = [item.role for item in roles if not item.can_continue]
    single_route = [item.role for item in roles if item.status == "READY_SINGLE_ROUTE"]
    overall = "BLOCKED" if blocked else ("AT_RISK" if single_route else "READY")
    return {
        "overall": overall,
        "blocked_roles": blocked,
        "single_route_roles": single_route,
        "roles": [item.to_dict() for item in roles],
    }


@dataclass(frozen=True)
class BudgetEstimate:
    """Transparent upper-bound estimate for repeated role calls."""

    role_count: int
    revision_rounds: int
    calls_per_round: int
    estimated_calls: int
    input_tokens_per_call: int
    output_tokens_per_call: int
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_total_tokens: int
    estimated_cost_min: float | None
    estimated_cost_max: float | None
    pricing_complete: bool

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def estimate_budget(
    config: RoutingConfig,
    risk: GenreRisk,
    *,
    revision_rounds: int = 2,
    input_tokens_per_call: int = 12000,
    output_tokens_per_call: int = 2500,
) -> BudgetEstimate:
    """Estimate calls, tokens, and configured cost range before execution.

    ``revision_rounds`` means full passes, including the initial pass. For
    example, 3 core roles plus 2 selected consultants over 3 passes means 15
    calls. Actual usage may be lower when only affected gates are re-run, or
    higher if a user's external runner adds retries. Prices are optional and
    user-supplied; when any role lacks pricing, token totals remain available
    but cost is reported as unknown instead of fabricated.
    """
    if revision_rounds < 1:
        raise ValueError("revision_rounds must be at least 1")
    if input_tokens_per_call < 0 or output_tokens_per_call < 0:
        raise ValueError("token estimates must be non-negative")
    selected = select_consultants(config, risk)
    roles = list(CORE_ROLES) + list(selected)
    calls = len(roles) * revision_rounds
    input_total = calls * input_tokens_per_call
    output_total = calls * output_tokens_per_call
    per_role_costs: list[tuple[float, float]] = []
    pricing_complete = True
    all_routings = config.all_role_routings()
    for role in roles:
        costs = []
        for cand in all_routings[role].candidates:
            if cand.input_cost_per_million is None or cand.output_cost_per_million is None:
                continue
            costs.append(
                input_tokens_per_call / 1_000_000 * cand.input_cost_per_million
                + output_tokens_per_call / 1_000_000 * cand.output_cost_per_million
            )
        if not costs:
            pricing_complete = False
        else:
            per_role_costs.append((min(costs), max(costs)))
    cost_min = cost_max = None
    if pricing_complete:
        cost_min = round(sum(x[0] for x in per_role_costs) * revision_rounds, 6)
        cost_max = round(sum(x[1] for x in per_role_costs) * revision_rounds, 6)
    return BudgetEstimate(
        role_count=len(roles),
        revision_rounds=revision_rounds,
        calls_per_round=len(roles),
        estimated_calls=calls,
        input_tokens_per_call=input_tokens_per_call,
        output_tokens_per_call=output_tokens_per_call,
        estimated_input_tokens=input_total,
        estimated_output_tokens=output_total,
        estimated_total_tokens=input_total + output_total,
        estimated_cost_min=cost_min,
        estimated_cost_max=cost_max,
        pricing_complete=pricing_complete,
    )


def execute_with_fallback(
    role: str,
    prompt: str,
    routing: RoleRouting,
    smoke: Sequence[SmokeResult],
    *,
    adapter_override: Mapping[str, AdapterFn] | None = None,
    min_semantic_len: int = MIN_SEMANTIC_LEN,
) -> tuple[str, Candidate, tuple[str, ...]]:
    """Execute a role call and continue across current-PASS candidates.

    Runtime failures are isolated and redacted. The function tries candidates
    in configured order, preserves a failure trail for checkpointing, and
    raises an explicit ``AdapterError`` only after every current-PASS route has
    failed. External runners should persist completed-role artifacts before
    calling the next role, so a later resume starts from the first incomplete
    role instead of repeating successful calls.
    """
    if min_semantic_len < 1:
        raise ValueError("min_semantic_len must be positive")
    adapter_override = adapter_override or {}
    pass_keys = {
        (item.provider, item.model)
        for item in smoke
        if item.fresh and item.status == SMOKE_PASS
    }
    failures: list[str] = []
    for cand in routing.candidates:
        if (cand.provider, cand.model) not in pass_keys:
            continue
        adapter = adapter_override.get(role) or select_adapter(cand)
        try:
            text = adapter(cand, prompt, cand.timeout)
            if not _semantic_ok(text, min_semantic_len):
                raise AdapterError("empty or non-semantic runtime response")
            return text, cand, tuple(failures)
        except Exception as exc:
            failures.append(f"{cand.provider}/{cand.model}:{redact(str(exc))}")
    detail = "; ".join(failures) or "no current PASS candidate"
    raise AdapterError(f"role '{role}' exhausted fallback chain: {detail}")


def build_route_plan(
    config: RoutingConfig,
    risk: GenreRisk,
    *,
    env: Mapping[str, str] | None = None,
    skip_missing_env: bool = True,
    adapter_override: Mapping[str, AdapterFn] | None = None,
    clock: Callable[[], str] | None = None,
) -> RoutePlan:
    """One-shot helper: select consultants, smoke, allocate.

    This is the entrypoint a CLI or external runner calls to produce a
    concrete plan. It never reads a historical PASS: the smoke step is
    always run fresh.
    """
    consultants = select_consultants(config, risk)
    roles = list(CORE_ROLES) + list(consultants)
    smoke = preflight_smoke(
        config,
        roles=roles,
        env=env,
        skip_missing_env=skip_missing_env,
        adapter_override=adapter_override,
        clock=clock,
    )
    return allocate_roles(config, smoke, consultants)


# --- Model ledger ----------------------------------------------------------


def render_model_ledger(plan: RoutePlan) -> str:
    """Render a route plan as a JSON-lines model ledger.

    Each line is one role's allocation plus its smoke trail. The ledger is
    the durable artifact a run leaves behind: it proves which provider/model
    was selected, when, and on what fresh evidence. Historical ledgers are
    for audit only - a later run must smoke again.
    """
    lines: list[str] = []
    for role in plan.plan_roles:
        alloc = plan.allocations.get(role)
        if alloc is None:
            continue
        entry = {
            "generated_at": plan.generated_at,
            "role": role,
            "provider": alloc.provider or None,
            "model": alloc.model or None,
            "selected_from": list(alloc.selected_from),
            "skipped_reason": alloc.skipped_reason or None,
            "consultants_selected": list(plan.consultants_selected),
            "smoke": [s.to_dict() for s in plan.smoke.get(role, [])],
        }
        lines.append(json.dumps(entry, ensure_ascii=False))
    return "\n".join(lines) + ("\n" if lines else "")


# --- Typing compat shim ----------------------------------------------------
# ``Mapping`` is imported lazily so the module reads cleanly top-to-bottom
# while still being stdlib-only. Kept at the bottom to avoid cluttering the
# public surface above.
try:  # pragma: no cover - import guard for type-checkers
    from collections.abc import Mapping  # noqa: F401
except ImportError:  # pragma: no cover - py<3.3 fallback
    from typing import Mapping  # type: ignore[assignment]  # noqa: F401
