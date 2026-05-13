"""EvalSimulator observability subclasses (T-5).

Inherits the canonical agent-observability lifecycle from
``shared/agent_observability/`` via subclassing — strict anti-duplication
§0 cement (NO mirror). Writes to T-1 mirror tables:

* ``eval_simulator_llm_call`` — agent + customer LLM calls during sim.
* ``eval_simulator_trace_event`` — turn lifecycle (turn_start / turn_end /
  llm_call / tool_call / node_enter / node_exit) + customer breadcrumbs.

Mandatory metadata jsonb (H5 — enforced per row):

::

    {
      "eval_run_kind":     "simulator",
      "archetype_slug":    str,
      "actor_profile_id":  str,
      "trial_n":           int,
      "simulation_id":     str(UUID),
      "run_id":            str(UUID),
    }

The metadata is constructed once at context build time (``EvalSimulatorObservabilityContext.start(...)``)
and propagated to **every** persisted row by the callback handler subclass.
This guarantees Streamlit prod queries can safely filter eval traffic
out via ``WHERE eval_metadata->>'eval_run_kind' = 'simulator'``.

Best-effort writes
==================

All persistence is wrapped in ``try/except`` + ``structlog.warning`` per
``.claude/rules/copilot-observability.md`` cement: an observability failure
must NEVER bubble out of the simulation loop. Failures degrade gracefully
to skipped rows, the simulation continues, and the structured warning
gives the operator enough breadcrumbs to diagnose offline.

Anti-duplication §0 — REUSE inventory
=====================================

Reused verbatim from ``shared/agent_observability/`` (NO mirror):

* :class:`~src.shared.agent_observability.recording.turn_envelope.BaseObservabilityContext`
  — full lifecycle (``observe_turn`` / ``_write_turn_*`` / ``set_turn_*`` /
  ``langchain_config`` / ``_commit_session``). Subclass overrides 3 abstract hooks:
  ``_add_trace_event`` / ``_aggregate_totals`` / ``_legacy_compat_keys_or_empty``.
* :class:`~src.shared.agent_observability.recording.base_callback_handler.BaseAgentCallbackHandler`
  — 8 LangChain callbacks + ``_persist_llm_call`` Template Method skeleton
  (sanitize → resolve pricing → calculate cost → persist). Subclass overrides
  2 abstract persisters: ``_persist_llm_call_row`` / ``_persist_trace_event_row``.
* :func:`~src.shared.agent_observability.recording.sanitization.sanitize_payload`
  — applied verbatim by the inherited ``_write_turn_*`` and Template Method paths.
* :class:`~src.shared.agent_observability.cost.fx_resolver.FXResolver` — reused
  via ``FXResolver.default()`` factory (encapsulates ``httpx.Client(timeout=10)``).
* :class:`~src.shared.agent_observability.pricing.resolver.PricingResolver` — reused.

Origin: PI-12 Story B eval-foundation-simulator-homologation T-5 (2026-05-07).

# voseo-allowed: docstring quotes glossary check artifact for arch fitness gate
"""

# NO ``from __future__ import annotations`` — story-wide cement from T-4.
# LangGraph runtime introspection requires resolved annotations; keeping
# this file free of lazy stringification matches the rest of the simulator
# tree (state.py, actor_profile.py, result.py, termination.py).

import contextlib
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_llm_call import (
    EvalSimulatorLlmCallModel,
)
from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_trace_event import (
    EvalSimulatorTraceEventModel,
)
from luana_core_observability.cost.fx_resolver import FXResolver
from luana_core_observability.persistence.pricing_snapshot_repository import (
    PricingSnapshotRepository,
)
from luana_core_observability.persistence.tenant_billing_config_repository import (
    TenantBillingConfigRepository,
)
from luana_core_observability.pricing.resolver import PricingResolver
from luana_core_observability.recording.base_callback_handler import (
    BaseAgentCallbackHandler,
)
from luana_core_observability.recording.turn_envelope import (
    BaseObservabilityContext,
    _empty_totals,
)

logger = structlog.get_logger()


_MANDATORY_EVAL_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "eval_run_kind",
        "archetype_slug",
        "actor_profile_id",
        "trial_n",
        "simulation_id",
        "run_id",
    },
)


