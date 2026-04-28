"""Agent observability registry — single source of truth for cross-agent ops.

Passive registry: agents call :func:`register_agent_observability` from
their own bootstrap module. The shared layer never imports
``src.modules.*`` (enforced by ``test_shared_agent_observability_purity``)
— the dependency points the other way: agents push their spec in.

Consumed by:

* :mod:`shared.agent_observability.reporting.cost_aggregator` — picks
  which model class an aggregator instance reads from.
* :mod:`shared.agent_observability.application.cost_alert_service` —
  iterates every agent and produces a per-agent cost breakdown.
* :mod:`shared.agent_observability.workers.retention_task` — knows
  which tables to purge and which env vars override their retention.
* :mod:`shared.agent_observability.workers.aggregate_refresh_task` —
  refreshes the v2 cross-agent MV which UNION-ALLs the same tables
  listed here.

Adding a new agent (e.g. ``email_agent``):

1. Declare its SQLAlchemy ``*_llm_call`` model.
2. Create the migration with mirror schema (NOT NULL ``tenant_id``,
   ``started_at``, ``occurred_on``, ``cost_usd``).
3. Append a ``register_agent_observability(...)`` call inside the new
   agent's ``observability/__init__.py``.
4. Add the agent's import to
   ``src.shared.infrastructure.agent_observability_bootstrap`` so every
   entrypoint loads the spec.
5. Re-run the v2 MV migration (idempotent).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.shared.domain.base_entity import Base

# ── Default retention windows ──────────────────────────────────────────


_DEFAULT_TRACE_RETENTION_DAYS: int = 90
_DEFAULT_LLM_CALL_RETENTION_DAYS: int = 365


# ── Spec dataclass ─────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class AgentObservabilitySpec:
    """Per-agent observability metadata for cross-agent operations."""

    agent_kind: str
    """Discriminator value (``copilot`` / ``sales_agent`` / …). Used as a
    column value in the v2 MV and as the breakdown key in cost alerts."""

    llm_call_model: type[Base]
    """SQLAlchemy model class for the ``*_llm_call`` table this agent
    writes to. Aggregator constructors accept this directly."""

    trace_event_table: str
    """Raw table name for the ``*_trace_event`` table. Used by the
    retention worker which issues raw SQL DELETEs."""

    llm_call_table: str
    """Raw table name for the ``*_llm_call`` table."""

    trace_retention_env_var: str
    """Env var that overrides the trace-event retention window."""

    llm_call_retention_env_var: str
    """Env var that overrides the LLM-call retention window."""

    trace_default_days: int = _DEFAULT_TRACE_RETENTION_DAYS
    """Default trace-event retention. Most agents keep 90 days."""

    llm_call_default_days: int = _DEFAULT_LLM_CALL_RETENTION_DAYS
    """Default LLM-call retention. Default 365 days for billing audits."""

    has_lead_id: bool = False
    """Whether the LLM-call model exposes a ``lead_id`` column."""


# ── Registry storage ───────────────────────────────────────────────────


_REGISTRY: dict[str, AgentObservabilitySpec] = {}


def register_agent_observability(spec: AgentObservabilitySpec) -> None:
    """Push an agent spec into the registry. Idempotent on ``agent_kind``.

    Subsequent calls with the same ``agent_kind`` overwrite the previous
    spec — useful only for tests that want to swap a fake registry
    entry; production callers register each kind exactly once.
    """
    _REGISTRY[spec.agent_kind] = spec


def agent_observability_registry() -> tuple[AgentObservabilitySpec, ...]:
    """Return the immutable list of registered agent observability specs.

    Order is insertion order (Python 3.7+ dict guarantee), so dashboards
    that iterate the registry render copilot before sales_agent (the
    order in which they call ``register_agent_observability``).
    """
    return tuple(_REGISTRY.values())


def get_spec(agent_kind: str) -> AgentObservabilitySpec:
    """Lookup helper. Raises ``KeyError`` if the agent isn't registered."""
    spec = _REGISTRY.get(agent_kind)
    if spec is None:
        msg = f"Unknown agent_kind {agent_kind!r}. Known: {list(_REGISTRY.keys())}"
        raise KeyError(msg)
    return spec


__all__ = [
    "AgentObservabilitySpec",
    "agent_observability_registry",
    "get_spec",
    "register_agent_observability",
]