def build_eval_metadata(
    *,
    archetype_slug: str,
    actor_profile_id: str,
    trial_n: int,
    simulation_id: UUID,
    run_id: UUID,
) -> dict[str, Any]:
    """Assemble the mandatory ``eval_metadata`` dict per H5.

    Always returns the 6 mandatory keys. The constant
    ``eval_run_kind="simulator"`` is enforced here (not configurable) so
    arch fitness gate ``test_simulator_writes_eval_kind_tag.py`` can probe
    every row across the suite.
    """
    return {
        "eval_run_kind": "simulator",
        "archetype_slug": archetype_slug,
        "actor_profile_id": actor_profile_id,
        "trial_n": int(trial_n),
        "simulation_id": str(simulation_id),
        "run_id": str(run_id),
    }


def _assert_eval_metadata_complete(metadata: dict[str, Any]) -> None:
    """Defense-in-depth (H5): refuse to persist when the 6 keys are absent.

    Raised as :class:`ValueError` so the inherited best-effort wrapper
    (``try/except`` in ``BaseObservabilityContext._write_turn_*`` and
    ``BaseAgentCallbackHandler.on_*``) logs a structured warning and
    drops the row. Bug-class ruled out: silent missing-tag rows that
    would later confuse cost reporting.
    """
    missing = _MANDATORY_EVAL_METADATA_KEYS.difference(metadata)
    if missing:
        msg = f"eval_metadata missing mandatory H5 keys: {sorted(missing)}. Got keys: {sorted(metadata)}"
        raise ValueError(msg)


# ───────────────────────────────────────────────────────────────────────
# Test-infra repos — co-located in observability.py since they only exist
# to bind the SQLAlchemy models to the H5 metadata invariant. Public
# observability writes via ``EvalSimulatorObservabilityContext`` /
# ``EvalSimulatorCallbackHandler`` — repos themselves are NOT part of
# H9 public surface (kept under ``_internal/``).
# ───────────────────────────────────────────────────────────────────────


class EvalSimulatorLlmCallRepository:
    """Persist ``eval_simulator_llm_call`` rows. Caller controls commit.

    Satisfies :class:`~src.shared.agent_observability.persistence.base_llm_call_repo.BaseLLMCallRepoProtocol`
    via structural typing — sync ``Session`` (matches the in-process
    ``agent_app.ainvoke`` invocation pattern from T-7).
    """

    def __init__(self, db: Session) -> None:
        """Bind the repository to a session."""
        self.db = db

    def add(self, **kwargs: Any) -> EvalSimulatorLlmCallModel:
        """Insert one row. Returns the persisted model.

        ``flush`` and ``commit`` are left to the caller (the callback
        handler batches several adds per turn before the orchestrator
        commits).
        """
        row = EvalSimulatorLlmCallModel(**kwargs)
        self.db.add(row)
        return row


class EvalSimulatorTraceEventRepository:
    """Persist ``eval_simulator_trace_event`` rows.

    Satisfies :class:`~src.shared.agent_observability.persistence.base_trace_event_repo.BaseTraceEventRepoProtocol`
    via structural typing.
    """

    def __init__(self, db: Session) -> None:
        """Bind the repository to a session."""
        self.db = db

    def add(
        self,
        *,
        tenant_id: UUID,
        turn_id: UUID,
        span_id: UUID,
        event_type: str,
        name: str | None = None,
        data: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        status: str = "ok",
        parent_span_id: UUID | None = None,
        # eval-specific (declared on abstract base via **agent_specific):
        channel_type: str = "eval_simulator",
        eval_metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> EvalSimulatorTraceEventModel:
        """Insert one trace-event row. Returns the persisted model.

        ``eval_metadata`` MUST contain the 6 mandatory H5 keys — assertion
        raised if any missing. ``created_at`` defaults to the value the
        caller computed (UTC); models declare the column non-null.
        """
        meta = eval_metadata or {}
        _assert_eval_metadata_complete(meta)
        row = EvalSimulatorTraceEventModel(
            id=uuid4(),
            tenant_id=tenant_id,
            lead_id=None,  # eval has no per-lead audit (NULL by design)
            channel_type=channel_type,
            turn_id=turn_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            event_type=event_type,
            name=name,
            data=data or {},
            duration_ms=duration_ms,
            status=status,
            eval_metadata=meta,
            created_at=created_at or datetime.now(tz=__import__("datetime").timezone.utc),
        )
        self.db.add(row)
        return row


# ───────────────────────────────────────────────────────────────────────
# Callback handler subclass — Template Method (override ONLY 2 abstract
# persisters). LangChain plumbing + cost recorder bridge stays in shared
# base.
# ───────────────────────────────────────────────────────────────────────


@dataclass
class EvalSimulatorCallbackHandler(BaseAgentCallbackHandler):
    """Self-contained recorder for eval simulator. One instance per turn.

    Inherits the 8 LangChain callbacks (``on_chat_model_start`` /
    ``on_llm_end`` / ``on_llm_error`` / ``on_tool_start`` / ``on_tool_end`` /
    ``on_tool_error`` / ``on_chain_start`` / ``on_chain_end``) +
    ``_persist_llm_call`` Template Method skeleton (sanitize → pricing →
    cost → persist) from :class:`BaseAgentCallbackHandler`. This subclass
    only carries:

    * eval-specific repos (``llm_call_repo`` / ``trace_repo``)
    * ``db_session`` (for ``_safe_rollback``)
    * ``eval_metadata`` (H5 — propagated to every persisted row)

    The two abstract method overrides inject ``eval_metadata`` +
    ``channel_type='eval_simulator'`` + ``lead_id=None`` onto every row.
    Best-effort: persist-time failures are caught by the inherited
    ``on_*`` wrappers and logged via ``structlog.warning``.
    """

    # Defaults required for dataclass field-ordering — base parent has
    # required fields without defaults (``tenant_id`` / ``turn_id`` /
    # ``pricing_resolver`` / ``fx_resolver``); subclasses adding fields
    # MUST default them. Real values arrive via ``__init__`` keyword args.
    llm_call_repo: EvalSimulatorLlmCallRepository = None  # type: ignore[assignment]
    trace_repo: EvalSimulatorTraceEventRepository = None  # type: ignore[assignment]
    db_session: Any = None  # SQLAlchemy Session — typed Any to keep Protocol structural
    eval_metadata: dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Validate H5 metadata at construction time.

        Catching missing keys here rather than per-row gives a single
        loud failure during turn setup vs N silent dropped rows during
        the LangGraph stream. Per-row defense-in-depth still applies in
        the persisters (see ``_assert_eval_metadata_complete``).
        """
        if self.eval_metadata is None:
            self.eval_metadata = {}
        _assert_eval_metadata_complete(self.eval_metadata)

    # ── abstract method overrides (Template Method) ──────────────────────

    def _persist_llm_call_row(self, **kwargs: Any) -> None:
        """Persist one row to ``eval_simulator_llm_call``.

        Injects ``lead_id=None`` (eval has no per-lead audit), ``channel_type``
        defaults to ``'eval_simulator'``, and the H5 ``eval_metadata`` jsonb.
        Best-effort handled by inherited ``on_llm_*`` callbacks.
        """
        self.llm_call_repo.add(
            parent_span_id=None,
            lead_id=None,
            channel_type="eval_simulator",
            eval_metadata=dict(self.eval_metadata),
            **kwargs,
        )

    def _persist_trace_event_row(self, **kwargs: Any) -> None:
        """Persist one row to ``eval_simulator_trace_event``.

        Injects ``channel_type='eval_simulator'`` + H5 ``eval_metadata``
        jsonb. Best-effort handled by inherited ``on_*`` callbacks.
        """
        self.trace_repo.add(
            channel_type="eval_simulator",
            eval_metadata=dict(self.eval_metadata),
            **kwargs,
        )


# ───────────────────────────────────────────────────────────────────────
# Observability context subclass — owns the full per-turn lifecycle.
# Inherits ``observe_turn`` / ``_write_turn_*`` / ``set_turn_*`` /
# ``langchain_config`` / ``_commit_session`` verbatim. Implements 3
# abstract hooks (``_add_trace_event`` / ``_aggregate_totals`` /
# ``_legacy_compat_keys_or_empty``).
# ───────────────────────────────────────────────────────────────────────


@dataclass
class EvalSimulatorObservabilityContext(BaseObservabilityContext):
    """Concrete eval-simulator context. Owns the callback handler + lifecycle.

    Inherits from :class:`BaseObservabilityContext` — DO NOT redefine the
    locked methods (``observe_turn``, ``_write_turn_*``, ``set_turn_*``,
    ``langchain_config``, ``_commit_session``); enforced by the arch test
    that AST-parses subclass surfaces.

    Wires every persisted row with the H5 mandatory metadata so the cost
    bucket separation invariant holds end-to-end.
    """

    eval_metadata: dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Validate H5 metadata at context construction time."""
        if self.eval_metadata is None:
            self.eval_metadata = {}
        _assert_eval_metadata_complete(self.eval_metadata)

    # ── factory ─────────────────────────────────────────────────────────

    @classmethod
    def start(
        cls,
        *,
        tenant_id: UUID,
        archetype_slug: str,
        actor_profile_id: str,
        trial_n: int,
        simulation_id: UUID,
        run_id: UUID,
        llm_call_repo: EvalSimulatorLlmCallRepository,
        trace_repo: EvalSimulatorTraceEventRepository,
        pricing_resolver: PricingResolver,
        fx_resolver: FXResolver,
        db_session: Session,
        tenant_currency: str = "USD",
        role: str = "agent",
        turn_id: UUID | None = None,
    ) -> "EvalSimulatorObservabilityContext":
        """Build a fresh per-turn context. Turn id is allocated if not provided.

        ``db_session`` is forwarded to :class:`EvalSimulatorCallbackHandler`
        for ``_safe_rollback``. Repos are shared with the orchestrator so
        the envelope's ``_commit_session`` covers the same UoW.
        """
        tid = turn_id or uuid4()
        eval_metadata = build_eval_metadata(
            archetype_slug=archetype_slug,
            actor_profile_id=actor_profile_id,
            trial_n=trial_n,
            simulation_id=simulation_id,
            run_id=run_id,
        )
        handler = EvalSimulatorCallbackHandler(
            tenant_id=tenant_id,
            turn_id=tid,
            pricing_resolver=pricing_resolver,
            fx_resolver=fx_resolver,
            tenant_currency=tenant_currency,
            role=role,
            llm_call_repo=llm_call_repo,
            trace_repo=trace_repo,
            db_session=db_session,
            eval_metadata=eval_metadata,
        )
        return cls(
            tenant_id=tenant_id,
            turn_id=tid,
            callback_handler=handler,
            trace_repo=trace_repo,
            llm_call_repo=llm_call_repo,
            eval_metadata=eval_metadata,
        )

    # ── abstract hook impls ────────────────────────────────────────────

    def _add_trace_event(
        self,
        *,
        event_type: str,
        name: str,
        data: dict[str, Any],
        duration_ms: int | None = None,
        status: str = "ok",
        span_id: UUID | None = None,
    ) -> None:
        """Persist one row to ``eval_simulator_trace_event``.

        Injects ``channel_type='eval_simulator'`` + H5 ``eval_metadata``.
        Best-effort: caught by inherited ``_write_turn_*`` outer wrappers,
        but we still log here for granular breadcrumbs.
        """
        try:
            self.trace_repo.add(
                tenant_id=self.tenant_id,
                turn_id=self.turn_id,
                span_id=span_id or uuid4(),
                event_type=event_type,
                name=name,
                data=data,
                duration_ms=duration_ms,
                status=status,
                channel_type="eval_simulator",
                eval_metadata=dict(self.eval_metadata),
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "eval_simulator_obs_add_trace_event_failed",
                event_type=event_type,
                error=str(exc),
                simulation_id=self.eval_metadata.get("simulation_id"),
            )

    def _aggregate_totals(self) -> dict[str, Any]:
        """Sum the ``eval_simulator_llm_call`` rows for this turn."""
        try:
            session = self.llm_call_repo.db
            with contextlib.suppress(Exception):
                session.flush()
            stmt = select(
                func.count().label("count"),
                func.coalesce(func.sum(EvalSimulatorLlmCallModel.input_tokens), 0).label(
                    "input_tokens",
                ),
                func.coalesce(func.sum(EvalSimulatorLlmCallModel.output_tokens), 0).label(
                    "output_tokens",
                ),
                func.coalesce(func.sum(EvalSimulatorLlmCallModel.cached_read_tokens), 0).label(
                    "cached_read_tokens",
                ),
                func.coalesce(func.sum(EvalSimulatorLlmCallModel.cost_usd), 0).label("cost_usd"),
            ).where(
                EvalSimulatorLlmCallModel.tenant_id == self.tenant_id,
                EvalSimulatorLlmCallModel.turn_id == self.turn_id,
            )
            row = session.execute(stmt).one()
            return {
                "llm_call_count": int(row.count),
                "total_input_tokens": int(row.input_tokens),
                "total_output_tokens": int(row.output_tokens),
                "total_cached_read_tokens": int(row.cached_read_tokens),
                "total_cost_usd": str(Decimal(row.cost_usd)),
                "model_responded": self._most_used_model(session),
            }
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "eval_simulator_obs_aggregate_totals_failed",
                error=str(exc),
                simulation_id=self.eval_metadata.get("simulation_id"),
            )
            return _empty_totals()

    def _most_used_model(self, session: Any) -> str:
        """Pick the model with the most LLM calls for this turn."""
        try:
            stmt = (
                select(
                    EvalSimulatorLlmCallModel.model_responded,
                    func.count().label("c"),
                )
                .where(
                    EvalSimulatorLlmCallModel.tenant_id == self.tenant_id,
                    EvalSimulatorLlmCallModel.turn_id == self.turn_id,
                )
                .group_by(EvalSimulatorLlmCallModel.model_responded)
                .order_by(func.count().desc())
                .limit(1)
            )
            row = session.execute(stmt).first()
            return str(row.model_responded) if row is not None else ""
        except Exception:  # noqa: BLE001 — best-effort
            return ""

    def _legacy_compat_keys_or_empty(self, totals: dict[str, Any]) -> dict[str, Any]:
        """Eval simulator has no legacy JSONB consumer — return empty dict.

        Any future Streamlit dashboard for eval cost would consume the
        new columnar schema directly (``eval_simulator_llm_call`` +
        ``eval_metadata`` jsonb), not this legacy compat shape.
        """
        del totals  # interface contract — kept for future symmetry
        return {}


# ───────────────────────────────────────────────────────────────────────
# Factory — paridad sales_agent ``build_sales_agent_observability_context``.
# Called by T-7 ``agent_bridge`` before invoking ``agent_app.ainvoke``.
# Best-effort: returns ``None`` when prerequisites missing rather than
# raising (no observability < broken simulation).
# ───────────────────────────────────────────────────────────────────────


def build_eval_simulator_observability_context(
    *,
    db: Session,
    tenant_id: UUID,
    archetype_slug: str,
    actor_profile_id: str,
    trial_n: int,
    simulation_id: UUID,
    run_id: UUID,
    turn_id: UUID,
    role: str = "agent",
) -> EvalSimulatorObservabilityContext | None:
    """Build a turn-scoped eval-simulator observability context.

    Returns ``None`` when ``tenant_id`` is missing — the simulator should
    abort cleanly rather than persist orphan rows. Construction failures
    (pricing repo unreachable, FX resolver init crash, billing config
    crash) are swallowed with a structured warning per
    ``.claude/rules/copilot-observability.md`` cement.

    The return shape (``Context | None``) mirrors
    :func:`~src.modules.sales_agent.observability.recording.factory.build_sales_agent_observability_context`
    so the agent_bridge consumer can treat both fall-back modes
    identically.
    """
    if tenant_id is None:
        return None
    try:
        billing_repo = TenantBillingConfigRepository(db)
        llm_call_repo = EvalSimulatorLlmCallRepository(db)
        trace_repo = EvalSimulatorTraceEventRepository(db)
        pricing_resolver = PricingResolver(repo_factory=lambda: PricingSnapshotRepository(db))
        fx_resolver = FXResolver.default()
        billing_cfg = billing_repo.get(tenant_id=tenant_id)
        tenant_currency = str(billing_cfg.billing_currency) if billing_cfg else "USD"
        return EvalSimulatorObservabilityContext.start(
            tenant_id=tenant_id,
            archetype_slug=archetype_slug,
            actor_profile_id=actor_profile_id,
            trial_n=trial_n,
            simulation_id=simulation_id,
            run_id=run_id,
            llm_call_repo=llm_call_repo,
            trace_repo=trace_repo,
            pricing_resolver=pricing_resolver,
            fx_resolver=fx_resolver,
            db_session=db,
            tenant_currency=tenant_currency,
            role=role,
            turn_id=turn_id,
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "eval_simulator_observability_context_factory_failed",
            error=str(exc),
            tenant_id=str(tenant_id),
            simulation_id=str(simulation_id),
        )
        return None


__all__ = [
    "EvalSimulatorCallbackHandler",
    "EvalSimulatorLlmCallRepository",
    "EvalSimulatorObservabilityContext",
    "EvalSimulatorTraceEventRepository",
    "build_eval_metadata",
    "build_eval_simulator_observability_context",
]
